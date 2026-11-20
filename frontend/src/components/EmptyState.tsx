import { SparklesIcon } from './Icons';

const SUGGESTIONS = [
  {
    title: 'Explain a concept',
    prompt: 'Explain how vector databases work in simple English, with an example.',
  },
  {
    title: 'Debug code',
    prompt: 'Help me debug a Python function that returns the wrong result. I will paste the code.',
  },
  {
    title: 'Write professionally',
    prompt: 'Draft a short, professional email asking for a project status update.',
  },
  {
    title: 'Plan learning',
    prompt: 'Create a 4-week learning roadmap for SQL, starting from zero.',
  },
];

export default function EmptyState({ onPick }: { onPick: (prompt: string) => void }) {
  return (
    <div className="flex flex-1 items-center justify-center overflow-y-auto px-4 py-10">
      <div className="w-full max-w-2xl text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500 to-indigo-600 text-white shadow-lg shadow-sky-200/50 dark:shadow-none">
          <SparklesIcon className="h-7 w-7" />
        </div>
        <h1 className="mt-5 text-3xl font-semibold tracking-tight text-slate-800 dark:text-slate-100">
          How can I help?
        </h1>
        <p className="mx-auto mt-2 max-w-lg text-[15px] leading-7 text-slate-500 dark:text-slate-400">
          Ask a question, paste code, upload a document, or describe a task. I remember useful context
          between conversations and answer honestly when I am unsure.
        </p>
        <div className="mt-8 grid gap-3 sm:grid-cols-2">
          {SUGGESTIONS.map((suggestion) => (
            <button
              key={suggestion.title}
              type="button"
              onClick={() => onPick(suggestion.prompt)}
              className="rounded-2xl border border-slate-200 bg-white p-4 text-left transition hover:border-sky-300 hover:shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:hover:border-sky-800"
            >
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                {suggestion.title}
              </p>
              <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
                {suggestion.prompt}
              </p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
