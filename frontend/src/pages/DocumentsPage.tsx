import { useEffect, useState, type ChangeEvent } from 'react';
import ErrorBanner from '../components/ErrorBanner';
import PageContainer from '../components/PageContainer';
import PageHeader from '../components/PageHeader';
import { DocumentIcon, SearchIcon, TrashIcon } from '../components/Icons';
import {
  deleteDocument,
  listDocuments,
  searchDocuments,
  uploadDocument,
} from '../services/api';
import type { DocumentRecord, DocumentSearchResult } from '../types/document';
import { errorMessage } from '../utils/errors';

function formatSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${Math.round(bytes / 1024)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<DocumentSearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const response = await listDocuments();
      setDocuments(response.items);
    } catch (cause) {
      setError(errorMessage(cause, 'Could not load documents.'));
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await uploadDocument(file);
      await load();
    } catch (cause) {
      setError(errorMessage(cause, 'Upload failed.'));
    } finally {
      setBusy(false);
      event.target.value = '';
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteDocument(id);
      await load();
    } catch (cause) {
      setError(errorMessage(cause, 'Could not delete document.'));
    }
  }

  async function handleSearch() {
    if (!query.trim()) {
      return;
    }
    setBusy(true);
    try {
      setResults(await searchDocuments(query.trim(), 5));
    } catch (cause) {
      setError(errorMessage(cause, 'Search failed.'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <PageContainer>
        <PageHeader
          title="Documents"
          description="Upload PDF, TXT, or Markdown files. The assistant can answer questions using their contents and will say when an answer comes from a document."
        />

        {error && <ErrorBanner message={error} className="mb-5" />}

        <section className="mb-6 rounded-2xl border border-dashed border-sky-300 bg-sky-50/50 p-6 text-center dark:border-sky-900 dark:bg-sky-950/20">
          <DocumentIcon className="mx-auto h-7 w-7 text-sky-600 dark:text-sky-400" />
          <p className="mt-2 text-sm font-medium">Upload a document</p>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            PDF, TXT, or Markdown · up to 10 MB
          </p>
          <label className="mt-4 inline-flex cursor-pointer items-center rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500">
            {busy ? 'Processing...' : 'Choose file'}
            <input
              type="file"
              accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown"
              onChange={(event) => void handleUpload(event)}
              className="hidden"
            />
          </label>
        </section>

        <section className="mb-6 rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-base font-semibold">Search documents</h2>
          <div className="mt-3 flex gap-2">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  void handleSearch();
                }
              }}
              placeholder="What would you like to find?"
              aria-label="Document search query"
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-sky-400 dark:border-slate-700 dark:bg-slate-950"
            />
            <button
              type="button"
              onClick={() => void handleSearch()}
              className="inline-flex items-center gap-2 rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 dark:bg-slate-200 dark:text-slate-900"
            >
              <SearchIcon className="h-4 w-4" />
              Search
            </button>
          </div>
          {results.length > 0 && (
            <div className="mt-4 space-y-2">
              {results.map((result, index) => (
                <div
                  key={`${result.document_id}-${result.chunk_index}-${index}`}
                  className="rounded-lg bg-slate-50 p-3 text-sm dark:bg-slate-950/60"
                >
                  <p className="mb-1 text-xs font-medium text-sky-700 dark:text-sky-400">
                    {result.filename} · chunk {result.chunk_index} · score {result.score}
                  </p>
                  <p className="whitespace-pre-wrap leading-6 text-slate-600 dark:text-slate-300">
                    {result.content}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>

        <div className="space-y-2">
          {documents.length === 0 && (
            <p className="rounded-2xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-400 dark:border-slate-800">
              No documents uploaded yet.
            </p>
          )}
          {documents.map((document) => (
            <div
              key={document.id}
              className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
            >
              <DocumentIcon className="h-5 w-5 shrink-0 text-slate-400" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{document.filename}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {formatSize(document.size_bytes)} · {document.chunk_count} chunks · {document.status}
                </p>
                {document.error_message && (
                  <p className="mt-1 text-xs text-rose-600">{document.error_message}</p>
                )}
              </div>
              <button
                type="button"
                onClick={() => void handleDelete(document.id)}
                aria-label={`Delete ${document.filename}`}
                className="rounded-lg p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40"
              >
                <TrashIcon className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
    </PageContainer>
  );
}
