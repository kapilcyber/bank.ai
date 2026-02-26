import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { getJobOpenings, API_BASE_URL } from '../config/api'
import CareersHeader from '../components/CareersHeader'
import './Careers.css'

// Full URL for JD PDF (backend serves uploads at same host, path like /uploads/jd/...)
const getJdPdfUrl = (jdFileUrl) => {
  if (!jdFileUrl) return null
  if (jdFileUrl.startsWith('http://') || jdFileUrl.startsWith('https://')) return jdFileUrl
  const origin = (API_BASE_URL || '').replace(/\/api\/?$/, '')
  return `${origin}${jdFileUrl.startsWith('/') ? '' : '/'}${jdFileUrl}`
}

// Check if we're running as standalone (careers page on port 3005)
const isStandalone = typeof window !== 'undefined' && (
  window.location.port === '3005' || 
  document.getElementById('careers-root') !== null
)

// Display label for job_type (internship, full_time, remote, hybrid, contract)
const getJobTypeLabel = (jobType) => {
  if (!jobType) return null
  const labels = {
    internship: 'Internship',
    full_time: 'Full-time',
    remote: 'Remote',
    hybrid: 'Hybrid',
    contract: 'Contract'
  }
  return labels[jobType] || jobType.replace('_', '-')
}

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
  const navigate = useNavigate()
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
    // Redirect to guest portal with job ID (guest sets employment type and goes to application)
    if (isStandalone) {
      const guestBaseUrl = import.meta.env.VITE_CAREERS_GUEST_REDIRECT_URL || window.location.origin.replace(':3005', ':3003')
      window.location.href = `${guestBaseUrl}/guest?jobId=${jobId}`
    } else {
      navigate(`/guest?jobId=${jobId}`)
    }
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

  // Filter jobs: null = "View all" (show all), otherwise filter by category
  const filteredJobs = !selectedCategory
    ? jobOpenings
    : jobOpenings.filter(job => {
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
        <motion.div
          className="latest-jobs-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Hero */}
          <div className="careers-hero">
            <span className="careers-hero-pill">We're hiring!</span>
            <h1 className="careers-hero-title">Be part of our mission</h1>
            <p className="careers-hero-description">
              We're looking for passionate people to join us on our mission. We value flat hierarchies, clear communication, and full ownership and responsibility.
            </p>
          </div>

          {/* Category Filters: View all + categories */}
          <div className="category-filters">
            <motion.button
              type="button"
              className={`category-filter ${selectedCategory === null ? 'active' : ''}`}
              onClick={() => setSelectedCategory(null)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              transition={{ duration: 0.2 }}
            >
              View all
            </motion.button>
            {categories.map((category) => (
              <motion.button
                key={category.id}
                type="button"
                className={`category-filter ${selectedCategory === category.id ? 'active' : ''}`}
                onClick={() => handleCategoryClick(category.id)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                transition={{ duration: 0.2 }}
              >
                {category.name}
              </motion.button>
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
            <motion.div
              className="job-openings-list"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              {filteredJobs.length === 0 ? (
                <div className="no-jobs-message">
                  <p>
                    {selectedCategory
                      ? `No job openings found for "${categories.find(c => c.id === selectedCategory)?.name}".`
                      : 'No job openings at the moment.'}
                  </p>
                  {selectedCategory && (
                    <button
                      type="button"
                      className="clear-filter-button"
                      onClick={() => setSelectedCategory(null)}
                    >
                      View all
                    </button>
                  )}
                </div>
              ) : (
                <div className="job-list">
                  {filteredJobs.map((job) => (
                    <motion.div
                      key={job.job_id || job.id}
                      className="job-row"
                      whileHover={{ backgroundColor: 'rgba(0,0,0,0.02)' }}
                      transition={{ duration: 0.2 }}
                    >
                      <div className="job-row-main">
                        <h3 className="job-row-title">{job.title}</h3>
                        {job.description && (
                          <p className="job-row-description">
                            {job.description.length > 160
                              ? `${job.description.slice(0, 160).trim()}…`
                              : job.description}
                          </p>
                        )}
                        <div className="job-row-tags">
                          <span className="job-row-tag">
                            <span className="job-row-tag-icon" aria-hidden>📍</span>
                            {job.location
                              ? job.location.includes('|')
                                ? job.location
                                : `India | ${job.location}`
                              : 'India'}
                          </span>
                          {getJobTypeLabel(job.job_type) && (
                            <span className="job-row-tag">
                              <span className="job-row-tag-icon" aria-hidden>💼</span>
                              {getJobTypeLabel(job.job_type)}
                            </span>
                          )}
                          {(job.experience_required != null && job.experience_required !== '') && (
                            <span className="job-row-tag">
                              <span className="job-row-tag-icon" aria-hidden>🕐</span>
                              {job.experience_required}
                            </span>
                          )}
                          {(job.business_area != null && job.business_area !== '') && (
                            <span className="job-row-tag">
                              <span className="job-row-tag-icon" aria-hidden>📋</span>
                              {job.business_area}
                            </span>
                          )}
                          {!job.experience_required && !job.job_type && (
                            <span className="job-row-tag">
                              <span className="job-row-tag-icon" aria-hidden>🕐</span>
                              Full-time
                            </span>
                          )}
                        </div>
                        {job.jd_file_url && (
                          <a
                            href={getJdPdfUrl(job.jd_file_url)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="job-row-jd-link"
                            onClick={(e) => e.stopPropagation()}
                          >
                            View Job Description (PDF)
                          </a>
                        )}
                      </div>
                      <div className="job-row-apply-wrap">
                        <button
                          type="button"
                          className="job-row-apply"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleApply(job.job_id || job.id)
                          }}
                        >
                          Apply
                          <span className="job-row-apply-arrow" aria-hidden>↗</span>
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  )
}

export default Careers
