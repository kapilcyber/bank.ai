import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { createPortal } from 'react-dom'
import { API_BASE_URL } from '../../config/api'
import './AdminDashboard.css' // Reuse existing styles for consistency

// Helper to clean text (reused)
const cleanCertText = (text) => {
    if (typeof text !== 'string') return ''
    return text
        .replace(/^[●☐☑✓✔✅❌□■▪▫•◦‣⁃∙⦿⦾]+\s*/g, '')
        .replace(/^[\-\*\d\.]+\s*/g, '')
        .replace(/^[\s\W]+/, '')
        .trim()
}

const getInitials = (name) => {
    const safeName = typeof name === 'string' ? name : (name && typeof name === 'object' ? (name.name || name.full_name || '') : '');
    if (!safeName || safeName === 'N/A') return '??'
    return safeName.split(' ').filter(Boolean).map(n => n[0]).join('').toUpperCase().substring(0, 2)
}

const formatUserType = (type) => {
    if (!type || typeof type !== 'string') return 'N/A'
    return type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}

const renderSafe = (value, fallback = 'N/A') => {
    if (value === null || value === undefined) return fallback;
    if (typeof value === 'object') {
        if (typeof value.email === 'string' && value.email.trim()) return value.email;
        if (typeof value.name === 'string' && value.name.trim()) return value.name;
        if (typeof value.full_name === 'string' && value.full_name.trim()) return value.full_name;
        if (typeof value.phone === 'string' && value.phone.trim()) return value.phone;
        try {
            const stringified = JSON.stringify(value);
            return stringified === '{}' ? fallback : stringified;
        } catch (e) {
            return fallback;
        }
    }
    return value;
}

