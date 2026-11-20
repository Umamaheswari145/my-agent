import type { Message } from '../types/chat';
import CopyButton from './CopyButton';
import { RefreshIcon, SparklesIcon, WarningIcon } from './Icons';
import MarkdownContent from './MarkdownContent';

const actionButtonClass =
  'inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-slate-500 transition hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200';

interface MessageBubbleProps {
  message: Message;
  canRegenerate: boolean;
  onRegenerate: (messageId: string) => void;
}

export default function MessageBubble({ message, canRegenerate, onRegenerate }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end px-4 py-3">
        <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-sky-600 px-4 py-3 text-[15px] leading-7 text-white shadow-sm">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3 px-4 py-3">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-sky-500 to-indigo-600 text-white shadow-sm">
        <SparklesIcon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        {message.is_error && (
          <div className="mb-2 inline-flex items-center gap-2 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-950/40 dark:text-rose-300">
            <WarningIcon className="h-4 w-4 shrink-0" />
            <span>Response could not be completed.</span>
          </div>
        )}
        {message.content ? (
          <MarkdownContent content={message.content} />
        ) : (
          <div className="flex items-center gap-1 py-2">
            <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.2s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.1s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
          </div>
        )}
        {message.content && (
          <div className="mt-2 flex items-center gap-1">
            <CopyButton
              text={message.content}
              ariaLabel="Copy response"
              className={actionButtonClass}
            />
            {canRegenerate && (
              <button
                type="button"
                onClick={() => onRegenerate(message.id)}
                className={actionButtonClass}
                aria-label="Regenerate response"
              >
                <RefreshIcon className="h-3.5 w-3.5" />
                Regenerate
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
