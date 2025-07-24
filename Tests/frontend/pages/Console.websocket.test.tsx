import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Console from '../../../frontend/src/pages/Console';

vi.mock('../../../frontend/src/state/useLogStore', () => {
  let logs: any[] = [];
  return {
    useLogStore: () => ({
      getLogsByCategory: () => logs,
      clearLogs: () => { logs = []; },
      clearCategory: () => { logs = []; }
    }),
    __setLogs: (newLogs: any[]) => { logs = newLogs; }
  };
});

const logStore = require('../../../frontend/src/state/useLogStore');

describe('Console Page WebSocket', () => {
  beforeEach(() => {
    localStorage.clear();
    logStore.__setLogs([]);
  });

  it('updates logs when new log event is received', async () => {
    logStore.__setLogs([{ timestamp: 'now', module: 'Test', category: 'System', message: 'Hello' }]);
    render(<Console />);
    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeInTheDocument();
    });
  });
}); 