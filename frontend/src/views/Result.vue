<template>
  <div class="result-page">
    <ResultStatePanel
      v-if="status !== 'ready' || !tripPlan"
      :status="panelStatus"
      @home="goBack"
      @retry="retryHydrate"
    />

    <div v-else class="result-page__shell">
      <TripSummaryHero :plan="tripPlan">
        <template #actions>
          <TripActionBar
            :exporting="exporting"
            :ask-open="chatOpen"
            ask-controls="result-ai-chat-panel"
            @back="goBack"
            @export="openExportDialog"
            @ask="chatOpen = true"
          />
        </template>
      </TripSummaryHero>

      <ResultSectionNav :model-value="publicSection" @update:model-value="onSelectSection" />

      <h2 id="result-section-heading" class="result-page__heading" tabindex="-1">{{ sectionHeading }}</h2>

      <div class="result-page__tools">
        <a-space size="middle" wrap>
          <a-button v-if="activeSection === 'map'" type="default" :loading="mapRefreshing" @click="refreshMap">
            {{ t('result.refreshMap') }}
          </a-button>
          <a-button v-if="!editMode" type="default" @click="toggleEditMode">{{ t('result.editTrip') }}</a-button>
          <a-button v-else type="primary" @click="saveChanges">{{ t('result.saveChanges') }}</a-button>
          <a-button v-if="editMode" type="default" @click="cancelEdit">{{ t('result.cancelEdit') }}</a-button>
        </a-space>
      </div>

      <OverviewSection
        v-show="activeSection === 'overview'"
        :plan="tripPlan"
        :attractions="overviewAttractions"
        :image-src="postcardImage"
        @open-day="goToDayFromOverview"
      />

      <BudgetSection
        v-show="activeSection === 'budget'"
        :plan="tripPlan"
        :items="filteredBudgetItems"
        :slices="budgetCategorySlices"
        :filter-type="budgetFilterType"
        :sort-mode="budgetSortMode"
        :undo-item="budgetUndoItem"
        :type-label="getBudgetTypeLabel"
        :apply-amount="applyBudgetAmount"
        :delete-item="deleteBudgetItem"
        @update:filter-type="budgetFilterType = $event"
        @update:sort-mode="budgetSortMode = $event"
        @undo="onBudgetUndo"
      />

      <MapSection v-if="activeSection === 'map'" ref="mapSectionRef" :plan="tripPlan" />

      <KnowledgeGraphSection
        v-if="activeSection === 'knowledge-graph'"
        :graph="graphData"
        :view-mode="graphViewMode"
        @update:view-mode="graphViewMode = $event"
      />

      <ItinerarySection
        v-show="activeSection === 'days'"
        :plan="tripPlan"
        :plan-key="planUiKey"
        :edit-mode="editMode"
        :image-src="itineraryImage"
        :focus-day-index="itineraryFocusDay"
        :focus-nonce="itineraryFocusNonce"
        :active="activeSection === 'days'"
        @view-map="openMapFromItinerary"
        @delete-attraction="deleteAttraction"
        @move-attraction="moveAttraction"
        @update-attraction="updateAttractionField"
      />

      <WeatherSection
        v-show="activeSection === 'weather'"
        :items="tripPlan.weather_info || []"
        :fallback-city="tripPlan.city"
      />
    </div>

    <TripActionBar
      v-if="status === 'ready' && tripPlan"
      class="result-page__mobile-bar"
      sticky
      :exporting="exporting"
      :ask-open="chatOpen"
      ask-controls="result-ai-chat-panel"
      @back="goBack"
      @export="openExportDialog"
      @ask="chatOpen = true"
    />

    <a-back-top :visibility-height="300">
      <div class="back-top-button">Top</div>
    </a-back-top>

    <AIChat
      hide-launcher
      :open="chatOpen"
      :trip-plan="tripPlan"
      :plan-key="planUiKey"
      @update:open="chatOpen = $event"
    />

    <ResultExportPanel
      ref="exportPanelRef"
      :plan="tripPlan"
      :photos="attractionPhotos"
      :plan-key="planUiKey"
      :reduce-motion="reduceMotion"
      :resolve-photo="resolvePhoto"
      :get-visible-map-element="() => mapSectionRef?.getMapElement() || null"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import AIChat from '@/components/AIChat.vue'
import TripSummaryHero from '@/components/result/TripSummaryHero.vue'
import TripActionBar from '@/components/result/TripActionBar.vue'
import ResultSectionNav from '@/components/result/ResultSectionNav.vue'
import ResultStatePanel from '@/components/result/ResultStatePanel.vue'
import OverviewSection from '@/components/result/overview/OverviewSection.vue'
import BudgetSection from '@/components/result/budget/BudgetSection.vue'
import ItinerarySection from '@/components/result/itinerary/ItinerarySection.vue'
import WeatherSection from '@/components/result/weather/WeatherSection.vue'
import MapSection from '@/components/result/map/MapSection.vue'
import KnowledgeGraphSection from '@/components/result/graph/KnowledgeGraphSection.vue'
import ResultExportPanel from '@/components/result/export/ResultExportPanel.vue'
import { toOverviewAttractionItems, type OverviewAttractionItem } from '@/components/result/overview/overviewModel'
import { normalizeQueryPlanId, useTripPlanState } from '@/composables/useTripPlanState'
import { useBudgetEditor } from '@/composables/useBudgetEditor'
import { useMotionPreference } from '@/composables/useMotionPreference'
import { useResultSection } from '@/composables/useResultSection'
import { useAttractionPhotos } from '@/composables/useAttractionPhotos'
import { useItineraryEditor } from '@/composables/useItineraryEditor'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const {
  tripPlan,
  graphData,
  planSourceKey,
  status,
  applyTripPlanPayload: writePlanState,
  hydrate,
} = useTripPlanState()

