<template>
  <a-drawer
    id="result-ai-chat-panel"
    :open="open"
    class="chat-drawer"
    :root-class-name="compact ? 'chat-drawer-root chat-drawer-root--sheet' : 'chat-drawer-root'"
    :class="{ 'is-sheet': compact }"
    :placement="compact ? 'bottom' : 'right'"
    :width="compact ? '100%' : 440"
    :height="compact ? '100dvh' : undefined"
    :closable="false"
    :keyboard="true"
    :destroy-on-close="false"
    @close="closeChatPanel"
    @after-open-change="onAfterOpenChange"
  >
    <template #title>
      <div class="chat-drawer__head">
        <div class="chat-drawer__titles">
          <h2 id="chat-drawer-title" class="chat-drawer__title" tabindex="-1" ref="titleRef">
            {{ t('result.chat.title') }}
          </h2>
          <p v-if="tripSummary" class="chat-drawer__summary">{{ tripSummary }}</p>
        </div>
        <AppIconButton v-bind="closeBtnProps" @click="closeChatPanel">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
          </svg>
        </AppIconButton>
      </div>
    </template>

    <div class="chat-drawer__body">
      <div
        ref="logRef"
        class="chat-drawer__log"
        role="log"
        aria-live="off"
        aria-relevant="additions"
        aria-atomic="false"
        @scroll="onLogScroll"
      >
        <ChatEmptyState
          v-if="visibleMessages.length === 0 && !chatLoading"
          title-id="chat-empty-title"
          :title="t('result.chat.emptyTitle')"
          :welcome="t('result.chat.welcome')"
          :suggestions="suggestions"
          :disabled="chatLoading || !tripPlan"
          @select="sendQuickQuestion"
        />

        <ChatMessage
          v-for="item in visibleMessages"
          :key="item.id"
          :role="item.role"
          :content="item.content"
          :status="item.status"
          :error-text="item.errorText"
          :retry-label="t('result.chat.retry')"
          :retrying="chatLoading"
          @retry="retryLast"
        />

        <div v-if="chatLoading" class="chat-pending" aria-hidden="true">
          <span class="chat-pending__dot" :class="{ 'is-static': reduceMotion }" />
          <span class="chat-pending__dot" :class="{ 'is-static': reduceMotion }" />
          <span class="chat-pending__dot" :class="{ 'is-static': reduceMotion }" />
        </div>
      </div>

      <p class="sr-only" aria-live="polite">{{ liveStatus }}</p>

      <button
        v-if="showJump"
        type="button"
        class="chat-drawer__jump"
        @click="jumpToLatest"
      >
        {{ t('result.chat.jumpLatest') }}
      </button>

      <ChatComposer
        ref="composerRef"
        v-model="chatInput"
        input-id="chat-composer-input"
        :placeholder="chatPlaceholder"
        :label="t('result.chat.inputLabel')"
        :send-label="t('result.chat.send')"
        :disabled="chatLoading || !tripPlan"
        :compact="compact"
        @send="sendChatMessage"
      />
    </div>
  </a-drawer>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, toRef, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import type { ChatMessage as ChatHistoryItem, TripChatResponse, TripPlan } from '@/types'
import { getRuntimeApiBaseUrl } from '@/services/api'
import AppIconButton from '@/components/ui/AppIconButton.vue'
import ChatComposer from '@/components/chat/ChatComposer.vue'
import ChatEmptyState from '@/components/chat/ChatEmptyState.vue'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import type { ChatBubbleStatus } from '@/components/chat/ChatMessage.vue'
import { useMotionPreference } from '@/composables/useMotionPreference'
import { useDrawerFocus } from '@/composables/useDrawerFocus'

type DisplayMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  status: ChatBubbleStatus
  errorText: string
}

const props = withDefaults(
  defineProps<{
    tripPlan: TripPlan | null
    hideLauncher?: boolean
    planKey?: string
    open: boolean
  }>(),
  {
    hideLauncher: false,
    planKey: '',
  }
)

const emit = defineEmits<{
  'update:open': [value: boolean]
}>()

