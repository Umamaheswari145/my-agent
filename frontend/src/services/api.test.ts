import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, listConversations, streamChat } from './api';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('api client', () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ ok: true })));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.clearAllMocks();
  });

  it('sends the configured access token', async () => {
    vi.stubEnv('VITE_API_ACCESS_TOKEN', 'secret-token');
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse({ items: [], total: 0, limit: 100, offset: 0 }),
    );
    await listConversations('hello', 25, 5);

    const [url, init] = vi.mocked(fetch).mock.calls[0];
    expect(String(url)).toContain('/api/conversations?limit=25&offset=5&query=hello');
    expect((init?.headers as Record<string, string>)['X-API-Key']).toBe('secret-token');
  });

  it('maps backend error bodies to ApiError', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse({ error: { code: 'unauthorized', message: 'Nope' } }, 401),
    );
    await expect(listConversations()).rejects.toMatchObject({
      status: 401,
      code: 'unauthorized',
      message: 'Nope',
    } satisfies Partial<ApiError>);
  });

  it('parses SSE blocks from a stream', async () => {
    const encoder = new TextEncoder();
    const chunks = [
      'event: started\ndata: {"type":"started","conversation_id":"c1","user_message_id":"u1","assistant_message_id":"a1","title":"Hi"}\n\n',
      'event: delta\ndata: {"type":"delta","content":"Hello"}\n\ndata: {"type":"delta","content":" world"}\n\n',
      'event: done\ndata: {"type":"done","message":{"id":"a1","conversation_id":"c1","role":"assistant","content":"Hello world","created_at":"2026-01-01T00:00:00Z","is_error":false}}\n\n',
    ];
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        for (const chunk of chunks) {
          controller.enqueue(encoder.encode(chunk));
        }
        controller.close();
      },
    });
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(stream, { status: 200 })),
    );

    const events = [];
    for await (const event of streamChat({ content: 'hi' })) {
      events.push(event);
    }

    expect(events.map((event) => event.type)).toEqual(['started', 'delta', 'delta', 'done']);
    expect(events[3]).toMatchObject({ message: { content: 'Hello world' } });
  });
});
