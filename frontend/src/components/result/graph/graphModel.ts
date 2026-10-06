import type { GraphCategory, GraphEdge, GraphNode, KnowledgeGraphData } from '@/types'

export const CATEGORY_KEY_MAP: Record<string, string> = {
  城市: 'city',
  都市: 'city',
  city: 'city',
  日程: 'schedule',
  行程: 'schedule',
  schedule: 'schedule',
  スケジュール: 'schedule',
  day: 'schedule',
  景点: 'attraction',
  観光地: 'attraction',
  attraction: 'attraction',
  酒店: 'hotel',
  ホテル: 'hotel',
  hotel: 'hotel',
  餐饮: 'meal',
  食事: 'meal',
  meal: 'meal',
  dining: 'meal',
  グルメ: 'meal',
  天气: 'weather',
  天気: 'weather',
  weather: 'weather',
  预算: 'budget',
  予算: 'budget',
  budget: 'budget',
  '偏好/建议': 'suggestion',
  '好み/提案': 'suggestion',
  'preference/suggestion': 'suggestion',
  tips: 'suggestion',
  おすすめ: 'suggestion',
  preference: 'suggestion',
}

export const KNOWN_CATEGORY_KEYS = [
  'city',
  'schedule',
  'attraction',
  'hotel',
  'meal',
  'weather',
  'budget',
  'suggestion',
] as const

export type KnownCategoryKey = (typeof KNOWN_CATEGORY_KEYS)[number]

export const CATEGORY_TOKEN_COLOR: Record<string, string> = {
  city: 'var(--color-sky)',
  schedule: 'var(--color-primary)',
  attraction: 'var(--color-success)',
  hotel: 'var(--color-sand)',
  meal: 'var(--color-accent)',
  weather: 'var(--color-info)',
  budget: 'var(--color-warning)',
  suggestion: 'var(--color-primary-hover)',
  unknown: 'var(--color-border-strong)',
}

export const CATEGORY_HEX: Record<string, string> = {
  city: '#3b74a8',
  schedule: '#147d72',
  attraction: '#1e7a55',
  hotel: '#d4a866',
  meal: '#f26a4f',
  weather: '#2f6fa3',
  budget: '#9a5b0a',
  suggestion: '#106b62',
  unknown: '#9db5ae',
}

export type ResolvedGraphNode = GraphNode & {
  uid: string
  categoryKey: string
  categoryName: string
  hasWeight: boolean
  visualSize: number
}

export type ResolvedGraphEdge = {
  uid: string
  sourceUid: string
  targetUid: string
  label: string
  directed: true
}

export const nodeUid = (id: unknown): string => String(id)

export const normalizeCategoryKey = (name: string): string => {
  const key = (name || '').toLowerCase()
  return CATEGORY_KEY_MAP[name] || CATEGORY_KEY_MAP[key] || name || 'unknown'
}

export const isKnownCategory = (key: string): key is KnownCategoryKey => {
  return (KNOWN_CATEGORY_KEYS as readonly string[]).includes(key)
}

export const categoryHex = (key: string): string => CATEGORY_HEX[key] || CATEGORY_HEX.unknown

export const visualSizeFromSymbol = (raw: unknown): { hasWeight: boolean; size: number } => {
  const numeric = Number(raw)
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return { hasWeight: false, size: 56 }
  }
  const baseSize = numeric >= 70 ? 100 : numeric >= 45 ? 80 : 60
  return { hasWeight: true, size: Math.round(baseSize * 1.25) }
}

export const isUsableGraph = (value: unknown): value is KnowledgeGraphData => {
  if (!value || typeof value !== 'object') return false
  const record = value as Record<string, unknown>
  return Array.isArray(record.nodes) && Array.isArray(record.edges)
}

export const resolveEndpoint = (
  raw: unknown,
  nodes: GraphNode[],
  byId: Map<string, GraphNode>
): GraphNode | null => {
  if (raw == null) return null
  const asId = byId.get(String(raw))
  if (asId) return asId
  if (typeof raw === 'number' && Number.isInteger(raw) && raw >= 0 && raw < nodes.length) {
    return nodes[raw]
  }
  if (typeof raw === 'string' && /^\d+$/.test(raw)) {
    const index = Number(raw)
    if (index >= 0 && index < nodes.length && !byId.has(raw)) {
      return nodes[index]
    }
  }
  return null
}

