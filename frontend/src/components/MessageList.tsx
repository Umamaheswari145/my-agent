import { useEffect, useRef } from 'react';
import type { Message } from '../types/chat';
import MessageBubble from './MessageBubble';

interface MessageListProps {
  messages: Message[];
  streaming: boolean;
  onRegenerate: (messageId: string) => void;
}

export default function MessageList({ messages, streaming, onRegenerate }: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const stickRef = useRef(true);

  useEffect(() => {
    const element = scrollRef.current;
    if (element && stickRef.current) {
      element.scrollTop = element.scrollHeight;
    }
  }, [messages, streaming]);

  function handleScroll() {
    const element = scrollRef.current;
    if (!element) {
      return;
    }
    stickRef.current =
      element.scrollHeight - element.scrollTop - element.clientHeight < 120;
  }

  return (
    <div
      ref={scrollRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto"
      aria-label="Conversation messages"
    >
      <div className="mx-auto w-full max-w-3xl divide-y divide-slate-100 dark:divide-slate-800/60">
        {messages.map((message, index) => (
          <MessageBubble
            key={message.id}
            message={message}
            canRegenerate={!streaming && message.role === 'assistant' && index === messages.length - 1}
            onRegenerate={onRegenerate}
          />
        ))}
      </div>
    </div>
  );
}
