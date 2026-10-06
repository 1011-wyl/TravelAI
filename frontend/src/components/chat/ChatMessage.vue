<template>
  <article
    class="chat-message"
    :class="[`is-${role}`, `is-${status}`]"
  >
    <p v-if="content" class="chat-message__body">{{ content }}</p>
    <div v-if="status === 'failed'" class="chat-message__fail">
      <p class="chat-message__error">{{ errorText }}</p>
      <AppButton variant="secondary" size="sm" :disabled="retrying" @click="emit('retry')">
        {{ retryLabel }}
      </AppButton>
    </div>
  </article>
</template>

<script setup lang="ts">
import AppButton from '@/components/ui/AppButton.vue'

export type ChatBubbleRole = 'user' | 'assistant'
export type ChatBubbleStatus = 'sent' | 'success' | 'failed'

defineProps<{
  role: ChatBubbleRole
  content: string
  status: ChatBubbleStatus
  errorText: string
  retryLabel: string
  retrying: boolean
}>()

const emit = defineEmits<{
  retry: []
}>()
</script>

<style scoped>
.chat-message {
  display: grid;
  gap: var(--space-2);
  max-width: 86%;
  min-width: 0;
}

.chat-message.is-user {
  margin-left: auto;
}

.chat-message.is-assistant {
  margin-right: auto;
}

.chat-message__body {
  margin: 0;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-size: 15px;
  line-height: 1.6;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
  user-select: text;
  color: var(--color-text);
}

.chat-message.is-user .chat-message__body {
  background: var(--color-primary-soft);
}

.chat-message.is-assistant .chat-message__body {
  background: var(--color-canvas-alt);
  border: 1px solid var(--color-border);
}

.chat-message__fail {
  display: grid;
  gap: var(--space-2);
  justify-items: start;
}

.chat-message__error {
  margin: 0;
  color: var(--color-error);
  font-size: var(--text-caption);
}
</style>
