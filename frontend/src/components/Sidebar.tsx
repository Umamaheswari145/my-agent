import { useMemo, useState, type ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { errorMessage } from '../utils/errors';
import {
  BookIcon,
  BrainIcon,
  CloseIcon,
  DocumentIcon,
  PencilIcon,
  PlusIcon,
  SearchIcon,
  SettingsIcon,
  SparklesIcon,
  TrashIcon,
} from './Icons';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

interface SidebarNavLinkProps {
  to: string;
  onClose: () => void;
  icon: ReactNode;
  children: ReactNode;
}

function SidebarNavLink({ to, onClose, icon, children }: SidebarNavLinkProps) {
  return (
    <NavLink
      to={to}
      onClick={onClose}
      className={({ isActive }) =>
        `flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${
          isActive
            ? 'bg-slate-200 font-medium text-slate-900 dark:bg-slate-800 dark:text-white'
            : 'text-slate-600 hover:bg-slate-200/70 dark:text-slate-300 dark:hover:bg-slate-800'
        }`
      }
    >
      {icon}
      {children}
    </NavLink>
  );
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  const navigate = useNavigate();
  const {
    conversations,
    conversationsLoading,
    conversationsError,
    addConversation,
    renameConversation,
    removeConversation,
  } = useApp();
  const [search, setSearch] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) {
      return conversations;
    }
    return conversations.filter((item) => item.title.toLowerCase().includes(term));
  }, [conversations, search]);

  async function handleNewChat() {
    setActionError(null);
    try {
      const created = await addConversation();
      onClose();
      navigate(`/chat/${created.id}`);
    } catch (cause) {
      setActionError(errorMessage(cause, 'Could not create a new chat.'));
    }
  }

  async function saveRename(id: string) {
    const title = draft.trim();
    setEditingId(null);
    if (title) {
      await renameConversation(id, title);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm('Delete this conversation? This cannot be undone.')) {
      return;
    }
    await removeConversation(id);
  }

  return (
    <>
      {open && (
        <button
          type="button"
          aria-label="Close sidebar"
          onClick={onClose}
          className="fixed inset-0 z-20 bg-slate-950/50 lg:hidden"
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-30 flex w-72 flex-col border-r border-slate-200 bg-slate-50 transition-transform dark:border-slate-800 dark:bg-slate-900/95 lg:static lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between px-4 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600 text-white shadow-sm">
              <SparklesIcon className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold leading-tight text-slate-800 dark:text-slate-100">
                AI Agent
              </p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">Your private assistant</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-200 dark:text-slate-400 dark:hover:bg-slate-800 lg:hidden"
            aria-label="Close sidebar"
          >
            <CloseIcon className="h-5 w-5" />
          </button>
        </div>

        <div className="px-3">
          <button
            type="button"
            onClick={() => void handleNewChat()}
            className="flex w-full items-center gap-2 rounded-xl bg-sky-600 px-3 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-sky-500"
          >
            <PlusIcon className="h-4 w-4" />
            New chat
          </button>
          {actionError && (
            <p className="px-1 pt-2 text-xs leading-5 text-rose-600 dark:text-rose-400">
              {actionError}
            </p>
          )}
        </div>

        <div className="px-3 pt-3">
          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-950/60">
            <SearchIcon className="h-4 w-4 shrink-0 text-slate-400" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search conversations"
              aria-label="Search conversations"
              className="w-full bg-transparent text-sm text-slate-700 outline-none placeholder:text-slate-400 dark:text-slate-200"
            />
          </div>
        </div>

        <nav className="mt-4 flex-1 overflow-y-auto px-3" aria-label="Conversations">
          <p className="px-2 pb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            Recent
          </p>
          {conversationsLoading && <p className="px-2 text-sm text-slate-400">Loading...</p>}
          {conversationsError && (
            <p className="px-2 text-xs leading-5 text-rose-600 dark:text-rose-400">
              {conversationsError}
            </p>
          )}
          {!conversationsLoading && filtered.length === 0 && (
            <p className="px-2 text-sm text-slate-400">
              {search ? 'No matching conversations' : 'No conversations yet'}
            </p>
          )}
          <div className="space-y-0.5">
            {filtered.map((conversation) => (
              <div
                key={conversation.id}
                className="group flex items-center gap-1 rounded-lg transition hover:bg-slate-200/70 dark:hover:bg-slate-800"
              >
                {editingId === conversation.id ? (
                  <input
                    autoFocus
                    value={draft}
                    onChange={(event) => setDraft(event.target.value)}
                    onBlur={() => void saveRename(conversation.id)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') {
                        void saveRename(conversation.id);
                      }
                      if (event.key === 'Escape') {
                        setEditingId(null);
                      }
                    }}
                    aria-label="Rename conversation"
                    className="m-1 w-full rounded-md border border-sky-400 bg-white px-2 py-1 text-sm outline-none dark:bg-slate-950"
                  />
                ) : (
                  <NavLink
                    to={`/chat/${conversation.id}`}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `min-w-0 flex-1 truncate px-3 py-2 text-sm ${
                        isActive
                          ? 'font-medium text-sky-700 dark:text-sky-300'
                          : 'text-slate-600 dark:text-slate-300'
                      }`
                    }
                  >
                    {conversation.title}
                  </NavLink>
                )}
                {editingId !== conversation.id && (
                  <div className="flex pr-1 opacity-0 transition group-hover:opacity-100 focus-within:opacity-100">
                    <button
                      type="button"
                      aria-label={`Rename ${conversation.title}`}
                      onClick={() => {
                        setEditingId(conversation.id);
                        setDraft(conversation.title);
                      }}
                      className="rounded-md p-1.5 text-slate-500 hover:bg-slate-300 dark:text-slate-400 dark:hover:bg-slate-700"
                    >
                      <PencilIcon className="h-3.5 w-3.5" />
                    </button>
                    <button
                      type="button"
                      aria-label={`Delete ${conversation.title}`}
                      onClick={() => void handleDelete(conversation.id)}
                      className="rounded-md p-1.5 text-slate-500 hover:bg-rose-100 hover:text-rose-600 dark:text-slate-400 dark:hover:bg-rose-950/50"
                    >
                      <TrashIcon className="h-3.5 w-3.5" />
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </nav>

        <div className="border-t border-slate-200 px-3 py-3 dark:border-slate-800">
          <div className="grid grid-cols-2 gap-1">
            <SidebarNavLink to="/memories" onClose={onClose} icon={<BrainIcon className="h-4 w-4" />}>
              Memories
            </SidebarNavLink>
            <SidebarNavLink to="/documents" onClose={onClose} icon={<DocumentIcon className="h-4 w-4" />}>
              Documents
            </SidebarNavLink>
            <SidebarNavLink to="/guide" onClose={onClose} icon={<BookIcon className="h-4 w-4" />}>
              Guide
            </SidebarNavLink>
            <SidebarNavLink to="/settings" onClose={onClose} icon={<SettingsIcon className="h-4 w-4" />}>
              Settings
            </SidebarNavLink>
          </div>
        </div>
      </aside>
    </>
  );
}
