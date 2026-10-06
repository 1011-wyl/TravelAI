<template>
  <a-checkbox-group class="interest-selector" :value="modelValue" @update:value="onChange">
    <label
      v-for="option in INTEREST_OPTIONS"
      :key="option.value"
      class="interest-selector__chip"
      :class="{ 'is-checked': modelValue.includes(option.value) }"
    >
      <a-checkbox :value="option.value">
        <span class="interest-selector__mark" aria-hidden="true">✓</span>
        {{ t(option.labelKey) }}
      </a-checkbox>
    </label>
  </a-checkbox-group>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { INTEREST_OPTIONS } from '@/components/landing/landingModel'

defineProps<{
  modelValue: string[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const { t } = useI18n()

const onChange = (value: Array<string | number | boolean>) => {
  emit('update:modelValue', value.map(String))
}
</script>

<style scoped>
.interest-selector {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.interest-selector__chip {
  display: inline-flex;
  min-height: var(--control-h-md);
  margin: 0;
  padding: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  background: var(--color-surface);
  cursor: pointer;
}

.interest-selector__chip:hover {
  background: var(--color-primary-soft);
}

.interest-selector__chip.is-checked {
  border-width: 2px;
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.interest-selector__chip :deep(.ant-checkbox-wrapper) {
  display: inline-flex;
  align-items: center;
  min-height: var(--control-h-md);
  padding: 0 14px;
  color: var(--color-text);
}

.interest-selector__chip :deep(.ant-checkbox) {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}

.interest-selector__mark {
  display: none;
  margin-right: 6px;
  color: var(--color-primary);
  font-weight: 700;
}

.interest-selector__chip.is-checked .interest-selector__mark {
  display: inline;
}

.interest-selector__chip :deep(.ant-checkbox-wrapper:focus-within) {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 75%, transparent);
  outline-offset: 2px;
  border-radius: var(--radius-pill);
}
</style>
