import { useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { SendIcon, StopIcon } from './Icons';

interface MessageInputProps {
  streaming: boolean;
  useWebSearch: boolean;
  onToggleWebSearch: () => void;
  onSend: (content: string) => void;
  onStop: () => void;
}

export default function MessageInput({
  streaming,
  useWebSearch,
  onToggleWebSearch,
  onSend,
  onStop,
}: MessageInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const element = textareaRef.current;
    if (element) {
      element.style.height = 'auto';
      element.style.height = `${Math.min(element.scrollHeight, 200)}px`;
    }
  }, [value]);

  function submit() {
    const content = value.trim();
    if (!content || streaming) {
      return;
    }
    onSend(content);
    setValue('');
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <div className="border-t border-slate-200 bg-white/80 px-4 py-4 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
      <div className="mx-auto w-full max-w-3xl">
        <div className="rounded-2xl border border-slate-200 bg-white p-2 shadow-sm transition focus-within:border-sky-400 focus-within:ring-2 focus-within:ring-sky-100 dark:border-slate-700 dark:bg-slate-900 dark:focus-within:border-sky-600 dark:focus-within:ring-sky-950">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            placeholder="Ask anything, or describe what you need help with..."
            aria-label="Message input"
            className="max-h-[200px] w-full resize-none bg-transparent px-2 py-2 text-[15px] leading-6 text-slate-800 outline-none placeholder:text-slate-400 dark:text-slate-100 dark:placeholder:text-slate-500"
          />
          <div className="mt-1 flex items-center justify-between gap-2 px-1">
            <button
              type="button"
              onClick={onToggleWebSearch}
              aria-pressed={useWebSearch}
              className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
                useWebSearch
                  ? 'bg-sky-100 text-sky-700 dark:bg-sky-950 dark:text-sky-300'
                  : 'text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
              }`}
            >
              Web search {useWebSearch ? 'on' : 'off'}
            </button>
            {streaming ? (
              <button
                type="button"
                onClick={onStop}
                className="inline-flex h-9 items-center gap-2 rounded-xl bg-slate-800 px-4 text-sm font-medium text-white transition hover:bg-slate-700 dark:bg-slate-200 dark:text-slate-900 dark:hover:bg-white"
              >
                <StopIcon className="h-4 w-4" />
                Stop
              </button>
            ) : (
              <button
                type="button"
                onClick={submit}
                disabled={!value.trim()}
                aria-label="Send message"
                className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-sky-600 text-white transition hover:bg-sky-500 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <SendIcon className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
        <p className="mt-2 text-center text-[11px] text-slate-400">
          Enter to send · Shift + Enter for a new line · AI can make mistakes, verify important information.
        </p>
      </div>
    </div>
  );
}
