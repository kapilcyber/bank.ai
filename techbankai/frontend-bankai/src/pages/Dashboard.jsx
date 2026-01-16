import { motion } from 'framer-motion'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import EmploymentIcon from '../components/EmploymentIcon'
import Navbar from '../components/Navbar'
import { useApp } from '../context/AppContext'
import './Dashboard.css'

const Dashboard = () => {
  const [selectedType, setSelectedType] = useState(null)
  const [hoveredType, setHoveredType] = useState(null)
  const navigate = useNavigate()
  const { setSelectedEmploymentType, userProfile } = useApp()

  // User's employment_type is set during signup - show only their role card on Dashboard
  // They must click the card to proceed to application

  const allEmploymentTypes = [
    {
      id: 'company-employee',
      title: 'Company Employee',
      description: 'Full-time or part-time employee at a company',
      color: '#335c67', // Teal
      role: 'Company Employee' // Added role for filtering
    },
    {
      id: 'freelancer',
      title: 'Freelancer',
      description: 'Independent contractor or self-employed',
      color: '#e5383b', // Vibrant Red
      role: 'Freelancer' // Added role for filtering
    },
    {
      id: 'guest-user',
      title: 'Guest User',
      description: 'Temporary or guest access',
      color: '#ce4257' // Pink Red
    }
  ]

  // Filter types based on user's employment_type from signup
  // If user already has an employment_type, they'll be redirected anyway
  // This filter is a fallback that shows only matching type if already set
  const employmentTypes = allEmploymentTypes.filter(type => {
    // Show all types if no employment_type is set yet
    if (!userProfile?.employment_type) return true;

    const userEmploymentType = userProfile.employment_type.trim().toLowerCase();
    const typeTitle = type.title.trim().toLowerCase();

    return typeTitle === userEmploymentType;
  })

  const handleTypeSelect = async (type) => {
    setSelectedType(type.id)

    // User's employment_type was already verified during signup
    // Just set the selected type and navigate to application
    setSelectedEmploymentType(type)
    
    setTimeout(() => {
      navigate('/application')
    }, 500)
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  const cardVariants = {
    hidden: { opacity: 0, y: 50, scale: 0.9 },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 100
      }
    }
  }

  return (
    <div className="dashboard-container">
      <Navbar userProfile={userProfile} />

      <div className="dashboard-content">
        <motion.div
          className="dashboard-hero"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <motion.div
            className="hero-glass"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h1>Welcome, {userProfile?.name || 'User'}!</h1>
            <p>Your personalized career dashboard at Techbank.Ai</p>
          </motion.div>
        </motion.div>

        <motion.div
          className={`employment-types-grid ${employmentTypes.length === 1 ? 'single-card' : ''}`}
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {employmentTypes.map((type) => (
            <motion.div
              key={type.id}
              className={`employment-type-card ${selectedType === type.id ? 'selected' : ''}`}
              variants={cardVariants}
              whileHover={{
                scale: 1.05,
                y: -10,
                transition: { duration: 0.2 }
              }}
              whileTap={{ scale: 0.95 }}
              onClick={() => handleTypeSelect(type)}
              onMouseEnter={() => setHoveredType(type.id)}
              onMouseLeave={() => setHoveredType(null)}
              style={{
                '--type-color': type.color,
                '--type-color-rgb': type.id === 'company-employee' ? '51, 92, 103' :
                  type.id === 'freelancer' ? '229, 56, 59' :
                    '206, 66, 87',
                '--hover-bg-start': type.id === 'company-employee' ? 'rgba(51, 92, 103, 0.25)' :
                  type.id === 'freelancer' ? 'rgba(229, 56, 59, 0.3)' :
                    'rgba(206, 66, 87, 0.25)',
                '--hover-bg-end': 'rgba(255, 255, 255, 0.95)'
              }}
            >
              <div className="icon-wrapper">
                <EmploymentIcon
                  type={type.id}
                  isHovered={hoveredType === type.id}
                />
              </div>

              <h2>{type.title}</h2>
              <p>{type.description}</p>

              <motion.div
                className="selection-indicator"
                initial={{ scale: 0 }}
                animate={{
                  scale: selectedType === type.id ? 1 : 0,
                  opacity: selectedType === type.id ? 1 : 0
                }}
                transition={{ type: "spring", stiffness: 200 }}
              >
                ✓ Selected
              </motion.div>
            </motion.div>
          ))}
        </motion.div>

        {selectedType && (
          <motion.div
            className="continue-hint"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <p>Redirecting to application page...</p>
          </motion.div>
        )}
      </div>
    </div>
  )
}

export default Dashboard

