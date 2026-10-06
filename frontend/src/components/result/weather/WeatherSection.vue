<template>
  <section id="weather" class="weather-section" aria-labelledby="result-section-heading">
    <EmptyJourneyState
      v-if="items.length === 0"
      :title="t('result.weather.emptyTitle')"
      :description="t('result.weather.emptyDesc')"
    />
    <div v-else class="weather-section__body">
      <WeatherDayRail :items="items" :selected-key="selectedKey" @select="selectedKey = $event" />

      <p class="weather-section__live" aria-live="polite">{{ liveText }}</p>

      <div class="weather-section__stage">
        <div class="weather-section__scene">
          <Transition :name="reduceMotion ? '' : 'weather-swap'" mode="out-in">
            <WeatherScene
              v-if="selectedWeather"
              :key="selectedKey || 'weather-scene'"
              :weather="selectedWeather"
              :fallback-city="fallbackCity"
            />
          </Transition>
        </div>
        <WeatherImpact />
      </div>

      <section class="weather-section__table" :aria-label="t('result.weather.tableLabel')">
        <table class="weather-section__grid">
          <thead>
            <tr>
              <th>{{ t('result.weather.colDate') }}</th>
              <th>{{ t('result.weather.colCity') }}</th>
              <th>{{ t('result.weatherDay') }}</th>
              <th>{{ t('result.weatherNight') }}</th>
              <th>{{ t('result.weatherPrecipitation') }}（{{ t('result.weather.estimated') }}）</th>
              <th>{{ t('result.weatherHumidity') }}（{{ t('result.weather.estimated') }}）</th>
              <th>{{ t('result.weatherWind') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in items" :key="weatherDayKey(item, index)">
              <td>{{ item.date || t('result.weather.missing') }}</td>
              <td>{{ item.city || fallbackCity }}</td>
              <td>{{ dayCell(item) }}</td>
              <td>{{ nightCell(item) }}</td>
              <td>{{ getWeatherPrecipitation(item.day_weather) }}</td>
              <td>{{ getWeatherHumidity(item.day_weather) }}</td>
              <td>{{ getWeatherWind(item) }}</td>
            </tr>
          </tbody>
        </table>

        <ul class="weather-section__cards">
          <li v-for="(item, index) in items" :key="`card-${weatherDayKey(item, index)}`">
            <p><strong>{{ t('result.weather.colDate') }}</strong> {{ item.date || t('result.weather.missing') }}</p>
            <p><strong>{{ t('result.weather.colCity') }}</strong> {{ item.city || fallbackCity }}</p>
            <p><strong>{{ t('result.weatherDay') }}</strong> {{ dayCell(item) }}</p>
            <p><strong>{{ t('result.weatherNight') }}</strong> {{ nightCell(item) }}</p>
            <p><strong>{{ t('result.weatherPrecipitation') }}（{{ t('result.weather.estimated') }}）</strong> {{ getWeatherPrecipitation(item.day_weather) }}</p>
            <p><strong>{{ t('result.weatherHumidity') }}（{{ t('result.weather.estimated') }}）</strong> {{ getWeatherHumidity(item.day_weather) }}</p>
            <p><strong>{{ t('result.weatherWind') }}</strong> {{ getWeatherWind(item) }}</p>
          </li>
        </ul>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { WeatherInfo } from '@/types'
import EmptyJourneyState from '@/components/feedback/EmptyJourneyState.vue'
import WeatherDayRail from './WeatherDayRail.vue'
import WeatherScene from './WeatherScene.vue'
import WeatherImpact from './WeatherImpact.vue'
import {
  formatWeatherTemp,
  getWeatherHumidity,
  getWeatherPrecipitation,
  getWeatherWind,
  weatherDayKey,
} from './weatherModel'

const props = defineProps<{
  items: WeatherInfo[]
  fallbackCity: string
}>()

const { t } = useI18n()
const selectedKey = ref<string | null>(null)

const reduceMotion = computed(() => document.documentElement.getAttribute('data-motion') === 'reduce')

const selectedWeather = computed(() => {
  const index = props.items.findIndex((item, itemIndex) => weatherDayKey(item, itemIndex) === selectedKey.value)
  if (index < 0) return null
  return props.items[index]
})

const liveText = computed(() => {
  if (!selectedWeather.value) return ''
  return t('result.weather.liveChanged', { date: selectedWeather.value.date || t('result.weather.missing') })
})

const dayCell = (item: WeatherInfo) => {
  const text = item.day_weather?.trim() || t('result.weather.missing')
  return `${text} · ${formatWeatherTemp(item.day_temp)}`
}

const nightCell = (item: WeatherInfo) => {
  const text = item.night_weather?.trim() || t('result.weather.missing')
  return `${text} · ${formatWeatherTemp(item.night_temp)}`
}

watch(
  () => props.items.map((item, index) => weatherDayKey(item, index)).join('|'),
  () => {
    const keys = props.items.map((item, index) => weatherDayKey(item, index))
    if (keys.length === 0) {
      selectedKey.value = null
      return
    }
    if (selectedKey.value && keys.includes(selectedKey.value)) return
    selectedKey.value = keys[0]
  },
  { immediate: true }
)
</script>

<style scoped>
.weather-section {
  position: relative;
  overflow-x: hidden;
  display: grid;
  gap: var(--space-6);
}

.weather-section__body {
  display: grid;
  gap: var(--space-6);
}

.weather-section__live {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
}

.weather-section__stage {
  display: grid;
  gap: var(--space-6);
}

.weather-section__scene {
  min-width: 0;
}

.weather-section__grid {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-body-s);
}

.weather-section__grid th,
.weather-section__grid td {
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  text-align: left;
  vertical-align: top;
}

.weather-section__cards {
  display: none;
  margin: 0;
  padding: 0;
  list-style: none;
  gap: var(--space-4);
}

.weather-section__cards li {
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.weather-section__cards p {
  margin: 0 0 var(--space-2);
}

.weather-swap-enter-active,
.weather-swap-leave-active {
  transition:
    opacity var(--duration-base) var(--ease-standard),
    transform var(--duration-base) var(--ease-standard);
}

.weather-swap-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.weather-swap-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

html[data-motion='reduce'] .weather-swap-enter-active,
html[data-motion='reduce'] .weather-swap-leave-active {
  transition: none;
}

@media (min-width: 1024px) {
  .weather-section__stage {
    grid-template-columns: 7fr 5fr;
    align-items: start;
  }
}

@media (max-width: 1023px) {
  .weather-section__grid {
    display: none;
  }

  .weather-section__cards {
    display: grid;
  }
}
</style>
