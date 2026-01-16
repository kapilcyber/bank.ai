import { AnimatePresence } from 'framer-motion'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import { AppProvider } from './context/AppContext'
// import LandingPage from './pages/LandingPage'
import AuthBackground from './components/AuthBackground'
import Application from './pages/Application'
import Dashboard from './pages/Dashboard'
import ForgotPassword from './pages/ForgotPassword'
import Login from './pages/Login'
import Profile from './pages/Profile'
import SignUp from './pages/SignUp'
// import Admin from './pages/Admin'

function AppRoutes() {
  const location = useLocation()

  // Check if we should show the animated background (for auth pages and main dashboard/profile/application)
  const showBackground = ['/login', '/signup', '/forgot-password', '/dashboard', '/profile', '/application'].includes(location.pathname)

  return (
    <div style={{
      position: 'relative',
      width: '100%',
      minHeight: '100vh',
      margin: 0,
      padding: 0
    }}>
      {showBackground && <AuthBackground />}
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/application"
            element={
              <ProtectedRoute>
                <Application />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />
          {/* <Route
          path="/admin/*"
          element={
            <ProtectedRoute adminOnly={true}>
              <Admin />
            </ProtectedRoute>
          }
        /> */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AnimatePresence>
    </div>
  )
}

function App() {
  console.log('📱 App component rendering...')

  try {
    return (
      <AppProvider>
        <AppRoutes />
      </AppProvider>
    )
  } catch (error) {
    console.error('❌ Error in App component:', error)
    return (
      <div style={{ padding: '20px', color: 'red', fontFamily: 'Arial' }}>
        <h1>Error in App Component</h1>
        <p>{error.message}</p>
        <pre>{error.stack}</pre>
      </div>
    )
  }
}

export default App

