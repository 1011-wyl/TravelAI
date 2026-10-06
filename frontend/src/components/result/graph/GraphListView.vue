<template>
  <div class="graph-list">
    <section
      v-for="group in groups"
      :key="group.key"
      class="graph-list__group"
      :aria-labelledby="`graph-list-${group.key}`"
    >
      <h3 :id="`graph-list-${group.key}`" class="graph-list__heading">{{ groupLabel(group) }}</h3>
      <ul class="graph-list__items">
        <li v-for="node in group.nodes" :key="node.uid">
          <button
            type="button"
            class="graph-list__item"
            :class="{ 'is-selected': node.uid === selectedId }"
            :aria-pressed="node.uid === selectedId"
            @click="emit('select', node.uid)"
          >
            <span class="graph-list__name">{{ node.name }}</span>
            <span class="graph-list__meta">
              {{ nodeType(node) }} · {{ t('result.graph.relationCount', { count: relationCount(node.uid) }) }}
            </span>
          </button>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { ResolvedGraphNode } from '@/components/result/graph/graphModel'
import { isKnownCategory } from '@/components/result/graph/graphModel'

defineProps<{
  groups: Array<{ key: string; name: string; nodes: ResolvedGraphNode[] }>
  selectedId: string | null
  relationCount: (uid: string) => number
}>()

const emit = defineEmits<{
  select: [id: string]
}>()

const { t } = useI18n()

const nodeType = (node: ResolvedGraphNode) => {
  if (isKnownCategory(node.categoryKey)) return t(`result.graph.categories.${node.categoryKey}`)
  return node.categoryName || node.categoryKey
}

const groupLabel = (group: { key: string; name: string }) => {
  if (isKnownCategory(group.key)) return t(`result.graph.categories.${group.key}`)
  return group.name || group.key
}
</script>

<style scoped>
.graph-list {
  display: grid;
  gap: var(--space-5);
  min-width: 0;
}

.graph-list__heading {
  margin: 0 0 var(--space-2);
  font-size: var(--text-h3);
  color: var(--color-text);
}

.graph-list__items {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: var(--space-2);
}

.graph-list__item {
  width: 100%;
  display: grid;
  gap: 2px;
  text-align: left;
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
  transition: border-color 180ms var(--ease-standard), background-color 180ms var(--ease-standard);
}

.graph-list__item.is-selected {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.graph-list__item:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.graph-list__name {
  font-weight: 600;
}

.graph-list__meta {
  color: var(--color-text-muted);
  font-size: var(--text-caption);
}

@media (prefers-reduced-motion: reduce) {
  .graph-list__item {
    transition: none;
  }
}
</style>
