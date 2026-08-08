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
  options?: string[] | null;
}

export interface PredictionRequest {
  features: Record<string, any>;
}

export interface PredictionResponse {
  predicted_value: number;
  predicted_sequence: number[];
  model_type: string;
  details?: Record<string, any>;
}

export interface RecommendationResponse {
  model_type: string;
  recommendation: string;
  action_index?: number | null;
}

// Get access token from localStorage or sessionStorage
const getAuthToken = (): string | null => {
  return localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
};

// Helper to make requests (attaches auth token if user is logged in, but allows unauthenticated access)
const fetchWithAuth = async (endpoint: string, options: RequestInit = {}) => {
  const token = getAuthToken();
  
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

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

// Get recommendation for a specific model type
export const getRecommendation = async (
  modelType: string
): Promise<RecommendationResponse> => {
  return fetchWithAuth(`/api/predictions/recommendation/${modelType}`);
};
