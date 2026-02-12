import { useState, useEffect } from 'react'
import { getPlatformAdminUsers, deletePlatformUser } from '../../config/api'
import './AdminUsers.css'

const formatRole = (mode) => {
  if (!mode) return 'ADMINISTRATOR'
  return mode.replace(/_/g, ' ').toUpperCase()
}

const AdminUsers = () => {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deletingId, setDeletingId] = useState(null)

  const fetchUsers = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await getPlatformAdminUsers()
      setUsers(res?.users ?? [])
    } catch (err) {
      console.error('Error loading platform users:', err)
      setError(err.message || 'Failed to load users')
      setUsers([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [])

  const handleDelete = async (user) => {
    if (!window.confirm(`Remove "${user.name}" (${user.email}) from platform? This will delete their credentials from the database.`)) return
    try {
      setDeletingId(user.id)
      setError(null)
      await deletePlatformUser(user.id)
      setUsers((prev) => prev.filter((u) => u.id !== user.id))
    } catch (err) {
      setError(err.message || err.detail || 'Failed to delete user')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="admin-users-page">
      <h2 className="admin-users-heading">Users</h2>

      {error && (
        <div className="admin-users-error">{error}</div>
      )}

      {loading ? (
        <div className="admin-users-loading">Loading users…</div>
      ) : users.length === 0 ? (
        <div className="admin-users-empty">No platform users found.</div>
      ) : (
        <div className="platform-admins-section">
          <table className="platform-admins-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Employee ID</th>
                <th>Role</th>
                <th className="th-actions">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td className="platform-admin-name">{u.name}</td>
                  <td className="platform-admin-email">{u.email}</td>
                  <td className="platform-admin-id">{u.employee_id || '—'}</td>
                  <td className="platform-admin-role">{formatRole(u.mode)}</td>
                  <td className="platform-admin-actions">
                    <button
                      type="button"
                      className="admin-user-delete-btn"
                      onClick={() => handleDelete(u)}
                      disabled={deletingId === u.id}
                      title="Remove user from platform (delete credentials)"
                    >
                      {deletingId === u.id ? '…' : 'Remove'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default AdminUsers
