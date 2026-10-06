<template>
  <section class="itinerary-section" aria-labelledby="result-section-heading">
    <EmptyJourneyState
      v-if="plan.days.length === 0"
      :title="t('result.itinerary.emptyTitle')"
      :description="t('result.itinerary.emptyDesc')"
    />
    <div v-else class="itinerary-section__layout">
      <DayNavigator
        :days="plan.days"
        :plan-city="plan.city"
        :current-index="currentIndex"
        @select="onSelectDay"
      />
      <div ref="timelineRoot" class="itinerary-section__timelines">
        <DayTimeline
          v-for="(day, index) in plan.days"
          :key="`${day.date}-${index}`"
          :day="day"
          :day-index="index"
          :plan-city="plan.city"
          :expanded="expandedDays.includes(index)"
          :edit-mode="editMode"
          :image-src="imageSrc"
          :lazy-images="index > 0"
          :instant-fold="instantFold(day)"
          :play-intro="introDays.includes(index)"
          @toggle="toggleDay"
          @intro-end="onIntroEnd"
          @view-map="emit('view-map')"
          @delete-attraction="onDelete"
          @move-attraction="onMove"
          @update-attraction="onUpdate"
        />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Attraction, DayPlan, TripPlan } from '@/types'
import EmptyJourneyState from '@/components/feedback/EmptyJourneyState.vue'
import DayNavigator from '@/components/result/itinerary/DayNavigator.vue'
import DayTimeline from '@/components/result/itinerary/DayTimeline.vue'

const props = defineProps<{
  plan: TripPlan
  planKey: string
  editMode: boolean
  imageSrc: (attraction: Attraction, index: number) => string
  focusDayIndex: number | null
  focusNonce: number
  active: boolean
}>()

const emit = defineEmits<{
  'view-map': []
  'delete-attraction': [dayIndex: number, attractionIndex: number]
  'move-attraction': [dayIndex: number, attractionIndex: number, direction: 'up' | 'down']
  'update-attraction': [
    dayIndex: number,
    attractionIndex: number,
    field: 'address' | 'visit_duration' | 'description',
    value: string | number
  ]
}>()

const { t } = useI18n()
const timelineRoot = ref<HTMLElement | null>(null)
const currentIndex = ref(0)
const expandedDays = ref<number[]>([])
const introDays = ref<number[]>([])
const playedIntro = ref<number[]>([])
let observer: IntersectionObserver | null = null

const defaultExpanded = (count: number) => {
  if (count <= 3) return Array.from({ length: count }, (_, index) => index)
  return count > 0 ? [0] : []
}

const reduceMotion = () => document.documentElement.getAttribute('data-motion') === 'reduce'

const instantFold = (day: DayPlan) => {
  const nodes = day.attractions.length + day.meals.length + (day.hotel ? 1 : 0)
  return reduceMotion() || nodes > 6
}

const queueIntro = (index: number) => {
  const day = props.plan.days[index]
  const hasRoute =
    Boolean(day?.attractions.length || day?.hotel || (day?.meals && day.meals.length))
  if (
    !day ||
    !hasRoute ||
    reduceMotion() ||
    instantFold(day) ||
    playedIntro.value.includes(index) ||
    introDays.value.includes(index)
  ) {
    return
  }
  introDays.value = [...introDays.value, index]
}

const scrollToDay = async (index: number) => {
  await nextTick()
  const el = document.getElementById(`itinerary-day-${index}`)
  el?.scrollIntoView({
    behavior: reduceMotion() ? 'auto' : 'smooth',
    block: 'start',
  })
  el?.focus()
}

const ensureExpanded = (index: number) => {
  if (!expandedDays.value.includes(index)) {
    expandedDays.value = [...expandedDays.value, index]
    queueIntro(index)
  }
}

const toggleDay = (index: number) => {
  if (expandedDays.value.includes(index)) {
    expandedDays.value = expandedDays.value.filter((item) => item !== index)
    return
  }
  expandedDays.value = [...expandedDays.value, index]
  queueIntro(index)
}

const onSelectDay = async (index: number) => {
  ensureExpanded(index)
  currentIndex.value = index
  if (!props.active) return
  await scrollToDay(index)
}

const onIntroEnd = (index: number) => {
  introDays.value = introDays.value.filter((item) => item !== index)
  if (!playedIntro.value.includes(index)) {
    playedIntro.value = [...playedIntro.value, index]
  }
}

const onDelete = (dayIndex: number, attractionIndex: number) => {
  emit('delete-attraction', dayIndex, attractionIndex)
}

const onMove = (dayIndex: number, attractionIndex: number, direction: 'up' | 'down') => {
  emit('move-attraction', dayIndex, attractionIndex, direction)
}

const onUpdate = (
  dayIndex: number,
  attractionIndex: number,
  field: 'address' | 'visit_duration' | 'description',
  value: string | number
) => {
  emit('update-attraction', dayIndex, attractionIndex, field, value)
}

const bindObserver = () => {
  observer?.disconnect()
  const root = timelineRoot.value
  if (!root || !props.active) return
  observer = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0]
      if (!visible) return
      const index = Number((visible.target as HTMLElement).dataset.dayIndex)
      if (Number.isFinite(index)) currentIndex.value = index
    },
    { root: null, threshold: [0.35, 0.6], rootMargin: '-140px 0px -40% 0px' }
  )
  root.querySelectorAll<HTMLElement>('[data-day-index]').forEach((node) => observer?.observe(node))
}

watch(
  () => props.planKey,
  (next, prev) => {
    if (!next || next === prev) return
    expandedDays.value = defaultExpanded(props.plan.days.length)
    currentIndex.value = 0
    introDays.value = []
    playedIntro.value = []
    if (expandedDays.value.includes(0)) queueIntro(0)
  },
  { immediate: true }
)

watch(
  () => [props.active, props.focusDayIndex, props.focusNonce] as const,
  async ([isActive, index]) => {
    if (!isActive || index == null) return
    ensureExpanded(index)
    currentIndex.value = index
    await scrollToDay(index)
  }
)

watch(
  () => props.active,
  async (isActive) => {
    if (isActive) {
      await nextTick()
      bindObserver()
      return
    }
    observer?.disconnect()
    observer = null
  }
)

onMounted(async () => {
  await nextTick()
  bindObserver()
})

watch(
  () => props.plan.days.length,
  async () => {
    await nextTick()
    bindObserver()
  }
)

onUnmounted(() => {
  observer?.disconnect()
  observer = null
})
</script>

<style scoped>
.itinerary-section {
  overflow-x: hidden;
}

.itinerary-section__layout {
  display: grid;
  gap: var(--space-6);
}

.itinerary-section__timelines {
  min-width: 0;
}

@media (min-width: 1024px) {
  .itinerary-section__layout {
    grid-template-columns: 240px minmax(0, 1fr);
    align-items: start;
  }
}
</style>
