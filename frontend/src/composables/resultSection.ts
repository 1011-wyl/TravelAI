export const RESULT_PUBLIC_SECTIONS = ['overview', 'budget', 'map', 'itinerary', 'graph', 'weather'] as const

export type ResultPublicSection = (typeof RESULT_PUBLIC_SECTIONS)[number]
export type ResultInternalSection = 'overview' | 'budget' | 'map' | 'days' | 'knowledge-graph' | 'weather'

const ALIAS_TO_PUBLIC: Record<string, ResultPublicSection> = {
  overview: 'overview',
  budget: 'budget',
  map: 'map',
  itinerary: 'itinerary',
  graph: 'graph',
  weather: 'weather',
  days: 'itinerary',
  'knowledge-graph': 'graph',
}

const PUBLIC_TO_INTERNAL: Record<ResultPublicSection, ResultInternalSection> = {
  overview: 'overview',
  budget: 'budget',
  map: 'map',
  itinerary: 'days',
  graph: 'knowledge-graph',
  weather: 'weather',
}

export const pickQueryValue = (value: unknown): string => {
  if (Array.isArray(value)) return String(value[0] ?? '')
  if (value == null) return ''
  return String(value)
}

export const normalizePublicSection = (raw: string): ResultPublicSection => {
  return ALIAS_TO_PUBLIC[raw] || 'overview'
}

export const toInternalSection = (section: ResultPublicSection): ResultInternalSection => {
  return PUBLIC_TO_INTERNAL[section]
}

export const isCanonicalPublicSection = (raw: string): raw is ResultPublicSection => {
  return (RESULT_PUBLIC_SECTIONS as readonly string[]).includes(raw)
}
