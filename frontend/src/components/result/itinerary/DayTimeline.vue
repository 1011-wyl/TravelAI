<template>
  <section class="day-timeline" :data-day-index="dayIndex">
    <header class="day-timeline__header">
      <div class="day-timeline__heading">
        <h3 :id="headingId" class="day-timeline__title" tabindex="-1">
          {{ t('common.dayNumber', { day: dayIndex + 1 }) }}
        </h3>
        <p class="day-timeline__meta">
          <span v-if="day.date">{{ day.date }}</span>
          <span>{{ day.city || planCity }}</span>
          <span v-if="day.is_transfer_day">{{ t('result.transferDay') }}</span>
        </p>
        <p v-if="!expanded" class="day-timeline__summary">{{ collapsedSummary }}</p>
      </div>
      <button
        type="button"
        class="day-timeline__toggle"
        :aria-expanded="expanded"
        :aria-controls="panelId"
        @click="emit('toggle', dayIndex)"
      >
        {{ expanded ? t('result.itinerary.collapse') : t('result.itinerary.expand') }}
      </button>
    </header>

    <div
      :id="panelId"
      class="day-timeline__panel"
      :class="{ 'is-open': expanded, 'is-instant': instantFold }"
      :inert="expanded ? undefined : true"
    >
      <div class="day-timeline__panel-inner">
        <ItineraryStop
          v-if="hasTransfer"
          kind="transfer"
          :kind-label="t('result.transferInfo')"
          :title="day.transfer_info || ''"
          :enter-index="playIntro ? 0 : -1"
        />

        <dl v-if="hasFacts" class="day-timeline__facts">
          <div v-if="day.description">
            <dt>{{ t('result.dayDescription') }}</dt>
            <dd>{{ day.description }}</dd>
          </div>
          <div v-if="day.transportation">
            <dt>{{ t('result.dayTransport') }}</dt>
            <dd>{{ day.transportation }}</dd>
          </div>
          <div v-if="day.accommodation">
            <dt>{{ t('result.dayAccommodation') }}</dt>
            <dd>{{ day.accommodation }}</dd>
          </div>
        </dl>

        <div
          v-if="hasStops"
          class="day-timeline__track"
          :class="{ 'is-intro': playIntro }"
          @animationend="onIntroEnd"
        >
          <ItineraryStop
            v-for="(attraction, attractionIndex) in attractions"
            :key="`attr-${attractionIndex}-${attraction.name}`"
            kind="attraction"
            :kind-label="t('result.attractionTitle')"
            :title="attraction.name"
            :place="attraction.address"
            :duration-label="durationText(attraction.visit_duration)"
            :price-label="attraction.ticket_price ? `¥${attraction.ticket_price}` : ''"
            :extra-lines="attractionExtra(attraction)"
            :note="attraction.description"
            :reservation-required="Boolean(attraction.reservation_required)"
            :reservation-tips="attraction.reservation_tips || ''"
            :image-src="imageSrc(attraction, attractionIndex)"
            :lazy-image="lazyImages"
            :edit-mode="editMode"
            :address-value="attraction.address"
            :duration-value="attraction.visit_duration"
            :move-up-disabled="attractionIndex === 0"
            :move-down-disabled="attractionIndex === attractions.length - 1"
            :enter-index="playIntro ? Math.min(attractionIndex + (hasTransfer ? 1 : 0), 5) : -1"
            @view-map="emit('view-map')"
            @remove="emit('delete-attraction', day.day_index, attractionIndex)"
            @move-up="emit('move-attraction', day.day_index, attractionIndex, 'up')"
            @move-down="emit('move-attraction', day.day_index, attractionIndex, 'down')"
            @update-address="emit('update-attraction', dayIndex, attractionIndex, 'address', $event)"
            @update-duration="emit('update-attraction', dayIndex, attractionIndex, 'visit_duration', $event)"
            @update-note="emit('update-attraction', dayIndex, attractionIndex, 'description', $event)"
          />

          <ItineraryStop
            v-if="day.hotel"
            kind="hotel"
            :kind-label="t('result.hotelTitle')"
            :title="day.hotel.name"
            :place="day.hotel.address"
            :price-label="day.hotel.estimated_cost ? `¥${day.hotel.estimated_cost}` : ''"
            :extra-lines="hotelExtra(day.hotel)"
            :enter-index="playIntro ? Math.min(attractions.length + (hasTransfer ? 1 : 0), 5) : -1"
          />

          <ItineraryStop
            v-for="(meal, mealIndex) in day.meals"
            :key="`meal-${mealIndex}-${meal.type}`"
            kind="meal"
            :kind-label="mealLabel(meal.type)"
            :title="meal.name"
            :place="meal.address || ''"
            :price-label="meal.estimated_cost ? `¥${meal.estimated_cost}` : ''"
            :note="meal.description || ''"
            :enter-index="playIntro ? Math.min(attractions.length + (day.hotel ? 1 : 0) + mealIndex + (hasTransfer ? 1 : 0), 5) : -1"
          />
        </div>
        <p v-else-if="!hasTransfer && !hasFacts" class="day-timeline__empty">{{ t('result.itinerary.emptyDay') }}</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Attraction, DayPlan, Hotel } from '@/types'
import ItineraryStop from '@/components/result/itinerary/ItineraryStop.vue'

type AttractionNode = Attraction & {
  reservation_required?: boolean
  reservation_tips?: string
}

