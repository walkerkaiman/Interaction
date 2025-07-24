import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Console from '../../../frontend/src/pages/Console';

describe('Console Page', () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({ json: async () => ['System', 'Error'] }) as any;
    localStorage.clear();
    vi.resetModules();
  });

  it('loads and displays log levels', async () => {
    render(<Console />);
    await waitFor(() => {
      expect(screen.getByText('System')).toBeInTheDocument();
      expect(screen.getByText('Error')).toBeInTheDocument();
    });
  });

  it('persists selected category in localStorage', async () => {
    render(<Console />);
    fireEvent.change(screen.getByLabelText(/log category/i), { target: { value: 'System' } });
    await waitFor(() => {
      expect(localStorage.getItem('consoleCategory')).toBe('System');
    });
  });
}); 