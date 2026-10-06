<template>
  <div v-if="node" class="node-detail">
    <h3 class="node-detail__name">{{ node.name }}</h3>
    <p class="node-detail__type">{{ typeLabel }}</p>
    <p v-if="description" class="node-detail__desc">{{ description }}</p>
    <p v-else class="node-detail__desc is-empty">{{ t('result.graph.noDescription') }}</p>

    <section v-if="outgoing.length" class="node-detail__group" :aria-labelledby="outId">
      <h4 :id="outId" class="node-detail__heading">{{ t('result.graph.outgoing') }}</h4>
      <ul class="node-detail__list">
        <li v-for="item in outgoing" :key="item.edge.uid">
          <button type="button" class="node-detail__link" @click="emit('select', item.node.uid)">
            <span>{{ item.node.name }}</span>
            <span v-if="item.edge.label" class="node-detail__rel">{{ item.edge.label }}</span>
          </button>
        </li>
      </ul>
    </section>

    <section v-if="incoming.length" class="node-detail__group" :aria-labelledby="inId">
      <h4 :id="inId" class="node-detail__heading">{{ t('result.graph.incoming') }}</h4>
      <ul class="node-detail__list">
        <li v-for="item in incoming" :key="item.edge.uid">
          <button type="button" class="node-detail__link" @click="emit('select', item.node.uid)">
            <span>{{ item.node.name }}</span>
            <span v-if="item.edge.label" class="node-detail__rel">{{ item.edge.label }}</span>
          </button>
        </li>
      </ul>
    </section>

    <p v-if="!outgoing.length && !incoming.length" class="node-detail__empty">
      {{ t('result.graph.noRelations') }}
    </p>
  </div>
  <div v-else class="node-detail node-detail--hint">
    <p>{{ t('result.graph.hint') }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ResolvedGraphEdge, ResolvedGraphNode } from '@/components/result/graph/graphModel'
import { isKnownCategory } from '@/components/result/graph/graphModel'

const props = defineProps<{
  node: ResolvedGraphNode | null
  outgoing: Array<{ edge: ResolvedGraphEdge; node: ResolvedGraphNode }>
  incoming: Array<{ edge: ResolvedGraphEdge; node: ResolvedGraphNode }>
}>()

const emit = defineEmits<{
  select: [id: string]
}>()

const { t } = useI18n()
const outId = 'graph-node-outgoing'
const inId = 'graph-node-incoming'

const typeLabel = computed(() => {
  if (!props.node) return ''
  if (isKnownCategory(props.node.categoryKey)) {
    return t(`result.graph.categories.${props.node.categoryKey}`)
  }
  return props.node.categoryName || props.node.categoryKey
})

const description = computed(() => {
  const value = props.node?.value
  return value ? String(value) : ''
})
</script>

<style scoped>
.node-detail {
  display: grid;
  gap: var(--space-3);
  min-width: 0;
}

.node-detail__name {
  margin: 0;
  font-size: var(--text-h3);
  color: var(--color-text);
}

.node-detail__type,
.node-detail__desc,
.node-detail__empty,
.node-detail--hint p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--text-body);
}

.node-detail__desc.is-empty {
  font-style: italic;
}

.node-detail__heading {
  margin: 0 0 var(--space-2);
  font-size: var(--text-caption);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.node-detail__list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: var(--space-2);
}

.node-detail__link {
  width: 100%;
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
  text-align: left;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-raised);
  color: var(--color-text);
  cursor: pointer;
}

.node-detail__link:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.node-detail__rel {
  color: var(--color-text-muted);
  font-size: var(--text-caption);
}

.node-detail--hint {
  padding: var(--space-4);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-lg);
}
</style>
