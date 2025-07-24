import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Performance from '../../../frontend/src/pages/Performance';

describe('Performance Page', () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/system_info')) return Promise.resolve({ json: async () => ({ cpu: { brand: 'TestCPU', cores: 4, speed: '3.2' }, osInfo: { distro: 'TestOS', release: '1.0' }, mem: { total: 4096 } }) });
      return Promise.resolve({ json: async () => ({}) });
    }) as any;
    localStorage.clear();
  });

  it('loads and displays system info', async () => {
    render(<Performance />);
    await waitFor(() => {
      expect(screen.getByText(/TestCPU/)).toBeInTheDocument();
      expect(screen.getByText(/TestOS/)).toBeInTheDocument();
    });
  });
}); 