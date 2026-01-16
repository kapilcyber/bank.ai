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
        const actualPort = typeof address === 'object' && address?.port ? address.port : (server.config.server?.port || 3004)
        const networkURL = `http://${networkIP}:${actualPort}`
        
        // Show network IP prominently
        console.log(`\n🌐 Network Access: ${networkURL}\n`)
      })
      
      // Override printUrls to filter localhost
      const originalPrintUrls = server.printUrls
      server.printUrls = function() {
        // Intercept console output temporarily to filter localhost
        const originalLog = console.log
        const originalInfo = console.info
        
        const filterLocalhost = (args) => {
          const message = args.join(' ')
          return !message.includes('Local:') && 
                 !message.includes('localhost:') &&
                 !message.match(/➜\s+Local:/)
        }
        
        console.log = function(...args) {
          if (filterLocalhost(args)) {
            originalLog.apply(console, args)
          }
        }
        
        console.info = function(...args) {
          if (filterLocalhost(args)) {
            originalInfo.apply(console, args)
          }
        }
        
        // Call original printUrls
        if (originalPrintUrls) {
          originalPrintUrls.call(this)
        }
        
        // Restore console methods
        console.log = originalLog
        console.info = originalInfo
      }
    }
  }
}

export default defineConfig({
  plugins: [react(), networkIPPlugin()],
  server: {
    port: 3004,
    host: '0.0.0.0', // Allow external connections
    open: `http://${networkIP}:3004`, // Open network IP instead of localhost
    strictPort: false, // Allow Vite to use next available port if 3004 is busy
  }
})
