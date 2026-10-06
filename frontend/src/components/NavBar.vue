<template>
  <header class="app-header" :class="{ 'is-solid': isSolid }">
    <div class="app-header__inner">
      <button type="button" class="app-brand" @click="onBrandClick">
        <span class="app-brand__route" aria-hidden="true">
          <span class="app-brand__node"></span>
          <span class="app-brand__line"></span>
          <span class="app-brand__node app-brand__node--end"></span>
        </span>
        <span class="app-brand__name">{{ t('app.brand') }}</span>
      </button>

      <nav class="app-header__nav" :aria-label="t('app.nav.primary')">
        <RouterLink to="/" class="app-header__link" :aria-current="isLanding ? 'page' : undefined">
          {{ t('app.nav.plan') }}
        </RouterLink>
        <RouterLink to="/result" class="app-header__link" :aria-current="isResult ? 'page' : undefined">
          {{ t('app.nav.trips') }}
        </RouterLink>
      </nav>

      <div class="app-header__actions">
        <a
          class="app-icon-btn app-header__wide-only"
          href="https://github.com/1sdv/TripStar"
          target="_blank"
          rel="noreferrer"
          :aria-label="t('app.nav.github')"
        >
          <svg height="18" width="18" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
          </svg>
        </a>

        <label class="sr-only" for="app-language-select">{{ t('app.language.label') }}</label>
        <a-select
          id="app-language-select"
          v-model:value="locale"
          class="app-lang"
          size="middle"
          :aria-label="t('app.language.label')"
        >
          <a-select-option value="zh-CN">{{ t('app.language.zh') }}</a-select-option>
          <a-select-option value="ja-JP">{{ t('app.language.ja') }}</a-select-option>
          <a-select-option value="en-US">{{ t('app.language.en') }}</a-select-option>
        </a-select>

        <span class="app-header__wide-only">
          <a-dropdown trigger="click" placement="bottomRight">
            <button type="button" class="app-icon-btn" :aria-label="t('app.appearance.theme')">
              {{ themeShort }}
            </button>
            <template #overlay>
              <a-menu :selected-keys="[themePreference]" @click="onThemeMenu">
                <a-menu-item key="system">{{ t('app.appearance.themeSystem') }}</a-menu-item>
                <a-menu-item key="light">{{ t('app.appearance.themeLight') }}</a-menu-item>
                <a-menu-item key="dark">{{ t('app.appearance.themeDark') }}</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </span>

        <span class="app-header__wide-only">
          <a-dropdown trigger="click" placement="bottomRight">
            <button type="button" class="app-icon-btn" :aria-label="t('app.appearance.motion')">
              {{ motionShort }}
            </button>
            <template #overlay>
              <a-menu :selected-keys="[motionPreference]" @click="onMotionMenu">
                <a-menu-item key="system">{{ t('app.appearance.motionSystem') }}</a-menu-item>
                <a-menu-item key="reduce">{{ t('app.appearance.motionReduce') }}</a-menu-item>
                <a-menu-item key="full">{{ t('app.appearance.motionFull') }}</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </span>

        <span ref="settingsTrigger">
          <AppIconButton
            :ariaLabel="t('settings.open')"
            :tooltip="t('settings.open')"
            @click="openSettings"
          >
            <svg width="20" height="20" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
              <path fill="currentColor" d="M600.704 64a32 32 0 0 1 30.464 22.208l35.2 109.376c14.784 7.232 28.928 15.36 42.432 24.512l112.384-24.192a32 32 0 0 1 34.432 15.36L944.32 364.8a32 32 0 0 1-4.032 37.504l-77.12 85.12a357.12 357.12 0 0 1 0 49.024l77.12 85.248a32 32 0 0 1 4.032 37.504l-88.704 153.6a32 32 0 0 1-34.432 15.296L708.8 803.904c-13.44 9.088-27.648 17.28-42.368 24.512l-35.264 109.376A32 32 0 0 1 600.704 960H423.296a32 32 0 0 1-30.464-22.208L357.696 828.48a351.616 351.616 0 0 1-42.56-24.64l-112.32 24.256a32 32 0 0 1-34.432-15.36L79.68 659.2a32 32 0 0 1 4.032-37.504l77.12-85.248a357.12 357.12 0 0 1 0-48.896l-77.12-85.248A32 32 0 0 1 79.68 364.8l88.704-153.6a32 32 0 0 1 34.432-15.296l112.32 24.256c13.568-9.152 27.776-17.408 42.56-24.64l35.2-109.312A32 32 0 0 1 423.232 64H600.64zM512 320a192 192 0 1 1 0 384 192 192 0 0 1 0-384z"/>
            </svg>
          </AppIconButton>
        </span>

        <AppButton class="app-cta" variant="primary" @click="onCtaClick">
          {{ t('home.nav.cta') }}
        </AppButton>

        <button
          ref="menuTrigger"
          type="button"
          class="app-icon-btn app-menu-trigger"
          :aria-expanded="menuOpen"
          aria-controls="mobile-nav-drawer"
          :aria-label="t('app.nav.openMenu')"
          @click="menuOpen = true"
        >
          <span class="app-menu-trigger__bar"></span>
          <span class="app-menu-trigger__bar"></span>
          <span class="app-menu-trigger__bar"></span>
        </button>
      </div>
    </div>

    <MobileNavDrawer :open="menuOpen" @close="closeMenu" @cta="onMobileCta" @settings="openSettingsFromMenu" />
    <SettingsDrawer :open="settingsOpen" @close="closeSettings" />
  </header>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useTheme } from '@/composables/useTheme'
