import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default {
  plugins: [react()],
  server: {
    allowedHosts: true,
    proxy: {
      '/api': {
        target: (typeof process !== 'undefined' && process.env.VITE_BACKEND_TARGET) || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
}
