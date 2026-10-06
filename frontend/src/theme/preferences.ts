export const THEME_STORAGE_KEY = 'travelai.theme'
export const MOTION_STORAGE_KEY = 'travelai.motion'

export const THEME_PREFERENCES = ['system', 'light', 'dark'] as const
export const MOTION_PREFERENCES = ['system', 'reduce', 'full'] as const

export type ThemePreference = (typeof THEME_PREFERENCES)[number]
export type MotionPreference = (typeof MOTION_PREFERENCES)[number]
export type ResolvedTheme = 'light' | 'dark'
export type ResolvedMotion = 'reduce' | 'full'

const isThemePreference = (value: string | null): value is ThemePreference =>
  THEME_PREFERENCES.includes(value as ThemePreference)

const isMotionPreference = (value: string | null): value is MotionPreference =>
  MOTION_PREFERENCES.includes(value as MotionPreference)

export const readStorage = (key: string): string | null => {
  try {
    return window.localStorage.getItem(key)
  } catch {
    return null
  }
}

export const writeStorage = (key: string, value: string): void => {
  try {
    window.localStorage.setItem(key, value)
  } catch {
    // Privacy mode or blocked storage must not break the shell.
  }
}

export const parseThemePreference = (value: string | null | undefined): ThemePreference =>
  isThemePreference(value ?? null) ? value as ThemePreference : 'system'

export const parseMotionPreference = (value: string | null | undefined): MotionPreference =>
  isMotionPreference(value ?? null) ? value as MotionPreference : 'system'

export const getSystemPrefersDark = (): boolean =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches

export const getSystemPrefersReducedMotion = (): boolean =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

export const resolveTheme = (preference: ThemePreference, prefersDark = getSystemPrefersDark()): ResolvedTheme => {
  if (preference === 'light') return 'light'
  if (preference === 'dark') return 'dark'
  return prefersDark ? 'dark' : 'light'
}

export const resolveMotion = (
  preference: MotionPreference,
  prefersReduced = getSystemPrefersReducedMotion()
): ResolvedMotion => {
  if (prefersReduced || preference === 'reduce') return 'reduce'
  return 'full'
}

export const applyDocumentTheme = (theme: ResolvedTheme): void => {
  if (typeof document === 'undefined') return
  document.documentElement.dataset.theme = theme
  document.documentElement.style.colorScheme = theme
}

export const applyDocumentMotion = (motion: ResolvedMotion): void => {
  if (typeof document === 'undefined') return
  document.documentElement.dataset.motion = motion
}
