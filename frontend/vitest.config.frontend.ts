import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['Tests/frontend/**/*.test.tsx'],
    environment: 'jsdom',
    globals: true,
    setupFiles: [],
  },
}); 