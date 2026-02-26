import { Routes, Route, Navigate } from 'react-router-dom'
import { AppProvider } from './context/AppContext'
import ProtectedRoute from './components/ProtectedRoute'
import ErrorBoundary from './components/ErrorBoundary'
import LandingPage from './pages/LandingPage'
import SetPassword from './pages/SetPassword'
import Profile from './pages/Profile'
import Admin from './pages/Admin'
import GuestPortal from './pages/GuestPortal'
import FreelancerPortal from './pages/FreelancerPortal'
import EmployeePortal from './pages/EmployeePortal'
import Careers from './pages/Careers'
import Application from './pages/Application'

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/set-password" element={<SetPassword />} />
      <Route path="/guest" element={<GuestPortal />} />
      <Route path="/freelancer" element={<FreelancerPortal />} />
      <Route path="/employee" element={<EmployeePortal />} />
      {/* Careers: support /careers, /Careers, and /careers.html so reload always stays on careers */}
      <Route path="/careers" element={<Careers />} />
      <Route path="/Careers" element={<Navigate to="/careers" replace />} />
      <Route path="/careers.html" element={<Navigate to="/careers" replace />} />
      <Route path="/application" element={<Application />} />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/*"
        element={
          <ProtectedRoute adminOnly={true}>
            <Admin />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
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

