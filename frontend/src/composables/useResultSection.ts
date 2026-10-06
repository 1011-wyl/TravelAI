import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  isCanonicalPublicSection,
  normalizePublicSection,
  pickQueryValue,
  toInternalSection,
  type ResultPublicSection,
} from '@/composables/resultSection'

export const useResultSection = () => {
  const route = useRoute()
  const router = useRouter()
  const { t } = useI18n()

  const rawSectionQuery = computed(() => pickQueryValue(route.query.section))
  const publicSection = computed(() => normalizePublicSection(rawSectionQuery.value))
  const activeSection = computed(() => toInternalSection(publicSection.value))
  const sectionHeading = computed(() => {
    if (publicSection.value === 'itinerary') return t('result.side.days')
    if (publicSection.value === 'graph') return t('result.side.graph')
    return t(`result.side.${publicSection.value}`)
  })

  let focusAfterSectionNav = false

  const writePublicSection = (section: ResultPublicSection, mode: 'push' | 'replace') => {
    if (pickQueryValue(route.query.section) === section) return
    const query = { ...route.query, section }
    if (mode === 'push') {
      void router.push({ query })
      return
    }
    void router.replace({ query })
  }

  const onSelectSection = (section: ResultPublicSection) => {
    focusAfterSectionNav = true
    writePublicSection(section, 'push')
  }

  const itineraryFocusDay = ref<number | null>(null)
  const itineraryFocusNonce = ref(0)

  const requestSection = (section: ResultPublicSection) => {
    focusAfterSectionNav = true
    writePublicSection(section, 'push')
  }

  const goToDayFromOverview = (dayArrayIndex: number) => {
    itineraryFocusDay.value = dayArrayIndex
    itineraryFocusNonce.value += 1
    requestSection('itinerary')
  }

  const openMapFromItinerary = () => {
    requestSection('map')
  }

  watch(
    () => route.query.section,
    (raw) => {
      const current = pickQueryValue(raw)
      if (isCanonicalPublicSection(current)) return
      writePublicSection(normalizePublicSection(current), 'replace')
    },
    { immediate: true }
  )

  const focusSectionHeading = async () => {
    if (!focusAfterSectionNav) return
    focusAfterSectionNav = false
    await nextTick()
    document.getElementById('result-section-heading')?.focus()
  }

  return {
    publicSection,
    activeSection,
    sectionHeading,
    onSelectSection,
    requestSection,
    goToDayFromOverview,
    openMapFromItinerary,
    itineraryFocusDay,
    itineraryFocusNonce,
    focusSectionHeading,
  }
}
