<template>
  <div class="budget-table">
    <div class="budget-table__toolbar">
      <label>
        <span>{{ t('result.budget.filterLabel') }}</span>
        <a-select v-model:value="filterType" class="budget-table__select">
          <a-select-option value="all">{{ t('result.budget.filterAll') }}</a-select-option>
          <a-select-option value="attraction">{{ t('result.budget.attraction') }}</a-select-option>
          <a-select-option value="hotel">{{ t('result.budget.hotel') }}</a-select-option>
          <a-select-option value="meal">{{ t('result.budget.meal') }}</a-select-option>
          <a-select-option value="transport">{{ t('result.budget.transport') }}</a-select-option>
        </a-select>
      </label>
      <label>
        <span>{{ t('result.budget.sortLabel') }}</span>
        <a-select v-model:value="sortMode" class="budget-table__select">
          <a-select-option value="amountDesc">{{ t('result.budget.sortAmountDesc') }}</a-select-option>
          <a-select-option value="amountAsc">{{ t('result.budget.sortAmountAsc') }}</a-select-option>
          <a-select-option value="dayAsc">{{ t('result.budget.sortDayAsc') }}</a-select-option>
          <a-select-option value="dayDesc">{{ t('result.budget.sortDayDesc') }}</a-select-option>
        </a-select>
      </label>
    </div>

    <table v-if="items.length" class="budget-table__grid">
      <caption class="sr-only">{{ t('result.budget.tableCaption') }}</caption>
      <thead>
        <tr>
          <th scope="col">{{ t('result.budget.detailType') }}</th>
          <th scope="col">{{ t('result.budget.detailDay') }}</th>
          <th scope="col">{{ t('result.budget.detailName') }}</th>
          <th scope="col">{{ t('result.budget.detailAmount') }}</th>
          <th scope="col">{{ t('result.budget.detailAction') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td>{{ typeLabel(item.type) }}</td>
          <td>{{ item.dayNumber ? t('common.dayNumber', { day: item.dayNumber }) : '--' }}</td>
          <td>{{ item.name }}</td>
          <td class="budget-table__amount">¥{{ formatBudgetAmount(item.amount) }}</td>
          <td>
            <div class="budget-table__actions">
              <AppButton variant="secondary" @click="emit('edit', item)">
                {{ t('common.edit') }}
              </AppButton>
              <AppButton variant="danger" @click="emit('remove', item)">
                {{ t('common.delete') }}
              </AppButton>
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <ul v-if="items.length" class="budget-table__cards">
      <li v-for="item in items" :key="`card-${item.id}`">
        <p><span>{{ t('result.budget.detailType') }}</span> {{ typeLabel(item.type) }}</p>
        <p>
          <span>{{ t('result.budget.detailDay') }}</span>
          {{ item.dayNumber ? t('common.dayNumber', { day: item.dayNumber }) : '--' }}
        </p>
        <p><span>{{ t('result.budget.detailName') }}</span> {{ item.name }}</p>
        <p class="budget-table__amount">
          <span>{{ t('result.budget.detailAmount') }}</span>
          ¥{{ formatBudgetAmount(item.amount) }}
        </p>
        <div class="budget-table__actions">
          <AppButton variant="secondary" @click="emit('edit', item)">{{ t('common.edit') }}</AppButton>
          <AppButton variant="danger" @click="emit('remove', item)">{{ t('common.delete') }}</AppButton>
        </div>
      </li>
    </ul>

    <p v-else class="budget-table__empty">{{ t('result.budget.noDetails') }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import AppButton from '@/components/ui/AppButton.vue'
import {
  formatBudgetAmount,
  type BudgetDetailItem,
  type BudgetFilterType,
  type BudgetItemType,
  type BudgetSortMode,
} from '@/composables/useBudgetEditor'

const props = defineProps<{
  items: BudgetDetailItem[]
  filterType: BudgetFilterType
  sortMode: BudgetSortMode
  typeLabel: (type: BudgetItemType) => string
}>()

const emit = defineEmits<{
  'update:filterType': [value: BudgetFilterType]
  'update:sortMode': [value: BudgetSortMode]
  edit: [item: BudgetDetailItem]
  remove: [item: BudgetDetailItem]
}>()

const { t } = useI18n()

const filterType = computed({
  get: () => props.filterType,
  set: (value: BudgetFilterType) => emit('update:filterType', value),
})

const sortMode = computed({
  get: () => props.sortMode,
  set: (value: BudgetSortMode) => emit('update:sortMode', value),
})
</script>

<style scoped>
.budget-table__toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.budget-table__toolbar label {
  display: grid;
  gap: var(--space-2);
  font-size: var(--text-body-s);
  font-weight: 600;
}

.budget-table__select {
  min-width: 180px;
}

.budget-table__grid {
  width: 100%;
  border-collapse: collapse;
  font-variant-numeric: tabular-nums;
}

.budget-table__grid th,
.budget-table__grid td {
  padding: var(--space-3) var(--space-2);
  border-bottom: 1px solid var(--color-border);
  text-align: left;
  vertical-align: middle;
}

.budget-table__amount {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.budget-table__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.budget-table__cards {
  display: none;
  margin: 0;
  padding: 0;
  list-style: none;
  gap: var(--space-3);
}

.budget-table__cards p {
  margin: 0 0 var(--space-2);
}

.budget-table__cards p span {
  display: block;
  color: var(--color-text-muted);
  font-size: var(--text-caption);
}

.budget-table__empty {
  margin: 0;
  color: var(--color-text-muted);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}

@media (max-width: 767px) {
  .budget-table__grid {
    display: none;
  }

  .budget-table__cards {
    display: grid;
  }

  .budget-table__cards li {
    padding: var(--space-4);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background: var(--color-surface);
  }

  .budget-table__select {
    width: min(100%, 240px);
  }
}

@media (min-width: 768px) {
  .budget-table__cards {
    display: none;
  }
}
</style>
