import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/modules': 'http://localhost:8000',
      // add other backend routes if needed
    }
  }
});
