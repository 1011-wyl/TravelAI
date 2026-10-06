<template>
  <div class="weather-day-rail" role="group" :aria-label="t('result.weather.railLabel')">
    <button
      v-for="(item, index) in items"
      :key="weatherDayKey(item, index)"
      type="button"
      class="weather-day-rail__item"
      :class="{ 'is-current': weatherDayKey(item, index) === selectedKey }"
      :aria-pressed="weatherDayKey(item, index) === selectedKey ? 'true' : 'false'"
      @click="emit('select', weatherDayKey(item, index))"
    >
      <span class="weather-day-rail__mark" aria-hidden="true"></span>
      <span class="weather-day-rail__weekday">{{ formatWeatherWeekday(item.date, locale, true) }}</span>
      <span class="weather-day-rail__date">{{ item.date || t('result.weather.missing') }}</span>
      <span class="weather-day-rail__summary">
        {{ formatWeatherTemp(item.day_temp) }}
        <template v-if="item.day_weather"> · {{ item.day_weather }}</template>
      </span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { WeatherInfo } from '@/types'
import { formatWeatherTemp, formatWeatherWeekday, weatherDayKey } from './weatherModel'

defineProps<{
  items: WeatherInfo[]
  selectedKey: string | null
}>()

const emit = defineEmits<{
  select: [key: string]
}>()

const { t, locale } = useI18n()
</script>

<style scoped>
.weather-day-rail {
  display: flex;
  gap: var(--space-2);
  overflow-x: auto;
  overscroll-behavior-x: contain;
  scroll-snap-type: x mandatory;
  padding-bottom: var(--space-2);
}

.weather-day-rail__item {
  position: relative;
  flex: 0 0 auto;
  display: grid;
  justify-items: start;
  gap: 2px;
  min-width: 64px;
  min-height: 56px;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
  scroll-snap-align: start;
  transition:
    border-color var(--duration-base) var(--ease-standard),
    background-color var(--duration-base) var(--ease-standard);
}

.weather-day-rail__item:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 75%, transparent);
  outline-offset: 2px;
}

.weather-day-rail__item.is-current {
  border-width: 2px;
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.weather-day-rail__mark {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-border-strong);
}

.weather-day-rail__item.is-current .weather-day-rail__mark {
  background: var(--color-primary);
}

.weather-day-rail__weekday {
  font-weight: 700;
  font-size: var(--text-body-s);
}

.weather-day-rail__date,
.weather-day-rail__summary {
  color: var(--color-text-muted);
  font-size: var(--text-caption);
}
</style>
