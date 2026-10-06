import { computed, onMounted, onUnmounted, ref } from 'vue'
import {
  THEME_STORAGE_KEY,
  applyDocumentTheme,
  parseThemePreference,
  readStorage,
  resolveTheme,
  writeStorage,
  type ResolvedTheme,
  type ThemePreference,
} from '@/theme/preferences'

const preference = ref<ThemePreference>(parseThemePreference(null))
const resolvedTheme = ref<ResolvedTheme>('light')
let media: MediaQueryList | null = null
let subscribers = 0
let initialized = false

const syncFromSystem = () => {
  if (preference.value !== 'system') return
  resolvedTheme.value = resolveTheme('system')
  applyDocumentTheme(resolvedTheme.value)
}

const ensureMedia = () => {
  if (typeof window === 'undefined' || media) return
  media = window.matchMedia('(prefers-color-scheme: dark)')
  media.addEventListener('change', syncFromSystem)
}

const releaseMedia = () => {
  if (!media || subscribers > 0) return
  media.removeEventListener('change', syncFromSystem)
  media = null
}

const hydrateTheme = () => {
  if (typeof window === 'undefined') return
  preference.value = parseThemePreference(readStorage(THEME_STORAGE_KEY))
  resolvedTheme.value = resolveTheme(preference.value)
  applyDocumentTheme(resolvedTheme.value)
  initialized = true
}

if (typeof window !== 'undefined') {
  hydrateTheme()
}

export const useTheme = () => {
  if (!initialized && typeof window !== 'undefined') {
    hydrateTheme()
  }

  onMounted(() => {
    subscribers += 1
    ensureMedia()
    hydrateTheme()
  })

  onUnmounted(() => {
    subscribers = Math.max(0, subscribers - 1)
    releaseMedia()
  })

  const setThemePreference = (next: ThemePreference) => {
    preference.value = next
    writeStorage(THEME_STORAGE_KEY, next)
    resolvedTheme.value = resolveTheme(next)
    applyDocumentTheme(resolvedTheme.value)
  }

  return {
    themePreference: preference,
    resolvedTheme,
    isDark: computed(() => resolvedTheme.value === 'dark'),
    setThemePreference,
  }
}
