<template>
  <article class="trip-brief">
    <h2 class="trip-brief__title">{{ t('home.brief.title') }}</h2>
    <ol class="trip-brief__cities">
      <li v-for="(city, index) in snapshot.cities" :key="`${city.city}-${index}`">
        <span class="trip-brief__city">{{ city.city }}</span>
        <span class="trip-brief__days">{{ t('home.brief.stayDays', { n: city.days }) }}</span>
      </li>
    </ol>
    <dl class="trip-brief__meta">
      <div>
        <dt>{{ t('home.startDateLabel') }}</dt>
        <dd>{{ snapshot.startDate }}</dd>
      </div>
      <div>
        <dt>{{ t('home.endDateSummaryLabel') }}</dt>
        <dd>{{ snapshot.endDate }}</dd>
      </div>
      <div>
        <dt>{{ t('home.travelDaysLabel') }}</dt>
        <dd>{{ t('home.totalDays', { n: snapshot.travelDays }) }}</dd>
      </div>
      <div>
        <dt>{{ t('home.transportationLabel') }}</dt>
        <dd>{{ transportLabel }}</dd>
      </div>
      <div>
        <dt>{{ t('home.accommodationLabel') }}</dt>
        <dd>{{ stayLabel }}</dd>
      </div>
      <div>
        <dt>{{ t('home.interestsLabel') }}</dt>
        <dd>{{ interestsLabel }}</dd>
      </div>
    </dl>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ACCOMMODATION_OPTIONS,
  INTEREST_OPTIONS,
  TRANSPORT_OPTIONS,
  type TripBriefSnapshot,
} from '@/components/landing/landingModel'

const props = defineProps<{
  snapshot: TripBriefSnapshot
}>()

const { t } = useI18n()

const transportLabel = computed(() => {
  const found = TRANSPORT_OPTIONS.find((item) => item.value === props.snapshot.transportation)
  return found ? t(found.labelKey) : props.snapshot.transportation
})

const stayLabel = computed(() => {
  const found = ACCOMMODATION_OPTIONS.find((item) => item.value === props.snapshot.accommodation)
  return found ? t(found.labelKey) : props.snapshot.accommodation
})

const interestsLabel = computed(() => {
  if (props.snapshot.preferences.length === 0) return t('home.brief.noInterests')
  return props.snapshot.preferences
    .map((value) => {
      const found = INTEREST_OPTIONS.find((item) => item.value === value)
      return found ? t(found.labelKey) : value
    })
    .join(t('home.cityOrderJoin'))
})
</script>

<style scoped>
.trip-brief {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-6);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-organic);
}

.trip-brief__title {
  margin: 0;
  font-size: var(--text-h3);
}

.trip-brief__cities {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: var(--space-2);
}

.trip-brief__cities li {
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
  padding-left: 18px;
  position: relative;
}

.trip-brief__cities li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.45em;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
}

.trip-brief__meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3) var(--space-4);
  margin: 0;
}

.trip-brief__meta dt {
  color: var(--color-text-muted);
  font-size: var(--text-caption);
}

.trip-brief__meta dd {
  margin: 4px 0 0;
}

@media (max-width: 639px) {
  .trip-brief__meta {
    grid-template-columns: 1fr;
  }
}
</style>
