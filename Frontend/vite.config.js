// Frontend/vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      "/upload": {
        target: "http://localhost:5000",
        changeOrigin: true,
        secure: false,
        logLevel: "debug",
        onProxyReq: (proxyReq, req, res) => {
          console.log(`Proxying ${req.method} request to: ${proxyReq.path}`);
        },
        onError: (err, req, res) => {
          console.error('Proxy error:', err);
          res.status(500).send('Proxy error');
        },
      },
      "/ask": {
        target: "http://localhost:5000",
        changeOrigin: true,
        secure: false,
        logLevel: "debug",
      },
      "/data": {
        target: "http://localhost:5000",
        changeOrigin: true,
        secure: false,
        logLevel: "debug",
      },
    },
  },
});