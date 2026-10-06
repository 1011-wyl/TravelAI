<template>
  <article
    class="itinerary-stop"
    :class="[`is-${kind}`, { 'is-enter': enterIndex >= 0 }]"
    :style="enterIndex >= 0 ? { '--stop-i': enterIndex } : undefined"
  >
    <div class="itinerary-stop__rail" aria-hidden="true">
      <span class="itinerary-stop__dot"></span>
    </div>
    <div class="itinerary-stop__body">
      <p class="itinerary-stop__kind">
        <span class="itinerary-stop__icon" aria-hidden="true">
          <svg v-if="kind === 'attraction'" viewBox="0 0 24 24" fill="none">
            <path d="M12 21s7-5.4 7-11a7 7 0 1 0-14 0c0 5.6 7 11 7 11z" stroke="currentColor" stroke-width="1.8" />
            <circle cx="12" cy="10" r="2.2" stroke="currentColor" stroke-width="1.8" />
          </svg>
          <svg v-else-if="kind === 'meal'" viewBox="0 0 24 24" fill="none">
            <path d="M5 4v8M5 12c0 3 3 4 3 8M9 4v6M19 5c-2.5 0-4 2-4 5v10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
          </svg>
          <svg v-else-if="kind === 'hotel'" viewBox="0 0 24 24" fill="none">
            <path d="M4 20V9l8-5 8 5v11" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
            <path d="M9 20v-6h6v6" stroke="currentColor" stroke-width="1.8" />
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none">
            <path d="M4 16h12l4-6H9L4 16z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
            <circle cx="8" cy="17.5" r="1.5" fill="currentColor" />
            <circle cx="15" cy="17.5" r="1.5" fill="currentColor" />
          </svg>
        </span>
        {{ kindLabel }}
      </p>
      <h4 class="itinerary-stop__title">{{ title }}</h4>
      <p v-if="place && !(editMode && kind === 'attraction')" class="itinerary-stop__meta">{{ place }}</p>
      <p v-if="durationLabel && !(editMode && kind === 'attraction')" class="itinerary-stop__meta">{{ durationLabel }}</p>
      <p v-if="priceLabel" class="itinerary-stop__meta">{{ priceLabel }}</p>
      <p v-for="(line, index) in extraLines" :key="index" class="itinerary-stop__meta">{{ line }}</p>
      <p v-if="note && !(editMode && kind === 'attraction')" class="itinerary-stop__note">{{ note }}</p>
      <div v-if="reservationRequired" class="itinerary-stop__alert">
        <strong>{{ t('result.itinerary.reservationRequired') }}</strong>
        <span v-if="reservationTips">{{ reservationTips }}</span>
      </div>

      <div v-if="imageSrc !== undefined" class="itinerary-stop__media" :class="{ 'is-failed': imageFailed, 'is-loading': imageLoading }">
        <img
          v-if="imageSrc && !imageFailed"
          :src="imageSrc"
          :alt="title"
          :loading="lazyImage ? 'lazy' : 'eager'"
          @load="imageLoading = false"
          @error="onImageError"
        />
        <div v-else class="itinerary-stop__fallback">{{ title }}</div>
      </div>

      <div v-if="editMode && kind === 'attraction'" class="itinerary-stop__edit">
        <label>
          {{ t('result.fieldAddress') }}
          <a-input :value="addressValue" @update:value="emit('update-address', String($event || ''))" />
        </label>
        <label>
          {{ t('result.fieldVisitDurationMinutes') }}
          <a-input-number
            :value="durationValue"
            :min="10"
            :max="480"
            @update:value="emit('update-duration', Number($event || 0))"
          />
        </label>
        <label>
          {{ t('result.fieldDescription') }}
          <a-textarea :value="note" :rows="2" @update:value="emit('update-note', String($event || ''))" />
        </label>
      </div>

      <div class="itinerary-stop__actions">
        <AppButton v-if="kind === 'attraction'" variant="secondary" @click="emit('view-map')">
          {{ t('result.itinerary.viewMap') }}
        </AppButton>
        <template v-if="editMode && kind === 'attraction'">
          <AppButton variant="secondary" :disabled="moveUpDisabled" @click="emit('move-up')">
            {{ t('result.itinerary.moveUp') }}
          </AppButton>
          <AppButton variant="secondary" :disabled="moveDownDisabled" @click="emit('move-down')">
            {{ t('result.itinerary.moveDown') }}
          </AppButton>
          <AppButton variant="danger" @click="emit('remove')">
            {{ t('common.delete') }}
          </AppButton>
        </template>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import AppButton from '@/components/ui/AppButton.vue'

export type ItineraryStopKind = 'attraction' | 'meal' | 'hotel' | 'transfer'

