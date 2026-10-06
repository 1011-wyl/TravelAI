import { ref, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import type { TripPlan } from '@/types'

export const useItineraryEditor = (
  tripPlan: Ref<TripPlan | null>,
  options: {
    persistPlan: (plan: TripPlan) => void
    recalculateBudgetTotals: () => void
    clearBudgetUndo: () => void
    onSaved?: () => void
  }
) => {
  const { t } = useI18n()
  const editMode = ref(false)
  const originalPlan = ref<TripPlan | null>(null)

  const toggleEditMode = () => {
    editMode.value = true
    originalPlan.value = JSON.parse(JSON.stringify(tripPlan.value))
    message.info(t('result.messages.enterEditMode'))
  }

  const saveChanges = () => {
    editMode.value = false
    options.recalculateBudgetTotals()
    if (tripPlan.value) {
      options.persistPlan(tripPlan.value)
    }
    message.success(t('result.messages.changesSaved'))
    options.onSaved?.()
  }

  const cancelEdit = () => {
    if (originalPlan.value) {
      tripPlan.value = JSON.parse(JSON.stringify(originalPlan.value))
    }
    options.clearBudgetUndo()
    editMode.value = false
    message.info(t('result.messages.editCanceled'))
  }

  /** Exit edit without restoring old snapshot onto the current tripPlan. */
  const discardEdit = () => {
    originalPlan.value = null
    editMode.value = false
  }

  const deleteAttraction = (dayIndex: number, attrIndex: number) => {
    if (!tripPlan.value) return

    const day = tripPlan.value.days[dayIndex]
    if (!day) return
    if (day.attractions.length <= 1) {
      message.warning(t('result.messages.keepOneAttraction'))
      return
    }

    day.attractions.splice(attrIndex, 1)
    options.recalculateBudgetTotals()
    message.success(t('result.messages.attractionDeleted'))
  }

  const moveAttraction = (dayIndex: number, attrIndex: number, direction: 'up' | 'down') => {
    if (!tripPlan.value) return

    const day = tripPlan.value.days[dayIndex]
    if (!day) return
    const attractions = day.attractions

    if (direction === 'up' && attrIndex > 0) {
      ;[attractions[attrIndex], attractions[attrIndex - 1]] = [attractions[attrIndex - 1], attractions[attrIndex]]
    } else if (direction === 'down' && attrIndex < attractions.length - 1) {
      ;[attractions[attrIndex], attractions[attrIndex + 1]] = [attractions[attrIndex + 1], attractions[attrIndex]]
    }
  }

  const updateAttractionField = (
    dayIndex: number,
    attrIndex: number,
    field: 'address' | 'visit_duration' | 'description',
    value: string | number
  ) => {
    if (!tripPlan.value) return
    const attraction = tripPlan.value.days[dayIndex]?.attractions[attrIndex]
    if (!attraction) return
    if (field === 'visit_duration') {
      attraction.visit_duration = Number(value)
      return
    }
    attraction[field] = String(value)
  }

  return {
    editMode,
    toggleEditMode,
    saveChanges,
    cancelEdit,
    discardEdit,
    deleteAttraction,
    moveAttraction,
    updateAttractionField,
  }
}
