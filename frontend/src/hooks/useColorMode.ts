import { useCallback, useState } from 'react';

export type ColorMode = 'light' | 'dark';
const KEY = 'color_mode';

export function readStoredMode(): ColorMode {
  try {
    return localStorage.getItem(KEY) === 'light' ? 'light' : 'dark';
  } catch {
    return 'dark';
  }
}

export function applyMode(mode: ColorMode): void {
  const root = document.documentElement;
  root.classList.remove('light', 'dark');
  root.classList.add(mode);
  root.style.colorScheme = mode;
}

export function useColorMode(): { mode: ColorMode; setMode: (m: ColorMode) => void } {
  const [mode, setModeState] = useState<ColorMode>(readStoredMode);
  const setMode = useCallback((m: ColorMode) => {
    setModeState(m);
    applyMode(m);
    try {
      localStorage.setItem(KEY, m);
    } catch {
      // storage unavailable; preference applies for this session only
    }
  }, []);
  return { mode, setMode };
}
