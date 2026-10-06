<template>
  <section class="chat-empty" :aria-labelledby="titleId">
    <h3 :id="titleId" class="chat-empty__title">{{ title }}</h3>
    <p class="chat-empty__welcome">{{ welcome }}</p>
    <ul class="chat-empty__list">
      <li v-for="item in suggestions" :key="item.id">
        <button
          type="button"
          class="chat-empty__suggestion"
          :disabled="disabled"
          @click="emit('select', item.question)"
        >
          {{ item.label }}
        </button>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
export type ChatSuggestion = {
  id: string
  label: string
  question: string
}

defineProps<{
  titleId: string
  title: string
  welcome: string
  suggestions: ChatSuggestion[]
  disabled: boolean
}>()

const emit = defineEmits<{
  select: [question: string]
}>()
</script>

<style scoped>
.chat-empty {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-2) 0 var(--space-4);
}

.chat-empty__title,
.chat-empty__welcome {
  margin: 0;
  color: var(--color-text);
}

.chat-empty__title {
  font-size: var(--text-h3);
}

.chat-empty__welcome {
  color: var(--color-text-muted);
  font-size: var(--text-body);
  line-height: 1.6;
}

.chat-empty__list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: var(--space-2);
}

.chat-empty__suggestion {
  width: 100%;
  min-height: var(--control-h-md);
  text-align: left;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
}

.chat-empty__suggestion:disabled {
  opacity: 0.48;
  cursor: not-allowed;
}

.chat-empty__suggestion:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 75%, transparent);
  outline-offset: 2px;
}
</style>
