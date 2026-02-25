import { API_BASE_URL } from "../config/api";

// Type definitions
export interface Feature {
  id: number;
  name: string;
  label: string;
  data_type: "boolean" | "float" | "int" | "string";
  model_type: "house" | "rental" | "land";
  required: boolean;
  active: boolean;
}

export interface PredictionRequest {
  features: Record<string, any>;
}

export interface PredictionResponse {
  predicted_value: number;
  model_type: string;
}

// Get access token from localStorage or sessionStorage
const getAuthToken = (): string | null => {
  return localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
};

// Helper to make authenticated requests
const fetchWithAuth = async (endpoint: string, options: RequestInit = {}) => {
  const token = getAuthToken();
  
  if (!token) {
    console.warn("No authentication token found - user may not be logged in");
    throw new Error("User not authenticated. Please login to access predictions.");
  }

  const headers = {
    ...options.headers,
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json",
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error: ${response.status} - ${error}`);
    }

    return response.json();
  } catch (err) {
    console.error("Fetch error:", err);
    throw err;
  }
};

// Get features for a specific model type
export const getFeatures = async (modelType: string): Promise<Feature[]> => {
  return fetchWithAuth(`/api/features/${modelType}`);
};

// Make a prediction for a specific model type
export const makePrediction = async (
  modelType: string,
  features: Record<string, any>
): Promise<PredictionResponse> => {
  const payload: PredictionRequest = { features };
  return fetchWithAuth(`/api/predictions/${modelType}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
};
