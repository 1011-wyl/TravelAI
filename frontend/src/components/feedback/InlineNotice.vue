<template>
  <div
    class="inline-notice"
    :class="`inline-notice--${kind}`"
    :role="liveRole"
    :aria-live="livePoliteness"
  >
    <span class="inline-notice__icon" aria-hidden="true">
      <svg v-if="kind === 'info'" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.8" />
        <path d="M12 10.5v6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
        <circle cx="12" cy="7.5" r="1" fill="currentColor" />
      </svg>
      <svg v-else-if="kind === 'success'" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.8" />
        <path d="M8 12.2l2.6 2.6L16.2 9.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      <svg v-else-if="kind === 'warning'" viewBox="0 0 24 24" fill="none">
        <path d="M12 4l9 16H3L12 4z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
        <path d="M12 10v4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
        <circle cx="12" cy="17.2" r="1" fill="currentColor" />
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.8" />
        <path d="M9 9l6 6M15 9l-6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
      </svg>
    </span>
    <div class="inline-notice__body">
      <p class="inline-notice__title">{{ title }}</p>
      <p v-if="message" class="inline-notice__message">{{ message }}</p>
      <div v-if="$slots.action" class="inline-notice__action">
        <slot name="action" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export type InlineNoticeKind = 'info' | 'success' | 'warning' | 'error'

const props = withDefaults(
  defineProps<{
    kind?: InlineNoticeKind
    title: string
    message?: string
    urgent?: boolean
  }>(),
  {
    kind: 'info',
    message: '',
    urgent: false,
  }
)

const liveRole = computed(() => (props.urgent || props.kind === 'error' ? 'alert' : 'status'))
const livePoliteness = computed(() => (liveRole.value === 'alert' ? 'assertive' : 'polite'))
</script>

<style scoped>
.inline-notice {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.inline-notice__icon {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  color: var(--color-primary);
}

.inline-notice__icon svg {
  width: 22px;
  height: 22px;
}

.inline-notice__title {
  margin: 0;
  font-weight: 700;
  color: var(--color-text);
}

.inline-notice__message {
  margin: 6px 0 0;
  color: var(--color-text-muted);
  font-size: var(--text-body-s);
}

.inline-notice__action {
  margin-top: var(--space-3);
}

.inline-notice--success .inline-notice__icon { color: var(--color-success); }
.inline-notice--warning {
  background: var(--color-warning-soft);
  border-color: color-mix(in srgb, var(--color-warning) 35%, var(--color-border));
}
.inline-notice--warning .inline-notice__icon { color: var(--color-warning); }
.inline-notice--error {
  background: var(--color-error-soft);
  border-color: color-mix(in srgb, var(--color-error) 35%, var(--color-border));
}
.inline-notice--error .inline-notice__icon { color: var(--color-error); }
.inline-notice--info .inline-notice__icon { color: var(--color-info); }
</style>
