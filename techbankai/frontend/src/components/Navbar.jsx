import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../context/AppContext'
import { API_BASE_URL } from '../config/api'
import './Navbar.css'

const Navbar = ({ userProfile, showAdminToggle = false, showProfile = true, adminTabs, activeTab, setActiveTab }) => {
  const props = { adminTabs, activeTab, setActiveTab } // Helper to keep the previous code working without changing 'props.' prefixes everywhere in the previous step instruction context, or I can just fix the usage in previous step. Actually, the Previous Step inserted `props.adminTabs`. So I need `props` to be defined. 
  // BETTER STRATEGY: Update the signature to `const Navbar = (props) => { const { userProfile, showAdminToggle = false, showProfile = true } = props; ...`
  // But that changes too much. 
  // I will just add the new props to destructuring and assign them to a 'props' object effectively or just change the signature to accept `props` directly and destructure userProfile etc from it.

  // Let's go with: const Navbar = (props) => { const { userProfile, showAdminToggle = false, showProfile = true } = props;

  const navigate = useNavigate()
  const { logout } = useApp()

  const handleAdminToggle = () => {
    navigate('/admin')
  }

  return (
    <motion.nav
      className="navbar"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="navbar-container">
        <motion.h1
          className="navbar-heading"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => navigate('/admin')}
        >
          Techbank.Ai
        </motion.h1>

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

          <button
            className="logout-button-nav"
            onClick={async () => {
              await logout()
              navigate('/')
            }}
            title="Logout"
          >
            Logout
          </button>
        </div>
      </div>
    </motion.nav>
  )
}

export default Navbar

