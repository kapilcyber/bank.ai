import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../context/AppContext'

const FREELANCER_TYPE = {
  id: 'freelancer',
  title: 'Freelancer',
  icon: '💼',
  description: 'Independent contractor or self-employed',
  color: '#4facfe'
}

const FreelancerPortal = () => {
  const navigate = useNavigate()
  const { setSelectedEmploymentType, setPortalEmployeeId } = useApp()

  useEffect(() => {
    setPortalEmployeeId(null)
    setSelectedEmploymentType(FREELANCER_TYPE)
    navigate('/application', { replace: true })
  }, [navigate, setSelectedEmploymentType, setPortalEmployeeId])

  return null
}

export default FreelancerPortal
