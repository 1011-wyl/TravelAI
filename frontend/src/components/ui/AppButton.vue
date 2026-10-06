<template>
  <button
    :class="['app-button', `app-button--${variant}`, `app-button--${size}`, { 'is-loading': loading, 'is-disabled': disabled, 'is-success': success }]"
    :type="htmlType"
    :disabled="disabled || loading || success"
    :aria-busy="loading || undefined"
    :aria-disabled="disabled || loading || undefined"
    @click="onClick"
  >
    <span v-if="loading" class="app-button__loader" aria-hidden="true">
      <span></span><span></span><span></span>
    </span>
    <span v-else-if="success" class="app-button__icon" aria-hidden="true">✓</span>
    <span v-else-if="$slots.icon" class="app-button__icon" aria-hidden="true">
      <slot name="icon" />
    </span>
    <span class="app-button__label">
      <slot />
    </span>
  </button>
</template>

<script setup lang="ts">
export type AppButtonVariant = 'primary' | 'accent' | 'secondary' | 'ghost' | 'danger'
export type AppButtonSize = 'sm' | 'md' | 'lg'
export type AppButtonHtmlType = 'button' | 'submit' | 'reset'

const props = withDefaults(
  defineProps<{
    variant?: AppButtonVariant
    size?: AppButtonSize
    htmlType?: AppButtonHtmlType
    disabled?: boolean
    loading?: boolean
    success?: boolean
  }>(),
  {
    variant: 'primary',
    size: 'md',
    htmlType: 'button',
    disabled: false,
    loading: false,
    success: false,
  }
)

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const onClick = (event: MouseEvent) => {
  if (props.disabled || props.loading || props.success) {
    event.preventDefault()
    event.stopPropagation()
    return
  }
  emit('click', event)
}
</script>

<style scoped>
.app-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  font-weight: 600;
  font-family: inherit;
  line-height: 1;
  cursor: pointer;
  white-space: nowrap;
  transition:
    transform var(--duration-fast) var(--ease-standard),
    background-color var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard);
}

.app-button:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 75%, transparent);
  outline-offset: 2px;
}

.app-button--sm {
  min-height: var(--control-h-sm);
  padding: 0 12px;
  font-size: var(--text-body-s);
}

.app-button--md {
  min-height: var(--control-h-md);
  padding: 0 var(--space-4);
  font-size: var(--text-body-s);
}

.app-button--lg {
  min-height: var(--control-h-lg);
  padding: 0 22px;
  font-size: var(--text-body);
}

.app-button--sm .app-button__icon :deep(svg) { width: 16px; height: 16px; }
.app-button--md .app-button__icon :deep(svg) { width: 18px; height: 18px; }
.app-button--lg .app-button__icon :deep(svg) { width: 20px; height: 20px; }

.app-button--primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.app-button--primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
  transform: translateY(-1px);
}

.app-button--accent {
  background: var(--color-accent-strong);
  color: var(--color-on-accent);
}

.app-button--accent:hover:not(:disabled) {
  filter: brightness(1.03);
  transform: translateY(-1px);
}

.app-button--secondary {
  background: var(--color-surface);
  color: var(--color-text);
  border-color: var(--color-border);
}

.app-button--secondary:hover:not(:disabled) {
  border-color: var(--color-border-strong);
  transform: translateY(-1px);
}

.app-button--ghost {
  background: transparent;
  color: var(--color-text);
}

.app-button--ghost:hover:not(:disabled) {
  background: var(--color-primary-soft);
  transform: translateY(-1px);
}

.app-button--danger {
  background: var(--color-error);
  color: var(--color-on-error);
}

.app-button--danger:hover:not(:disabled) {
  filter: brightness(1.03);
  transform: translateY(-1px);
}

.app-button:active:not(:disabled) {
  transform: scale(0.985);
  transition-duration: var(--duration-instant);
}

.app-button:disabled,
.app-button.is-disabled,
.app-button.is-loading {
  opacity: 0.48;
  cursor: not-allowed;
  transform: none;
}

.app-button__loader {
  display: inline-flex;
  gap: 3px;
}

.app-button__loader span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: button-node 1.2s ease-in-out infinite;
}

.app-button__loader span:nth-child(2) { animation-delay: 120ms; }
.app-button__loader span:nth-child(3) { animation-delay: 240ms; }

@keyframes button-node {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

html[data-motion='reduce'] .app-button,
html[data-motion='reduce'] .app-button:hover,
html[data-motion='reduce'] .app-button:active {
  transform: none !important;
  transition: background-color 1ms linear, border-color 1ms linear, color 1ms linear !important;
}

html[data-motion='reduce'] .app-button__loader span {
  animation: none;
}
</style>
