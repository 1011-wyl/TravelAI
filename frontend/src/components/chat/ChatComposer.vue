<template>
  <form class="chat-composer" @submit.prevent="emit('send')">
    <label class="sr-only" :for="inputId">{{ label }}</label>
    <textarea
      :id="inputId"
      ref="fieldRef"
      class="chat-composer__input"
      rows="1"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :aria-label="label"
      @input="onInput"
      @keydown="onKeydown"
      @compositionstart="composing = true"
      @compositionend="onCompositionEnd"
    />
    <AppButton
      class="chat-composer__send"
      variant="primary"
      html-type="submit"
      :disabled="disabled || !modelValue.trim()"
      :aria-label="sendLabel"
    >
      {{ sendLabel }}
    </AppButton>
  </form>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import AppButton from '@/components/ui/AppButton.vue'

const props = defineProps<{
  modelValue: string
  placeholder: string
  label: string
  sendLabel: string
  disabled: boolean
  compact: boolean
  inputId: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  send: []
}>()

const fieldRef = ref<HTMLTextAreaElement | null>(null)
const composing = ref(false)

const resize = () => {
  const field = fieldRef.value
  if (!field) return
  field.style.height = 'auto'
  const maxHeight = 16 * 1.6 * 5
  field.style.height = `${Math.min(field.scrollHeight, maxHeight)}px`
}

const onInput = (event: Event) => {
  const target = event.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
  void nextTick(resize)
}

const onCompositionEnd = (event: CompositionEvent) => {
  composing.value = false
  emit('update:modelValue', (event.target as HTMLTextAreaElement).value)
}

const onKeydown = (event: KeyboardEvent) => {
  if (event.key !== 'Enter' || event.shiftKey) return
  if (composing.value || event.isComposing || event.keyCode === 229) return
  // Phones in landscape can exceed the Sheet breakpoint. Touch input still
  // uses Enter for a newline; desktop keyboards retain Enter-to-send.
  if (props.compact || window.matchMedia('(pointer: coarse)').matches) return
  event.preventDefault()
  if (props.disabled || !props.modelValue.trim()) return
  emit('send')
}

watch(
  () => props.modelValue,
  () => {
    void nextTick(resize)
  }
)

const focus = () => {
  fieldRef.value?.focus()
}

defineExpose({ focus })
</script>

<style scoped>
.chat-composer {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--space-2);
  align-items: end;
  padding: var(--space-3);
  padding-bottom: calc(var(--space-3) + env(safe-area-inset-bottom));
  border-top: 1px solid var(--color-border);
  background: var(--color-surface);
}

.chat-composer__input {
  width: 100%;
  min-height: var(--control-h-md);
  max-height: 7.5rem;
  resize: none;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-canvas-alt);
  color: var(--color-text);
  font: inherit;
  font-size: 16px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}

.chat-composer__input:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 75%, transparent);
  outline-offset: 2px;
}

.chat-composer__send {
  min-width: var(--control-h-md);
  min-height: var(--control-h-md);
}
</style>
