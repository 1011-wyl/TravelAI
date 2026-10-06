import { onUnmounted, ref } from 'vue'
import type { GraphCategory, KnowledgeGraphData, TripPlan, TripPlanResponse } from '@/types'
import { pollTaskStatus } from '@/services/api'

export type ResultLoadStatus = 'loading' | 'ready' | 'missing' | 'restore-failed' | 'parse-failed'

const isRecord = (value: unknown): value is Record<string, unknown> =>
  Boolean(value) && typeof value === 'object'

export const isUsableTripPlan = (value: unknown): value is TripPlan => {
  if (!isRecord(value)) return false
  return typeof value.city === 'string' && Array.isArray(value.days)
}

export const normalizeQueryPlanId = (queryPlanId: unknown): string => {
  if (Array.isArray(queryPlanId)) return String(queryPlanId[0] || '')
  if (queryPlanId == null) return ''
  return String(queryPlanId)
}

const parseJsonValue = (raw: string | null): { ok: true; value: unknown } | { ok: false } => {
  if (!raw) return { ok: true, value: null }
  try {
    return { ok: true, value: JSON.parse(raw) as unknown }
  } catch {
    return { ok: false }
  }
}

export const useTripPlanState = () => {
  const tripPlan = ref<TripPlan | null>(null)
  const graphData = ref<KnowledgeGraphData | null>(null)
  const graphCategories = ref<GraphCategory[]>([])
  const planId = ref('')
  /** Page-local plan adoption identity; not persisted to DTO/storage. */
  const planSourceKey = ref('')
  const status = ref<ResultLoadStatus>('loading')

  let planSourceSerial = 0
  let hydrateSeq = 0
  let disposed = false

  const isHydrateCurrent = (seq: number) => !disposed && seq === hydrateSeq

  const nextPlanSourceKey = () => {
    planSourceSerial += 1
    return `src:${planSourceSerial}`
  }

  /** Invalidate in-flight UI work immediately; old plan must not stay editable. */
  const beginPlanSwitch = () => {
    planSourceKey.value = ''
    tripPlan.value = null
    graphData.value = null
    graphCategories.value = []
    status.value = 'loading'
  }

  const applyTripPlanPayload = (
    payload: {
      plan: TripPlan
      graph?: KnowledgeGraphData | null
      planId?: string
      persistGraph?: boolean
    },
    options?: { adopt?: boolean; hydrateSeq?: number }
  ) => {
    if (options?.hydrateSeq != null && !isHydrateCurrent(options.hydrateSeq)) {
      return false
    }
    if (disposed) return false

    tripPlan.value = payload.plan
    status.value = 'ready'

    if (payload.planId) {
      planId.value = payload.planId
      sessionStorage.setItem('planId', payload.planId)
    }

    sessionStorage.setItem('tripPlan', JSON.stringify(payload.plan))

    if (options?.adopt) {
      planSourceKey.value = nextPlanSourceKey()
    }

    if (payload.graph) {
      graphData.value = payload.graph
      graphCategories.value = payload.graph.categories || []
      sessionStorage.setItem('graphData', JSON.stringify(payload.graph))
      return true
    }

    if (payload.graph === undefined && payload.persistGraph !== true) {
      return true
    }

    graphData.value = null
    graphCategories.value = []
    sessionStorage.removeItem('graphData')
    return true
  }

  const restoreTripPlanFromResponse = (
    response?: TripPlanResponse | null,
    options?: { hydrateSeq?: number }
  ) => {
    if (!response?.data || !isUsableTripPlan(response.data)) return false
    return applyTripPlanPayload(
      {
        plan: response.data,
        graph: response.graph_data || null,
        planId: String(response.plan_id || planId.value || ''),
      },
      { adopt: true, hydrateSeq: options?.hydrateSeq }
    )
  }

  const hydrate = async (queryPlanId: unknown) => {
    const seq = ++hydrateSeq
    beginPlanSwitch()

    const storedPlanId = String(sessionStorage.getItem('planId') || '')
    const queryId = normalizeQueryPlanId(queryPlanId)
    const resolvedPlanId = queryId || storedPlanId || ''

    if (!isHydrateCurrent(seq)) return

    planId.value = resolvedPlanId
    if (resolvedPlanId) {
      sessionStorage.setItem('planId', resolvedPlanId)
    }

    const cachedPlanId = storedPlanId
    const data = sessionStorage.getItem('tripPlan')
    const canUseCachedData =
      Boolean(data) && (!resolvedPlanId || !cachedPlanId || cachedPlanId === resolvedPlanId)

    if (data && canUseCachedData) {
      const parsedPlan = parseJsonValue(data)
      if (!isHydrateCurrent(seq)) return
      if (!parsedPlan.ok) {
        status.value = 'parse-failed'
        return
      }
      if (!isUsableTripPlan(parsedPlan.value)) {
        status.value = 'parse-failed'
        return
      }

      const graphRaw = sessionStorage.getItem('graphData')
      let graph: KnowledgeGraphData | undefined
      if (graphRaw) {
        const parsedGraph = parseJsonValue(graphRaw)
        if (parsedGraph.ok && parsedGraph.value && isRecord(parsedGraph.value)) {
          graph = parsedGraph.value as unknown as KnowledgeGraphData
        }
      }

      applyTripPlanPayload(
        {
          plan: parsedPlan.value,
          graph: graph || undefined,
          planId: resolvedPlanId || cachedPlanId,
          persistGraph: false,
        },
        { adopt: true, hydrateSeq: seq }
      )
      return
    }

    if (resolvedPlanId) {
      try {
        const task = await pollTaskStatus(resolvedPlanId)
        if (!isHydrateCurrent(seq)) return
        if (task?.status === 'completed' && task.result) {
          if (restoreTripPlanFromResponse(task.result, { hydrateSeq: seq })) return
        }
        if (!isHydrateCurrent(seq)) return
        status.value = 'restore-failed'
        return
      } catch (error) {
        console.error('结果页从后端回补旅行计划失败:', error)
        if (!isHydrateCurrent(seq)) return
        status.value = 'restore-failed'
        return
      }
    }

    if (!isHydrateCurrent(seq)) return
    status.value = 'missing'
  }

  onUnmounted(() => {
    disposed = true
    hydrateSeq += 1
    planSourceKey.value = ''
  })

  return {
    tripPlan,
    graphData,
    graphCategories,
    planId,
    planSourceKey,
    status,
    applyTripPlanPayload,
    restoreTripPlanFromResponse,
    hydrate,
  }
}
