import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { getJobOpenings } from '../config/api'
import CareersHeader from '../components/CareersHeader'
import './Careers.css'

// Check if we're running as standalone (careers page on port 3005)
const isStandalone = typeof window !== 'undefined' && (
  window.location.port === '3005' || 
  document.getElementById('careers-root') !== null
)

// Icon mapping for different job types
const getJobIcon = (title) => {
  const titleLower = title?.toLowerCase() || ''
  
  if (titleLower.includes('sales') || titleLower.includes('executive')) {
    return '💼' // Briefcase icon
  } else if (titleLower.includes('security')) {
    return '🛡️' // Shield icon
  } else if (titleLower.includes('network')) {
    return '🌐' // Network icon
  } else if (titleLower.includes('infrastructure') || titleLower.includes('it')) {
    return '🖥️' // Monitor icon
  } else if (titleLower.includes('development') || titleLower.includes('manager')) {
    return '📈' // Upward trend icon
  } else if (titleLower.includes('mim')) {
    return '⚠️' // Warning triangle icon
  } else if (titleLower.includes('data') || titleLower.includes('ai')) {
    return '🤖' // AI/Data icon
  }
  return '💼' // Default briefcase icon
}

const categories = [
  { id: 'data-ai', name: 'Data/AI', keywords: ['data', 'ai', 'artificial intelligence', 'machine learning', 'ml', 'data engineer', 'data scientist'] },
  { id: 'sales-executive', name: 'Inside Sales Executive', keywords: ['sales', 'executive', 'inside sales'] },
  { id: 'security', name: 'Security Engineer', keywords: ['security', 'cyber', 'infosec'] },
  { id: 'networking', name: 'Networking Engineer', keywords: ['network', 'networking'] },
  { id: 'infrastructure', name: 'IT Infrastructure Engineer', keywords: ['infrastructure', 'it infrastructure', 'system', 'devops'] },
  { id: 'business-development', name: 'Business Development Manager', keywords: ['business development', 'bd', 'manager', 'development manager'] }
]

const Careers = () => {
  const [jobOpenings, setJobOpenings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [Navbar, setNavbar] = useState(null)
  const [userProfile, setUserProfile] = useState(null)

  // Load Navbar and AppContext only if not in standalone mode
  useEffect(() => {
    if (!isStandalone) {
      Promise.all([
        import('../components/Navbar').catch(() => null),
        import('../context/AppContext').catch(() => null)
      ]).then(([NavbarModule, AppContextModule]) => {
        if (NavbarModule) {
          setNavbar(() => NavbarModule.default)
        }
        if (AppContextModule && AppContextModule.useApp) {
          try {
            const { useApp } = AppContextModule
            // Try to use AppContext if available
          } catch (e) {
            // AppContext not available
          }
        }
      })
    }
  }, [])

  const handleApply = (jobId) => {
    // Redirect to guest page on port 3005
    window.location.href = `http://192.168.0.107:3005/guest?jobId=${jobId}`
  }

  useEffect(() => {
    const fetchJobOpenings = async () => {
      try {
        setLoading(true)
        const data = await getJobOpenings()
        // Handle both response formats - backend returns { jobs: [...] } or { job_openings: [...] }
        const jobs = Array.isArray(data) ? data : (data.jobs || data.job_openings || [])
        setJobOpenings(jobs)
        setError(null)
      } catch (err) {
        console.error('Error fetching job openings:', err)
        setError(err.message || 'Failed to load job openings')
      } finally {
        setLoading(false)
      }
    }

    fetchJobOpenings()
  }, [])

  // Filter jobs based on selected category
  const filteredJobs = jobOpenings.filter(job => {
    if (!selectedCategory) return true
    
    const category = categories.find(cat => cat.id === selectedCategory)
    if (!category) return true
    
    const jobTitle = job.title?.toLowerCase() || ''
    const businessArea = job.business_area?.toLowerCase() || ''
    const combined = `${jobTitle} ${businessArea}`
    
    return category.keywords.some(keyword => 
      combined.includes(keyword.toLowerCase())
    )
  })

  const handleCategoryClick = (categoryId) => {
    // Toggle: if same category clicked, deselect it
    setSelectedCategory(selectedCategory === categoryId ? null : categoryId)
  }

  return (
    <div className="careers-page">
      {isStandalone ? (
        <CareersHeader />
      ) : (
        Navbar && <Navbar userProfile={userProfile} showProfile={true} />
      )}
      <div className="careers-content">
        {/* Latest Jobs Section */}
        <motion.div
          className="latest-jobs-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="latest-jobs-header">
            <h2 className="latest-jobs-title">Latest Jobs</h2>
          </div>
          
          <p className="latest-jobs-description">
            At Cache, we combine human ingenuity with breakthrough technology and foster innovation for an inclusive workplace.
          </p>

          {/* Category Filters */}
          <div className="category-filters">
            {categories.map((category) => (
              <motion.div
                key={category.id}
                className={`category-filter ${selectedCategory === category.id ? 'active' : ''}`}
                onClick={() => handleCategoryClick(category.id)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                transition={{ duration: 0.2 }}
              >
                {category.name}
              </motion.div>
            ))}
          </div>

          {loading && (
            <div className="loading-state">
              <p>Loading job openings...</p>
            </div>
          )}
          
          {error && (
            <div className="error-state">
              <p className="error">Error: {error}</p>
            </div>
          )}
          
          {!loading && !error && (
            <>
              {/* Only show job openings when a category is selected */}
              {selectedCategory && (
                <motion.div
                  className="job-openings-grid"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  {filteredJobs.length === 0 ? (
                    <div className="no-jobs-message">
                      <p>
                        No job openings found for "{categories.find(c => c.id === selectedCategory)?.name}".
                      </p>
                      <button 
                        className="clear-filter-button"
                        onClick={() => setSelectedCategory(null)}
                      >
                        Back to Categories
                      </button>
                    </div>
                  ) : (
                    filteredJobs.map((job) => (
                      <motion.div
                        key={job.job_id || job.id}
                        className="job-card"
                        whileHover={{ scale: 1.02, boxShadow: '0 8px 16px rgba(0,0,0,0.15)' }}
                        transition={{ duration: 0.2 }}
                      >
                        <div className="job-icon">{getJobIcon(job.title)}</div>
                        <div className="job-content">
                          <h3 className="job-title">{job.title}</h3>
                          <p className="job-location">
                            {job.location 
                              ? job.location.includes('|') 
                                ? job.location 
                                : `India | ${job.location}`
                              : 'India | Location not specified'}
                          </p>
                          <p className="job-business-area">
                            Business Area: <span>{job.business_area || 'Not specified'}</span>
                          </p>
                          <button
                            className="apply-button"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleApply(job.job_id || job.id)
                            }}
                          >
                            Apply Now
                          </button>
                        </div>
                      </motion.div>
                    ))
                  )}
                </motion.div>
              )}
              
              {/* Show message when no category is selected */}
              {!selectedCategory && !loading && !error && (
                <div className="select-category-message">
                  <p>Select a category above to view job openings</p>
                </div>
              )}
            </>
          )}
        </motion.div>
      </div>
    </div>
  )
}

export default Careers
