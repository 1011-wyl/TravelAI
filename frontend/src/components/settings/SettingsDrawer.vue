<template>
  <a-drawer
    :open="open"
    class="settings-drawer"
    root-class-name="settings-drawer-root"
    placement="right"
    :width="420"
    :closable="false"
    :mask-closable="saveState !== 'saving'"
    :keyboard="saveState !== 'saving'"
    destroy-on-close
    @close="onRequestClose"
    @after-open-change="onAfterOpenChange"
  >
    <template #title>
      <div class="settings-drawer__head">
        <h2 id="settings-drawer-title" class="settings-drawer__title">{{ t('settings.title') }}</h2>
        <AppIconButton
          :ariaLabel="t('settings.close')"
          :disabled="saveState === 'saving'"
          @click="onRequestClose"
        >
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
          </svg>
        </AppIconButton>
      </div>
    </template>

    <div
      class="settings-drawer__body"
      :aria-busy="loading || undefined"
    >
      <p v-if="loading" class="sr-only">{{ t('common.loading') }}</p>

      <InlineNotice
        v-if="loadError"
        kind="error"
        :title="t('settings.messages.loadFailed')"
        :message="loadError"
      >
        <template #action>
          <AppButton variant="secondary" size="sm" :loading="loading" @click="loadSettings">
            {{ t('settings.retry') }}
          </AppButton>
        </template>
      </InlineNotice>

      <template v-else-if="loading">
        <ContentSkeleton variant="text" :lines="3" />
        <ContentSkeleton variant="list" :lines="4" />
      </template>

      <template v-else>
        <section class="settings-section">
          <AppSectionHeader :title="t('settings.sections.appearance')" :heading-level="2" />
          <div class="settings-field">
            <p class="settings-field__label">{{ t('app.appearance.theme') }}</p>
            <AppSegmentedControl
              :model-value="themePreference"
              :options="themeOptions"
              name="settings-theme"
              :ariaLabel="t('app.appearance.theme')"
              @update:model-value="onThemeChange"
            />
          </div>
          <div class="settings-field">
            <p class="settings-field__label">{{ t('app.appearance.motion') }}</p>
            <AppSegmentedControl
              :model-value="motionPreference"
              :options="motionOptions"
              name="settings-motion"
              :ariaLabel="t('app.appearance.motion')"
              @update:model-value="onMotionChange"
            />
          </div>
        </section>

        <section class="settings-section">
          <AppSectionHeader :title="t('settings.sections.language')" :heading-level="2" />
          <AppSegmentedControl
            :model-value="locale"
            :options="languageOptions"
            name="settings-language"
            :ariaLabel="t('app.language.label')"
            @update:model-value="onLocaleChange"
          />
        </section>

        <section class="settings-section">
          <AppSectionHeader
            :title="t('settings.sections.services')"
            :description="t('settings.sections.servicesHint')"
            :heading-level="2"
          />
          <a-form :model="settingsForm" layout="vertical" class="runtime-settings-form">
            <a-form-item name="api_base_url" :label="t('settings.labels.apiBaseUrl')">
              <a-input
                v-model:value="settingsForm.api_base_url"
                :placeholder="t('settings.placeholders.apiBaseUrl')"
                allow-clear
              />
            </a-form-item>
            <a-form-item name="vite_amap_web_js_key" :label="t('settings.labels.amapJsKey')">
              <SecretPeekInput v-model="settingsForm.vite_amap_web_js_key" />
            </a-form-item>
            <a-form-item name="vite_amap_web_key" :label="t('settings.labels.amapWebKey')">
              <SecretPeekInput v-model="settingsForm.vite_amap_web_key" />
            </a-form-item>
            <a-form-item name="google_maps_api_key" :label="t('settings.labels.googleMapsApiKey')">
              <SecretPeekInput
                v-model="settingsForm.google_maps_api_key"
                :placeholder="t('settings.placeholders.googleMapsApiKey')"
              />
            </a-form-item>
            <a-form-item name="google_maps_proxy" :label="t('settings.labels.googleMapsProxy')">
              <a-input
                v-model:value="settingsForm.google_maps_proxy"
                :placeholder="t('settings.placeholders.googleMapsProxy')"
                allow-clear
              />
            </a-form-item>
            <a-form-item name="openai_base_url" :label="t('settings.labels.openaiBaseUrl')">
              <a-input
                v-model:value="settingsForm.openai_base_url"
                :placeholder="t('settings.placeholders.openaiBaseUrl')"
                allow-clear
              />
            </a-form-item>
            <a-form-item name="openai_model" :label="t('settings.labels.openaiModel')">
              <a-input
                v-model:value="settingsForm.openai_model"
                :placeholder="t('settings.placeholders.openaiModel')"
                allow-clear
              />
            </a-form-item>
            <a-form-item name="openai_api_key" :label="t('settings.labels.openaiApiKey')">
              <SecretPeekInput v-model="settingsForm.openai_api_key" />
            </a-form-item>
            <a-form-item name="xhs_cookie" :label="t('settings.labels.xhsCookie')">
              <a-textarea
                v-model:value="settingsForm.xhs_cookie"
                :rows="4"
                :placeholder="t('settings.placeholders.xhsCookie')"
                allow-clear
              />
            </a-form-item>
          </a-form>
        </section>

        <InlineNotice
          v-if="saveState === 'error'"
          kind="error"
          :title="t('settings.messages.saveFailed')"
          :message="saveError"
        >
          <template #action>
            <AppButton variant="secondary" size="sm" @click="saveSettings">
              {{ t('settings.retry') }}
            </AppButton>
          </template>
        </InlineNotice>
      </template>
    </div>

    <template #footer>
      <div class="settings-drawer__footer">
        <AppButton variant="secondary" :disabled="saveState === 'saving'" @click="onRequestClose">
          {{ t('settings.cancel') }}
        </AppButton>
        <AppButton
          variant="primary"
          :disabled="loading || !!loadError"
          :loading="saveState === 'saving'"
          :success="saveState === 'saved'"
          @click="saveSettings"
        >
          {{ saveButtonLabel }}
        </AppButton>
      </div>
    </template>
  </a-drawer>
