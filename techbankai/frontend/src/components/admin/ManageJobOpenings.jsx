import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  getJobOpenings,
  createJobOpening,
  updateJobOpening,
  deleteJobOpening,
  API_ENDPOINTS
} from '../../config/api'
import './ManageJobOpenings.css'

const ManageJobOpenings = () => {
  const [jobOpenings, setJobOpenings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [editingJob, setEditingJob] = useState(null)
  const [formData, setFormData] = useState({
    title: '',
    location: '',
    business_area: '',
    description: '',
    status: 'active'
  })
  const [jdMethod, setJdMethod] = useState('write') // 'write' or 'upload'
  const [jdFile, setJdFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)

  useEffect(() => {
    fetchJobOpenings()
  }, [])

  const fetchJobOpenings = async () => {
    try {
      setLoading(true)
      setError(null)
      // Admin should see all jobs (active and inactive), so pass status='all'
      let data
      try {
        data = await getJobOpenings({ status: 'all', limit: 1000 }) // Get all jobs for admin
      } catch (adminErr) {
        // If admin request fails (403), try fetching active jobs as fallback
        if (adminErr.status === 403 || adminErr.status === 401) {
          console.warn('Admin access denied, fetching active jobs instead:', adminErr)
          data = await getJobOpenings({ status: 'active', limit: 1000 })
        } else {
          throw adminErr
        }
      }
      console.log('Job openings response:', data)
      // Backend returns { jobs: [...] } or { job_openings: [...] } or array
      const jobs = Array.isArray(data) ? data : (data.jobs || data.job_openings || [])
      console.log('Extracted jobs:', jobs)
      setJobOpenings(jobs)
      if (jobs.length === 0) {
        console.log('No jobs found in response')
      }
    } catch (err) {
      console.error('Error fetching job openings:', err)
      const errorMessage = err.message || err.detail || 'Failed to load job openings'
      setError(errorMessage)
      // If it's a 403 error, it means admin access is required
      if (err.status === 403) {
        setError('Admin access required. Please make sure you are logged in as an admin.')
      }
      // Set empty array on error so UI doesn't break
      setJobOpenings([])
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Validate: if upload method, file must be provided; if write method, description should be provided
    if (jdMethod === 'upload' && !jdFile) {
      setError('Please upload a JD file or switch to "Write JD" method')
      return
    }
    
    try {
      const fileToUpload = jdMethod === 'upload' ? jdFile : null
      const descriptionText = jdMethod === 'write' ? formData.description : ''
      
      const jobData = {
        ...formData,
        description: descriptionText
      }
      
      if (editingJob) {
        await updateJobOpening(editingJob.job_id, jobData, fileToUpload)
      } else {
        await createJobOpening(jobData, fileToUpload)
      }
      await fetchJobOpenings()
      setShowForm(false)
      setEditingJob(null)
      setJdFile(null)
      setJdMethod('write')
      setFormData({
        title: '',
        location: '',
        business_area: '',
        description: '',
        status: 'active'
      })
    } catch (err) {
      console.error('Error saving job opening:', err)
      setError(err.message || 'Failed to save job opening')
    }
  }

  const handleEdit = (job) => {
    setEditingJob(job)
    setFormData({
      title: job.title || '',
      location: job.location || '',
      business_area: job.business_area || '',
      description: job.description || '',
      status: job.status || 'active'
    })
    setJdFile(null)
    setJdMethod(job.jd_file_url ? 'upload' : 'write')
    setShowForm(true)
  }
  
  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = (selectedFile) => {
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']
    if (!allowedTypes.includes(selectedFile.type)) {
      setError('Please upload a PDF, DOC, or DOCX file')
      return
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setError('File size should be less than 10MB')
      return
    }

    setJdFile(selectedFile)
    setError(null)
  }

  const handleRemoveFile = () => {
    setJdFile(null)
  }

  const handleDelete = async (jobId) => {
    if (!window.confirm('Are you sure you want to delete this job opening?')) {
      return
    }
    try {
      await deleteJobOpening(jobId)
      await fetchJobOpenings()
    } catch (err) {
      console.error('Error deleting job opening:', err)
      setError(err.message || 'Failed to delete job opening')
    }
  }

  return (
    <div className="manage-job-openings">
      <div className="header-section">
        <h1>Manage Job Openings</h1>
        <button
          className="btn-primary"
          onClick={() => {
            setShowForm(!showForm)
            setEditingJob(null)
            setJdFile(null)
            setJdMethod('write')
            setFormData({
              title: '',
              location: '',
              business_area: '',
              description: '',
              status: 'active'
            })
          }}
        >
          {showForm ? 'Cancel' : '+ Add New Job Opening'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {showForm && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="job-form"
        >
          <h2>{editingJob ? 'Edit Job Opening' : 'Create New Job Opening'}</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Title *</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Location *</label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Business Area *</label>
              <select
                value={formData.business_area}
                onChange={(e) => setFormData({ ...formData, business_area: e.target.value })}
                required
              >
                <option value="">Select Business Area</option>
                <option value="Data/AI">Data/AI</option>
                <option value="Inside Sales Executive">Inside Sales Executive</option>
                <option value="Security Engineer">Security Engineer</option>
                <option value="Networking Engineer">Networking Engineer</option>
                <option value="IT Infrastructure Engineer">IT Infrastructure Engineer</option>
                <option value="Business Development Manager">Business Development Manager</option>
              </select>
            </div>
            <div className="form-group">
              <label>Description</label>
              <div className="jd-method-tabs">
                <button
                  type="button"
                  className={`jd-tab ${jdMethod === 'write' ? 'active' : ''}`}
                  onClick={() => {
                    setJdMethod('write')
                    setJdFile(null)
                  }}
                >
                  ✍️ Write JD
                </button>
                <button
                  type="button"
                  className={`jd-tab ${jdMethod === 'upload' ? 'active' : ''}`}
                  onClick={() => {
                    setJdMethod('upload')
                    setFormData({ ...formData, description: '' })
                  }}
                >
                  📁 Upload PDF
                </button>
              </div>

              {jdMethod === 'upload' ? (
                <div
                  className={`jd-drop-zone ${dragActive ? 'drag-active' : ''} ${jdFile ? 'has-file' : ''}`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  {!jdFile ? (
                    <>
                      <div className="upload-icon">📁</div>
                      <h3>Upload File</h3>
                      <p>Drag and drop your PDF or DOCX here, or click to browse.</p>
                      <label htmlFor="jd-file-input" className="browse-jd-btn">
                        Browse Files
                      </label>
                      <input
                        id="jd-file-input"
                        type="file"
                        accept=".pdf,.docx,.doc"
                        onChange={handleFileSelect}
                        style={{ display: 'none' }}
                      />
                      <p className="file-format-hint">Accepted formats: PDF, DOC, DOCX (Max size: 10MB)</p>
                    </>
                  ) : (
                    <div className="file-preview-jd">
                      <div className="file-icon-jd">📄</div>
                      <div className="file-info-jd">
                        <h3>{jdFile.name}</h3>
                        <p>{(jdFile.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                      <button type="button" className="remove-file-btn" onClick={handleRemoveFile}>
                        ✕
                      </button>
                    </div>
                  )}
                </div>
              ) : (
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={5}
                  placeholder="Enter job description here..."
              />
              )}
            </div>
            <div className="form-group">
              <label>Status *</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                required
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
            <div className="form-actions">
              <button type="submit" className="btn-primary">
                {editingJob ? 'Update' : 'Create'}
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => {
                  setShowForm(false)
                  setEditingJob(null)
                  setJdFile(null)
                  setJdMethod('write')
                }}
              >
                Cancel
              </button>
            </div>
          </form>
        </motion.div>
      )}

      {loading ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '80px 40px', 
          color: '#555',
          background: 'linear-gradient(135deg, rgba(255, 218, 198, 0.7) 0%, rgba(255, 232, 217, 0.7) 25%, rgba(232, 213, 255, 0.7) 50%, rgba(216, 226, 220, 0.7) 75%, rgba(184, 216, 255, 0.7) 100%)',
          backdropFilter: 'blur(40px) saturate(200%)',
          WebkitBackdropFilter: 'blur(40px) saturate(200%)',
          borderRadius: '20px',
          boxShadow: '0 4px 24px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 218, 198, 0.3)',
          border: '1px solid rgba(255, 255, 255, 0.3)'
        }}>
          <div style={{ 
            display: 'inline-block',
            width: '40px',
            height: '40px',
            border: '4px solid rgba(102, 126, 234, 0.2)',
            borderTopColor: '#667eea',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
            marginBottom: '20px'
          }}></div>
          <p style={{ 
            fontSize: '16px', 
            margin: 0, 
            fontWeight: '600',
            color: '#2d3748'
          }}>
            Loading job openings...
          </p>
        </div>
      ) : (
        <div className="job-openings-list">
          {jobOpenings.length === 0 ? (
            <div style={{ 
              textAlign: 'center', 
              padding: '80px 40px', 
              background: 'linear-gradient(135deg, rgba(255, 218, 198, 0.7) 0%, rgba(255, 232, 217, 0.7) 25%, rgba(232, 213, 255, 0.7) 50%, rgba(216, 226, 220, 0.7) 75%, rgba(184, 216, 255, 0.7) 100%)',
              backdropFilter: 'blur(40px) saturate(200%)',
              WebkitBackdropFilter: 'blur(40px) saturate(200%)',
              borderRadius: '20px',
              boxShadow: '0 4px 24px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 218, 198, 0.3)',
              border: '1px solid rgba(255, 255, 255, 0.3)'
            }}>
              <div style={{ 
                fontSize: '48px',
                marginBottom: '20px',
                opacity: 0.6
              }}>💼</div>
              <p style={{ 
                fontSize: '20px', 
                marginBottom: '12px', 
                color: '#1a1a1a',
                fontWeight: '700',
                letterSpacing: '-0.02em'
              }}>
                No job openings found
              </p>
              <p style={{ 
                fontSize: '15px', 
                color: '#666',
                margin: 0,
                lineHeight: '1.6'
              }}>
                Click "+ Add New Job Opening" to create your first job opening.
              </p>
            </div>
          ) : (
            jobOpenings.map((job) => (
              <motion.div
                key={job.job_id || job.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="job-card"
              >
                <div className="job-info">
                  <h3>{job.title || 'Untitled Job Opening'}</h3>
                  {job.location && (
                  <p><strong>Location:</strong> {job.location}</p>
                  )}
                  {job.business_area && (
                  <p><strong>Business Area:</strong> {job.business_area}</p>
                  )}
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '8px',
                    marginTop: '8px',
                    flexWrap: 'wrap'
                  }}>
                    <span style={{ 
                      color: job.status === 'active' ? '#059669' : '#dc2626',
                      textTransform: 'capitalize',
                      fontWeight: '600',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      background: job.status === 'active' 
                        ? 'rgba(16, 185, 129, 0.15)' 
                        : 'rgba(239, 68, 68, 0.15)',
                      border: job.status === 'active' 
                        ? '1px solid rgba(16, 185, 129, 0.25)' 
                        : '1px solid rgba(239, 68, 68, 0.25)',
                      fontSize: '11px',
                      letterSpacing: '0.02em'
                    }}>{job.status || 'active'}</span>
                  </div>
                </div>
                <div className="job-actions">
                  <button
                    className="btn-edit"
                    onClick={() => handleEdit(job)}
                  >
                    Edit
                  </button>
                  <button
                    className="btn-delete"
                    onClick={() => handleDelete(job.job_id || job.id)}
                  >
                    Delete
                  </button>
                </div>
              </motion.div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default ManageJobOpenings

