import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import WikiPage from '../../../frontend/src/pages/Wiki';

describe('Wiki Page', () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/modules')) return Promise.resolve({ json: async () => [{ name: 'modA' }] });
      if (url.includes('/api/module_wiki/')) return Promise.resolve({ text: async () => '# Wiki Content' });
      if (url.includes('/api/audio_files')) return Promise.resolve({ json: async () => ['file1.wav'] });
      return Promise.resolve({ json: async () => ({}) });
    }) as any;
    localStorage.clear();
  });

  it('loads and displays module list', async () => {
    render(<WikiPage />);
    await waitFor(() => {
      expect(screen.getByText(/moda/i)).toBeInTheDocument();
    });
  });

  it('loads and displays wiki content', async () => {
    render(<WikiPage />);
    fireEvent.click(screen.getByText(/moda/i));
    await waitFor(() => {
      expect(screen.getByText(/wiki content/i)).toBeInTheDocument();
    });
  });
}); 