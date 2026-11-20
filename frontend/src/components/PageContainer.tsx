import type { ReactNode } from 'react';

export default function PageContainer({ children }: { children: ReactNode }) {
  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-3xl px-6 py-8">{children}</div>
    </div>
  );
}
