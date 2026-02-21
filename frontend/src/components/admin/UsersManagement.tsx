import React, { useEffect, useState } from 'react';

interface User {
  id: number;
  email: string;
  created_at?: string;
}

const UsersManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState<string>("");

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
      
      const response = await fetch('http://localhost:8000/api/admin/users', {
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="users-summary">
        <p>Showing <strong>{filteredUsers.length}</strong> of <strong>{users.length}</strong> users</p>
      </div>
    </div>
  );
};

export default UsersManagement;
