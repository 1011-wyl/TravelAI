<template>
  <section class="map-section" aria-labelledby="result-section-heading">
    <div class="map-section__toolbar">
      <AppSegmentedControl
        class="map-section__switch"
        :model-value="mobileView"
        :options="viewOptions"
        :aria-label="t('result.map.viewSwitch')"
        @update:model-value="onViewChange"
      />
    </div>

    <div class="map-section__layout" :class="`is-${mobileView}`">
      <RouteStopList
        class="map-section__list"
        :stops="stops"
        :selected-id="selectedId"
        @select="selectStop"
      />
      <TravelMap class="map-section__map" :status="status" :provider="provider">
        <MapStateOverlay
          :status="status"
          :settings-read-failed="settingsReadFailed"
          :retrying="refreshing"
          @retry="refresh"
          @open-settings="openSettingsDrawer"
        />
      </TravelMap>
    </div>

    <TextRouteFallback :stops="stops" />
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { TripPlan } from '@/types'
import { RUNTIME_SETTINGS_UPDATED_EVENT } from '@/services/api'
import AppSegmentedControl from '@/components/ui/AppSegmentedControl.vue'
import RouteStopList from './RouteStopList.vue'
import TravelMap from './TravelMap.vue'
import MapStateOverlay from './MapStateOverlay.vue'
import TextRouteFallback from './TextRouteFallback.vue'
import {
  collectMapStops,
  openSettingsDrawer,
  useTravelMap,
} from '@/composables/useTravelMap'

const props = defineProps<{
  plan: TripPlan
}>()

const { t, locale } = useI18n()
const selectedId = ref<string | null>(null)
const mobileView = ref<'list' | 'map'>('list')
const localeTag = computed(() => {
  const currentLocale = String(locale.value || 'en').toLowerCase()
  if (currentLocale.startsWith('zh')) return 'zh-CN'
  if (currentLocale.startsWith('ja')) return 'ja-JP'
  return 'en-US'
})

const stops = computed(() => collectMapStops(props.plan))

const viewOptions = computed(() => [
  { value: 'list' as const, label: t('result.map.viewList') },
  { value: 'map' as const, label: t('result.map.viewMap') },
])

const travel = useTravelMap(
  computed(() => props.plan),
  {
    localeTag,
    selectedStopId: selectedId,
    onSelectStop: (id) => {
      selectedId.value = id
    },
  }
)

const {
  status,
  provider,
  settingsReadFailed,
  refreshing,
  initMap,
  refresh,
  invalidate,
  resize,
  focusStop,
  syncSelectedMarker,
  getMapElement,
} = travel

const selectStop = async (id: string) => {
  selectedId.value = id
  syncSelectedMarker(id)
  const stop = stops.value.find((item) => item.id === id)
  if (!stop?.locatable) return
  if (window.matchMedia('(max-width: 1023px)').matches) {
    mobileView.value = 'map'
    await nextTick()
    resize()
  }
  focusStop(id)
}

const onViewChange = async (value: string) => {
  if (value !== 'list' && value !== 'map') return
  mobileView.value = value
  await nextTick()
  resize()
}

const onSettingsUpdated = () => {
  void refresh()
}

watch(selectedId, (id) => {
  syncSelectedMarker(id)
})

onMounted(async () => {
  window.addEventListener(RUNTIME_SETTINGS_UPDATED_EVENT, onSettingsUpdated)
  await initMap()
})

onUnmounted(() => {
  window.removeEventListener(RUNTIME_SETTINGS_UPDATED_EVENT, onSettingsUpdated)
  invalidate()
})

defineExpose({
  refresh,
  invalidate,
  getMapElement,
})
</script>

<style scoped>
.map-section {
  display: grid;
  gap: var(--space-6);
  overflow-x: hidden;
}

.map-section__toolbar {
  display: none;
}

.map-section__layout {
  display: grid;
  gap: var(--space-6);
}

.map-section__list,
.map-section__map {
  min-width: 0;
}

@media (max-width: 1023px) {
  .map-section__toolbar {
    display: block;
  }

  .map-section__layout.is-list .map-section__map,
  .map-section__layout.is-map .map-section__list {
    display: none;
  }
}

@media (min-width: 1024px) {
  .map-section__layout {
    grid-template-columns: 4fr 8fr;
    align-items: start;
  }
}
</style>
