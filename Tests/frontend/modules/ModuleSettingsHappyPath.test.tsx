import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import ModuleSettingsForm from '../../../frontend/src/components/ModuleSettingsForm';

describe('ModuleSettingsForm Happy Path', () => {
  it('calls onChange with new value when a setting is changed', async () => {
    const user = userEvent.setup();
    const sampleConfig = { paramA: 'foo', paramB: 42 };
    const mockManifest = {
      name: 'TestModule',
      fields: [
        { type: 'text', name: 'paramA', label: 'Param A' },
        { type: 'number', name: 'paramB', label: 'Param B' }
      ]
    };
    const handleChange = vi.fn();
    render(<ModuleSettingsForm manifest={mockManifest} config={sampleConfig} onChange={handleChange} />);
    const input = screen.getByLabelText(/param a/i);
    await user.clear(input);
    await user.type(input, 'bar');
    expect(handleChange).toHaveBeenCalledWith({ ...sampleConfig, paramA: 'bar' });
  });
}); 