export const resolveGraph = (data: KnowledgeGraphData | null): {
  nodes: ResolvedGraphNode[]
  edges: ResolvedGraphEdge[]
  categories: GraphCategory[]
  droppedEdges: number
} => {
  if (!data) return { nodes: [], edges: [], categories: [], droppedEdges: 0 }
  const categories = Array.isArray(data.categories) ? data.categories : []
  const rawNodes = Array.isArray(data.nodes) ? data.nodes : []
  const byId = new Map<string, GraphNode>()
  const seen = new Set<string>()
  const nodes: ResolvedGraphNode[] = []

  rawNodes.forEach((node, index) => {
    if (!node || node.id == null || node.id === '') {
      console.warn('[graph] skip node without id at', index)
      return
    }
    const uid = nodeUid(node.id)
    if (seen.has(uid)) {
      console.warn('[graph] skip duplicate node id', uid)
      return
    }
    seen.add(uid)
    byId.set(uid, node)
    const categoryName = categories[Number(node.category)]?.name || ''
    const categoryKey = normalizeCategoryKey(categoryName || 'unknown')
    const weight = visualSizeFromSymbol(node.symbolSize)
    nodes.push({
      ...node,
      uid,
      categoryKey: isKnownCategory(categoryKey) ? categoryKey : categoryKey || 'unknown',
      categoryName,
      hasWeight: weight.hasWeight,
      visualSize: weight.size,
    })
  })

  const uidSet = new Set(nodes.map((item) => item.uid))
  const edges: ResolvedGraphEdge[] = []
  let droppedEdges = 0
  ;(Array.isArray(data.edges) ? data.edges : []).forEach((edge: GraphEdge, index) => {
    const source = resolveEndpoint(edge?.source, rawNodes, byId)
    const target = resolveEndpoint(edge?.target, rawNodes, byId)
    if (!source || !target) {
      droppedEdges += 1
      console.warn('[graph] skip dangling edge', index)
      return
    }
    const sourceUid = nodeUid(source.id)
    const targetUid = nodeUid(target.id)
    if (!uidSet.has(sourceUid) || !uidSet.has(targetUid)) {
      droppedEdges += 1
      return
    }
    edges.push({
      uid: `e${index}-${sourceUid}-${targetUid}`,
      sourceUid,
      targetUid,
      label: edge.label || '',
      directed: true,
    })
  })

  return { nodes, edges, categories, droppedEdges }
}

export const buildStaticPositions = (
  nodes: ResolvedGraphNode[],
  edges: ResolvedGraphEdge[],
  width: number,
  height: number
): Map<string, { x: number; y: number }> => {
  const degreeMap = new Map<string, number>()
  nodes.forEach((node) => degreeMap.set(node.uid, 0))
  edges.forEach((edge) => {
    degreeMap.set(edge.sourceUid, (degreeMap.get(edge.sourceUid) || 0) + 1)
    degreeMap.set(edge.targetUid, (degreeMap.get(edge.targetUid) || 0) + 1)
  })

  let rootUid = nodes[0]?.uid || ''
  let maxDegree = -1
  nodes.forEach((node) => {
    const degree = degreeMap.get(node.uid) || 0
    if (degree > maxDegree) {
      maxDegree = degree
      rootUid = node.uid
    }
  })

  const grouped = new Map<string, ResolvedGraphNode[]>()
  nodes.forEach((node) => {
    if (node.uid === rootUid) return
    const key = node.categoryKey || 'misc'
    if (!grouped.has(key)) grouped.set(key, [])
    grouped.get(key)!.push(node)
  })

  const orderedGroupKeys = Array.from(grouped.keys()).sort((a, b) => {
    return (grouped.get(b)?.length || 0) - (grouped.get(a)?.length || 0)
  })

  const cx = width / 2
  const cy = height / 2
  const outerRadiusX = Math.max(80, width / 2 - 24)
  const outerRadiusY = Math.max(80, height / 2 - 24)
  const layerFactors = [1, 0.9, 0.8, 0.7]
  const positionMap = new Map<string, { x: number; y: number }>()
  if (rootUid) positionMap.set(rootUid, { x: cx, y: cy })

  orderedGroupKeys.forEach((groupKey, groupIndex) => {
    const group = grouped.get(groupKey) || []
    const baseAngle = -Math.PI / 2 + (2 * Math.PI * groupIndex) / Math.max(1, orderedGroupKeys.length)
    const spread = Math.min(1.25, Math.max(0.55, group.length * 0.03))
    const layerStride = Math.max(1, Math.ceil(group.length / layerFactors.length))
    group.forEach((node, nodeIndex) => {
      const t = group.length === 1 ? 0 : nodeIndex / (group.length - 1) - 0.5
      const angle = baseAngle + t * spread
      const layerIndex = Math.min(layerFactors.length - 1, Math.floor(nodeIndex / layerStride))
      const layerFactor = layerFactors[layerIndex]
      const nodeRadius = Math.round(node.visualSize * 0.34)
      let x = cx + Math.cos(angle) * outerRadiusX * layerFactor
      let y = cy + Math.sin(angle) * outerRadiusY * layerFactor
      x = Math.max(nodeRadius + 8, Math.min(width - nodeRadius - 8, x))
      y = Math.max(nodeRadius + 8, Math.min(height - nodeRadius - 8, y))
      positionMap.set(node.uid, { x, y })
    })
  })

  return positionMap
}