</template>

<script setup lang="ts">
import { computed, reactive, ref, toRef, watch } from 'vue'
import { useDrawerFocus } from '@/composables/useDrawerFocus'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import type { RuntimeSettings } from '@/types'
import { getRuntimeSettings, saveRuntimeSettings } from '@/services/api'
import { maskSecret } from '@/utils/secretMask'
import { useTheme } from '@/composables/useTheme'
import { useMotionPreference } from '@/composables/useMotionPreference'
import type { MotionPreference, ThemePreference } from '@/theme/preferences'
import type { AppLocale } from '@/i18n'
import AppButton from '@/components/ui/AppButton.vue'
import AppIconButton from '@/components/ui/AppIconButton.vue'
import AppSectionHeader from '@/components/ui/AppSectionHeader.vue'
import AppSegmentedControl from '@/components/ui/AppSegmentedControl.vue'
import InlineNotice from '@/components/feedback/InlineNotice.vue'
import ContentSkeleton from '@/components/feedback/ContentSkeleton.vue'
import SecretPeekInput from '@/components/settings/SecretPeekInput.vue'

type SaveState = 'idle' | 'saving' | 'saved' | 'error'

const props = defineProps<{
  open: boolean
}>()
const drawerFocus = useDrawerFocus(toRef(props, 'open'), '.settings-drawer-root', '.app-menu-trigger')

const emit = defineEmits<{
  close: []
}>()

const { t, locale } = useI18n()
const { themePreference, setThemePreference } = useTheme()
const { motionPreference, setMotionPreference } = useMotionPreference()

const loading = ref(false)
const loadError = ref('')
const saveState = ref<SaveState>('idle')
const saveError = ref('')
let savedTimer: number | null = null

const settingsForm = reactive<RuntimeSettings>({
  api_base_url: '',
  vite_amap_web_key: '',
  vite_amap_web_js_key: '',
  google_maps_api_key: '',
  google_maps_proxy: '',
  xhs_cookie: '',
  openai_api_key: '',
  openai_base_url: '',
  openai_model: '',
})

const themeOptions = computed(() => [
  { value: 'system' as ThemePreference, label: t('app.appearance.themeSystem') },
  { value: 'light' as ThemePreference, label: t('app.appearance.themeLight') },
  { value: 'dark' as ThemePreference, label: t('app.appearance.themeDark') },
])

