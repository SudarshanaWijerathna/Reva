import React, { useEffect, useState } from 'react';
import { portfolioService, type PropertyDetailData } from '../services/portfolioService';

type PropertyType = 'housing' | 'rental' | 'land';

interface HousingFormData {
  location: string;
  district: string;
  purchase_price: string;
  acquisition_costs: string;
  capital_improvements: string;
  purchase_date: string;
  land_size_perches: string;
  house_size_sqft: string;
  floors: string;
  built_year: string;
  property_condition: string;
  bedrooms: string;
  bathrooms: string;
}

interface RentalFormData {
  location: string;
  district: string;
  purchase_price: string;
  acquisition_costs: string;
  capital_improvements: string;
  purchase_date: string;
  monthly_rent: string;
  occupancy_status: string;
  lease_start_date: string;
  lease_end_date: string;
  tenant_type: string;
  property_subtype: string;
  bedrooms: string;
  bathrooms: string;
  floor_area_sqft: string;
  land_size_perches: string;
  furnishing_status: string;
  vacancy_rate: string;
  monthly_maintenance: string;
}

interface LandFormData {
  location: string;
  district: string;
  purchase_price: string;
  acquisition_costs: string;
  capital_improvements: string;
  purchase_date: string;
  land_size: string;
  zoning_type: string;
  road_access: string;
  electricity: boolean;
  water: boolean;
  clear_deed: boolean;
  bank_loan: boolean;
  near_town: boolean;
  distance_to_town_m: string;
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
    district: '',
    purchase_price: '',
    acquisition_costs: '',
    capital_improvements: '',
    purchase_date: '',
    land_size_perches: '',
    house_size_sqft: '',
    floors: '',
    built_year: '',
    property_condition: 'good',
    bedrooms: '',
    bathrooms: '',
  });

  const [rentalForm, setRentalForm] = useState<RentalFormData>({
    location: '',
    district: '',
    purchase_price: '',
    acquisition_costs: '',
    capital_improvements: '',
    purchase_date: '',
    monthly_rent: '',
    occupancy_status: 'occupied',
    lease_start_date: '',
    lease_end_date: '',
    tenant_type: 'family',
    property_subtype: 'House',
    bedrooms: '',
    bathrooms: '',
    floor_area_sqft: '',
    land_size_perches: '',
    furnishing_status: 'unknown',
    vacancy_rate: '0',
    monthly_maintenance: '0',
  });

  const [landForm, setLandFormData] = useState<LandFormData>({
    location: '',
    district: '',
    purchase_price: '',
    acquisition_costs: '',
    capital_improvements: '',
    purchase_date: '',
    land_size: '',
    zoning_type: 'residential',
    road_access: '',
    electricity: false,
    water: false,
    clear_deed: false,
    bank_loan: false,
    near_town: false,
    distance_to_town_m: '',
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
        district: initialProperty.district || '',
        purchase_price: initialProperty.property_type === 'land'
          ? initialProperty.purchase_price_per_perch?.toString() || ''
          : initialProperty.purchase_price?.toString() || '',
        acquisition_costs: initialProperty.acquisition_costs?.toString() || '',
        capital_improvements: initialProperty.capital_improvements?.toString() || '',
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
          bedrooms: initialProperty.bedrooms?.toString() || '',
          bathrooms: initialProperty.bathrooms?.toString() || '',
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
          property_subtype: initialProperty.property_subtype || 'House',
          bedrooms: initialProperty.bedrooms?.toString() || '',
          bathrooms: initialProperty.bathrooms?.toString() || '',
          floor_area_sqft: initialProperty.floor_area_sqft?.toString() || '',
          land_size_perches: initialProperty.land_size_perches?.toString() || '',
          furnishing_status: initialProperty.furnishing_status || 'unknown',
          vacancy_rate: initialProperty.vacancy_rate?.toString() || '0',
          monthly_maintenance: initialProperty.monthly_maintenance?.toString() || '0',
        });
      }

      if (initialProperty.property_type === 'land') {
        setLandFormData({
          ...baseValues,
          land_size: initialProperty.land_size?.toString() || '',
          zoning_type: initialProperty.zoning_type || 'residential',
          road_access: initialProperty.road_access || '',
          electricity: initialProperty.electricity ?? false,
          water: initialProperty.water ?? false,
          clear_deed: initialProperty.clear_deed ?? false,
          bank_loan: initialProperty.bank_loan ?? false,
          near_town: initialProperty.near_town ?? false,
          distance_to_town_m: initialProperty.distance_to_town_m?.toString() || '',
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
    const value = e.target instanceof HTMLInputElement && e.target.type === 'checkbox'
      ? e.target.checked
      : e.target.value;
    setLandFormData({ ...landForm, [e.target.name]: value });
  };

  const validateForm = (data: any): boolean => {
    const requiredFields = ['location', 'district', 'purchase_price', 'purchase_date'];
    
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

    const requiredHousingFields = ['land_size_perches', 'house_size_sqft', 'floors', 'built_year', 'bedrooms', 'bathrooms'];
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
        district: housingForm.district,
        purchase_price: parseFloat(housingForm.purchase_price),
        acquisition_costs: parseFloat(housingForm.acquisition_costs) || 0,
        capital_improvements: parseFloat(housingForm.capital_improvements) || 0,
        purchase_date: housingForm.purchase_date,
        land_size_perches: parseFloat(housingForm.land_size_perches),
        house_size_sqft: parseFloat(housingForm.house_size_sqft),
        floors: parseInt(housingForm.floors),
        built_year: parseInt(housingForm.built_year),
        property_condition: housingForm.property_condition,
        bedrooms: parseInt(housingForm.bedrooms),
        bathrooms: parseInt(housingForm.bathrooms),
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

    const requiredRentalFields = ['monthly_rent', 'lease_start_date', 'lease_end_date', 'property_subtype', 'bedrooms', 'bathrooms', 'floor_area_sqft', 'land_size_perches'];
    for (const field of requiredRentalFields) {
      if (!rentalForm[field as keyof RentalFormData]) {
        setError(`${field.replace(/_/g, ' ')} is required`);
        return;
      }
    }
    if (rentalForm.lease_end_date < rentalForm.lease_start_date) {
      setError('Lease end/change date cannot be before the lease start date');
      return;
    }

    setLoading(true);

    try {
      const payload = {
        location: rentalForm.location,
        district: rentalForm.district,
        purchase_price: parseFloat(rentalForm.purchase_price),
        acquisition_costs: parseFloat(rentalForm.acquisition_costs) || 0,
        capital_improvements: parseFloat(rentalForm.capital_improvements) || 0,
        purchase_date: rentalForm.purchase_date,
        monthly_rent: parseFloat(rentalForm.monthly_rent),
        occupancy_status: rentalForm.occupancy_status,
        lease_start_date: rentalForm.lease_start_date,
        lease_end_date: rentalForm.lease_end_date,
        tenant_type: rentalForm.tenant_type,
        property_subtype: rentalForm.property_subtype,
        bedrooms: parseInt(rentalForm.bedrooms),
        bathrooms: parseInt(rentalForm.bathrooms),
        floor_area_sqft: parseFloat(rentalForm.floor_area_sqft),
        land_size_perches: parseFloat(rentalForm.land_size_perches),
        furnishing_status: rentalForm.furnishing_status,
        vacancy_rate: parseFloat(rentalForm.vacancy_rate) || 0,
        monthly_maintenance: parseFloat(rentalForm.monthly_maintenance) || 0,
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
        district: landForm.district,
        purchase_price: parseFloat(landForm.purchase_price),
        acquisition_costs: parseFloat(landForm.acquisition_costs) || 0,
        capital_improvements: parseFloat(landForm.capital_improvements) || 0,
        purchase_date: landForm.purchase_date,
        land_size: parseFloat(landForm.land_size),
        zoning_type: landForm.zoning_type,
        road_access: landForm.road_access,
        electricity: landForm.electricity,
        water: landForm.water,
        clear_deed: landForm.clear_deed,
        bank_loan: landForm.bank_loan,
        near_town: landForm.near_town,
        distance_to_town_m: parseFloat(landForm.distance_to_town_m) || null,
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
      district: '',
      purchase_price: '',
      acquisition_costs: '',
      capital_improvements: '',
      purchase_date: '',
      land_size_perches: '',
      house_size_sqft: '',
      floors: '',
      built_year: '',
      property_condition: 'good',
      bedrooms: '',
      bathrooms: '',
    });
    setRentalForm({
      location: '',
      district: '',
      purchase_price: '',
      acquisition_costs: '',
      capital_improvements: '',
      purchase_date: '',
      monthly_rent: '',
      occupancy_status: 'occupied',
      lease_start_date: '',
      lease_end_date: '',
      tenant_type: 'family',
      property_subtype: 'House',
      bedrooms: '',
      bathrooms: '',
      floor_area_sqft: '',
      land_size_perches: '',
      furnishing_status: 'unknown',
      vacancy_rate: '0',
      monthly_maintenance: '0',
    });
    setLandFormData({
      location: '',
      district: '',
      purchase_price: '',
      acquisition_costs: '',
      capital_improvements: '',
      purchase_date: '',
      land_size: '',
      zoning_type: 'residential',
      road_access: '',
      electricity: false,
      water: false,
      clear_deed: false,
      bank_loan: false,
      near_town: false,
      distance_to_town_m: '',
    });
    setError("");
    setSuccess("");
  };

  const valuationInputStyle: React.CSSProperties = {
    width: '100%', padding: '8px 12px', border: '1px solid #ddd',
    borderRadius: '6px', fontSize: '14px', boxSizing: 'border-box',
  };
  const valuationLabelStyle: React.CSSProperties = {
    display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333',
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
          <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '600' }}>{isEditMode ? 'Edit Property' : 'Add New Property'}</h2>
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
              disabled={isEditMode && initialProperty?.property_type !== tab}
              style={{
                padding: '12px 16px',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500',
                color: activeTab === tab ? '#2563eb' : '#666',
                opacity: isEditMode && initialProperty?.property_type !== tab ? 0.5 : 1,
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
            <form onSubmit={(e) => { e.preventDefault(); handleSubmitHousing(); }}>
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

                <div>
                  <label style={valuationLabelStyle}>District *</label>
                  <input type="text" name="district" placeholder="e.g. Colombo, Gampaha, Kalutara"
                    value={housingForm.district} onChange={handleHousingChange} style={valuationInputStyle} />
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
                    <label style={valuationLabelStyle}>Acquisition Costs</label>
                    <input type="number" name="acquisition_costs" placeholder="Legal, stamp and registration costs"
                      value={housingForm.acquisition_costs} onChange={handleHousingChange} style={valuationInputStyle} />
                  </div>
                  <div>
                    <label style={valuationLabelStyle}>Capital Improvements</label>
                    <input type="number" name="capital_improvements" placeholder="Major improvements"
                      value={housingForm.capital_improvements} onChange={handleHousingChange} style={valuationInputStyle} />
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

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={valuationLabelStyle}>Bedrooms *</label>
                    <input type="number" name="bedrooms" min="0" value={housingForm.bedrooms}
                      onChange={handleHousingChange} style={valuationInputStyle} />
                  </div>
                  <div>
                    <label style={valuationLabelStyle}>Bathrooms *</label>
                    <input type="number" name="bathrooms" min="0" value={housingForm.bathrooms}
                      onChange={handleHousingChange} style={valuationInputStyle} />
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
                  {loading ? <><i className="fa-solid fa-spinner fa-spin" style={{ marginRight: '6px' }}></i>{isEditMode ? 'Saving...' : 'Adding...'}</> : (isEditMode ? 'Save Changes' : 'Add Property')}
                </button>
              </div>
            </form>
          )}

          {/* Rental Form */}
          {activeTab === 'rental' && (
            <form onSubmit={(e) => { e.preventDefault(); handleSubmitRental(); }}>
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

                <div>
                  <label style={valuationLabelStyle}>District *</label>
                  <input type="text" name="district" placeholder="e.g. Colombo, Gampaha, Kalutara"
                    value={rentalForm.district} onChange={handleRentalChange} style={valuationInputStyle} />
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

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={valuationLabelStyle}>Acquisition Costs</label>
                    <input type="number" name="acquisition_costs" value={rentalForm.acquisition_costs}
                      onChange={handleRentalChange} style={valuationInputStyle} />
                  </div>
                  <div>
                    <label style={valuationLabelStyle}>Capital Improvements</label>
                    <input type="number" name="capital_improvements" value={rentalForm.capital_improvements}
                      onChange={handleRentalChange} style={valuationInputStyle} />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={valuationLabelStyle}>Property Type *</label>
                    <select name="property_subtype" value={rentalForm.property_subtype}
                      onChange={handleRentalChange} style={valuationInputStyle}>
                      <option value="House">House</option><option value="Apartment">Apartment</option>
                      <option value="Annex">Annex</option><option value="Office space">Office space</option>
                    </select>
                  </div>
                  <div>
                    <label style={valuationLabelStyle}>Furnishing</label>
                    <select name="furnishing_status" value={rentalForm.furnishing_status}
                      onChange={handleRentalChange} style={valuationInputStyle}>
                      <option value="unknown">Unknown</option><option value="furnished">Furnished</option>
                      <option value="semi-furnished">Semi-furnished</option><option value="unfurnished">Unfurnished</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div><label style={valuationLabelStyle}>Bedrooms *</label>
                    <input type="number" name="bedrooms" min="0" value={rentalForm.bedrooms} onChange={handleRentalChange} style={valuationInputStyle} /></div>
                  <div><label style={valuationLabelStyle}>Bathrooms *</label>
                    <input type="number" name="bathrooms" min="0" value={rentalForm.bathrooms} onChange={handleRentalChange} style={valuationInputStyle} /></div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div><label style={valuationLabelStyle}>Floor Area (sqft) *</label>
                    <input type="number" name="floor_area_sqft" value={rentalForm.floor_area_sqft} onChange={handleRentalChange} style={valuationInputStyle} /></div>
                  <div><label style={valuationLabelStyle}>Land Size (perches) *</label>
                    <input type="number" name="land_size_perches" value={rentalForm.land_size_perches} onChange={handleRentalChange} style={valuationInputStyle} /></div>
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

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div><label style={valuationLabelStyle}>Expected Vacancy Rate</label>
                    <input type="number" name="vacancy_rate" min="0" max="1" step="0.01" value={rentalForm.vacancy_rate} onChange={handleRentalChange} style={valuationInputStyle} /></div>
                  <div><label style={valuationLabelStyle}>Monthly Maintenance</label>
                    <input type="number" name="monthly_maintenance" min="0" value={rentalForm.monthly_maintenance} onChange={handleRentalChange} style={valuationInputStyle} /></div>
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
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Current Rent Starts *</label>
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
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Rent Change Date *</label>
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
                <small style={{ color: '#6b7280' }}>
                  Rent income is counted by calendar month from the start date through today. When the agreed rent changes, edit this property with the new rent and its new start date; the previous period is retained.
                </small>

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
                  {loading ? <><i className="fa-solid fa-spinner fa-spin" style={{ marginRight: '6px' }}></i>{isEditMode ? 'Saving...' : 'Adding...'}</> : (isEditMode ? 'Save Changes' : 'Add Property')}
                </button>
              </div>
            </form>
          )}

          {/* Land Form */}
          {activeTab === 'land' && (
            <form onSubmit={(e) => { e.preventDefault(); handleSubmitLand(); }}>
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

                <div>
                  <label style={valuationLabelStyle}>District *</label>
                  <input type="text" name="district" placeholder="e.g. Colombo, Gampaha, Kalutara"
                    value={landForm.district} onChange={handleLandChange} style={valuationInputStyle} />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '4px', color: '#333' }}>Price per perch *</label>
                    <input
                      type="number"
                      name="purchase_price"
                      placeholder="LKR / perch"
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
                    <small style={{ display: 'block', marginTop: '4px', color: '#6b7280' }}>
                      Total land cost: {landForm.purchase_price && landForm.land_size
                        ? `LKR ${(parseFloat(landForm.purchase_price) * parseFloat(landForm.land_size)).toLocaleString()}`
                        : 'enter price and land size'}
                    </small>
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

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div><label style={valuationLabelStyle}>Acquisition Costs</label>
                    <input type="number" name="acquisition_costs" value={landForm.acquisition_costs} onChange={handleLandChange} style={valuationInputStyle} /></div>
                  <div><label style={valuationLabelStyle}>Capital Improvements</label>
                    <input type="number" name="capital_improvements" value={landForm.capital_improvements} onChange={handleLandChange} style={valuationInputStyle} /></div>
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

                <div>
                  <label style={valuationLabelStyle}>Known Land Features</label>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
                    {[
                      ['electricity', 'Electricity'], ['water', 'Water'], ['clear_deed', 'Clear deed'],
                      ['bank_loan', 'Bank loan eligible'], ['near_town', 'Near town'],
                    ].map(([name, label]) => (
                      <label key={name} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 13 }}>
                        <input type="checkbox" name={name} checked={Boolean(landForm[name as keyof LandFormData])} onChange={handleLandChange} />
                        {label}
                      </label>
                    ))}
                  </div>
                </div>

                {landForm.near_town && (
                  <div><label style={valuationLabelStyle}>Distance to Town (metres)</label>
                    <input type="number" name="distance_to_town_m" min="0" value={landForm.distance_to_town_m} onChange={handleLandChange} style={valuationInputStyle} /></div>
                )}

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
                  {loading ? <><i className="fa-solid fa-spinner fa-spin" style={{ marginRight: '6px' }}></i>{isEditMode ? 'Saving...' : 'Adding...'}</> : (isEditMode ? 'Save Changes' : 'Add Property')}
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
