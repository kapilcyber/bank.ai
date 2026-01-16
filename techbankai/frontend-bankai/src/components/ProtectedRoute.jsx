import { Navigate, useLocation } from 'react-router-dom'
import { useApp } from '../context/AppContext'

const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { isAuthenticated, userProfile } = useApp()
  const location = useLocation()

  if (!isAuthenticated) {
    // Redirect to login with the attempted location
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children
}

export default ProtectedRoute
