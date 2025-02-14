import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '^/api/.*': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true,
        configure: (proxy, options) => {
          proxy.on('error', (err, req, res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log('Sending Request to:', req.method, proxyReq.path);
          });
          proxy.on('proxyRes', (proxyRes, req, res) => {
            console.log('Received Response from:', req.method, req.url, proxyRes.statusCode);
            // 添加 CORS 头
            res.setHeader('Access-Control-Allow-Origin', 'http://localhost:5173');
            res.setHeader('Access-Control-Allow-Credentials', 'true');
          });
        }
      }
    }
  }
})