const props = withDefaults(
  defineProps<{
    kind: ItineraryStopKind
    title: string
    kindLabel: string
    place?: string
    durationLabel?: string
    priceLabel?: string
    extraLines?: string[]
    note?: string
    reservationRequired?: boolean
    reservationTips?: string
    imageSrc?: string
    lazyImage?: boolean
    editMode?: boolean
    addressValue?: string
    durationValue?: number
    moveUpDisabled?: boolean
    moveDownDisabled?: boolean
    enterIndex?: number
  }>(),
  {
    place: '',
    durationLabel: '',
    priceLabel: '',
    extraLines: () => [],
    note: '',
    reservationRequired: false,
    reservationTips: '',
    lazyImage: true,
    editMode: false,
    addressValue: '',
    durationValue: 0,
    moveUpDisabled: false,
    moveDownDisabled: false,
    enterIndex: -1,
  }
)

const emit = defineEmits<{
  'view-map': []
  remove: []
  'move-up': []
  'move-down': []
  'update-address': [value: string]
  'update-duration': [value: number]
  'update-note': [value: string]
}>()

const { t } = useI18n()
const imageFailed = ref(false)
const imageLoading = ref(Boolean(props.imageSrc))

watch(
  () => props.imageSrc,
  (src) => {
    imageFailed.value = false
    imageLoading.value = Boolean(src)
  }
)

const onImageError = () => {
  imageFailed.value = true
  imageLoading.value = false
}
</script>

<style scoped>
.itinerary-stop {
  display: grid;
  grid-template-columns: 20px minmax(0, 1fr);
  gap: var(--space-3);
}

.itinerary-stop__rail {
  position: relative;
  border-left: 2px solid var(--color-border);
  margin-left: 9px;
}

.itinerary-stop__dot {
  position: absolute;
  left: -6px;
  top: 8px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-canvas);
}

.itinerary-stop.is-meal .itinerary-stop__dot { background: var(--color-accent); }
.itinerary-stop.is-hotel .itinerary-stop__dot { background: var(--color-sand); }
.itinerary-stop.is-transfer .itinerary-stop__dot { background: var(--color-sky); }

.itinerary-stop__kind {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  margin: 0 0 var(--space-1);
  color: var(--color-text-muted);
  font-size: var(--text-caption);
  font-weight: 600;
}

.itinerary-stop__icon {
  width: 18px;
  height: 18px;
  color: var(--color-primary);
}

.itinerary-stop__icon svg {
  width: 18px;
  height: 18px;
  display: block;
}

.itinerary-stop__title {
  margin: 0;
  font-size: var(--text-h3);
  line-height: var(--leading-h3);
}

.itinerary-stop__meta,
.itinerary-stop__note {
  margin: var(--space-1) 0 0;
  color: var(--color-text-muted);
  white-space: pre-wrap;
}

.itinerary-stop__alert {
  display: grid;
  gap: 4px;
  margin-top: var(--space-2);
  padding: var(--space-3);
  border: 1px solid color-mix(in srgb, var(--color-warning) 35%, var(--color-border));
  border-radius: var(--radius-md);
  background: var(--color-warning-soft);
}

.itinerary-stop__media {
  margin-top: var(--space-3);
  aspect-ratio: 4 / 3;
  max-width: 420px;
  overflow: hidden;
  border-radius: var(--radius-md);
  background: var(--color-canvas-alt);
}

.itinerary-stop__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.itinerary-stop__fallback {
  display: grid;
  place-items: center;
  height: 100%;
  padding: var(--space-4);
  color: var(--color-text-muted);
  text-align: center;
}

.itinerary-stop__edit,
.itinerary-stop__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-3);
}

.itinerary-stop__edit {
  display: grid;
}

.itinerary-stop__edit label {
  display: grid;
  gap: var(--space-2);
  font-size: var(--text-body-s);
  font-weight: 600;
}

.itinerary-stop__media.is-loading {
  background: linear-gradient(90deg, var(--color-canvas-alt), var(--color-surface), var(--color-canvas-alt));
  background-size: 200% 100%;
  animation: stop-shimmer 1.6s linear infinite;
}

@keyframes stop-shimmer {
  from { background-position: 100% 0; }
  to { background-position: -100% 0; }
}

html[data-motion='reduce'] .itinerary-stop__media.is-loading {
  animation: none;
}

.itinerary-stop.is-enter {
  animation: stop-enter var(--duration-fast) var(--ease-standard) both;
  animation-delay: calc(var(--stop-i, 0) * 40ms);
}

@keyframes stop-enter {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

html[data-motion='reduce'] .itinerary-stop.is-enter {
  animation: none;
}
</style>
