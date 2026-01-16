import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { login } from '../config/api'
import { useApp } from '../context/AppContext'
import './Login.css'

const Login = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState({})
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [authError, setAuthError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const navigate = useNavigate()
  const location = useLocation()
  const { isAuthenticated, userProfile, setIsAuthenticated, setUserProfile, logout } = useApp()

  // Admin mode is disabled as per separation request
  const isAdminPanelMode = false

  useEffect(() => {
    // If arriving at login with ?admin=true but already logged in as a normal user, 
    // we should log out so the user can sign in with admin credentials.
    const handleAuthState = async () => {
      if (isAuthenticated) {
        if (isAdminPanelMode) {
          if (userProfile?.mode === 'admin') {
            // Already an admin, just go to admin panel
            navigate('/admin', { replace: true })
          } else {
            // Logged in as user but wants admin, clear session
            await logout()
          }
        } else if (userProfile?.mode === 'admin') {
          // Already logged in as admin, visiting regular login, send to admin
          navigate('/admin', { replace: true })
        } else {
          // Already logged in as user, visiting regular login, send to dashboard
          navigate('/dashboard', { replace: true })
        }
      }
    }

    handleAuthState()

    if (location.state?.message) {
      setSuccessMessage(location.state.message)
      // Clear the message from location state
      window.history.replaceState({}, document.title)
    }
  }, [location, isAuthenticated, userProfile, isAdminPanelMode, logout, navigate])

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const validatePassword = (password) => {
    return password.length >= 8
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    if (name === 'email') {
      setEmail(value)
    } else if (name === 'password') {
      setPassword(value)
    }

    // Clear errors when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }))
    }
    if (authError) {
      setAuthError('')
    }
  }

  const handleBlur = (e) => {
    const { name, value } = e.target
    let error = ''

    if (name === 'email') {
      if (!value) {
        error = 'Email address is required'
      } else if (!validateEmail(value)) {
        error = 'Please enter a valid email address'
      }
    } else if (name === 'password') {
      if (!value) {
        error = 'Password is required'
      } else if (!validatePassword(value)) {
        error = 'Password must be at least 8 characters'
      }
    }

    if (error) {
      setErrors(prev => ({
        ...prev,
        [name]: error
      }))
    }
  }

  const isFormValid = () => {
    return validateEmail(email) && validatePassword(password)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setAuthError('')

    // Validate form
    if (!validateEmail(email)) {
      setErrors({ email: 'Please enter a valid email address' })
      return
    }
    if (!validatePassword(password)) {
      setErrors({ password: 'Password must be at least 8 characters' })
      return
    }

    setIsLoading(true)
    setAuthError('') // Clear any previous errors

    try {
      const data = await login(email, password)

      // Set user profile from response
      const userProfileData = {
        id: data.user?.id || data.user_id || data.id,
        name: data.user?.name || data.name || '',
        email: data.user?.email || data.email || email,
        mode: data.user?.mode || data.mode || 'user',
        role: data.user?.role || data.role || '',
        employment_type: data.user?.employment_type || data.employment_type || null,
        employeeId: data.user?.employee_id || data.employee_id || '',
        freelancerId: data.user?.freelancer_id || data.freelancer_id || '',
        profile_img: data.user?.profile_img || data.profile_img || null,
        created_at: data.user?.created_at || data.created_at || new Date().toISOString()
      }

      setIsAuthenticated(true)
      setUserProfile(userProfileData)
      setIsLoading(false)

      // Determine where to redirect
      const from = location.state?.from?.pathname
      if (from) {
        navigate(from, { replace: true })
      } else {
        navigate('/dashboard')
      }
    } catch (error) {
      console.error('Login error:', error)
      setAuthError(error.message || 'Invalid email or password. Please try again.')
      setIsLoading(false)
    }
  }

  return (
    <div className="login-container">
      <motion.div
        className="auth-page-wrapper"
        initial={{ rotateY: -180, opacity: 0 }}
        animate={{ rotateY: 0, opacity: 1 }}
        exit={{ rotateY: 180, opacity: 0 }}
        transition={{ duration: 0.8, ease: "easeInOut" }}
      >
        <div className="login-card">
          <motion.div
            className="brand-header"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h1 className="brand-title">Techbank.Ai</h1>
            <p className="brand-tagline">Advanced Resume Screening & Management Platform</p>
          </motion.div>

          <motion.h2
            className="login-title"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            Welcome Back
          </motion.h2>

          <motion.p
            className="login-subtitle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            Login to access your account
          </motion.p>

          <form onSubmit={handleSubmit} className="login-form">
            {successMessage && (
              <motion.div
                className="auth-success"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                {successMessage}
              </motion.div>
            )}
            {authError && (
              <motion.div
                className="auth-error"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                {authError}
              </motion.div>
            )}

            <motion.div
              className="form-group"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
            >
              <label htmlFor="email">Email Address</label>
              <input
                type="email"
                id="email"
                name="email"
                value={email}
                onChange={handleChange}
                onBlur={handleBlur}
                placeholder="example@gmail.com"
                className={errors.email ? 'error' : ''}
                autoComplete="off"
              />
              {errors.email && <span className="error-message">{errors.email}</span>}
            </motion.div>

            <motion.div
              className="form-group"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 }}
            >
              <label htmlFor="password">Password</label>
              <div className="password-input-wrapper">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  name="password"
                  value={password}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  placeholder="Enter your password"
                  className={errors.password ? 'error' : ''}
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>
              {errors.password && <span className="error-message">{errors.password}</span>}
            </motion.div>

            <motion.div
              className="forgot-password-link"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.55 }}
            >
              <Link to="/forgot-password" className="forgot-link">
                Forgot Password?
              </Link>
            </motion.div>

            <motion.button
              type="submit"
              className="login-button"
              disabled={!isFormValid() || isLoading}
              whileHover={isFormValid() && !isLoading ? { scale: 1.02 } : {}}
              whileTap={isFormValid() && !isLoading ? { scale: 0.98 } : {}}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
            >
              {isLoading ? 'Logging in...' : 'Login'}
            </motion.button>

            <motion.div
              className="login-footer"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.7 }}
            >
              <p>
                Don't have an account?{' '}
                <Link to="/signup" className="signup-link">
                  Sign Up
                </Link>
              </p>
            </motion.div>
          </form>
        </div>
      </motion.div>
    </div>
  )
}

export default Login

