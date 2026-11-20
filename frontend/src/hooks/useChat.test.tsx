import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppProvider } from '../context/AppContext';
import {
  createConversation,
  listConversations,
  listMessages,
  streamChat,
} from '../services/api';
import type { ChatEvent } from '../types/chat';
import { useChat } from './useChat';

const navigateMock = vi.hoisted(() => vi.fn());

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => navigateMock };
});

vi.mock('../services/api', () => ({
  ApiError: class ApiError extends Error {
    status = 0;
    code = '';

    constructor(status: number, code: string, message: string) {
      super(message);
      this.status = status;
      this.code = code;
    }
  },
  createConversation: vi.fn(),
  deleteConversation: vi.fn(),
  listConversations: vi.fn(),
  renameConversation: vi.fn(),
  listMessages: vi.fn(),
  streamChat: vi.fn(),
}));

const conversation = {
  id: 'conv-1',
  title: 'New chat',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

function wrapper({ children }: { children: ReactNode }) {
  return (
    <MemoryRouter>
      <AppProvider>{children}</AppProvider>
    </MemoryRouter>
  );
}

describe('useChat', () => {
  beforeEach(() => {
    navigateMock.mockClear();
    vi.mocked(listConversations).mockResolvedValue({
      items: [],
      total: 0,
      limit: 100,
      offset: 0,
    });
    vi.mocked(listMessages).mockResolvedValue({
      items: [],
      total: 0,
      limit: 500,
      offset: 0,
    });
    vi.mocked(createConversation).mockResolvedValue(conversation);
    vi.mocked(streamChat).mockImplementation(async function* () {
      const events: ChatEvent[] = [
        {
          type: 'started',
          conversation_id: 'conv-1',
          user_message_id: 'u1',
          assistant_message_id: 'a1',
          title: 'New chat',
        },
        { type: 'delta', content: 'Hello' },
        { type: 'delta', content: ' world' },
        {
          type: 'done',
          message: {
            id: 'a1',
            conversation_id: 'conv-1',
            role: 'assistant',
            content: 'Hello world',
            created_at: '2026-01-01T00:00:00Z',
            is_error: false,
          },
        },
      ];
      for (const event of events) {
        yield event;
      }
    });
  });

  it('streams a reply into the message list', async () => {
    const { result } = renderHook(() => useChat(undefined), { wrapper });

    await act(async () => {
      await result.current.send('Say hello');
    });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[1].content).toBe('Hello world');
    });
    expect(result.current.streaming).toBe(false);
    expect(vi.mocked(createConversation)).toHaveBeenCalledOnce();
    expect(vi.mocked(streamChat)).toHaveBeenCalledWith(
      expect.objectContaining({ content: 'Say hello', conversation_id: 'conv-1' }),
      expect.any(AbortSignal),
    );
  });

  it('navigates to the new conversation before streaming starts', async () => {
    let navigateCallsAtStreamStart: unknown[][] = [];
    vi.mocked(streamChat).mockImplementation(async function* () {
      navigateCallsAtStreamStart = navigateMock.mock.calls.map((call) => [...call]);
      yield {
        type: 'done',
        message: {
          id: 'a1',
          conversation_id: 'conv-1',
          role: 'assistant',
          content: 'Hello world',
          created_at: '2026-01-01T00:00:00Z',
          is_error: false,
        },
      };
    });

    const { result } = renderHook(() => useChat(undefined), { wrapper });

    await act(async () => {
      await result.current.send('Say hello');
    });

    expect(navigateCallsAtStreamStart).toContainEqual(['/chat/conv-1', { replace: true }]);
  });

  it('does not reload messages when the new conversation URL takes effect', async () => {
    vi.mocked(listMessages).mockClear();
    const { result, rerender } = renderHook(({ id }) => useChat(id), {
      initialProps: { id: undefined as string | undefined },
      wrapper,
    });

    await act(async () => {
      await result.current.send('Say hello');
    });
    rerender({ id: 'conv-1' });

    expect(vi.mocked(listMessages)).not.toHaveBeenCalled();
    expect(result.current.messages).toHaveLength(2);
  });

  it('loads existing messages for a conversation', async () => {
    vi.mocked(listMessages).mockResolvedValueOnce({
      items: [
        {
          id: 'm1',
          conversation_id: 'conv-1',
          role: 'user',
          content: 'Old question',
          created_at: '2026-01-01T00:00:00Z',
          is_error: false,
        },
      ],
      total: 1,
      limit: 500,
      offset: 0,
    });

    const { result } = renderHook(() => useChat('conv-1'), { wrapper });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(1);
    });
    expect(result.current.messages[0].content).toBe('Old question');
    expect(result.current.loading).toBe(false);
  });
});
