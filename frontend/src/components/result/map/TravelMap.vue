<template>
  <div class="travel-map" :aria-label="t('result.map.canvasLabel')">
    <div
      :id="googleContainerId"
      class="travel-map__canvas"
      :class="{ 'is-active': provider === 'google' }"
    ></div>
    <div
      :id="amapContainerId"
      class="travel-map__canvas"
      :class="{ 'is-active': provider === 'amap' }"
    ></div>
    <p v-if="status === 'ready' && provider" class="travel-map__badge">
      {{ provider === 'google' ? t('result.map.providerGoogle') : t('result.map.providerAmap') }}
    </p>
    <slot />
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { TravelMapProvider, TravelMapStatus } from '@/composables/useTravelMap'

withDefaults(
  defineProps<{
    status: TravelMapStatus
    provider: TravelMapProvider | null
    googleContainerId?: string
    amapContainerId?: string
  }>(),
  {
    googleContainerId: 'google-map-container',
    amapContainerId: 'amap-container',
  }
)

const { t } = useI18n()
</script>

<style scoped>
.travel-map {
  position: relative;
  min-height: 360px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-canvas-alt);
}

.travel-map__canvas {
  display: none;
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.travel-map__canvas.is-active {
  display: block;
}

.travel-map__badge {
  position: absolute;
  top: var(--space-2);
  left: var(--space-2);
  z-index: 1;
  margin: 0;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  font-size: var(--text-caption);
  font-weight: 700;
}

@media (min-width: 768px) {
  .travel-map {
    min-height: 480px;
  }
}

@media (min-width: 1024px) {
  .travel-map {
    min-height: 560px;
  }
}
</style>

<style>
.travelai-map-marker {
  position: relative;
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.travelai-map-marker.is-selected {
  outline: 2px solid #147d72;
  outline-offset: 2px;
  border-radius: 50%;
}

.travelai-map-marker__core {
  position: relative;
  z-index: 1;
  width: 20px;
  height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.travelai-map-marker__index {
  position: absolute;
  left: 50%;
  bottom: -14px;
  transform: translateX(-50%);
  font-size: 11px;
  font-weight: 700;
  color: #f6fbff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.7);
}

.travelai-map-tooltip {
  max-width: 240px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(17, 29, 38, 0.96);
  color: #f6fbff;
}

.travelai-map-tooltip__line {
  margin: 0;
  font-size: 13px;
  color: rgba(240, 246, 252, 0.72);
}

.travelai-map-tooltip__line + .travelai-map-tooltip__line {
  margin-top: 2px;
}

.travelai-map-tooltip__line--title {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff !important;
}

#amap-container .amap-info-content {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}

#amap-container .amap-info-sharp {
  display: none !important;
}
</style>
