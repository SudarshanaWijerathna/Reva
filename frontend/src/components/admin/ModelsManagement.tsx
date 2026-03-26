import React, { useEffect, useState } from 'react';
import { API_BASE_URL } from '../../config/api';

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
  name: 'land-model-v1',
  model_type: 'land',
  version: 'v1',
  deployed_endpoint: '',
  artifact_url: '',
  performance_notes: '',
  mae: '',
  rmse: '',
  r2_score: '',
  mape: '',
  is_active: true,
};

const ModelsManagement: React.FC = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [showForm, setShowForm] = useState<boolean>(false);
  const [formData, setFormData] = useState<ModelFormData>(defaultFormData);

  const modelTypes: Array<ModelFormData['model_type']> = ['land', 'house', 'rental'];

  useEffect(() => {
    fetchModels();
  }, []);

  const getAuthToken = (): string | null => {
    return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  };

  const parseOptionalNumber = (value: string): number | null => {
    const normalized = value.trim();
    if (normalized === '') return null;
    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : null;
  };

  const fetchModels = async () => {
    try {
      setLoading(true);
      const token = getAuthToken();
      if (!token) throw new Error('User is not authenticated');

      const response = await fetch(`${API_BASE_URL}/api/admin/models`, {
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
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load models';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateModel = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = getAuthToken();
      if (!token) throw new Error('User is not authenticated');

      const payload = {
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
      };

      const response = await fetch(`${API_BASE_URL}/api/admin/models`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`Failed to create model: ${detail}`);
      }

      setShowForm(false);
      setFormData(defaultFormData);
      fetchModels();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create model';
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

      fetchModels();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to activate model';
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
              <label>Model Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="house-catboost-v1"
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
                  placeholder="v1"
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
                placeholder="https://house-service.<env>.<region>.azurecontainerapps.io/predict"
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Artifact URL</label>
                <input
                  type="url"
                  value={formData.artifact_url}
                  onChange={(e) => setFormData({ ...formData, artifact_url: e.target.value })}
                  placeholder="https://..."
                />
              </div>

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
            </div>

            <div className="form-row">
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
            </div>

            <div className="form-row">
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

              <div className="form-group">
                <label>Performance Notes</label>
                <input
                  type="text"
                  value={formData.performance_notes}
                  onChange={(e) => setFormData({ ...formData, performance_notes: e.target.value })}
                  placeholder="Best in 2026-Q1 validation"
                />
              </div>
            </div>

            <div className="form-group checkbox">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              />
              <label>Activate Immediately</label>
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
                <th>Name</th>
                <th>Type</th>
                <th>Version</th>
                <th>MAE</th>
                <th>Status</th>
                <th>Registered</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {models.map((model) => (
                <tr key={model.id}>
                  <td>
                    <strong>{model.name}</strong>
                    <div style={{ fontSize: '12px', color: '#666' }}>{model.deployed_endpoint}</div>
                  </td>
                  <td>{model.model_type}</td>
                  <td>{model.version}</td>
                  <td>{typeof model.mae === 'number' ? model.mae.toFixed(4) : 'N/A'}</td>
                  <td>
                    <span className={`status-badge ${model.is_active ? 'active' : 'inactive'}`}>
                      {model.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>{model.created_at ? new Date(model.created_at).toLocaleDateString() : 'N/A'}</td>
                  <td>
                    {!model.is_active && (
                      <button className="btn-action" onClick={() => handleActivate(model.id)}>
                        Activate
                      </button>
                    )}
                    {model.is_active && <span className="badge-active">Active</span>}
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
