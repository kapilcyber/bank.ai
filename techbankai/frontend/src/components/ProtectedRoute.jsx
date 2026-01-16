import { Navigate, useLocation } from 'react-router-dom'
import { useApp } from '../context/AppContext'

const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { isAuthenticated, userProfile } = useApp()
  const location = useLocation()

  if (!isAuthenticated) {
    // Redirect to home (which is now Admin Login)
    const searchParams = adminOnly ? '?admin=true' : ''
    return <Navigate to={`/${searchParams}`} state={{ from: location }} replace />
  }

  if (adminOnly && !userProfile?.mode?.toLowerCase().includes('admin')) {
    // If admin access is required but user is not an admin, redirect to home
    return <Navigate to="/?admin=true" state={{ from: location }} replace />
  }

  return children
}

export default ProtectedRoute