const { t } = useI18n()
const { reduceMotion } = useMotionPreference()
const drawerFocus = useDrawerFocus(toRef(props, 'open'), '.chat-drawer-root')
const chatInput = ref('')
const chatLoading = ref(false)
const compact = ref(false)
const stickToBottom = ref(true)
const showJump = ref(false)
const liveStatus = ref('')
const titleRef = ref<HTMLElement | null>(null)
const logRef = ref<HTMLElement | null>(null)
const composerRef = ref<{ focus: () => void } | null>(null)
const messages = ref<DisplayMessage[]>([])
let requestSeq = 0
let media: MediaQueryList | null = null
let messageSerial = 0

const nextId = () => {
  messageSerial += 1
  return `chat-${messageSerial}`
}

const suggestions = computed(() => [
  {
    id: 'price',
    label: t('result.chat.quickPriceLabel'),
    question: t('result.chat.quickPriceQuestion'),
  },
  {
    id: 'suitability',
    label: t('result.chat.quickSuitabilityLabel'),
    question: t('result.chat.quickSuitabilityQuestion'),
  },
  {
    id: 'meal',
    label: t('result.chat.quickMealLabel'),
    question: t('result.chat.quickMealQuestion'),
  },
])

const chatPlaceholder = computed(() => {
  if (!props.tripPlan) return t('result.noTripPlanDesc')
  return t('result.chat.placeholder')
})

const closeBtnProps = computed(() => ({
  ariaLabel: t('result.chat.close'),
}))

const tripSummary = computed(() => {
  const plan = props.tripPlan
  if (!plan) return ''
  const days = plan.days?.length || 0
  return t('result.chat.summary', {
    city: plan.city,
    start: plan.start_date || '',
    end: plan.end_date || '',
    days,
  })
})

const visibleMessages = computed(() => messages.value)

const successfulHistory = (): ChatHistoryItem[] => {
  return messages.value
    .filter((item) => item.status === 'sent' || item.status === 'success')
    .map((item) => ({ role: item.role, content: item.content }))
}

const scrollLog = (force: boolean) => {
  const el = logRef.value
  if (!el) return
  if (!force && !stickToBottom.value) {
    showJump.value = true
    return
  }
  showJump.value = false
  stickToBottom.value = true
  const top = el.scrollHeight
  if (reduceMotion.value) {
    el.scrollTop = top
    return
  }
  el.scrollTo({ top, behavior: 'smooth' })
}

const onLogScroll = () => {
  const el = logRef.value
  if (!el) return
  const gap = el.scrollHeight - el.scrollTop - el.clientHeight
  stickToBottom.value = gap < 72
  showJump.value = !stickToBottom.value
}

const jumpToLatest = () => {
  stickToBottom.value = true
  scrollLog(true)
}

const resetSession = () => {
  requestSeq += 1
  messages.value = []
  chatInput.value = ''
  chatLoading.value = false
  liveStatus.value = ''
  showJump.value = false
  stickToBottom.value = true
}

const askTrip = async (text: string) => {
  if (!props.tripPlan || chatLoading.value) return
  const history = successfulHistory().slice(0, -1)
  const seq = ++requestSeq
  chatLoading.value = true
  liveStatus.value = t('result.chat.generating')
  await nextTick()
  // Disabling the focused send control can move focus to body. Keep Esc and
  // the Drawer focus trap usable while the request is pending.
  if (document.activeElement === document.body || document.activeElement?.hasAttribute('disabled')) {
    titleRef.value?.focus()
  }
  scrollLog(stickToBottom.value)

  try {
    const apiBase = getRuntimeApiBaseUrl()
    const res = await axios.post<TripChatResponse>(`${apiBase}/api/chat/ask`, {
      message: text,
      trip_plan: props.tripPlan,
      history,
    })
    if (seq !== requestSeq) return
    if (res.data.success) {
      messages.value.push({
        id: nextId(),
        role: 'assistant',
        content: String(res.data.reply || ''),
        status: 'success',
        errorText: '',
      })
    } else {
      messages.value.push({
        id: nextId(),
        role: 'assistant',
        content: '',
        status: 'failed',
        errorText: t('result.chat.replyFallback'),
      })
    }
  } catch (err) {
    console.error('Chat error:', err)
    if (seq !== requestSeq) return
    messages.value.push({
      id: nextId(),
      role: 'assistant',
      content: '',
      status: 'failed',
      errorText: t('result.chat.networkError'),
    })
  } finally {
    if (seq === requestSeq) {
      chatLoading.value = false
      liveStatus.value = ''
      await nextTick()
      scrollLog(false)
    }
  }
}

