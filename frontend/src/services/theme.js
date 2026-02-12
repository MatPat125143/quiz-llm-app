const safeLocalStorageGet = (key) => {
    try {
        return localStorage.getItem(key);
    } catch {
        return null;
    }
};

const safeLocalStorageSet = (key, value) => {
    try {
        localStorage.setItem(key, value);
        return true;
    } catch {
        return false;
    }
};

const safeDispatchTheme = (theme) => {
    try {
        window.dispatchEvent(new CustomEvent('themechange', {detail: theme}));
        return true;
    } catch {
        return false;
    }
};

export const getStoredTheme = () => safeLocalStorageGet('theme');

export const getSystemTheme = () => {
    if (typeof window === 'undefined' || !window.matchMedia) return 'light';
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

export const getInitialTheme = () => getStoredTheme() || getSystemTheme();

export const applyTheme = (theme) => {
    const root = document.documentElement;
    const isDark = theme === 'dark';
    root.classList.toggle('dark', isDark);
    root.dataset.theme = theme;
    safeLocalStorageSet('theme', theme);
    safeDispatchTheme(theme);
};

export const toggleThemeValue = (theme) => (theme === 'dark' ? 'light' : 'dark');
