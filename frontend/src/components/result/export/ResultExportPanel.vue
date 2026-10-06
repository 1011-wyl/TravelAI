<template>
  <ExportDialog
    :open="dialogOpen"
    :phase="phase"
    :include-map="includeMap"
    :error-text="errorText"
    :filename="filename"
    :reduce-motion="reduceMotion"
    @update:include-map="includeMap = $event"
    @confirm="confirm"
    @cancel="cancel"
    @retry="retry"
    @retry-map="retryMap"
    @continue-without-map="continueWithoutMap"
  />

  <div class="trip-export-host" aria-hidden="true">
    <TripExportDocument
      v-if="snapshot"
      ref="exportDocRef"
      :plan="snapshot"
      :photos="snapshotPhotos"
      :map-data-url="mapDataUrl"
    />
    <ExportMapHost
      v-if="useOffscreenMap && snapshot"
      ref="exportMapRef"
      :plan="snapshot"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, toRef, type Ref } from 'vue'
import type { Attraction, TripPlan } from '@/types'
import ExportDialog from '@/components/result/export/ExportDialog.vue'
import TripExportDocument from '@/components/result/export/TripExportDocument.vue'
import ExportMapHost from '@/components/result/export/ExportMapHost.vue'
import { useTripExport } from '@/composables/useTripExport'

const props = defineProps<{
  plan: TripPlan | null
  photos: Record<string, string>
  planKey: string
  reduceMotion: boolean
  resolvePhoto: (attraction: Attraction) => string
  getVisibleMapElement: () => HTMLElement | null
}>()

const exportDocRef = ref<{ rootEl: HTMLElement | null } | null>(null)
const exportMapRef = ref<{
  getStatus: () => string
  getMapElement: () => HTMLElement | null
  refresh: () => Promise<void>
} | null>(null)

const {
  dialogOpen,
  phase,
  includeMap,
  errorText,
  filename,
  snapshot,
  snapshotPhotos,
  mapDataUrl,
  useOffscreenMap,
  exporting,
  openDialog,
  confirm,
  retry,
  retryMap,
  continueWithoutMap,
  cancel,
} = useTripExport({
  plan: toRef(props, 'plan') as Ref<TripPlan | null>,
  photos: toRef(props, 'photos') as Ref<Record<string, string>>,
  planKey: toRef(props, 'planKey') as Ref<string>,
  resolvePhoto: (attraction) => props.resolvePhoto(attraction),
  getVisibleMapElement: () => props.getVisibleMapElement(),
  getDocumentEl: () => exportDocRef.value?.rootEl || null,
  getMapHost: () => exportMapRef.value,
})

defineExpose({
  get exporting() {
    return exporting.value
  },
  openDialog,
})
</script>
