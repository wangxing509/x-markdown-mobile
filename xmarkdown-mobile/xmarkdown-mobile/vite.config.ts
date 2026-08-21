import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base './' 使构建产物可部署到任意子路径（GitHub Pages 项目页 / username.github.io/repo/）
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'markdown-vendor': ['react-markdown', 'remark-gfm', 'rehype-highlight'],
        },
      },
    },
  },
})
