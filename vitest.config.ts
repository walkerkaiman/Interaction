import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['Tests/backend/**/*.test.ts'],
    environment: 'node',
    globals: true,
    pool: 'forks',
    poolOptions: {
      forks: {
        singleFork: true,
      },
    },
    coverage: {
      reporter: ['text', 'json', 'html'],
    },
  },
}); 