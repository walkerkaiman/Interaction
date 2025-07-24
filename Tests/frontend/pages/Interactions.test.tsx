import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Interactions from '../../../frontend/src/pages/Interactions';
import { vi } from 'vitest';

// Mock fetch for module manifests and registration
beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async (url, options) => {
    if (url === '/modules') {
      return {
        ok: true,
        json: async () => ([
          {
            name: 'time_input',
            manifest: {
              name: 'Time Input',
              fields: [
                { name: 'target_time', type: 'time', label: 'Target Time', default: '12:00:00' }
              ]
            }
          },
          {
            name: 'audio_output',
            manifest: {
              name: 'Audio Output',
              fields: [
                { name: 'file_path', type: 'text', label: 'File Path', default: '' },
                { name: 'volume', type: 'number', label: 'Volume', default: 80 }
              ]
            }
          }
        ])
      };
    }
    if (url === '/api/interactions') {
      // Only succeed if valid
      if (options && options.body && options.body.includes('12:00:00')) {
        return { ok: true, json: async () => ({}) };
      }
      return { ok: false };
    }
    return { ok: true, json: async () => ({}) };
  }));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('Interactions page validation', () => {
  it('shows error snackbar and does not clear form on invalid input', async () => {
    render(<Interactions />);
    // Click Add New Interaction
    fireEvent.click(screen.getByText('Add New Interaction'));
    // Select input module
    fireEvent.mouseDown(screen.getByLabelText('Select Input Module'));
    fireEvent.click(await screen.findByText('Time Input'));
    // Leave target_time empty (invalid)
    // Select output module
    fireEvent.mouseDown(screen.getByLabelText('Select Output Module'));
    fireEvent.click(await screen.findByText('Audio Output'));
    // Fill output fields
    fireEvent.change(screen.getByLabelText('File Path'), { target: { value: 'test.wav' } });
    fireEvent.change(screen.getByLabelText('Volume'), { target: { value: '80' } });
    // Click Register
    fireEvent.click(screen.getByText('Register'));
    // Should show error snackbar
    await waitFor(() => {
      expect(screen.getByText(/Input module \(Time Input\):/)).toBeInTheDocument();
      expect(screen.getByText(/Target Time is required/)).toBeInTheDocument();
    });
    // The form should still have the values
    expect(screen.getByLabelText('File Path')).toHaveValue('test.wav');
    expect(screen.getByLabelText('Volume')).toHaveValue(80);
  });

  it('registers interaction and shows success snackbar on valid input', async () => {
    render(<Interactions />);
    fireEvent.click(screen.getByText('Add New Interaction'));
    // Select input module
    fireEvent.mouseDown(screen.getByLabelText('Select Input Module'));
    fireEvent.click(await screen.findByText('Time Input'));
    // Fill target_time
    fireEvent.change(screen.getByLabelText('Target Time'), { target: { value: '12:00:00' } });
    // Select output module
    fireEvent.mouseDown(screen.getByLabelText('Select Output Module'));
    fireEvent.click(await screen.findByText('Audio Output'));
    // Fill output fields
    fireEvent.change(screen.getByLabelText('File Path'), { target: { value: 'test.wav' } });
    fireEvent.change(screen.getByLabelText('Volume'), { target: { value: '80' } });
    // Click Register
    fireEvent.click(screen.getByText('Register'));
    // Should show success snackbar
    await waitFor(() => {
      expect(screen.getByText('Interaction registered!')).toBeInTheDocument();
    });
  });
}); 