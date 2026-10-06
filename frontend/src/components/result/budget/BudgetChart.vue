<template>
  <section class="budget-chart" :aria-label="t('result.budget.chartLabel')">
    <h3 class="budget-chart__title">{{ t('result.budget.chartTitle') }}</h3>
    <ul class="budget-chart__bars" v-if="slices.length">
      <li v-for="slice in slices" :key="slice.key">
        <div class="budget-chart__meta">
          <span class="budget-chart__swatch" :class="`is-${slice.key}`" aria-hidden="true"></span>
          <span>{{ slice.label }}</span>
          <span class="budget-chart__amount">¥{{ formatBudgetAmount(slice.amount) }}</span>
        </div>
        <div class="budget-chart__track" :aria-hidden="true">
          <div
            class="budget-chart__fill"
            :class="[`is-${slice.key}`, { 'is-negative': slice.amount < 0 }]"
            :style="{ width: barWidth(slice) }"
          ></div>
        </div>
      </li>
    </ul>
    <table class="budget-chart__table">
      <caption class="sr-only">{{ t('result.budget.chartTableCaption') }}</caption>
      <thead>
        <tr>
          <th scope="col">{{ t('result.budget.detailType') }}</th>
          <th scope="col">{{ t('result.budget.detailAmount') }}</th>
          <th scope="col">{{ t('result.budget.share') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="slice in slices" :key="`row-${slice.key}`">
          <th scope="row">{{ slice.label }}</th>
          <td>¥{{ formatBudgetAmount(slice.amount) }}</td>
          <td>{{ shareLabel(slice.share) }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { formatBudgetAmount, type BudgetCategorySlice } from '@/composables/useBudgetEditor'

defineProps<{
  slices: BudgetCategorySlice[]
}>()

const { t } = useI18n()

const barWidth = (slice: BudgetCategorySlice) => {
  if (slice.share == null) return '0%'
  return `${Math.min(100, slice.share * 100)}%`
}

const shareLabel = (share: number | null) => {
  if (share == null) return t('result.budget.shareUnavailable')
  return `${Math.round(share * 1000) / 10}%`
}
</script>

<style scoped>
.budget-chart {
  display: grid;
  gap: var(--space-4);
}

.budget-chart__title {
  margin: 0;
  font-size: var(--text-h3);
}

.budget-chart__bars {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: var(--space-3);
}

.budget-chart__meta {
  display: grid;
  grid-template-columns: 12px 1fr auto;
  gap: var(--space-2);
  align-items: center;
  font-size: var(--text-body-s);
}

.budget-chart__amount {
  font-variant-numeric: tabular-nums;
}

.budget-chart__swatch,
.budget-chart__fill {
  background: var(--color-text-muted);
}

.budget-chart__swatch {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.budget-chart__track {
  height: 10px;
  border-radius: var(--radius-pill);
  background: var(--color-canvas-alt);
  overflow: hidden;
}

.budget-chart__fill {
  height: 100%;
  min-width: 0;
}

.budget-chart__fill.is-negative {
  background: var(--color-error);
}

.is-attraction { background: var(--color-sand); }
.is-hotel { background: var(--color-primary); }
.is-meal { background: var(--color-accent); }
.is-transport { background: var(--color-sky); }
.is-shopping { background: #8E79B5; }
.is-interCity,
.is-other { background: var(--color-text-muted); }

html[data-theme='dark'] .is-shopping { background: #B7A4E5; }

.budget-chart__table {
  width: 100%;
  border-collapse: collapse;
  font-variant-numeric: tabular-nums;
}

.budget-chart__table th,
.budget-chart__table td {
  padding: var(--space-2) 0;
  border-bottom: 1px solid var(--color-border);
  text-align: left;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}
</style>
