import { create } from 'zustand';

interface ModuleState {
  id: string;
  config: any;
  mode?: 'trigger' | 'streaming';
  isLocked?: boolean;
}

interface ModulesStore {
  modules: Record<string, ModuleState>;
  availableModules: any[];
  fetchAvailableModules: () => Promise<void>;
  connectWebSocket: () => void;
  updateModuleSettings: (id: string, settings: any) => Promise<void>;
  updateModuleMode: (id: string, mode: 'trigger' | 'streaming') => Promise<void>;
}

console.debug('useModulesStore.ts loaded');
export const useModulesStore = create<ModulesStore>((set: any, _get: any) => ({
  modules: {},
  availableModules: [],
  fetchAvailableModules: async (): Promise<void> => {
    const res = await fetch('/modules');
    const data = await res.json();
    set({ availableModules: data });
  },
  connectWebSocket: (): void => {
    const ws = new WebSocket(`ws://${window.location.host}`);
    ws.onmessage = (event: MessageEvent) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'all_modules') {
        const modules: Record<string, ModuleState> = {};
        msg.modules.forEach((m: any) => {
          modules[m.id] = { id: m.id, config: m.config };
        });
        set({ modules });
      } else if (msg.type === 'module_update') {
        set((state: any) => ({
          modules: {
            ...state.modules,
            [msg.moduleId]: {
              ...state.modules[msg.moduleId],
              config: msg.newState,
              isLocked: false,
            },
          },
        }));
      } else if (msg.type === 'module_mode') {
        set((state: any) => ({
          modules: {
            ...state.modules,
            [msg.moduleId]: {
              ...state.modules[msg.moduleId],
              mode: msg.mode,
              isLocked: false,
            },
          },
        }));
      } else if (msg.type === 'module_lock') {
        set((state: any) => ({
          modules: {
            ...state.modules,
            [msg.moduleId]: {
              ...state.modules[msg.moduleId],
              isLocked: true,
            },
          },
        }));
      } else if (msg.type === 'module_unlock') {
        set((state: any) => ({
          modules: {
            ...state.modules,
            [msg.moduleId]: {
              ...state.modules[msg.moduleId],
              isLocked: false,
            },
          },
        }));
      }
    };
  },
  updateModuleSettings: async (id: any, settings: any): Promise<void> => {
    set((state: any) => ({
      modules: {
        ...state.modules,
        [id]: {
          ...state.modules[id],
          isLocked: true,
        },
      },
    }));
    await fetch(`/modules/${id}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    // UI will unlock on WebSocket update
  },
  updateModuleMode: async (id: any, mode: any): Promise<void> => {
    set((state: any) => ({
      modules: {
        ...state.modules,
        [id]: {
          ...state.modules[id],
          isLocked: true,
        },
      },
    }));
    await fetch(`/modules/${id}/mode`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode }),
    });
    // UI will unlock on WebSocket update
  },
})); 