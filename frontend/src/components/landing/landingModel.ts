import type { Dayjs } from 'dayjs'
import type { TripTaskStage } from '@/types'

export type LandingCityStay = {
  city: string
  days: number
}

export type LandingFormData = {
  cities: LandingCityStay[]
  start_date: Dayjs | undefined
  transportation: string
  accommodation: string
  preferences: string[]
  free_text_input: string
}

export type TripBriefSnapshot = {
  cities: LandingCityStay[]
  startDate: string
  endDate: string
  travelDays: number
  transportation: string
  accommodation: string
  preferences: string[]
}

export const MAX_CITIES = 5
export const MIN_CITIES = 1
export const MIN_CITY_DAYS = 1
export const MAX_CITY_DAYS = 15
export const DEFAULT_CITY_DAYS = 2
export const MAX_TRAVEL_DAYS = 30

export const INTEREST_OPTIONS = [
  { value: '历史文化', labelKey: 'home.interests.history' },
  { value: '自然风光', labelKey: 'home.interests.nature' },
  { value: '美食', labelKey: 'home.interests.food' },
  { value: '购物', labelKey: 'home.interests.shopping' },
  { value: '艺术', labelKey: 'home.interests.art' },
  { value: '休闲', labelKey: 'home.interests.leisure' },
] as const

export const TRANSPORT_OPTIONS = [
  { value: '公共交通', labelKey: 'home.transportation.public' },
  { value: '自驾', labelKey: 'home.transportation.drive' },
  { value: '步行', labelKey: 'home.transportation.walk' },
  { value: '混合', labelKey: 'home.transportation.mixed' },
] as const

export const ACCOMMODATION_OPTIONS = [
  { value: '经济型酒店', labelKey: 'home.accommodation.budget' },
  { value: '舒适型酒店', labelKey: 'home.accommodation.comfort' },
  { value: '豪华酒店', labelKey: 'home.accommodation.luxury' },
  { value: '民宿', labelKey: 'home.accommodation.homestay' },
] as const

export const JOURNEY_NODES = [
  { id: 'understand', labelKey: 'home.journey.understand', stages: ['submitted', 'initializing'] },
  { id: 'inspire', labelKey: 'home.journey.inspire', stages: ['attraction_search', 'weather_search'] },
  { id: 'route', labelKey: 'home.journey.route', stages: ['planning'] },
  { id: 'balance', labelKey: 'home.journey.balance', stages: ['hotel_search'] },
  { id: 'pack', labelKey: 'home.journey.pack', stages: ['graph_building', 'completed'] },
] as const

export const createDefaultLandingForm = (): LandingFormData => ({
  cities: [{ city: '', days: DEFAULT_CITY_DAYS }],
  start_date: undefined,
  transportation: '公共交通',
  accommodation: '经济型酒店',
  preferences: [],
  free_text_input: '',
})

export const resolveJourneyNodeIndex = (stage: TripTaskStage | ''): number => {
  if (!stage) return 0
  const index = JOURNEY_NODES.findIndex((node) => (node.stages as readonly string[]).includes(stage))
  return index >= 0 ? index : -1
}

export const knownStageLabelKey = (stage: TripTaskStage): string | null => {
  if (stage === 'submitted' || stage === 'initializing') return 'home.loading.initializing'
  if (stage === 'attraction_search') return 'home.loading.searchingAttractions'
  if (stage === 'weather_search') return 'home.loading.queryingWeather'
  if (stage === 'hotel_search') return 'home.loading.recommendingHotels'
  if (stage === 'planning' || stage === 'graph_building') return 'home.loading.generatingPlan'
  if (stage === 'completed') return 'home.loading.done'
  return null
}
