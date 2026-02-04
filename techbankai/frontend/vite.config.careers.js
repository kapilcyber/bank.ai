import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { networkInterfaces } from 'os'

// Get network IP address
function getNetworkIP() {
  const interfaces = networkInterfaces()
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name] || []) {
      // Skip internal (loopback) and non-IPv4 addresses
      if (iface.family === 'IPv4' && !iface.internal) {
        // Prefer private network IPs (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
        if (iface.address.startsWith('192.168.') || 
            iface.address.startsWith('10.') || 
            iface.address.startsWith('172.')) {
          return iface.address
        }
      }
    }
  }
  // Fallback: return first non-internal IPv4 address
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name] || []) {
      if (iface.family === 'IPv4' && !iface.internal) {
        return iface.address
      }
    }
  }
  return 'localhost'
}

const networkIP = getNetworkIP()

// Plugin to filter out localhost and customize server output
const networkIPPlugin = () => {
  return {
    name: 'network-ip',
    configureServer(server) {
      // Get actual port after server starts
      server.httpServer?.once('listening', () => {
        const address = server.httpServer?.address()
        const actualPort = typeof address === 'object' && address?.port ? address.port : 3005
        const networkURL = `http://${networkIP}:${actualPort}`
        
        // Show network IP prominently
        console.log(`\n🌐 Careers Page - Network Access: ${networkURL}/careers.html\n`)
        console.log(`📋 Careers page running on port ${actualPort}\n`)
        console.log(`📍 Access at: http://localhost:${actualPort}/careers.html\n`)
        console.log(`💡 Careers page is standalone and accessible separately from main app\n`)
      })
    }
  }
}

export default defineConfig({
  plugins: [react(), networkIPPlugin()],
  server: {
    port: 3005,
    host: '0.0.0.0', // Allow external connections
    open: false, // Don't auto-open, user can navigate manually
    strictPort: false, // Allow Vite to use next available port if 3005 is busy
  },
  build: {
    rollupOptions: {
      input: './careers.html'
    },
    outDir: 'dist-careers'
  }
})
