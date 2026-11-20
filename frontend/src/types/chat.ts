export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export type MessageRole = 'user' | 'assistant' | 'system' | 'tool';

export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  created_at: string;
  tool_name?: string | null;
  is_error: boolean;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface ChatRequest {
  content: string;
  conversation_id?: string | null;
  regenerate_of?: string | null;
  use_web_search?: boolean;
}

export interface ChatStarted {
  type: 'started';
  conversation_id: string;
  user_message_id: string;
  assistant_message_id: string;
  title: string;
}

export interface ChatDelta {
  type: 'delta';
  content: string;
}

export interface ChatDone {
  type: 'done';
  message: Message;
}

export interface ChatError {
  type: 'error';
  code: string;
  message: string;
}

export type ChatEvent = ChatStarted | ChatDelta | ChatDone | ChatError;
