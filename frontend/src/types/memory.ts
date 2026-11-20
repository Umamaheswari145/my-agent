export type MemoryKind = 'preference' | 'project' | 'fact' | 'instruction';

export interface Memory {
  id: string;
  content: string;
  kind: MemoryKind | string;
  created_at: string;
  updated_at: string;
}
