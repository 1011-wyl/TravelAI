<template>
  <div
    class="content-skeleton"
    :class="`content-skeleton--${variant}`"
    aria-hidden="true"
  >
    <template v-if="variant === 'text'">
      <span
        v-for="index in lines"
        :key="index"
        class="content-skeleton__bar"
        :style="{ width: index === lines ? '62%' : '100%', height: '14px' }"
      />
    </template>
    <template v-else-if="variant === 'metric'">
      <span class="content-skeleton__bar" style="width: 48%; height: 12px;" />
      <span class="content-skeleton__bar" style="width: 72%; height: 28px;" />
    </template>
    <template v-else-if="variant === 'image'">
      <span class="content-skeleton__media" :style="{ height: imageHeight }" />
    </template>
    <template v-else>
      <span v-for="index in lines" :key="index" class="content-skeleton__row">
        <span class="content-skeleton__dot" />
        <span class="content-skeleton__bar" :style="{ width: index % 2 ? '88%' : '74%', height: '14px' }" />
      </span>
    </template>
  </div>
</template>

<script setup lang="ts">
export type ContentSkeletonVariant = 'text' | 'metric' | 'image' | 'list'

withDefaults(
  defineProps<{
    variant?: ContentSkeletonVariant
    lines?: number
    imageHeight?: string
  }>(),
  {
    variant: 'text',
    lines: 3,
    imageHeight: '160px',
  }
)
</script>

<style scoped>
.content-skeleton {
  display: grid;
  gap: var(--space-3);
}

.content-skeleton__bar,
.content-skeleton__media,
.content-skeleton__dot {
  display: block;
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--color-canvas-alt) 0%, var(--color-surface) 50%, var(--color-canvas-alt) 100%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.6s linear infinite;
}

.content-skeleton__media {
  width: 100%;
  border-radius: var(--radius-lg);
}

.content-skeleton__row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.content-skeleton__dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

@keyframes skeleton-shimmer {
  from { background-position: 100% 0; }
  to { background-position: -100% 0; }
}

html[data-motion='reduce'] .content-skeleton__bar,
html[data-motion='reduce'] .content-skeleton__media,
html[data-motion='reduce'] .content-skeleton__dot {
  animation: none;
  background: var(--color-canvas-alt);
}
</style>
