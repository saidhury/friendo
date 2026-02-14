import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/users': 'http://localhost:8000',
      '/tasks': 'http://localhost:8000',
      '/energy': 'http://localhost:8000',
      '/api': 'http://localhost:8000'
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
})
