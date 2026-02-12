import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { login, adminSignup, isAdminRole } from '../config/api'
import AdminTransition from '../components/admin/AdminTransition'
import StartupSequence from '../components/StartupSequence'
import './LandingPage.css'

const ADMIN_ROLES = ['Admin', 'Talent Acquisition', 'HR']

const LandingPage = () => {
    const [showSignup, setShowSignup] = useState(false)
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [errors, setErrors] = useState({})
    const [showPassword, setShowPassword] = useState(false)
    const [signupData, setSignupData] = useState({
        name: '',
        email: '',
        password: '',
        confirmPassword: '',
        role: 'Admin',
        employeeId: ''
    })
    const [isLoading, setIsLoading] = useState(false)
    const [authError, setAuthError] = useState('')
    const [authSuccess, setAuthSuccess] = useState('')
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
                if (isAdminRole(userProfile?.mode)) {
                    navigate('/admin', { replace: true })
                } else {
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
        if (showSignup && Object.keys(signupData).includes(name)) {
            setSignupData(prev => ({ ...prev, [name]: value }))
        } else if (name === 'email') {
            setEmail(value)
        } else if (name === 'password') {
            setPassword(value)
        }

        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }))
        }
        if (authError) setAuthError('')
        if (authSuccess) setAuthSuccess('')
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

    const isSignupValid = () => {
        const { name, email: em, password: pw, confirmPassword, employeeId } = signupData
        const n = (name || '').trim()
        const e = (em || '').trim()
        const p = (pw || '').trim()
        const c = (confirmPassword || '').trim()
        const emp = (employeeId || '').trim()
        if (n.length < 2) return false
        if (!e || !validateEmail(e)) return false
        if (!p || p.length < 8) return false
        if (p !== c) return false
        if (!emp) return false
        return true
    }

    /** Returns the first signup validation error message, or null if valid. */
    const getSignupValidationError = () => {
        const { name, email: em, password: pw, confirmPassword, employeeId } = signupData
        const n = (name || '').trim()
        const e = (em || '').trim()
        const p = (pw || '').trim()
        const c = (confirmPassword || '').trim()
        const emp = (employeeId || '').trim()
        if (n.length < 2) return 'Name must be at least 2 characters.'
        if (!e) return 'Email is required.'
        if (!validateEmail(e)) return 'Please enter a valid email address.'
        if (!p) return 'Password is required.'
        if (p.length < 8) return 'Password must be at least 8 characters.'
        if (p !== c) return 'Passwords do not match.'
        if (!emp) return 'Employee ID is required.'
        return null
    }

    const handleSignupSubmit = async (e) => {
        e.preventDefault()
        setAuthError('')
        const { name, email: em, password: pw, confirmPassword, role, employeeId } = signupData
        if (!name?.trim()) {
            setErrors({ name: 'Name is required' })
            return
        }
        if (name.trim().length < 2) {
            setErrors({ name: 'Name must be at least 2 characters' })
            return
        }
        if (!validateEmail(em)) {
            setErrors({ email: 'Please enter a valid email address' })
            return
        }
        if (!validatePassword(pw)) {
            setErrors({ password: 'Password must be at least 8 characters' })
            return
        }
        if (pw !== confirmPassword) {
            setErrors({ confirmPassword: 'Passwords do not match' })
            return
        }
        if (!employeeId?.trim()) {
            setErrors({ employeeId: 'Employee ID is required' })
            return
        }

        setIsLoading(true)
        try {
            await adminSignup({
                name: name.trim(),
                email: em.trim().toLowerCase(),
                password: pw,
                role: role || 'Admin',
                employee_id: employeeId.trim()
            })
            setAuthError('')
            setAuthSuccess('Account created. Please log in.')
            setShowSignup(false)
            setEmail(em)
            setPassword('')
            setSignupData({ name: '', email: '', password: '', confirmPassword: '', role: 'Admin', employeeId: '' })
        } catch (error) {
            setAuthError(error.message || 'Signup failed. Please try again.')
        } finally {
            setIsLoading(false)
        }
    }

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
              employee_id: data.user?.employee_id || null,
              created_at: data.user?.created_at || new Date().toISOString()
            }

            if (isAdminRole(userProfileData.mode)) {
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
                <img src="/Untitled-1.png" alt="Women Owned" className="logo-left" />
                <img src="/cache.png" alt="Cache" className="logo-right" />
            </div>
            <motion.div
                className="auth-page-wrapper"
                initial={{ rotateY: -180, opacity: 0 }}
                animate={{ rotateY: 0, opacity: 1 }}
                exit={{ rotateY: 180, opacity: 0 }}
                transition={{ duration: 0.8, ease: "easeInOut" }}
            >
                <div className={`login-card ${showSignup ? 'login-card--signup' : ''}`}>
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

                    {showSignup ? (
                        <form onSubmit={handleSignupSubmit} className="login-form login-form--signup">
                            <div className="signup-row">
                                <motion.div className="form-group" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
                                    <label htmlFor="signup-name">Name <span className="required">*</span></label>
                                    <input
                                        type="text"
                                        id="signup-name"
                                        name="name"
                                        value={signupData.name}
                                        onChange={handleChange}
                                        placeholder="Full name"
                                        className={errors.name ? 'error' : ''}
                                        autoComplete="name"
                                    />
                                    {errors.name && <span className="error-message">{errors.name}</span>}
                                </motion.div>
                                <motion.div className="form-group" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
                                    <label htmlFor="signup-email">Email <span className="required">*</span></label>
                                    <input
                                        type="email"
                                        id="signup-email"
                                        name="email"
                                        value={signupData.email}
                                        onChange={handleChange}
                                        placeholder="admin@techbank.ai"
                                        className={errors.email ? 'error' : ''}
                                        autoComplete="email"
                                    />
                                    {errors.email && <span className="error-message">{errors.email}</span>}
                                </motion.div>
                            </div>
                            <div className="signup-row">
                                <motion.div className="form-group" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.25 }}>
                                    <label htmlFor="signup-password">Password <span className="required">*</span></label>
                                    <div className="password-input-wrapper">
                                        <input
                                            type={showPassword ? 'text' : 'password'}
                                            id="signup-password"
                                            name="password"
                                            value={signupData.password}
                                            onChange={handleChange}
                                            placeholder="Min 8 characters"
                                            className={errors.password ? 'error' : ''}
                                            autoComplete="new-password"
                                        />
                                        <button
                                            type="button"
                                            className="password-toggle"
                                            onClick={() => setShowPassword(!showPassword)}
                                            aria-label={showPassword ? 'Hide password' : 'Show password'}
                                        >
                                            👁️
                                        </button>
                                    </div>
                                    {errors.password && <span className="error-message">{errors.password}</span>}
                                </motion.div>
                                <motion.div className="form-group" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.25 }}>
                                    <label htmlFor="signup-confirm">Confirm Password <span className="required">*</span></label>
                                    <div className="password-input-wrapper">
                                        <input
                                            type={showPassword ? 'text' : 'password'}
                                            id="signup-confirm"
                                            name="confirmPassword"
                                            value={signupData.confirmPassword}
                                            onChange={handleChange}
                                            placeholder="Re-enter password"
                                            className={errors.confirmPassword ? 'error' : ''}
                                            autoComplete="new-password"
                                        />
                                        <button
                                            type="button"
                                            className="password-toggle"
                                            onClick={() => setShowPassword(!showPassword)}
                                            aria-label={showPassword ? 'Hide password' : 'Show password'}
                                        >
                                            👁️
                                        </button>
                                    </div>
                                    {errors.confirmPassword && <span className="error-message">{errors.confirmPassword}</span>}
                                </motion.div>
                            </div>
                            <div className="signup-row">
                                <motion.div className="form-group" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}>
                                    <label htmlFor="signup-role">Role <span className="required">*</span></label>
                                    <select id="signup-role" name="role" value={signupData.role} onChange={handleChange} className="signup-select">
                                        {ADMIN_ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                                    </select>
                                </motion.div>
                                <motion.div className="form-group" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.35 }}>
                                    <label htmlFor="signup-employee">Employee ID <span className="required">*</span></label>
                                    <input
                                        type="text"
                                        id="signup-employee"
                                        name="employeeId"
                                        value={signupData.employeeId}
                                        onChange={handleChange}
                                        placeholder="Employee ID"
                                        className={errors.employeeId ? 'error' : ''}
                                        autoComplete="off"
                                    />
                                    {errors.employeeId && <span className="error-message">{errors.employeeId}</span>}
                                    <p className="signup-field-hint">Must match your entry in the company list (verified on signup).</p>
                                </motion.div>
                            </div>
                            {!isSignupValid() && getSignupValidationError() && (
                                <p className="signup-hint" role="alert">{getSignupValidationError()}</p>
                            )}
                            <motion.button
                                type="submit"
                                className="login-button"
                                disabled={!isSignupValid() || isLoading}
                                whileHover={isSignupValid() && !isLoading ? { scale: 1.02 } : {}}
                                whileTap={isSignupValid() && !isLoading ? { scale: 0.98 } : {}}
                            >
                                {isLoading ? 'Creating account...' : 'Sign up'}
                            </motion.button>
                            <p className="auth-toggle">
                                Already have an account?{' '}
                                <button type="button" className="auth-toggle-btn" onClick={() => { setShowSignup(false); setAuthError(''); setErrors({}); }}>
                                    Login
                                </button>
                            </p>
                        </form>
                    ) : (
                        <form onSubmit={handleSubmit} className="login-form">
                            {authSuccess && (
                                <p className="auth-success" role="status">{authSuccess}</p>
                            )}
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
                                        👁️
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
                            <p className="auth-toggle">
                                Don&apos;t have an account?{' '}
                                <button type="button" className="auth-toggle-btn" onClick={() => { setShowSignup(true); setAuthError(''); setAuthSuccess(''); setErrors({}); }}>
                                    Sign up
                                </button>
                            </p>
                        </form>
                    )}
                </div>
            </motion.div>
        </div>
    )
}

export default LandingPage
