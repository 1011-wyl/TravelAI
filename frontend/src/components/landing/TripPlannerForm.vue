<template>
  <a-form
    ref="formRef"
    class="trip-planner"
    :model="modelValue"
    layout="vertical"
    @finish="emit('submit')"
    @finish-failed="focusFirstInvalidField"
  >
    <section class="trip-planner__group">
      <h2 class="trip-planner__heading">{{ t('home.groups.where') }}</h2>
      <CityRouteEditor :cities="modelValue.cities" @update:cities="updateCities" />
    </section>

    <section class="trip-planner__group">
      <h2 class="trip-planner__heading">{{ t('home.groups.when') }}</h2>
      <div class="trip-planner__when">
        <a-form-item name="start_date" :rules="startDateRules">
          <template #label>
            <span>{{ t('home.startDateLabel') }}</span>
            <span class="req" aria-hidden="true">*</span>
            <span class="sr-only">{{ t('home.required') }}</span>
          </template>
          <a-date-picker
            :value="modelValue.start_date"
            class="trip-planner__control"
            style="width: 100%"
            :placeholder="t('home.startDatePlaceholder')"
            :aria-required="true"
            @update:value="updateStartDate"
          />
        </a-form-item>
        <div class="trip-planner__summary" aria-live="polite">
          <p>
            <span class="trip-planner__summary-label">{{ t('home.travelDaysLabel') }}</span>
            <strong>{{ t('home.totalDays', { n: totalDays }) }}</strong>
          </p>
          <p>
            <span class="trip-planner__summary-label">{{ t('home.endDateSummaryLabel') }}</span>
            <strong>{{ endDateLabel }}</strong>
          </p>
        </div>
      </div>
    </section>

    <section class="trip-planner__group">
      <h2 class="trip-planner__heading">{{ t('home.groups.how') }}</h2>
      <div class="trip-planner__prefs">
        <a-form-item name="transportation">
          <template #label>{{ t('home.transportationLabel') }}</template>
          <a-select
            :value="modelValue.transportation"
            class="trip-planner__control"
            @update:value="onTransportChange"
          >
            <a-select-option v-for="option in TRANSPORT_OPTIONS" :key="option.value" :value="option.value">
              {{ t(option.labelKey) }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item name="accommodation">
          <template #label>{{ t('home.accommodationLabel') }}</template>
          <a-select
            :value="modelValue.accommodation"
            class="trip-planner__control"
            @update:value="onStayChange"
          >
            <a-select-option v-for="option in ACCOMMODATION_OPTIONS" :key="option.value" :value="option.value">
              {{ t(option.labelKey) }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </div>
      <a-form-item name="preferences">
        <template #label>{{ t('home.interestsLabel') }}</template>
        <InterestSelector
          :model-value="modelValue.preferences"
          @update:model-value="(value) => emit('update:preferences', value)"
        />
      </a-form-item>
      <a-form-item name="free_text_input">
        <template #label>{{ t('home.specialNeedsLabel') }}</template>
        <a-textarea
          :value="modelValue.free_text_input"
          :placeholder="t('home.specialNeedsPlaceholder')"
          :rows="4"
          class="trip-planner__textarea"
          @update:value="(value: string) => emit('update:freeText', value)"
        />
      </a-form-item>
    </section>

    <AppButton
      class="trip-planner__submit"
      variant="accent"
      size="lg"
      html-type="submit"
      :loading="submitting"
      :disabled="submitting"
    >
      {{ submitting ? t('home.departing') : t('home.submit') }}
    </AppButton>
  </a-form>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Dayjs } from 'dayjs'
import AppButton from '@/components/ui/AppButton.vue'
import CityRouteEditor from '@/components/landing/CityRouteEditor.vue'
import InterestSelector from '@/components/landing/InterestSelector.vue'
import {
  ACCOMMODATION_OPTIONS,
  TRANSPORT_OPTIONS,
  type LandingCityStay,
  type LandingFormData,
} from '@/components/landing/landingModel'

const props = defineProps<{
  modelValue: LandingFormData
  totalDays: number
  endDate: Dayjs | null
  submitting: boolean
}>()

const emit = defineEmits<{
  submit: []
  'update:cities': [value: LandingCityStay[]]
  'update:startDate': [value: Dayjs | undefined]
  'update:transportation': [value: string]
  'update:accommodation': [value: string]
  'update:preferences': [value: string[]]
  'update:freeText': [value: string]
}>()

const { t } = useI18n()

const startDateRules = computed(() => [{ required: true, message: t('home.startDateRequired') }])
const endDateLabel = computed(() => (props.endDate ? props.endDate.format('YYYY-MM-DD') : t('home.endDatePending')))

const updateCities = (value: LandingCityStay[]) => emit('update:cities', value)
const updateStartDate = (value: Dayjs | string | undefined) => {
  emit('update:startDate', typeof value === 'string' ? undefined : value)
}

const formRef = ref<{ $el: HTMLElement } | null>(null)
const focusFirstInvalidField = async () => {
  await nextTick()
  const first = formRef.value?.$el.querySelector<HTMLElement>(
    '.ant-form-item-has-error input, .ant-form-item-has-error textarea, .ant-form-item-has-error [tabindex="0"]'
  )
  first?.focus()
  first?.scrollIntoView({ block: 'center', behavior: 'instant' })
}
const onTransportChange = (value: unknown) => {
  if (typeof value === 'string') emit('update:transportation', value)
}
const onStayChange = (value: unknown) => {
  if (typeof value === 'string') emit('update:accommodation', value)
}
</script>

<style scoped>
.trip-planner {
  display: grid;
  gap: var(--space-8);
  padding: 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-organic);
}

.trip-planner__group {
  display: grid;
  gap: var(--space-4);
}

.trip-planner__heading {
  margin: 0;
  color: var(--color-text);
  font-size: var(--text-h3);
  line-height: var(--leading-h3);
}

.trip-planner__when,
.trip-planner__prefs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.trip-planner__summary {
  display: grid;
  align-content: center;
  gap: var(--space-2);
  min-height: var(--control-h-lg);
  padding: var(--space-3) var(--space-4);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
}

.trip-planner__summary p {
  margin: 0;
}

.trip-planner__summary-label {
  display: block;
  color: var(--color-text-muted);
  font-size: var(--text-caption);
}

.trip-planner__control :deep(.ant-picker),
.trip-planner__control :deep(.ant-select-selector),
.trip-planner__textarea :deep(textarea) {
  min-height: var(--control-h-lg);
  font-size: 16px;
}

.trip-planner__submit {
  width: 100%;
  min-width: 220px;
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

@media (min-width: 768px) {
  .trip-planner {
    padding: var(--space-8);
  }

  .trip-planner__submit {
    width: auto;
    justify-self: start;
  }
}

@media (max-width: 639px) {
  .trip-planner__when,
  .trip-planner__prefs {
    grid-template-columns: 1fr;
  }
}
</style>
