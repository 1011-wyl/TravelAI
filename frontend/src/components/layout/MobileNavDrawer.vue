<template>
  <a-drawer
    :open="open"
    id="mobile-nav-drawer"
    placement="bottom"
    height="auto"
    :closable="false"
    class="mobile-nav-drawer"
    root-class-name="mobile-nav-drawer-root"
    :body-style="{ padding: '0 0 16px' }"
    @close="emit('close')"
    @after-open-change="onAfterOpenChange"
  >
    <div class="mobile-nav-drawer__panel">
      <div class="mobile-nav-drawer__head">
        <p id="mobile-nav-drawer-title" class="mobile-nav-drawer__title">{{ t('app.nav.menu') }}</p>
        <button
          type="button"
          class="mobile-nav-drawer__close"
          :aria-label="t('app.nav.closeMenu')"
          @click="emit('close')"
        >
          ×
        </button>
      </div>
      <nav class="mobile-nav-drawer__nav" :aria-label="t('app.nav.primary')">
        <div ref="firstFocus">
          <RouterLink
            to="/"
            class="mobile-nav-drawer__link"
            :aria-current="isLanding ? 'page' : undefined"
            @click="emit('close')"
          >
            {{ t('app.nav.plan') }}
          </RouterLink>
        </div>
        <RouterLink
          to="/result"
          class="mobile-nav-drawer__link"
          :aria-current="isResult ? 'page' : undefined"
          @click="emit('close')"
        >
          {{ t('app.nav.trips') }}
        </RouterLink>
        <a
          class="mobile-nav-drawer__link"
          href="https://github.com/1sdv/TripStar"
          target="_blank"
          rel="noreferrer"
        >
          GitHub
        </a>
        <button type="button" class="mobile-nav-drawer__link" @click="emit('settings')">
          {{ t('settings.open') }}
        </button>
        <button type="button" class="mobile-nav-drawer__link" @click="emit('cta')">
          {{ t('home.nav.cta') }}
        </button>
      </nav>
    </div>
  </a-drawer>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, toRef } from 'vue'
import { useDrawerFocus } from '@/composables/useDrawerFocus'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  close: []
  cta: []
  settings: []
}>()

const { t } = useI18n()
const route = useRoute()
const firstFocus = ref<HTMLElement | null>(null)
const drawerFocus = useDrawerFocus(toRef(props, 'open'), '.mobile-nav-drawer-root')

const isLanding = computed(() => route.path === '/')
const isResult = computed(() => route.path === '/result')

const onAfterOpenChange = async (visible: boolean) => {
  await drawerFocus.afterOpenChange(visible)
  if (!visible) return
  await nextTick()
  firstFocus.value?.querySelector('a')?.focus()
}
</script>

<style scoped>
.mobile-nav-drawer__panel {
  padding: var(--space-4);
  padding-bottom: calc(var(--space-4) + env(safe-area-inset-bottom));
}

.mobile-nav-drawer__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.mobile-nav-drawer__title {
  margin: 0;
  font-size: var(--text-h3);
  font-weight: var(--weight-heading);
  color: var(--color-text);
}

.mobile-nav-drawer__close {
  width: var(--control-h-md);
  height: var(--control-h-md);
  border: 0;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text);
  font-size: 28px;
  line-height: 1;
  cursor: pointer;
}

.mobile-nav-drawer__nav {
  display: grid;
  gap: var(--space-2);
}

.mobile-nav-drawer__link {
  display: flex;
  align-items: center;
  min-height: var(--control-h-md);
  padding: 0 var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  text-decoration: none;
  font-size: var(--text-body);
  font-weight: 600;
  cursor: pointer;
}

.mobile-nav-drawer__link[aria-current='page'] {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
}
</style>
