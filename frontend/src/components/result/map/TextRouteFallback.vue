<template>
  <section class="text-route" :aria-label="t('result.map.textRouteLabel')">
    <h3 class="text-route__title">{{ t('result.map.textRouteTitle') }}</h3>
    <ol class="text-route__list">
      <li v-for="stop in stops" :key="stop.id">
        <strong>{{ stop.dayIndex + 1 }}-{{ stop.attrIndex + 1 }} {{ stop.name }}</strong>
        <span v-if="stop.address">{{ stop.address }}</span>
        <span v-if="stop.description">{{ stop.description }}</span>
        <span v-if="!stop.locatable">{{ t('result.map.unlocated') }}</span>
      </li>
    </ol>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { MapStop } from '@/composables/useTravelMap'

defineProps<{
  stops: MapStop[]
}>()

const { t } = useI18n()
</script>

<style scoped>
.text-route {
  display: grid;
  gap: var(--space-3);
}

.text-route__title {
  margin: 0;
  font-size: var(--text-h3);
}

.text-route__list {
  margin: 0;
  padding-left: 1.2em;
  display: grid;
  gap: var(--space-3);
}

.text-route__list li {
  display: grid;
  gap: 2px;
}

.text-route__list span {
  color: var(--color-text-muted);
  white-space: pre-wrap;
}
</style>
