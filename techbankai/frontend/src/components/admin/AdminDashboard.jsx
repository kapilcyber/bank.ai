import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { motion } from 'framer-motion'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, PieChart, Pie, Cell, Sector, LineChart, Line,
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts'
import { API_BASE_URL } from '../../config/api'
import './AdminDashboard.css'

// Helper to clean text from unwanted characters
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
    // If it's a known contact object structure, pick the best string field
    if (typeof value.email === 'string' && value.email.trim()) return value.email;
    if (typeof value.name === 'string' && value.name.trim()) return value.name;
    if (typeof value.full_name === 'string' && value.full_name.trim()) return value.full_name;
    if (typeof value.phone === 'string' && value.phone.trim()) return value.phone;

    // Fallback to stringifying if it's an object/array we can't otherwise render
    try {
      const stringified = JSON.stringify(value);
      return stringified === '{}' ? fallback : stringified;
    } catch (e) {
      return fallback;
    }
  }
  return value;
}

const NightingaleRoseWedge = (props) => {
  const {
    cx, cy, midAngle, innerRadius, outerRadius, startAngle, endAngle,
    fill, payload, maxTotal
  } = props;

  // Calculate the custom radius based on the total value
  // We use a square root scale to make the AREA proportional to the value (classic Nightingale)
  const normalizedValue = maxTotal > 0 ? (payload.total / maxTotal) : 0;
  const customOuterRadius = innerRadius + (outerRadius - innerRadius) * Math.sqrt(normalizedValue);

  return (
    <g className="rose-wedge">
      <Sector
        cx={cx}
        cy={cy}
        startAngle={startAngle}
        endAngle={endAngle}
        innerRadius={innerRadius}
        outerRadius={customOuterRadius}
        fill={fill}
        stroke="#00f2ff"
        strokeWidth={1}
        fillOpacity={0.4}
        className="wedge-sector"
      />
      {/* Add a glowing edge */}
      <Sector
        cx={cx}
        cy={cy}
        startAngle={startAngle}
        endAngle={endAngle}
        innerRadius={customOuterRadius - 2}
        outerRadius={customOuterRadius}
        fill="#00f2ff"
        fillOpacity={0.8}
      />
    </g>
  );
};

