import { isValidElement, type ReactNode } from 'react';
import ReactMarkdown, { type Components } from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';
import CopyButton from './CopyButton';

function nodeText(node: ReactNode): string {
  if (typeof node === 'string' || typeof node === 'number') {
    return String(node);
  }
  if (Array.isArray(node)) {
    return node.map(nodeText).join('');
  }
  if (isValidElement<{ children?: ReactNode }>(node)) {
    return nodeText(node.props.children);
  }
  return '';
}

const components: Components = {
  pre({ children }) {
    const code = nodeText(children).replace(/\n$/, '');
    return (
      <div className="group/code relative my-3 overflow-hidden rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-950/60">
        <CopyButton
          text={code}
          ariaLabel="Copy code"
          className="absolute right-2 top-2 inline-flex items-center gap-1 rounded-md bg-white/90 px-2 py-1 text-xs font-medium text-slate-600 opacity-60 shadow-sm transition hover:opacity-100 dark:bg-slate-800/90 dark:text-slate-300"
        />
        <pre className="overflow-x-auto p-4 pt-10 text-[13px] leading-relaxed">{children}</pre>
      </div>
    );
  },
  a({ href, children }) {
    return (
      <a href={href} target="_blank" rel="noreferrer" className="text-sky-600 underline decoration-sky-300 underline-offset-2 hover:text-sky-700 dark:text-sky-400 dark:decoration-sky-700">
        {children}
      </a>
    );
  },
  ul({ children }) {
    return <ul className="my-2 list-disc space-y-1 pl-5">{children}</ul>;
  },
  ol({ children }) {
    return <ol className="my-2 list-decimal space-y-1 pl-5">{children}</ol>;
  },
  h1({ children }) {
    return <h1 className="mb-2 mt-4 text-xl font-semibold">{children}</h1>;
  },
  h2({ children }) {
    return <h2 className="mb-2 mt-4 text-lg font-semibold">{children}</h2>;
  },
  h3({ children }) {
    return <h3 className="mb-1 mt-3 text-base font-semibold">{children}</h3>;
  },
  p({ children }) {
    return <p className="my-2 leading-7">{children}</p>;
  },
  table({ children }) {
    return (
      <div className="my-3 overflow-x-auto">
        <table className="w-full border-collapse text-sm">{children}</table>
      </div>
    );
  },
  th({ children }) {
    return <th className="border border-slate-200 px-3 py-1.5 text-left font-semibold dark:border-slate-700">{children}</th>;
  },
  td({ children }) {
    return <td className="border border-slate-200 px-3 py-1.5 dark:border-slate-700">{children}</td>;
  },
};

export default function MarkdownContent({ content }: { content: string }) {
  return (
    <div className="text-[15px] text-slate-700 dark:text-slate-200">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