const props = defineProps<{
  day: DayPlan
  dayIndex: number
  planCity: string
  expanded: boolean
  editMode: boolean
  imageSrc: (attraction: Attraction, index: number) => string
  lazyImages: boolean
  instantFold: boolean
  playIntro: boolean
}>()

const emit = defineEmits<{
  toggle: [dayIndex: number]
  'view-map': []
  'intro-end': [dayIndex: number]
  'delete-attraction': [dayIndex: number, attractionIndex: number]
  'move-attraction': [dayIndex: number, attractionIndex: number, direction: 'up' | 'down']
  'update-attraction': [dayIndex: number, attractionIndex: number, field: 'address' | 'visit_duration' | 'description', value: string | number]
}>()

const { t } = useI18n()
const headingId = computed(() => `itinerary-day-${props.dayIndex}`)
const panelId = computed(() => `itinerary-day-panel-${props.dayIndex}`)
const attractions = computed(() => props.day.attractions as AttractionNode[])
const hasTransfer = computed(() => Boolean(props.day.is_transfer_day && props.day.transfer_info))
const hasFacts = computed(() => Boolean(props.day.description || props.day.transportation || props.day.accommodation))
const hasStops = computed(() => Boolean(props.day.attractions.length || props.day.hotel || props.day.meals.length))

const collapsedSummary = computed(() => {
  const city = props.day.city || props.planCity
  const count = props.day.attractions.length
  const minutes = props.day.attractions.reduce((sum, item) => sum + (Number(item.visit_duration) || 0), 0)
  const parts = [city]
  if (count) parts.push(t('result.itinerary.attractionCount', { count }))
  if (minutes) parts.push(`${minutes}${t('result.minuteUnit')}`)
  return parts.filter(Boolean).join(t('result.summary.cityJoin'))
})

const durationText = (value?: number) => {
  if (!value) return ''
  return t('result.fieldVisitDuration') + ' ' + value + t('result.minuteUnit')
}

const mealLabel = (type: string) => {
  const labels: Record<string, string> = {
    breakfast: t('result.meals.breakfast'),
    lunch: t('result.meals.lunch'),
    dinner: t('result.meals.dinner'),
    snack: t('result.meals.snack'),
  }
  return labels[type] || type
}

const attractionExtra = (attraction: AttractionNode) => {
  const lines: string[] = []
  if (attraction.rating) lines.push(`${t('result.fieldRating')}: ${attraction.rating}`)
  return lines
}

const hotelExtra = (hotel: Hotel) => {
  const lines: string[] = []
  if (hotel.type) lines.push(`${t('result.fieldType')}: ${hotel.type}`)
  if (hotel.price_range) lines.push(`${t('result.fieldPriceRange')}: ${hotel.price_range}`)
  if (hotel.rating) lines.push(`${t('result.fieldRating')}: ${hotel.rating}`)
  if (hotel.distance) lines.push(`${t('result.fieldDistance')}: ${hotel.distance}`)
  return lines
}

const onIntroEnd = (event?: AnimationEvent) => {
  if (event && event.target !== event.currentTarget) return
  emit('intro-end', props.dayIndex)
}

watch(
  () => props.playIntro,
  (play) => {
    if (!play) return
    window.setTimeout(() => {
      if (props.playIntro) onIntroEnd()
    }, 720)
  }
)
</script>

<style scoped>
.day-timeline {
  padding-bottom: var(--space-8);
  border-bottom: 1px solid var(--color-border);
}

.day-timeline__header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--space-3);
  align-items: flex-start;
}

.day-timeline__title {
  margin: 0;
  scroll-margin-top: 140px;
  font-size: var(--text-h3);
}

.day-timeline__meta,
.day-timeline__summary {
  margin: var(--space-1) 0 0;
  color: var(--color-text-muted);
}

.day-timeline__meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.day-timeline__toggle {
  min-height: var(--control-h-md);
  min-width: var(--control-h-md);
  padding: 0 var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: inherit;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.day-timeline__toggle:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 75%, transparent);
  outline-offset: 2px;
}

.day-timeline__panel {
  display: grid;
  grid-template-rows: 0fr;
  overflow: hidden;
  transition: grid-template-rows var(--duration-slow) var(--ease-standard);
}

.day-timeline__panel.is-open {
  grid-template-rows: 1fr;
}

.day-timeline__panel.is-instant,
html[data-motion='reduce'] .day-timeline__panel {
  transition: none;
}

.day-timeline__panel-inner {
  overflow: hidden;
  min-height: 0;
  display: grid;
  gap: var(--space-6);
  padding-top: var(--space-4);
}

.day-timeline__facts {
  margin: 0;
  display: grid;
  gap: var(--space-2);
}

.day-timeline__facts dt {
  color: var(--color-text-muted);
  font-size: var(--text-caption);
}

.day-timeline__facts dd {
  margin: 2px 0 0;
  white-space: pre-wrap;
}

.day-timeline__track {
  display: grid;
  gap: var(--space-6);
}

.day-timeline__track.is-intro {
  animation: itinerary-grow var(--duration-scene) var(--ease-standard) both;
  transform-origin: top;
}

.day-timeline__empty {
  margin: 0;
  color: var(--color-text-muted);
}

@keyframes itinerary-grow {
  from {
    opacity: 0.4;
    transform: scaleY(0.92);
  }
  to {
    opacity: 1;
    transform: scaleY(1);
  }
}

html[data-motion='reduce'] .day-timeline__track.is-intro {
  animation: none;
}
</style>
