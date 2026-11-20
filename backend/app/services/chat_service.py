import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.agents.agent import AgentService
from app.core.config import Settings
from app.core.constants import ASSISTANT_ROLE, USER_ROLE
from app.core.errors import AppError
from app.llm.base import ChatMessage, LLMProvider
from app.llm.errors import ProviderNotConfiguredError
from app.models import Conversation, Message, User
from app.prompts.system_prompt import build_system_prompt
from app.schemas.conversation import (
    ChatDeltaEvent,
    ChatDoneEvent,
    ChatErrorEvent,
    ChatRequest,
    ChatResponse,
    ChatStartedEvent,
    MessageResponse,
)
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.memory_service import MemoryService
from app.services.model_config_service import ModelConfigService
from app.services.preference_service import PreferenceService
from app.tools.calculator import CalculatorTool
from app.tools.documents import DocumentSearchTool
from app.tools.memories import MemorySearchTool
from app.tools.registry import ToolRegistry
from app.tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChatEvent:
    name: str
    data: dict[str, object]


@dataclass(frozen=True)
class PreparedChat:
    conversation: Conversation
    assistant_message: Message
    user_message: Message
    agent: AgentService
    history: tuple[ChatMessage, ...]


class ChatService:
    def __init__(
        self,
        settings: Settings,
        db: Session,
        user: User,
        provider: LLMProvider | None,
    ) -> None:
        self._settings = settings
        self._db = db
        self._user = user
        self._provider = provider
        self._conversations = ConversationService()
        self._preferences = PreferenceService()
        self._model_configs = ModelConfigService()
        self._memories = MemoryService()
        self._documents = DocumentService(settings)

    async def send(self, request: ChatRequest) -> ChatResponse:
        prepared = await self._prepare(request)
        try:
            result = await prepared.agent.run(prepared.history)
            content = result.content.strip() or "I could not generate a response. Please try again."
            self._conversations.update_message(self._db, prepared.assistant_message, content)
        except Exception as exc:
            self._conversations.mark_message_error(
                self._db, prepared.assistant_message, self._friendly_message(exc)
            )
            raise
        return ChatResponse(
            conversation_id=prepared.conversation.id,
            title=prepared.conversation.title,
            message=MessageResponse.model_validate(prepared.assistant_message),
            user_message_id=prepared.user_message.id,
        )

    async def stream(self, request: ChatRequest) -> AsyncIterator[ChatEvent]:
        prepared = await self._prepare(request)
        yield ChatEvent(
            "started",
            ChatStartedEvent(
                conversation_id=prepared.conversation.id,
                user_message_id=prepared.user_message.id,
                assistant_message_id=prepared.assistant_message.id,
                title=prepared.conversation.title,
            ).model_dump(mode="json"),
        )

        buffer: list[str] = []
        last_saved = 0
        failed = False
        try:
            async for text in prepared.agent.stream(prepared.history):
                buffer.append(text)
                yield ChatEvent("delta", ChatDeltaEvent(content=text).model_dump(mode="json"))
                current = "".join(buffer)
                if len(current) - last_saved >= 500:
                    self._conversations.update_message(
                        self._db, prepared.assistant_message, current
                    )
                    last_saved = len(current)
            content = "".join(buffer).strip() or "I could not generate a response. Please try again."
            self._conversations.update_message(self._db, prepared.assistant_message, content)
            yield ChatEvent(
                "done",
                ChatDoneEvent(
                    message=MessageResponse.model_validate(prepared.assistant_message)
                ).model_dump(mode="json"),
            )
        except Exception as exc:
            failed = True
            logger.warning("Chat generation failed: %s", exc)
            self._conversations.mark_message_error(
                self._db, prepared.assistant_message, self._friendly_message(exc)
            )
            yield ChatEvent(
                "error",
                ChatErrorEvent(
                    code=getattr(exc, "error_code", "generation_error"),
                    message=self._friendly_message(exc),
                ).model_dump(mode="json"),
            )
        finally:
            partial = "".join(buffer)
            if not failed and partial and prepared.assistant_message.content != partial:
                self._conversations.update_message(
                    self._db, prepared.assistant_message, partial
                )

    async def _prepare(self, request: ChatRequest) -> PreparedChat:
        if self._provider is None:
            raise ProviderNotConfiguredError(
                "LLM_API_KEY is not configured. Add it to backend/.env to enable AI responses."
            )

        conversation = self._get_or_create_conversation(request)
        user_message = self._resolve_user_message(conversation, request)

        preference = self._preferences.get_or_create(self._db, self._user)
        model_config = self._model_configs.get_or_create(self._db, self._user, self._settings)

        if preference.memory_enabled and request.regenerate_of is None:
            await self._memories.extract_from_text(
                self._db,
                self._user,
                user_message.content,
                source="conversation",
                provider=self._provider,
            )

        memories = []
        if preference.memory_enabled:
            memories = await self._memories.retrieve(
                self._db, self._user, request.content, self._settings.MEMORY_TOP_K, self._provider
            )

        document_context = await self._document_context(request.content)
        web_context = await self._web_context(request) if request.use_web_search else ""

        system_prompt = build_system_prompt(
            custom_prompt=model_config.system_prompt or self._settings.SYSTEM_PROMPT,
            preference_text=self._preferences.instructions(preference),
            memories=memories,
            document_context=document_context,
            web_context=web_context,
        )

        recent = self._conversations.recent_messages(
            self._db, conversation, self._settings.MAX_CONTEXT_MESSAGES
        )
        history = tuple(
            ChatMessage(role=message.role, content=message.content)
            for message in recent
            if message.role in {USER_ROLE, ASSISTANT_ROLE} and message.content.strip()
        )

        registry = ToolRegistry()
        registry.register(CalculatorTool())
        registry.register(WebSearchTool(self._settings))
        registry.register(MemorySearchTool(self._db, self._user, self._memories))
        registry.register(
            DocumentSearchTool(self._db, self._user, self._documents, self._settings)
        )
        agent = AgentService(self._provider, registry, system_prompt)

        assistant_message = self._conversations.add_message(
            self._db, conversation, role=ASSISTANT_ROLE, content=""
        )
        return PreparedChat(
            conversation=conversation,
            assistant_message=assistant_message,
            user_message=user_message,
            agent=agent,
            history=history,
        )

    def _get_or_create_conversation(self, request: ChatRequest) -> Conversation:
        if request.conversation_id is None:
            return self._conversations.create(self._db, self._user)
        return self._conversations.get(self._db, self._user, request.conversation_id)

    def _resolve_user_message(self, conversation: Conversation, request: ChatRequest) -> Message:
        if request.regenerate_of is not None:
            target = self._db.get(Message, request.regenerate_of)
            if target is None or target.user_id != self._user.id or target.conversation_id != conversation.id:
                raise AppError("Message not found.", status_code=404, error_code="not_found")
            from app.repositories.messages import MessageRepository

            MessageRepository().delete_tail(self._db, conversation.id, target.id)
            previous = self._conversations.last_user_message(self._db, conversation)
            if previous is None:
                raise AppError("Nothing to regenerate.", status_code=400, error_code="bad_request")
            return previous

        message = self._conversations.add_message(
            self._db, conversation, role=USER_ROLE, content=request.content
        )
        if conversation.title.startswith("New chat"):
            self._conversations.set_title_from_message(self._db, conversation, request.content)
        return message

    async def _document_context(self, query: str) -> str:
        try:
            results = await self._documents.search(
                self._db, self._user, query, 3, self._provider
            )
        except Exception:
            logger.warning("Document retrieval failed", exc_info=True)
            return ""
        if not results:
            return ""
        return "\n".join(
            f"[{item.filename}, chunk {item.chunk_index}] {item.content}" for item in results
        )

    async def _web_context(self, request: ChatRequest) -> str:
        tool = WebSearchTool(self._settings)
        result = await tool.run({"query": request.content[:400], "count": 3})
        return result.output if result.success else ""

    @staticmethod
    def _friendly_message(exc: Exception) -> str:
        if isinstance(exc, AppError):
            return exc.detail
        logger.exception("Unexpected chat error")
        return "An unexpected error occurred while generating the response."