const AdminDashboard = ({ onNavigateToRecords }) => {
  const [selectedUserType, setSelectedUserType] = useState('all')
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCandidate, setSelectedCandidate] = useState(null)
  const [timeframe, setTimeframe] = useState('month') // 'day', 'month', 'quarter'
  const [selectedState, setSelectedState] = useState('')
  const [syncing, setSyncing] = useState(false)
  const [syncStatus, setSyncStatus] = useState(null)

  const INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Delhi", "Chandigarh", "Puducherry", "Jammu & Kashmir", "Andaman & Nicobar", "Lakshadweep", "Ladakh", "Dadra & Nagar Haveli"
  ].sort();

  useEffect(() => {
    fetchDashboardData()
    
    // Listen for resume upload events for immediate refresh
    const handleResumeUploaded = (event) => {
      console.log('📥 AdminDashboard: Received resumeUploaded event', event.detail)
      // Add a small delay to ensure backend has committed the transaction
      setTimeout(() => {
        console.log('🔄 AdminDashboard: Refreshing dashboard data after upload...')
        fetchDashboardData()
      }, 1000) // 1 second delay to ensure DB commit
    }

    // Refresh when component becomes visible (only when tab becomes active)
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        console.log('🔄 AdminDashboard: Tab visible, refreshing from database...')
        fetchDashboardData()
      }
    }

    // Refresh when window regains focus (only when user returns to the tab)
    const handleFocus = () => {
      console.log('🔄 AdminDashboard: Window focused, refreshing from database...')
      fetchDashboardData()
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

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('authToken')
      
      // Debug: Check if token exists
      console.log('🔑 AdminDashboard: Token exists:', !!token)
      console.log('🔑 AdminDashboard: Token length:', token?.length)
      console.log('🔑 AdminDashboard: Token preview:', token ? `${token.substring(0, 20)}...` : 'No token')
      
      if (!token) {
        const errorMsg = 'No authentication token found. Please log in as an admin.'
        console.error('❌ AdminDashboard:', errorMsg)
        setError(errorMsg)
        setLoading(false)
        return
      }

      const response = await fetch(`${API_BASE_URL}/admin/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      console.log('📡 AdminDashboard: API Response status:', response.status)
      console.log('📡 AdminDashboard: API Response ok:', response.ok)

      if (response.status === 401) {
        // Clear invalid token
        console.warn('⚠️ AdminDashboard: 401 Unauthorized - Clearing invalid token')
        localStorage.removeItem('authToken')
        const errorMsg = 'Session expired or invalid. Please log in again as an admin.'
        throw new Error(errorMsg)
      }

      if (response.status === 403) {
        const errorMsg = 'Access Denied. Your account does not have admin permissions. Please log out and log in with an admin account.'
        console.error('❌ AdminDashboard:', errorMsg)
        throw new Error(errorMsg)
      }

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error')
        console.error('❌ AdminDashboard: API Error:', response.status, errorText)
        throw new Error(`Failed to fetch dashboard data (${response.status}): ${errorText}`)
      }

      const data = await response.json()
      
      // Debug logging
      console.log('📊 AdminDashboard: Raw API response:', data)
      console.log('📊 AdminDashboard: total_records =', data.total_records)
      console.log('📊 AdminDashboard: total_resumes =', data.total_resumes)

      // Transform backend data to match frontend format
      const transformedData = {
        totalRecords: data.total_records ?? data.total_resumes ?? 0,
        totalUsers: data.total_users || 0,
        totalJD: data.total_jd_analyses || 0,
        totalMatches: data.total_matches || 0,
        userTypeCounts: data.user_type_breakdown || {},
        topSkills: data.top_skills || [],
        topSkillsByUserType: data.top_skills_by_user_type || {},
        departments: data.departments || Object.keys(data.user_type_breakdown || {}),
        departmentDistribution: data.departmentDistribution || data.user_type_breakdown || {},
        trends: data.trends || { day: [], month: [], quarter: [] },
        experienceDistribution: data.experience_distribution || [],
        locationDistribution: data.location_distribution || [],
        roleDistribution: data.role_distribution || [],
        recentResumes: data.recentResumes || data.recent_resumes || [],
        recentJD: data.recent_jd_analyses || []
      }

      console.log('📊 AdminDashboard: Transformed data:', transformedData)
      console.log('📊 AdminDashboard: totalRecords =', transformedData.totalRecords)
      
      setDashboardData(transformedData)
      setError(null)
      console.log('✅ AdminDashboard: Dashboard data loaded successfully')
    } catch (err) {
      console.error('❌ AdminDashboard: Error fetching dashboard data:', err)
      console.error('❌ AdminDashboard: Error details:', {
        message: err.message,
        stack: err.stack,
        name: err.name
      })
      
      // Provide user-friendly error message
      let errorMessage = err.message || 'Failed to load dashboard data. Please check if you are logged in as admin.'
      
      // Handle network errors
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        errorMessage = 'Network error: Could not connect to server. Please check if the backend is running.'
      }
      
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleOutlookSync = async () => {
    try {
      setSyncing(true)
      setSyncStatus(null)
      const token = localStorage.getItem('authToken')

      const response = await fetch(`${API_BASE_URL}/resumes/outlook/trigger`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` })
        }
      })

      const data = await response.json()
      if (response.ok) {
        setSyncStatus({ success: true, message: 'Outlook sync pipeline activated!' })
        setTimeout(() => setSyncStatus(null), 5000)
      } else {
        throw new Error(data.detail || 'Failed to trigger Outlook sync')
      }
    } catch (err) {
      setSyncStatus({ success: false, message: err.message })
      setTimeout(() => setSyncStatus(null), 7000)
    } finally {
      setSyncing(false)
    }
  }

  if (loading) {
    return (
      <div className="admin-dashboard">
        <div className="loading-message">
          <div className="spinner"></div>
          Loading dashboard data...
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
          <button onClick={fetchDashboardData} className="retry-btn">
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  if (!dashboardData) {
    return (
      <div className="admin-dashboard">
        <div className="error-message">No data available</div>
      </div>
    )
  }

  // Calculate filtered data based on selected user type
  const filteredTotal = selectedUserType === 'all'
    ? (dashboardData?.totalRecords ?? 0)
    : (dashboardData?.userTypeCounts?.[selectedUserType] || 0)
  
  // Debug logging
  console.log('📊 AdminDashboard: filteredTotal =', filteredTotal)
  console.log('📊 AdminDashboard: selectedUserType =', selectedUserType)
  console.log('📊 AdminDashboard: dashboardData.totalRecords =', dashboardData?.totalRecords)

  const filteredTopSkills = selectedUserType === 'all'
    ? dashboardData.topSkills
    : (dashboardData.topSkillsByUserType?.[selectedUserType] || [])



  return (
    <div className="admin-dashboard">
      <div className="dashboard-header">
        <div className="header-text-group">
          <h2>Dashboard</h2>
          <button
            onClick={handleOutlookSync}
            disabled={syncing}
            className={`outlook-sync-btn ${syncing ? 'syncing' : ''}`}
            title="Sync resumes from HR Outlook inbox"
          >
            <span className="btn-icon">📧</span>
            {syncing ? 'Syncing...' : 'Sync Outlook'}
          </button>
          {syncStatus && (
            <div className={`sync-status-toast ${syncStatus.success ? 'success' : 'error'}`}>
              {syncStatus.message}
            </div>
          )}
        </div>
        <div className="user-type-filter-wrapper">
          <select
            value={selectedUserType}
            onChange={(e) => setSelectedUserType(e.target.value)}
            className="premium-cyber-select"
          >
            <option value="all">All Talent Categories</option>
            <option value="Company Employee">Company Employee</option>
            <option value="Freelancer">Freelancer</option>
            <option value="Guest User">Guest User</option>
            <option value="Admin Uploads">Admin Uploads</option>
          </select>
        </div>
      </div>

      <div className="stats-overview-grid">
        <motion.div
          className="stat-card-new"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="stat-icon-wrapper" style={{ background: 'rgba(0, 242, 255, 0.1)', color: '#00f2ff' }}>
            <span>📈</span>
          </div>
          <div className="stat-info-new">
            <span className="label">Total Talent Pool</span>
            <span className="value">{filteredTotal ? filteredTotal.toLocaleString() : '0'}</span>
            <span className="stat-trend-new">Global Database</span>
          </div>
        </motion.div>

        <motion.div
          className="stat-card-new"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <div className="stat-icon-wrapper" style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}>
            <span>🏢</span>
          </div>
          <div className="stat-info-new">
            <span className="label">Active Departments</span>
            <span className="value">{dashboardData.departments.length}</span>
            <span className="stat-trend-new">Cross-Functional</span>
          </div>
        </motion.div>

        <motion.div
          className="stat-card-new"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <div className="stat-icon-wrapper" style={{ background: 'rgba(139, 92, 246, 0.1)', color: '#8b5cf6' }}>
            <span>✅</span>
          </div>
          <div className="stat-info-new">
            <span className="label">Current Filter</span>
            <span className="value">{filteredTotal}</span>
            <span className="stat-trend-new">Matched Candidates</span>
          </div>
        </motion.div>
      </div>

      <div className="dashboard-grid-new">
        <motion.div
          className="dashboard-section acquisition-trends"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="section-header-row">
            <h3>Onboarding Trends</h3>
            <div className="timeframe-toggles">
              <button
                className={`toggle-btn ${timeframe === 'day' ? 'active' : ''}`}
                onClick={() => setTimeframe('day')}
              >Day</button>
              <button
                className={`toggle-btn ${timeframe === 'month' ? 'active' : ''}`}
                onClick={() => setTimeframe('month')}
              >Month</button>
              <button
                className={`toggle-btn ${timeframe === 'quarter' ? 'active' : ''}`}
                onClick={() => setTimeframe('quarter')}
              >Quarter</button>
            </div>
          </div>

          <div className="chart-container" style={{ height: '350px', marginTop: '1.5rem', display: 'flex', justifyContent: 'center' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dashboardData.trends[timeframe] || []} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <filter id="line-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                  </filter>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" vertical={false} />
                <XAxis
                  dataKey="name"
                  stroke="#94a3b8"
                  fontSize={11}
                  fontWeight={600}
                  axisLine={false}
                  tickLine={false}
                  dy={10}
                />
                <YAxis
                  stroke="#94a3b8"
                  fontSize={11}
                  fontWeight={600}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="custom-recharts-tooltip">
                          <p style={{ color: '#fff', fontSize: '12px', fontWeight: 800, margin: 0 }}>{label}</p>
                          <div style={{ height: '1px', background: 'rgba(255,255,255,0.1)', margin: '8px 0' }} />
                          {payload.map((entry, index) => (
                            <p key={index} style={{ color: entry.color, fontSize: '0.85rem', margin: '4px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span style={{ backgroundColor: entry.color, width: '8px', height: '8px', borderRadius: '50%' }} />
                              {entry.name}: <span style={{ fontWeight: 800 }}>{entry.value}</span>
                            </p>
                          ))}
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend
                  verticalAlign="top"
                  align="right"
                  height={36}
                  iconType="circle"
                  wrapperStyle={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px' }}
                />
                <Line
                  type="monotone"
                  dataKey="Company Employee"
                  stroke="#00f2ff"
                  strokeWidth={3}
                  dot={{ r: 4, fill: '#00f2ff', strokeWidth: 2, stroke: '#0a192f' }}
                  activeDot={{ r: 6, strokeWidth: 0, style: { filter: 'url(#line-glow)' } }}
                  animationDuration={1500}
                />
                <Line
                  type="monotone"
                  dataKey="Freelancer"
                  stroke="#7000ff"
                  strokeWidth={3}
                  dot={{ r: 4, fill: '#7000ff', strokeWidth: 2, stroke: '#0a192f' }}
                  activeDot={{ r: 6, strokeWidth: 0, style: { filter: 'url(#line-glow)' } }}
                  animationDuration={1500}
                  delay={200}
                />
                <Line
                  type="monotone"
                  dataKey="Guest User"
                  stroke="#ff00ff"
                  strokeWidth={3}
                  dot={{ r: 4, fill: '#ff00ff', strokeWidth: 2, stroke: '#0a192f' }}
                  activeDot={{ r: 6, strokeWidth: 0, style: { filter: 'url(#line-glow)' } }}
                  animationDuration={1500}
                  delay={400}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-stats-mini">
            <p className="rose-chart-info" style={{ marginTop: '1rem', textAlign: 'center' }}>
              <span className="info-icon">📈</span>
              Analyzing candidate acquisition flow for current <strong>{timeframe}ly</strong> cycle.
            </p>
          </div>
        </motion.div>


        <motion.div
          className="dashboard-section exp-distribution-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <div className="section-header-row">
            <h3>Experience Distribution</h3>
            <span className="section-subtitle">Density Analysis (Years)</span>
          </div>
          <div className="chart-container" style={{ height: '280px', marginTop: '1.5rem' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dashboardData.experienceDistribution} margin={{ top: 10, right: 30, left: 10, bottom: 35 }}>
                <defs>
                  <linearGradient id="colorExp" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00f2ff" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#00f2ff" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="exp"
                  stroke="#94a3b8"
                  fontSize={10}
                  fontWeight={700}
                  axisLine={false}
                  tickLine={false}
                  interval={0}
                  height={50}
                  padding={{ left: 10, right: 10 }}
                  label={{ value: 'Years of Experience', position: 'insideBottom', offset: 0, fill: '#64748b', fontSize: 10, fontWeight: 700 }}
                />
                <YAxis
                  stroke="#94a3b8"
                  fontSize={12}
                  fontWeight={600}
                  axisLine={false}
                  tickLine={false}
                  hide={true}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="custom-recharts-tooltip">
                          <p style={{ color: '#fff', fontSize: '12px', fontWeight: 800, margin: 0 }}>{payload[0].payload.exp} Years Exp</p>
                          <p style={{ color: '#00f2ff', fontSize: '14px', fontWeight: 900, margin: '4px 0 0' }}>Count: {payload[0].value}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="count"
                  stroke="#00f2ff"
                  strokeWidth={3}
                  fillOpacity={1}
                  fill="url(#colorExp)"
                  animationDuration={2000}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>


        <motion.div
          className="dashboard-section skills-radar-section"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="section-header-row">
            <h3>Top Candidate Skills</h3>
            <span className="section-subtitle">Real-time Analytics</span>
          </div>

          <div className="skills-analytics-radar" style={{ height: '400px', marginTop: '1.5rem' }}>
            {filteredTopSkills.length === 0 ? (
              <div className="no-data-placeholder">
                <p>No skill data detected in database</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={filteredTopSkills.slice(0, 8)}>
                  <PolarGrid stroke="rgba(16, 185, 129, 0.1)" />
                  <PolarAngleAxis
                    dataKey="skill"
                    tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 700 }}
                  />
                  <PolarRadiusAxis
                    angle={30}
                    domain={[0, 'auto']}
                    tick={false}
                    axisLine={false}
                  />
                  <Radar
                    name="Skills"
                    dataKey="count"
                    stroke="#10b981"
                    strokeWidth={2}
                    fill="#10b981"
                    fillOpacity={0.3}
                    dot={{ r: 4, fill: '#10b981', fillOpacity: 1 }}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className="custom-recharts-tooltip">
                            <p style={{ color: '#fff', fontSize: '12px', fontWeight: 800, margin: 0 }}>{payload[0].payload.skill}</p>
                            <p style={{ color: '#10b981', fontSize: '14px', fontWeight: 900, margin: '4px 0 0' }}>Count: {payload[0].value}</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            )}
          </div>
        </motion.div>

        <motion.div
          className="dashboard-section location-histogram-section"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <div className="section-header-row">
            <div className="header-left">
              <h3>Geospatial Talent Density</h3>
              <span className="section-subtitle">Talent by Location</span>
            </div>
            <div className="location-filter-wrapper">
              <select
                className="premium-cyber-select"
                value={selectedState}
                onChange={(e) => setSelectedState(e.target.value)}
                style={{ width: '180px' }}
              >
                <option value="">Top States</option>
                {INDIAN_STATES.map(state => (
                  <option key={state} value={state}>{state}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="location-analytics-histogram" style={{ height: '400px', marginTop: '1.5rem' }}>
            {dashboardData.locationDistribution.length === 0 ? (
              <div className="no-data-placeholder">
                <p>No location data available</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={(() => {
                    const sorted = [...dashboardData.locationDistribution].sort((a, b) => b.count - a.count);
                    if (!selectedState) return sorted.slice(0, 8);

                    const topState = sorted.find(s => s.state === selectedState);
                    const others = sorted.filter(s => s.state !== selectedState);

                    if (topState) {
                      return [topState, ...others.slice(0, 7)];
                    } else {
                      // If selected state has 0 count in database
                      return [{ state: selectedState, count: 0 }, ...others.slice(0, 7)];
                    }
                  })()}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                >
                  <defs>
                    <linearGradient id="barGradient" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.1} />
                      <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.8} />
                    </linearGradient>
                    <linearGradient id="highlightGradient" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#ec4899" stopOpacity={0.2} />
                      <stop offset="100%" stopColor="#ec4899" stopOpacity={1} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                  <XAxis type="number" hide />
                  <YAxis
                    dataKey="state"
                    type="category"
                    tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 700 }}
                    width={80}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    cursor={{ fill: 'rgba(139, 92, 246, 0.05)' }}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const isHighlighted = payload[0].payload.state === selectedState;
                        return (
                          <div className="custom-recharts-tooltip" style={{ borderColor: isHighlighted ? '#ec4899' : 'rgba(255,255,255,0.1)' }}>
                            <p style={{ color: '#fff', fontSize: '12px', fontWeight: 800, margin: 0 }}>
                              {payload[0].payload.state}
                              {isHighlighted && <span style={{ marginLeft: '8px', color: '#ec4899', fontSize: '10px' }}>● Selected Focus</span>}
                            </p>
                            <p style={{ color: isHighlighted ? '#ec4899' : '#8b5cf6', fontSize: '14px', fontWeight: 900, margin: '4px 0 0' }}>{payload[0].value} Professionals</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar
                    dataKey="count"
                    radius={[0, 4, 4, 0]}
                    barSize={20}
                    animationDuration={1500}
                  >
                    {(() => {
                      const data = (() => {
                        const sorted = [...dashboardData.locationDistribution].sort((a, b) => b.count - a.count);
                        if (!selectedState) return sorted.slice(0, 8);
                        const topState = sorted.find(s => s.state === selectedState);
                        const others = sorted.filter(s => s.state !== selectedState);
                        return topState ? [topState, ...others.slice(0, 7)] : [{ state: selectedState, count: 0 }, ...others.slice(0, 7)];
                      })();
                      return data.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.state === selectedState ? "url(#highlightGradient)" : "url(#barGradient)"}
                        />
                      ));
                    })()}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </motion.div>

      </div>



    </div>
  )
}

const getDepartmentColor = (dept) => {
  const colors = {
    'Company Employee': '#3282b8',
    'Freelancer': '#00d4ff',

    'Guest User': '#0f4c75',
    'Engineering': '#3282b8',
    'Design': '#00d4ff',
    'Marketing': '#bbe1fa',
    'Sales': '#0f4c75',
    'HR': '#43e97b'
  }
  return colors[dept] || '#3282b8'
}

export default AdminDashboard