const motionOptions = computed(() => [
  { value: 'system' as MotionPreference, label: t('app.appearance.motionSystem') },
  { value: 'reduce' as MotionPreference, label: t('app.appearance.motionReduce') },
  { value: 'full' as MotionPreference, label: t('app.appearance.motionFull') },
])

const languageOptions = computed(() => [
  { value: 'zh-CN', label: t('app.language.zh') },
  { value: 'en-US', label: t('app.language.en') },
  { value: 'ja-JP', label: t('app.language.ja') },
])

const saveButtonLabel = computed(() => {
  if (saveState.value === 'saved') return t('settings.saved')
  if (saveState.value === 'saving') return t('settings.saving')
  return t('settings.saveApply')
})

const applyRuntimeSettings = (settings: RuntimeSettings) => {
  settingsForm.api_base_url = settings.api_base_url || ''
  settingsForm.vite_amap_web_key = maskSecret(settings.vite_amap_web_key)
  settingsForm.vite_amap_web_js_key = maskSecret(settings.vite_amap_web_js_key)
  settingsForm.google_maps_api_key = maskSecret(settings.google_maps_api_key)
  settingsForm.google_maps_proxy = settings.google_maps_proxy || ''
  settingsForm.xhs_cookie = maskSecret(settings.xhs_cookie)
  settingsForm.openai_api_key = maskSecret(settings.openai_api_key)
  settingsForm.openai_base_url = settings.openai_base_url || ''
  settingsForm.openai_model = settings.openai_model || ''
}

const loadSettings = async () => {
  loading.value = true
  loadError.value = ''
  saveState.value = 'idle'
  saveError.value = ''
  try {
    const settings = await getRuntimeSettings()
    applyRuntimeSettings(settings)
  } catch (error: unknown) {
    const err = error as { message?: string }
    loadError.value = err?.message || t('settings.messages.loadFailed')
  } finally {
    loading.value = false
  }
}

const saveSettings = async () => {
  if (saveState.value === 'saving' || loading.value || loadError.value) return
  saveState.value = 'saving'
  saveError.value = ''
  try {
    const payload: RuntimeSettings = { ...settingsForm }
    const saved = await saveRuntimeSettings(payload)
    applyRuntimeSettings(saved)
    saveState.value = 'saved'
    message.success(t('settings.messages.saved'))
    if (savedTimer) window.clearTimeout(savedTimer)
    savedTimer = window.setTimeout(() => {
      saveState.value = 'idle'
      emit('close')
    }, 2000)
  } catch (error: unknown) {
    const err = error as { message?: string }
    saveState.value = 'error'
    saveError.value = err?.message || t('settings.messages.saveFailed')
  }
}

const onThemeChange = (value: string) => {
  setThemePreference(value as ThemePreference)
}

const onMotionChange = (value: string) => {
  setMotionPreference(value as MotionPreference)
}

const onLocaleChange = (value: string) => {
  locale.value = value as AppLocale
}

const onRequestClose = () => {
  if (saveState.value === 'saving') return
  emit('close')
}

const onAfterOpenChange = (visible: boolean) => {
  void drawerFocus.afterOpenChange(visible)
  if (!visible && savedTimer) {
    window.clearTimeout(savedTimer)
    savedTimer = null
  }
}

watch(
  () => props.open,
  (open) => {
    if (open) {
      void loadSettings()
    } else {
      saveState.value = 'idle'
      saveError.value = ''
      loadError.value = ''
    }
  }
)
</script>

<style scoped>
.settings-drawer__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.settings-drawer__title {
  margin: 0;
  font-size: var(--text-h3);
  line-height: var(--leading-h3);
}

.settings-drawer__body {
  display: grid;
  gap: var(--space-6);
}

.settings-section {
  display: grid;
  gap: var(--space-4);
}

.settings-field {
  display: grid;
  gap: var(--space-2);
}

.settings-field__label {
  margin: 0;
  font-size: var(--text-body-s);
  font-weight: 600;
}

.settings-drawer__footer {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.runtime-settings-form :deep(.ant-form-item) {
  margin-bottom: 12px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}

@media (max-width: 767px) {
  .settings-drawer__footer {
    position: sticky;
    bottom: 0;
  }
}
</style>
