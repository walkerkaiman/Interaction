import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import NodeMap from '../../../frontend/src/components/NodeMap';

describe('NodeMap', () => {
  beforeEach(() => {
    global.fetch = vi.fn()
      .mockImplementationOnce(() => Promise.resolve({ json: async () => [
        { name: 'osc_input' },
        { name: 'audio_output' },
        { name: 'dmx_output' }
      ] }))
      .mockImplementationOnce(() => Promise.resolve({ json: async () => [
        { input: { module: 'osc_input' }, output: { module: 'audio_output' } },
        { input: { module: 'osc_input' }, output: { module: 'dmx_output' } }
      ] }));
  });

  it('renders modules and interactions from API', async () => {
    render(<NodeMap />);
    await waitFor(() => {
      expect(screen.getByText('osc_input')).toBeInTheDocument();
      expect(screen.getByText('audio_output')).toBeInTheDocument();
      expect(screen.getByText('dmx_output')).toBeInTheDocument();
      expect(screen.getByText(/osc_input.* 2.*audio_output/)).toBeInTheDocument();
      expect(screen.getByText(/osc_input.* 2.*dmx_output/)).toBeInTheDocument();
    });
  });

  it('renders empty state if no modules or interactions', async () => {
    (global.fetch as any)
      .mockImplementationOnce(() => Promise.resolve({ json: async () => [] }))
      .mockImplementationOnce(() => Promise.resolve({ json: async () => [] }));
    render(<NodeMap />);
    await waitFor(() => {
      expect(screen.queryByText(/→/)).not.toBeInTheDocument();
    });
  });

  it('handles fetch failure gracefully', async () => {
    (global.fetch as any)
      .mockRejectedValueOnce(new Error('fail'))
      .mockRejectedValueOnce(new Error('fail'));
    render(<NodeMap />);
    await waitFor(() => {
      expect(screen.queryByText(/→/)).not.toBeInTheDocument();
    });
  });
}); 