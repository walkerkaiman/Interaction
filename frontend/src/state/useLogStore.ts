import { create } from 'zustand';

export interface LogEntry {
  message: string;
  module?: string;
  timestamp: string;
  category: string;
}

interface LogStore {
  logs: Record<string, LogEntry[]>; // category -> array of logs
  addLog: (log: LogEntry) => void;
  clearLogs: () => void;
  clearCategory: (category: string) => void;
  getLogsByCategory: (category: string) => LogEntry[];
}

const MAX_LOGS_PER_CATEGORY = 200;

export const useLogStore = create<LogStore>((set, get) => ({
  logs: {},
  addLog: (log: LogEntry) => {
    set((state) => {
      const cat = log.category || 'System';
      const prev = state.logs[cat] || [];
      const next = [...prev, log].slice(-MAX_LOGS_PER_CATEGORY);
      return { logs: { ...state.logs, [cat]: next } };
    });
  },
  clearLogs: () => set({ logs: {} }),
  clearCategory: (category: string) => set((state) => {
    const newLogs = { ...state.logs };
    delete newLogs[category];
    return { logs: newLogs };
  }),
  getLogsByCategory: (category: string) => {
    const logs = get().logs;
    if (category === 'all') {
      // Flatten all logs and sort by timestamp
      return Object.values(logs).flat().sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    }
    return logs[category] || [];
  },
})); 