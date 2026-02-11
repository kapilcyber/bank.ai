import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { verifyEmployee } from '../config/api'
import './EmployeePortal.css'

const EMPLOYEE_TYPE = {
  id: 'company-employee',
  title: 'Company Employee',
  icon: '🏢',
  description: 'Full-time or part-time employee at a company',
  color: '#667eea'
}

const EmployeePortal = () => {
  const navigate = useNavigate()
  const { setSelectedEmploymentType, setPortalEmployeeId } = useApp()
  const [employeeId, setEmployeeId] = useState('')
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!employeeId.trim() || !email.trim()) {
      setError('Please enter your Employee ID and Email.')
      return
    }
    setLoading(true)
    try {
      const data = await verifyEmployee(employeeId.trim(), email.trim())
      if (data.valid) {
        setPortalEmployeeId(employeeId.trim().toUpperCase())
        setSelectedEmploymentType(EMPLOYEE_TYPE)
        navigate('/application', { replace: true })
      } else {
        setError(data.message || 'Employee ID and Email do not match company records.')
      }
    } catch (err) {
      setError(err.message || 'Verification failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="employee-portal-container">
      <div className="employee-portal-card">
        <motion.div
          className="employee-portal-header"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="employee-portal-title">Company Employee Portal</h1>
          <p className="employee-portal-subtitle">Enter your Employee ID and Email to continue</p>
        </motion.div>
        <form onSubmit={handleSubmit} className="employee-portal-form">
          {error && (
            <div className="employee-portal-error">{error}</div>
          )}
          <div className="form-group">
            <label htmlFor="employee-id">Employee ID <span className="required">*</span></label>
            <input
              type="text"
              id="employee-id"
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              placeholder="e.g. CT1001"
              disabled={loading}
              className={error ? 'error' : ''}
            />
          </div>
          <div className="form-group">
            <label htmlFor="employee-email">Email <span className="required">*</span></label>
            <input
              type="email"
              id="employee-email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your.email@company.com"
              disabled={loading}
              className={error ? 'error' : ''}
            />
          </div>
          <button type="submit" className="employee-portal-btn" disabled={loading}>
            {loading ? 'Verifying...' : 'Verify & Continue'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default EmployeePortal
