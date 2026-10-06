<template>
  <nav class="day-navigator" :aria-label="t('result.itinerary.navLabel')">
    <ol class="day-navigator__list">
      <li v-for="(day, index) in days" :key="`${day.date}-${index}`">
        <button
          type="button"
          class="day-navigator__item"
          :class="{ 'is-current': index === currentIndex }"
          :aria-current="index === currentIndex ? 'true' : undefined"
          @click="emit('select', index)"
        >
          <span class="day-navigator__mark" aria-hidden="true"></span>
          <span class="day-navigator__copy">
            <strong>{{ t('common.dayNumber', { day: index + 1 }) }}</strong>
            <span v-if="day.date">{{ day.date }}</span>
            <span>{{ day.city || planCity }}</span>
          </span>
          <span v-if="index === currentIndex" class="day-navigator__current">{{ t('result.itinerary.currentDay') }}</span>
        </button>
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { DayPlan } from '@/types'

defineProps<{
  days: DayPlan[]
  planCity: string
  currentIndex: number
}>()

const emit = defineEmits<{
  select: [index: number]
}>()

const { t } = useI18n()
</script>

<style scoped>
.day-navigator__list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  gap: var(--space-2);
  overflow-x: auto;
  overscroll-behavior-x: contain;
}

.day-navigator__item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-height: var(--control-h-md);
  min-width: max-content;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    border-color var(--duration-base) var(--ease-standard),
    background-color var(--duration-base) var(--ease-standard);
}

.day-navigator__item:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 75%, transparent);
  outline-offset: 2px;
}

.day-navigator__mark {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-border-strong);
  flex-shrink: 0;
  transform: translateX(0);
  transition:
    background-color var(--duration-base) var(--ease-standard),
    transform var(--duration-base) var(--ease-standard);
}

.day-navigator__current {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.day-navigator__copy {
  display: grid;
  gap: 2px;
  font-size: var(--text-caption);
  color: var(--color-text-muted);
}

.day-navigator__copy strong {
  color: var(--color-text);
  font-size: var(--text-body-s);
}

.day-navigator__item.is-current {
  border-width: 2px;
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.day-navigator__item.is-current .day-navigator__mark {
  background: var(--color-primary);
  transform: translateX(2px);
}

@media (min-width: 1024px) {
  .day-navigator {
    position: sticky;
    top: calc(var(--header-h) + var(--control-h-md) + var(--space-2));
    align-self: start;
  }

  .day-navigator__list {
    flex-direction: column;
    overflow: visible;
  }

  .day-navigator__item {
    width: 100%;
  }
}
</style>
