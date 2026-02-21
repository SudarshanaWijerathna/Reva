import React, { useEffect, useState } from 'react';

interface Model {
  id: number;
  model_name: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

interface ModelFormData {
  model_name: string;
  active: boolean;
}

const ModelsManagement: React.FC = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [showForm, setShowForm] = useState<boolean>(false);
  
  const [formData, setFormData] = useState<ModelFormData>({
    model_name: 'land',
    active: true
  });

  const modelTypes = ['land', 'house', 'rental'];

  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
      
      const response = await fetch('http://localhost:8000/api/admin/models', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch models');
      }

      const data = await response.json();
      setModels(data);
      setError("");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load models";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateModel = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
      
      const response = await fetch('http://localhost:8000/api/admin/models', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Failed to create model');
      }

      setShowForm(false);
      setFormData({ model_name: 'land', active: true });
      fetchModels();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create model";
      alert(errorMessage);
    }
  };

  const handleSetActive = async (modelId: number) => {
    try {
      const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
      
      const response = await fetch(`http://localhost:8000/api/admin/models/${modelId}/set-active`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to set active model');
      }

      fetchModels();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to set active model";
      alert(errorMessage);
    }
  };

  return (
    <div className="models-management">
      <div className="content-header">
        <h2>Models Management</h2>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ Register Model'}
        </button>
      </div>

      {showForm && (
        <div className="form-container">
          <h3>Register New Model</h3>
          <form onSubmit={handleCreateModel} className="admin-form">
            <div className="form-group">
              <label>Model Type *</label>
              <select
                value={formData.model_name}
                onChange={(e) => setFormData({...formData, model_name: e.target.value})}
                required
              >
                {modelTypes.map(type => (
                  <option key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group checkbox">
              <input
                type="checkbox"
                checked={formData.active}
                onChange={(e) => setFormData({...formData, active: e.target.checked})}
              />
              <label>Active</label>
            </div>

            <button type="submit" className="btn-primary">Register Model</button>
          </form>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading models...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : models.length === 0 ? (
        <div className="empty-state">No models registered</div>
      ) : (
        <div className="models-table">
          <table>
            <thead>
              <tr>
                <th>Model Type</th>
                <th>Status</th>
                <th>Registered</th>
                <th>Last Updated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {models.map(model => (
                <tr key={model.id}>
                  <td><strong>{model.model_name.charAt(0).toUpperCase() + model.model_name.slice(1)}</strong></td>
                  <td>
                    <span className={`status-badge ${model.active ? 'active' : 'inactive'}`}>
                      {model.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>{new Date(model.created_at).toLocaleDateString()}</td>
                  <td>{new Date(model.updated_at).toLocaleDateString()}</td>
                  <td>
                    {!model.active && (
                      <button 
                        className="btn-action"
                        onClick={() => handleSetActive(model.id)}
                      >
                        Activate
                      </button>
                    )}
                    {model.active && (
                      <span className="badge-active">✓ Active</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default ModelsManagement;
