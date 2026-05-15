import { create } from 'zustand';

export type Locale = 'zh-CN' | 'en-US';
export type ThemeMode = 'light' | 'dark';

function loadFromStorage<T>(key: string, fallback: T): T {
  try {
    const stored = localStorage.getItem(key);
    return stored ? (JSON.parse(stored) as T) : fallback;
  } catch {
    return fallback;
  }
}

function saveToStorage(key: string, value: unknown) {
  localStorage.setItem(key, JSON.stringify(value));
}

interface AppSettings {
  locale: Locale;
  themeMode: ThemeMode;
  setLocale: (locale: Locale) => void;
  setThemeMode: (mode: ThemeMode) => void;
  toggleTheme: () => void;
}

export const useAppSettings = create<AppSettings>((set, get) => ({
  locale: loadFromStorage<Locale>('fintech-locale', 'zh-CN'),
  themeMode: loadFromStorage<ThemeMode>('fintech-theme', 'light'),
  setLocale: (locale) => {
    saveToStorage('fintech-locale', locale);
    set({ locale });
  },
  setThemeMode: (mode) => {
    saveToStorage('fintech-theme', mode);
    set({ themeMode: mode });
  },
  toggleTheme: () => {
    const next = get().themeMode === 'light' ? 'dark' : 'light';
    get().setThemeMode(next);
  },
}));
