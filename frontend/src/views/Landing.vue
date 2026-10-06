<template>
  <div class="landing">
    <div class="landing__stage">
      <TripHero class="landing__hero" />
      <div id="trip-planner" class="landing__planner">
        <TripPlannerForm
          v-if="!loading"
          :model-value="formData"
          :total-days="totalDays"
          :end-date="computedEndDate"
          :submitting="loading"
          @submit="handleSubmit"
          @update:cities="(value) => (formData.cities = value)"
          @update:start-date="(value) => (formData.start_date = value)"
          @update:transportation="(value) => (formData.transportation = value)"
          @update:accommodation="(value) => (formData.accommodation = value)"
          @update:preferences="(value) => (formData.preferences = value)"
          @update:free-text="(value) => (formData.free_text_input = value)"
        />
        <div v-else class="landing__live">
          <TripBrief v-if="submittedBrief" :snapshot="submittedBrief" />
          <PlanningJourney
            :stage="taskStage"
            :progress="loadingProgress"
            :status-message="loadingStatus"
            :plan-code="planCode"
            :elapsed-ms="elapsedMs"
            :completed="taskCompleted"
          />
        </div>
        <ErrorJourneyState
          v-if="generateError"
          class="landing__generate-error"
          :title="t('home.generateError.title')"
          :what-happened="generateError"
          :data-status="t('home.generateError.dataKept')"
        >
          <template #action>
            <div class="landing__error-actions">
              <AppButton variant="secondary" :disabled="loading" @click="focusPlanner">
                {{ t('home.generateError.edit') }}
              </AppButton>
              <AppButton variant="primary" :loading="loading" :disabled="loading" @click="handleSubmit">
                {{ t('home.generateError.retry') }}
              </AppButton>
            </div>
          </template>
        </ErrorJourneyState>
      </div>
    </div>

    <TripHistory
      class="landing__history"
      :items="historyPlans"
      :status="historyStatus"
      :error-message="historyError"
      @open="openHistoryPlan"
      @retry="loadHistoryPlans"
      @focus-planner="focusPlanner"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { generateTripPlan, getTripHistory } from '@/services/api'
import { getCurrentLocale } from '@/i18n'
import type { CityStay, TripFormData, TripHistoryItem, TripTaskStage } from '@/types'
import TripHero from '@/components/landing/TripHero.vue'
import TripPlannerForm from '@/components/landing/TripPlannerForm.vue'
import PlanningJourney from '@/components/landing/PlanningJourney.vue'
import TripHistory from '@/components/landing/TripHistory.vue'
import type { HistoryStatus } from '@/components/landing/TripHistory.vue'
import TripBrief from '@/components/trip/TripBrief.vue'
import ErrorJourneyState from '@/components/feedback/ErrorJourneyState.vue'
import AppButton from '@/components/ui/AppButton.vue'
import {
  MAX_TRAVEL_DAYS,
  createDefaultLandingForm,
  knownStageLabelKey,
  type TripBriefSnapshot,
} from '@/components/landing/landingModel'

const router = useRouter()
const { t } = useI18n()

const loading = ref(false)
const loadingProgress = ref(0)
const loadingStatus = ref('')
const planCode = ref('')
const taskStage = ref<TripTaskStage | ''>('')
const taskCompleted = ref(false)
const generateError = ref('')
const elapsedMs = ref(0)
const submittedBrief = ref<TripBriefSnapshot | null>(null)
const historyLoading = ref(false)
const historyPlans = ref<TripHistoryItem[]>([])
const historyError = ref('')
const formData = reactive(createDefaultLandingForm())

let elapsedTimer: number | null = null

const totalDays = computed(() => formData.cities.reduce((sum, item) => sum + (item.days || 1), 0))
const computedEndDate = computed(() => {
  if (!formData.start_date) return null
  return formData.start_date.add(totalDays.value - 1, 'day')
})
const historyStatus = computed<HistoryStatus>(() => {
  if (historyLoading.value) return 'loading'
  if (historyError.value) return 'error'
  if (historyPlans.value.length === 0) return 'empty'
  return 'success'
})

const stopElapsed = () => {
  if (elapsedTimer) {
    window.clearInterval(elapsedTimer)
    elapsedTimer = null
  }
}

const startElapsed = () => {
  stopElapsed()
  const startedAt = Date.now()
  elapsedMs.value = 0
  elapsedTimer = window.setInterval(() => {
    elapsedMs.value = Date.now() - startedAt
  }, 1000)
}

const openHistoryPlan = (planId: string) => {
  if (!planId) return
  sessionStorage.removeItem('tripPlan')
  sessionStorage.removeItem('graphData')
  sessionStorage.setItem('planId', planId)
  router.push({ path: '/result', query: { plan_id: planId } })
}

const loadHistoryPlans = async () => {
  historyLoading.value = true
  historyError.value = ''
  try {
    historyPlans.value = await getTripHistory(8)
  } catch (error: unknown) {
    const err = error as { message?: string }
    historyPlans.value = []
    historyError.value = err?.message || t('home.history.loadFailed')
  } finally {
    historyLoading.value = false
  }
}

const focusPlanner = () => {
  const planner = document.getElementById('trip-planner')
  planner?.scrollIntoView({ block: 'start' })
  planner?.querySelector<HTMLElement>('input, textarea, button')?.focus()
}

