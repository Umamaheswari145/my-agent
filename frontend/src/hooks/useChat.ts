import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type Dispatch,
  type SetStateAction,
} from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { errorMessage } from '../utils/errors';
import {
  createConversation,
  listMessages,
  streamChat,
} from '../services/api';
import type { ChatEvent, ChatRequest, Message } from '../types/chat';

function temporaryUserMessage(content: string): Message {
  return {
    id: `temp:user:${Date.now()}`,
    conversation_id: '',
    role: 'user',
    content,
    created_at: new Date().toISOString(),
    is_error: false,
  };
}

function temporaryAssistantMessage(): Message {
  return {
    id: `temp:assistant:${Date.now()}`,
    conversation_id: '',
    role: 'assistant',
    content: '',
    created_at: new Date().toISOString(),
    is_error: false,
  };
}

export function useChat(conversationId: string | undefined) {
  const navigate = useNavigate();
  const { refreshConversations } = useApp();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [webSearch, setWebSearch] = useState(false);
  const activeIdRef = useRef<string | undefined>(conversationId);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    activeIdRef.current = conversationId;
    if (!conversationId) {
      setMessages([]);
      return;
    }
    let cancelled = false;
    setLoading(true);
    listMessages(conversationId)
      .then((result) => {
        if (!cancelled) {
          setMessages(result.items);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError('Could not load this conversation.');
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [conversationId]);

  const runStream = useCallback(
    async (
      request: ChatRequest,
      placeholderUser: Message,
      placeholderAssistant: Message,
      createdNew: boolean,
    ) => {
      const controller = new AbortController();
      abortRef.current = controller;
      setStreaming(true);
      setError(null);
      const ids = { userId: placeholderUser.id, assistantId: placeholderAssistant.id };
      setMessages((current) => [...current, placeholderUser, placeholderAssistant]);

      try {
        for await (const event of streamChat(request, controller.signal)) {
          applyEvent(event, ids, setMessages);
        }
        await refreshConversations();
        if (createdNew && activeIdRef.current) {
          navigate(`/chat/${activeIdRef.current}`, { replace: true });
        }
      } catch (cause) {
        if (!controller.signal.aborted) {
          const message = errorMessage(cause, 'The request could not be completed.');
          setError(message);
          setMessages((current) =>
            current.map((item) =>
              item.id === ids.assistantId ? { ...item, is_error: true } : item,
            ),
          );
        }
      } finally {
        setStreaming(false);
        abortRef.current = null;
      }
    },
    [navigate, refreshConversations],
  );

  const send = useCallback(
    async (content: string) => {
      const trimmed = content.trim();
      if (!trimmed || streaming) {
        return;
      }
      let conversationId = activeIdRef.current;
      let createdNew = false;
      if (!conversationId) {
        const created = await createConversation();
        conversationId = created.id;
        activeIdRef.current = conversationId;
        createdNew = true;
      }
      await runStream(
        {
          content: trimmed,
          conversation_id: conversationId,
          use_web_search: webSearch,
        },
        temporaryUserMessage(trimmed),
        temporaryAssistantMessage(),
        createdNew,
      );
    },
    [runStream, streaming, webSearch],
  );

  const regenerate = useCallback(
    async (assistantMessageId: string) => {
      if (streaming) {
        return;
      }
      const index = messages.findIndex((item) => item.id === assistantMessageId);
      if (index < 0) {
        return;
      }
      let userContent = '';
      for (let cursor = index - 1; cursor >= 0; cursor -= 1) {
        if (messages[cursor].role === 'user') {
          userContent = messages[cursor].content;
          break;
        }
      }
      if (!userContent) {
        return;
      }
      setMessages(messages.slice(0, index));
      await runStream(
        {
          content: userContent,
          conversation_id: activeIdRef.current ?? null,
          regenerate_of: assistantMessageId,
          use_web_search: webSearch,
        },
        temporaryUserMessage(userContent),
        temporaryAssistantMessage(),
        false,
      );
    },
    [messages, runStream, streaming, webSearch],
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return {
    messages,
    loading,
    streaming,
    error,
    webSearch,
    toggleWebSearch: () => setWebSearch((current) => !current),
    send,
    stop,
    regenerate,
    clearError: () => setError(null),
  };
}

interface StreamIds {
  userId: string;
  assistantId: string;
}

function applyEvent(
  event: ChatEvent,
  ids: StreamIds,
  setMessages: Dispatch<SetStateAction<Message[]>>,
) {
  if (event.type === 'started') {
    const previousUserId = ids.userId;
    const previousAssistantId = ids.assistantId;
    setMessages((current) =>
      current.map((item) => {
        if (item.id === previousUserId) {
          return { ...item, id: event.user_message_id, conversation_id: event.conversation_id };
        }
        if (item.id === previousAssistantId) {
          return { ...item, id: event.assistant_message_id, conversation_id: event.conversation_id };
        }
        return item;
      }),
    );
    ids.userId = event.user_message_id;
    ids.assistantId = event.assistant_message_id;
    return;
  }
  if (event.type === 'delta') {
    setMessages((current) =>
      current.map((item) =>
        item.id === ids.assistantId ? { ...item, content: item.content + event.content } : item,
      ),
    );
    return;
  }
  if (event.type === 'done') {
    setMessages((current) =>
      current.map((item) => (item.id === ids.assistantId ? event.message : item)),
    );
    return;
  }
  setMessages((current) =>
    current.map((item) =>
      item.id === ids.assistantId
        ? { ...item, content: item.content || event.message, is_error: true }
        : item,
    ),
  );
}
