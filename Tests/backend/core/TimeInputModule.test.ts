import { describe, it, expect, beforeEach, vi } from 'vitest';
import { TimeInputModule } from '../../../backend/src/modules/time_input/index';

function makeModule(config = { target_time: '23:59:59' }) {
  const log = vi.fn();
  const mod = new TimeInputModule(config, log);
  // Mock emitEvent to avoid side effects
  mod.emitEvent = vi.fn();
  return { mod, log };
}

describe('TimeInputModule', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should instantiate and start countdown', () => {
    const { mod } = makeModule({ target_time: '23:59:59' });
    expect(mod.isRunning()).toBe(true);
    expect(typeof mod.getCountdown()).toBe('string');
  });

  it('should stop and start correctly', async () => {
    const { mod } = makeModule();
    await mod.stop();
    expect(mod.isRunning()).toBe(false);
    await mod.start();
    expect(mod.isRunning()).toBe(true);
  });

  it('should return countdown info', () => {
    const { mod } = makeModule({ target_time: '12:00:00' });
    const info = mod.getCountdownInfo();
    expect(info).toHaveProperty('countdown');
    expect(info).toHaveProperty('target_time', '12:00:00');
    expect(info).toHaveProperty('isActive', true);
  });

  it('should handle missing target_time', () => {
    const { mod } = makeModule({});
    expect(mod.getCountdown()).toBe('No target time set');
  });

  it('should handle invalid target_time', () => {
    const { mod } = makeModule({ target_time: 'invalid' });
    expect(mod.getCountdown()).toBe('Invalid time format');
  });

  it('should emit trigger event when countdown reaches zero', () => {
    const { mod } = makeModule({ target_time: '00:00:00' });
    // Fast-forward time to force countdown to zero
    vi.setSystemTime(new Date('2099-01-01T00:00:00'));
    const result = mod.getCountdown();
    expect(result).toBe('Time to trigger!');
  });

  it('should call emitEvent on onTrigger', () => {
    const { mod } = makeModule();
    const event = { type: 'trigger', foo: 1 };
    mod.onTrigger(event);
    expect(mod.emitEvent).toHaveBeenCalledWith(event);
  });

  it('should call emitEvent on onStream', () => {
    const { mod } = makeModule();
    const value = { bar: 2 };
    mod.onStream(value);
    expect(mod.emitEvent).toHaveBeenCalledWith({ value });
  });
}); 