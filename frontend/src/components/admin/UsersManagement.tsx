import React, { useEffect, useState } from 'react';
import { API_BASE_URL } from '../../config/api';

interface User {
  id: number;
  email: string;
  created_at?: string;
}

interface DeleteUserResponse {
  id: number;
  email: string;
  deleted_properties: number;
  deleted_predictions: number;
  deleted_profile: boolean;
  deleted_preferences: boolean;
  message: string;
}

const UsersManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [successMessage, setSuccessMessage] = useState<string>("");
  const [deletingUserId, setDeletingUserId] = useState<number | null>(null);
  const currentUserEmail = (localStorage.getItem("user_email") || sessionStorage.getItem("user_email") || "").toLowerCase();

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
      
      const response = await fetch(`${API_BASE_URL}/api/admin/users`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch users');
      }

      const data = await response.json();
      setUsers(data);
      setError("");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load users";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (user: User) => {
    const isCurrentAdmin = user.email.toLowerCase() === currentUserEmail;
    if (isCurrentAdmin) {
      setError("You cannot delete your own admin account.");
      return;
    }

    const confirmed = window.confirm(
      `Delete ${user.email}?\n\nThis will permanently remove the user and related data such as their profile, preferences, saved properties, and prediction history.`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingUserId(user.id);
      setError("");
      setSuccessMessage("");

      const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
      const response = await fetch(`${API_BASE_URL}/api/admin/users/${user.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json().catch(() => null) as DeleteUserResponse | { detail?: string } | null;

      if (!response.ok) {
        throw new Error(data && 'detail' in data && data.detail ? data.detail : 'Failed to delete user');
      }

      const deleted = data as DeleteUserResponse;
      setUsers((prevUsers) => prevUsers.filter((item) => item.id !== user.id));
      setSuccessMessage(
        `${deleted.email} was deleted. Removed ${deleted.deleted_properties} propert${deleted.deleted_properties === 1 ? 'y' : 'ies'} and ${deleted.deleted_predictions} prediction record${deleted.deleted_predictions === 1 ? '' : 's'}.`
      );
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to delete user";
      setError(errorMessage);
    } finally {
      setDeletingUserId(null);
    }
  };

  const filteredUsers = users.filter(user =>
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="users-management">
      <div className="content-header">
        <h2>Users Management</h2>
        <div className="user-count">Total Users: <strong>{users.length}</strong></div>
      </div>

      <div className="search-container">
        <input
          type="text"
          placeholder="Search by email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
      </div>

      {successMessage && <div className="success-message">{successMessage}</div>}

      {loading ? (
        <div className="loading">Loading users...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : filteredUsers.length === 0 ? (
        <div className="empty-state">No users found</div>
      ) : (
        <div className="users-table">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Email</th>
                <th>Joined Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((user) => (
                <tr key={user.id}>
                  <td>{user.id}</td>
                  <td><strong>{user.email}</strong></td>
                  <td>
                    {user.created_at 
                      ? new Date(user.created_at).toLocaleDateString()
                      : 'N/A'
                    }
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button
                        type="button"
                        className="btn-delete"
                        onClick={() => handleDeleteUser(user)}
                        disabled={deletingUserId === user.id || user.email.toLowerCase() === currentUserEmail}
                        title={user.email.toLowerCase() === currentUserEmail ? "You can't delete your own admin account" : "Delete user and related data"}
                      >
                        {deletingUserId === user.id ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="users-summary">
        <p>Showing <strong>{filteredUsers.length}</strong> of <strong>{users.length}</strong> users</p>
        <p>Deleting a user permanently removes their related profile, preferences, saved properties, and prediction history.</p>
      </div>
    </div>
  );
};

export default UsersManagement;