const Records = ({ initialFilter, setInitialFilter }) => {
    const [searchTerm, setSearchTerm] = useState(initialFilter || '')
    const [records, setRecords] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [selectedCandidate, setSelectedCandidate] = useState(null)

    // Fetch records from database - always fresh data
    const fetchRecords = async () => {
        try {
            setLoading(true)
            setError(null)
            const token = localStorage.getItem('authToken')

            // Using the same endpoint as dashboard for now as it contains the recent records
            const response = await fetch(`${API_BASE_URL}/admin/stats`, {
                headers: {
                    ...(token && { Authorization: `Bearer ${token}` })
                }
            })

            if (response.status === 401) throw new Error('Unauthorized')
            if (response.status === 403) throw new Error('Access Denied')
            if (!response.ok) throw new Error('Failed to fetch records')

            const data = await response.json()
            // Extract recent resumes/records
            const recentResumes = data.recentResumes || data.recent_resumes || []
            setRecords(recentResumes)
        } catch (err) {
            console.error('Error fetching records:', err)
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    // Initial fetch and setup real-time updates
    useEffect(() => {
        fetchRecords()

        // Listen for resume upload events for immediate refresh
        const handleResumeUploaded = (event) => {
            console.log('📥 Records: Received resumeUploaded event', event.detail)
            // Add a small delay to ensure backend has committed the transaction
            setTimeout(() => {
                console.log('🔄 Records: Refreshing records after upload...')
                fetchRecords()
            }, 1000) // 1 second delay to ensure DB commit
        }
        
        // Refresh when component becomes visible (only when tab becomes active)
        const handleVisibilityChange = () => {
            if (!document.hidden) {
                console.log('🔄 Records: Tab visible, refreshing from database...')
                fetchRecords()
            }
        }
        
        // Refresh when window regains focus (only when user returns to the tab)
        const handleFocus = () => {
            console.log('🔄 Records: Window focused, refreshing from database...')
            fetchRecords()
        }
        
        // Set up event listeners
        window.addEventListener('resumeUploaded', handleResumeUploaded)
        document.addEventListener('visibilitychange', handleVisibilityChange)
        window.addEventListener('focus', handleFocus)
        
        // Cleanup
        return () => {
            window.removeEventListener('resumeUploaded', handleResumeUploaded)
            document.removeEventListener('visibilitychange', handleVisibilityChange)
            window.removeEventListener('focus', handleFocus)
        }
    }, [])

    if (loading) {
        return (
            <div className="admin-dashboard">
                <div className="loading-message">
                    <div className="spinner"></div>
                    Loading records...
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="admin-dashboard">
                <div className="error-message">
                    <h3>Connection Error</h3>
                    <p>{error}</p>
                    <button onClick={fetchRecords} className="retry-btn">Retry</button>
                </div>
            </div>
        )
    }

    return (
        <div className="admin-dashboard">
            <div className="dashboard-header">
                <div className="header-text-group">
                    <h2>Candidate Records</h2>
                    <p className="dashboard-subtitle">View and manage latest applications</p>
                </div>

                <div className="records-search-wrapper">
                    <div className="search-input-group">
                        <input
                            type="text"
                            placeholder="Search talent database..."
                            className="premium-cyber-input"
                            style={{ width: '350px' }}
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    {searchTerm && (
                        <button
                            className="reset-view-btn"
                            onClick={() => {
                                setSearchTerm('');
                                if (setInitialFilter) setInitialFilter(null);
                            }}
                            title="Clear All Filters"
                        >
                            ↺
                        </button>
                    )}
                </div>
            </div>

            <motion.div
                className="dashboard-section"
                style={{ width: '100%', padding: '0', background: 'transparent', boxShadow: 'none', border: 'none' }}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <div className="table-container" style={{ marginTop: 0 }}>
                    <table className="data-table">
                        <colgroup>
                            <col style={{ width: '4%' }} />
                            <col style={{ width: '18%' }} />
                            <col style={{ width: '8%' }} />
                            <col style={{ width: '9%' }} />
                            <col style={{ width: '9%' }} />
                            <col style={{ width: '6%' }} />
                            <col style={{ width: '6%' }} />
                            <col style={{ width: '7%' }} />
                            <col style={{ width: '10%' }} />
                            <col style={{ width: '10%' }} />
                            <col style={{ width: '13%' }} />
                        </colgroup>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Candidate Details</th>
                                <th>Type</th>
                                <th>Role</th>
                                <th>Location</th>
                                <th>Experience</th>
                                <th>Notice</th>
                                <th>Relocate</th>
                                <th>Skills</th>
                                <th>Certifications</th>
                                <th>Education</th>
                            </tr>
                        </thead>
                        <tbody>
                            {(() => {
                                const filtered = records.filter(r => {
                                    if (!searchTerm) return true;
                                    const search = searchTerm.toLowerCase();
                                    return (
                                        (r.name || r.full_name || '').toLowerCase().includes(search) ||
                                        (r.role || '').toLowerCase().includes(search) ||
                                        (r.location || '').toLowerCase().includes(search) ||
                                        (r.skills || []).some(s => s.toLowerCase().includes(search))
                                    );
                                });

                                if (filtered.length === 0) {
                                    return (
                                        <tr>
                                            <td colSpan="10" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                                                {searchTerm ? `No results found for "${searchTerm}"` : 'No records found'}
                                            </td>
                                        </tr>
                                    );
                                }

                                return filtered.map((resume, index) => (
                                    <tr
                                        key={resume.id || resume.resume_id}
                                        className="clickable-row"
                                        onClick={() => setSelectedCandidate(resume)}
                                    >
                                        <td><span className="id-badge">#{index + 1}</span></td>
                                        <td>
                                            <div className="name-cell">
                                                <div className="avatar-sm">{getInitials(resume.name || resume.full_name || 'N/A')}</div>
                                                <div className="name-info">
                                                    <span className="candidate-name" title={renderSafe(resume.name || resume.full_name)}>{renderSafe(resume.name || resume.full_name, 'Anonymous')}</span>
                                                    <span className="candidate-email-sub" title={renderSafe(resume.email)}>{renderSafe(resume.email, 'No Email')}</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td>
                                            <span className={`type-badge-new ${resume.user_type || resume.source_type || 'default'}`}>
                                                {formatUserType(resume.user_type || resume.source_type)}
                                            </span>
                                        </td>
                                        <td><span className="role-text" title={renderSafe(resume.role)}>{renderSafe(resume.role)}</span></td>
                                        <td><span className="location-text" title={renderSafe(resume.location)}>{renderSafe(resume.location)}</span></td>
                                        <td>
                                            <span className="exp-badge-new">
                                                {resume.experience_years ? `${parseFloat(resume.experience_years).toFixed(1)} yrs` : '0 yrs'}
                                            </span>
                                        </td>
                                        <td><span className="notice-text">{resume.notice_period !== undefined ? `${resume.notice_period}d` : 'N/A'}</span></td>
                                        <td>
                                            <span className={`relocate-pill ${resume.ready_to_relocate ? 'yes' : 'no'}`}>
                                                {resume.ready_to_relocate ? 'YES' : 'NO'}
                                            </span>
                                        </td>
                                        <td>
                                            <div className="skills-tags-new">
                                                {(resume.skills || []).slice(0, 1).map((skill, idx) => (
                                                    <span key={idx} className="skill-tag-new">{skill}</span>
                                                ))}
                                                {resume.skills && resume.skills.length > 1 && (
                                                    <span className="more-count">+{resume.skills.length - 1}</span>
                                                )}
                                            </div>
                                        </td>
                                        <td>
                                            <div className="skills-tags-new">
                                                {(resume.parsed_data?.resume_certificates || [])
                                                    .filter(c => c && c !== "Not mentioned")
                                                    .slice(0, 1).map((cert, idx) => (
                                                        <span key={idx} className="cert-tag-new">{cleanCertText(cert)}</span>
                                                    ))}
                                                {resume.parsed_data?.resume_certificates?.filter(c => c && c !== "Not mentioned")?.length > 1 && (
                                                    <span className="more-count">+{resume.parsed_data.resume_certificates.filter(c => c && c !== "Not mentioned").length - 1}</span>
                                                )}
                                                {(!(resume.parsed_data?.resume_certificates?.filter(c => c && c !== "Not mentioned")?.length > 0)) && (
                                                    <span className="na-text">N/A</span>
                                                )}
                                            </div>
                                        </td>
                                        <td>
                                            <div className="education-tags-new">
                                                {(resume.educations || [])
                                                    .slice(0, 1).map((edu, idx) => (
                                                        <span key={idx} className="edu-tag-new" title={`${edu.degree || 'Education'}${edu.institution ? ` - ${edu.institution}` : ''}${edu.grade ? ` (${edu.grade})` : ''}`}>
                                                            {edu.degree || 'Education'}
                                                        </span>
                                                    ))}
                                                {(resume.educations || []).length > 1 && (
                                                    <span className="more-count">+{(resume.educations || []).length - 1}</span>
                                                )}
                                                {(!(resume.educations || []).length > 0) && (
                                                    <span className="na-text">N/A</span>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            })()}
                        </tbody>
                    </table>
                </div>
            </motion.div>

            {/* Reusing the Modal from Dashboard would require exporting it or duplicating. 
          For now I will duplicate the simple modal logic to ensure independence 
          or better yet, I should export CandidateDetailModal from AdminDashboard if possible.
          Let's verify if AdminDashboard exports it. */
            }
            <CandidateDetailModal
                candidate={selectedCandidate}
                onClose={() => setSelectedCandidate(null)}
            />
        </div>
    )
}

// Duplicated modal for strict isolation as per usual React component patterns if not in shared file
const CandidateDetailModal = ({ candidate, onClose }) => {
    useEffect(() => {
        if (candidate) {
            document.body.style.overflow = 'hidden'
        } else {
            document.body.style.overflow = 'unset'
        }
        return () => {
            document.body.style.overflow = 'unset'
        }
    }, [candidate])

    if (!candidate) return null

    const cleanText = (text) => {
        if (typeof text !== 'string') return ''
        return text
            .replace(/^[●☐☑✓✔✅❌□■▪▫•◦‣⁃∙⦿⦾]+\s*/g, '')
            .replace(/^[\-\*\d\.]+\s*/g, '')
            .replace(/^[\s\W]+/, '')
            .trim()
    }

    const parsed = candidate.parsed_data || {}

    let certs = candidate.certificates || []
    if (certs.length === 0 && parsed.resume_certificates && Array.isArray(parsed.resume_certificates)) {
        certs = parsed.resume_certificates
            .filter(c => c && c !== "Not mentioned")
            .map(name => ({ name: name, issuer: 'Detected', date_obtained: null }))
    }

    const educations = candidate.educations || []
    const skills = candidate.skills && candidate.skills.length > 0 ? candidate.skills : (parsed.resume_skills || [])

    return createPortal(
        <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
        >
            <motion.div
                className="modal-content"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                onClick={e => e.stopPropagation()}
            >
                <div className="modal-header">
                    <div className="header-top">
                        <div className="candidate-profile-summary">
                            <div className="profile-avatar-lg">{getInitials(candidate.name || candidate.full_name || 'N/A')}</div>
                            <div className="profile-info-main">
                                <h2>{renderSafe(candidate.name || candidate.full_name, 'Candidate Profile')}</h2>
                                <div className="header-badges-row">
                                    <span className="premium-badge type">{formatUserType(candidate.user_type || candidate.source_type || 'Candidate')}</span>
                                    {candidate.role && <span className="premium-badge role">{candidate.role}</span>}
                                </div>
                            </div>
                        </div>
                        <button className="close-btn-new" aria-label="Close" onClick={onClose}>&times;</button>
                    </div>
                </div>

                <div className="modal-body">
                    <div className="modal-grid-container">
                        <section className="modal-section">
                            <h3 className="section-title-sm">Quick Contacts & Essentials</h3>
                            <div className="info-cards-row">
                                <div className="info-mini-card">
                                    <span className="mini-icon">📧</span>
                                    <div className="mini-content">
                                        <label>Email Address</label>
                                        <p>{renderSafe(candidate.email)}</p>
                                    </div>
                                </div>
                                <div className="info-mini-card">
                                    <span className="mini-icon">📍</span>
                                    <div className="mini-content">
                                        <label>Current Location</label>
                                        <p>{renderSafe(candidate.location)}</p>
                                    </div>
                                </div>
                                <div className="info-mini-card">
                                    <span className="mini-icon">💼</span>
                                    <div className="mini-content">
                                        <label>Total Experience</label>
                                        <p>{candidate.experience_years ? `${parseFloat(candidate.experience_years).toFixed(1)} Years` : 'N/A'}</p>
                                    </div>
                                </div>
                                <div className="info-mini-card">
                                    <span className="mini-icon">⏳</span>
                                    <div className="mini-content">
                                        <label>Notice Period</label>
                                        <p>{candidate.notice_period !== undefined ? `${candidate.notice_period} Days` : 'N/A'}</p>
                                    </div>
                                </div>
                            </div>
                        </section>

                        <section className="modal-section highlight">
                            <div className="detail-item-premium">
                                <label>Relocation Status & Preference</label>
                                <div className={`status-box ${candidate.ready_to_relocate ? 'active' : ''}`}>
                                    {candidate.ready_to_relocate ? (
                                        <div className="status-content">
                                            <span className="status-main">Ready to Relocate</span>
                                            <span className="status-sub">Preferred: {candidate.preferred_location || 'Open'}</span>
                                        </div>
                                    ) : 'Not open to relocation'}
                                </div>
                            </div>
                        </section>

                        <div className="skills-certs-grid">
                            <div className="content-block">
                                <h3><span className="block-icon">🚀</span> Core Skills</h3>
                                <div className="premium-tag-list">
                                    {skills.length > 0 ? (
                                        skills.map((skill, idx) => (
                                            <span key={idx} className="premium-skill-tag">{skill}</span>
                                        ))
                                    ) : <p className="no-data-text">No skills detected</p>}
                                </div>
                            </div>

                            <div className="content-block">
                                <h3><span className="block-icon">📜</span> Certifications</h3>
                                <div className="premium-tag-list">
                                    {certs.length > 0 ? (
                                        certs.map((cert, idx) => (
                                            <span key={idx} className="premium-cert-tag">{cleanCertText(cert.name)}</span>
                                        ))
                                    ) : <p className="no-data-text">No certifications found</p>}
                                </div>
                            </div>
                        </div>

                        <section className="modal-section">
                            <h3 className="section-title-sm"><span className="block-icon">💼</span> Work Experience</h3>
                            {candidate.work_history && candidate.work_history.length > 0 ? (
                                <div className="experience-list" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                    {candidate.work_history.map((exp, idx) => (
                                        <div key={idx} className="experience-item" style={{ 
                                            padding: '1rem', 
                                            background: 'rgba(50, 130, 184, 0.05)', 
                                            borderRadius: '8px',
                                            border: '1px solid rgba(50, 130, 184, 0.2)'
                                        }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                                                <h4 style={{ margin: 0, color: '#3282b8', fontSize: '1rem', fontWeight: '700' }}>
                                                    {exp.role || 'Position'}
                                                </h4>
                                                {(exp.start_date || exp.end_date) && (
                                                    <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                                                        {exp.start_date || ''} {exp.start_date && exp.end_date ? '-' : ''} {exp.end_date || ''}
                                                        {exp.is_current && ' (Current)'}
                                                    </span>
                                                )}
                                            </div>
                                            {exp.company && (
                                                <p style={{ margin: '0.25rem 0', color: '#64748b', fontSize: '0.9rem' }}>
                                                    <strong>Company:</strong> {exp.company}
                                                </p>
                                            )}
                                            {exp.location && (
                                                <p style={{ margin: '0.25rem 0', color: '#64748b', fontSize: '0.9rem' }}>
                                                    <strong>Location:</strong> {exp.location}
                                                </p>
                                            )}
                                            {exp.description && (
                                                <p style={{ margin: '0.5rem 0 0', color: '#94a3b8', fontSize: '0.85rem', fontStyle: 'italic' }}>
                                                    {exp.description}
                                                </p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="no-data-text">No work experience records found</p>
                            )}
                        </section>

                        <section className="modal-section">
                            <h3 className="section-title-sm"><span className="block-icon">🎓</span> Education</h3>
                            {educations.length > 0 ? (
                                <div className="education-list" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                    {educations.map((edu, idx) => (
                                        <div key={idx} className="education-item" style={{ 
                                            padding: '1rem', 
                                            background: 'rgba(50, 130, 184, 0.05)', 
                                            borderRadius: '8px',
                                            border: '1px solid rgba(50, 130, 184, 0.2)'
                                        }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                                                <h4 style={{ margin: 0, color: '#3282b8', fontSize: '1rem', fontWeight: '700' }}>
                                                    {edu.degree || 'Education'}
                                                </h4>
                                                {(edu.start_date || edu.end_date) && (
                                                    <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                                                        {edu.start_date || ''} {edu.start_date && edu.end_date ? '-' : ''} {edu.end_date || ''}
                                                    </span>
                                                )}
                                            </div>
                                            {edu.institution && (
                                                <p style={{ margin: '0.25rem 0', color: '#64748b', fontSize: '0.9rem' }}>
                                                    <strong>Institution:</strong> {edu.institution}
                                                </p>
                                            )}
                                            {edu.field_of_study && (
                                                <p style={{ margin: '0.25rem 0', color: '#64748b', fontSize: '0.9rem' }}>
                                                    <strong>Field:</strong> {edu.field_of_study}
                                                </p>
                                            )}
                                            {edu.grade && (
                                                <p style={{ margin: '0.25rem 0', color: '#64748b', fontSize: '0.9rem' }}>
                                                    <strong>Grade:</strong> {edu.grade}
                                                </p>
                                            )}
                                            {edu.description && (
                                                <p style={{ margin: '0.5rem 0 0', color: '#94a3b8', fontSize: '0.85rem', fontStyle: 'italic' }}>
                                                    {edu.description}
                                                </p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="no-data-text">No education records found</p>
                            )}
                        </section>
                    </div>
                </div>

                {candidate.file_url && (
                    <div className="modal-footer-premium">
                        <a
                            href={candidate.file_url}
                            target="_blank"
                            rel="noreferrer"
                            className="view-resume-action-btn"
                        >
                            📄 View Full Resume
                        </a>
                    </div>
                )}
            </motion.div>
        </motion.div>,
        document.body
    )
}

export default Records
