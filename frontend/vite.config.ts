import path from 'node:path'
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const frontendEnv = loadEnv(mode, process.cwd(), '')
  const rootEnv = loadEnv(mode, path.resolve(__dirname, '..'), '')
  const mergedEnv = { ...rootEnv, ...frontendEnv }

  return {
    plugins: [react()],
    define: {
      'import.meta.env.VITE_GOOGLE_CLIENT_ID': JSON.stringify(mergedEnv.VITE_GOOGLE_CLIENT_ID ?? ''),
    },
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
  }
})
