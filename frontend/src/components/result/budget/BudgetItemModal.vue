<template>
  <a-modal
    :open="open"
    :title="title"
    :confirm-loading="submitting"
    :ok-text="t('common.save')"
    :cancel-text="t('common.cancel')"
    destroy-on-close
    @ok="onConfirm"
    @cancel="onCancel"
    @update:open="onOpenChange"
  >
    <form class="budget-item-form" @submit.prevent="onConfirm">
      <label class="budget-item-form__field">
        <span>{{ t('result.budget.detailType') }}</span>
        <input :value="typeLabel" readonly>
      </label>
      <label class="budget-item-form__field">
        <span>{{ t('result.budget.detailName') }}</span>
        <input :value="itemName" readonly>
      </label>
      <label class="budget-item-form__field">
        <span>{{ t('result.budget.detailAmount') }}</span>
        <a-input-number
          v-model:value="draftAmount"
          :min="0"
          :precision="2"
          :controls="false"
          inputmode="decimal"
          class="budget-item-form__amount"
          :status="error ? 'error' : undefined"
          :aria-invalid="error ? true : undefined"
        />
        <span v-if="error" class="budget-item-form__error">{{ error }}</span>
      </label>
    </form>
  </a-modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatBudgetAmount, type BudgetDetailItem } from '@/composables/useBudgetEditor'

const props = defineProps<{
  open: boolean
  item: BudgetDetailItem | null
  typeLabel: string
  submitting: boolean
}>()

const emit = defineEmits<{
  cancel: []
  confirm: [amount: number]
}>()

const { t } = useI18n()
const draftAmount = ref<number | undefined>(undefined)
const error = ref('')

const title = computed(() =>
  props.item ? t('result.budget.editTitle', { name: props.item.name }) : t('result.budget.editPrice')
)
const itemName = computed(() => props.item?.name || '')

watch(
  () => [props.open, props.item] as const,
  ([open, item]) => {
    if (!open || !item) return
    draftAmount.value = Number(formatBudgetAmount(item.amount))
    error.value = ''
  }
)

const onCancel = () => {
  error.value = ''
  emit('cancel')
}

const onOpenChange = (next: boolean) => {
  if (!next) onCancel()
}

const onConfirm = () => {
  if (props.submitting) return
  const numeric = Number(draftAmount.value)
  if (!Number.isFinite(numeric) || numeric < 0) {
    error.value = t('result.messages.budgetInvalidAmount')
    return
  }
  error.value = ''
  emit('confirm', numeric)
}
</script>

<style scoped>
.budget-item-form {
  display: grid;
  gap: var(--space-4);
}

.budget-item-form__field {
  display: grid;
  gap: var(--space-2);
  font-size: var(--text-body-s);
  font-weight: 600;
}

.budget-item-form__field input {
  min-height: var(--control-h-md);
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-canvas-alt);
  color: var(--color-text);
  font: inherit;
}

.budget-item-form__amount {
  width: 100%;
}

.budget-item-form__error {
  color: var(--color-error);
  font-weight: 500;
}
</style>
