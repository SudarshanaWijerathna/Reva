import React, { useEffect, useMemo, useState } from 'react';
import { API_BASE_URL } from '../../config/api';
import { getAuthToken } from '../../services/authService';

interface Model {
  id: number;
  name: string;
  model_type: 'land' | 'house' | 'rental';
  version: string;
  deployed_endpoint: string;
  artifact_url?: string | null;
  performance_notes?: string | null;
  mae?: number | null;
  rmse?: number | null;
  r2_score?: number | null;
  mape?: number | null;
  is_active: boolean;
  uploaded_by_email?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

interface ModelFormData {
  name: string;
  model_type: 'land' | 'house' | 'rental';
  version: string;
  deployed_endpoint: string;
  artifact_url: string;
  performance_notes: string;
  mae: string;
  rmse: string;
  r2_score: string;
  mape: string;
  is_active: boolean;
}

const defaultFormData: ModelFormData = {
  name: '',
  model_type: 'land',
  version: 'v1',
  deployed_endpoint: '',
  artifact_url: '',
  performance_notes: '',
  mae: '',
  rmse: '',
  r2_score: '',
  mape: '',
  is_active: false,
};

const modelTypes: Array<ModelFormData['model_type']> = ['land', 'house', 'rental'];

const formatMetric = (value?: number | null): string => {
  return typeof value === 'number' ? value.toFixed(4) : 'N/A';
};

const formatDateTime = (value?: string | null): string => {
  if (!value) return 'N/A';
  return new Date(value).toLocaleString();
};

const ModelsManagement: React.FC = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [showForm, setShowForm] = useState<boolean>(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [expandedModelId, setExpandedModelId] = useState<number | null>(null);
  const [selectedModelType, setSelectedModelType] = useState<string>('all');
  const [activeOnly, setActiveOnly] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [formData, setFormData] = useState<ModelFormData>(defaultFormData);

  useEffect(() => {
    fetchModels();
  }, [selectedModelType, activeOnly]);

  useEffect(() => {
    if (!successMessage) return;
    const timer = setTimeout(() => setSuccessMessage(''), 3000);
    return () => clearTimeout(timer);
  }, [successMessage]);

  const selectedModel = useMemo(
    () => models.find((model) => model.id === expandedModelId) || null,
    [models, expandedModelId]
  );

  const parseOptionalNumber = (value: string): number | null => {
    const normalized = value.trim();
    if (!normalized) return null;
    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : null;
  };

  const buildPayload = () => ({
    name: formData.name.trim(),
    model_type: formData.model_type,
    version: formData.version.trim() || 'v1',
    deployed_endpoint: formData.deployed_endpoint.trim(),
    artifact_url: formData.artifact_url.trim() || null,
    performance_notes: formData.performance_notes.trim() || null,
    mae: parseOptionalNumber(formData.mae),
    rmse: parseOptionalNumber(formData.rmse),
    r2_score: parseOptionalNumber(formData.r2_score),
    mape: parseOptionalNumber(formData.mape),
    is_active: formData.is_active,
  });

  const resetForm = () => {
    setFormData(defaultFormData);
    setEditingId(null);
    setShowForm(false);
  };

  const populateForm = (model: Model) => {
    setFormData({
      name: model.name,
      model_type: model.model_type,
      version: model.version,
      deployed_endpoint: model.deployed_endpoint,
      artifact_url: model.artifact_url || '',
      performance_notes: model.performance_notes || '',
      mae: model.mae != null ? String(model.mae) : '',
      rmse: model.rmse != null ? String(model.rmse) : '',
      r2_score: model.r2_score != null ? String(model.r2_score) : '',
      mape: model.mape != null ? String(model.mape) : '',
      is_active: model.is_active,
    });
    setEditingId(model.id);
    setShowForm(true);
  };

  const fetchModels = async () => {
    try {
      setLoading(true);
      const token = getAuthToken();
      if (!token) throw new Error('User is not authenticated');

      const params = new URLSearchParams();
      if (selectedModelType !== 'all') params.set('model_type', selectedModelType);
      if (activeOnly) params.set('active_only', 'true');

      const query = params.toString();
      const response = await fetch(`${API_BASE_URL}/api/admin/models${query ? `?${query}` : ''}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`Failed to fetch models: ${detail}`);
      }

      const data: Model[] = await response.json();
      setModels(data);
      setError('');

      if (expandedModelId && !data.some((model) => model.id === expandedModelId)) {
        setExpandedModelId(null);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load models';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const token = getAuthToken();
      if (!token) throw new Error('User is not authenticated');

      const isEditing = editingId !== null;
      const response = await fetch(
        isEditing ? `${API_BASE_URL}/api/admin/models/${editingId}` : `${API_BASE_URL}/api/admin/models`,
        {
          method: isEditing ? 'PUT' : 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(buildPayload()),
        }
      );

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`Failed to ${isEditing ? 'update' : 'create'} model: ${detail}`);
      }

      const savedModel: Model = await response.json();
      resetForm();
      setExpandedModelId(savedModel.id);
      setSuccessMessage(isEditing ? 'Model updated successfully!' : 'Model registered successfully!');
      fetchModels();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save model';
      alert(errorMessage);
    }
  };

  const handleActivate = async (modelId: number) => {
    try {
      const token = getAuthToken();
      if (!token) throw new Error('User is not authenticated');

      const response = await fetch(`${API_BASE_URL}/api/admin/models/${modelId}/activate`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`Failed to activate model: ${detail}`);
      }

      const activatedModel: Model = await response.json();
      setExpandedModelId(activatedModel.id);
      setSuccessMessage(`Activated ${activatedModel.name}.`);
      fetchModels();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to activate model';
      alert(errorMessage);
    }
  };

  const handleDelete = async (model: Model) => {
    if (!window.confirm(`Delete model "${model.name}" (${model.version})?`)) {
      return;
    }

    try {
      const token = getAuthToken();
      if (!token) throw new Error('User is not authenticated');

      const response = await fetch(`${API_BASE_URL}/api/admin/models/${model.id}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`Failed to delete model: ${detail}`);
      }

      if (expandedModelId === model.id) {
        setExpandedModelId(null);
      }

      if (editingId === model.id) {
        resetForm();
      }

      setSuccessMessage(`Deleted ${model.name}.`);
      fetchModels();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete model';
      alert(errorMessage);
    }
  };

