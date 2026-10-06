<template>
  <header class="app-section-header">
    <div class="app-section-header__copy">
      <component :is="headingTag" class="app-section-header__title">
        {{ title }}
      </component>
      <p v-if="description" class="app-section-header__desc">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="app-section-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    title: string
    description?: string
    headingLevel?: 1 | 2 | 3
  }>(),
  {
    description: '',
    headingLevel: 2,
  }
)

const headingTag = computed(() => `h${props.headingLevel}`)
</script>

<style scoped>
.app-section-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.app-section-header__title {
  margin: 0;
  color: var(--color-text);
  font-weight: var(--weight-heading);
  font-size: var(--text-h2);
  line-height: var(--leading-h2);
}

.app-section-header__desc {
  margin: var(--space-2) 0 0;
  max-width: 68ch;
  color: var(--color-text-muted);
  font-size: var(--text-body);
  line-height: var(--leading-body);
}

.app-section-header__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

@media (max-width: 767px) {
  .app-section-header {
    flex-direction: column;
  }
}
</style>
