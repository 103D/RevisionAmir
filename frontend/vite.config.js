import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  // ============================================================
  // Plugins
  // ============================================================
  plugins: [react()],

  // ============================================================
  // CSS Configuration
  // ============================================================
  css: {
    modules: false, // Disable CSS modules (use global CSS)
  },

  // ============================================================
  // Development Server
  // ============================================================
  server: {
    port: 5173,
    strictPort: false, // Use next available port if 5173 is busy
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path, // Keep original path
      },
    },
  },

  // ============================================================
  // Build Configuration
  // ============================================================
  build: {
    outDir: 'public',
    sourcemap: false, // Disable sourcemaps in production
    minify: 'terser',
    target: 'esnext',
  },
});
