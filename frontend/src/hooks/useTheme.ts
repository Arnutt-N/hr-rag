import { useEffect } from 'react';
import { useSettingsStore } from '@/lib/store';

export function useTheme() {
  const { theme, setTheme } = useSettingsStore();

  useEffect(() => {
    const root = document.documentElement;

    const apply = (t: 'light' | 'dark') => {
      if (t === 'dark') root.classList.add('dark');
      else root.classList.remove('dark');
    };

    if (theme === 'system') {
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      apply(mq.matches ? 'dark' : 'light');
      const listener = (e: MediaQueryListEvent) => apply(e.matches ? 'dark' : 'light');
      mq.addEventListener('change', listener);
      return () => mq.removeEventListener('change', listener);
    }

    if (theme) apply(theme);
  }, [theme]);

  return { theme, setTheme };
}