import { useMotionPreference } from '@/composables/useMotionPreference'
import MobileNavDrawer from '@/components/layout/MobileNavDrawer.vue'
import SettingsDrawer from '@/components/settings/SettingsDrawer.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppIconButton from '@/components/ui/AppIconButton.vue'
import { OPEN_SETTINGS_EVENT } from '@/composables/useTravelMap'
import type { MotionPreference, ThemePreference } from '@/theme/preferences'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const { themePreference, setThemePreference } = useTheme()
const { motionPreference, setMotionPreference, reduceMotion } = useMotionPreference()

const isSolid = ref(false)
const menuOpen = ref(false)
const menuTrigger = ref<HTMLButtonElement | null>(null)
const settingsTrigger = ref<HTMLElement | null>(null)
const settingsOpen = ref(false)

const isLanding = computed(() => route.path === '/')
const isResult = computed(() => route.path === '/result')
const themeShort = computed(() => {
  if (themePreference.value === 'light') return 'Aa'
  if (themePreference.value === 'dark') return 'A'
  return 'Auto'
})
const motionShort = computed(() => {
  if (motionPreference.value === 'reduce') return '–'
  if (motionPreference.value === 'full') return '≈'
  return 'Sys'
})

const updateSolid = () => {
  isSolid.value = window.scrollY > 24
}

onMounted(() => {
  updateSolid()
  window.addEventListener('scroll', updateSolid, { passive: true })
  window.addEventListener(OPEN_SETTINGS_EVENT, openSettings)
})

onUnmounted(() => {
  window.removeEventListener('scroll', updateSolid)
  window.removeEventListener(OPEN_SETTINGS_EVENT, openSettings)
})

const onBrandClick = () => {
  void router.push('/')
  window.scrollTo({ top: 0, behavior: reduceMotion.value ? 'auto' : 'smooth' })
}

const onCtaClick = () => {
  if (isLanding.value) {
    const target = document.getElementById('trip-planner')
    if (target) {
      const y = target.getBoundingClientRect().top + window.scrollY - 72
      window.scrollTo({ top: y, behavior: reduceMotion.value ? 'auto' : 'smooth' })
      return
    }
  }
  void router.push('/')
}

const onMobileCta = () => {
  menuOpen.value = false
  onCtaClick()
}

const closeMenu = () => {
  menuOpen.value = false
  menuTrigger.value?.focus()
}

const onThemeMenu = (info: { key: string | number }) => {
  setThemePreference(String(info.key) as ThemePreference)
}

const onMotionMenu = (info: { key: string | number }) => {
  setMotionPreference(String(info.key) as MotionPreference)
}

const openSettings = () => {
  settingsOpen.value = true
}

const openSettingsFromMenu = async () => {
  menuOpen.value = false
  await nextTick()
  window.setTimeout(() => {
    settingsOpen.value = true
  }, 220)
}

const closeSettings = async () => {
  settingsOpen.value = false
  await nextTick()
  settingsTrigger.value?.querySelector('button')?.focus()
}
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: var(--z-header);
  height: var(--header-h);
  background: transparent;
  border-bottom: 1px solid transparent;
  transition:
    background-color var(--duration-base) var(--ease-standard),
    border-color var(--duration-base) var(--ease-standard),
    box-shadow var(--duration-base) var(--ease-standard);
}

.app-header.is-solid {
  background: color-mix(in srgb, var(--color-surface) 88%, transparent);
  border-bottom-color: var(--color-border);
  box-shadow: var(--shadow-1);
  backdrop-filter: blur(16px);
}

.app-header__inner {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
  height: 100%;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 0 var(--page-gutter);
}

.app-brand {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  min-height: var(--control-h-md);
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--color-text);
  cursor: pointer;
}

.app-brand__route {
  display: inline-flex;
  align-items: center;
  width: 36px;
}

.app-brand__node {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
}

.app-brand__line {
  flex: 1;
  height: 2px;
  margin: 0 2px;
  background: var(--color-primary);
  transform-origin: left center;
  transition: transform var(--duration-fast) var(--ease-standard);
}

.app-brand:hover .app-brand__line {
  transform: translateX(2px);
}

.app-brand__name {
  font-size: 16px;
  font-weight: 650;
}

.app-header__nav {
  display: none;
  align-items: center;
  gap: var(--space-6);
  margin-left: var(--space-4);
}

.app-header__link {
  position: relative;
  display: inline-flex;
  align-items: center;
  min-height: var(--control-h-md);
  color: var(--color-text-muted);
  text-decoration: none;
  font-weight: 600;
}

.app-header__link[aria-current='page'] {
  color: var(--color-text);
}

.app-header__link[aria-current='page']::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: 10px;
  width: 24px;
  height: 2px;
  background: var(--color-primary);
  transform-origin: left center;
  transition: transform var(--duration-base) var(--ease-standard);
}

.app-header__actions {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  gap: var(--space-2);
  margin-left: auto;
}

.app-icon-btn {
  min-width: var(--control-h-md);
  min-height: var(--control-h-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.app-lang {
  width: 112px;
}

.app-menu-trigger {
  flex-direction: column;
  gap: 4px;
  display: none;
}

.app-menu-trigger__bar {
  display: block;
  width: 16px;
  height: 2px;
  background: currentColor;
}

@media (min-width: 768px) {
  .app-header__nav {
    display: flex;
  }

  .app-menu-trigger {
    display: none;
  }
}

@media (max-width: 767px) {
  .app-header__nav,
  :deep(.app-cta),
  .app-lang,
  .app-header__wide-only {
    display: none;
  }

  .app-menu-trigger {
    display: inline-flex;
  }

  .app-header__actions {
    gap: var(--space-1);
  }
}

html[data-motion='reduce'] .app-brand:hover .app-brand__line,
html[data-motion='reduce'] .app-header__link[aria-current='page']::after {
  transition: none;
}
</style>
