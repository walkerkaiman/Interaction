import React from 'react';
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ModuleSettingsForm from '../../../frontend/src/components/ModuleSettingsForm';

describe('ModuleSettingsForm', () => {
  const manifest = {
    name: 'TestModule',
    fields: [
      { type: 'text', name: 'paramA', label: 'Param A' },
      { type: 'number', name: 'paramB', label: 'Param B' },
      { type: 'slider', name: 'paramC', label: 'Param C', min: 0, max: 10, step: 1 },
      { type: 'filepath', name: 'file_path', label: 'Audio File' },
      { type: 'waveform', name: 'waveform', label: 'Waveform' },
      { type: 'time', name: 'paramTime', label: 'Time' }
    ]
  };
  const config = { paramA: 'foo', paramB: 42, paramC: 5, file_path: 'test.wav', waveform: '', paramTime: '12:00' };

  beforeEach(() => {
    global.fetch = vi.fn()
      .mockImplementation((url: string) => {
        if (url.includes('/api/audio_files')) {
          return Promise.resolve({ ok: true, json: async () => ['test.wav', 'other.wav'] });
        }
        if (url.includes('/modules/') && url.includes('/settings')) {
          return Promise.resolve({ ok: true });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }) as any;
  });

  it('renders all field types', () => {
    render(<ModuleSettingsForm manifest={manifest} config={config} moduleId="testmod" />);
    expect(screen.getByLabelText(/param a/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/param b/i)).toBeInTheDocument();
    expect(screen.getByText(/param c/i)).toBeInTheDocument();
    expect(screen.getByText(/audio file/i)).toBeInTheDocument();
    expect(screen.getByText(/waveform/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/time/i)).toBeInTheDocument();
  });

  it('calls onConfigChange when a field is changed', () => {
    const onConfigChange = vi.fn();
    render(<ModuleSettingsForm manifest={manifest} config={config} moduleId="testmod" onConfigChange={onConfigChange} />);
    fireEvent.change(screen.getByLabelText(/param a/i), { target: { value: 'bar' } });
    expect(onConfigChange).toHaveBeenCalledWith(expect.objectContaining({ paramA: 'bar' }));
  });

  it('persists changes via fetch when persistOnChange is true', async () => {
    render(<ModuleSettingsForm manifest={manifest} config={config} moduleId="testmod" persistOnChange={true} />);
    fireEvent.change(screen.getByLabelText(/param a/i), { target: { value: 'bar' } });
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/modules/testmod/settings'), expect.any(Object));
    });
  });

  it('handles audio file fetch and upload', async () => {
    render(<ModuleSettingsForm manifest={manifest} config={config} moduleId="testmod" />);
    expect(await screen.findByText('test.wav')).toBeInTheDocument();
    // Simulate drop event for upload (skip actual file upload logic)
    // Could add more detailed upload simulation if needed
  });

  it('handles error state for audio file fetch', async () => {
    (global.fetch as any).mockImplementationOnce(() => Promise.resolve({ ok: false }));
    render(<ModuleSettingsForm manifest={manifest} config={config} moduleId="testmod" />);
    expect(await screen.findByText(/error loading audio files/i)).toBeInTheDocument();
  });

  it('renders waveform preview if file_path is set', () => {
    render(<ModuleSettingsForm manifest={manifest} config={{ ...config, file_path: 'test.wav' }} moduleId="testmod" />);
    expect(screen.getByAltText('Waveform')).toBeInTheDocument();
  });

  it('handles empty/malformed manifest gracefully', () => {
    render(<ModuleSettingsForm manifest={{ name: 'Empty', fields: [] }} config={{}} moduleId="testmod" />);
    expect(screen.getByText(/empty settings/i)).toBeInTheDocument();
  });
}); 