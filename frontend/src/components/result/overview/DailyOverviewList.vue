<template>
  <section class="daily-overview" aria-labelledby="daily-overview-title">
    <h3 id="daily-overview-title">{{ t('result.overview.dailyTitle') }}</h3>
    <ol class="daily-overview__list">
      <li v-for="(day, index) in days" :key="`${day.date}-${index}`" class="daily-overview__item">
        <button type="button" class="daily-overview__hit" @click="emit('open-day', index)">
          <span class="daily-overview__day">{{ t('common.dayNumber', { day: index + 1 }) }}</span>
          <span class="daily-overview__meta">
            <strong>{{ day.city || planCity }}</strong>
            <span v-if="day.date">{{ day.date }}</span>
          </span>
          <p class="daily-overview__places">{{ placeSummary(day) }}</p>
        </button>
      </li>
    </ol>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { DayPlan } from '@/types'

defineProps<{
  days: DayPlan[]
  planCity: string
}>()

const emit = defineEmits<{
  'open-day': [dayArrayIndex: number]
}>()

const { t } = useI18n()

const placeSummary = (day: DayPlan) => {
  const names = day.attractions.map((item) => item.name).filter(Boolean)
  if (names.length === 0) return day.description || t('common.noData')
  return names.join(t('result.summary.cityJoin'))
}
</script>

<style scoped>
.daily-overview h3 {
  margin: 0 0 var(--space-4);
}

.daily-overview__list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: var(--space-2);
}

.daily-overview__hit {
  display: grid;
  gap: 4px;
  width: 100%;
  min-height: var(--control-h-md);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: inherit;
  text-align: left;
  font: inherit;
  cursor: pointer;
}

.daily-overview__hit:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 75%, transparent);
}

.daily-overview__day,
.daily-overview__places {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--text-body-s);
}

.daily-overview__meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
</style>
