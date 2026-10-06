<template>
  <div
    class="app-segmented"
    role="radiogroup"
    :aria-label="ariaLabel"
    @keydown="onKeydown"
  >
    <label
      v-for="option in options"
      :key="String(option.value)"
      class="app-segmented__option"
      :class="{ 'is-checked': option.value === modelValue, 'is-disabled': disabled || option.disabled }"
    >
      <input
        class="app-segmented__input"
        type="radio"
        :name="groupName"
        :value="option.value"
        :checked="option.value === modelValue"
        :disabled="disabled || option.disabled"
        @change="select(option.value)"
      />
      <span class="app-segmented__label">{{ option.label }}</span>
    </label>
  </div>
</template>

<script setup lang="ts" generic="T extends string">
import { computed } from 'vue'

export type SegmentedOption<Value extends string = string> = {
  value: Value
  label: string
  disabled?: boolean
}

const props = withDefaults(
  defineProps<{
    modelValue: T
    options: SegmentedOption<T>[]
    disabled?: boolean
    ariaLabel: string
    name?: string
  }>(),
  {
    disabled: false,
    name: '',
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: T]
}>()

const groupName = computed(() => props.name || `segmented-${props.ariaLabel}`)

const enabledValues = computed(() => props.options.filter((item) => !item.disabled).map((item) => item.value))

const select = (value: T) => {
  if (props.disabled) return
  emit('update:modelValue', value)
}

const onKeydown = (event: KeyboardEvent) => {
  if (props.disabled) return
  if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft' && event.key !== 'ArrowDown' && event.key !== 'ArrowUp') {
    return
  }
  event.preventDefault()
  const values = enabledValues.value
  const index = values.indexOf(props.modelValue)
  if (index < 0 || values.length === 0) return
  const delta = event.key === 'ArrowRight' || event.key === 'ArrowDown' ? 1 : -1
  const next = values[(index + delta + values.length) % values.length]
  select(next)
}
</script>

<style scoped>
.app-segmented {
  display: inline-flex;
  flex-wrap: wrap;
  gap: var(--space-1);
  padding: var(--space-1);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-canvas-alt);
}

.app-segmented__option {
  position: relative;
  display: inline-flex;
  align-items: center;
  min-height: var(--control-h-md);
  padding: 0 var(--space-4);
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.app-segmented__input {
  position: absolute;
  inset: 0;
  z-index: 2;
  opacity: 0;
  margin: 0;
  cursor: inherit;
}

.app-segmented__label {
  position: relative;
  z-index: 1;
  pointer-events: none;
  font-size: var(--text-body-s);
  font-weight: 600;
  color: var(--color-text-muted);
}

.app-segmented__option.is-checked {
  background: var(--color-surface);
  box-shadow: var(--shadow-1);
  border: 2px solid var(--color-primary);
}

.app-segmented__option.is-checked .app-segmented__label {
  color: var(--color-text);
}

.app-segmented__option.is-checked .app-segmented__label::after {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-left: 8px;
  border-radius: 50%;
  background: var(--color-primary);
  vertical-align: middle;
}

.app-segmented__option.is-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.app-segmented__input:focus-visible + .app-segmented__label {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 75%, transparent);
  outline-offset: 2px;
}

html[data-motion='reduce'] .app-segmented__option {
  transition: none;
}
</style>
