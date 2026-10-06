<template>
  <component
    :is="rootTag"
    class="app-card"
    :class="[
      `app-card--${variant}`,
      {
        'is-selected': selected,
        'is-disabled': disabled,
        'is-loading': loading,
        'is-interactive': isInteractive,
      },
    ]"
    v-bind="rootAttrs"
    @click="onClick"
  >
    <div v-if="loading" class="app-card__skeleton" aria-hidden="true"></div>
    <slot />
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

export type AppCardVariant = 'content' | 'interactive' | 'feature'

const props = withDefaults(
  defineProps<{
    variant?: AppCardVariant
    selected?: boolean
    disabled?: boolean
    loading?: boolean
    to?: string
    href?: string
    ariaLabel?: string
  }>(),
  {
    variant: 'content',
    selected: false,
    disabled: false,
    loading: false,
    to: '',
    href: '',
    ariaLabel: '',
  }
)

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const isInteractive = computed(() => props.variant === 'interactive' || props.variant === 'feature')

const rootTag = computed(() => {
  if (!isInteractive.value) return 'article'
  if (props.disabled) return 'div'
  if (props.to) return RouterLink
  if (props.href) return 'a'
  return 'button'
})

const rootAttrs = computed(() => {
  if (!isInteractive.value) return {}
  if (props.disabled) {
    return { 'aria-disabled': 'true', role: 'button' }
  }
  if (props.to) {
    return { to: props.to, 'aria-label': props.ariaLabel || undefined }
  }
  if (props.href) {
    return { href: props.href, 'aria-label': props.ariaLabel || undefined }
  }
  return {
    type: 'button',
    'aria-label': props.ariaLabel || undefined,
    'aria-pressed': props.selected || undefined,
  }
})

const onClick = (event: MouseEvent) => {
  if (props.disabled || props.loading || !isInteractive.value) return
  emit('click', event)
}
</script>

<style scoped>
.app-card {
  display: block;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: inherit;
  text-align: left;
  text-decoration: none;
  font: inherit;
  box-shadow: none;
}

.app-card--feature {
  border-radius: var(--radius-organic);
  overflow: hidden;
  position: relative;
}

.app-card--interactive,
.app-card--feature.is-interactive {
  cursor: pointer;
  transition:
    transform var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    background-color var(--duration-fast) var(--ease-standard);
}

.app-card--interactive:hover:not(.is-disabled),
.app-card--feature.is-interactive:hover:not(.is-disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-2);
}

.app-card--interactive:focus-visible,
.app-card--feature:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 75%, transparent);
  outline-offset: 2px;
}

.app-card.is-selected {
  border-width: 2px;
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.app-card.is-disabled {
  opacity: 0.48;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.app-card.is-loading {
  position: relative;
  min-height: 96px;
}

.app-card__skeleton {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--color-canvas-alt) 0%, var(--color-surface) 50%, var(--color-canvas-alt) 100%);
  background-size: 200% 100%;
  animation: card-shimmer 1.6s linear infinite;
}

@keyframes card-shimmer {
  from { background-position: 100% 0; }
  to { background-position: -100% 0; }
}

html[data-motion='reduce'] .app-card--interactive:hover,
html[data-motion='reduce'] .app-card--feature:hover {
  transform: none;
  box-shadow: none;
}

html[data-motion='reduce'] .app-card__skeleton {
  animation: none;
  background: var(--color-canvas-alt);
}
</style>
