<template>
  <div v-if="status !== 'ready'" class="map-state-overlay" role="status">
    <h3 class="map-state-overlay__title">{{ title }}</h3>
    <p class="map-state-overlay__body">{{ body }}</p>
    <div class="map-state-overlay__actions">
      <AppButton v-if="status === 'missing-key' || status === 'failed'" variant="secondary" @click="emit('open-settings')">
        {{ t('result.map.openSettings') }}
      </AppButton>
      <AppButton v-if="status === 'failed'" variant="primary" :loading="retrying" @click="emit('retry')">
        {{ t('result.map.retry') }}
      </AppButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import AppButton from '@/components/ui/AppButton.vue'
import type { TravelMapStatus } from '@/composables/useTravelMap'

const props = defineProps<{
  status: TravelMapStatus
  settingsReadFailed?: boolean
  retrying?: boolean
}>()

const emit = defineEmits<{
  retry: []
  'open-settings': []
}>()

const { t } = useI18n()

const title = computed(() => {
  if (props.status === 'checking-key') return t('result.map.checkingTitle')
  if (props.status === 'loading-google') return t('result.map.loadingGoogleTitle')
  if (props.status === 'fallback-amap') return t('result.map.fallbackTitle')
  if (props.status === 'loading-amap') return t('result.map.loadingAmapTitle')
  if (props.status === 'missing-key') return t('result.map.missingTitle')
  return t('result.map.failedTitle')
})

const body = computed(() => {
  if (props.status === 'checking-key') return t('result.map.checkingBody')
  if (props.status === 'loading-google') return t('result.map.loadingGoogleBody')
  if (props.status === 'fallback-amap') return t('result.map.fallbackBody')
  if (props.status === 'loading-amap') return t('result.map.loadingAmapBody')
  if (props.status === 'missing-key') return t('result.map.missingBody')
  if (props.settingsReadFailed) return t('result.map.settingsFailedBody')
  return t('result.map.failedBody')
})
</script>

<style scoped>
.map-state-overlay {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: grid;
  align-content: center;
  justify-items: center;
  gap: var(--space-3);
  padding: var(--space-6);
  background: color-mix(in srgb, var(--color-canvas) 88%, transparent);
  text-align: center;
}

.map-state-overlay__title {
  margin: 0;
  font-size: var(--text-h3);
}

.map-state-overlay__body {
  margin: 0;
  max-width: 42ch;
  color: var(--color-text-muted);
}

.map-state-overlay__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  justify-content: center;
}
</style>
