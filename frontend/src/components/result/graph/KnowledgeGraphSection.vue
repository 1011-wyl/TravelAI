<template>
  <section class="kg-section" aria-labelledby="result-section-heading">
    <ContentSkeleton v-if="hydrating" variant="list" :lines="6" />

    <EmptyJourneyState
      v-else-if="invalid"
      :title="t('result.graph.invalidTitle')"
      :description="t('result.graph.invalidDesc')"
    />

    <EmptyJourneyState
      v-else-if="empty"
      :title="t('result.graph.emptyTitle')"
      :description="t('result.graph.emptyDesc')"
    />

    <template v-else>
      <div class="kg-section__toolbar">
        <AppSegmentedControl
          :model-value="viewMode"
          :options="viewOptions"
          :aria-label="t('result.graph.viewSwitch')"
          name="graph-view"
          @update:model-value="onViewChange"
        />
        <AppButton
          v-if="viewMode === 'graph'"
          variant="secondary"
          size="sm"
          @click="canvasRef?.resetView()"
        >
          {{ t('result.graph.resetView') }}
        </AppButton>
      </div>

      <div class="kg-section__filters" role="group" :aria-label="t('result.graph.filterLabel')">
        <button
          type="button"
          class="kg-filter"
          :class="{ 'is-active': filterKey === 'all' }"
          :aria-pressed="filterKey === 'all'"
          @click="filterKey = 'all'"
        >
          {{ t('result.graph.filterAll') }}
        </button>
        <button
          v-for="option in categoryOptions"
          :key="option.key"
          type="button"
          class="kg-filter"
          :class="{ 'is-active': filterKey === option.key }"
          :aria-pressed="filterKey === option.key"
          @click="filterKey = option.key"
        >
          <span class="kg-filter__dot" :style="{ background: categoryHex(option.key) }" />
          {{ categoryOptionLabel(option) }}
        </button>
      </div>

      <InlineNotice
        v-if="chartError && viewMode === 'graph'"
        kind="warning"
        :title="t('result.graph.chartErrorTitle')"
        :message="t('result.graph.chartErrorDesc')"
      >
        <template #action>
          <AppButton size="sm" variant="secondary" @click="retryChart">
            {{ t('result.graph.retryChart') }}
          </AppButton>
          <AppButton size="sm" variant="ghost" @click="emit('update:viewMode', 'list')">
            {{ t('result.graph.useList') }}
          </AppButton>
        </template>
      </InlineNotice>

      <EmptyJourneyState
        v-if="filteredEmpty"
        :title="t('result.graph.filterEmptyTitle')"
        :description="t('result.graph.filterEmptyDesc')"
      />

      <div v-else class="kg-section__layout" :class="`is-${viewMode}`">
        <GraphListView
          v-if="viewMode === 'list'"
          :groups="groupedList"
          :selected-id="selectedId"
          :relation-count="relationCount"
          @select="selectedId = $event"
        />
        <GraphCanvas
          v-else-if="!chartError"
          :key="chartKey"
          ref="canvasRef"
          :nodes="filteredNodes"
          :edges="filteredEdges"
          :selected-id="selectedId"
          :reduce-motion="reduceMotion"
          :canvas-aria-label="t('result.graph.canvasLabel')"
          @select="selectedId = $event"
          @clear="selectedId = null"
          @load-error="chartError = true"
        />
        <aside class="kg-section__detail">
          <GraphNodeDetail
            :node="selectedNode"
            :outgoing="selectedRelations.outgoing"
            :incoming="selectedRelations.incoming"
            @select="selectedId = $event"
          />
        </aside>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { KnowledgeGraphData } from '@/types'
import AppButton from '@/components/ui/AppButton.vue'
import AppSegmentedControl from '@/components/ui/AppSegmentedControl.vue'
import ContentSkeleton from '@/components/feedback/ContentSkeleton.vue'
import EmptyJourneyState from '@/components/feedback/EmptyJourneyState.vue'
import InlineNotice from '@/components/feedback/InlineNotice.vue'
import GraphCanvas from './GraphCanvas.vue'
import GraphListView from './GraphListView.vue'
import GraphNodeDetail from './GraphNodeDetail.vue'
import { useKnowledgeGraph } from '@/composables/useKnowledgeGraph'
import { useMotionPreference } from '@/composables/useMotionPreference'
import { categoryHex, isKnownCategory } from './graphModel'

