import { useState, useEffect } from 'react';

export default function ThemeToggle() {
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('neurasearch-theme') || 'dark';
    }
    return 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('neurasearch-theme', theme);
    
    // Toggle Tailwind dark class for components using dark: prefix
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  const toggle = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  const isDark = theme === 'dark';

  return (
    <button
      onClick={toggle}
      className="relative w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 hover:scale-110 group"
      style={{
        background: isDark
          ? 'linear-gradient(135deg, rgba(139,92,246,0.15), rgba(6,182,212,0.15))'
          : 'linear-gradient(135deg, rgba(251,191,36,0.2), rgba(249,115,22,0.15))',
        border: `1px solid ${isDark ? 'rgba(139,92,246,0.3)' : 'rgba(251,191,36,0.4)'}`,
        boxShadow: isDark
          ? '0 0 15px rgba(139,92,246,0.1)'
          : '0 0 15px rgba(251,191,36,0.15)',
      }}
      title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
    >
      {/* Sun icon */}
      <svg
        className={`absolute w-5 h-5 transition-all duration-500 ${
          isDark ? 'opacity-0 rotate-90 scale-0' : 'opacity-100 rotate-0 scale-100'
        }`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="#f59e0b"
        strokeWidth={2}
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
      </svg>
      {/* Moon icon */}
      <svg
        className={`absolute w-5 h-5 transition-all duration-500 ${
          isDark ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 -rotate-90 scale-0'
        }`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="#8b5cf6"
        strokeWidth={2}
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
      </svg>
    </button>
  );
}
