<template>
  <nav class="result-section-nav" :aria-label="t('result.nav.label')">
    <button
      v-for="item in items"
      :key="item.key"
      type="button"
      class="result-section-nav__item"
      :class="{ 'is-current': item.key === modelValue }"
      :aria-current="item.key === modelValue ? 'page' : undefined"
      @click="emit('update:modelValue', item.key)"
    >
      {{ t(item.labelKey) }}
    </button>
  </nav>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { ResultPublicSection } from '@/composables/resultSection'

const items: Array<{ key: ResultPublicSection; labelKey: string }> = [
  { key: 'overview', labelKey: 'result.side.overview' },
  { key: 'budget', labelKey: 'result.side.budget' },
  { key: 'map', labelKey: 'result.side.map' },
  { key: 'itinerary', labelKey: 'result.side.days' },
  { key: 'graph', labelKey: 'result.side.graph' },
  { key: 'weather', labelKey: 'result.side.weather' },
]

defineProps<{
  modelValue: ResultPublicSection
}>()

const emit = defineEmits<{
  'update:modelValue': [value: ResultPublicSection]
}>()

const { t } = useI18n()
</script>

<style scoped>
.result-section-nav {
  display: flex;
  gap: var(--space-2);
  min-width: 0;
  overflow-x: auto;
  overscroll-behavior-x: contain;
  padding-bottom: var(--space-2);
  position: sticky;
  top: var(--header-h);
  z-index: 5;
  background: var(--color-canvas);
}

.result-section-nav__item {
  flex: 0 0 auto;
  min-height: var(--control-h-md);
  padding: 0 var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  background: var(--color-surface);
  color: var(--color-text-muted);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.result-section-nav__item.is-current {
  color: var(--color-text);
  border-color: var(--color-primary);
  border-width: 2px;
  background: var(--color-primary-soft);
}

.result-section-nav__item:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 75%, transparent);
  outline-offset: 2px;
}

@media (min-width: 1024px) {
  .result-section-nav {
    overflow: visible;
  }
}
</style>
