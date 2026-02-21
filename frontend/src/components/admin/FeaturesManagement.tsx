import React, { useEffect, useState } from 'react';

interface Feature {
  id: number;
  name: string;
  label: string;
  data_type: string;
  model_type: string;
  required: boolean;
  active: boolean;
  created_at: string;
}

interface FeatureFormData {
  name: string;
  label: string;
  data_type: string;
  model_type: string;
  required: boolean;
  active: boolean;
}

const FeaturesManagement: React.FC = () => {
  const [features, setFeatures] = useState<Feature[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [showForm, setShowForm] = useState<boolean>(false);
  const [selectedModelType, setSelectedModelType] = useState<string>("all");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [successMessage, setSuccessMessage] = useState<string>("");
  
  const [formData, setFormData] = useState<FeatureFormData>({
    name: '',
    label: '',
    data_type: 'float',
    model_type: 'land',
    required: false,
    active: true
  });

  const modelTypes = ['land', 'house', 'rental'];
  const dataTypes = ['boolean', 'float', 'int', 'string'];

  useEffect(() => {
    fetchFeatures();
  }, [selectedModelType]);

  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(""), 3000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  const fetchFeatures = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
      
      const url = selectedModelType === 'all' 
        ? 'http://localhost:8000/api/admin/features'
        : `http://localhost:8000/api/admin/features?model_type=${selectedModelType}`;

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch features');
      }

      const data = await response.json();
      setFeatures(data);
      setError("");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load features";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFeature = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
      
      const method = editingId ? 'PUT' : 'POST';
      const url = editingId 
        ? `http://localhost:8000/api/admin/features/${editingId}`
        : 'http://localhost:8000/api/admin/features';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error(`Failed to ${editingId ? 'update' : 'create'} feature`);
      }

      setShowForm(false);
      setEditingId(null);
      setFormData({
        name: '',
        label: '',
        data_type: 'float',
        model_type: 'land',
        required: false,
        active: true
      });
      setSuccessMessage(editingId ? 'Feature updated successfully!' : 'Feature created successfully!');
      fetchFeatures();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to save feature";
      alert(errorMessage);
    }
  };

  const handleEditFeature = (feature: Feature) => {
    setFormData({
      name: feature.name,
      label: feature.label,
      data_type: feature.data_type,
      model_type: feature.model_type,
      required: feature.required,
      active: feature.active
    });
    setEditingId(feature.id);
    setShowForm(true);
  };

  const handleDeleteFeature = async (featureId: number, featureName: string) => {
    if (!window.confirm(`Are you sure you want to delete the feature "${featureName}"?`)) {
      return;
    }

    try {
      const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
      
      const response = await fetch(`http://localhost:8000/api/admin/features/${featureId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete feature');
      }

      setSuccessMessage('Feature deleted successfully!');
      fetchFeatures();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to delete feature";
      alert(errorMessage);
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setShowForm(false);
    setFormData({
      name: '',
      label: '',
      data_type: 'float',
      model_type: 'land',
      required: false,
      active: true
    });
  };

  const filteredFeatures = selectedModelType === 'all' 
    ? features 
    : features.filter(f => f.model_type === selectedModelType);

  return (
    <div className="features-management">
      <div className="content-header">
        <h2>Features Management</h2>
        <button 
          className="btn-primary" 
          onClick={() => editingId ? handleCancelEdit() : setShowForm(!showForm)}
        >
          {showForm ? 'Cancel' : '+ Create Feature'}
        </button>
      </div>

      {successMessage && (
        <div className="success-message">
          ✓ {successMessage}
        </div>
      )}

      {showForm && (
        <div className="form-container">
          <h3>{editingId ? 'Edit Feature' : 'Create New Feature'}</h3>
          <form onSubmit={handleCreateFeature} className="admin-form">
            <div className="form-group">
              <label>Feature Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="e.g., square_feet"
                required
              />
            </div>

            <div className="form-group">
              <label>Feature Label *</label>
              <input
                type="text"
                value={formData.label}
                onChange={(e) => setFormData({...formData, label: e.target.value})}
                placeholder="e.g., Square Feet"
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Data Type *</label>
                <select
                  value={formData.data_type}
                  onChange={(e) => setFormData({...formData, data_type: e.target.value})}
                  required
                >
                  {dataTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Model Type *</label>
                <select
                  value={formData.model_type}
                  onChange={(e) => setFormData({...formData, model_type: e.target.value})}
                  required
                >
                  {modelTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group checkbox">
                <input
                  type="checkbox"
                  checked={formData.required}
                  onChange={(e) => setFormData({...formData, required: e.target.checked})}
                />
                <label>Required Field</label>
              </div>

              <div className="form-group checkbox">
                <input
                  type="checkbox"
                  checked={formData.active}
                  onChange={(e) => setFormData({...formData, active: e.target.checked})}
                />
                <label>Active</label>
              </div>
            </div>

            <button type="submit" className="btn-primary">
              {editingId ? 'Update Feature' : 'Create Feature'}
            </button>
          </form>
        </div>
      )}

      <div className="filter-bar">
        <label>Filter by Model Type:</label>
        <div className="filter-buttons">
          {['all', ...modelTypes].map(type => (
            <button
              key={type}
              className={`filter-btn ${selectedModelType === type ? 'active' : ''}`}
              onClick={() => setSelectedModelType(type)}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading features...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : filteredFeatures.length === 0 ? (
        <div className="empty-state">No features found</div>
      ) : (
        <div className="features-table">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Label</th>
                <th>Data Type</th>
                <th>Model Type</th>
                <th>Required</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredFeatures.map(feature => (
                <tr key={feature.id}>
                  <td><strong>{feature.name}</strong></td>
                  <td>{feature.label}</td>
                  <td><code>{feature.data_type}</code></td>
                  <td><span className="badge">{feature.model_type}</span></td>
                  <td>{feature.required ? '✓' : '-'}</td>
                  <td>
                    <span className={`status-badge ${feature.active ? 'active' : 'inactive'}`}>
                      {feature.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>{new Date(feature.created_at).toLocaleDateString()}</td>
                  <td className="action-buttons">
                    <button 
                      className="btn-edit"
                      onClick={() => handleEditFeature(feature)}
                      title="Edit feature"
                    >
                      ✎ Edit
                    </button>
                    <button 
                      className="btn-delete"
                      onClick={() => handleDeleteFeature(feature.id, feature.name)}
                      title="Delete feature"
                    >
                      🗑 Delete
                    </button>
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

export default FeaturesManagement;
