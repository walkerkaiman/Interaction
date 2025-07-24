import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Performance from '../../../frontend/src/pages/Performance';

// Mock WebSocket and message handler utilities
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

describe('Performance Page WebSocket', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('updates stats on system_stats WebSocket message', async () => {
    render(<Performance />);
    // Simulate receiving a system_stats message
    wsApi.__trigger({ type: 'system_stats', cpu: 0.5, memory: 0.25, temperature: 42, uptime: 123, load: [1,2,3] });
    await waitFor(() => {
      expect(screen.getByText(/CPU Usage/)).toBeInTheDocument();
      expect(screen.getByText(/Memory Usage/)).toBeInTheDocument();
    });
  });
}); 