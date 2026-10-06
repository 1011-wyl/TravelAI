<template>
  <aside class="weather-impact">
    <InlineNotice :title="t('result.weather.impactTitle')" :message="t('result.weather.impactNeutral')" kind="info" />
    <p class="weather-impact__note">{{ t('result.weather.impactHint') }}</p>
  </aside>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import InlineNotice from '@/components/feedback/InlineNotice.vue'

const { t } = useI18n()
</script>

<style scoped>
.weather-impact {
  display: grid;
  align-content: start;
  gap: var(--space-4);
  min-width: 0;
}

.weather-impact__note {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--text-body-s);
}
</style>
