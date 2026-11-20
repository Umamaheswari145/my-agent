import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import MarkdownContent from './MarkdownContent';

describe('MarkdownContent', () => {
  it('renders GFM headings, lists and code blocks with a copy button', () => {
    render(
      <MarkdownContent
        content={'## Title\n\n- one\n- two\n\n```js\nconst x = 1;\n```'}
      />,
    );

    expect(screen.getByRole('heading', { name: 'Title', level: 2 })).toBeInTheDocument();
    expect(screen.getByText('one')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Copy code' })).toBeInTheDocument();
    expect(screen.getByText('const', { exact: false })).toBeInTheDocument();
  });
});
