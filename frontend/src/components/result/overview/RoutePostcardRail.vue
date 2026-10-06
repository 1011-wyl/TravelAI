<template>
  <div class="postcard-rail">
    <div class="postcard-rail__toolbar">
      <AppIconButton :ariaLabel="t('result.overview.prevCards')" :disabled="atStart" @click="scrollBy(-1)">
        <svg viewBox="0 0 24 24" fill="none"><path d="M14 6l-6 6 6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </AppIconButton>
      <AppIconButton :ariaLabel="t('result.overview.nextCards')" :disabled="atEnd" @click="scrollBy(1)">
        <svg viewBox="0 0 24 24" fill="none"><path d="M10 6l6 6-6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </AppIconButton>
    </div>
    <svg v-if="items.length > 1" class="postcard-rail__path" viewBox="0 0 100 12" preserveAspectRatio="none" aria-hidden="true">
      <path class="postcard-rail__stroke" d="M2 8 C 20 8, 30 3, 50 3 S 80 10, 98 6" fill="none" stroke="currentColor" stroke-width="1.4" />
    </svg>
    <div ref="scroller" class="postcard-rail__scroller" @scroll="updateEdges">
      <RoutePostcard
        v-for="(item, index) in items"
        :key="`${item.dayArrayIndex}-${item.order}-${item.name}`"
        :item="item"
        :image-src="imageSrc(item, index)"
        :ariaLabel="t('result.overview.openNamed', { name: item.name, day: item.dayNumber })"
        :style="{ animationDelay: `${Math.min(index, 5) * 40}ms` }"
        @open-day="emit('open-day', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppIconButton from '@/components/ui/AppIconButton.vue'
import RoutePostcard from '@/components/result/overview/RoutePostcard.vue'
import type { OverviewAttractionItem } from '@/components/result/overview/overviewModel'

defineProps<{
  items: OverviewAttractionItem[]
  imageSrc: (item: OverviewAttractionItem, index: number) => string
}>()

const emit = defineEmits<{
  'open-day': [dayArrayIndex: number]
}>()

const { t } = useI18n()
const scroller = ref<HTMLElement | null>(null)
const atStart = ref(true)
const atEnd = ref(false)

const updateEdges = () => {
  const el = scroller.value
  if (!el) return
  atStart.value = el.scrollLeft <= 8
  atEnd.value = el.scrollLeft + el.clientWidth >= el.scrollWidth - 8
}

const scrollBy = (direction: number) => {
  const el = scroller.value
  if (!el) return
  const amount = Math.min(360, el.clientWidth * 0.82) * direction
  const reduce = document.documentElement.getAttribute('data-motion') === 'reduce'
  el.scrollBy({ left: amount, behavior: reduce ? 'auto' : 'smooth' })
}

onMounted(async () => {
  await nextTick()
  updateEdges()
})
</script>

<style scoped>
.postcard-rail {
  display: grid;
  gap: var(--space-3);
  min-width: 0;
}

.postcard-rail__toolbar {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}

.postcard-rail__path {
  width: 100%;
  height: 12px;
  color: var(--color-primary);
}

.postcard-rail__stroke {
  stroke-dasharray: 160;
  stroke-dashoffset: 160;
  animation: rail-draw 720ms var(--ease-emphasized) forwards;
}

.postcard-rail__scroller {
  display: flex;
  gap: var(--space-4);
  min-width: 0;
  overflow-x: auto;
  overscroll-behavior-x: contain;
  scroll-snap-type: x mandatory;
  padding-bottom: var(--space-2);
}

.postcard-rail__scroller > * {
  animation: card-in var(--duration-slow) var(--ease-standard) both;
}

@keyframes rail-draw {
  to { stroke-dashoffset: 0; }
}

@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

html[data-motion='reduce'] .postcard-rail__stroke,
html[data-motion='reduce'] .postcard-rail__scroller > * {
  animation: none;
  stroke-dashoffset: 0;
  opacity: 1;
  transform: none;
}
</style>
