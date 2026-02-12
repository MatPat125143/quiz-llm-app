import { useEffect, useState } from 'react';
import { applyTheme, getInitialTheme, toggleThemeValue } from '../services/theme';

export default function useThemeToggle() {
  const [theme, setTheme] = useState(getInitialTheme());

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const toggleTheme = () => setTheme((prev) => toggleThemeValue(prev));

  return {
    theme,
    setTheme,
    toggleTheme,
  };
}
