import { useState } from 'react'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import Navbar from '../components/Navbar'
import AdminDashboard from '../components/admin/AdminDashboard'
import AdminPortalLinks from '../components/admin/AdminPortalLinks'
import SearchTalent from '../components/admin/SearchTalent'
import SearchUsingJD from '../components/admin/SearchUsingJD'
import AddNewResume from '../components/admin/AddNewResume'
import Records from '../components/admin/Records'
import ManageJobOpenings from '../components/admin/ManageJobOpenings'
import AdminTransition from '../components/admin/AdminTransition'
import CyberBackground from '../components/admin/CyberBackground'
import './Admin.css'

const Admin = () => {
  const { userProfile } = useApp()
  const [activeTab, setActiveTab] = useState('dashboard')
  const [showEntrance, setShowEntrance] = useState(() => {
    // Only show if not shown this session
    return !sessionStorage.getItem('adminEntranceShown')
  })
  const [initialFilter, setInitialFilter] = useState(null)

  const navigateToRecords = (filter = null) => {
    setInitialFilter(filter)
    setActiveTab('records')
  }

  const handleEntranceComplete = () => {
    setShowEntrance(false)
    sessionStorage.setItem('adminEntranceShown', 'true')
  }

  if (showEntrance) {
    return <AdminTransition onComplete={handleEntranceComplete} />
  }

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊', colorClass: 'tab-dashboard' },
    { id: 'links', label: 'Links', icon: '🔗', colorClass: 'tab-links' },
    { id: 'records', label: 'Records', icon: '📂', colorClass: 'tab-records' },
    { id: 'search-talent', label: 'Search Talent', icon: '🔍', colorClass: 'tab-search-talent' },
    { id: 'search-jd', label: 'Search Using JD', icon: '📝', colorClass: 'tab-search-jd' },
    { id: 'add-resume', label: 'Add New Resume', icon: '➕', colorClass: 'tab-add-resume' },
    { id: 'manage-jobs', label: 'Manage Jobs', icon: '💼', colorClass: 'tab-manage-jobs' }
  ]

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <AdminDashboard onNavigateToRecords={navigateToRecords} />
      case 'links':
        return <AdminPortalLinks />
      case 'records':
        return <Records initialFilter={initialFilter} setInitialFilter={setInitialFilter} />
      case 'search-talent':
        return <SearchTalent />
      case 'search-jd':
        return <SearchUsingJD />
      case 'add-resume':
        return <AddNewResume />
      case 'manage-jobs':
        return <ManageJobOpenings />
      default:
        return <AdminDashboard onNavigateToRecords={navigateToRecords} />
    }
  }

  return (
    <div className="admin-container">
      <CyberBackground />
      <Navbar
        userProfile={userProfile}
        showProfile={true}
        adminTabs={tabs}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <div className="admin-content">
        <motion.div
          className="admin-content-area"
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {renderContent()}
        </motion.div>
      </div>
    </div>
  )
}

export default Admin

