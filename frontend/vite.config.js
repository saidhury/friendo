import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const isDev = mode === 'development'
  
  return {
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
      assetsDir: 'assets',
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: !isDev,
          drop_debugger: !isDev,
          pure_funcs: isDev ? [] : ['console.log', 'console.info', 'console.debug'],
          passes: 2
        },
        mangle: {
          safari10: true
        },
        format: {
          comments: false
        }
      },
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom']
          },
          compact: true
        }
      },
      sourcemap: false,
      chunkSizeWarningLimit: 500,
      cssCodeSplit: true,
      reportCompressedSize: false,
      target: 'es2020'
    },
    preview: {
      port: 4173
    },
    esbuild: {
      legalComments: 'none',
      treeShaking: true
    }
  }
})
