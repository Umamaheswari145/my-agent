import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import {
  ApiError,
  createConversation as apiCreateConversation,
  deleteConversation as apiDeleteConversation,
  listConversations,
  renameConversation as apiRenameConversation,
} from '../services/api';
import type { Conversation } from '../types/chat';
import { storageGet, storageSet } from '../utils/storage';

type Theme = 'light' | 'dark';

interface AppContextValue {
  theme: Theme;
  toggleTheme: () => void;
  conversations: Conversation[];
  conversationsLoading: boolean;
  conversationsError: string | null;
  refreshConversations: () => Promise<void>;
  addConversation: (title?: string) => Promise<Conversation>;
  renameConversation: (id: string, title: string) => Promise<void>;
  removeConversation: (id: string) => Promise<void>;
}

const AppContext = createContext<AppContextValue | null>(null);

function initialTheme(): Theme {
  const stored = storageGet('personal-ai-agent:theme');
  if (stored === 'light' || stored === 'dark') {
    return stored;
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(initialTheme);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationsLoading, setConversationsLoading] = useState(false);
  const [conversationsError, setConversationsError] = useState<string | null>(null);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    storageSet('personal-ai-agent:theme', theme);
  }, [theme]);

  const refreshConversations = useCallback(async () => {
    setConversationsLoading(true);
    setConversationsError(null);
    try {
      const result = await listConversations();
      setConversations(result.items);
    } catch (cause) {
      setConversationsError(
        cause instanceof ApiError
          ? `${cause.message} Check the server configuration.`
          : 'Could not load conversations. Check the server.',
      );
    } finally {
      setConversationsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshConversations();
  }, [refreshConversations]);

  const addConversation = useCallback(async (title?: string) => {
    const created = await apiCreateConversation(title);
    setConversations((current) => [created, ...current]);
    return created;
  }, []);

  const renameConversation = useCallback(async (id: string, title: string) => {
    const updated = await apiRenameConversation(id, title);
    setConversations((current) =>
      current.map((item) => (item.id === id ? updated : item)),
    );
  }, []);

  const removeConversation = useCallback(async (id: string) => {
    await apiDeleteConversation(id);
    setConversations((current) => current.filter((item) => item.id !== id));
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme((current) => (current === 'dark' ? 'light' : 'dark'));
  }, []);

  const value = useMemo<AppContextValue>(
    () => ({
      theme,
      toggleTheme,
      conversations,
      conversationsLoading,
      conversationsError,
      refreshConversations,
      addConversation,
      renameConversation,
      removeConversation,
    }),
    [
      theme,
      toggleTheme,
      conversations,
      conversationsLoading,
      conversationsError,
      refreshConversations,
      addConversation,
      renameConversation,
      removeConversation,
    ],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppContextValue {
  const context = useContext(AppContext);
  if (context === null) {
    throw new Error('useApp must be used inside AppProvider');
  }
  return context;
}
