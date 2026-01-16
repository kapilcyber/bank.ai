import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { login } from '../config/api'
import AdminTransition from '../components/admin/AdminTransition'
import StartupSequence from '../components/StartupSequence'
import CyberBackground from '../components/admin/CyberBackground'
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
        <div className="landing-container">
            <CyberBackground />

            <motion.div
                className="login-card"
                initial={{ opacity: 0, y: 50, scale: 0.8, filter: 'blur(10px)' }}
                animate={{ opacity: 1, y: 0, scale: 1, filter: 'blur(0px)' }}
                transition={{
                    duration: 1.2,
                    ease: [0.34, 1.56, 0.64, 1], // Custom bounce/back-out
                    opacity: { duration: 0.8 },
                    filter: { duration: 1 }
                }}
            >
                <div className="brand-header">
                    <h1 className="brand-title">TechBank.Ai</h1>
                    <p className="brand-tagline">Advanced Admin Portal</p>
                </div>

                <h2 className="login-title">Admin Login</h2>
                <p className="login-subtitle">Enter your credentials to access the management panel</p>

                <form onSubmit={handleSubmit} className="login-form">
                    {authError && (
                        <motion.div
                            className="auth-error"
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                        >
                            {authError}
                        </motion.div>
                    )}

                    <div className="form-group">
                        <label htmlFor="email">Email Address</label>
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
                        {errors.email && <span className="error-message">{errors.email}</span>}
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <div className="password-input-wrapper">
                            <input
                                type={showPassword ? 'text' : 'password'}
                                id="password"
                                name="password"
                                value={password}
                                onChange={handleChange}
                                onBlur={handleBlur}
                                placeholder="••••••••"
                                className={errors.password ? 'error' : ''}
                            />
                            <button
                                type="button"
                                className="password-toggle"
                                onClick={() => setShowPassword(!showPassword)}
                            >
                                {showPassword ? '🙈' : '👁️'}
                            </button>
                        </div>
                        {errors.password && <span className="error-message">{errors.password}</span>}
                    </div>

                    <button
                        type="submit"
                        className="login-button"
                        disabled={!isFormValid() || isLoading}
                    >
                        {isLoading ? 'Authenticating...' : 'Login to Admin Panel'}
                    </button>
                </form>
            </motion.div>
        </div>
    )
}

export default LandingPage
