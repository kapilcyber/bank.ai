import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../context/AppContext'

const GUEST_TYPE = {
  id: 'guest-user',
  title: 'Guest User',
  icon: '👤',
  description: 'Temporary or guest access',
  color: '#43e97b'
}

const GuestPortal = () => {
  const navigate = useNavigate()
  const { setSelectedEmploymentType, setPortalEmployeeId } = useApp()

  useEffect(() => {
    setPortalEmployeeId(null)
    setSelectedEmploymentType(GUEST_TYPE)
    navigate('/application', { replace: true })
  }, [navigate, setSelectedEmploymentType, setPortalEmployeeId])

  return null
}

export default GuestPortal
