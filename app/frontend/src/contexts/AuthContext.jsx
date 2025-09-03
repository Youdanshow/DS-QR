import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [limits, setLimits] = useState({ used: 0, max: 3, isPremium: false, isFounder: false });
  const [isLoading, setIsLoading] = useState(true);

  // Configure axios to include credentials for cookies
  axios.defaults.withCredentials = true;

  // Check for URL fragment authentication (priority over existing session)
  useEffect(() => {
    const checkUrlAuth = async () => {
      const hash = window.location.hash;
      if (hash && hash.includes('session_id=')) {
        const sessionId = hash.split('session_id=')[1];
        
        try {
          const response = await axios.post(`${API}/auth/session`, { session_id: sessionId });
          setUser(response.data.user);
          setLimits(response.data.limits);
          
          // Clear the hash from URL
          window.location.hash = '';
          
          // Redirect to main page if on profile page
          if (window.location.pathname === '/profile') {
            window.location.href = '/';
            return;
          }
        } catch (error) {
          console.error('Failed to authenticate with session ID:', error);
        }
      }
      
      // If no URL auth, check existing session
      await checkAuth();
    };

    checkUrlAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data.user);
      setLimits(response.data.limits);
    } catch (error) {
      // Not authenticated, get guest limits
      try {
        const response = await axios.get(`${API}/qr/history`);
        setLimits(response.data.limits);
      } catch (err) {
        console.error('Failed to get guest limits', err);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithGoogle = () => {
    // Get current URL for redirect
    const currentUrl = window.location.origin + '/profile';
    const authUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(currentUrl)}`;
    
    // Redirect to Emergent Auth
    window.location.href = authUrl;
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setLimits({ used: 0, max: 3, isPremium: false, isFounder: false });
      
      // Reload to get guest limits
      checkAuth();
    }
  };

  const updateLimits = (newLimits) => {
    setLimits(newLimits);
  };

  const upgradeToPremium = async () => {
    try {
      const response = await axios.post(`${API}/subscription/upgrade`, { planType: 'monthly' });
      setLimits(response.data.limits);
      
      // Update user premium status
      if (user) {
        setUser({ ...user, isPremium: true });
      }
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Upgrade failed' 
      };
    }
  };

  const redeemPromoCode = async (promoCode) => {
    try {
      const response = await axios.post(`${API}/auth/redeem-promo`, { promoCode });
      setLimits(response.data.limits);
      
      // Update user to founder status
      if (user) {
        setUser({ ...user, isPremium: true, isFounder: true });
      }
      
      return { success: true, message: response.data.message };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Redemption failed' 
      };
    }
  };

  const value = {
    user,
    limits,
    isLoading,
    isAuthenticated: !!user,
    loginWithGoogle,
    logout,
    updateLimits,
    upgradeToPremium,
    redeemPromoCode
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};