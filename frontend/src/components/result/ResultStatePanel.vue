<template>
  <section class="result-state" :aria-busy="status === 'loading' || undefined">
    <div v-if="status === 'loading'" class="result-state__loading">
      <p class="sr-only">{{ t('common.loading') }}</p>
      <ContentSkeleton variant="text" :lines="3" />
      <ContentSkeleton variant="image" image-height="180px" />
      <p>{{ t('result.state.loading') }}</p>
    </div>
    <EmptyJourneyState
      v-else-if="status === 'missing'"
      :title="t('result.state.missingTitle')"
      :description="t('result.state.missingDesc')"
    >
      <template #action>
        <AppButton variant="primary" @click="emit('home')">{{ t('result.backCreateTrip') }}</AppButton>
      </template>
    </EmptyJourneyState>
    <ErrorJourneyState
      v-else
      :title="status === 'parse-failed' ? t('result.state.parseTitle') : t('result.state.restoreTitle')"
      :what-happened="status === 'parse-failed' ? t('result.state.parseDesc') : t('result.state.restoreDesc')"
      :data-status="t('result.state.dataLocal')"
    >
      <template #action>
        <div class="result-state__actions">
          <AppButton v-if="status === 'restore-failed'" variant="secondary" @click="emit('retry')">
            {{ t('result.state.retry') }}
          </AppButton>
          <AppButton variant="primary" @click="emit('home')">{{ t('result.backHome') }}</AppButton>
        </div>
      </template>
    </ErrorJourneyState>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import AppButton from '@/components/ui/AppButton.vue'
import ContentSkeleton from '@/components/feedback/ContentSkeleton.vue'
import EmptyJourneyState from '@/components/feedback/EmptyJourneyState.vue'
import ErrorJourneyState from '@/components/feedback/ErrorJourneyState.vue'
import type { ResultLoadStatus } from '@/composables/useTripPlanState'

defineProps<{
  status: Exclude<ResultLoadStatus, 'ready'>
}>()

const emit = defineEmits<{
  home: []
  retry: []
}>()

const { t } = useI18n()
</script>

<style scoped>
.result-state {
  padding: var(--space-8) 0;
}

.result-state__loading {
  display: grid;
  gap: var(--space-4);
}

.result-state__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-2);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}
</style>
