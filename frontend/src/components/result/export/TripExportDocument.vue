<template>
  <article ref="rootRef" class="trip-export-doc">
    <header class="trip-export-doc__header">
      <h1 class="trip-export-doc__title">{{ title }}</h1>
      <p class="trip-export-doc__subtitle">{{ subtitle }}</p>
      <p v-if="plan.overall_suggestions" class="trip-export-doc__suggest">{{ plan.overall_suggestions }}</p>
    </header>

    <section v-if="plan.budget" class="trip-export-card">
      <h2 class="trip-export-card__title">{{ t('result.budget.title') }}</h2>
      <div class="trip-export-metrics">
        <div class="trip-export-metric">
          <div class="trip-export-metric__label">{{ t('result.budget.attraction') }}</div>
          <div class="trip-export-metric__value">¥{{ plan.budget.total_attractions || 0 }}</div>
        </div>
        <div class="trip-export-metric">
          <div class="trip-export-metric__label">{{ t('result.budget.hotel') }}</div>
          <div class="trip-export-metric__value">¥{{ plan.budget.total_hotels || 0 }}</div>
        </div>
        <div class="trip-export-metric">
          <div class="trip-export-metric__label">{{ t('result.budget.meal') }}</div>
          <div class="trip-export-metric__value">¥{{ plan.budget.total_meals || 0 }}</div>
        </div>
        <div class="trip-export-metric">
          <div class="trip-export-metric__label">{{ t('result.budget.transport') }}</div>
          <div class="trip-export-metric__value">¥{{ plan.budget.total_transportation || 0 }}</div>
        </div>
      </div>
      <div class="trip-export-total">
        <span>{{ t('result.budget.total') }}</span>
        <strong>¥{{ plan.budget.total || 0 }}</strong>
      </div>
    </section>

    <section v-if="mapDataUrl" class="trip-export-card">
      <h2 class="trip-export-card__title">{{ t('result.side.map') }}</h2>
      <img class="trip-export-map" :src="mapDataUrl" alt="" />
    </section>

    <section v-for="(day, index) in plan.days" :key="`export-day-${index}`" class="trip-export-card">
      <h2 class="trip-export-card__title">
        {{ t('result.export.dayTitle', { day: index + 1 }) }}
        <span v-if="day.date" class="trip-export-day__meta">{{ day.date }}</span>
      </h2>
      <div class="trip-export-attractions">
        <article v-for="(attraction, ai) in day.attractions" :key="`export-a-${index}-${ai}`" class="trip-export-stop">
          <img
            v-if="photoOf(attraction) && !failedPhotos[photoOf(attraction)]"
            class="trip-export-stop__photo"
            :src="photoOf(attraction)"
            alt=""
            crossorigin="anonymous"
            @error="failedPhotos[photoOf(attraction)] = true"
          />
          <div v-else class="trip-export-stop__placeholder">{{ attraction.name }}</div>
          <h3 class="trip-export-stop__name">{{ ai + 1 }}. {{ attraction.name }}</h3>
          <p class="trip-export-stop__line">{{ attraction.address || '—' }}</p>
          <p class="trip-export-stop__line">
            {{ t('result.export.durationLine', { duration: attraction.visit_duration || '—' }) }}
            <template v-if="attraction.ticket_price">  |  ¥{{ attraction.ticket_price }}</template>
          </p>
          <p v-if="attraction.description" class="trip-export-stop__line">{{ attraction.description }}</p>
        </article>
      </div>
      <div v-if="day.meals && day.meals.length" class="trip-export-meals">
        <strong>{{ t('result.export.mealTitle') }}</strong>
        <div class="trip-export-meals__list">
          <div v-for="(meal, mi) in day.meals" :key="`export-m-${index}-${mi}`" class="trip-export-meal">
            <b>{{ mealLabel(meal.type) }}</b>:
            {{ meal.name || t('result.export.noMealRecommendation') }}
            <template v-if="meal.estimated_cost"> (¥{{ meal.estimated_cost }})</template>
          </div>
        </div>
      </div>
    </section>

    <section v-if="hotels.length" class="trip-export-card">
      <h2 class="trip-export-card__title">{{ t('result.hotelTitle') }}</h2>
      <article v-for="(hotel, hi) in hotels" :key="`export-h-${hi}`" class="trip-export-hotel">
        <b>{{ hotel.name || t('result.export.hotelFallback') }}</b>
        <span v-if="hotel.price" class="trip-export-hotel__price">¥{{ hotel.price }}{{ t('result.export.perNight') }}</span>
        <p v-if="hotel.address" class="trip-export-stop__line">{{ hotel.address }}</p>
      </article>
    </section>

    <section v-if="weatherItems.length" class="trip-export-card">
      <h2 class="trip-export-card__title">{{ t('result.export.weatherTitle') }}</h2>
      <div class="trip-export-weather">
        <article v-for="(item, wi) in weatherItems" :key="`export-w-${wi}`" class="trip-export-weather__card">
          <div class="trip-export-weather__date">{{ item.date }}</div>
          <div class="trip-export-weather__label">{{ t('result.export.daytime') }}</div>
          <div>{{ item.day_weather }} {{ item.day_temp }}°C</div>
          <div class="trip-export-weather__label">{{ t('result.export.nighttime') }}</div>
          <div>{{ item.night_weather }} {{ item.night_temp }}°C</div>
          <div class="trip-export-weather__label">{{ item.wind_direction }} {{ item.wind_power }}</div>
        </article>
      </div>
    </section>

    <footer class="trip-export-footer">
      <img
        v-if="showQr"
        class="trip-export-footer__qr"
        :src="qrUrl"
        alt=""
        crossorigin="anonymous"
        @error="showQr = false"
      />
      <div class="trip-export-footer__brand">TravelAI</div>
      <div class="trip-export-footer__url">https://github.com/1sdv/TripStar</div>
      <div class="trip-export-footer__note">{{ t('result.export.footer') }}</div>
    </footer>
  </article>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Attraction, TripPlan, WeatherInfo } from '@/types'
import '@/styles/export.css'

export type ExportHotel = {
  name?: string
  price?: number | string
  address?: string
}

export type ExportPlan = TripPlan & {
  hotel_recommendations?: ExportHotel[]
}

const props = defineProps<{
  plan: ExportPlan
  photos: Record<string, string>
  mapDataUrl: string
}>()

const { t } = useI18n()
const rootRef = ref<HTMLElement | null>(null)
const showQr = ref(true)
const failedPhotos = ref<Record<string, boolean>>({})
const qrUrl = 'https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=' + encodeURIComponent('https://github.com/1sdv/TripStar')

const title = computed(() => t('result.export.title', { city: props.plan.city }))
const subtitle = computed(() =>
  t('result.export.subtitle', {
    start: props.plan.start_date || '',
    end: props.plan.end_date || '',
    days: props.plan.days?.length || 0,
  })
)

const hotels = computed(() => props.plan.hotel_recommendations || [])
const weatherItems = computed(() => {
  const info = props.plan.weather_info
  return Array.isArray(info) ? (info as WeatherInfo[]) : []
})

const mealLabel = (type: string) => {
  if (type === 'breakfast' || type === 'lunch' || type === 'dinner' || type === 'snack') {
    return t(`result.meals.${type}`)
  }
  return type
}

const photoOf = (attraction: Attraction) => props.photos[attraction.name] || ''

defineExpose({ rootEl: rootRef })
</script>