const chatOpen = ref(false)
const mapSectionRef = ref<{
  refresh: () => Promise<void>
  invalidate: () => void
  getMapElement: () => HTMLElement | null
} | null>(null)
const mapRefreshing = ref(false)
const graphViewMode = ref<'graph' | 'list' | null>(null)
const exportPanelRef = ref<{ exporting: boolean; openDialog: () => void } | null>(null)
/** Isolation key from plan adoption version; empty while switching/loading. */
const planUiKey = planSourceKey
const { reduceMotion } = useMotionPreference()
const { attractionPhotos, getAttractionImage, itineraryImage, resolvePhoto, loadAttractionPhotos } =
  useAttractionPhotos({ plan: tripPlan, planKey: planUiKey })

const exporting = computed(() => exportPanelRef.value?.exporting ?? false)
const openExportDialog = () => exportPanelRef.value?.openDialog()
const overviewAttractions = computed(() => (tripPlan.value ? toOverviewAttractionItems(tripPlan.value) : []))
const postcardImage = (item: OverviewAttractionItem, index: number) => getAttractionImage(item.name, index)
const {
  publicSection,
  activeSection,
  sectionHeading,
  onSelectSection,
  goToDayFromOverview,
  openMapFromItinerary,
  itineraryFocusDay,
  itineraryFocusNonce,
  focusSectionHeading,
} = useResultSection()
const panelStatus = computed(() => (status.value === 'ready' ? 'missing' : status.value))

const {
  filterType: budgetFilterType,
  sortMode: budgetSortMode,
  undoItem: budgetUndoItem,
  filteredBudgetItems,
  categorySlices: budgetCategorySlices,
  getBudgetTypeLabel,
  recalculateBudgetTotals,
  applyAmount: applyBudgetAmount,
  deleteItem: deleteBudgetItem,
  restoreUndo: restoreBudgetItem,
  clearUndo: clearBudgetUndo,
} = useBudgetEditor(tripPlan, {
  persist: () => {
    if (tripPlan.value) sessionStorage.setItem('tripPlan', JSON.stringify(tripPlan.value))
  },
  onLinkedChange: () => mapSectionRef.value?.invalidate(),
})

const onBudgetUndo = () => {
  if (restoreBudgetItem()) message.success(t('result.messages.budgetItemRestored'))
}

const refreshMap = async () => {
  if (mapRefreshing.value) return
  mapRefreshing.value = true
  try {
    await mapSectionRef.value?.refresh()
  } catch (error) {
    console.error('刷新地图失败:', error)
    message.error(t('result.messages.mapLoadFailed'))
  } finally {
    mapRefreshing.value = false
  }
}

const {
  editMode,
  toggleEditMode,
  saveChanges,
  cancelEdit,
  discardEdit,
  deleteAttraction,
  moveAttraction,
  updateAttractionField,
} = useItineraryEditor(tripPlan, {
  persistPlan: (plan) => writePlanState({ plan }),
  recalculateBudgetTotals,
  clearBudgetUndo,
  onSaved: () => {
    if (activeSection.value === 'map') void refreshMap()
  },
})

const afterPlanReady = async () => {
  clearBudgetUndo()
  if (status.value === 'ready' && tripPlan.value) await loadAttractionPhotos()
}

const runHydrate = async () => {
  await hydrate(route.query.plan_id)
  await afterPlanReady()
}

watch(
  () => normalizeQueryPlanId(route.query.plan_id),
  () => {
    void runHydrate()
  },
  { immediate: true }
)

watch(activeSection, async () => {
  if (tripPlan.value) await focusSectionHeading()
})

watch(planSourceKey, (next, prev) => {
  if (next === prev) return
  discardEdit()
  clearBudgetUndo()
  graphViewMode.value = null
  mapSectionRef.value?.invalidate()
})

const retryHydrate = async () => {
  await runHydrate()
}

const goBack = () => router.push('/')
</script>

<style scoped>
.result-page {
  max-width: var(--content-max);
  margin-inline: auto;
  padding: var(--space-6) var(--page-gutter);
  padding-bottom: calc(var(--space-8) + env(safe-area-inset-bottom));
}

.result-page__shell {
  display: grid;
  gap: var(--space-6);
}

.result-page__heading {
  margin: 0;
  scroll-margin-top: calc(var(--header-h) + 76px);
  font-family: var(--font-serif);
  font-size: var(--text-h2);
}

.result-page__heading:focus:not(:focus-visible) {
  outline: none;
}

.result-page__tools {
  display: flex;
  flex-wrap: wrap;
}

@media (max-width: 767px) {
  .result-page {
    padding-bottom: calc(88px + env(safe-area-inset-bottom));
  }
}

.back-top-button {
  width: 50px;
  height: 50px;
  background: var(--color-primary);
  color: var(--color-surface);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.03em;
  box-shadow: var(--shadow-2);
  cursor: pointer;
}
</style>
