import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './',
  server: {
    proxy: {
      '/chat': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/health': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/transcribe': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/sync': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/sync/status': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/provider': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    }
  }
})
