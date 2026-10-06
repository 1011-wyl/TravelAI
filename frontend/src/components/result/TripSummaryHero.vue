<template>
  <section class="trip-hero-summary" aria-labelledby="trip-summary-title">
    <div class="trip-hero-summary__copy">
      <p class="trip-hero-summary__kicker">{{ t('result.summary.kicker') }}</p>
      <h1 id="trip-summary-title" class="trip-hero-summary__title">{{ title }}</h1>
      <p v-if="routeLabel" class="trip-hero-summary__route">{{ routeLabel }}</p>
      <dl class="trip-hero-summary__metrics">
        <div v-if="dateLabel">
          <dt>{{ t('result.summary.dates') }}</dt>
          <dd>{{ dateLabel }}</dd>
        </div>
        <div v-if="daysLabel">
          <dt>{{ t('result.summary.days') }}</dt>
          <dd>{{ daysLabel }}</dd>
        </div>
        <div v-if="budgetLabel">
          <dt>{{ t('result.summary.budget') }}</dt>
          <dd>{{ budgetLabel }}</dd>
        </div>
      </dl>
      <div class="trip-hero-summary__desktop-actions">
        <slot name="actions" />
      </div>
    </div>
    <div class="trip-hero-summary__map" aria-hidden="true"></div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { TripPlan } from '@/types'

const props = defineProps<{
  plan: TripPlan
}>()

const { t } = useI18n()

const title = computed(() => props.plan.city || t('result.summary.untitled'))
const routeLabel = computed(() => {
  const cities = props.plan.cities?.filter(Boolean) || []
  if (cities.length <= 1) return ''
  return cities.join(t('result.summary.cityJoin'))
})
const dateLabel = computed(() => {
  if (!props.plan.start_date || !props.plan.end_date) return ''
  return t('result.dateRange', { start: props.plan.start_date, end: props.plan.end_date })
})
const daysLabel = computed(() => {
  const count = props.plan.days?.length
  if (!count) return ''
  return t('common.dayCount', { count })
})
const budgetLabel = computed(() => {
  const total = props.plan.budget?.total
  if (!Number.isFinite(Number(total)) || Number(total) <= 0) return ''
  return `¥${Number(total)}`
})
</script>

<style scoped>
.trip-hero-summary {
  display: grid;
  gap: var(--space-6);
  padding: var(--space-6);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-organic);
  background: var(--color-surface);
  overflow: hidden;
}

.trip-hero-summary__kicker {
  margin: 0 0 var(--space-2);
  color: var(--color-text-muted);
  font-size: var(--text-body-s);
}

.trip-hero-summary__title {
  margin: 0;
  font-family: var(--font-serif);
  font-size: var(--text-h1);
  line-height: var(--leading-h1);
}

.trip-hero-summary__route,
.trip-hero-summary__metrics dd {
  margin: var(--space-2) 0 0;
}

.trip-hero-summary__metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--space-4);
  margin: var(--space-6) 0 0;
}

.trip-hero-summary__metrics dt {
  color: var(--color-text-muted);
  font-size: var(--text-caption);
}

.trip-hero-summary__map {
  position: relative;
  min-height: 160px;
  border-radius: var(--radius-lg);
  background:
    radial-gradient(circle at 20% 20%, var(--color-glow-primary), transparent 55%),
    radial-gradient(circle at 80% 80%, var(--color-glow-accent), transparent 50%);
  background-color: var(--color-canvas-alt);
}

.trip-hero-summary__map::after {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--color-contour);
  mask: url('../../assets/topographic-lines.svg') center / 280px 280px repeat;
  -webkit-mask: url('../../assets/topographic-lines.svg') center / 280px 280px repeat;
}

.trip-hero-summary__desktop-actions {
  margin-top: var(--space-6);
}

@media (min-width: 1024px) {
  .trip-hero-summary {
    grid-template-columns: 7fr 5fr;
    align-items: stretch;
  }
}

@media (max-width: 767px) {
  .trip-hero-summary__desktop-actions {
    display: none;
  }
}
</style>
