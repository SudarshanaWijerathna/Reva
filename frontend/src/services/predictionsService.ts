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
  /**
   * The model's native unit, named by `unit`: price per perch for land,
   * total price for house, monthly rent for rental. Use `total_value` for
   * the whole-plot land figure rather than multiplying here.
   */
  predicted_value: number;
  predicted_sequence: number[];
  model_type: string;
  details?: Record<string, any>;

  /** "LKR_per_perch" | "LKR_total" | "LKR_per_month" */
  unit?: string | null;
  /** Whole-plot value for land; null for models already quoting a total. */
  total_value?: number | null;
  /** "high" | "medium" | "low" — model coverage composed with index freshness. */
  confidence?: string | null;
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
const fetchWithAuth = async (endpoint: string, options: RequestInit = {}, retries = 3) => {
  const token = getAuthToken();
  
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Prevent duplicate /api/api/ paths
  let cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  if (API_BASE_URL.endsWith('/api') && cleanEndpoint.startsWith('/api/')) {
    cleanEndpoint = cleanEndpoint.substring(4);
  }
  const targetUrl = `${API_BASE_URL}${cleanEndpoint}`;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetch(targetUrl, {
        ...options,
        headers,
      });

      if (response.status === 502 || response.status === 503 || response.status === 504) {
        if (attempt < retries) {
          // Render free instance is waking up from sleep, wait 3 seconds and retry
          await new Promise((res) => setTimeout(res, 3000));
          continue;
        }
        throw new Error("Server is waking up from sleep mode (Render cold start). Please try again in 5 seconds.");
      }

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`API Error: ${response.status} - ${error}`);
      }

      return await response.json();
    } catch (err) {
      if (attempt < retries && (err instanceof TypeError || (err instanceof Error && (err.message.includes("502") || err.message.includes("Failed to fetch"))))) {
        await new Promise((res) => setTimeout(res, 3000));
        continue;
      }
      console.error("Fetch error:", err);
      throw err;
    }
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

