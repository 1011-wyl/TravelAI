import type { TripPlan } from '@/types'

export type OverviewAttractionItem = {
  name: string
  address: string
  visit_duration: number
  description: string
  ticket_price?: number
  dayNumber: number
  dayArrayIndex: number
  order: number
}

export const toOverviewAttractionItems = (plan: TripPlan): OverviewAttractionItem[] => {
  const items: OverviewAttractionItem[] = []
  plan.days.forEach((day, dayArrayIndex) => {
    day.attractions.forEach((attraction, order) => {
      items.push({
        name: attraction.name,
        address: attraction.address,
        visit_duration: attraction.visit_duration,
        description: attraction.description,
        ticket_price: attraction.ticket_price,
        dayNumber: dayArrayIndex + 1,
        dayArrayIndex,
        order,
      })
    })
  })
  return items
}