const props = defineProps<{
  graph: KnowledgeGraphData | null
  hydrating?: boolean
  viewMode: 'graph' | 'list' | null
}>()

const emit = defineEmits<{
  'update:viewMode': [value: 'graph' | 'list']
}>()

const hydrating = computed(() => Boolean(props.hydrating))

const { t } = useI18n()
const { reduceMotion } = useMotionPreference()
const filterKey = ref('all')
const selectedId = ref<string | null>(null)
const chartError = ref(false)
const chartKey = ref(0)
const canvasRef = ref<{ resetView: () => void } | null>(null)
const graphRef = computed(() => props.graph)
const kg = useKnowledgeGraph(graphRef, filterKey, selectedId)

const {
  empty,
  invalid,
  filteredNodes,
  filteredEdges,
  categoryOptions,
  selectedNode,
  relationsOf,
  groupedList,
} = kg

const defaultViewMode = (): 'graph' | 'list' => {
  if (typeof window !== 'undefined' && window.innerWidth < 1024) return 'list'
  return 'graph'
}

const viewMode = computed(() => props.viewMode ?? defaultViewMode())

const viewOptions = computed(() => [
  { value: 'graph' as const, label: t('result.graph.viewGraph') },
  { value: 'list' as const, label: t('result.graph.viewList') },
])

const filteredEmpty = computed(() => !empty.value && !invalid.value && filteredNodes.value.length === 0)

const selectedRelations = computed(() => {
  if (!selectedNode.value) return { outgoing: [], incoming: [] }
  return relationsOf(selectedNode.value.uid)
})

const relationCount = (uid: string) => relationsOf(uid).count

const categoryOptionLabel = (option: { key: string; name: string }) => {
  if (isKnownCategory(option.key)) return t(`result.graph.categories.${option.key}`)
  return option.name || option.key
}

const onViewChange = (value: string) => {
  if (value === 'graph' || value === 'list') emit('update:viewMode', value)
}

const retryChart = () => {
  chartError.value = false
  chartKey.value += 1
}

watch(filteredNodes, (nodes) => {
  if (selectedId.value && !nodes.some((node) => node.uid === selectedId.value)) {
    selectedId.value = null
  }
})

const onEscape = (event: KeyboardEvent) => {
  if (event.key !== 'Escape') return
  const target = event.target as HTMLElement | null
  if (target?.closest('.ant-drawer, .ant-modal, [role="dialog"]')) return
  if (!selectedId.value) return
  selectedId.value = null
  event.stopPropagation()
}

watch(
  () => props.viewMode,
  (mode) => {
    if (mode == null) emit('update:viewMode', defaultViewMode())
  },
  { immediate: true }
)

onMounted(() => {
  window.addEventListener('keydown', onEscape)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onEscape)
})
</script>

<style scoped>
.kg-section {
  display: grid;
  gap: var(--space-4);
  min-width: 0;
  max-width: 100%;
  overflow-x: hidden;
}

.kg-section__toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  align-items: center;
  justify-content: space-between;
}

.kg-section__filters {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.kg-filter {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 0.35rem 0.7rem;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
}

.kg-filter.is-active {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.kg-filter:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.kg-filter__dot {
  width: 0.7rem;
  height: 0.7rem;
  border-radius: 50%;
}

.kg-section__layout {
  display: grid;
  gap: var(--space-4);
  min-width: 0;
}

.kg-section__layout.is-graph {
  grid-template-columns: minmax(0, 1fr);
}

.kg-section__detail {
  min-width: 0;
}

@media (min-width: 1024px) {
  .kg-section__layout.is-graph,
  .kg-section__layout.is-list {
    grid-template-columns: minmax(0, 8fr) minmax(16rem, 4fr);
    align-items: start;
  }
}
</style>
