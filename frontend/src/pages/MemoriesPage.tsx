import { useEffect, useState } from 'react';
import ErrorBanner from '../components/ErrorBanner';
import PageContainer from '../components/PageContainer';
import PageHeader from '../components/PageHeader';
import { CheckIcon, PencilIcon, PlusIcon, TrashIcon } from '../components/Icons';
import { createMemory, deleteMemory, listMemories, updateMemory } from '../services/api';
import type { Memory } from '../types/memory';
import { errorMessage } from '../utils/errors';

const inputClass =
  'w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-sky-400 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-900 dark:focus:border-sky-600';
const KINDS = ['fact', 'preference', 'project', 'instruction'];

export default function MemoriesPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [content, setContent] = useState('');
  const [kind, setKind] = useState('fact');
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const result = await listMemories();
      setMemories(result.items);
    } catch (cause) {
      setError(errorMessage(cause, 'Could not load memories.'));
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleCreate() {
    if (!content.trim()) {
      return;
    }
    try {
      await createMemory(content.trim(), kind);
      setContent('');
      await load();
    } catch (cause) {
      setError(errorMessage(cause, 'Could not add memory.'));
    }
  }

  async function handleUpdate(id: string) {
    if (!draft.trim()) {
      return;
    }
    try {
      await updateMemory(id, draft.trim(), kind);
      setEditing(null);
      await load();
    } catch (cause) {
      setError(errorMessage(cause, 'Could not update memory.'));
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteMemory(id);
      await load();
    } catch (cause) {
      setError(errorMessage(cause, 'Could not delete memory.'));
    }
  }

  return (
    <PageContainer>
        <PageHeader
          title="Memories"
          description="Facts and preferences the assistant can recall in future conversations. Review and remove them at any time."
        />

        {error && <ErrorBanner message={error} className="mb-5" />}

        <section className="mb-6 rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-base font-semibold">Add a memory</h2>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Do not store passwords, API keys, or other sensitive values here.
          </p>
          <div className="mt-4 flex flex-col gap-2 sm:flex-row">
            <input
              value={content}
              onChange={(event) => setContent(event.target.value)}
              placeholder="For example: I prefer concise answers with code examples"
              aria-label="New memory"
              className={inputClass}
            />
            <select
              value={kind}
              onChange={(event) => setKind(event.target.value)}
              aria-label="Memory type"
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
            >
              {KINDS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => void handleCreate()}
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500"
            >
              <PlusIcon className="h-4 w-4" />
              Add
            </button>
          </div>
        </section>

        <div className="space-y-2">
          {memories.length === 0 && (
            <p className="rounded-2xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-400 dark:border-slate-800">
              No memories yet. Useful preferences are also saved automatically from conversations.
            </p>
          )}
          {memories.map((memory) => (
            <div
              key={memory.id}
              className="group flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
            >
              <span className="mt-0.5 rounded-md bg-sky-50 px-2 py-1 text-[11px] font-medium text-sky-700 dark:bg-sky-950 dark:text-sky-300">
                {memory.kind}
              </span>
              {editing === memory.id ? (
                <div className="flex flex-1 flex-col gap-2 sm:flex-row">
                  <input
                    value={draft}
                    onChange={(event) => setDraft(event.target.value)}
                    aria-label="Edit memory"
                    className={inputClass}
                  />
                  <button
                    type="button"
                    onClick={() => void handleUpdate(memory.id)}
                    className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-2 text-sm text-white"
                  >
                    <CheckIcon className="h-4 w-4" />
                    Save
                  </button>
                </div>
              ) : (
                <p className="flex-1 text-sm leading-6 text-slate-700 dark:text-slate-200">
                  {memory.content}
                </p>
              )}
              {editing !== memory.id && (
                <div className="flex shrink-0 gap-1">
                  <button
                    type="button"
                    onClick={() => {
                      setEditing(memory.id);
                      setDraft(memory.content);
                    }}
                    aria-label="Edit memory"
                    className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                  >
                    <PencilIcon className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleDelete(memory.id)}
                    aria-label="Delete memory"
                    className="rounded-lg p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
    </PageContainer>
  );
}