const toPublicGenerateError = (raw?: string) => {
  const text = (raw || '').trim()
  if (!text || text.length > 160 || /[\n\r]/.test(text)) {
    return t('home.messages.generateRetry')
  }
  if (/\b(at\s+\S+|traceback|stack|ECONNREFUSED|ENOENT|network error|timeout)\b/i.test(text)) {
    return t('home.messages.generateRetry')
  }
  if (/[/\\].+\.\w{2,4}/.test(text) || /localhost:\d+/i.test(text)) {
    return t('home.messages.generateRetry')
  }
  return text
}

const handleSubmit = async () => {
  if (loading.value) return

  const validCities = formData.cities.filter((item) => item.city.trim())
  if (validCities.length === 0) {
    message.error(t('home.atLeastOneCity'))
    return
  }
  if (!formData.start_date) {
    message.error(t('home.messages.selectDate'))
    return
  }
  if (totalDays.value > MAX_TRAVEL_DAYS) {
    message.warning(t('home.messages.travelDaysTooLong'))
    return
  }

  generateError.value = ''

  const endDate = computedEndDate.value!
  submittedBrief.value = {
    cities: validCities.map((item) => ({ city: item.city.trim(), days: item.days || 1 })),
    startDate: formData.start_date.format('YYYY-MM-DD'),
    endDate: endDate.format('YYYY-MM-DD'),
    travelDays: totalDays.value,
    transportation: formData.transportation,
    accommodation: formData.accommodation,
    preferences: [...formData.preferences],
  }

  loading.value = true
  loadingProgress.value = 5
  loadingStatus.value = t('home.loading.initializing')
  planCode.value = ''
  taskStage.value = 'initializing'
  taskCompleted.value = false
  startElapsed()

  try {
    sessionStorage.removeItem('tripPlan')
    sessionStorage.removeItem('graphData')
    sessionStorage.removeItem('planId')

    const citiesPayload: CityStay[] = validCities.map((item) => ({ city: item.city.trim(), days: item.days || 1 }))
    const requestData: TripFormData = {
      city: citiesPayload[0].city,
      cities: citiesPayload,
      start_date: formData.start_date.format('YYYY-MM-DD'),
      end_date: endDate.format('YYYY-MM-DD'),
      travel_days: totalDays.value,
      transportation: formData.transportation,
      accommodation: formData.accommodation,
      preferences: formData.preferences,
      free_text_input: formData.free_text_input,
      language: getCurrentLocale(),
    }

    const response = await generateTripPlan(requestData, {
      onTaskCreated: (task) => {
        planCode.value = task.plan_id || task.task_id
        loadingProgress.value = 5
        loadingStatus.value = t('home.loading.initializing')
        taskStage.value = 'submitted'
      },
      onTaskEvent: (event) => {
        if (event.plan_id) planCode.value = event.plan_id
        if (Number.isFinite(event.progress)) {
          loadingProgress.value = Math.max(0, Math.min(100, event.progress))
        }
        taskStage.value = event.stage
        const stageKey = knownStageLabelKey(event.stage)
        loadingStatus.value = event.message || (stageKey ? t(stageKey) : t('home.journey.neutral'))
      },
    })

    loadingProgress.value = 100
    loadingStatus.value = t('home.loading.done')
    taskStage.value = 'completed'
    taskCompleted.value = true

    if (response.success && response.data) {
      const planId = response.plan_id || planCode.value
      sessionStorage.setItem('tripPlan', JSON.stringify(response.data))
      if (response.graph_data) sessionStorage.setItem('graphData', JSON.stringify(response.graph_data))
      if (planId) sessionStorage.setItem('planId', planId)
      message.success(t('home.messages.generateSuccess'))
      setTimeout(() => {
        if (planId) {
          router.push({ path: '/result', query: { plan_id: planId } })
        } else {
          router.push('/result')
        }
      }, 500)
    } else {
      sessionStorage.removeItem('tripPlan')
      sessionStorage.removeItem('graphData')
      sessionStorage.removeItem('planId')
      taskCompleted.value = false
      generateError.value = toPublicGenerateError(response.message)
    }
  } catch (error: unknown) {
    const err = error as { message?: string }
    sessionStorage.removeItem('tripPlan')
    sessionStorage.removeItem('graphData')
    sessionStorage.removeItem('planId')
    taskCompleted.value = false
    generateError.value = toPublicGenerateError(err?.message)
  } finally {
    setTimeout(() => {
      loading.value = false
      loadingProgress.value = 0
      loadingStatus.value = ''
      taskStage.value = ''
      taskCompleted.value = false
      stopElapsed()
    }, 1000)
  }
}

onMounted(() => {
  void loadHistoryPlans()
})

onUnmounted(() => {
  stopElapsed()
})
</script>

<style scoped>
.landing {
  width: min(100%, var(--content-max));
  margin: 0 auto;
  padding: var(--space-8) var(--page-gutter) var(--space-16);
  display: grid;
  gap: var(--space-16);
  overflow-x: hidden;
}

.landing__stage {
  display: grid;
  gap: var(--space-8);
}

.landing__planner {
  scroll-margin-top: calc(var(--header-h) + 12px);
  min-width: 0;
}

.landing__live {
  display: grid;
  gap: var(--space-4);
}

.landing__generate-error {
  margin-top: var(--space-4);
}

.landing__error-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-2);
}

@media (min-width: 1024px) {
  .landing__stage {
    grid-template-columns: 5fr 7fr;
    align-items: start;
    gap: var(--space-12);
  }
}
</style>
