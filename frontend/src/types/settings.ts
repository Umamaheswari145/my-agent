export type Verbosity = 'concise' | 'balanced' | 'detailed';

export interface Preferences {
  id: number;
  response_style: string;
  tone: string;
  verbosity: Verbosity;
  extra_instructions: string;
  memory_enabled: boolean;
  updated_at: string;
}

export type PreferencesUpdate = Partial<Pick<Preferences,
  'response_style' | 'tone' | 'verbosity' | 'extra_instructions' | 'memory_enabled'
>>;
