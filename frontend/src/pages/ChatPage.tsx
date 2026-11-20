import { useParams } from 'react-router-dom';
import EmptyState from '../components/EmptyState';
import ErrorBanner from '../components/ErrorBanner';
import MessageInput from '../components/MessageInput';
import MessageList from '../components/MessageList';
import { CloseIcon, SparklesIcon } from '../components/Icons';
import { useApp } from '../context/AppContext';
import { useChat } from '../hooks/useChat';

export default function ChatPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { conversations } = useApp();
  const chat = useChat(conversationId);
  const title = conversations.find((item) => item.id === conversationId)?.title;

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <header className="flex items-center gap-3 border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <SparklesIcon className="h-5 w-5 text-sky-600 dark:text-sky-400" />
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-sm font-semibold text-slate-800 dark:text-slate-100">
            {title ?? 'New conversation'}
          </h1>
        </div>
      </header>

      {chat.error && (
        <ErrorBanner
          message={chat.error}
          className="mx-auto mt-3 w-full max-w-3xl"
          action={
            <button type="button" onClick={chat.clearError} aria-label="Dismiss error">
              <CloseIcon className="h-4 w-4" />
            </button>
          }
        />
      )}

      {chat.messages.length === 0 ? (
        <EmptyState onPick={(prompt) => void chat.send(prompt)} />
      ) : (
        <MessageList
          messages={chat.messages}
          streaming={chat.streaming}
          onRegenerate={(id) => void chat.regenerate(id)}
        />
      )}

      <MessageInput
        streaming={chat.streaming}
        useWebSearch={chat.webSearch}
        onToggleWebSearch={chat.toggleWebSearch}
        onSend={(content) => void chat.send(content)}
        onStop={chat.stop}
      />
    </div>
  );
}
