import { motion, AnimatePresence } from 'framer-motion'
import { useEffect } from 'react'
import './ResumeNotificationModal.css'

const ResumeNotificationModal = ({ isOpen, onClose, autoFilledFields = [] }) => {
  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        onClose()
      }, 10000) // Auto-dismiss after 10 seconds

      return () => clearTimeout(timer)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const fieldNames = {
    firstName: 'First Name',
    lastName: 'Last Name',
    email: 'Email',
    phone: 'Phone',
    address: 'Address',
    city: 'City',
    country: 'Country',
    zipCode: 'Zip Code',
    role: 'Role',
    currentCompany: 'Current Company',
    experience: 'Experience',
    skills: 'Skills',
    education: 'Education'
  }

  const filledFieldsList = autoFilledFields.map(f => fieldNames[f] || f).join(', ')

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="resume-notification-toast"
          initial={{ opacity: 0, x: 400, scale: 0.9 }}
          animate={{ opacity: 1, x: 0, scale: 1 }}
          exit={{ opacity: 0, x: 400, scale: 0.9 }}
          transition={{ type: "spring", stiffness: 300, damping: 25 }}
        >
          <div className="toast-header">
            <div className="toast-success-icon">✓</div>
            <h4 className="toast-title">Resume parsed successfully!</h4>
            <button className="toast-close-btn" onClick={onClose}>×</button>
          </div>
          
          <div className="toast-body">
            <div className="toast-item">
              <span className="toast-icon">📄</span>
              <span className="toast-text">
                Auto-filled <strong>{autoFilledFields.length}</strong> field(s): {filledFieldsList}
              </span>
            </div>
            
            <div className="toast-item">
              <span className="toast-icon">✏️</span>
              <span className="toast-text">You can now review and edit any field as needed.</span>
            </div>
            
            <div className="toast-item">
              <span className="toast-icon">✨</span>
              <span className="toast-text">Fields with ✨ icon are auto-filled and can be edited.</span>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default ResumeNotificationModal
