<template>
  <div class="trip-export-map-host" aria-hidden="true">
    <TravelMap
      class="trip-export-map-host__canvas"
      :status="status"
      :provider="provider"
      google-container-id="export-google-map-container"
      amap-container-id="export-amap-container"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { TripPlan } from '@/types'
import TravelMap from '@/components/result/map/TravelMap.vue'
import { useTravelMap } from '@/composables/useTravelMap'

const props = defineProps<{
  plan: TripPlan
}>()

const { locale } = useI18n()
const selectedId = ref<string | null>(null)
const localeTag = computed(() => {
  const currentLocale = String(locale.value || 'en').toLowerCase()
  if (currentLocale.startsWith('zh')) return 'zh-CN'
  if (currentLocale.startsWith('ja')) return 'ja-JP'
  return 'en-US'
})

const travel = useTravelMap(
  computed(() => props.plan),
  {
    localeTag,
    selectedStopId: selectedId,
    onSelectStop: (id) => {
      selectedId.value = id
    },
    containerIds: {
      google: 'export-google-map-container',
      amap: 'export-amap-container',
    },
    quiet: true,
  }
)

const { status, provider, initMap, invalidate, getMapElement, refresh } = travel

onMounted(() => {
  void initMap()
})

onUnmounted(() => {
  invalidate()
})

defineExpose({
  getStatus: () => status.value,
  getMapElement,
  refresh,
  invalidate,
})
</script>

<style scoped>
.trip-export-map-host,
.trip-export-map-host__canvas {
  width: 800px;
  height: 420px;
}

.trip-export-map-host__canvas :deep(.travel-map) {
  min-height: 420px;
  height: 420px;
  border: none;
  border-radius: 0;
}
</style>
