import { API_BASE_URL } from "../config/api";

// Type definitions
export interface PropertyData {
  property_id: number;
  created_at: string;
  type: "housing" | "rental" | "land";
  location: string;
  purchase_price: number;
  purchase_price_per_perch?: number;
  cost_basis: number;
  current_value: number | null;
  estimated_current_value: number | null;
  profit: number | null;
  unrealized_capital_gain: number | null;
  unrealized_gain_pct: number | null;
  total_return_lkr: number;
  rental_income_to_date?: number;
  rental_months_to_date?: number;
  valuation_as_of: string | null;
  valuation_status: string;
  valuation_method: string;
  valuation_confidence: "high" | "medium" | "low";
  valuation_notes: string[];
  value_range: { lower: number | null; upper: number | null; coverage: string };
  model_anchor: string | null;
  index_factor: number | null;
  sentiment: string;
  status: string;
}

export interface PropertyDetailData {
  property_id: number;
  property_type: "housing" | "rental" | "land";
  created_at: string;
  location: string;
  district?: string;
  locality?: string;
  latitude?: number;
  longitude?: number;
  purchase_price: number;
  purchase_price_per_perch?: number;
  acquisition_costs?: number;
  capital_improvements?: number;
  purchase_date: string;
  status: string;
  land_size_perches?: number;
  house_size_sqft?: number;
  floors?: number;
  built_year?: number;
  property_condition?: string;
  bedrooms?: number;
  bathrooms?: number;
  parking_spaces?: number;
  road_width_ft?: number;
  water_available?: boolean;
  electricity_available?: boolean;
  description?: string;
  monthly_rent?: number;
  occupancy_status?: string;
  lease_start_date?: string;
  lease_end_date?: string;
  tenant_type?: string;
  property_subtype?: string;
  floor_area_sqft?: number;
  furnishing_status?: string;
  vacancy_rate?: number;
  monthly_maintenance?: number;
  monthly_management_fees?: number;
  annual_rates_taxes?: number;
  annual_insurance?: number;
  annual_other_expenses?: number;
  rental_income_to_date?: number;
  rental_months_to_date?: number;
  land_size?: number;
  zoning_type?: string;
  road_access?: string;
  electricity?: boolean;
  water?: boolean;
  clear_deed?: boolean;
  bank_loan?: boolean;
  near_town?: boolean;
  distance_to_town_m?: number;
}

export interface PortfolioSummary {
  portfolio_value: number;
  total_investment: number;
  growth_percentage: number;
  total_profit: number;
  cost_basis: number;
  unrealized_capital_gain: number;
  cumulative_net_rental_income: number;
  total_return_lkr: number;
  property_mix: {
    housing: number;
    rental: number;
    land: number;
  };
  sentiment: string;
}

export interface PortfolioInsight {
  insight: string;
}

// Get access token from localStorage or sessionStorage
const getAuthToken = (): string | null => {
  return localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
};

// Helper to make authenticated requests
const fetchWithAuth = async (endpoint: string, options: RequestInit = {}) => {
  const token = getAuthToken();
  
  if (!token) {
    throw new Error("No authentication token found");
  }

  const headers = {
    ...options.headers,
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json",
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // Token might be expired or invalid
    localStorage.removeItem("access_token");
    sessionStorage.removeItem("access_token");
    throw new Error("Unauthorized - please login again");
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || "API request failed");
  }

  return response.json();
};

export const portfolioService = {
  /**
   * Get portfolio summary (portfolio value, total profit, sentiment, property mix)
   */
  async getSummary(): Promise<PortfolioSummary> {
    return fetchWithAuth("/portfolio/summary");
  },

  /**
   * Get list of user's properties with details
   */
  async getProperties(): Promise<PropertyData[]> {
    const data = await fetchWithAuth("/portfolio/properties");
    // Filter out property_id if it's included in the response
    if (Array.isArray(data)) {
      return data.map((prop: any) => ({
        ...prop,
      }));
    }
    return [];
  },

  /**
   * Get AI-generated insights about the portfolio
   */
  async getInsights(): Promise<PortfolioInsight> {
    return fetchWithAuth("/portfolio/insights");
  },

  async getPropertyDetails(propertyId: number): Promise<PropertyDetailData> {
    return fetchWithAuth(`/properties/${propertyId}`);
  },

  /**
   * Add a new housing property
   */
  async createHousingProperty(data: Record<string, unknown>): Promise<any> {
    return fetchWithAuth("/properties/housing", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Add a new rental property
   */
  async createRentalProperty(data: Record<string, unknown>): Promise<any> {
    return fetchWithAuth("/properties/rental", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Add a new land property
   */
  async createLandProperty(data: Record<string, unknown>): Promise<any> {
    return fetchWithAuth("/properties/land", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateHousingProperty(
    propertyId: number,
    data: Record<string, unknown>
  ): Promise<any> {
    return fetchWithAuth(`/properties/housing/${propertyId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  async updateRentalProperty(
    propertyId: number,
    data: Record<string, unknown>
  ): Promise<any> {
    return fetchWithAuth(`/properties/rental/${propertyId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  async updateLandProperty(
    propertyId: number,
    data: Record<string, unknown>
  ): Promise<any> {
    return fetchWithAuth(`/properties/land/${propertyId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  async deleteProperty(propertyId: number, propertyType: "housing" | "rental" | "land"): Promise<any> {
    return fetchWithAuth(`/properties/${propertyType}/${propertyId}`, {
      method: "DELETE",
    });
  },
};
