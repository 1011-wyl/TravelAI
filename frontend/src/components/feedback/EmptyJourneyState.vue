<template>
  <section class="empty-journey" aria-labelledby="empty-journey-title">
    <svg class="empty-journey__art" viewBox="0 0 240 120" fill="none" aria-hidden="true">
      <path d="M18 86 C54 86, 62 38, 108 38 S162 92, 222 62" stroke="var(--color-primary)" stroke-width="2.4" stroke-linecap="round" />
      <circle cx="18" cy="86" r="6" fill="var(--color-primary)" />
      <circle cx="108" cy="38" r="6" fill="var(--color-accent-strong)" />
      <circle cx="222" cy="62" r="6" fill="var(--color-primary)" />
    </svg>
    <h2 id="empty-journey-title" class="empty-journey__title">{{ title }}</h2>
    <p class="empty-journey__desc">{{ description }}</p>
    <div v-if="$slots.action" class="empty-journey__action">
      <slot name="action" />
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description: string
}>()
</script>

<style scoped>
.empty-journey {
  display: grid;
  justify-items: center;
  text-align: center;
  gap: var(--space-4);
  padding: var(--space-8) var(--space-4);
}

.empty-journey__art {
  width: min(240px, 70vw);
  height: auto;
}

.empty-journey__title {
  margin: 0;
  font-size: var(--text-h2);
  line-height: var(--leading-h2);
}

.empty-journey__desc {
  margin: 0;
  max-width: 48ch;
  color: var(--color-text-muted);
}

.empty-journey__action {
  margin-top: var(--space-2);
}
</style>
