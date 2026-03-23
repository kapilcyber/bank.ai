import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
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
  const [searchParams] = useSearchParams()
  const { setSelectedEmploymentType, setPortalEmployeeId } = useApp()

  useEffect(() => {
    setPortalEmployeeId(null)
    setSelectedEmploymentType(GUEST_TYPE)
    const jobId = searchParams.get('jobId')
    // Defer navigation so AppContext updates before /application mounts (avoids Application redirecting to "/")
    queueMicrotask(() => {
      navigate('/application' + (jobId ? `?jobId=${jobId}` : ''), { replace: true })
    })
  }, [navigate, setSelectedEmploymentType, setPortalEmployeeId, searchParams])

  return null
}

export default GuestPortal
