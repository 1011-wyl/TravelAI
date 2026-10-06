import { computed, onUnmounted, ref, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Attraction, Hotel, Meal, TripPlan } from '@/types'

export type BudgetItemType = 'attraction' | 'hotel' | 'meal' | 'transport'
export type BudgetSortMode = 'amountDesc' | 'amountAsc' | 'dayAsc' | 'dayDesc'
export type BudgetFilterType = 'all' | BudgetItemType

export type BudgetDetailItem = {
  id: string
  type: BudgetItemType
  dayIndex: number | null
  dayNumber: number | null
  name: string
  amount: number
  sourceIndex?: number
}

export type BudgetRestorePayload =
  | {
      type: 'attraction'
      attraction: Attraction
      insertIndex: number
    }
  | {
      type: 'meal'
      meal: Meal
      insertIndex: number
    }
  | {
      type: 'hotel'
      hotel: Hotel
      accommodation: string
    }
  | {
      type: 'transport'
      transportation: string
    }

export type BudgetRestoreItem = {
  uid: string
  base: BudgetDetailItem
  payload: BudgetRestorePayload
}

export type BudgetCategoryKey = BudgetItemType | 'interCity' | 'other'

export type BudgetCategorySlice = {
  key: BudgetCategoryKey
  label: string
  amount: number
  share: number | null
}

const UNDO_MS = 6000

export const toBudgetNumber = (value: unknown): number => {
  const numeric = Number(value)
  if (!Number.isFinite(numeric) || numeric <= 0) return 0
  return numeric
}

export const roundBudgetAmount = (value: number): number => {
  return Math.round((value + Number.EPSILON) * 100) / 100
}

export const formatBudgetAmount = (value: number): string => {
  const rounded = roundBudgetAmount(value)
  return Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(2)
}

const cloneData = <T>(data: T): T => JSON.parse(JSON.stringify(data)) as T

