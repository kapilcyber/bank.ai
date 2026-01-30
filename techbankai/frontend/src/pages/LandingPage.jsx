import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { login } from '../config/api'
import AdminTransition from '../components/admin/AdminTransition'
import StartupSequence from '../components/StartupSequence'
import './LandingPage.css'

const LandingPage = () => {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [errors, setErrors] = useState({})
    const [showPassword, setShowPassword] = useState(false)
    const [isLoading, setIsLoading] = useState(false)
    const [authError, setAuthError] = useState('')
    const [showAdminTransition, setShowAdminTransition] = useState(false)
    const [showInitialStartup, setShowInitialStartup] = useState(() => {
        // Only show once per session
        return !sessionStorage.getItem('startupShown')
    })

    const navigate = useNavigate()
    const location = useLocation()
    const { isAuthenticated, userProfile, setIsAuthenticated, setUserProfile, logout } = useApp()

    useEffect(() => {
        const checkAuth = async () => {
            if (isAuthenticated && !showAdminTransition) {
                const isAdmin = userProfile?.mode?.toLowerCase().includes('admin')
                if (isAdmin) {
                    navigate('/admin', { replace: true })
                } else {
                    // If logged in as user but only admin is allowed now, logout
                    await logout()
                }
            }
        }
        checkAuth()
    }, [isAuthenticated, userProfile, navigate, logout, showAdminTransition])

    const validateEmail = (email) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        return emailRegex.test(email)
    }

    const validatePassword = (password) => {
        return password.length >= 8
    }

    const handleChange = (e) => {
        const { name, value } = e.target
        if (name === 'email') setEmail(value)
        else if (name === 'password') setPassword(value)

        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }))
        }
        if (authError) setAuthError('')
    }

    const handleBlur = (e) => {
        const { name, value } = e.target
        let error = ''
        if (name === 'email') {
            if (!value) error = 'Email address is required'
            else if (!validateEmail(value)) error = 'Please enter a valid email address'
        } else if (name === 'password') {
            if (!value) error = 'Password is required'
            else if (!validatePassword(value)) error = 'Password must be at least 8 characters'
        }
        if (error) setErrors(prev => ({ ...prev, [name]: error }))
    }

    const isFormValid = () => validateEmail(email) && validatePassword(password)

    const handleTransitionComplete = () => {
        sessionStorage.setItem('adminEntranceShown', 'true')
        const from = location.state?.from?.pathname || '/admin'
        navigate(from, { replace: true })
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setAuthError('')

        if (!validateEmail(email)) {
            setErrors({ email: 'Please enter a valid email address' })
            return
        }
        if (!validatePassword(password)) {
            setErrors({ password: 'Password must be at least 8 characters' })
            return
        }

        setIsLoading(true)
        try {
            const data = await login(email, password)
            const userProfileData = {
                id: data.user?.id || data.user_id,
                name: data.user?.name || '',
                email: data.user?.email || email,
                mode: data.user?.mode || 'user',
                profile_img: data.user?.profile_img || null,
                created_at: data.user?.created_at || new Date().toISOString()
            }

            const isAdmin = userProfileData.mode?.toLowerCase().includes('admin')

            if (isAdmin) {
                setIsAuthenticated(true)
                setUserProfile(userProfileData)
                setShowAdminTransition(true)
            } else {
                setAuthError('Access Denied: Admin credentials required.')
                await logout()
            }
        } catch (error) {
            setAuthError(error.message || 'Invalid email or password. Please try again.')
        } finally {
            setIsLoading(false)
        }
    }

    if (showInitialStartup) {
        return <StartupSequence onComplete={() => {
            setShowInitialStartup(false)
            sessionStorage.setItem('startupShown', 'true')
        }} />
    }

    if (showAdminTransition) {
        return <AdminTransition onComplete={handleTransitionComplete} />
    }

    return (
        <div className="login-container">
            {authError && (
                <div className="auth-popup-overlay" onClick={() => setAuthError('')}>
                    <motion.div
                        className="auth-popup"
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="auth-popup-icon">!</div>
                        <p className="auth-popup-message">{authError}</p>
                        <button
                            type="button"
                            className="auth-popup-btn"
                            onClick={() => setAuthError('')}
                        >
                            OK
                        </button>
                    </motion.div>
                </div>
            )}
            <div className="page-logos">
                <img src="/women.png" alt="Women Owned" className="logo-left" />
                <img src="/cache.png" alt="Cache" className="logo-right" />
            </div>
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
                        <h1 className="brand-title">TechBankAI</h1>
                        <div className="brand-tagline">
                            <span className="powered-by-text">powered by</span>
                            <img src="/cache.png" alt="Cache" className="cache-logo" />
                        </div>
                    </motion.div>

                    <form onSubmit={handleSubmit} className="login-form">
                        <motion.div
                            className="form-group"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.2 }}
                        >
                            <label htmlFor="email">Email Address <span className="required">*</span></label>
                            <input
                                type="email"
                                id="email"
                                name="email"
                                value={email}
                                onChange={handleChange}
                                onBlur={handleBlur}
                                placeholder="admin@techbank.ai"
                                className={errors.email ? 'error' : ''}
                                autoComplete="off"
                            />
                        </motion.div>

                        <motion.div
                            className="form-group"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.3 }}
                        >
                            <label htmlFor="password">Password <span className="required">*</span></label>
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
                        </motion.div>

                        <motion.button
                            type="submit"
                            className="login-button"
                            disabled={!isFormValid() || isLoading}
                            whileHover={isFormValid() && !isLoading ? { scale: 1.02 } : {}}
                            whileTap={isFormValid() && !isLoading ? { scale: 0.98 } : {}}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.4 }}
                        >
                            {isLoading ? 'Authenticating...' : 'Login to Admin Panel'}
                        </motion.button>
                    </form>
                </div>
            </motion.div>
        </div>
    )
}

export default LandingPage
