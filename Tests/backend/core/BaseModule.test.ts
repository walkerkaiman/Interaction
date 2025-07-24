import { describe, it, expect, beforeEach, vi } from 'vitest';
import { BaseModule, ModuleConfig } from '../../../backend/src/core/BaseModule';

// Mock subclass for testing
class MockBaseModule extends BaseModule {
  started = false;
  stopped = false;
  handledEvents: any[] = [];
  protected async onStart() { this.started = true; }
  protected async onStop() { this.stopped = true; }
  protected onHandleEvent(event: any) { this.handledEvents.push(event); }
}

describe('BaseModule', () => {
  let config: ModuleConfig;
  let manifest: any;
  let log: any;
  let logSpy: any;
  let module: MockBaseModule;

  beforeEach(() => {
    config = { foo: 'bar' };
    manifest = { name: 'mockModule' };
    log = vi.fn();
    logSpy = log;
    module = new MockBaseModule(config, manifest, log);
  });

  it('should construct with config, manifest, and log', () => {
    expect(module.getConfig()).toEqual(config);
    expect(module.getModuleName()).toBe('mockModule');
  });

  it('should set and get config', () => {
    const newConfig = { baz: 123 };
    module.setConfig(newConfig);
    expect(module.getConfig()).toEqual(newConfig);
    expect(logSpy).toHaveBeenCalledWith('Module config updated', 'System');
  });

  it('should lock and unlock', () => {
    module.lock();
    expect(module.isLocked()).toBe(true);
    expect(logSpy).toHaveBeenCalledWith('Module locked', 'System');
    module.unlock();
    expect(module.isLocked()).toBe(false);
    expect(logSpy).toHaveBeenCalledWith('Module unlocked', 'System');
  });

  it('should call onStart and onStop', async () => {
    await module.start();
    expect(module.started).toBe(true);
    await module.stop();
    expect(module.stopped).toBe(true);
  });

  it('should call onHandleEvent', () => {
    module.handleEvent({ foo: 1 });
    expect(module.handledEvents).toContainEqual({ foo: 1 });
  });

  it('should log errors in start/stop/handleEvent', async () => {
    const errorModule = new (class extends MockBaseModule {
      protected async onStart() { throw new Error('fail start'); }
      protected async onStop() { throw new Error('fail stop'); }
      protected onHandleEvent() { throw new Error('fail handle'); }
    })(config, manifest, log);
    await errorModule.start();
    await errorModule.stop();
    errorModule.handleEvent({});
    expect(logSpy).toHaveBeenCalledWith(expect.stringContaining('Error in start'), 'Error');
    expect(logSpy).toHaveBeenCalledWith(expect.stringContaining('Error in stop'), 'Error');
    expect(logSpy).toHaveBeenCalledWith(expect.stringContaining('Error in handleEvent'), 'Error');
  });
}); 