import React, { useEffect, useState } from 'react';
import { portfolioService, type PropertyDetailData } from '../services/portfolioService';
import '../assets/css/dashboard.css';

type PropertyType = 'housing' | 'rental' | 'land';

interface HousingFormData {
  location: string;
  purchase_price: string;
  purchase_date: string;
  land_size_perches: string;
  house_size_sqft: string;
  floors: string;
  built_year: string;
  property_condition: string;
}

interface RentalFormData {
  location: string;
  purchase_price: string;
  purchase_date: string;
  monthly_rent: string;
  occupancy_status: string;
  lease_start_date: string;
  lease_end_date: string;
  tenant_type: string;
}

interface LandFormData {
  location: string;
  purchase_price: string;
  purchase_date: string;
  land_size: string;
  zoning_type: string;
  road_access: string;
}

interface AddPropertyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPropertyAdded: () => void;
  initialProperty?: PropertyDetailData | null;
}

const AddPropertyModal: React.FC<AddPropertyModalProps> = ({ isOpen, onClose, onPropertyAdded, initialProperty }) => {
  const [activeTab, setActiveTab] = useState<PropertyType>(initialProperty?.property_type || 'housing');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [success, setSuccess] = useState<string>("");
  const isEditMode = Boolean(initialProperty);

  const [housingForm, setHousingForm] = useState<HousingFormData>({
    location: '',
    purchase_price: '',
    purchase_date: '',
    land_size_perches: '',
    house_size_sqft: '',
    floors: '',
    built_year: '',
    property_condition: 'good',
  });

  const [rentalForm, setRentalForm] = useState<RentalFormData>({
    location: '',
    purchase_price: '',
    purchase_date: '',
    monthly_rent: '',
    occupancy_status: 'occupied',
    lease_start_date: '',
    lease_end_date: '',
    tenant_type: 'family',
  });

  const [landForm, setLandFormData] = useState<LandFormData>({
    location: '',
    purchase_price: '',
    purchase_date: '',
    land_size: '',
    zoning_type: 'residential',
    road_access: '',
  });

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    if (initialProperty) {
      setActiveTab(initialProperty.property_type);
      setError('');
      setSuccess('');

      const baseValues = {
        location: initialProperty.location || '',
        purchase_price: initialProperty.purchase_price?.toString() || '',
        purchase_date: initialProperty.purchase_date || '',
      };

      if (initialProperty.property_type === 'housing') {
        setHousingForm({
          ...baseValues,
          land_size_perches: initialProperty.land_size_perches?.toString() || '',
          house_size_sqft: initialProperty.house_size_sqft?.toString() || '',
          floors: initialProperty.floors?.toString() || '',
          built_year: initialProperty.built_year?.toString() || '',
          property_condition: initialProperty.property_condition || 'good',
        });
      }

      if (initialProperty.property_type === 'rental') {
        setRentalForm({
          ...baseValues,
          monthly_rent: initialProperty.monthly_rent?.toString() || '',
          occupancy_status: initialProperty.occupancy_status || 'occupied',
          lease_start_date: initialProperty.lease_start_date || '',
          lease_end_date: initialProperty.lease_end_date || '',
          tenant_type: initialProperty.tenant_type || 'family',
        });
      }

      if (initialProperty.property_type === 'land') {
        setLandFormData({
          ...baseValues,
          land_size: initialProperty.land_size?.toString() || '',
          zoning_type: initialProperty.zoning_type || 'residential',
          road_access: initialProperty.road_access || '',
        });
      }
      return;
    }

    resetForm();
  }, [initialProperty, isOpen]);

  const handleHousingChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setHousingForm({ ...housingForm, [e.target.name]: e.target.value });
  };

  const handleRentalChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setRentalForm({ ...rentalForm, [e.target.name]: e.target.value });
  };

  const handleLandChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setLandFormData({ ...landForm, [e.target.name]: e.target.value });
  };

  const validateForm = (data: any): boolean => {
    const requiredFields = ['location', 'purchase_price', 'purchase_date'];
    
    for (const field of requiredFields) {
      if (!data[field]) {
        setError(`${field.replace(/_/g, ' ')} is required`);
        return false;
      }
    }
    
    if (isNaN(parseFloat(data.purchase_price))) {
      setError('Purchase price must be a valid number');
      return false;
    }
    
    return true;
  };

  const handleSubmitHousing = async () => {
    setError("");
    setSuccess("");

    if (!validateForm(housingForm)) return;

    const requiredHousingFields = ['land_size_perches', 'house_size_sqft', 'floors', 'built_year'];
    for (const field of requiredHousingFields) {
      if (!housingForm[field as keyof HousingFormData]) {
        setError(`${field.replace(/_/g, ' ')} is required`);
        return;
      }
    }

    setLoading(true);

    try {
      const payload = {
        location: housingForm.location,
        purchase_price: parseFloat(housingForm.purchase_price),
        purchase_date: housingForm.purchase_date,
        land_size_perches: parseFloat(housingForm.land_size_perches),
        house_size_sqft: parseFloat(housingForm.house_size_sqft),
        floors: parseInt(housingForm.floors),
        built_year: parseInt(housingForm.built_year),
        property_condition: housingForm.property_condition,
      };

      if (isEditMode && initialProperty) {
        await portfolioService.updateHousingProperty(initialProperty.property_id, payload);
        setSuccess('Housing property updated successfully!');
      } else {
        await portfolioService.createHousingProperty(payload);
        setSuccess('Housing property added successfully!');
      }
      
      setTimeout(() => {
        resetForm();
        onPropertyAdded();
        onClose();
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add property');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitRental = async () => {
    setError("");
    setSuccess("");

    if (!validateForm(rentalForm)) return;

    const requiredRentalFields = ['monthly_rent', 'lease_start_date', 'lease_end_date'];
    for (const field of requiredRentalFields) {
      if (!rentalForm[field as keyof RentalFormData]) {
        setError(`${field.replace(/_/g, ' ')} is required`);
        return;
      }
    }

    setLoading(true);

    try {
      const payload = {
        location: rentalForm.location,
        purchase_price: parseFloat(rentalForm.purchase_price),
        purchase_date: rentalForm.purchase_date,
        monthly_rent: parseFloat(rentalForm.monthly_rent),
        occupancy_status: rentalForm.occupancy_status,
        lease_start_date: rentalForm.lease_start_date,
        lease_end_date: rentalForm.lease_end_date,
        tenant_type: rentalForm.tenant_type,
      };

      if (isEditMode && initialProperty) {
        await portfolioService.updateRentalProperty(initialProperty.property_id, payload);
        setSuccess('Rental property updated successfully!');
      } else {
        await portfolioService.createRentalProperty(payload);
        setSuccess('Rental property added successfully!');
      }
      
      setTimeout(() => {
        resetForm();
        onPropertyAdded();
        onClose();
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add property');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitLand = async () => {
    setError("");
    setSuccess("");

    if (!validateForm(landForm)) return;

    const requiredLandFields = ['land_size', 'road_access'];
    for (const field of requiredLandFields) {
      if (!landForm[field as keyof LandFormData]) {
        setError(`${field.replace(/_/g, ' ')} is required`);
        return;
      }
    }

    setLoading(true);

    try {
      const payload = {
        location: landForm.location,
        purchase_price: parseFloat(landForm.purchase_price),
        purchase_date: landForm.purchase_date,
        land_size: parseFloat(landForm.land_size),
        zoning_type: landForm.zoning_type,
        road_access: landForm.road_access,
      };

      if (isEditMode && initialProperty) {
        await portfolioService.updateLandProperty(initialProperty.property_id, payload);
        setSuccess('Land property updated successfully!');
      } else {
        await portfolioService.createLandProperty(payload);
        setSuccess('Land property added successfully!');
      }
      
      setTimeout(() => {
        resetForm();
        onPropertyAdded();
        onClose();
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add property');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setHousingForm({
      location: '',
      purchase_price: '',
      purchase_date: '',
      land_size_perches: '',
      house_size_sqft: '',
      floors: '',
      built_year: '',
      property_condition: 'good',
    });
    setRentalForm({
      location: '',
      purchase_price: '',
      purchase_date: '',
      monthly_rent: '',
      occupancy_status: 'occupied',
      lease_start_date: '',
      lease_end_date: '',
      tenant_type: 'family',
    });
    setLandFormData({
      location: '',
      purchase_price: '',
      purchase_date: '',
      land_size: '',
      zoning_type: 'residential',
      road_access: '',
    });
    setError("");
    setSuccess("");
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Blur overlay */}
      {/* Backdrop */}
      <div className="property-modal-overlay" onClick={onClose} />

      {/* Modal Card */}
      <div className="property-modal-card">
        {/* Header */}
        <div className="property-modal-header">
          <h2>{isEditMode ? 'Edit Property' : 'Add New Property'}</h2>
          <button onClick={onClose} className="property-modal-close-btn" aria-label="Close modal">
            <i className="fa-solid fa-xmark"></i>
          </button>
        </div>

        {/* Tabs */}
        <div className="property-modal-tabs">
          {(['housing', 'rental', 'land'] as PropertyType[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              disabled={isEditMode && initialProperty?.property_type !== tab}
              className={`property-modal-tab ${activeTab === tab ? 'active' : ''}`}
            >
              <img
                src={
                  tab === 'housing'
                    ? '/img/icons/house.svg'
                    : tab === 'rental'
                    ? '/img/icons/rental.svg'
                    : '/img/icons/land.svg'
                }
                alt={tab}
                className="property-tab-svg"
              />
              <span>{tab.charAt(0).toUpperCase() + tab.slice(1)}</span>
            </button>
          ))}
        </div>

        {/* Content Body */}
        <div className="property-modal-body">
          {/* Error Message */}
          {error && (
            <div className="property-modal-alert error">
              <i className="fa-solid fa-circle-exclamation"></i>
              <span>{error}</span>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="property-modal-alert success">
              <i className="fa-solid fa-circle-check"></i>
              <span>{success}</span>
            </div>
          )}

          {/* Housing Form */}
          {activeTab === 'housing' && (
            <form onSubmit={(e) => { e.preventDefault(); handleSubmitHousing(); }} className="property-modal-form">
              <div className="property-form-group">
                <label className="property-form-label">Location *</label>
                <input
                  type="text"
                  name="location"
                  placeholder="Property location"
                  value={housingForm.location}
                  onChange={handleHousingChange}
                  className="property-form-input"
                  required
                />
              </div>

              <div className="property-form-grid-2">
                <div className="property-form-group">
                  <label className="property-form-label">Purchase Price *</label>
                  <input
                    type="number"
                    name="purchase_price"
                    placeholder="LKR"
                    value={housingForm.purchase_price}
                    onChange={handleHousingChange}
                    step="0.01"
                    className="property-form-input"
                    required
                  />
                </div>

                <div className="property-form-group">
                  <label className="property-form-label">Purchase Date *</label>
                  <input
                    type="date"
                    name="purchase_date"
                    value={housingForm.purchase_date}
                    onChange={handleHousingChange}
                    className="property-form-input"
                    required
                  />
                </div>
              </div>

              <div className="property-form-grid-2">
                <div className="property-form-group">
                  <label className="property-form-label">Land Size (Perches) *</label>
                  <input
                    type="number"
                    name="land_size_perches"
                    placeholder="Perches"
                    value={housingForm.land_size_perches}
                    onChange={handleHousingChange}
                    step="0.01"
                    className="property-form-input"
                    required
                  />
                </div>

                <div className="property-form-group">
                  <label className="property-form-label">House Size (Sqft) *</label>
                  <input
                    type="number"
                    name="house_size_sqft"
                    placeholder="Sqft"
                    value={housingForm.house_size_sqft}
                    onChange={handleHousingChange}
                    step="0.01"
                    className="property-form-input"
                    required
                  />
                </div>
              </div>

              <div className="property-form-grid-2">
                <div className="property-form-group">
                  <label className="property-form-label">Floors *</label>
                  <input
                    type="number"
                    name="floors"
                    placeholder="Number of floors"
                    value={housingForm.floors}
                    onChange={handleHousingChange}
                    className="property-form-input"
                    required
                  />
                </div>

                <div className="property-form-group">
                  <label className="property-form-label">Built Year *</label>
                  <input
                    type="number"
                    name="built_year"
                    placeholder="YYYY"
                    value={housingForm.built_year}
                    onChange={handleHousingChange}
                    className="property-form-input"
                    required
                  />
                </div>
              </div>

              <div className="property-form-group">
                <label className="property-form-label">Property Condition *</label>
                <select
                  name="property_condition"
                  value={housingForm.property_condition}
                  onChange={handleHousingChange}
                  className="property-form-select"
                  required
                >
                  <option value="new">New</option>
                  <option value="good">Good</option>
                  <option value="need renovation">Need Renovation</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary property-submit-btn"
              >
                {loading ? (
                  <>
                    <i className="fa-solid fa-spinner fa-spin"></i>
                    <span>{isEditMode ? 'Saving...' : 'Adding...'}</span>
                  </>
                ) : (
                  <span>{isEditMode ? 'Save Changes' : 'Add Property'}</span>
                )}
              </button>
            </form>
          )}

          {/* Rental Form */}
          {activeTab === 'rental' && (
            <form onSubmit={(e) => { e.preventDefault(); handleSubmitRental(); }} className="property-modal-form">
              <div className="property-form-group">
                <label className="property-form-label">Location *</label>
                <input
                  type="text"
                  name="location"
                  placeholder="Property location"
                  value={rentalForm.location}
                  onChange={handleRentalChange}
                  className="property-form-input"
                  required
                />
              </div>

              <div className="property-form-grid-2">
                <div className="property-form-group">
                  <label className="property-form-label">Purchase Price *</label>
                  <input
                    type="number"
                    name="purchase_price"
                    placeholder="LKR"
                    value={rentalForm.purchase_price}
                    onChange={handleRentalChange}
                    step="0.01"
                    className="property-form-input"
                    required
                  />
                </div>

                <div className="property-form-group">
                  <label className="property-form-label">Purchase Date *</label>
                  <input
                    type="date"
                    name="purchase_date"
                    value={rentalForm.purchase_date}
                    onChange={handleRentalChange}
                    className="property-form-input"
                    required
                  />
                </div>
              </div>

              <div className="property-form-group">
                <label className="property-form-label">Monthly Rent *</label>
                <input
                  type="number"
                  name="monthly_rent"
                  placeholder="LKR"
                  value={rentalForm.monthly_rent}
                  onChange={handleRentalChange}
                  step="0.01"
                  className="property-form-input"
                  required
                />
              </div>

              <div className="property-form-group">
                <label className="property-form-label">Occupancy Status *</label>
                <select
                  name="occupancy_status"
                  value={rentalForm.occupancy_status}
                  onChange={handleRentalChange}
                  className="property-form-select"
                  required
                >
                  <option value="occupied">Occupied</option>
                  <option value="vacant">Vacant</option>
                </select>
              </div>

              <div className="property-form-grid-2">
                <div className="property-form-group">
                  <label className="property-form-label">Lease Start Date *</label>
                  <input
                    type="date"
                    name="lease_start_date"
                    value={rentalForm.lease_start_date}
                    onChange={handleRentalChange}
                    className="property-form-input"
                    required
                  />
                </div>

                <div className="property-form-group">
                  <label className="property-form-label">Lease End Date *</label>
                  <input
                    type="date"
                    name="lease_end_date"
                    value={rentalForm.lease_end_date}
                    onChange={handleRentalChange}
                    className="property-form-input"
                    required
                  />
                </div>
              </div>

              <div className="property-form-group">
                <label className="property-form-label">Tenant Type *</label>
                <select
                  name="tenant_type"
                  value={rentalForm.tenant_type}
                  onChange={handleRentalChange}
                  className="property-form-select"
                  required
                >
                  <option value="family">Family</option>
                  <option value="office">Office</option>
                  <option value="commercial">Commercial</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary property-submit-btn"
              >
                {loading ? (
                  <>
                    <i className="fa-solid fa-spinner fa-spin"></i>
                    <span>{isEditMode ? 'Saving...' : 'Adding...'}</span>
                  </>
                ) : (
                  <span>{isEditMode ? 'Save Changes' : 'Add Property'}</span>
                )}
              </button>
            </form>
          )}

          {/* Land Form */}
          {activeTab === 'land' && (
            <form onSubmit={(e) => { e.preventDefault(); handleSubmitLand(); }} className="property-modal-form">
              <div className="property-form-group">
                <label className="property-form-label">Location *</label>
                <input
                  type="text"
                  name="location"
                  placeholder="Property location"
                  value={landForm.location}
                  onChange={handleLandChange}
                  className="property-form-input"
                  required
                />
              </div>

              <div className="property-form-grid-2">
                <div className="property-form-group">
                  <label className="property-form-label">Purchase Price *</label>
                  <input
                    type="number"
                    name="purchase_price"
                    placeholder="LKR"
                    value={landForm.purchase_price}
                    onChange={handleLandChange}
                    step="0.01"
                    className="property-form-input"
                    required
                  />
                </div>

                <div className="property-form-group">
                  <label className="property-form-label">Purchase Date *</label>
                  <input
                    type="date"
                    name="purchase_date"
                    value={landForm.purchase_date}
                    onChange={handleLandChange}
                    className="property-form-input"
                    required
                  />
                </div>
              </div>

              <div className="property-form-group">
                <label className="property-form-label">Land Size (Perches) *</label>
                <input
                  type="number"
                  name="land_size"
                  placeholder="Size in perches"
                  value={landForm.land_size}
                  onChange={handleLandChange}
                  step="0.01"
                  className="property-form-input"
                  required
                />
              </div>

              <div className="property-form-group">
                <label className="property-form-label">Zoning Type *</label>
                <select
                  name="zoning_type"
                  value={landForm.zoning_type}
                  onChange={handleLandChange}
                  className="property-form-select"
                  required
                >
                  <option value="residential">Residential</option>
                  <option value="commercial">Commercial</option>
                  <option value="agricultural">Agricultural</option>
                </select>
              </div>

              <div className="property-form-group">
                <label className="property-form-label">Road Access *</label>
                <input
                  type="text"
                  name="road_access"
                  placeholder="Road access details"
                  value={landForm.road_access}
                  onChange={handleLandChange}
                  className="property-form-input"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary property-submit-btn"
              >
                {loading ? (
                  <>
                    <i className="fa-solid fa-spinner fa-spin"></i>
                    <span>{isEditMode ? 'Saving...' : 'Adding...'}</span>
                  </>
                ) : (
                  <span>{isEditMode ? 'Save Changes' : 'Add Property'}</span>
                )}
              </button>
            </form>
          )}
        </div>
      </div>
    </>
  );
};

export default AddPropertyModal;
