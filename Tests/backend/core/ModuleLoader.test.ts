import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ModuleLoader } from '../../../backend/src/core/ModuleLoader';
import { Logger } from '../../../backend/src/core/Logger';
import fs from 'fs';

// Mock modules
class MockModule {
  static manifest = { name: 'mock' };
  constructor(config: any, log: any) {
    this.config = config;
    this.log = log;
  }
  config: any;
  log: any;
}
class MockModule2 {
  static manifest = { name: 'mock2' };
  constructor(config: any, log: any) {
    this.config = config;
    this.log = log;
  }
  config: any;
  log: any;
}

describe('ModuleLoader', () => {
  let logger: Logger;
  let loader: ModuleLoader;
  let logSpy: any;
  let registry: Record<string, any>;
  let readFileSpy: any;

  beforeEach(() => {
    logger = new Logger('No Logging');
    logSpy = vi.spyOn(logger, 'log');
    registry = { mock: MockModule, mock2: MockModule2 };
    loader = new ModuleLoader(logger, registry);
  });

  afterEach(() => {
    if (readFileSpy) readFileSpy.mockRestore();
  });

  it('should load a valid module class by name', () => {
    const modClass = loader.getModuleClass('mock');
    expect(modClass).toBe(MockModule);
  });

  it('should return undefined for missing module', () => {
    const modClass = loader.getModuleClass('notfound');
    expect(modClass).toBeUndefined();
  });

  it('should return available modules with manifest', () => {
    const available = loader.getAvailableModules();
    expect(available.length).toBeGreaterThanOrEqual(2);
    expect(available[0]).toHaveProperty('name');
    expect(available[0]).toHaveProperty('manifest');
  });

  it('should load modules from config file', () => {
    const config = {
      interactions: [
        {
          input: { module: 'mock', config: { foo: 1 } },
          output: { module: 'mock2', config: { bar: 2 } }
        }
      ]
    };
    readFileSpy = vi.spyOn(fs, 'readFileSync').mockImplementation(() => JSON.stringify(config));
    const modules = loader.loadModulesFromConfig('fakepath.json');
    expect(modules.length).toBe(2);
    expect(modules[0]).toBeInstanceOf(MockModule);
    expect(modules[1]).toBeInstanceOf(MockModule2);
    expect(modules[0].config).toEqual({ foo: 1 });
    expect(modules[1].config).toEqual({ bar: 2 });
  });

  it('should handle unknown modules in config gracefully', () => {
    const config = {
      interactions: [
        {
          input: { module: 'notfound', config: {} },
          output: { module: 'mock2', config: {} }
        }
      ]
    };
    readFileSpy = vi.spyOn(fs, 'readFileSync').mockImplementation(() => JSON.stringify(config));
    const modules = loader.loadModulesFromConfig('fakepath.json');
    expect(modules.length).toBe(1);
    expect(modules[0]).toBeInstanceOf(MockModule2);
    expect(logSpy).toHaveBeenCalledWith('[System] Unknown input module: notfound', 'System');
  });

  it('should handle modules with missing or malformed manifest', () => {
    class NoManifest {}
    class BadManifest { static manifest = null; }
    const reg = { no: NoManifest, bad: BadManifest };
    const l = new ModuleLoader(logger, reg);
    const available = l.getAvailableModules();
    expect(available.find(m => m.name === 'no').manifest).toEqual({});
    expect(available.find(m => m.name === 'bad').manifest).toEqual({});
  });
}); 