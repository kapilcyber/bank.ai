import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/** guest | freelancer | employee */
const PORTALS = {
  guest: { base: '/guest/', port: 3008 },
  freelancer: { base: '/freelancer/', port: 3006 },
  employee: { base: '/employee/', port: 3007 },
}

/** mode: portal-guest | portal-guest-proxy | portal-freelancer | ... */
function parseMode(mode) {
  if (!mode.startsWith('portal-')) return null
  let rest = mode.slice('portal-'.length)
  const behindProxy = rest.endsWith('-proxy')
  if (behindProxy) rest = rest.slice(0, -'-proxy'.length)
  const spec = PORTALS[rest]
  if (!spec) return null
  return { name: rest, ...spec, behindProxy }
}

export default defineConfig(({ mode }) => {
  const p = parseMode(mode)
  if (!p) {
    throw new Error(
      `vite.config.portal.js: use --mode portal-guest|portal-freelancer|portal-employee (optional -proxy for reverse proxy on :80)`
    )
  }
  return {
    base: p.base,
    plugins: [react()],
    server: {
      port: p.port,
      host: '0.0.0.0',
      strictPort: true,
      allowedHosts: true,
      // Keep portal dev servers headless; user opens /guest|/freelancer|/employee manually.
      open: false,
      hmr: p.behindProxy ? { protocol: 'ws', clientPort: 80 } : undefined,
    },
    build: {
      rollupOptions: {
        input: './index.html',
      },
    },
  }
})
