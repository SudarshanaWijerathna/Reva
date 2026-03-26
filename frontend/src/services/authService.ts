import { API_BASE_URL } from '../config/api';

type AuthStorage = Storage;

const STORAGES: AuthStorage[] = [localStorage, sessionStorage];

export const getAuthStorage = (): AuthStorage | null => {
  if (localStorage.getItem('access_token')) return localStorage;
  if (sessionStorage.getItem('access_token')) return sessionStorage;
  return null;
};

export const getAuthToken = (): string | null => {
  return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
};

export const getStoredUserEmail = (): string | null => {
  return localStorage.getItem('user_email') || sessionStorage.getItem('user_email');
};

export const isStoredAdmin = (): boolean => {
  return localStorage.getItem('is_admin') === 'true' || sessionStorage.getItem('is_admin') === 'true';
};

export const clearAuthStorage = (): void => {
  for (const storage of STORAGES) {
    storage.removeItem('access_token');
    storage.removeItem('token_type');
    storage.removeItem('user_email');
    storage.removeItem('is_admin');
  }
};

export const persistAuthSession = (
  storage: AuthStorage,
  payload: { accessToken: string; tokenType: string; email: string; isAdmin: boolean }
): void => {
  clearAuthStorage();
  storage.setItem('access_token', payload.accessToken);
  storage.setItem('token_type', payload.tokenType);
  storage.setItem('user_email', payload.email);
  storage.setItem('is_admin', String(payload.isAdmin));
};

export const checkAdminAccess = async (token?: string | null): Promise<boolean> => {
  const authToken = token || getAuthToken();
  if (!authToken) return false;

  const response = await fetch(`${API_BASE_URL}/api/admin/stats`, {
    headers: {
      Authorization: `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
  });

  if (response.ok) {
    return true;
  }

  if (response.status === 401 || response.status === 403) {
    return false;
  }

  throw new Error(`Failed to verify admin access (${response.status})`);
};
