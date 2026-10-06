<template>
  <section class="error-journey" aria-labelledby="error-journey-title">
    <svg class="error-journey__art" viewBox="0 0 240 120" fill="none" aria-hidden="true">
      <path d="M18 70 C60 70, 78 40, 112 46" stroke="var(--color-error)" stroke-width="2.4" stroke-linecap="round" />
      <path d="M132 58 C164 78, 188 40, 222 52" stroke="var(--color-error)" stroke-width="2.4" stroke-dasharray="6 6" stroke-linecap="round" />
      <circle cx="18" cy="70" r="6" fill="var(--color-error)" />
      <circle cx="222" cy="52" r="6" fill="var(--color-error)" />
    </svg>
    <h2 id="error-journey-title" class="error-journey__title">{{ title }}</h2>
    <p class="error-journey__what">{{ whatHappened }}</p>
    <p v-if="dataStatus" class="error-journey__data">{{ dataStatus }}</p>
    <div v-if="$slots.action" class="error-journey__action">
      <slot name="action" />
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  whatHappened: string
  dataStatus?: string
}>()
</script>

<style scoped>
.error-journey {
  display: grid;
  justify-items: center;
  text-align: center;
  gap: var(--space-3);
  padding: var(--space-8) var(--space-4);
}

.error-journey__art {
  width: min(240px, 70vw);
  height: auto;
}

.error-journey__title {
  margin: 0;
  font-size: var(--text-h2);
}

.error-journey__what,
.error-journey__data {
  margin: 0;
  max-width: 52ch;
  color: var(--color-text-muted);
}

.error-journey__action {
  margin-top: var(--space-3);
}
</style>
