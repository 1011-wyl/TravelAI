<template>
  <button
    class="app-icon-button"
    :class="{ 'is-disabled': disabled }"
    type="button"
    :disabled="disabled"
    :aria-label="ariaLabel"
    :title="tooltip || ariaLabel"
    @click="onClick"
  >
    <span class="app-icon-button__glyph" aria-hidden="true">
      <slot />
    </span>
  </button>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    ariaLabel: string
    tooltip?: string
    disabled?: boolean
  }>(),
  {
    tooltip: '',
    disabled: false,
  }
)

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const onClick = (event: MouseEvent) => {
  if (props.disabled) {
    event.preventDefault()
    event.stopPropagation()
    return
  }
  emit('click', event)
}
</script>

<style scoped>
.app-icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--control-h-md);
  height: var(--control-h-md);
  min-width: var(--control-h-md);
  min-height: var(--control-h-md);
  padding: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
  transition:
    transform var(--duration-fast) var(--ease-standard),
    background-color var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard);
}

.app-icon-button:hover:not(:disabled) {
  border-color: var(--color-border-strong);
  transform: translateY(-1px);
}

.app-icon-button:active:not(:disabled) {
  transform: scale(0.985);
}

.app-icon-button:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 75%, transparent);
  outline-offset: 2px;
}

.app-icon-button:disabled {
  opacity: 0.48;
  cursor: not-allowed;
  transform: none;
}

.app-icon-button__glyph :deep(svg) {
  width: 18px;
  height: 18px;
  display: block;
}

html[data-motion='reduce'] .app-icon-button,
html[data-motion='reduce'] .app-icon-button:hover,
html[data-motion='reduce'] .app-icon-button:active {
  transform: none !important;
}
</style>
