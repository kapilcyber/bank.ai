import { Navigate, useLocation } from 'react-router-dom'
import { useApp } from '../context/AppContext'
import { isAdminRole } from '../config/api'

const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { isAuthenticated, userProfile } = useApp()
  const location = useLocation()

  if (!isAuthenticated) {
    const searchParams = adminOnly ? '?admin=true' : ''
    return <Navigate to={`/${searchParams}`} state={{ from: location }} replace />
  }

  if (adminOnly && !isAdminRole(userProfile?.mode)) {
    return <Navigate to="/?admin=true" state={{ from: location }} replace />
  }

  return children
}

export default ProtectedRoute
