<template>
  <dl class="budget-summary" :aria-label="t('result.budget.summaryLabel')">
    <div class="budget-summary__total">
      <dt>{{ t('result.budget.total') }}</dt>
      <dd>
        <span class="budget-summary__currency" aria-hidden="true">¥</span>
        <span class="budget-summary__value">{{ formatBudgetAmount(total) }}</span>
        <span class="sr-only">{{ t('result.budget.amountWithCurrency', { amount: formatBudgetAmount(total) }) }}</span>
      </dd>
    </div>
    <div v-for="slice in slices" :key="slice.key" class="budget-summary__sub">
      <dt>{{ slice.label }}</dt>
      <dd class="budget-summary__sub-value">¥{{ formatBudgetAmount(slice.amount) }}</dd>
    </div>
  </dl>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { TripPlan } from '@/types'
import { formatBudgetAmount, type BudgetCategorySlice } from '@/composables/useBudgetEditor'

const props = defineProps<{
  plan: TripPlan
  slices: BudgetCategorySlice[]
}>()

const { t } = useI18n()
const total = computed(() => Number(props.plan.budget?.total ?? 0))
</script>

<style scoped>
.budget-summary {
  display: grid;
  gap: var(--space-4);
  margin: 0;
}

.budget-summary__total dd {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  margin: var(--space-1) 0 0;
}

.budget-summary__currency {
  color: var(--color-text-muted);
  font-size: 14px;
}

.budget-summary__value {
  font-size: 36px;
  line-height: 1.1;
  font-weight: var(--weight-heading);
  font-variant-numeric: tabular-nums;
  color: var(--color-text);
  transition: color var(--duration-base) var(--ease-standard);
}

.budget-summary__sub {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
}

.budget-summary__sub dt {
  color: var(--color-text-muted);
  font-size: var(--text-body-s);
}

.budget-summary__sub-value {
  margin: 0;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}

html[data-motion='reduce'] .budget-summary__value {
  transition: none;
}

@media (min-width: 768px) {
  .budget-summary {
    grid-template-columns: minmax(200px, 1.2fr) repeat(auto-fit, minmax(120px, 1fr));
    align-items: end;
  }

  .budget-summary__total {
    grid-column: 1;
  }
}
</style>
