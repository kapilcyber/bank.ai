import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../context/AppContext'
import { getProfile, updateProfile, uploadProfilePhoto, removeProfilePhoto, API_BASE_URL } from '../config/api'
import Navbar from '../components/Navbar'
import CyberBackground from '../components/admin/CyberBackground'
import './Profile.css'

const Profile = () => {
  const navigate = useNavigate()
  const { userProfile, logout, setUserProfile } = useApp()
  const [isEditing, setIsEditing] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)

  // Use profile_img from backend profile data
  const profileImg = userProfile?.profile_img
    ? (userProfile.profile_img.startsWith('http') ? userProfile.profile_img : `${API_BASE_URL.replace('/api', '')}${userProfile.profile_img}`)
    : null

  const [editedProfile, setEditedProfile] = useState({
    name: userProfile?.name || '',
    email: userProfile?.email || '',
    phone: userProfile?.phone || '',
    role: userProfile?.mode || userProfile?.role || 'Administrator'
  })

  const handleImageUpload = async (e) => {
    const file = e.target.files[0]
    if (file) {
      try {
        setLoading(true)
        setError('')
        const updatedUser = await uploadProfilePhoto(file)
        setUserProfile(prev => ({
          ...prev,
          profile_img: updatedUser.profile_img
        }))
      } catch (err) {
        console.error('Photo upload error:', err)
        setError('Mainframe rejected the image upload.')
      } finally {
        setLoading(false)
      }
    }
  }

  const handleImageRemove = async () => {
    if (!userProfile?.profile_img) return
    
    try {
      setLoading(true)
      setError('')
      const result = await removeProfilePhoto()
      setUserProfile(prev => ({
        ...prev,
        profile_img: result.profile_img || null
      }))
    } catch (err) {
      console.error('Photo remove error:', err)
      setError('Failed to purge profile image from mainframe.')
    } finally {
      setLoading(false)
    }
  }

  const triggerFileInput = () => {
    // Using ref for direct DOM access
    if (fileInputRef.current) {
      fileInputRef.current.click()
    }
  }

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        setLoading(true)
        const profile = await getProfile()
        const mergedProfile = {
          ...userProfile,
          ...profile,
          role: profile.mode || 'Administrator'
        }
        setUserProfile(mergedProfile)
        setEditedProfile({
          name: mergedProfile.name || '',
          email: mergedProfile.email || '',
          phone: mergedProfile.phone || '',
          role: mergedProfile.role || 'Administrator'
        })
      } catch (err) {
        console.error('Error loading profile:', err)
        setError('Could not sync profile with mainframe.')
      } finally {
        setLoading(false)
      }
    }
    fetchProfile()
  }, [])

  const handleSave = async () => {
    try {
      setLoading(true)
      const payload = { name: editedProfile.name }
      const updated = await updateProfile(payload)
      setUserProfile({ ...userProfile, ...editedProfile, name: updated.name })
      setIsEditing(false)
    } catch (err) {
      setError('Update failed. Connection unstable.')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    setEditedProfile({ ...editedProfile, [e.target.name]: e.target.value })
  }

  return (
    <div className="profile-page">
      <CyberBackground />
      <Navbar userProfile={userProfile} />

      <div className="profile-container">
        <motion.div
          className="profile-card-cyber"
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        >
          {/* Header with Glow Avatar */}
          <div className="profile-header-cyber">
            <div className="avatar-section-wrapper">
              <div className="avatar-upload-wrapper" onClick={triggerFileInput}>
                <div className="profile-avatar-glow">
                  {profileImg ? (
                    <img src={profileImg} alt="Profile" className="avatar-img" />
                  ) : (
                    userProfile?.name ? userProfile.name.charAt(0).toUpperCase() : 'A'
                  )}
                  <div className="avatar-ring"></div>
                  <div className="avatar-overlay">
                    <span className="upload-icon">📷</span>
                  </div>
                </div>
                <input
                  type="file"
                  id="profile-upload-input"
                  hidden
                  accept="image/*"
                  onChange={handleImageUpload}
                  ref={fileInputRef}
                />
              </div>
              <div className="avatar-action-buttons">
                <button 
                  className="avatar-action-btn upload-btn"
                  onClick={triggerFileInput}
                  disabled={loading}
                  title="Upload photo"
                >
                  📷
                </button>
                <button 
                  className="avatar-action-btn remove-btn"
                  onClick={handleImageRemove}
                  disabled={loading || !userProfile?.profile_img}
                  title={userProfile?.profile_img ? "Remove photo" : "No photo to remove"}
                >
                  🗑️
                </button>
              </div>
            </div>
            <div className="profile-info-cyber">
              <h1 className="cyber-name">{userProfile?.name || 'Admin User'}</h1>
              <div className="cyber-status-pill">
                <span className="status-dot"></span> SYSTEM {userProfile?.mode?.toUpperCase() || 'ROOT'} ACCESS
              </div>
            </div>
          </div>

          <div className="cyber-divider"></div>

          {/* Information Grid */}
          <div className="profile-grid">
            <div className="cyber-info-box">
              <label><span className="icon">🛡️</span> FULL NAME</label>
              {isEditing ? (
                <input
                  name="name"
                  value={editedProfile.name}
                  onChange={handleChange}
                  className="cyber-input"
                />
              ) : (
                <p className="cyber-value">{userProfile?.name || 'Not Defined'}</p>
              )}
            </div>

            <div className="cyber-info-box">
              <label><span className="icon">📧</span> SYSTEM EMAIL</label>
              <p className="cyber-value secondary">{userProfile?.email || 'N/A'}</p>
            </div>

            <div className="cyber-info-box">
              <label><span className="icon">⚔️</span> ASSIGNED ROLE</label>
              <p className="cyber-value highlight">{userProfile?.mode?.toUpperCase() || 'ADMINISTRATOR'}</p>
            </div>

            <div className="cyber-info-box">
              <label><span className="icon">📅</span> ACCESS GRANTED</label>
              <p className="cyber-value secondary">
                {userProfile?.created_at ? new Date(userProfile.created_at).toLocaleDateString() : 'Dec 2023'}
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="profile-footer-cyber">
            {!isEditing ? (
              <button className="cyber-btn primary" onClick={() => setIsEditing(true)}>
                EDIT PROTOCOLS
              </button>
            ) : (
              <div className="edit-actions">
                <button className="cyber-btn success" onClick={handleSave} disabled={loading}>
                  {loading ? 'SYNCING...' : 'SAVE CHANGES'}
                </button>
                <button className="cyber-btn cancel" onClick={() => setIsEditing(false)}>
                  ABORT
                </button>
              </div>
            )}
            <button className="cyber-btn primary" onClick={() => navigate('/admin')}>
              RETURN TO MAINFRAME
            </button>
            <button className="cyber-btn danger" onClick={() => { logout(); navigate('/'); }}>
              TERMINATE SESSION
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default Profile
