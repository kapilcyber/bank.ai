import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../context/AppContext'
import { API_BASE_URL } from '../config/api'
import './Navbar.css'

const Navbar = ({ userProfile, showProfile = true }) => {
  const navigate = useNavigate()
  const { logout } = useApp()

  const handleProfileClick = () => {
    navigate('/profile')
  }

  // Get full image URL for profile photo
  const getProfileImageUrl = () => {
    if (!userProfile?.profile_img) return null
    // If it starts with http, use as is, otherwise prepend backend URL
    if (userProfile.profile_img.startsWith('http')) {
      return userProfile.profile_img
    }
    // Remove /api from API_BASE_URL to get the backend base URL
    const backendUrl = API_BASE_URL.replace('/api', '')
    return `${backendUrl}${userProfile.profile_img}`
  }

  return (
    <motion.nav
      className="navbar"
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <div className="navbar-container">
        <img src="/women.png" alt="Women Owned" className="navbar-logo-left" />
        
        <motion.h1
          className="navbar-heading"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => navigate('/dashboard')}
        >
          Techbank.Ai
        </motion.h1>

        <div className="navbar-actions">
          {showProfile && (
            <motion.button
              className="profile-button"
              onClick={handleProfileClick}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {getProfileImageUrl() ? (
                <img 
                  src={getProfileImageUrl()} 
                  alt="Profile" 
                  className="profile-avatar-img"
                />
              ) : (
                <div className="profile-avatar">
                  {userProfile?.name ? userProfile.name.charAt(0).toUpperCase() : 'U'}
                </div>
              )}
            </motion.button>
          )}

          <motion.button
            className="logout-button-nav"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={async () => {
              await logout()
              navigate('/')
            }}
            title="Logout"
          >
            Logout
          </motion.button>
        </div>
        
        <img src="/cache.png" alt="Cache" className="navbar-logo-right" />
      </div>
    </motion.nav>
  )
}

export default Navbar
