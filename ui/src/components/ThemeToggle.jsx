import React from 'react';
import { Sun, Moon } from 'lucide-react';

const ThemeToggle = ({ theme, setTheme }) => {
  return (
    <button
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      className="p-2.5 rounded-xl dark:bg-white/5 bg-gray-100 hover:bg-gray-200 dark:hover:bg-white/10 dark:text-gray-500 text-gray-600 dark:hover:text-white hover:text-black transition-all shadow-inner active:scale-90 border dark:border-white/5 border-gray-200"
      title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
    >
      {theme === 'dark' ? (
        <Sun className="w-5 h-5 text-yellow-500" />
      ) : (
        <Moon className="w-5 h-5 text-indigo-600" />
      )}
    </button>
  );
};

export default ThemeToggle;
