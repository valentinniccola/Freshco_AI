import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('freshco_token') || null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login', 'register', 'forgot_password'
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const storedToken = localStorage.getItem('freshco_token');
      if (storedToken) {
        try {
          const res = await authAPI.getMe();
          setUser(res.data);
          setToken(storedToken);
        } catch (err) {
          console.warn('Session expired or invalid token');
          localStorage.removeItem('freshco_token');
          localStorage.removeItem('freshco_user');
          setUser(null);
          setToken(null);
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, []);

  const login = async (usernameOrEmail, password) => {
    const res = await authAPI.login({
      username_or_email: usernameOrEmail,
      password,
    });
    const { access_token, user: userData } = res.data;
    localStorage.setItem('freshco_token', access_token);
    localStorage.setItem('freshco_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    setIsAuthModalOpen(false);
    return userData;
  };

  const register = async (username, email, password, phoneNumber = '') => {
    const payload = {
      username,
      email,
      password,
    };
    if (phoneNumber && phoneNumber.trim() !== '') {
      payload.phone_number = phoneNumber.trim();
    }

    const res = await authAPI.register(payload);
    const { access_token, user: userData } = res.data;
    localStorage.setItem('freshco_token', access_token);
    localStorage.setItem('freshco_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    setIsAuthModalOpen(false);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('freshco_token');
    localStorage.removeItem('freshco_user');
    setToken(null);
    setUser(null);
  };

  const openAuth = (mode = 'login') => {
    setAuthMode(mode);
    setIsAuthModalOpen(true);
  };

  const closeAuth = () => {
    setIsAuthModalOpen(false);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAdmin: user?.role === 'admin',
        loading,
        login,
        register,
        logout,
        isAuthModalOpen,
        authMode,
        setAuthMode,
        openAuth,
        closeAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
