<template>
  <section class="planning-journey" aria-labelledby="planning-journey-title">
    <h2 id="planning-journey-title" class="planning-journey__title">{{ t('home.journey.title') }}</h2>
    <p v-if="planCode" class="planning-journey__code">{{ t('home.loading.planCode', { code: planCode }) }}</p>
    <ol class="planning-journey__nodes">
      <li
        v-for="(node, index) in JOURNEY_NODES"
        :key="node.id"
        class="planning-journey__node"
        :class="{
          'is-complete': index < currentIndex || completed,
          'is-current': index === currentIndex && !completed,
        }"
      >
        <span class="planning-journey__dot" aria-hidden="true">
          <span v-if="index < currentIndex || completed">✓</span>
        </span>
        <div>
          <p class="planning-journey__name">{{ t(node.labelKey) }}</p>
          <p v-if="index === displayIndex" class="planning-journey__status">{{ statusText }}</p>
        </div>
      </li>
    </ol>
    <div v-if="hasPercent" class="planning-journey__bar" role="progressbar" :aria-label="t('home.journey.title')" :aria-valuenow="progress" aria-valuemin="0" aria-valuemax="100">
      <span :style="{ width: `${progress}%` }"></span>
    </div>
    <div v-else class="planning-journey__indeterminate" role="progressbar" :aria-label="t('home.journey.title')" :aria-valuetext="t('common.loading')"></div>
    <p class="sr-only" aria-live="polite">{{ statusText }}</p>
    <p v-if="showWaitHint" class="planning-journey__hint">{{ t('home.journey.waitHint') }}</p>
    <p v-if="completed" class="planning-journey__done">{{ t('home.journey.viewPlan') }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { TripTaskStage } from '@/types'
import { JOURNEY_NODES, knownStageLabelKey, resolveJourneyNodeIndex } from '@/components/landing/landingModel'

const props = withDefaults(
  defineProps<{
    stage: TripTaskStage | ''
    progress: number
    statusMessage: string
    planCode: string
    elapsedMs: number
    completed: boolean
  }>(),
  {
    stage: '',
    progress: 0,
    statusMessage: '',
    planCode: '',
    elapsedMs: 0,
    completed: false,
  }
)

const { t } = useI18n()

const mappedIndex = computed(() => resolveJourneyNodeIndex(props.stage))
const currentIndex = computed(() => {
  if (props.completed) return JOURNEY_NODES.length - 1
  if (mappedIndex.value >= 0) return mappedIndex.value
  return 0
})
const displayIndex = computed(() => currentIndex.value)
const hasPercent = computed(() => Number.isFinite(props.progress) && props.progress > 0)
const showWaitHint = computed(() => !props.completed && props.elapsedMs >= 10000)

const statusText = computed(() => {
  if (props.statusMessage) return props.statusMessage
  if (props.stage) {
    const key = knownStageLabelKey(props.stage as TripTaskStage)
    if (key) return t(key)
  }
  return t('home.journey.neutral')
})
</script>

<style scoped>
.planning-journey {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-6);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.planning-journey__title {
  margin: 0;
  font-size: var(--text-h3);
}

.planning-journey__code,
.planning-journey__hint,
.planning-journey__done,
.planning-journey__status {
  margin: 0;
  color: var(--color-text-muted);
}

.planning-journey__nodes {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: var(--space-3);
}

.planning-journey__node {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  gap: var(--space-3);
  align-items: start;
}

.planning-journey__dot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 2px solid var(--color-border);
  border-radius: 50%;
  color: #fff;
  font-size: 12px;
}

.planning-journey__node.is-complete .planning-journey__dot {
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.planning-journey__node.is-current .planning-journey__dot {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-accent) 25%, transparent);
  animation: node-breathe 1.2s var(--ease-standard) infinite;
}

.planning-journey__name {
  margin: 0;
  font-weight: 650;
}

.planning-journey__bar,
.planning-journey__indeterminate {
  height: 6px;
  overflow: hidden;
  border-radius: var(--radius-pill);
  background: var(--color-canvas-alt);
}

.planning-journey__bar span {
  display: block;
  height: 100%;
  background: var(--color-primary);
}

.planning-journey__indeterminate {
  background: repeating-linear-gradient(90deg, var(--color-canvas-alt) 0 12px, var(--color-border) 12px 24px);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}

@keyframes node-breathe {
  50% {
    transform: scale(1.08);
  }
}

html[data-motion='reduce'] .planning-journey__node.is-current .planning-journey__dot {
  animation: none;
}
</style>
