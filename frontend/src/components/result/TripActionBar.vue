<template>
  <div class="trip-action-bar" :class="{ 'is-mobile-sticky': sticky }">
    <AppButton variant="secondary" @click="emit('back')">{{ t('result.backHome') }}</AppButton>
    <AppButton variant="secondary" :disabled="exporting" @click="emit('export')">
      {{ t('result.exportImage') }}
    </AppButton>
    <AppButton
      variant="primary"
      :aria-expanded="askOpen ? 'true' : 'false'"
      :aria-controls="askControls"
      @click="emit('ask')"
    >{{ t('result.chat.toggle') }}</AppButton>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import AppButton from '@/components/ui/AppButton.vue'

withDefaults(
  defineProps<{
    sticky?: boolean
    exporting?: boolean
    askOpen?: boolean
    askControls?: string
  }>(),
  {
    sticky: false,
    exporting: false,
    askOpen: false,
    askControls: 'result-ai-chat-panel',
  }
)

const emit = defineEmits<{
  back: []
  export: []
  ask: []
}>()

const { t } = useI18n()
</script>

<style scoped>
.trip-action-bar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.trip-action-bar.is-mobile-sticky {
  display: none;
}

@media (max-width: 767px) {
  .trip-action-bar.is-mobile-sticky {
    display: flex;
    position: sticky;
    bottom: 0;
    z-index: 20;
    padding: var(--space-3) var(--page-gutter) calc(var(--space-3) + env(safe-area-inset-bottom));
    background: color-mix(in srgb, var(--color-surface) 92%, transparent);
    border-top: 1px solid var(--color-border);
  }
}
</style>
