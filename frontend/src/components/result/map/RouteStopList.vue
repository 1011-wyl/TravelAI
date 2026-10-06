<template>
  <ol class="route-stop-list">
    <li v-for="stop in stops" :key="stop.id">
      <button
        type="button"
        class="route-stop-list__item"
        :class="{ 'is-current': stop.id === selectedId, 'is-unlocated': !stop.locatable }"
        :aria-pressed="stop.id === selectedId"
        @click="emit('select', stop.id)"
      >
        <span class="route-stop-list__index">{{ stop.dayIndex + 1 }}-{{ stop.attrIndex + 1 }}</span>
        <span class="route-stop-list__copy">
          <strong>{{ stop.name }}</strong>
          <span v-if="stop.visit_duration">{{ stop.visit_duration }}{{ t('result.minuteUnit') }}</span>
          <span v-if="stop.address">{{ stop.address }}</span>
          <span v-if="!stop.locatable" class="route-stop-list__warn">{{ t('result.map.unlocated') }}</span>
        </span>
      </button>
    </li>
  </ol>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { MapStop } from '@/composables/useTravelMap'

defineProps<{
  stops: MapStop[]
  selectedId: string | null
}>()

const emit = defineEmits<{
  select: [id: string]
}>()

const { t } = useI18n()
</script>

<style scoped>
.route-stop-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: var(--space-2);
}

.route-stop-list__item {
  display: flex;
  gap: var(--space-3);
  width: 100%;
  min-height: var(--control-h-md);
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.route-stop-list__item:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 75%, transparent);
  outline-offset: 2px;
}

.route-stop-list__item.is-current {
  border-left: 3px solid var(--color-primary);
  background: var(--color-primary-soft);
}

.route-stop-list__index {
  flex: 0 0 auto;
  min-width: 44px;
  font-weight: 700;
}

.route-stop-list__copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.route-stop-list__copy span {
  color: var(--color-text-muted);
  font-size: var(--text-caption);
}

.route-stop-list__warn {
  color: var(--color-warning);
}
</style>
