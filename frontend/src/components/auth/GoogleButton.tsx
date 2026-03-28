import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { API_BASE_URL } from '../../config/api';
import { checkAdminAccess, persistAuthSession } from '../../services/authService';

declare global {
  interface Window {
    google?: {
      accounts?: {
        oauth2?: {
          initTokenClient: (config: GoogleTokenClientConfig) => GoogleTokenClient;
        };
      };
    };
  }
}

interface GoogleTokenResponse {
  access_token?: string;
  error?: string;
}

interface GoogleAuthResponse {
  access_token: string;
  token_type: string;
  email: string;
  full_name?: string | null;
  picture?: string | null;
}

interface GoogleTokenClient {
  requestAccessToken: (overrideConfig?: { prompt?: string }) => void;
}

interface GoogleTokenClientConfig {
  client_id: string;
  scope: string;
  callback: (response: GoogleTokenResponse) => void;
  error_callback?: (error: unknown) => void;
}

let googleIdentityScriptPromise: Promise<void> | null = null;

function loadGoogleIdentityScript() {
  if (window.google?.accounts?.oauth2) {
    return Promise.resolve();
  }

  if (googleIdentityScriptPromise) {
    return googleIdentityScriptPromise;
  }

  googleIdentityScriptPromise = new Promise<void>((resolve, reject) => {
    const existingScript = document.querySelector<HTMLScriptElement>('script[data-google-identity="true"]');

    if (existingScript) {
      existingScript.addEventListener('load', () => resolve(), { once: true });
      existingScript.addEventListener('error', () => reject(new Error('Failed to load Google Identity Services.')), { once: true });
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.dataset.googleIdentity = 'true';
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load Google Identity Services.'));
    document.head.appendChild(script);
  });

  return googleIdentityScriptPromise;
}

export default function GoogleButton({ text }: { text: string }) {
  const { closeAuthModal, redirectPath } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined;

  const handleGoogleLogin = async () => {
    if (isLoading) {
      return;
    }

    if (!googleClientId) {
      setErrorMessage('Google sign-in is not configured yet. Add VITE_GOOGLE_CLIENT_ID to your environment and restart the frontend.');
      return;
    }

    setErrorMessage('');
    setIsLoading(true);

    try {
      await loadGoogleIdentityScript();

      const tokenClient = window.google?.accounts?.oauth2?.initTokenClient({
        client_id: googleClientId,
        scope: 'openid email profile',
        callback: async (tokenResponse) => {
          if (!tokenResponse.access_token) {
            console.error('Google login failed to return an access token.', tokenResponse.error);
            setIsLoading(false);
            return;
          }

          try {
            const res = await fetch(`${API_BASE_URL}/auth/google`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                token: tokenResponse.access_token,
              }),
            });
            const authData = await res.json().catch(() => null) as GoogleAuthResponse | { detail?: string } | null;

            if (!res.ok || !authData || !('access_token' in authData)) {
              throw new Error(authData && 'detail' in authData && authData.detail ? authData.detail : 'Google sign-in failed');
            }

            let isAdmin = false;
            try {
              isAdmin = await checkAdminAccess(authData.access_token);
            } catch (adminErr) {
              console.error("Failed to check admin status:", adminErr);
            }

            persistAuthSession(localStorage, {
              accessToken: authData.access_token,
              tokenType: authData.token_type,
              email: authData.email,
              fullName: authData.full_name,
              pictureUrl: authData.picture,
              isAdmin,
            });

            const pathToGo = redirectPath;
            closeAuthModal();

            if (pathToGo) {
              window.location.href = pathToGo;
            } else {
              window.location.reload();
            }
          } catch (error) {
            const message = error instanceof Error ? error.message : 'Google sign-in failed';
            console.error("Failed to finish Google sign-in", error);
            setErrorMessage(message);
            setIsLoading(false);
          }
        },
        error_callback: (error) => {
          console.error('Google Login Failed', error);
          setErrorMessage('Google sign-in was cancelled or blocked.');
          setIsLoading(false);
        }
      });

      if (!tokenClient) {
        throw new Error('Google token client failed to initialize.');
      }

      tokenClient.requestAccessToken({ prompt: 'consent' });
    } catch (error) {
      console.error('Failed to initialize Google login', error);
      setErrorMessage('Failed to initialize Google sign-in.');
      setIsLoading(false);
    }
  };

  return (
    <>
      <button 
        className="btn-google" 
        type="button"
        onClick={handleGoogleLogin}
        disabled={isLoading}
      >
        <svg width="20" height="20" viewBox="0 0 24 24">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
        </svg>
        {isLoading ? "Connecting..." : text}
      </button>
      {errorMessage ? (
        <p style={{ color: "#d93025", marginTop: 12, marginBottom: 0 }}>{errorMessage}</p>
      ) : null}
    </>
  );
}
