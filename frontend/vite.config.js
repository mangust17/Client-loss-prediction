import { fileURLToPath, URL } from 'node:url'
import { resolve } from 'path'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  base: '/',
  plugins: [
    vue()
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    }
  },
  optimizeDeps: {
    include: ['plotly.js-dist-min'],
    exclude: ['probe-image-size']
  },
  build: {
    commonjsOptions: {
      include: [/node_modules/],
      exclude: ['probe-image-size']
    },
    rollupOptions: {
      external: ['probe-image-size']
    }
  },
  define: {
    'process.env': {},
    'global': {},
  },
  server: {
    port: 5173,
    host: true
  }
})
