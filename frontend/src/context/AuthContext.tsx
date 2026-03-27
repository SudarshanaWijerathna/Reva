import React, { createContext, useState, useContext, ReactNode, useCallback } from 'react';

interface AuthContextType {
  isModalOpen: boolean;
  authMode: 'login' | 'signup';
  redirectPath: string | null; // <-- Remembers where to send the user
  authUpdateKey: number;       // <-- A trigger to force navbars to update
  openAuthModal: (mode?: 'login' | 'signup', redirectPath?: string) => void;
  closeAuthModal: () => void;
  switchAuthMode: (mode: 'login' | 'signup') => void;
  notifyAuthChange: () => void; // <-- The function to pull the trigger
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login');
  const [redirectPath, setRedirectPath] = useState<string | null>(null);
  const [authUpdateKey, setAuthUpdateKey] = useState(0);

  const openAuthModal = (mode: 'login' | 'signup' = 'login', path?: string) => {
    setAuthMode(mode);
    setRedirectPath(path || null);
    setIsModalOpen(true);
    document.body.style.overflow = 'hidden'; 
  };

  const closeAuthModal = () => {
    setIsModalOpen(false);
    setRedirectPath(null); // Clear memory on close
    document.body.style.overflow = 'unset'; 
  };

  const switchAuthMode = (mode: 'login' | 'signup') => {
    setAuthMode(mode);
  };

  const notifyAuthChange = useCallback(() => {
    setAuthUpdateKey(prev => prev + 1); // Shouts to the app that auth changed!
  }, []);

  return (
    <AuthContext.Provider value={{ 
      isModalOpen, authMode, redirectPath, authUpdateKey, 
      openAuthModal, closeAuthModal, switchAuthMode, notifyAuthChange 
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}