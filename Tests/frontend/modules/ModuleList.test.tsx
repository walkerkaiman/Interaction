import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ModuleList from '../../../frontend/src/components/ModuleList';

describe('ModuleList', () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({
      json: async () => [
        { name: 'osc_input' },
        { name: 'audio_output' },
        { name: 'dmx_output' }
      ]
    }) as any;
  });

  it('renders all modules from API', async () => {
    render(<ModuleList />);
    await waitFor(() => {
      expect(screen.getByText('osc_input')).toBeInTheDocument();
      expect(screen.getByText('audio_output')).toBeInTheDocument();
      expect(screen.getByText('dmx_output')).toBeInTheDocument();
    });
  });

  it('renders empty list if no modules', async () => {
    (global.fetch as any).mockResolvedValueOnce({ json: async () => [] });
    render(<ModuleList />);
    await waitFor(() => {
      expect(screen.queryAllByRole('listitem').length).toBe(0);
    });
  });

  it('handles fetch failure gracefully', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('fail'));
    render(<ModuleList />);
    // Should not throw, but nothing rendered
    await waitFor(() => {
      expect(screen.queryAllByRole('listitem').length).toBe(0);
    });
  });
}); 