const sendChatMessage = async () => {
  const text = chatInput.value.trim()
  if (!text || chatLoading.value || !props.tripPlan) return
  messages.value.push({
    id: nextId(),
    role: 'user',
    content: text,
    status: 'sent',
    errorText: '',
  })
  chatInput.value = ''
  stickToBottom.value = true
  await nextTick()
  scrollLog(true)
  await askTrip(text)
}

const sendQuickQuestion = (question: string) => {
  if (chatLoading.value || !props.tripPlan) return
  chatInput.value = question
  void sendChatMessage()
}

const retryLast = () => {
  if (chatLoading.value || !props.tripPlan) return
  const failed = [...messages.value].reverse().find((item) => item.status === 'failed')
  const lastUser = [...messages.value].reverse().find((item) => item.role === 'user' && item.status === 'sent')
  if (!failed || !lastUser) return
  messages.value = messages.value.filter((item) => item.id !== failed.id)
  void askTrip(lastUser.content)
}

const openChatPanel = () => {
  emit('update:open', true)
}

const closeChatPanel = () => {
  emit('update:open', false)
}

const onAfterOpenChange = (visible: boolean) => {
  void drawerFocus.afterOpenChange(visible)
  if (!visible) {
    emit('update:open', false)
    return
  }
  void nextTick(() => {
    composerRef.value?.focus()
    if (document.activeElement !== document.getElementById('chat-composer-input')) {
      titleRef.value?.focus()
    }
    scrollLog(true)
  })
}

const syncCompact = () => {
  compact.value = Boolean(media?.matches)
}

onMounted(() => {
  void props.hideLauncher
  media = window.matchMedia('(max-width: 767px)')
  syncCompact()
  media.addEventListener('change', syncCompact)
})

onUnmounted(() => {
  media?.removeEventListener('change', syncCompact)
  media = null
  requestSeq += 1
})

watch(
  () => props.planKey,
  (next, prev) => {
    // Reset as soon as plan switch starts (key may become empty before the next adopt).
    if (next === prev) return
    if (prev == null && !next) return
    if (prev !== undefined) resetSession()
  }
)

defineExpose({
  openChatPanel,
})
</script>

<style scoped>
.chat-drawer__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.chat-drawer__titles {
  min-width: 0;
}

.chat-drawer__title {
  margin: 0;
  font-size: var(--text-h3);
  color: var(--color-text);
}

.chat-drawer__summary {
  margin: var(--space-1) 0 0;
  color: var(--color-text-muted);
  font-size: var(--text-caption);
  overflow-wrap: anywhere;
}

.chat-drawer__body {
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  height: 100%;
  min-height: 0;
  position: relative;
}

.chat-drawer__log {
  min-height: 0;
  overflow: auto;
  display: grid;
  align-content: start;
  gap: var(--space-3);
  padding: var(--space-2) 2px var(--space-4);
}

.chat-pending {
  display: flex;
  gap: 6px;
  padding: var(--space-2) var(--space-3);
}

.chat-pending__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
  animation: chat-dot 960ms var(--ease-standard) infinite;
}

.chat-pending__dot:nth-child(2) {
  animation-delay: 160ms;
}

.chat-pending__dot:nth-child(3) {
  animation-delay: 320ms;
}

.chat-pending__dot.is-static {
  animation: none;
  opacity: 0.55;
}

.chat-drawer__jump {
  position: absolute;
  left: 50%;
  bottom: 6.5rem;
  transform: translateX(-50%);
  min-height: var(--control-h-md);
  padding: 0 var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface-raised);
  color: var(--color-text);
  box-shadow: var(--shadow-2);
  cursor: pointer;
}

.chat-drawer__jump:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 75%, transparent);
  outline-offset: 2px;
}

@keyframes chat-dot {
  0%,
  80%,
  100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  40% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .chat-pending__dot {
    animation: none;
  }

  .chat-drawer__jump {
    transform: translateX(-50%);
  }
}
</style>
