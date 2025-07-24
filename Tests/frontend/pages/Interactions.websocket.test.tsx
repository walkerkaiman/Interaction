import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Interactions from '../../../frontend/src/pages/Interactions';

vi.mock('../../../frontend/src/api/ws', () => {
  let handler: any = null;
  return {
    connectWebSocket: vi.fn(),
    addMessageHandler: (cb: any) => { handler = cb; },
    removeMessageHandler: vi.fn(),
    __trigger: (msg: any) => handler && handler(msg)
  };
});

const wsApi = require('../../../frontend/src/api/ws');

describe('Interactions Page WebSocket', () => {
  beforeEach(() => {
    localStorage.clear();
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/modules')) return Promise.resolve({ json: async () => [{ name: 'inputA' }, { name: 'outputB' }] });
      if (url.includes('/api/interactions')) return Promise.resolve({ json: async () => [{ input: { module: 'inputA' }, output: { module: 'outputB' } }] });
      return Promise.resolve({ json: async () => ({}) });
    }) as any;
  });

  it('updates modules on all_modules WebSocket message', async () => {
    render(<Interactions />);
    wsApi.__trigger({ type: 'all_modules', modules: [{ id: 'inputA', config: {} }, { id: 'outputB', config: {} }] });
    await waitFor(() => {
      expect(screen.getByText('inputA')).toBeInTheDocument();
      expect(screen.getByText('outputB')).toBeInTheDocument();
    });
  });
}); 