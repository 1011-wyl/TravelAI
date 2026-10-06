<template>
  <section class="overview-section" aria-labelledby="result-section-heading">
    <p v-if="summary" class="overview-section__summary">{{ summary }}</p>
    <dl v-if="metrics.length" class="overview-section__metrics">
      <div v-for="metric in metrics" :key="metric.label">
        <dt>{{ metric.label }}</dt>
        <dd>{{ metric.value }}</dd>
      </div>
    </dl>
    <RoutePostcardRail
      v-if="attractions.length"
      :items="attractions"
      :image-src="imageSrc"
      @open-day="emit('open-day', $event)"
    />
    <p v-else>{{ t('common.noData') }}</p>
    <DailyOverviewList :days="plan.days" :plan-city="plan.city" @open-day="emit('open-day', $event)" />
    <TravelTipsPanel :plan="plan" />
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { TripPlan } from '@/types'
import RoutePostcardRail from '@/components/result/overview/RoutePostcardRail.vue'
import DailyOverviewList from '@/components/result/overview/DailyOverviewList.vue'
import TravelTipsPanel from '@/components/result/overview/TravelTipsPanel.vue'
import type { OverviewAttractionItem } from '@/components/result/overview/overviewModel'

const props = defineProps<{
  plan: TripPlan
  attractions: OverviewAttractionItem[]
  imageSrc: (item: OverviewAttractionItem, index: number) => string
}>()

const emit = defineEmits<{
  'open-day': [dayArrayIndex: number]
}>()

const { t } = useI18n()

const summary = computed(() => props.plan.overall_suggestions?.trim() || '')
const metrics = computed(() => {
  const items: Array<{ label: string; value: string }> = []
  if (props.plan.start_date && props.plan.end_date) {
    items.push({
      label: t('result.summary.dates'),
      value: t('result.dateRange', { start: props.plan.start_date, end: props.plan.end_date }),
    })
  }
  if (props.plan.days?.length) {
    items.push({
      label: t('result.summary.days'),
      value: t('common.dayCount', { count: props.plan.days.length }),
    })
  }
  if (Number.isFinite(Number(props.plan.budget?.total)) && Number(props.plan.budget?.total) > 0) {
    items.push({
      label: t('result.summary.budget'),
      value: `¥${props.plan.budget?.total}`,
    })
  }
  return items.slice(0, 3)
})
</script>

<style scoped>
.overview-section {
  display: grid;
  gap: var(--space-8);
}

.overview-section__summary {
  margin: 0;
  max-width: 68ch;
  font-size: var(--text-body-l);
  line-height: var(--leading-body-l);
}

.overview-section__metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--space-4);
  margin: 0;
}

.overview-section__metrics dt {
  color: var(--color-text-muted);
  font-size: var(--text-caption);
}

.overview-section__metrics dd {
  margin: 4px 0 0;
  font-weight: 650;
}
</style>
