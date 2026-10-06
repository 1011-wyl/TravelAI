<template>
  <a-config-provider :theme="antdTheme">
    <div class="app-shell">
      <a class="skip-link" href="#main-content">{{ t('app.skipToContent') }}</a>
      <div class="app-atmosphere" aria-hidden="true">
        <div class="app-atmosphere__glow"></div>
        <div class="app-atmosphere__topo"></div>
      </div>
      <NavBar />
      <main id="main-content" class="app-shell__main" tabindex="-1">
        <RouterView v-slot="{ Component }">
          <Transition name="route-fade">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </a-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import NavBar from '@/components/NavBar.vue'
import { useTheme } from '@/composables/useTheme'
import { useMotionPreference } from '@/composables/useMotionPreference'
import { createAntdTheme } from '@/theme/antdTheme'

const { t } = useI18n()
const { resolvedTheme } = useTheme()
const { resolvedMotion } = useMotionPreference()

const antdTheme = computed(() => createAntdTheme(resolvedTheme.value, resolvedMotion.value))
</script>

<style scoped>
.route-fade-enter-active,
.route-fade-leave-active {
  transition: opacity var(--duration-base) var(--ease-standard);
}

.route-fade-enter-from,
.route-fade-leave-to {
  opacity: 0;
}

html[data-motion='reduce'] .route-fade-enter-active,
html[data-motion='reduce'] .route-fade-leave-active {
  transition: none;
}
</style>
