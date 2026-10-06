import { computed, onMounted, onUnmounted, ref } from 'vue'
import {
  MOTION_STORAGE_KEY,
  applyDocumentMotion,
  parseMotionPreference,
  readStorage,
  resolveMotion,
  writeStorage,
  type MotionPreference,
  type ResolvedMotion,
} from '@/theme/preferences'

const preference = ref<MotionPreference>(parseMotionPreference(null))
const resolvedMotion = ref<ResolvedMotion>('full')
let media: MediaQueryList | null = null
let subscribers = 0
let initialized = false

const syncFromSystem = () => {
  resolvedMotion.value = resolveMotion(preference.value)
  applyDocumentMotion(resolvedMotion.value)
}

const ensureMedia = () => {
  if (typeof window === 'undefined' || media) return
  media = window.matchMedia('(prefers-reduced-motion: reduce)')
  media.addEventListener('change', syncFromSystem)
}

const releaseMedia = () => {
  if (!media || subscribers > 0) return
  media.removeEventListener('change', syncFromSystem)
  media = null
}

const hydrateMotion = () => {
  if (typeof window === 'undefined') return
  preference.value = parseMotionPreference(readStorage(MOTION_STORAGE_KEY))
  resolvedMotion.value = resolveMotion(preference.value)
  applyDocumentMotion(resolvedMotion.value)
  initialized = true
}

if (typeof window !== 'undefined') {
  hydrateMotion()
}

export const useMotionPreference = () => {
  if (!initialized && typeof window !== 'undefined') {
    hydrateMotion()
  }

  onMounted(() => {
    subscribers += 1
    ensureMedia()
    hydrateMotion()
  })

  onUnmounted(() => {
    subscribers = Math.max(0, subscribers - 1)
    releaseMedia()
  })

  const setMotionPreference = (next: MotionPreference) => {
    preference.value = next
    writeStorage(MOTION_STORAGE_KEY, next)
    resolvedMotion.value = resolveMotion(next)
    applyDocumentMotion(resolvedMotion.value)
  }

  return {
    motionPreference: preference,
    resolvedMotion,
    reduceMotion: computed(() => resolvedMotion.value === 'reduce'),
    setMotionPreference,
  }
}
