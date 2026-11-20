export interface DocumentRecord {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  status: 'processing' | 'ready' | 'failed';
  chunk_count: number;
  error_message: string | null;
  created_at: string;
}

export interface DocumentSearchResult {
  document_id: string;
  filename: string;
  chunk_index: number;
  content: string;
  score: number;
}
