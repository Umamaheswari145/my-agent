import type { ChatEvent, ChatRequest, Conversation, Message, Paginated } from '../types/chat';
import type { DocumentRecord, DocumentSearchResult } from '../types/document';
import type { Memory } from '../types/memory';
import type { Preferences, PreferencesUpdate } from '../types/settings';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

interface ErrorBody {
  error?: { code?: string; message?: string };
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

function headers(): Record<string, string> {
  const result: Record<string, string> = { Accept: 'application/json' };
  const token = import.meta.env.VITE_API_ACCESS_TOKEN ?? '';
  if (token) {
    result['X-API-Key'] = token;
  }
  return result;
}

async function parseError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as ErrorBody;
    return new ApiError(
      response.status,
      body.error?.code ?? 'request_failed',
      body.error?.message ?? `Request failed with status ${response.status}`,
    );
  } catch {
    return new ApiError(response.status, 'request_failed', `Request failed with status ${response.status}`);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { ...headers(), ...init?.headers },
  });
  if (!response.ok) {
    throw await parseError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

function jsonInit(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  };
}

export function listConversations(
  query = '',
  limit = 100,
  offset = 0,
): Promise<Paginated<Conversation>> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (query) {
    params.set('query', query);
  }
  return request<Paginated<Conversation>>(`/api/conversations?${params.toString()}`);
}

export function createConversation(title?: string): Promise<Conversation> {
  return request<Conversation>('/api/conversations', jsonInit('POST', { title }));
}

export function renameConversation(id: string, title: string): Promise<Conversation> {
  return request<Conversation>(`/api/conversations/${id}`, jsonInit('PATCH', { title }));
}

export function deleteConversation(id: string): Promise<void> {
  return request<void>(`/api/conversations/${id}`, { method: 'DELETE' });
}

export function listMessages(
  conversationId: string,
  limit = 500,
): Promise<Paginated<Message>> {
  return request<Paginated<Message>>(
    `/api/conversations/${conversationId}/messages?limit=${limit}`,
  );
}

export async function* streamChat(
  payload: ChatRequest,
  signal?: AbortSignal,
): AsyncGenerator<ChatEvent> {
  const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: 'POST',
    headers: { ...headers(), 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  });
  if (!response.ok) {
    throw await parseError(response);
  }
  if (!response.body) {
    throw new ApiError(500, 'stream_unavailable', 'Streaming is not supported by this browser.');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n');
      let boundary = buffer.indexOf('\n\n');
      while (boundary !== -1) {
        const block = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const dataLine = block.split('\n').find((line) => line.startsWith('data:'));
        if (dataLine) {
          yield JSON.parse(dataLine.slice(5).trim()) as ChatEvent;
        }
        boundary = buffer.indexOf('\n\n');
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export function listMemories(): Promise<Paginated<Memory>> {
  return request<Paginated<Memory>>('/api/memories?limit=200');
}

export async function createMemory(content: string, kind: string): Promise<Memory> {
  return request<Memory>('/api/memories', jsonInit('POST', { content, kind }));
}

export async function updateMemory(id: string, content: string, kind: string): Promise<Memory> {
  return request<Memory>(`/api/memories/${id}`, jsonInit('PATCH', { content, kind }));
}

export function deleteMemory(id: string): Promise<void> {
  return request<void>(`/api/memories/${id}`, { method: 'DELETE' });
}

export function getPreferences(): Promise<Preferences> {
  return request<Preferences>('/api/preferences');
}

export function updatePreferences(changes: PreferencesUpdate): Promise<Preferences> {
  return request<Preferences>('/api/preferences', jsonInit('PATCH', changes));
}

export function listDocuments(): Promise<Paginated<DocumentRecord>> {
  return request<Paginated<DocumentRecord>>('/api/documents?limit=200');
}

export async function uploadDocument(file: File): Promise<DocumentRecord> {
  const body = new FormData();
  body.append('file', file);
  return request<DocumentRecord>('/api/documents', {
    method: 'POST',
    body,
  });
}

export function deleteDocument(id: string): Promise<void> {
  return request<void>(`/api/documents/${id}`, { method: 'DELETE' });
}

export function searchDocuments(
  query: string,
  limit = 5,
): Promise<DocumentSearchResult[]> {
  return request<DocumentSearchResult[]>('/api/documents/search', jsonInit('POST', { query, limit }));
}
