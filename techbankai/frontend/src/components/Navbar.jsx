import { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../context/AppContext'
import { API_BASE_URL } from '../config/api'
import LogoutTransition from './admin/LogoutTransition'
import './Navbar.css'

const Navbar = ({ userProfile, showAdminToggle = false, showProfile = true, showLogout = true, adminTabs, activeTab, setActiveTab, centerHeading }) => {
  const props = { adminTabs, activeTab, setActiveTab }
  const isPortalMode = !!centerHeading // Helper to keep the previous code working without changing 'props.' prefixes everywhere in the previous step instruction context, or I can just fix the usage in previous step. Actually, the Previous Step inserted `props.adminTabs`. So I need `props` to be defined. 
  // BETTER STRATEGY: Update the signature to `const Navbar = (props) => { const { userProfile, showAdminToggle = false, showProfile = true } = props; ...`
  // But that changes too much. 
  // I will just add the new props to destructuring and assign them to a 'props' object effectively or just change the signature to accept `props` directly and destructure userProfile etc from it.

  // Let's go with: const Navbar = (props) => { const { userProfile, showAdminToggle = false, showProfile = true } = props;

  const navigate = useNavigate()
  const { logout } = useApp()
  const [showLogoutTransition, setShowLogoutTransition] = useState(false)

  const handleAdminToggle = () => {
    navigate('/admin')
  }

  const handleLogout = async () => {
    setShowLogoutTransition(true)
  }

  const handleLogoutComplete = async () => {
    await logout()
    navigate('/')
  }

  if (showLogoutTransition) {
    return <LogoutTransition onComplete={handleLogoutComplete} />
  }

  return (
    <motion.nav
      className="navbar"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="navbar-container">
        <div className="navbar-left">
          <img 
            src="/women.png" 
            alt="Women Owned" 
            className="navbar-women-logo"
          />
          <motion.h1
            className="navbar-heading"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => !isPortalMode && navigate('/admin')}
            style={{ cursor: isPortalMode ? 'default' : 'pointer' }}
          >
            techbankai
          </motion.h1>
        </div>

        {/* Center heading (e.g. role title on application page) */}
        {centerHeading && (
          <div className="navbar-center-heading">
            <h1 className="navbar-center-heading-text">{centerHeading}</h1>
          </div>
        )}

        {/* Central Admin Tabs */}
        {props.adminTabs && (
          <div className="navbar-center-tabs">
            {props.adminTabs.map((tab) => (
              <motion.button
                key={tab.id}
                className={`nav-glass-tab ${tab.colorClass} ${props.activeTab === tab.id ? 'active' : ''}`}
                onClick={() => props.setActiveTab(tab.id)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <span className="tab-icon">{tab.icon}</span>
                <span className="tab-label">{tab.label}</span>
              </motion.button>
            ))}
          </div>
        )}

        <div className="navbar-actions">
          {showAdminToggle && (
            <button
              className="admin-toggle"
              onClick={handleAdminToggle}
            >
              Admin
            </button>
          )}

          {showProfile && (
            <button
              className="profile-button"
              onClick={() => navigate('/profile')}
            >
              <div className="profile-avatar">
                {userProfile?.profile_img ? (
                  <img
                    src={userProfile.profile_img.startsWith('http') ? userProfile.profile_img : `${API_BASE_URL.replace('/api', '')}${userProfile.profile_img}`}
                    alt="P"
                    className="navbar-avatar-img"
                  />
                ) : (
                  userProfile?.name ? userProfile.name.charAt(0).toUpperCase() : 'U'
                )}
              </div>
            </button>
          )}

          {showLogout && (
            <button
              className="logout-button-nav"
              onClick={handleLogout}
              title="Logout"
            >
              Logout
            </button>
          )}

          <img 
            src="/cache.png" 
            alt="Cache" 
            className="navbar-cache-logo"
          />
        </div>
      </div>
    </motion.nav>
  )
}

export default Navbar

