import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(
          JSON.stringify({ items: [], total: 0, limit: 100, offset: 0 }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    );
  });

  it('renders the chat home page', async () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { name: /how can i help/i })).toBeInTheDocument();
  });

  it('renders the guide page', async () => {
    render(
      <MemoryRouter initialEntries={['/guide']}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { name: 'Guide', level: 1 })).toBeInTheDocument();
    expect(screen.getByText(/1\. Start a chat/)).toBeInTheDocument();
  });

  it('renders a conversation page when loaded directly from its URL', async () => {
    render(
      <MemoryRouter initialEntries={['/chat/conv-1']}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { name: /how can i help/i })).toBeInTheDocument();
    expect(screen.queryByText('Page not found')).not.toBeInTheDocument();
  });
});
