import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import InteractionEditor from '../../../frontend/src/pages/InteractionEditor';

describe('InteractionEditor Page', () => {
  beforeEach(() => {
    vi.resetModules();
    localStorage.clear();
  });

  it('renders settings form for selected module', async () => {
    // Mock useModulesStore
    vi.mock('../../../frontend/src/state/useModulesStore', () => ({
      useModulesStore: () => ({
        availableModules: [{ name: 'modA', manifest: { name: 'modA', fields: [] } }],
        modules: { modA: { config: {} } },
        fetchAvailableModules: vi.fn()
      })
    }));
    render(<InteractionEditor />);
    fireEvent.change(screen.getByLabelText(/select module/i), { target: { value: 'modA' } });
    await waitFor(() => {
      expect(screen.getByText(/moda settings/i)).toBeInTheDocument();
    });
  });

  it('handles no modules available', async () => {
    vi.mock('../../../frontend/src/state/useModulesStore', () => ({
      useModulesStore: () => ({
        availableModules: [],
        modules: {},
        fetchAvailableModules: vi.fn()
      })
    }));
    render(<InteractionEditor />);
    expect(screen.getByText(/select a module to configure/i)).toBeInTheDocument();
  });
}); 