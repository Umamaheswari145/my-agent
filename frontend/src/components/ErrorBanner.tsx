import type { ReactNode } from 'react';
import { WarningIcon } from './Icons';

interface ErrorBannerProps {
  message: string;
  className?: string;
  action?: ReactNode;
}

export default function ErrorBanner({ message, className = '', action }: ErrorBannerProps) {
  return (
    <div
      className={`flex items-start gap-2 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:bg-rose-950/40 dark:text-rose-300 ${className}`}
    >
      <WarningIcon className="mt-0.5 h-4 w-4 shrink-0" />
      <span className="flex-1">{message}</span>
      {action}
    </div>
  );
}
