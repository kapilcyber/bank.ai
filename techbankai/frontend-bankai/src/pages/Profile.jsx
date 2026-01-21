import { motion } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { getProfile, updateProfile, uploadProfilePhoto, removeProfilePhoto, API_BASE_URL } from '../config/api'
import { useApp } from '../context/AppContext'
import './Profile.css'

const Profile = () => {
  const navigate = useNavigate()
  const { userProfile, logout, setUserProfile } = useApp()
  const [isEditing, setIsEditing] = useState(false)
  const [loading, setLoading] = useState(false)
  const [photoLoading, setPhotoLoading] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)
  const [editedProfile, setEditedProfile] = useState({
    name: userProfile?.name || '',
    email: userProfile?.email || '',
    phone: userProfile?.phone || '',
    dateOfBirth: userProfile?.dateOfBirth || '',
    state: userProfile?.state || '',
    city: userProfile?.city || '',
    pincode: userProfile?.pincode || '',
    role: userProfile?.role || '',
    skills: userProfile?.skills || ''
  })

  useEffect(() => {
    // Load latest profile from backend
    const fetchProfile = async () => {
      try {
        setLoading(true)
        setError('')
        const profile = await getProfile()
        const mergedProfile = {
          ...userProfile,
          id: profile.id,
          name: profile.name,
          email: profile.email,
          phone: profile.phone,
          dateOfBirth: profile.dob || userProfile?.dateOfBirth,
          dob: profile.dob,
          state: profile.state,
          city: profile.city,
          pincode: profile.pincode,
          mode: profile.mode,
          role: profile.role,
          employment_type: profile.employment_type,
          profile_img: profile.profile_img,
          employeeId: profile.employee_id,
          freelancerId: profile.freelancer_id,
          created_at: profile.created_at || userProfile?.created_at,
          createdAt: profile.created_at || userProfile?.created_at,
        }
        setUserProfile(mergedProfile)
        setEditedProfile({
          name: mergedProfile.name || '',
          email: mergedProfile.email || '',
          phone: mergedProfile.phone || '',
          dateOfBirth: mergedProfile.dateOfBirth || mergedProfile.dob || '',
          state: mergedProfile.state || '',
          city: mergedProfile.city || '',
          pincode: mergedProfile.pincode || '',
          role: mergedProfile.role || '',
          skills: mergedProfile.skills || ''
        })
      } catch (err) {
        console.error('Error loading profile:', err)
        setError(err.message || 'Failed to load profile')
      } finally {
        setLoading(false)
      }
    }

    // Only fetch if we have a token (user is authenticated)
    fetchProfile()
  }, [])

  // Handle photo upload
  const handlePhotoUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if (!validTypes.includes(file.type)) {
      setError('Please select a valid image file (JPEG, PNG, GIF, or WebP)')
      return
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('Image size should be less than 5MB')
      return
    }

    try {
      setPhotoLoading(true)
      setError('')
      const result = await uploadProfilePhoto(file)
      
      // Update user profile with new photo
      setUserProfile({
        ...userProfile,
        profile_img: result.profile_img
      })
      
      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (err) {
      console.error('Photo upload error:', err)
      setError(err.message || 'Failed to upload photo')
    } finally {
      setPhotoLoading(false)
    }
  }

  // Handle photo remove
  const handlePhotoRemove = async () => {
    if (!userProfile?.profile_img) return

    try {
      setPhotoLoading(true)
      setError('')
      const result = await removeProfilePhoto()
      
      // Update user profile to remove photo - use result from API
      setUserProfile({
        ...userProfile,
        profile_img: result.profile_img || null
      })
    } catch (err) {
      console.error('Photo remove error:', err)
      setError(err.message || 'Failed to remove photo')
    } finally {
      setPhotoLoading(false)
    }
  }

  // Trigger file input click
  const triggerPhotoUpload = () => {
    fileInputRef.current?.click()
  }

  // Get full image URL
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

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  const handleEdit = () => {
    setIsEditing(true)
  }

  const handleSave = async () => {
    try {
      setLoading(true)
      setError('')

      // Prepare data for backend (only fields it knows)
      const payload = {
        name: editedProfile.name,
        phone: editedProfile.phone || '',
        dob: editedProfile.dateOfBirth || '',
        state: editedProfile.state || '',
        city: editedProfile.city || '',
        pincode: editedProfile.pincode || '',
      }

      const updated = await updateProfile(payload)

      const updatedProfile = {
        ...userProfile,
        ...editedProfile,
        name: updated.name,
        email: updated.email,
        phone: updated.phone,
        dateOfBirth: updated.dob || editedProfile.dateOfBirth,
        dob: updated.dob,
        state: updated.state,
        city: updated.city,
        pincode: updated.pincode,
        mode: updated.mode || userProfile?.mode,
        created_at: updated.created_at || userProfile?.created_at,
        createdAt: updated.created_at || userProfile?.created_at,
      }

      setUserProfile(updatedProfile)
      setIsEditing(false)
    } catch (err) {
      console.error('Profile save error:', err)
      setError(err.message || 'Failed to save profile')
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    setEditedProfile({
      name: userProfile?.name || '',
      email: userProfile?.email || '',
      phone: userProfile?.phone || '',
      dateOfBirth: userProfile?.dateOfBirth || '',
      role: userProfile?.role || '',
      skills: userProfile?.skills || ''
    })
    setIsEditing(false)
  }

  const handleChange = (e) => {
    setEditedProfile({
      ...editedProfile,
      [e.target.name]: e.target.value
    })
  }

  return (
    <div className="profile-container">
      <Navbar userProfile={userProfile} />

      <div className="profile-content">
        {error && (
          <div className="profile-error">
            {error}
          </div>
        )}
        <motion.div
          className="profile-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="profile-top-actions">
            <button className="action-button secondary" onClick={() => navigate('/dashboard')}>
              Back to Dashboard
            </button>
          </div>
          <div className="profile-header-section">
            <div className="profile-avatar-container">
              {getProfileImageUrl() ? (
                <img 
                  src={getProfileImageUrl()} 
                  alt="Profile" 
                  className="profile-avatar-image"
                />
              ) : (
                <div className="profile-avatar-large">
                  {userProfile?.name ? userProfile.name.charAt(0).toUpperCase() : 'U'}
                </div>
              )}
              <div className="profile-photo-actions">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handlePhotoUpload}
                  accept="image/jpeg,image/png,image/gif,image/webp"
                  style={{ display: 'none' }}
                />
                <button 
                  className="photo-action-btn upload-btn"
                  onClick={triggerPhotoUpload}
                  disabled={photoLoading}
                  title="Upload photo"
                >
                  {photoLoading ? '...' : '📷'}
                </button>
                <button 
                  className="photo-action-btn remove-btn"
                  onClick={handlePhotoRemove}
                  disabled={photoLoading || !userProfile?.profile_img}
                  title={userProfile?.profile_img ? "Remove photo" : "No photo to remove"}
                  style={{ opacity: userProfile?.profile_img ? 1 : 0.4 }}
                >
                  {photoLoading ? '...' : '🗑️'}
                </button>
              </div>
            </div>
            <div className="profile-header-info">
              <h1>{userProfile?.name || 'User'}</h1>
              <p>{userProfile?.email || 'No email provided'}</p>
              {userProfile?.employment_type && (
                <span className={`profile-role role-${userProfile.employment_type.toLowerCase().replace(' ', '-')}`}>
                  {userProfile.employment_type === 'Company Employee' && '🏢 '}
                  {userProfile.employment_type === 'Freelancer' && '💼 '}
                  {userProfile.employment_type === 'Guest User' && '👤 '}
                  {userProfile.employment_type}
                </span>
              )}
            </div>
            {!isEditing ? (
              <button className="edit-profile-btn" onClick={handleEdit}>
                {loading ? 'Loading...' : 'Edit Profile'}
              </button>
            ) : (
              <div className="edit-actions-header">
                <button className="save-btn" onClick={handleSave}>
                  Save
                </button>
                <button className="cancel-btn" onClick={handleCancel}>
                  Cancel
                </button>
              </div>
            )}
          </div>

          <div className="profile-divider-main"></div>

          <div className="profile-sections">
            <motion.div
              className="profile-section"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <h2>Personal Information</h2>
              <div className="info-grid">
                <div className="info-item">
                  <span className="info-label">Full Name</span>
                  {isEditing ? (
                    <input
                      type="text"
                      name="name"
                      value={editedProfile.name}
                      onChange={handleChange}
                      className="profile-input"
                      placeholder="Enter your name"
                    />
                  ) : (
                    <span className="info-value">{userProfile?.name || 'Not set'}</span>
                  )}
                </div>
                <div className="info-item">
                  <span className="info-label">Email Address</span>
                  {isEditing ? (
                    <input
                      type="email"
                      name="email"
                      value={editedProfile.email}
                      onChange={handleChange}
                      className="profile-input"
                      placeholder="Enter your email"
                    />
                  ) : (
                    <span className="info-value">{userProfile?.email || 'Not set'}</span>
                  )}
                </div>
                <div className="info-item">
                  <span className="info-label">Phone Number</span>
                  {isEditing ? (
                    <input
                      type="tel"
                      name="phone"
                      value={editedProfile.phone}
                      onChange={handleChange}
                      className="profile-input"
                      placeholder="Enter your phone number"
                    />
                  ) : (
                    <span className="info-value">{userProfile?.phone || 'Not set'}</span>
                  )}
                </div>
                <div className="info-item">
                  <span className="info-label">Date of Birth</span>
                  {isEditing ? (
                    <input
                      type="date"
                      name="dateOfBirth"
                      value={editedProfile.dateOfBirth}
                      onChange={handleChange}
                      className="profile-input"
                    />
                  ) : (
                    <span className="info-value">
                      {userProfile?.dateOfBirth
                        ? new Date(userProfile.dateOfBirth).toLocaleDateString()
                        : 'Not set'}
                    </span>
                  )}
                </div>
                <div className="info-item">
                  <span className="info-label">State</span>
                  {isEditing ? (
                    <input
                      type="text"
                      name="state"
                      value={editedProfile.state}
                      onChange={handleChange}
                      className="profile-input"
                      placeholder="Enter your state"
                    />
                  ) : (
                    <span className="info-value">{userProfile?.state || 'Not set'}</span>
                  )}
                </div>
                <div className="info-item">
                  <span className="info-label">City</span>
                  {isEditing ? (
                    <input
                      type="text"
                      name="city"
                      value={editedProfile.city}
                      onChange={handleChange}
                      className="profile-input"
                      placeholder="Enter your city"
                    />
                  ) : (
                    <span className="info-value">{userProfile?.city || 'Not set'}</span>
                  )}
                </div>
                <div className="info-item">
                  <span className="info-label">Pincode</span>
                  {isEditing ? (
                    <input
                      type="text"
                      name="pincode"
                      value={editedProfile.pincode}
                      onChange={handleChange}
                      className="profile-input"
                      placeholder="Enter your pincode"
                      maxLength="6"
                    />
                  ) : (
                    <span className="info-value">{userProfile?.pincode || 'Not set'}</span>
                  )}
                </div>
              </div>
            </motion.div>

            <motion.div
              className="profile-section"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <h2>Account Information</h2>
              <div className="info-grid">
                <div className="info-item">
                  <span className="info-label">Account Created Date</span>
                  <span className="info-value">
                    {userProfile?.created_at || userProfile?.createdAt
                      ? new Date(userProfile.created_at || userProfile.createdAt).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })
                      : 'Not available'}
                  </span>
                </div>
                <div className="info-item">
                  <span className="info-label">Account Created Time</span>
                  <span className="info-value">
                    {userProfile?.created_at || userProfile?.createdAt
                      ? new Date(userProfile.created_at || userProfile.createdAt).toLocaleTimeString('en-US', {
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit',
                          hour12: true
                        })
                      : 'Not available'}
                  </span>
                </div>
              </div>
            </motion.div>

            <motion.div
              className="profile-section"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <h2>Employment Information</h2>
              <div className="info-grid">
                <div className="info-item">
                  <span className="info-label">Employment Type</span>
                  <span className="info-value employment-type-value">
                    {userProfile?.employment_type || 'Not set'}
                  </span>
                </div>
                {userProfile?.employment_type === 'Company Employee' && userProfile?.employeeId && (
                  <div className="info-item">
                    <span className="info-label">Employee ID</span>
                    <span className="info-value id-badge">{userProfile.employeeId}</span>
                  </div>
                )}
                {userProfile?.employment_type === 'Freelancer' && userProfile?.freelancerId && (
                  <div className="info-item">
                    <span className="info-label">Freelancer ID</span>
                    <span className="info-value id-badge">{userProfile.freelancerId}</span>
                  </div>
                )}
                <div className="info-item">
                  <span className="info-label">Skills</span>
                  {isEditing ? (
                    <input
                      type="text"
                      name="skills"
                      value={editedProfile.skills}
                      onChange={handleChange}
                      className="profile-input"
                      placeholder="Enter your skills (comma separated)"
                    />
                  ) : (
                    <span className="info-value">{userProfile?.skills || 'Not set'}</span>
                  )}
                </div>
              </div>
            </motion.div>
          </div>

          <div className="profile-actions">
            <button className="action-button danger" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default Profile

