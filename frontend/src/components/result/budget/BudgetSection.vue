<template>
  <section class="budget-section" aria-labelledby="result-section-heading">
    <AppSectionHeader :title="t('result.budget.title')" :description="t('result.budget.description')" :heading-level="3" />

    <EmptyJourneyState
      v-if="!plan.budget"
      :title="t('result.budget.emptyTitle')"
      :description="t('result.budget.emptyDesc')"
    />

    <template v-else>
      <InlineNotice
        v-if="zeroTotal && items.length === 0"
        kind="info"
        :title="t('result.budget.zeroTitle')"
        :message="t('result.budget.zeroDesc')"
      />

      <BudgetSummary :plan="plan" :slices="slices" />
      <BudgetChart :slices="slices" />
      <BudgetTable
        :items="items"
        :filter-type="filterType"
        :sort-mode="sortMode"
        :type-label="typeLabel"
        @update:filter-type="emit('update:filterType', $event)"
        @update:sort-mode="emit('update:sortMode', $event)"
        @edit="openEdit"
        @remove="openDelete"
      />

      <InlineNotice
        v-if="undoItem"
        kind="success"
        :title="t('result.budget.undoTitle', { name: undoItem.base.name })"
        :message="t('result.budget.undoDesc')"
      >
        <template #action>
          <AppButton variant="secondary" @click="emit('undo')">{{ t('result.budget.restore') }}</AppButton>
        </template>
      </InlineNotice>
    </template>

    <BudgetItemModal
      :open="Boolean(editingItem)"
      :item="editingItem"
      :type-label="editingItem ? typeLabel(editingItem.type) : ''"
      :submitting="saving"
      @cancel="closeEdit"
      @confirm="saveEdit"
    />

    <a-modal
      :open="Boolean(deletingItem)"
      :title="deletingItem ? t('result.budget.deleteTitle', { name: deletingItem.name }) : t('common.delete')"
      :ok-text="t('common.delete')"
      :cancel-text="t('common.cancel')"
      ok-type="danger"
      :confirm-loading="saving"
      destroy-on-close
      @ok="confirmDelete"
      @cancel="closeDelete"
      @update:open="(next: boolean) => { if (!next) closeDelete() }"
    >
      <p>{{ deletingItem ? t('result.budget.deleteDesc', { name: deletingItem.name }) : '' }}</p>
    </a-modal>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import type { TripPlan } from '@/types'
import AppButton from '@/components/ui/AppButton.vue'
import AppSectionHeader from '@/components/ui/AppSectionHeader.vue'
import EmptyJourneyState from '@/components/feedback/EmptyJourneyState.vue'
import InlineNotice from '@/components/feedback/InlineNotice.vue'
import BudgetSummary from '@/components/result/budget/BudgetSummary.vue'
import BudgetChart from '@/components/result/budget/BudgetChart.vue'
import BudgetTable from '@/components/result/budget/BudgetTable.vue'
import BudgetItemModal from '@/components/result/budget/BudgetItemModal.vue'
import type {
  BudgetCategorySlice,
  BudgetDetailItem,
  BudgetFilterType,
  BudgetItemType,
  BudgetRestoreItem,
  BudgetSortMode,
} from '@/composables/useBudgetEditor'

const props = defineProps<{
  plan: TripPlan
  items: BudgetDetailItem[]
  slices: BudgetCategorySlice[]
  filterType: BudgetFilterType
  sortMode: BudgetSortMode
  undoItem: BudgetRestoreItem | null
  typeLabel: (type: BudgetItemType) => string
  applyAmount: (item: BudgetDetailItem, amount: unknown) => 'updated' | 'invalid' | 'unchanged' | 'missing'
  deleteItem: (item: BudgetDetailItem) => boolean
}>()

const emit = defineEmits<{
  'update:filterType': [value: BudgetFilterType]
  'update:sortMode': [value: BudgetSortMode]
  undo: []
}>()

const { t } = useI18n()
const editingItem = ref<BudgetDetailItem | null>(null)
const deletingItem = ref<BudgetDetailItem | null>(null)
const saving = ref(false)
const lastFocus = ref<HTMLElement | null>(null)

const zeroTotal = computed(() => Number(props.plan.budget?.total ?? 0) === 0)

const rememberFocus = () => {
  lastFocus.value = document.activeElement instanceof HTMLElement ? document.activeElement : null
}

const restoreFocus = () => {
  lastFocus.value?.focus()
  lastFocus.value = null
}

const openEdit = (item: BudgetDetailItem) => {
  rememberFocus()
  editingItem.value = item
}

const closeEdit = () => {
  editingItem.value = null
  saving.value = false
  restoreFocus()
}

const saveEdit = (amount: number) => {
  if (!editingItem.value || saving.value) return
  saving.value = true
  const result = props.applyAmount(editingItem.value, amount)
  saving.value = false
  if (result === 'invalid') {
    message.warning(t('result.messages.budgetInvalidAmount'))
    return
  }
  if (result === 'updated') {
    message.success(t('result.messages.budgetAmountUpdated'))
  }
  closeEdit()
}

const openDelete = (item: BudgetDetailItem) => {
  rememberFocus()
  deletingItem.value = item
}

const closeDelete = () => {
  deletingItem.value = null
  saving.value = false
  restoreFocus()
}

const confirmDelete = () => {
  if (!deletingItem.value || saving.value) return
  saving.value = true
  const ok = props.deleteItem(deletingItem.value)
  saving.value = false
  if (ok) {
    message.success(t('result.messages.budgetItemDeleted'))
  }
  closeDelete()
}
</script>

<style scoped>
.budget-section {
  display: grid;
  gap: var(--space-6);
}
</style>
