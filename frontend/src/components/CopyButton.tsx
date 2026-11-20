import { useState } from 'react';
import { CheckIcon, CopyIcon } from './Icons';
import { copyText } from '../utils/clipboard';

interface CopyButtonProps {
  text: string;
  ariaLabel: string;
  className: string;
}

export default function CopyButton({ text, ariaLabel, className }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    const ok = await copyText(text);
    if (!ok) {
      return;
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  return (
    <button type="button" onClick={() => void handleCopy()} className={className} aria-label={ariaLabel}>
      {copied ? <CheckIcon className="h-3.5 w-3.5" /> : <CopyIcon className="h-3.5 w-3.5" />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  );
}
