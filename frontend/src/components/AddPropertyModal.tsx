import React, { useState } from 'react';
import { portfolioService } from '../services/portfolioService';

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
}

const AddPropertyModal: React.FC<AddPropertyModalProps> = ({ isOpen, onClose, onPropertyAdded }) => {
  const [activeTab, setActiveTab] = useState<PropertyType>('housing');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [success, setSuccess] = useState<string>("");

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

  const handleAddHousing = async () => {
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

      await portfolioService.createHousingProperty(payload);
      setSuccess('Housing property added successfully!');
      
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

  const handleAddRental = async () => {
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

      await portfolioService.createRentalProperty(payload);
      setSuccess('Rental property added successfully!');
      
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

  const handleAddLand = async () => {
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

      await portfolioService.createLandProperty(payload);
      setSuccess('Land property added successfully!');
      
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
      <div 
        className="modal-overlay"
        onClick={onClose}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          backdropFilter: 'blur(4px)',
          zIndex: 1000,
        }}
      />

      {/* Modal */}
      <div
        className="property-modal"
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          backgroundColor: '#fff',
          borderRadius: '12px',
          boxShadow: '0 10px 40px rgba(0, 0, 0, 0.2)',
          zIndex: 1001,
          maxWidth: '500px',
          width: '90%',
          maxHeight: '85vh',
          overflow: 'auto',
        }}
      >
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '20px',
          borderBottom: '1px solid #e8e8e8',
          position: 'sticky',
          top: 0,
          backgroundColor: '#fff',
        }}>
          <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '600' }}>Add New Property</h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: '#666',
            }}
          >
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div style={{
          display: 'flex',
          borderBottom: '1px solid #e8e8e8',
          padding: '0 20px',
          gap: '10px',
        }}>
          {(['housing', 'rental', 'land'] as PropertyType[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '12px 16px',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500',
                color: activeTab === tab ? '#2563eb' : '#666',
                borderBottom: activeTab === tab ? '2px solid #2563eb' : 'none',
                borderRadius: '0',
                transition: 'all 0.3s ease',
              }}
            >
              <i className={`fa-solid ${
                tab === 'housing' ? 'fa-house' :
                tab === 'rental' ? 'fa-building' :
                'fa-tree'
              }`} style={{ marginRight: '6px' }}></i>
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Content */}
        <div style={{ padding: '24px' }}>
          {/* Error Message */}
          {error && (
            <div style={{
              padding: '12px 16px',
              backgroundColor: '#fce8e6',
              color: '#d93025',
              borderRadius: '8px',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
            }}>
              <i className="fa-solid fa-exclamation-circle"></i>
              <span>{error}</span>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div style={{
              padding: '12px 16px',
              backgroundColor: '#e8f5e9',
              color: '#1b5e20',
              borderRadius: '8px',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
            }}>
              <i className="fa-solid fa-check-circle"></i>
              <span>{success}</span>
            </div>
          )}

          {/* Housing Form */}
          {activeTab === 'housing' && (
            <form onSubmit={(e) => { e.preventDefault(); handleAddHousing(); }}>
              <div style={{ display: 'grid', gap: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Location *</label>
                  <input
                    type="text"
                    name="location"
                    placeholder="Property location"
                    value={housingForm.location}
                    onChange={handleHousingChange}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #ddd',
                      borderRadius: '6px',
                      fontSize: '14px',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Purchase Price *</label>
                    <input
                      type="number"
                      name="purchase_price"
                      placeholder="LKR"
                      value={housingForm.purchase_price}
                      onChange={handleHousingChange}
                      step="0.01"
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #ddd',
                        borderRadius: '6px',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Purchase Date *</label>
                    <input
                      type="date"
                      name="purchase_date"
                      value={housingForm.purchase_date}
                      onChange={handleHousingChange}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #ddd',
                        borderRadius: '6px',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Land Size (Perches) *</label>
                    <input
                      type="number"
                      name="land_size_perches"
                      placeholder="Perches"
                      value={housingForm.land_size_perches}
                      onChange={handleHousingChange}
                      step="0.01"
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #ddd',
                        borderRadius: '6px',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>House Size (Sqft) *</label>
                    <input
                      type="number"
                      name="house_size_sqft"
                      placeholder="Sqft"
                      value={housingForm.house_size_sqft}
                      onChange={handleHousingChange}
                      step="0.01"
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #ddd',
                        borderRadius: '6px',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Floors *</label>
                    <input
                      type="number"
                      name="floors"
                      placeholder="Number of floors"
                      value={housingForm.floors}
                      onChange={handleHousingChange}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #ddd',
                        borderRadius: '6px',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Built Year *</label>
                    <input
                      type="number"
                      name="built_year"
                      placeholder="YYYY"
                      value={housingForm.built_year}
                      onChange={handleHousingChange}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #ddd',
                        borderRadius: '6px',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Property Condition *</label>
                  <select
                    name="property_condition"
                    value={housingForm.property_condition}
                    onChange={handleHousingChange}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #ddd',
                      borderRadius: '6px',
                      fontSize: '14px',
                      boxSizing: 'border-box',
                    }}
                  >
                    <option value="new">New</option>
                    <option value="good">Good</option>
                    <option value="need renovation">Need Renovation</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    padding: '10px 16px',
                    backgroundColor: '#2563eb',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '500',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    opacity: loading ? 0.7 : 1,
                    marginTop: '8px',
                  }}
                >
                  {loading ? <><i className="fa-solid fa-spinner fa-spin" style={{ marginRight: '6px' }}></i>Adding...</> : 'Add Property'}
                </button>
              </div>
            </form>
          )}

          {/* Rental Form */}
          {activeTab === 'rental' && (
            <form onSubmit={(e) => { e.preventDefault(); handleAddRental(); }}>
              <div style={{ display: 'grid', gap: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Location *</label>
                  <input
                    type="text"
                    name="location"
                    placeholder="Property location"
                    value={rentalForm.location}
                    onChange={handleRentalChange}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #ddd',
                      borderRadius: '6px',
                      fontSize: '14px',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Purchase Price *</label>
                    <input
                      type="number"
                      name="purchase_price"
                      placeholder="LKR"
                      value={rentalForm.purchase_price}
                      onChange={handleRentalChange}
                      step="0.01"
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #ddd',
                        borderRadius: '6px',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Purchase Date *</label>
                    <input
                      type="date"
                      name="purchase_date"
                      value={rentalForm.purchase_date}
                      onChange={handleRentalChange}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #ddd',
                        borderRadius: '6px',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Monthly Rent *</label>
                  <input
                    type="number"
                    name="monthly_rent"
                    placeholder="LKR"
                    value={rentalForm.monthly_rent}
                    onChange={handleRentalChange}
                    step="0.01"
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #ddd',
                      borderRadius: '6px',
                      fontSize: '14px',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Occupancy Status *</label>
                  <select
                    name="occupancy_status"
                    value={rentalForm.occupancy_status}
                    onChange={handleRentalChange}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #ddd',
                      borderRadius: '6px',
                      fontSize: '14px',
                      boxSizing: 'border-box',
                    }}
                  >
                    <option value="occupied">Occupied</option>
                    <option value="vacant">Vacant</option>
                  </select>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Lease Start Date *</label>
                    <input
                      type="date"
                      name="lease_start_date"
                      value={rentalForm.lease_start_date}
                      onChange={handleRentalChange}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #ddd',
                        borderRadius: '6px',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Lease End Date *</label>
                    <input
                      type="date"
                      name="lease_end_date"
                      value={rentalForm.lease_end_date}
                      onChange={handleRentalChange}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #ddd',
                        borderRadius: '6px',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Tenant Type *</label>
                  <select
                    name="tenant_type"
                    value={rentalForm.tenant_type}
                    onChange={handleRentalChange}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #ddd',
                      borderRadius: '6px',
                      fontSize: '14px',
                      boxSizing: 'border-box',
                    }}
                  >
                    <option value="family">Family</option>
                    <option value="office">Office</option>
                    <option value="commercial">Commercial</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    padding: '10px 16px',
                    backgroundColor: '#2563eb',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '500',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    opacity: loading ? 0.7 : 1,
                    marginTop: '8px',
                  }}
                >
                  {loading ? <><i className="fa-solid fa-spinner fa-spin" style={{ marginRight: '6px' }}></i>Adding...</> : 'Add Property'}
                </button>
              </div>
            </form>
          )}

          {/* Land Form */}
          {activeTab === 'land' && (
            <form onSubmit={(e) => { e.preventDefault(); handleAddLand(); }}>
              <div style={{ display: 'grid', gap: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Location *</label>
                  <input
                    type="text"
                    name="location"
                    placeholder="Property location"
                    value={landForm.location}
                    onChange={handleLandChange}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #ddd',
                      borderRadius: '6px',
                      fontSize: '14px',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Purchase Price *</label>
                    <input
                      type="number"
                      name="purchase_price"
                      placeholder="LKR"
                      value={landForm.purchase_price}
                      onChange={handleLandChange}
                      step="0.01"
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #ddd',
                        borderRadius: '6px',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Purchase Date *</label>
                    <input
                      type="date"
                      name="purchase_date"
                      value={landForm.purchase_date}
                      onChange={handleLandChange}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #ddd',
                        borderRadius: '6px',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Land Size *</label>
                  <input
                    type="number"
                    name="land_size"
                    placeholder="Size"
                    value={landForm.land_size}
                    onChange={handleLandChange}
                    step="0.01"
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #ddd',
                      borderRadius: '6px',
                      fontSize: '14px',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Zoning Type *</label>
                  <select
                    name="zoning_type"
                    value={landForm.zoning_type}
                    onChange={handleLandChange}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #ddd',
                      borderRadius: '6px',
                      fontSize: '14px',
                      boxSizing: 'border-box',
                    }}
                  >
                    <option value="residential">Residential</option>
                    <option value="commercial">Commercial</option>
                    <option value="agricultural">Agricultural</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Road Access *</label>
                  <input
                    type="text"
                    name="road_access"
                    placeholder="Road access details"
                    value={landForm.road_access}
                    onChange={handleLandChange}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #ddd',
                      borderRadius: '6px',
                      fontSize: '14px',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    padding: '10px 16px',
                    backgroundColor: '#2563eb',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '500',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    opacity: loading ? 0.7 : 1,
                    marginTop: '8px',
                  }}
                >
                  {loading ? <><i className="fa-solid fa-spinner fa-spin" style={{ marginRight: '6px' }}></i>Adding...</> : 'Add Property'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </>
  );
};

export default AddPropertyModal;
