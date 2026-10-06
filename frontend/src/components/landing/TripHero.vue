<template>
  <section class="trip-hero" aria-labelledby="trip-hero-title">
    <div class="trip-hero__topo" aria-hidden="true"></div>
    <p class="trip-hero__kicker">{{ t('home.heroBadge') }}</p>
    <h1 id="trip-hero-title" class="trip-hero__title">{{ t('home.heroTitle') }}</h1>
    <p class="trip-hero__desc">{{ t('home.heroDesc') }}</p>
    <svg class="trip-hero__route" viewBox="0 0 280 88" fill="none" aria-hidden="true">
      <path
        class="trip-hero__path"
        d="M18 62 C72 62, 88 22, 140 22 S198 70, 262 40"
        stroke="currentColor"
        stroke-width="2.4"
        stroke-linecap="round"
      />
      <circle cx="18" cy="62" r="7" fill="var(--color-primary)" />
      <circle class="trip-hero__sunrise" cx="140" cy="22" r="7" fill="var(--color-accent)" />
      <circle cx="262" cy="40" r="7" fill="var(--color-primary)" />
    </svg>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<style scoped>
.trip-hero {
  position: relative;
  display: grid;
  align-content: center;
  gap: var(--space-4);
  min-height: 280px;
  padding: var(--space-8) 0;
}

.trip-hero__topo {
  position: absolute;
  inset: 8% 8% auto 0;
  height: 72%;
  pointer-events: none;
  opacity: 0.55;
  background-image: url('../../assets/topographic-lines.svg');
  background-size: 320px 320px;
  mask-image: linear-gradient(90deg, rgba(0, 0, 0, 0.7), transparent 88%);
}

.trip-hero__kicker {
  position: relative;
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--text-body-s);
  font-weight: 600;
}

.trip-hero__title {
  position: relative;
  margin: 0;
  max-width: 12ch;
  color: var(--color-text);
  font-family: var(--font-serif);
  font-size: var(--text-display-xl);
  font-weight: var(--weight-display);
  line-height: var(--leading-display-xl);
}

.trip-hero__desc {
  position: relative;
  margin: 0;
  max-width: 34ch;
  color: var(--color-text-muted);
  font-size: var(--text-body-l);
  line-height: var(--leading-body-l);
}

.trip-hero__route {
  position: relative;
  width: min(280px, 100%);
  color: var(--color-primary);
}

.trip-hero__path {
  stroke-dasharray: 360;
  stroke-dashoffset: 360;
  animation: route-draw 720ms var(--ease-emphasized) forwards;
}

.trip-hero__sunrise {
  transform-box: fill-box;
  transform-origin: center;
}

@keyframes route-draw {
  to {
    stroke-dashoffset: 0;
  }
}

html[data-motion='reduce'] .trip-hero__path {
  animation: none;
  stroke-dashoffset: 0;
}
</style>
