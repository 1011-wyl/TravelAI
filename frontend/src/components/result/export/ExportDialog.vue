<template>
  <a-modal
    :open="open"
    :title="t('result.export.dialogTitle')"
    :footer="null"
    :mask-closable="!busy"
    :keyboard="!busy"
    destroy-on-close
    @cancel="onRequestClose"
  >
    <div class="export-dialog" :class="{ 'is-static': reduceMotion }" :aria-busy="busy || undefined">
      <template v-if="phase === 'options'">
        <p class="export-dialog__lead">{{ t('result.export.dialogLead') }}</p>
        <label class="export-dialog__option">
          <input v-model="includeMapModel" type="checkbox" />
          <span>{{ t('result.export.includeMap') }}</span>
        </label>
        <p class="export-dialog__hint">{{ t('result.export.includeMapHint') }}</p>
        <div class="export-dialog__actions">
          <AppButton variant="secondary" @click="emit('cancel')">{{ t('common.cancel') }}</AppButton>
          <AppButton variant="primary" @click="emit('confirm', includeMapModel)">
            {{ t('result.export.confirm') }}
          </AppButton>
        </div>
      </template>

      <template v-else-if="busy">
        <p class="export-dialog__status">{{ statusText }}</p>
        <div class="export-dialog__actions">
          <AppButton v-if="cancellable" variant="secondary" @click="emit('cancel')">
            {{ t('result.export.cancelWork') }}
          </AppButton>
        </div>
      </template>

      <template v-else-if="phase === 'map-failed'">
        <InlineNotice kind="warning" :title="t('result.export.mapFailedTitle')" :message="errorText" />
        <div class="export-dialog__actions">
          <AppButton variant="secondary" @click="emit('retry-map')">{{ t('result.export.retryMap') }}</AppButton>
          <AppButton variant="primary" @click="emit('continue-without-map')">
            {{ t('result.export.continueWithoutMap') }}
          </AppButton>
          <AppButton variant="ghost" @click="emit('cancel')">{{ t('common.cancel') }}</AppButton>
        </div>
      </template>

      <template v-else-if="phase === 'failed' || phase === 'oversized'">
        <InlineNotice
          kind="error"
          :title="phase === 'oversized' ? t('result.export.oversizedTitle') : t('result.export.failedTitle')"
          :message="errorText"
        />
        <div class="export-dialog__actions">
          <AppButton v-if="phase === 'failed'" variant="primary" @click="emit('retry')">
            {{ t('result.export.retry') }}
          </AppButton>
          <AppButton variant="secondary" @click="emit('cancel')">{{ t('common.cancel') }}</AppButton>
        </div>
      </template>

      <template v-else-if="phase === 'done'">
        <InlineNotice kind="success" :title="t('result.export.doneTitle')" :message="filename" />
        <div class="export-dialog__actions">
          <AppButton variant="primary" @click="emit('cancel')">{{ t('result.export.close') }}</AppButton>
        </div>
      </template>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import AppButton from '@/components/ui/AppButton.vue'
import InlineNotice from '@/components/feedback/InlineNotice.vue'
import type { ExportPhase } from '@/composables/useTripExport'

const props = defineProps<{
  open: boolean
  phase: ExportPhase
  includeMap: boolean
  errorText: string
  filename: string
  reduceMotion: boolean
}>()

const emit = defineEmits<{
  cancel: []
  confirm: [includeMap: boolean]
  retry: []
  'retry-map': []
  'continue-without-map': []
  'update:includeMap': [value: boolean]
}>()

const { t } = useI18n()

const includeMapModel = computed({
  get: () => props.includeMap,
  set: (value: boolean) => emit('update:includeMap', value),
})

const busy = computed(() =>
  ['preparing', 'images', 'map', 'rendering', 'downloading'].includes(props.phase)
)

const cancellable = computed(() => props.phase === 'preparing' || props.phase === 'images' || props.phase === 'map')

const statusText = computed(() => {
  if (props.phase === 'preparing') return t('result.export.stagePrepare')
  if (props.phase === 'images') return t('result.export.stageImages')
  if (props.phase === 'map') return t('result.export.stageMap')
  if (props.phase === 'rendering') return t('result.export.stageRender')
  if (props.phase === 'downloading') return t('result.export.stageDownload')
  return t('result.export.stagePrepare')
})

const onRequestClose = () => {
  if (busy.value && !cancellable.value) return
  emit('cancel')
}
</script>

<style scoped>
.export-dialog {
  display: grid;
  gap: var(--space-4);
}

.export-dialog__lead,
.export-dialog__hint,
.export-dialog__status {
  margin: 0;
  color: var(--color-text-muted);
}

.export-dialog__option {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: var(--control-h-md);
  cursor: pointer;
}

.export-dialog__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  justify-content: flex-end;
}

.export-dialog.is-static .export-dialog__status {
  animation: none;
}
</style>
