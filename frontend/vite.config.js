import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
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
