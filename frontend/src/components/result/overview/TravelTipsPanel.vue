<template>
  <section v-if="tips.length" class="travel-tips" aria-labelledby="travel-tips-title">
    <h3 id="travel-tips-title">{{ t('result.overview.tipsTitle') }}</h3>
    <ul>
      <li v-for="(tip, index) in tips" :key="index">{{ tip }}</li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { TripPlan } from '@/types'

const props = defineProps<{
  plan: TripPlan
}>()

const { t } = useI18n()

const tips = computed(() => {
  const items: string[] = []
  if (props.plan.overall_suggestions?.trim()) items.push(props.plan.overall_suggestions.trim())
  props.plan.days.forEach((day) => {
    if (day.is_transfer_day && day.transfer_info?.trim()) items.push(day.transfer_info.trim())
  })
  return items
})
</script>

<style scoped>
.travel-tips h3 {
  margin: 0 0 var(--space-3);
}

.travel-tips ul {
  margin: 0;
  padding-left: 1.2em;
  color: var(--color-text-muted);
}
</style>
