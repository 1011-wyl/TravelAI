<template>
  <section class="trip-history" aria-labelledby="trip-history-title">
    <AppSectionHeader :title="t('home.history.title')" :heading-level="2">
      <template #actions>
        <span v-if="status === 'success'" class="trip-history__count">{{ t('home.history.count', { n: items.length }) }}</span>
        <AppButton variant="ghost" size="sm" :loading="status === 'loading'" @click="emit('retry')">
          {{ t('home.history.refresh') }}
        </AppButton>
      </template>
    </AppSectionHeader>

    <div v-if="status === 'loading'" class="trip-history__grid" aria-busy="true">
      <p class="sr-only">{{ t('common.loading') }}</p>
      <ContentSkeleton v-for="index in 3" :key="index" variant="text" :lines="3" class="trip-history__skeleton" />
    </div>

    <EmptyJourneyState
      v-else-if="status === 'empty'"
      :title="t('home.history.emptyTitle')"
      :description="t('home.history.empty')"
    >
      <template #action>
        <AppButton variant="primary" @click="emit('focusPlanner')">{{ t('home.history.planNow') }}</AppButton>
      </template>
    </EmptyJourneyState>

    <ErrorJourneyState
      v-else-if="status === 'error'"
      :title="t('home.history.loadFailed')"
      :what-happened="errorMessage || t('home.history.loadFailed')"
      :data-status="t('home.history.dataKept')"
    >
      <template #action>
        <AppButton variant="secondary" @click="emit('retry')">{{ t('home.history.refresh') }}</AppButton>
      </template>
    </ErrorJourneyState>

    <div v-else class="trip-history__grid">
      <AppCard
        v-for="item in items"
        :key="item.plan_id"
        variant="interactive"
        class="trip-ticket"
        :ariaLabel="t('home.history.openNamed', { city: item.city || t('home.history.unknownPlace') })"
        @click="emit('open', item.plan_id)"
      >
        <div class="trip-ticket__inner">
          <div class="trip-ticket__date">
            <span>{{ dateLabel(item.start_date) }}</span>
          </div>
          <div class="trip-ticket__body">
            <p class="trip-ticket__city">{{ item.city || t('home.history.unknownPlace') }}</p>
            <p class="trip-ticket__summary">{{ item.overall_suggestions || t('home.history.noSummary') }}</p>
            <p class="trip-ticket__meta">
              {{ durationLabel(item) }}
              · {{ t('home.history.updatedAt') }} {{ formatHistoryTime(item.updated_at) }}
            </p>
          </div>
          <span class="trip-ticket__open">{{ t('home.history.open') }}</span>
        </div>
      </AppCard>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { TripHistoryItem } from '@/types'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppSectionHeader from '@/components/ui/AppSectionHeader.vue'
import ContentSkeleton from '@/components/feedback/ContentSkeleton.vue'
import EmptyJourneyState from '@/components/feedback/EmptyJourneyState.vue'
import ErrorJourneyState from '@/components/feedback/ErrorJourneyState.vue'

export type HistoryStatus = 'loading' | 'empty' | 'error' | 'success'

defineProps<{
  items: TripHistoryItem[]
  status: HistoryStatus
  errorMessage: string
}>()

const emit = defineEmits<{
  open: [planId: string]
  retry: []
  focusPlanner: []
}>()

const { t } = useI18n()

const formatHistoryTime = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return t('home.history.unknownTime')
  return date.toLocaleString()
}

const dateLabel = (value: string) => {
  if (!value) return t('home.history.noDate')
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return t('home.history.noDate')
  return value
}

const durationLabel = (item: TripHistoryItem) => {
  if (!item.travel_days) return t('home.history.noDuration')
  return t('home.totalDays', { n: item.travel_days })
}
</script>

<style scoped>
.trip-history {
  display: grid;
  gap: var(--space-6);
}

.trip-history__count {
  color: var(--color-text-muted);
  font-size: var(--text-body-s);
}

.trip-history__grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-4);
}

.trip-history__skeleton {
  min-height: 132px;
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.trip-ticket {
  width: 100%;
}

.trip-ticket__inner {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr) auto;
  gap: var(--space-4);
  align-items: center;
  padding: var(--space-4);
  min-width: 0;
}

.trip-ticket__date {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 88px;
  padding: var(--space-2);
  border-right: 1px dashed var(--color-border);
  color: var(--color-text-muted);
  font-size: var(--text-caption);
  text-align: center;
}

.trip-ticket__city {
  margin: 0 0 6px;
  font-size: var(--text-h3);
  font-weight: 650;
}

.trip-ticket__summary,
.trip-ticket__meta {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--text-body-s);
}

.trip-ticket__open {
  color: var(--color-primary);
  font-weight: 650;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}

@media (min-width: 768px) {
  .trip-history__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1024px) {
  .trip-history__grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 639px) {
  .trip-ticket__inner {
    grid-template-columns: 72px minmax(0, 1fr);
  }

  .trip-ticket__open {
    grid-column: 2;
  }
}
</style>
