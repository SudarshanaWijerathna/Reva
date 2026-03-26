import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Any request that starts with /api...
      '/api': {
        // ...will be routed to your local Python server
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // This strips out the "/api" part so Python just sees "/ask"
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})