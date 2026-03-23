import { useState } from 'react'
import { motion } from 'framer-motion'
import './AdminPortalLinks.css'

// Main app: npm run dev → :3005. Guest/Freelancer/Employee portals use separate dev servers.
const PORT_GUEST = Number(import.meta.env.VITE_PORT_GUEST) || 3008
const PORT_FREELANCER = Number(import.meta.env.VITE_PORT_FREELANCER) || 3006
const PORT_EMPLOYEE = Number(import.meta.env.VITE_PORT_EMPLOYEE) || 3007

const portalLinks = [
  { label: 'Guest Portal', path: '/guest', port: PORT_GUEST },
  { label: 'Freelancer Portal', path: '/freelancer', port: PORT_FREELANCER },
  { label: 'Company Employee Portal', path: '/employee', port: PORT_EMPLOYEE }
]

const getPortalBaseUrl = (port) => {
  return `${window.location.protocol}//${window.location.hostname}:${port}`
}

/** Reverse proxy on default HTTP port (:80) — same host, path only (no :3006–:3008 in URL). */
const usePathOnlyPortalUrls = () => {
  const p = window.location.port
  return !p || p === '80' || p === '443'
}

const getPortalPublicUrl = (path, port) => {
  if (usePathOnlyPortalUrls()) {
    return `${window.location.origin}${path}`
  }
  return `${getPortalBaseUrl(port)}${path}`
}

const AdminPortalLinks = () => {
  const [copiedLink, setCopiedLink] = useState(null)

  const copyPortalLink = (path, port) => {
    const url = getPortalPublicUrl(path, port)

    const doCopy = () => {
      setCopiedLink(path)
      setTimeout(() => setCopiedLink(null), 2000)
    }

    const fallbackCopy = () => {
      const textarea = document.createElement('textarea')
      textarea.value = url
      textarea.setAttribute('readonly', '')
      textarea.style.position = 'fixed'
      textarea.style.left = '-9999px'
      textarea.style.top = '0'
      document.body.appendChild(textarea)
      textarea.select()
      textarea.setSelectionRange(0, url.length)
      try {
        const ok = document.execCommand('copy')
        if (ok) doCopy()
      } finally {
        document.body.removeChild(textarea)
      }
    }

    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(url).then(doCopy).catch(fallbackCopy)
    } else {
      fallbackCopy()
    }
  }

  return (
    <div className="admin-portal-links">
      <div className="portal-links-header">
        <h2>Portal Links</h2>
      </div>
      <motion.div
        className="portal-links-section"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="portal-links-list">
          {portalLinks.map(({ label, path, port }) => {
            const url = getPortalPublicUrl(path, port)
            const isCopied = copiedLink === path
            return (
              <div key={path} className="portal-link-row">
                <span className="portal-link-label">{label}</span>
                <code className="portal-link-url">{url}</code>
                <button
                  type="button"
                  className="portal-link-copy-btn"
                  onClick={() => copyPortalLink(path, port)}
                  title="Copy link"
                >
                  {isCopied ? 'Copied!' : 'Copy'}
                </button>
              </div>
            )
          })}
        </div>
      </motion.div>
    </div>
  )
}

export default AdminPortalLinks