  return (
    <div className="models-management">
      <div className="content-header">
        <div>
          <h2>Models Management</h2>
          <div className="user-count">{models.length} models in registry</div>
        </div>
        <button className="btn-primary" onClick={() => (showForm ? resetForm() : setShowForm(true))}>
          {showForm ? 'Cancel' : '+ Register Model'}
        </button>
      </div>

      {successMessage && <div className="success-message">OK {successMessage}</div>}

      {showForm && (
        <div className="form-container">
          <h3>{editingId ? 'Edit Model Registry Entry' : 'Register New Model'}</h3>
          <form onSubmit={handleSubmit} className="admin-form">
            <div className="form-group">
              <label>Model Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="house-catboost-v2"
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Model Type *</label>
                <select
                  value={formData.model_type}
                  onChange={(e) =>
                    setFormData({ ...formData, model_type: e.target.value as ModelFormData['model_type'] })
                  }
                  required
                >
                  {modelTypes.map((type) => (
                    <option key={type} value={type}>
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Version *</label>
                <input
                  type="text"
                  value={formData.version}
                  onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                  placeholder="v2"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>Deployed Endpoint *</label>
              <input
                type="url"
                value={formData.deployed_endpoint}
                onChange={(e) => setFormData({ ...formData, deployed_endpoint: e.target.value })}
                placeholder="https://service.example.com/predict"
                required
              />
            </div>

            <div className="form-group">
              <label>Artifact URL</label>
              <input
                type="url"
                value={formData.artifact_url}
                onChange={(e) => setFormData({ ...formData, artifact_url: e.target.value })}
                placeholder="https://storage.example.com/model.pkl"
              />
            </div>

            <div className="form-group">
              <label>Performance Notes</label>
              <input
                type="text"
                value={formData.performance_notes}
                onChange={(e) => setFormData({ ...formData, performance_notes: e.target.value })}
                placeholder="Top performer on Colombo validation split"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>MAE</label>
                <input
                  type="number"
                  step="any"
                  value={formData.mae}
                  onChange={(e) => setFormData({ ...formData, mae: e.target.value })}
                  placeholder="2.31"
                />
              </div>

              <div className="form-group">
                <label>RMSE</label>
                <input
                  type="number"
                  step="any"
                  value={formData.rmse}
                  onChange={(e) => setFormData({ ...formData, rmse: e.target.value })}
                  placeholder="4.52"
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>R2 Score</label>
                <input
                  type="number"
                  step="any"
                  value={formData.r2_score}
                  onChange={(e) => setFormData({ ...formData, r2_score: e.target.value })}
                  placeholder="0.91"
                />
              </div>

              <div className="form-group">
                <label>MAPE</label>
                <input
                  type="number"
                  step="any"
                  value={formData.mape}
                  onChange={(e) => setFormData({ ...formData, mape: e.target.value })}
                  placeholder="8.2"
                />
              </div>
            </div>

            <div className="form-group checkbox">
              <input
                id="model-active"
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              />
              <label htmlFor="model-active">Set as active model for this type</label>
            </div>

            <button type="submit" className="btn-primary">
              {editingId ? 'Update Model' : 'Register Model'}
            </button>
          </form>
        </div>
      )}

      <div className="filter-bar">
        <label>Filter Models:</label>
        <div className="filter-buttons">
          {['all', ...modelTypes].map((type) => (
            <button
              key={type}
              className={`filter-btn ${selectedModelType === type ? 'active' : ''}`}
              onClick={() => setSelectedModelType(type)}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
          <button
            className={`filter-btn ${activeOnly ? 'active' : ''}`}
            onClick={() => setActiveOnly((current) => !current)}
          >
            Active Only
          </button>
        </div>
      </div>

      {selectedModel && (
        <div className="form-container model-details-card">
          <div className="content-header model-details-header">
            <div>
              <h3>{selectedModel.name}</h3>
              <div className="user-count">
                {selectedModel.model_type} · {selectedModel.version} · {selectedModel.is_active ? 'Active' : 'Inactive'}
              </div>
            </div>
            <div className="action-buttons">
              <button className="btn-edit" onClick={() => populateForm(selectedModel)}>
                Edit
              </button>
              {!selectedModel.is_active && (
                <button className="btn-action" onClick={() => handleActivate(selectedModel.id)}>
                  Activate
                </button>
              )}
              <button className="btn-delete" onClick={() => handleDelete(selectedModel)}>
                Delete
              </button>
            </div>
          </div>

          <div className="model-meta-grid">
            <div className="model-meta-item">
              <label>Endpoint</label>
              <span>{selectedModel.deployed_endpoint}</span>
            </div>
            <div className="model-meta-item">
              <label>Artifact URL</label>
              <span>{selectedModel.artifact_url || 'N/A'}</span>
            </div>
            <div className="model-meta-item">
              <label>Uploaded By</label>
              <span>{selectedModel.uploaded_by_email || 'N/A'}</span>
            </div>
            <div className="model-meta-item">
              <label>Created</label>
              <span>{formatDateTime(selectedModel.created_at)}</span>
            </div>
            <div className="model-meta-item">
              <label>Updated</label>
              <span>{formatDateTime(selectedModel.updated_at)}</span>
            </div>
            <div className="model-meta-item">
              <label>Notes</label>
              <span>{selectedModel.performance_notes || 'N/A'}</span>
            </div>
          </div>

          <div className="model-metrics-grid">
            <div className="metric-card">
              <label>MAE</label>
              <strong>{formatMetric(selectedModel.mae)}</strong>
            </div>
            <div className="metric-card">
              <label>RMSE</label>
              <strong>{formatMetric(selectedModel.rmse)}</strong>
            </div>
            <div className="metric-card">
              <label>R2 Score</label>
              <strong>{formatMetric(selectedModel.r2_score)}</strong>
            </div>
            <div className="metric-card">
              <label>MAPE</label>
              <strong>{formatMetric(selectedModel.mape)}</strong>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading models...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : models.length === 0 ? (
        <div className="empty-state">No models registered for this filter.</div>
      ) : (
        <div className="models-table">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Version</th>
                <th>Metrics</th>
                <th>Status</th>
                <th>Uploaded By</th>
                <th>Registered</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {models.map((model) => (
                <tr key={model.id}>
                  <td>
                    <strong>{model.name}</strong>
                    <div className="table-subtext">{model.deployed_endpoint}</div>
                  </td>
                  <td>
                    <span className="badge">{model.model_type}</span>
                  </td>
                  <td>{model.version}</td>
                  <td>
                    <div className="table-subtext">MAE: {formatMetric(model.mae)}</div>
                    <div className="table-subtext">RMSE: {formatMetric(model.rmse)}</div>
                  </td>
                  <td>
                    <span className={`status-badge ${model.is_active ? 'active' : 'inactive'}`}>
                      {model.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>{model.uploaded_by_email || 'N/A'}</td>
                  <td>{model.created_at ? new Date(model.created_at).toLocaleDateString() : 'N/A'}</td>
                  <td className="action-buttons">
                    <button
                      className="btn-action"
                      onClick={() => setExpandedModelId(expandedModelId === model.id ? null : model.id)}
                    >
                      {expandedModelId === model.id ? 'Hide' : 'View'}
                    </button>
                    <button className="btn-edit" onClick={() => populateForm(model)}>
                      Edit
                    </button>
                    {!model.is_active && (
                      <button className="btn-action" onClick={() => handleActivate(model.id)}>
                        Activate
                      </button>
                    )}
                    <button className="btn-delete" onClick={() => handleDelete(model)}>
                      Delete
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

export default ModelsManagement;
