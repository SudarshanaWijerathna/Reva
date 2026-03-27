import { API_BASE_URL } from '../config/api';

type AuthStorage = Storage;
type UserProfileResponse = {
  full_name?: string;
  email?: string;
};

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

export const getStoredUserFullName = (): string | null => {
  return localStorage.getItem('user_full_name') || sessionStorage.getItem('user_full_name');
};

export const isStoredAdmin = (): boolean => {
  return localStorage.getItem('is_admin') === 'true' || sessionStorage.getItem('is_admin') === 'true';
};

export const formatDisplayNameFromEmail = (email: string): string => {
  const localPart = email.split('@')[0] || 'User';

  return localPart
    .split(/[._-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ') || 'User';
};

export const getStoredDisplayName = (): string | null => {
  const fullName = getStoredUserFullName();
  if (fullName?.trim()) {
    return fullName.trim();
  }

  const email = getStoredUserEmail();
  return email ? formatDisplayNameFromEmail(email) : null;
};

export const clearAuthStorage = (): void => {
  for (const storage of STORAGES) {
    storage.removeItem('access_token');
    storage.removeItem('token_type');
    storage.removeItem('user_email');
    storage.removeItem('user_full_name');
    storage.removeItem('is_admin');
  }
};

export const persistAuthSession = (
  storage: AuthStorage,
  payload: { accessToken: string; tokenType: string; email: string; fullName?: string | null; isAdmin: boolean }
): void => {
  clearAuthStorage();
  storage.setItem('access_token', payload.accessToken);
  storage.setItem('token_type', payload.tokenType);
  storage.setItem('user_email', payload.email);
  if (payload.fullName?.trim()) {
    storage.setItem('user_full_name', payload.fullName.trim());
  }
  storage.setItem('is_admin', String(payload.isAdmin));
};

export const fetchCurrentUserProfile = async (
  token?: string | null
): Promise<UserProfileResponse | null> => {
  const authToken = token || getAuthToken();
  if (!authToken) return null;

  const response = await fetch(`${API_BASE_URL}/users/me`, {
    headers: {
      Authorization: `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
  });

  if (response.ok) {
    return response.json();
  }

  if (response.status === 401 || response.status === 403 || response.status === 404) {
    return null;
  }

  throw new Error(`Failed to load user profile (${response.status})`);
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
