import React, { createContext, useContext, useState, useEffect } from 'react';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [settings, setSettings] = useState(() => {
    const saved = localStorage.getItem('kl_settings');
    return saved ? JSON.parse(saved) : {
      language: 'English',
      theme: 'dark',
      model: 'Groq (Fast)'
    };
  });

  useEffect(() => {
    localStorage.setItem('kl_settings', JSON.stringify(settings));
    
    // Apply theme to HTML element for Tailwind dark mode
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(settings.theme);
    
    // Also apply to body for CSS variables
    document.body.className = settings.theme;
  }, [settings]);

  return (
    <AppContext.Provider value={{ settings, setSettings }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);
