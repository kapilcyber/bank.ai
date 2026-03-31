import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import os from 'node:os'

/** First non-internal IPv4 — for opening http://<ip>/ when using a :80 reverse proxy (no port in URL). */
function getLanIPv4() {
  for (const nets of Object.values(os.networkInterfaces())) {
    if (!nets) continue
    for (const n of nets) {
      if (n.family === 'IPv4' && !n.internal) return n.address
    }
  }
  return '127.0.0.1'
}

// npm run dev:behind-proxy → use nginx (or similar) on :80/:8080 so the browser avoids Vite's dev port.
export default defineConfig(({ mode }) => {
  const behindProxy = mode === 'behind-proxy'
  const lan = getLanIPv4()

  return {
    plugins: [react()],
    server: {
      port: 3005,
      host: '0.0.0.0', // Allow external connections
      // Direct dev: show :3005. Behind proxy on :80/:8080: open LAN URL so phones/other PCs can use the same pattern.
      open: behindProxy ? `http://${lan}/` : 'http://127.0.0.1:3005/',
      strictPort: true, // Always use port 3005 internally; exit if busy
      // Allow Host header from reverse proxy (http://<lan-ip>/ without :3005)
      allowedHosts: true,
      // HMR via proxy on :8080 (client uses same hostname as the URL — 127.0.0.1 or LAN IP)
      hmr: behindProxy ? { protocol: 'ws', clientPort: 8080 } : undefined,
    },
    build: {
      rollupOptions: {
        input: './index.html'
      }
    }
  }
})
