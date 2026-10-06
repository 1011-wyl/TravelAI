import { computed, type Ref } from 'vue'
import type { KnowledgeGraphData } from '@/types'
import {
  isUsableGraph,
  normalizeCategoryKey,
  resolveGraph,
  type ResolvedGraphEdge,
  type ResolvedGraphNode,
} from '@/components/result/graph/graphModel'

export const useKnowledgeGraph = (
  graph: Ref<KnowledgeGraphData | null | undefined>,
  filterKey: Ref<string>,
  selectedId: Ref<string | null>
) => {
  const usable = computed(() => isUsableGraph(graph.value) || graph.value == null)
  const resolved = computed(() => resolveGraph(isUsableGraph(graph.value) ? graph.value : null))

  const nodes = computed(() => resolved.value.nodes)
  const edges = computed(() => resolved.value.edges)
  const empty = computed(() => usable.value && nodes.value.length === 0)
  const invalid = computed(() => graph.value != null && !isUsableGraph(graph.value))

  const categoryOptions = computed(() => {
    const seen = new Map<string, string>()
    resolved.value.categories.forEach((category) => {
      const name = String(category?.name || '').trim()
      if (!name) return
      const key = normalizeCategoryKey(name)
      if (!seen.has(key)) seen.set(key, name)
    })
    nodes.value.forEach((node) => {
      if (!seen.has(node.categoryKey)) seen.set(node.categoryKey, node.categoryName || node.categoryKey)
    })
    return Array.from(seen.entries()).map(([key, name]) => ({ key, name }))
  })

  const filteredNodes = computed(() => {
    if (filterKey.value === 'all') return nodes.value
    return nodes.value.filter((node) => node.categoryKey === filterKey.value)
  })

  const filteredUids = computed(() => new Set(filteredNodes.value.map((node) => node.uid)))

  const filteredEdges = computed(() => {
    return edges.value.filter(
      (edge) => filteredUids.value.has(edge.sourceUid) && filteredUids.value.has(edge.targetUid)
    )
  })

  const selectedNode = computed(() => {
    if (!selectedId.value) return null
    return filteredNodes.value.find((node) => node.uid === selectedId.value) || null
  })

  const relationsOf = (uid: string) => {
    const outgoing: Array<{ edge: ResolvedGraphEdge; node: ResolvedGraphNode }> = []
    const incoming: Array<{ edge: ResolvedGraphEdge; node: ResolvedGraphNode }> = []
    edges.value.forEach((edge) => {
      if (edge.sourceUid === uid) {
        const node = nodes.value.find((item) => item.uid === edge.targetUid)
        if (node) outgoing.push({ edge, node })
      }
      if (edge.targetUid === uid) {
        const node = nodes.value.find((item) => item.uid === edge.sourceUid)
        if (node) incoming.push({ edge, node })
      }
    })
    return { outgoing, incoming, count: outgoing.length + incoming.length }
  }

  const groupedList = computed(() => {
    const groups = new Map<string, ResolvedGraphNode[]>()
    filteredNodes.value.forEach((node) => {
      if (!groups.has(node.categoryKey)) groups.set(node.categoryKey, [])
      groups.get(node.categoryKey)!.push(node)
    })
    return Array.from(groups.entries()).map(([key, items]) => ({
      key,
      name: items[0]?.categoryName || key,
      nodes: items,
    }))
  })

  return {
    usable,
    empty,
    invalid,
    nodes,
    edges,
    filteredNodes,
    filteredEdges,
    categoryOptions,
    selectedNode,
    relationsOf,
    groupedList,
  }
}
