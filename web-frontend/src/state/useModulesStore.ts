import { create } from 'zustand';
import { fetchModules } from '../api/api';

// No need to import SetState; use 'set: any' for compatibility

interface Module {
  id: string;
  name: string;
  type: string;
  [key: string]: any;
}

interface ModulesState {
  modules: Module[];
  loading: boolean;
  error: string | null;
  fetchAll: () => Promise<void>;
}

export const useModulesStore = create<ModulesState>((set: any) => ({
  modules: [],
  loading: false,
  error: null,
  fetchAll: async () => {
    set({ loading: true, error: null });
    try {
      const modules = await fetchModules();
      set({ modules, loading: false });
    } catch (err: any) {
      set({ error: err.message || 'Failed to fetch modules', loading: false });
    }
  },
})); 