import { InputModuleBase } from './InputModuleBase';
import { OutputModuleBase } from './OutputModuleBase';

interface ModuleConnection {
  input: InputModuleBase;
  output: OutputModuleBase;
}

/**
 * MessageRouter
 *
 * The MessageRouter is responsible for routing events between input and output modules
 * according to the current set of interactions. It supports:
 *
 * - One-to-one, one-to-many, and many-to-one routing: Any input can be connected to any number of outputs, and vice versa.
 * - Mode-aware routing: Events are routed with the correct mode ('trigger' or 'streaming').
 * - Dynamic updates: Interactions can be added, removed, or updated at runtime, and the router updates its connections accordingly.
 * - Integration: Input modules call messageRouter.routeEvent(this, event, this.mode) to route events.
 *
 * Usage:
 *   - The router is a singleton (import { messageRouter } from './MessageRouter').
 *   - When an input module emits an event, call this.emitEvent(event) in onTrigger/onStream.
 *   - The router will deliver the event to all connected outputs as defined by the current interactions.
 *   - The backend updates the router when interactions are added/removed/updated via API endpoints.
 *
 * Example:
 *   // Add a new interaction at runtime
 *   messageRouter.addInteraction(interaction, modules);
 *
 *   // Remove an interaction
 *   messageRouter.removeInteraction(interaction);
 *
 *   // Route an event from an input module
 *   messageRouter.routeEvent(inputModule, event, 'trigger');
 *
 *   // Rebuild all connections (e.g., after bulk update)
 *   messageRouter.rebuild(interactions, modules);
 *
 * See also: InputModuleBase.emitEvent, backend API endpoints for interaction management.
 */
export class MessageRouter {
  private connections: ModuleConnection[] = [];

  constructor(interactions: any[] = [], modules: any[] = []) {
    if (interactions.length && modules.length) {
      this.rebuild(interactions, modules);
    }
  }

  rebuild(interactions: any[], modules: any[]) {
    try {
      this.connections = [];
      for (const interaction of interactions) {
        const input = modules.find(m => 
          m.getModuleName() === interaction.input.module && 
          JSON.stringify(m.getConfig()) === JSON.stringify(interaction.input.config)
        );
        const output = modules.find(m => 
          m.getModuleName() === interaction.output.module && 
          JSON.stringify(m.getConfig()) === JSON.stringify(interaction.output.config)
        );
        if (input && output) {
          this.connections.push({ input, output });
          console.log(`[System] Registered interaction: ${interaction.input.module} → ${interaction.output.module}`);
        }
      }
      console.log(`[System] MessageRouter connections rebuilt. Total: ${this.connections.length}`);
      this.printConnections();
    } catch (err) {
      console.error('[Error] Error in MessageRouter.rebuild:', err);
    }
  }

  printConnections() {
    if (this.connections.length === 0) {
      console.log('[System] No MessageRouter connections.');
    } else {
      console.log('[System] Current MessageRouter connections:');
      this.connections.forEach((conn, idx) => {
        console.log(`  [${idx}] ${conn.input.getModuleName()} (${JSON.stringify(conn.input.getConfig())}) → ${conn.output.getModuleName()} (${JSON.stringify(conn.output.getConfig())})`);
      });
    }
  }

  addInteraction(interaction: any, modules: any[]) {
    try {
      const input = modules.find(m => 
        m.getModuleName() === interaction.input.module && 
        JSON.stringify(m.getConfig()) === JSON.stringify(interaction.input.config)
      );
      const output = modules.find(m => 
        m.getModuleName() === interaction.output.module && 
        JSON.stringify(m.getConfig()) === JSON.stringify(interaction.output.config)
      );
      if (input && output) {
        this.connections.push({ input, output });
      }
    } catch (err) {
      console.error('Error in MessageRouter.addInteraction:', err);
    }
  }

  removeInteraction(interaction: any) {
    try {
      this.connections = this.connections.filter(conn =>
        !(conn.input.getModuleName() === interaction.input.module &&
          JSON.stringify(conn.input.getConfig()) === JSON.stringify(interaction.input.config) &&
          conn.output.getModuleName() === interaction.output.module &&
          JSON.stringify(conn.output.getConfig()) === JSON.stringify(interaction.output.config))
      );
      console.log(`[System] Removed interaction: ${interaction.input.module} → ${interaction.output.module}`);
      console.log(`[System] MessageRouter connections after removal. Total: ${this.connections.length}`);
      this.printConnections();
    } catch (err) {
      console.error('[Error] Error in MessageRouter.removeInteraction:', err);
    }
  }

  updateInteraction(oldInteraction: any, newInteraction: any, modules: any[]) {
    try {
      this.removeInteraction(oldInteraction);
      this.addInteraction(newInteraction, modules);
      console.log(`[System] Updated interaction: ${oldInteraction.input.module} → ${oldInteraction.output.module} to ${newInteraction.input.module} → ${newInteraction.output.module}`);
      console.log(`[System] MessageRouter connections after update. Total: ${this.connections.length}`);
      this.printConnections();
    } catch (err) {
      console.error('[Error] Error in MessageRouter.updateInteraction:', err);
    }
  }

  routeEvent(fromModule: InputModuleBase, event: any, mode: 'trigger' | 'streaming') {
    try {
      let routed = false;
      console.log(`[System] Attempting to route event from ${fromModule.getModuleName()} with config ${JSON.stringify(fromModule.getConfig())}: ${JSON.stringify(event)}`);
      for (const conn of this.connections) {
        if (conn.input === fromModule) {
          console.log(`[System] Routing event from ${fromModule.getModuleName()} to ${conn.output.getModuleName()}: ${JSON.stringify(event)}`);
          conn.output.handleEvent({ ...event, mode });
          routed = true;
        }
      }
      if (!routed) {
        console.log(`[System] No connections found for event from ${fromModule.getModuleName()} with config ${JSON.stringify(fromModule.getConfig())}`);
      }
    } catch (err) {
      console.error('[Error] Error in MessageRouter.routeEvent:', err);
    }
  }

  getConnections() {
    return this.connections;
  }
}

// Singleton instance
export const messageRouter = new MessageRouter(); 