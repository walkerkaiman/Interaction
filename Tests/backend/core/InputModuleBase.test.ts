import { describe, it, expect, beforeEach, vi } from 'vitest';
import { InputModuleBase } from '../../../backend/src/core/InputModuleBase';

vi.mock('../../../backend/src/core/MessageRouter', () => {
  return {
    messageRouter: { routeEvent: vi.fn() }
  };
});
import { messageRouter } from '../../../backend/src/core/MessageRouter';

// Mock subclass
class MockInputModule extends InputModuleBase {
  triggerEvents: any[] = [];
  streamEvents: any[] = [];
  triggerParams: any = { foo: 'bar' };
  protected onGetTriggerParameters() { return this.triggerParams; }
  onTrigger(event: any) { this.triggerEvents.push(event); }
  onStream(value: any) { this.streamEvents.push(value); }
  protected async onStart() {}
  protected async onStop() {}
  protected onHandleEvent(event: any) {}
}

describe('InputModuleBase', () => {
  let module: MockInputModule;
  let log: any;
  let manifest: any;
  let config: any;

  beforeEach(() => {
    log = vi.fn();
    manifest = { name: 'mockInput' };
    config = { foo: 1 };
    module = new MockInputModule(config, manifest, log);
    (messageRouter.routeEvent as any).mockClear();
  });

  it('should construct with config, manifest, and log', () => {
    expect(module.getConfig()).toEqual(config);
    expect(module.getModuleName()).toBe('mockInput');
  });

  it('should set mode and log', () => {
    module.setMode('streaming');
    expect(log).toHaveBeenCalledWith('Input module mode set to streaming', 'System');
  });

  it('should emitEvent and call messageRouter.routeEvent', () => {
    const event = { foo: 2 };
    module['emitEvent'](event);
    expect(messageRouter.routeEvent).toHaveBeenCalledWith(module, event, 'trigger');
  });

  it('should get trigger parameters', () => {
    expect(module.getTriggerParameters()).toEqual({ foo: 'bar' });
  });

  it('should handle trigger event', () => {
    module.setMode('trigger');
    module.handleEvent({ foo: 3 });
    expect(module.triggerEvents).toContainEqual({ foo: 3 });
  });

  it('should handle streaming event', () => {
    module.setMode('streaming');
    module.handleEvent({ value: 42 });
    expect(module.streamEvents).toContainEqual(42);
  });

  it('should log errors in setMode/getTriggerParameters/handleEvent', () => {
    const errorModule = new (class extends MockInputModule {
      protected onGetTriggerParameters() { throw new Error('fail param'); }
      onTrigger() { throw new Error('fail trigger'); }
      onStream() { throw new Error('fail stream'); }
      protected async onStart() {}
      protected async onStop() {}
      protected onHandleEvent(event: any) {}
    })(config, manifest, log);
    errorModule.getTriggerParameters();
    errorModule.setMode('trigger');
    errorModule.handleEvent({ value: 1 });
    expect(log).toHaveBeenCalledWith(expect.stringContaining('Error in getTriggerParameters'), 'Error');
    expect(log).toHaveBeenCalledWith(expect.stringContaining('Error in handleEvent'), 'Error');
  });
}); 