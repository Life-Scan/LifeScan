import path from 'node:path'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    port: 5173,
  },
  css: {
    modules: {
      // Classes legíveis no navegador durante o desenvolvimento (ex.: Painel_cartao__a1b2)
      generateScopedName: '[name]_[local]__[hash:base64:4]',
    },
  },
})
