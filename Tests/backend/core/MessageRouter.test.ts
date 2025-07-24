import { describe, it, expect, beforeEach, vi } from 'vitest';
import { MessageRouter } from '../../../backend/src/core/MessageRouter';

// Minimal stubs for InputModuleBase and OutputModuleBase
class MockInputModule {
  constructor(private name: string, private config: any = {}) {}
  getModuleName() { return this.name; }
  getConfig() { return this.config; }
}
class MockOutputModule {
  public handledEvents: any[] = [];
  constructor(private name: string, private config: any = {}) {}
  getModuleName() { return this.name; }
  getConfig() { return this.config; }
  handleEvent(event: any) { this.handledEvents.push(event); }
}

describe('MessageRouter', () => {
  let router: MessageRouter;
  let inputA: MockInputModule;
  let inputB: MockInputModule;
  let outputA: MockOutputModule;
  let outputB: MockOutputModule;
  let modules: any[];

  beforeEach(() => {
    router = new MessageRouter();
    inputA = new MockInputModule('inputA', { id: 1 });
    inputB = new MockInputModule('inputB', { id: 2 });
    outputA = new MockOutputModule('outputA', { id: 1 });
    outputB = new MockOutputModule('outputB', { id: 2 });
    modules = [inputA, inputB, outputA, outputB];
  });

  it('should initialize with no connections', () => {
    expect(router.getConnections()).toEqual([]);
  });

  it('should build correct connections with rebuild', () => {
    const interactions = [
      { input: { module: 'inputA', config: { id: 1 } }, output: { module: 'outputA', config: { id: 1 } } },
      { input: { module: 'inputB', config: { id: 2 } }, output: { module: 'outputB', config: { id: 2 } } },
    ];
    router.rebuild(interactions, modules);
    const conns = router.getConnections();
    expect(conns.length).toBe(2);
    expect(conns[0].input).toBe(inputA);
    expect(conns[0].output).toBe(outputA);
    expect(conns[1].input).toBe(inputB);
    expect(conns[1].output).toBe(outputB);
  });

  it('should handle empty or invalid input in rebuild', () => {
    router.rebuild([], []);
    expect(router.getConnections()).toEqual([]);
    router.rebuild([{ input: {}, output: {} }], modules);
    expect(router.getConnections()).toEqual([]);
  });

  it('should add a new connection with addInteraction', () => {
    const interaction = { input: { module: 'inputA', config: { id: 1 } }, output: { module: 'outputA', config: { id: 1 } } };
    router.addInteraction(interaction, modules);
    const conns = router.getConnections();
    expect(conns.length).toBe(1);
    expect(conns[0].input).toBe(inputA);
    expect(conns[0].output).toBe(outputA);
  });

  it('should not add a connection if modules are missing', () => {
    const interaction = { input: { module: 'inputX', config: { id: 99 } }, output: { module: 'outputA', config: { id: 1 } } };
    router.addInteraction(interaction, modules);
    expect(router.getConnections()).toEqual([]);
  });

  it('should remove the correct connection with removeInteraction', () => {
    const interaction = { input: { module: 'inputA', config: { id: 1 } }, output: { module: 'outputA', config: { id: 1 } } };
    router.addInteraction(interaction, modules);
    expect(router.getConnections().length).toBe(1);
    router.removeInteraction(interaction);
    expect(router.getConnections()).toEqual([]);
  });

  it('should handle removal of non-existent connections gracefully', () => {
    const interaction = { input: { module: 'inputA', config: { id: 1 } }, output: { module: 'outputA', config: { id: 1 } } };
    expect(() => router.removeInteraction(interaction)).not.toThrow();
    expect(router.getConnections()).toEqual([]);
  });

  it('should update an interaction', () => {
    const oldInteraction = { input: { module: 'inputA', config: { id: 1 } }, output: { module: 'outputA', config: { id: 1 } } };
    const newInteraction = { input: { module: 'inputB', config: { id: 2 } }, output: { module: 'outputB', config: { id: 2 } } };
    router.addInteraction(oldInteraction, modules);
    expect(router.getConnections().length).toBe(1);
    router.updateInteraction(oldInteraction, newInteraction, modules);
    const conns = router.getConnections();
    expect(conns.length).toBe(1);
    expect(conns[0].input).toBe(inputB);
    expect(conns[0].output).toBe(outputB);
  });

  it('should route events from input to output if a connection exists', () => {
    const interaction = { input: { module: 'inputA', config: { id: 1 } }, output: { module: 'outputA', config: { id: 1 } } };
    router.addInteraction(interaction, modules);
    const event = { foo: 'bar' };
    router.routeEvent(inputA as any, event, 'trigger');
    expect(outputA.handledEvents.length).toBe(1);
    expect(outputA.handledEvents[0]).toMatchObject({ foo: 'bar', mode: 'trigger' });
  });

  it('should not route events if no connection exists', () => {
    const event = { foo: 'bar' };
    router.routeEvent(inputA as any, event, 'trigger');
    expect(outputA.handledEvents.length).toBe(0);
  });

  it('should return the current list of connections', () => {
    const interaction = { input: { module: 'inputA', config: { id: 1 } }, output: { module: 'outputA', config: { id: 1 } } };
    router.addInteraction(interaction, modules);
    expect(router.getConnections().length).toBe(1);
  });

  // Optional: test printConnections via spies if desired
  it('should print connections (smoke test)', () => {
    const spy = vi.spyOn(console, 'log');
    const interaction = { input: { module: 'inputA', config: { id: 1 } }, output: { module: 'outputA', config: { id: 1 } } };
    router.addInteraction(interaction, modules);
    router.printConnections();
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });

  it('should ignore malformed interactions in rebuild', () => {
    const malformed = [
      {},
      { input: null, output: null },
      { input: { module: 'inputA' }, output: { module: 'outputA' } },
      { input: { module: 'inputA', config: 123 }, output: { module: 'outputA', config: 456 } },
      { input: { module: 'inputA', config: { id: 1 } } }, // missing output
      { output: { module: 'outputA', config: { id: 1 } } }, // missing input
      null,
      undefined
    ];
    expect(() => router.rebuild(malformed as any, modules)).not.toThrow();
    expect(router.getConnections()).toEqual([]);
  });

  it('should ignore malformed interaction in addInteraction', () => {
    const malformed = [
      {},
      { input: null, output: null },
      { input: { module: 'inputA' }, output: { module: 'outputA' } },
      { input: { module: 'inputA', config: 123 }, output: { module: 'outputA', config: 456 } },
      { input: { module: 'inputA', config: { id: 1 } } }, // missing output
      { output: { module: 'outputA', config: { id: 1 } } }, // missing input
      null,
      undefined
    ];
    for (const bad of malformed) {
      expect(() => router.addInteraction(bad as any, modules)).not.toThrow();
      expect(router.getConnections()).toEqual([]);
    }
  });

  it('should ignore malformed interactions in updateInteraction', () => {
    const good = { input: { module: 'inputA', config: { id: 1 } }, output: { module: 'outputA', config: { id: 1 } } };
    const malformed = [
      {},
      { input: null, output: null },
      { input: { module: 'inputA' }, output: { module: 'outputA' } },
      { input: { module: 'inputA', config: 123 }, output: { module: 'outputA', config: 456 } },
      { input: { module: 'inputA', config: { id: 1 } } }, // missing output
      { output: { module: 'outputA', config: { id: 1 } } }, // missing input
      null,
      undefined
    ];
    router.addInteraction(good, modules);
    for (const bad of malformed) {
      expect(() => router.updateInteraction(good, bad as any, modules)).not.toThrow();
      // Should remove the good connection and not add a bad one
      expect(router.getConnections()).toEqual([]);
      // Restore good connection for next iteration
      router.addInteraction(good, modules);
    }
  });
}); 