import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: false,
        secure: false,
      },
      '/media': {
        target: 'http://backend:8000',
        changeOrigin: false,
        secure: false,
      }
    }
  }
})
