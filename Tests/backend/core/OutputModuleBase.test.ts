import { describe, it, expect, beforeEach, vi } from 'vitest';
import { OutputModuleBase } from '../../../backend/src/core/OutputModuleBase';

// Mock subclass
class MockOutputModule extends OutputModuleBase {
  triggerEvents: any[] = [];
  streamEvents: any[] = [];
  onTriggerEvent(event: any) { this.triggerEvents.push(event); }
  onStreamingEvent(event: any) { this.streamEvents.push(event); }
}

describe('OutputModuleBase', () => {
  let module: MockOutputModule;
  let log: any;
  let manifest: any;
  let config: any;

  beforeEach(() => {
    log = vi.fn();
    manifest = { name: 'mockOutput' };
    config = { foo: 1 };
    module = new MockOutputModule(config, manifest, log);
  });

  it('should construct with config, manifest, and log', () => {
    expect(module.getConfig()).toEqual(config);
    expect(module.getModuleName()).toBe('mockOutput');
  });

  it('should set mode and log', () => {
    module.setMode('streaming');
    expect(log).toHaveBeenCalledWith('Output module mode set to streaming', 'System');
  });

  it('should handle trigger event', () => {
    module.handleEvent({ mode: 'trigger', foo: 2 });
    expect(module.triggerEvents).toContainEqual({ mode: 'trigger', foo: 2 });
  });

  it('should handle streaming event', () => {
    module.handleEvent({ mode: 'streaming', foo: 3 });
    expect(module.streamEvents).toContainEqual({ mode: 'streaming', foo: 3 });
  });

  it('should log errors in setMode/handleEvent', () => {
    const errorModule = new (class extends MockOutputModule {
      onTriggerEvent() { throw new Error('fail trigger'); }
      onStreamingEvent() { throw new Error('fail stream'); }
    })(config, manifest, log);
    errorModule.setMode('trigger');
    errorModule.handleEvent({ mode: 'trigger' });
    errorModule.handleEvent({ mode: 'streaming' });
    expect(log).toHaveBeenCalledWith(expect.stringContaining('Error in handleEvent'), 'Error');
  });
}); 