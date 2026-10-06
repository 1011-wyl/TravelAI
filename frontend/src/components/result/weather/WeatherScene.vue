<template>
  <article class="weather-scene" :class="`is-${kind}`">
    <div class="weather-scene__art" aria-hidden="true">
      <svg v-if="kind === 'sunny' || kind === 'sun-shower'" viewBox="0 0 120 80" fill="none">
        <circle cx="86" cy="28" r="16" fill="var(--color-sand)" />
        <circle cx="86" cy="28" r="26" fill="var(--color-sand)" opacity="0.22" />
        <path
          v-if="kind === 'sun-shower'"
          d="M18 48h28M24 56h22M30 64h18"
          stroke="var(--color-sky)"
          stroke-width="2"
          stroke-linecap="round"
        />
      </svg>
      <svg v-else-if="kind === 'cloudy'" viewBox="0 0 120 80" fill="none">
        <ellipse cx="46" cy="42" rx="28" ry="16" fill="var(--color-border-strong)" opacity="0.45" />
        <ellipse cx="74" cy="46" rx="24" ry="14" fill="var(--color-border)" />
      </svg>
      <svg v-else-if="kind === 'rainy' || kind === 'thunder-storm'" viewBox="0 0 120 80" fill="none">
        <ellipse cx="58" cy="30" rx="32" ry="16" fill="var(--color-sky)" opacity="0.45" />
        <path d="M30 48l6 16M42 48l6 16M54 48l6 16M66 48l6 16M78 48l6 16M36 56l4 12M60 56l4 12M72 56l4 12" stroke="var(--color-sky)" stroke-width="1.6" stroke-linecap="round" />
        <path v-if="kind === 'thunder-storm'" d="M64 36l-10 16h8l-6 14 18-20h-8l8-10z" fill="var(--color-sand)" />
      </svg>
      <svg v-else-if="kind === 'flurries'" viewBox="0 0 120 80" fill="none">
        <ellipse cx="58" cy="28" rx="30" ry="14" fill="var(--color-border-strong)" opacity="0.4" />
        <circle cx="34" cy="52" r="3" fill="var(--color-sky)" />
        <circle cx="52" cy="60" r="2.5" fill="var(--color-sky)" />
        <circle cx="70" cy="50" r="3" fill="var(--color-sky)" />
        <circle cx="86" cy="62" r="2.2" fill="var(--color-sky)" />
      </svg>
      <svg v-else viewBox="0 0 120 80" fill="none">
        <path d="M16 58c18-18 38-18 56 0s38 18 56 0" stroke="var(--color-border-strong)" stroke-width="2" stroke-linecap="round" />
        <circle cx="60" cy="28" r="10" stroke="var(--color-text-muted)" stroke-width="2" />
      </svg>
    </div>

    <p class="weather-scene__kicker">{{ weekday }}</p>
    <h3 class="weather-scene__date">{{ dateLabel }}</h3>
    <p class="weather-scene__city">{{ city }}</p>
    <p class="weather-scene__temp">{{ tempLabel }}</p>
    <p class="weather-scene__desc">{{ description }}</p>

    <dl class="weather-scene__metrics">
      <div>
        <dt>{{ t('result.weatherDay') }}</dt>
        <dd>{{ dayLine }}</dd>
      </div>
      <div>
        <dt>{{ t('result.weatherNight') }}</dt>
        <dd>{{ nightLine }}</dd>
      </div>
      <div>
        <dt>{{ t('result.weatherPrecipitation') }}（{{ t('result.weather.estimated') }}）</dt>
        <dd>{{ precipitation }}</dd>
      </div>
      <div>
        <dt>{{ t('result.weatherHumidity') }}（{{ t('result.weather.estimated') }}）</dt>
        <dd>{{ humidity }}</dd>
      </div>
      <div>
        <dt>{{ t('result.weatherWind') }}</dt>
        <dd>{{ wind }}</dd>
      </div>
    </dl>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { WeatherInfo } from '@/types'
import {
  combinedWeatherText,
  formatWeatherDate,
  formatWeatherTemp,
  formatWeatherWeekday,
  getWeatherHumidity,
  getWeatherIconKind,
  getWeatherPrecipitation,
  getWeatherWind,
} from './weatherModel'

const props = defineProps<{
  weather: WeatherInfo
  fallbackCity: string
}>()

const { t, locale } = useI18n()
const kind = computed(() => getWeatherIconKind(combinedWeatherText(props.weather)))
const weekday = computed(() => formatWeatherWeekday(props.weather.date, locale.value))
const dateLabel = computed(() => formatWeatherDate(props.weather.date, locale.value))
const city = computed(() => props.weather.city || props.fallbackCity)
const tempLabel = computed(() => formatWeatherTemp(props.weather.day_temp))
const description = computed(() => props.weather.day_weather?.trim() || t('result.weather.missing'))
const dayLine = computed(() => {
  const text = props.weather.day_weather?.trim() || t('result.weather.missing')
  return `${text} · ${formatWeatherTemp(props.weather.day_temp)}`
})
const nightLine = computed(() => {
  const text = props.weather.night_weather?.trim() || t('result.weather.missing')
  return `${text} · ${formatWeatherTemp(props.weather.night_temp)}`
})
const precipitation = computed(() => getWeatherPrecipitation(props.weather.day_weather))
const humidity = computed(() => getWeatherHumidity(props.weather.day_weather))
const wind = computed(() => getWeatherWind(props.weather))
</script>

<style scoped>
.weather-scene {
  display: grid;
  gap: var(--space-2);
  min-width: 0;
  padding: var(--space-6);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.weather-scene.is-sunny,
.weather-scene.is-sun-shower {
  background: color-mix(in srgb, var(--color-sand) 16%, var(--color-surface));
}

.weather-scene.is-rainy,
.weather-scene.is-thunder-storm,
.weather-scene.is-cloudy,
.weather-scene.is-flurries {
  background: color-mix(in srgb, var(--color-sky) 12%, var(--color-surface));
}

.weather-scene__art {
  width: min(160px, 40%);
}

.weather-scene__art svg {
  width: 100%;
  height: auto;
  display: block;
}

.weather-scene__kicker,
.weather-scene__city,
.weather-scene__desc {
  margin: 0;
  color: var(--color-text-muted);
}

.weather-scene__date,
.weather-scene__temp {
  margin: 0;
}

.weather-scene__temp {
  font-size: var(--text-display-l);
  line-height: var(--leading-display-l);
  font-weight: var(--weight-display);
}

.weather-scene__metrics {
  display: grid;
  gap: var(--space-3);
  margin: var(--space-4) 0 0;
}

.weather-scene__metrics dt {
  color: var(--color-text-muted);
  font-size: var(--text-caption);
}

.weather-scene__metrics dd {
  margin: 2px 0 0;
}
</style>
