import type { SVGProps } from 'react';

type IconProps = SVGProps<SVGSVGElement>;

function Icon({ children, ...props }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export function PlusIcon(props: IconProps) {
  return <Icon {...props}><path d="M12 5v14M5 12h14" /></Icon>;
}

export function SearchIcon(props: IconProps) {
  return <Icon {...props}><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></Icon>;
}

export function SettingsIcon(props: IconProps) {
  return <Icon {...props}><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6V21h-4v-.1a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.6-1H3v-4h.1a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.6V3h4v.1a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1H21v4h-.1a1.7 1.7 0 0 0-1.5 1Z" /></Icon>;
}

export function SendIcon(props: IconProps) {
  return <Icon {...props}><path d="m5 12 14-7-7 14-2-6-5-1Z" /></Icon>;
}

export function StopIcon(props: IconProps) {
  return <Icon {...props}><rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" stroke="none" /></Icon>;
}

export function CopyIcon(props: IconProps) {
  return <Icon {...props}><rect x="9" y="9" width="11" height="11" rx="2" /><path d="M15 5H6a2 2 0 0 0-2 2v9" /></Icon>;
}

export function CheckIcon(props: IconProps) {
  return <Icon {...props}><path d="m5 12 5 5L20 7" /></Icon>;
}

export function TrashIcon(props: IconProps) {
  return <Icon {...props}><path d="M4 7h16M9 7V5h6v2M6 7l1 13h10l1-13M10 11v6M14 11v6" /></Icon>;
}

export function PencilIcon(props: IconProps) {
  return <Icon {...props}><path d="M4 20h4L20 8l-4-4L4 16v4ZM14 6l4 4" /></Icon>;
}

export function MenuIcon(props: IconProps) {
  return <Icon {...props}><path d="M4 7h16M4 12h16M4 17h16" /></Icon>;
}

export function CloseIcon(props: IconProps) {
  return <Icon {...props}><path d="M6 6l12 12M18 6 6 18" /></Icon>;
}

export function DocumentIcon(props: IconProps) {
  return <Icon {...props}><path d="M6 2h8l4 4v16H6V2ZM14 2v5h5M9 12h6M9 16h6" /></Icon>;
}

export function BookIcon(props: IconProps) {
  return <Icon {...props}><path d="M4 5a2 2 0 0 1 2-2h5v18H6a2 2 0 0 1-2-2V5ZM20 5a2 2 0 0 0-2-2h-5v18h5a2 2 0 0 0 2-2V5ZM11 3v18" /></Icon>;
}

export function SparklesIcon(props: IconProps) {
  return <Icon {...props}><path d="m12 3 1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6L12 3ZM19 16l.7 1.8L21.5 18l-1.8.7L19 20.5l-.7-1.8L16.5 18l1.8-.2L19 16Z" /></Icon>;
}

export function RefreshIcon(props: IconProps) {
  return <Icon {...props}><path d="M20 11a8 8 0 1 0-2.3 6M20 5v6h-6" /></Icon>;
}

export function BrainIcon(props: IconProps) {
  return <Icon {...props}><path d="M9 4a3 3 0 0 0-3 3 3 3 0 0 0-2 5 3 3 0 0 0 2 4 3 3 0 0 0 3 3V4ZM15 4a3 3 0 0 1 3 3 3 3 0 0 1 2 5 3 3 0 0 1-2 4 3 3 0 0 1-3 3V4Z" /></Icon>;
}

export function WarningIcon(props: IconProps) {
  return <Icon {...props}><path d="M12 3 2 20h20L12 3ZM12 9v5M12 17v.01" /></Icon>;
}
