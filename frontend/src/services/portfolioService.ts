import { API_BASE_URL } from "../config/api";

// Type definitions
export interface PropertyData {
  property_id: number;
  created_at: string;
  type: "housing" | "rental" | "land";
  location: string;
  purchase_price: number;
  current_value: number;
  profit: number;
  sentiment: string;
  status: string;
}

export interface PortfolioSummary {
  portfolio_value: number;
  total_investment: number;
  growth_percentage: number;
  total_profit: number;
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
        property_id: prop.property_id,
        created_at: prop.created_at,
        type: prop.type,
        location: prop.location,
        purchase_price: prop.purchase_price,
        current_value: prop.current_value,
        profit: prop.profit,
        sentiment: prop.sentiment,
        status: prop.status,
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
};