export const useBudgetEditor = (
  tripPlan: Ref<TripPlan | null>,
  options?: {
    persist?: () => void
    onLinkedChange?: () => void
  }
) => {
  const { t } = useI18n()
  const filterType = ref<BudgetFilterType>('all')
  const sortMode = ref<BudgetSortMode>('amountDesc')
  const undoItem = ref<BudgetRestoreItem | null>(null)
  let undoTimer: ReturnType<typeof setTimeout> | null = null

  const persist = () => {
    options?.persist?.()
  }

  const getMealLabel = (type: string): string => {
    const labels: Record<string, string> = {
      breakfast: t('result.meals.breakfast'),
      lunch: t('result.meals.lunch'),
      dinner: t('result.meals.dinner'),
      snack: t('result.meals.snack'),
    }
    return labels[type] || type
  }

  const getBudgetTypeLabel = (type: BudgetItemType): string => {
    const labels: Record<BudgetItemType, string> = {
      attraction: t('result.budget.attraction'),
      hotel: t('result.budget.hotel'),
      meal: t('result.budget.meal'),
      transport: t('result.budget.transport'),
    }
    return labels[type]
  }

  const clearUndoTimer = () => {
    if (!undoTimer) return
    clearTimeout(undoTimer)
    undoTimer = null
  }

  const clearUndo = () => {
    clearUndoTimer()
    undoItem.value = null
  }

  const scheduleUndo = (item: BudgetRestoreItem) => {
    clearUndoTimer()
    undoItem.value = item
    undoTimer = setTimeout(() => {
      undoItem.value = null
      undoTimer = null
    }, UNDO_MS)
  }

  const recalculateBudgetTotals = (transportationOverride?: number) => {
    if (!tripPlan.value) return

    let attractionTotal = 0
    let hotelTotal = 0
    let mealTotal = 0

    tripPlan.value.days.forEach((day) => {
      day.attractions.forEach((attraction) => {
        attractionTotal += toBudgetNumber(attraction.ticket_price)
      })

      if (day.hotel) {
        hotelTotal += toBudgetNumber(day.hotel.estimated_cost)
      }

      day.meals.forEach((meal) => {
        mealTotal += toBudgetNumber(meal.estimated_cost)
      })
    })

    const transportationTotal = roundBudgetAmount(
      transportationOverride ?? toBudgetNumber(tripPlan.value.budget?.total_transportation)
    )

    tripPlan.value.budget = {
      total_attractions: roundBudgetAmount(attractionTotal),
      total_hotels: roundBudgetAmount(hotelTotal),
      total_meals: roundBudgetAmount(mealTotal),
      total_transportation: transportationTotal,
      total: roundBudgetAmount(attractionTotal + hotelTotal + mealTotal + transportationTotal),
    }
  }

  const budgetItems = computed<BudgetDetailItem[]>(() => {
    if (!tripPlan.value) return []

    const items: BudgetDetailItem[] = []

    tripPlan.value.days.forEach((day, dayIndex) => {
      const dayNumber = dayIndex + 1

      day.attractions.forEach((attraction, attractionIndex) => {
        const amount = roundBudgetAmount(toBudgetNumber(attraction.ticket_price))
        if (amount <= 0) return
        items.push({
          id: `attraction-${dayIndex}-${attractionIndex}`,
          type: 'attraction',
          dayIndex,
          dayNumber,
          name: attraction.name,
          amount,
          sourceIndex: attractionIndex,
        })
      })

      if (day.hotel) {
        const amount = roundBudgetAmount(toBudgetNumber(day.hotel.estimated_cost))
        if (amount > 0) {
          items.push({
            id: `hotel-${dayIndex}`,
            type: 'hotel',
            dayIndex,
            dayNumber,
            name: day.hotel.name,
            amount,
          })
        }
      }

      day.meals.forEach((meal, mealIndex) => {
        const amount = roundBudgetAmount(toBudgetNumber(meal.estimated_cost))
        if (amount <= 0) return
        items.push({
          id: `meal-${dayIndex}-${mealIndex}`,
          type: 'meal',
          dayIndex,
          dayNumber,
          name: `${getMealLabel(meal.type)} · ${meal.name}`,
          amount,
          sourceIndex: mealIndex,
        })
      })
    })

    const transportTotal = roundBudgetAmount(toBudgetNumber(tripPlan.value.budget?.total_transportation))
    const transportDays = tripPlan.value.days
      .map((day, dayIndex) => ({ day, dayIndex }))
      .filter(({ day }) => Boolean(day.transportation && day.transportation.trim()))

    if (transportTotal > 0 && transportDays.length > 0) {
      const avg = roundBudgetAmount(transportTotal / transportDays.length)
      let remaining = transportTotal

      transportDays.forEach(({ day, dayIndex }, index) => {
        const amount = index === transportDays.length - 1 ? remaining : Math.min(avg, remaining)
        remaining = roundBudgetAmount(remaining - amount)
        items.push({
          id: `transport-${dayIndex}`,
          type: 'transport',
          dayIndex,
          dayNumber: day.day_index + 1,
          name: day.transportation,
          amount: roundBudgetAmount(amount),
        })
      })
    }

    return items
  })

  const filteredBudgetItems = computed<BudgetDetailItem[]>(() => {
    let items = budgetItems.value

    if (filterType.value !== 'all') {
      items = items.filter((item) => item.type === filterType.value)
    }

    const sorted = [...items]
    sorted.sort((a, b) => {
      const dayA = a.dayNumber ?? Number.MAX_SAFE_INTEGER
      const dayB = b.dayNumber ?? Number.MAX_SAFE_INTEGER

      switch (sortMode.value) {
        case 'amountAsc':
          return a.amount - b.amount
        case 'dayAsc':
          return dayA - dayB || b.amount - a.amount
        case 'dayDesc':
          return dayB - dayA || b.amount - a.amount
        case 'amountDesc':
        default:
          return b.amount - a.amount
      }
    })

    return sorted
  })

  const categorySlices = computed<BudgetCategorySlice[]>(() => {
    const budget = tripPlan.value?.budget
    const rows: Array<{ key: BudgetCategoryKey; label: string; amount: number }> = [
      { key: 'attraction', label: t('result.budget.attraction'), amount: Number(budget?.total_attractions ?? 0) },
      { key: 'hotel', label: t('result.budget.hotel'), amount: Number(budget?.total_hotels ?? 0) },
      { key: 'meal', label: t('result.budget.meal'), amount: Number(budget?.total_meals ?? 0) },
      { key: 'transport', label: t('result.budget.transport'), amount: Number(budget?.total_transportation ?? 0) },
    ]
    if (budget?.total_inter_city_transport) {
      rows.push({
        key: 'interCity',
        label: t('result.interCityTransport'),
        amount: Number(budget.total_inter_city_transport),
      })
    }

    const magnitude = rows.reduce((sum, row) => sum + Math.abs(row.amount), 0)
    return rows.map((row) => ({
      ...row,
      share: magnitude === 0 ? null : Math.abs(row.amount) / magnitude,
    }))
  })

  const applyAmount = (item: BudgetDetailItem, rawAmount: unknown): 'updated' | 'invalid' | 'unchanged' | 'missing' => {
    if (!tripPlan.value || item.dayIndex === null) return 'missing'

    const day = tripPlan.value.days[item.dayIndex]
    if (!day) return 'missing'

    const numeric = Number(String(rawAmount).trim())
    if (!Number.isFinite(numeric) || numeric < 0) return 'invalid'

    const nextAmount = roundBudgetAmount(numeric)
    if (nextAmount === roundBudgetAmount(item.amount)) return 'unchanged'

    let changed = false

    if (item.type === 'attraction' && typeof item.sourceIndex === 'number' && day.attractions[item.sourceIndex]) {
      day.attractions[item.sourceIndex].ticket_price = nextAmount
      changed = true
    }

    if (item.type === 'meal' && typeof item.sourceIndex === 'number' && day.meals[item.sourceIndex]) {
      day.meals[item.sourceIndex].estimated_cost = nextAmount
      changed = true
    }

    if (item.type === 'hotel' && day.hotel) {
      day.hotel.estimated_cost = nextAmount
      changed = true
    }

    const transportationTotal =
      item.type === 'transport'
        ? Math.max(
            0,
            roundBudgetAmount(toBudgetNumber(tripPlan.value.budget?.total_transportation) - item.amount + nextAmount)
          )
        : undefined

    if (item.type === 'transport' && day.transportation && day.transportation.trim()) {
      changed = true
    }

    if (!changed) return 'missing'

    recalculateBudgetTotals(transportationTotal)
    persist()
    return 'updated'
  }

  const deleteItem = (item: BudgetDetailItem): boolean => {
    if (!tripPlan.value || item.dayIndex === null) return false

    const day = tripPlan.value.days[item.dayIndex]
    if (!day) return false

    let changed = false
    let restorePayload: BudgetRestorePayload | null = null

    if (item.type === 'attraction' && typeof item.sourceIndex === 'number') {
      const attraction = day.attractions[item.sourceIndex]
      if (attraction) {
        restorePayload = {
          type: 'attraction',
          attraction: cloneData(attraction),
          insertIndex: item.sourceIndex,
        }
        day.attractions.splice(item.sourceIndex, 1)
        changed = true
      }
    }

    if (item.type === 'meal' && typeof item.sourceIndex === 'number') {
      const meal = day.meals[item.sourceIndex]
      if (meal) {
        restorePayload = {
          type: 'meal',
          meal: cloneData(meal),
          insertIndex: item.sourceIndex,
        }
        day.meals.splice(item.sourceIndex, 1)
        changed = true
      }
    }

    if (item.type === 'hotel') {
      if (day.hotel) {
        restorePayload = {
          type: 'hotel',
          hotel: cloneData(day.hotel),
          accommodation: day.accommodation || '',
        }
        day.hotel = undefined
        day.accommodation = ''
        changed = true
      }
    }

    if (item.type === 'transport') {
      if (day.transportation && day.transportation.trim()) {
        restorePayload = {
          type: 'transport',
          transportation: day.transportation,
        }
        day.transportation = ''
        changed = true
      }
    }

    if (!changed || !restorePayload) return false

    scheduleUndo({
      uid: `${item.id}-${Date.now()}`,
      base: cloneData(item),
      payload: restorePayload,
    })

    const transportationTotal =
      item.type === 'transport'
        ? Math.max(
            0,
            roundBudgetAmount(
              toBudgetNumber(tripPlan.value.budget?.total_transportation) - roundBudgetAmount(item.amount)
            )
          )
        : undefined

    recalculateBudgetTotals(transportationTotal)
    persist()
    options?.onLinkedChange?.()
    return true
  }

  const restoreUndo = (): boolean => {
    const pendingItem = undoItem.value
    if (!tripPlan.value || !pendingItem || pendingItem.base.dayIndex === null) return false

    const day = tripPlan.value.days[pendingItem.base.dayIndex]
    if (!day) return false

    let changed = false

    if (pendingItem.payload.type === 'attraction') {
      const insertAt = Math.max(0, Math.min(pendingItem.payload.insertIndex, day.attractions.length))
      day.attractions.splice(insertAt, 0, cloneData(pendingItem.payload.attraction))
      changed = true
    }

    if (pendingItem.payload.type === 'meal') {
      const insertAt = Math.max(0, Math.min(pendingItem.payload.insertIndex, day.meals.length))
      day.meals.splice(insertAt, 0, cloneData(pendingItem.payload.meal))
      changed = true
    }

    if (pendingItem.payload.type === 'hotel') {
      day.hotel = cloneData(pendingItem.payload.hotel)
      day.accommodation = pendingItem.payload.accommodation
      changed = true
    }

    if (pendingItem.payload.type === 'transport') {
      day.transportation = pendingItem.payload.transportation
      changed = true
    }

    if (!changed) return false

    const transportationTotal =
      pendingItem.base.type === 'transport'
        ? roundBudgetAmount(toBudgetNumber(tripPlan.value.budget?.total_transportation) + pendingItem.base.amount)
        : undefined

    recalculateBudgetTotals(transportationTotal)
    clearUndo()
    persist()
    options?.onLinkedChange?.()
    return true
  }

  onUnmounted(() => {
    clearUndoTimer()
  })

  return {
    filterType,
    sortMode,
    undoItem,
    budgetItems,
    filteredBudgetItems,
    categorySlices,
    getBudgetTypeLabel,
    formatBudgetAmount,
    recalculateBudgetTotals,
    applyAmount,
    deleteItem,
    restoreUndo,
    clearUndo,
  }
}
