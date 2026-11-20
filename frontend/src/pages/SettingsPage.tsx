import { useEffect, useState } from 'react';
import ErrorBanner from '../components/ErrorBanner';
import PageContainer from '../components/PageContainer';
import PageHeader from '../components/PageHeader';
import { CheckIcon } from '../components/Icons';
import { useApp } from '../context/AppContext';
import { getPreferences, updatePreferences } from '../services/api';
import type { Preferences } from '../types/settings';
import { errorMessage } from '../utils/errors';

const inputClass =
  'w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-900 dark:focus:border-sky-600 dark:focus:ring-sky-950';
const labelClass = 'mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300';

export default function SettingsPage() {
  const { theme, toggleTheme } = useApp();
  const [preferences, setPreferences] = useState<Preferences | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getPreferences()
      .then((preferenceResult) => {
        if (!cancelled) {
          setPreferences(preferenceResult);
        }
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setError(errorMessage(cause, 'Could not load settings.'));
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function flash(message: string) {
    setSaved(message);
    window.setTimeout(() => setSaved(null), 2000);
  }

  async function savePreferences() {
    if (!preferences) {
      return;
    }
    try {
      const updated = await updatePreferences({
        response_style: preferences.response_style,
        tone: preferences.tone,
        verbosity: preferences.verbosity,
        extra_instructions: preferences.extra_instructions,
        memory_enabled: preferences.memory_enabled,
      });
      setPreferences(updated);
      flash('Preferences saved');
    } catch (cause) {
      setError(errorMessage(cause, 'Could not save preferences.'));
    }
  }

  return (
    <PageContainer>
        <PageHeader
          title="Settings"
          description="Control appearance, response style, and memory. The access key is loaded from local server setup."
        />

        {error && <ErrorBanner message={error} className="mb-5" />}
        {saved && (
          <div className="mb-5 flex items-center gap-2 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
            <CheckIcon className="h-4 w-4" />
            {saved}
          </div>
        )}

        <section className="mb-6 rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-base font-semibold">Appearance</h2>
          <button
            type="button"
            onClick={toggleTheme}
            className="mt-3 rounded-lg border border-slate-200 px-3 py-2 text-sm hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            Switch to {theme === 'dark' ? 'light' : 'dark'} theme
          </button>
        </section>

        <section className="mb-6 rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-base font-semibold">Response preferences</h2>
          {preferences ? (
            <div className="mt-4 space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className={labelClass} htmlFor="response-style">Response style</label>
                  <input
                    id="response-style"
                    className={inputClass}
                    value={preferences.response_style}
                    onChange={(event) =>
                      setPreferences({ ...preferences, response_style: event.target.value })
                    }
                  />
                </div>
                <div>
                  <label className={labelClass} htmlFor="tone">Tone</label>
                  <input
                    id="tone"
                    className={inputClass}
                    value={preferences.tone}
                    onChange={(event) =>
                      setPreferences({ ...preferences, tone: event.target.value })
                    }
                  />
                </div>
              </div>
              <div>
                <label className={labelClass} htmlFor="verbosity">Answer length</label>
                <select
                  id="verbosity"
                  className={inputClass}
                  value={preferences.verbosity}
                  onChange={(event) =>
                    setPreferences({
                      ...preferences,
                      verbosity: event.target.value as Preferences['verbosity'],
                    })
                  }
                >
                  <option value="concise">Concise</option>
                  <option value="balanced">Balanced</option>
                  <option value="detailed">Detailed</option>
                </select>
              </div>
              <div>
                <label className={labelClass} htmlFor="extra-instructions">
                  Additional instructions
                </label>
                <textarea
                  id="extra-instructions"
                  rows={3}
                  className={inputClass}
                  value={preferences.extra_instructions}
                  onChange={(event) =>
                    setPreferences({ ...preferences, extra_instructions: event.target.value })
                  }
                  placeholder="For example: always show a short summary at the end."
                />
              </div>
              <label className="flex items-center gap-3 text-sm text-slate-700 dark:text-slate-300">
                <input
                  type="checkbox"
                  checked={preferences.memory_enabled}
                  onChange={(event) =>
                    setPreferences({ ...preferences, memory_enabled: event.target.checked })
                  }
                  className="h-4 w-4 rounded border-slate-300 text-sky-600"
                />
                Enable long-term memory
              </label>
              <button
                type="button"
                onClick={() => void savePreferences()}
                className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500"
              >
                Save preferences
              </button>
            </div>
          ) : (
            <p className="mt-3 text-sm text-slate-400">Loading preferences...</p>
          )}
        </section>
    </PageContainer>
  );
}
