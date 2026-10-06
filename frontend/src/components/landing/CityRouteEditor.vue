<template>
  <div class="city-route">
    <p class="sr-only" aria-live="polite">{{ liveOrder }}</p>
    <ol class="city-route__list">
      <li v-for="(city, index) in cities" :key="index" class="city-route__item">
        <span class="city-route__rail" aria-hidden="true">
          <span class="city-route__node"></span>
          <span v-if="index < cities.length - 1" class="city-route__line"></span>
        </span>
        <div class="city-route__fields">
          <a-form-item
            :name="['cities', index, 'city']"
            :rules="[{ required: true, message: t('home.cityRequired') }]"
          >
            <template #label>
              <span>{{ t('home.cityNLabel', { n: index + 1 }) }}</span>
              <span class="req" aria-hidden="true">*</span>
              <span class="sr-only">{{ t('home.required') }}</span>
            </template>
            <a-input
              :value="city.city"
              :placeholder="t('home.cityPlaceholder')"
              class="city-route__control"
              :aria-required="true"
              @update:value="(value: string) => updateCity(index, value)"
            />
          </a-form-item>
          <a-form-item :name="['cities', index, 'days']">
            <template #label>{{ t('home.cityStayDays') }}</template>
            <a-input-number
              :value="city.days"
              :min="minDays"
              :max="maxDays"
              class="city-route__control"
              style="width: 100%"
              @update:value="(value) => updateDays(index, typeof value === 'number' ? value : null)"
            />
          </a-form-item>
        </div>
        <div class="city-route__actions">
          <AppIconButton
            :ariaLabel="t('home.moveCityUp')"
            :disabled="index === 0"
            @click="move(index, -1)"
          >
            <svg viewBox="0 0 24 24" fill="none"><path d="M6 14l6-6 6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </AppIconButton>
          <AppIconButton
            :ariaLabel="t('home.moveCityDown')"
            :disabled="index === cities.length - 1"
            @click="move(index, 1)"
          >
            <svg viewBox="0 0 24 24" fill="none"><path d="M6 10l6 6 6-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </AppIconButton>
          <AppIconButton
            :ariaLabel="t('home.removeCity')"
            :disabled="cities.length <= minCities"
            :tooltip="cities.length <= minCities ? t('home.cannotRemoveLastCity') : t('home.removeCity')"
            @click="remove(index)"
          >
            <svg viewBox="0 0 24 24" fill="none"><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
          </AppIconButton>
        </div>
      </li>
    </ol>
    <AppButton
      variant="secondary"
      :disabled="cities.length >= maxCities"
      @click="add"
    >
      {{ t('home.addCity') }}
    </AppButton>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import AppButton from '@/components/ui/AppButton.vue'
import AppIconButton from '@/components/ui/AppIconButton.vue'
import {
  DEFAULT_CITY_DAYS,
  MAX_CITIES,
  MAX_CITY_DAYS,
  MIN_CITIES,
  MIN_CITY_DAYS,
  type LandingCityStay,
} from '@/components/landing/landingModel'

const props = defineProps<{
  cities: LandingCityStay[]
}>()

const emit = defineEmits<{
  'update:cities': [value: LandingCityStay[]]
}>()

const { t } = useI18n()
const minCities = MIN_CITIES
const maxCities = MAX_CITIES
const minDays = MIN_CITY_DAYS
const maxDays = MAX_CITY_DAYS

const liveOrder = computed(() => {
  const names = props.cities.map((item) => item.city.trim()).filter(Boolean)
  if (names.length === 0) return ''
  return t('home.cityOrderAnnounced', { cities: names.join(t('home.cityOrderJoin')) })
})

const clone = () => props.cities.map((item) => ({ ...item }))

const updateCity = (index: number, value: string) => {
  const next = clone()
  next[index].city = value
  emit('update:cities', next)
}

const updateDays = (index: number, value: unknown) => {
  const next = clone()
  const days = typeof value === 'number' ? value : Number(value)
  next[index].days = Number.isFinite(days) && days >= MIN_CITY_DAYS ? days : DEFAULT_CITY_DAYS
  emit('update:cities', next)
}

const add = () => {
  if (props.cities.length >= MAX_CITIES) return
  emit('update:cities', [...clone(), { city: '', days: DEFAULT_CITY_DAYS }])
}

const remove = (index: number) => {
  if (props.cities.length <= MIN_CITIES) return
  const next = clone()
  next.splice(index, 1)
  emit('update:cities', next)
}

const move = (index: number, delta: number) => {
  const target = index + delta
  if (target < 0 || target >= props.cities.length) return
  const next = clone()
  const [item] = next.splice(index, 1)
  next.splice(target, 0, item)
  emit('update:cities', next)
}
</script>

<style scoped>
.city-route {
  display: grid;
  gap: var(--space-4);
}

.city-route__list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: var(--space-3);
}

.city-route__item {
  display: grid;
  grid-template-columns: 16px minmax(0, 1fr) auto;
  gap: var(--space-3);
  align-items: start;
}

.city-route__rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: var(--control-h-lg);
  padding-top: 34px;
}

.city-route__node {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-primary);
}

.city-route__line {
  flex: 1;
  width: 2px;
  min-height: 28px;
  margin-top: 6px;
  background: var(--color-border-strong);
}

.city-route__fields {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 120px;
  gap: var(--space-3);
  min-width: 0;
}

.city-route__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
  padding-top: 28px;
}

.city-route__control :deep(.ant-input),
.city-route__control :deep(.ant-input-number-input) {
  min-height: var(--control-h-lg);
  font-size: 16px;
}

.req {
  margin-left: 4px;
  color: var(--color-error);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}

@media (max-width: 639px) {
  .city-route__item {
    grid-template-columns: 16px minmax(0, 1fr);
  }

  .city-route__fields {
    grid-template-columns: 1fr;
  }

  .city-route__actions {
    grid-column: 2;
    padding-top: 0;
  }
}
</style>
