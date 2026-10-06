<template>
  <article class="route-postcard">
    <button type="button" class="route-postcard__hit" :aria-label="ariaLabel" @click="emit('open-day', item.dayArrayIndex)">
      <div class="route-postcard__media" :class="{ 'is-failed': imageFailed, 'is-loading': imageLoading }">
        <img
          v-if="imageSrc && !imageFailed"
          :src="imageSrc"
          :alt="item.name"
          @load="imageLoading = false"
          @error="onError"
        />
        <div v-else class="route-postcard__fallback">
          <span aria-hidden="true">📍</span>
          <span>{{ item.name }}</span>
        </div>
      </div>
      <div class="route-postcard__body">
        <p class="route-postcard__order">{{ t('result.overview.cardOrder', { day: item.dayNumber, n: item.order + 1 }) }}</p>
        <h3 class="route-postcard__name">{{ item.name }}</h3>
        <p v-if="item.address" class="route-postcard__place">{{ item.address }}</p>
        <p v-if="item.visit_duration" class="route-postcard__stay">
          {{ t('result.export.durationLine', { duration: item.visit_duration }) }}
        </p>
        <span class="route-postcard__action">{{ t('result.overview.openDay') }}</span>
      </div>
    </button>
  </article>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { OverviewAttractionItem } from '@/components/result/overview/overviewModel'

const props = defineProps<{
  item: OverviewAttractionItem
  imageSrc: string
  ariaLabel: string
}>()

const emit = defineEmits<{
  'open-day': [dayArrayIndex: number]
}>()

const { t } = useI18n()
const imageFailed = ref(false)
const imageLoading = ref(Boolean(props.imageSrc))

const onError = () => {
  imageFailed.value = true
  imageLoading.value = false
}
</script>

<style scoped>
.route-postcard {
  flex: 0 0 min(360px, 82vw);
  scroll-snap-align: start;
}

.route-postcard__hit {
  display: grid;
  width: 100%;
  padding: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  color: inherit;
  text-align: left;
  font: inherit;
  cursor: pointer;
  overflow: hidden;
  transition:
    transform var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard);
}

.route-postcard__hit:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-2);
}

.route-postcard__hit:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 75%, transparent);
  outline-offset: 2px;
}

.route-postcard__media {
  aspect-ratio: 4 / 3;
  background:
    radial-gradient(circle at 30% 20%, var(--color-glow-primary), transparent 60%),
    var(--color-canvas-alt);
  overflow: hidden;
}

.route-postcard__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--duration-fast) var(--ease-standard);
}

.route-postcard__hit:hover img {
  transform: scale(1.02);
}

.route-postcard__fallback {
  display: grid;
  place-content: center;
  gap: var(--space-2);
  height: 100%;
  text-align: center;
  padding: var(--space-4);
}

.route-postcard__body {
  display: grid;
  gap: var(--space-1);
  padding: var(--space-4);
}

.route-postcard__order,
.route-postcard__place,
.route-postcard__stay {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--text-body-s);
}

.route-postcard__name {
  margin: 0;
  font-size: var(--text-h3);
}

.route-postcard__action {
  margin-top: var(--space-2);
  color: var(--color-primary);
  font-weight: 650;
}

html[data-motion='reduce'] .route-postcard__hit,
html[data-motion='reduce'] .route-postcard__hit:hover,
html[data-motion='reduce'] .route-postcard__media img {
  transform: none;
  transition: none;
}
</style>
