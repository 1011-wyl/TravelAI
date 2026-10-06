<template>
  <div class="graph-canvas" :class="{ 'is-enter': enterReady && !reduceMotion }">
    <div ref="hostRef" class="graph-canvas__host" role="img" :aria-label="canvasAriaLabel" />
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTheme } from '@/composables/useTheme'
import type { ResolvedGraphEdge, ResolvedGraphNode } from '@/components/result/graph/graphModel'
import { buildStaticPositions, categoryHex, isKnownCategory } from '@/components/result/graph/graphModel'

type EChartsNS = typeof import('echarts')
type EChartsInst = import('echarts').ECharts

let cachedEcharts: EChartsNS | null = null

const loadEcharts = async (): Promise<EChartsNS> => {
  if (cachedEcharts) return cachedEcharts
  cachedEcharts = await import('echarts')
  return cachedEcharts
}

const props = defineProps<{
  nodes: ResolvedGraphNode[]
  edges: ResolvedGraphEdge[]
  selectedId: string | null
  reduceMotion: boolean
  canvasAriaLabel: string
}>()

const emit = defineEmits<{
  select: [id: string]
  clear: []
  loadError: []
  ready: []
}>()

const { t } = useI18n()
const { resolvedTheme } = useTheme()
const hostRef = ref<HTMLElement | null>(null)
const enterReady = ref(false)
let chart: EChartsInst | null = null
let observer: ResizeObserver | null = null
let generation = 0
let clickBound = false
let zrClick: ((event: { target?: unknown }) => void) | null = null
let chartClick: ((params: { dataType?: string; data?: unknown }) => void) | null = null

const categoryLabel = (node: ResolvedGraphNode) => {
  if (isKnownCategory(node.categoryKey)) return t(`result.graph.categories.${node.categoryKey}`)
  return node.categoryName || node.categoryKey
}

const palette = () => {
  const dark = resolvedTheme.value === 'dark'
  return {
    tooltipBg: dark ? 'rgba(16, 28, 26, 0.96)' : 'rgba(255, 255, 255, 0.96)',
    tooltipBorder: dark ? 'rgba(61, 125, 116, 0.45)' : 'rgba(20, 125, 114, 0.28)',
    tooltipText: dark ? '#f4f7f4' : '#16302b',
    edge: dark ? 'rgba(155, 176, 170, 0.45)' : 'rgba(93, 114, 109, 0.4)',
    edgeLabel: dark ? '#c5d4cf' : '#5d726d',
    accent: '#147d72',
  }
}

// Light sand/coral/unknown nodes need dark labels; white fails 4.5:1.
const readableNodeLabel = (hex: string) => {
  const luminance = (color: string) => {
    const rgb = [1, 3, 5].map((offset) => parseInt(color.slice(offset, offset + 2), 16) / 255)
    const linear = rgb.map((channel) => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4)
    return linear[0] * 0.2126 + linear[1] * 0.7152 + linear[2] * 0.0722
  }
  const bg = luminance(hex)
  const darkRatio = (bg + 0.05) / (luminance('#16302b') + 0.05)
  const lightRatio = 1.05 / (bg + 0.05)
  return darkRatio > lightRatio ? '#16302b' : '#ffffff'
}

const buildOption = (width: number, height: number) => {
  const colors = palette()
  const positions = buildStaticPositions(props.nodes, props.edges, width, height)
  const staticLayout = props.reduceMotion
  const data = props.nodes.map((node) => {
    const point = positions.get(node.uid)
    const size = node.hasWeight ? node.visualSize : 56
    const color = categoryHex(node.categoryKey)
    const selected = props.selectedId === node.uid
    return {
      id: node.uid,
      name: node.name,
      category: node.category,
      value: node.value,
      x: point?.x ?? width / 2,
      y: point?.y ?? height / 2,
      symbolSize: size,
      itemStyle: {
        color,
        borderColor: selected ? colors.accent : 'transparent',
        borderWidth: selected ? 3 : 0,
      },
      label: {
        show: size >= 56,
        position: 'inside' as const,
        color: readableNodeLabel(color),
        fontSize: size >= 90 ? 10 : 8,
        fontWeight: 600 as const,
        formatter: () => {
          const name = String(node.name || '')
          return name.length > 6 ? `${name.slice(0, 6)}…` : name
        },
      },
    }
  })
  const links = props.edges.map((edge) => {
    const adjacent =
      props.selectedId != null &&
      (edge.sourceUid === props.selectedId || edge.targetUid === props.selectedId)
    return {
      source: edge.sourceUid,
      target: edge.targetUid,
      label: edge.label,
      lineStyle: {
        color: adjacent ? colors.accent : colors.edge,
        width: adjacent ? 2.4 : 1.4,
        curveness: 0.08,
      },
      labelStyle: {
        show: Boolean(edge.label),
        formatter: edge.label,
        fontSize: 10,
        color: colors.edgeLabel,
      },
    }
  })

  return {
    backgroundColor: 'transparent',
    animation: !props.reduceMotion,
    animationDuration: props.reduceMotion ? 0 : 480,
    animationDurationUpdate: props.reduceMotion ? 0 : 180,
    tooltip: {
      trigger: 'item' as const,
      backgroundColor: colors.tooltipBg,
      borderColor: colors.tooltipBorder,
      borderWidth: 1,
      padding: [10, 14],
      textStyle: { color: colors.tooltipText, fontSize: 13 },
      formatter: (params: { dataType?: string; data?: Record<string, unknown> }) => {
        if (params.dataType === 'node') {
          const node = props.nodes.find((item) => item.uid === String(params.data?.id))
          if (!node) return ''
          const typeLine = `${t('result.graph.type')}: ${categoryLabel(node)}`
          const detail = node.value
            ? `<br/>${t('result.graph.detail')}: ${node.value}`
            : ''
          return `<b>${node.name}</b><br/>${typeLine}${detail}`
        }
        if (params.dataType === 'edge') {
          const label = String(params.data?.label || '')
          return label || t('result.graph.relation')
        }
        return ''
      },
    },
    series: [
      {
        id: 'inspiration-graph',
        type: 'graph',
        layout: staticLayout ? 'none' : 'force',
        data,
        links: links.map((link) => ({
          ...link,
          label: {
            show: Boolean(link.label),
            formatter: link.label || '',
            fontSize: 10,
            color: colors.edgeLabel,
          },
        })),
        roam: true,
        draggable: !props.reduceMotion,
        zoom: 1,
        force: staticLayout
          ? undefined
          : {
              initLayout: 'none',
              repulsion: width < 500 ? 360 : 520,
              gravity: width < 500 ? 0.2 : 0.06,
              edgeLength: width < 500 ? [60, 140] : [95, 220],
              friction: 0.2,
              layoutAnimation: !props.reduceMotion,
            },
        emphasis: {
          focus: 'adjacency',
          lineStyle: { width: 3, color: colors.accent },
        },
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: [0, 8],
        silent: false,
      },
    ],
  } as import('echarts').EChartsOption
}

const unbind = () => {
  if (!chart) return
  chart.off('click')
  chart.getZr().off('click')
  clickBound = false
  chartClick = null
  zrClick = null
}

const bind = () => {
  if (!chart || clickBound) return
  chartClick = (params: { dataType?: string; data?: unknown }) => {
    const data = params.data as { id?: string } | null | undefined
    if (params.dataType === 'node' && data?.id != null) {
      emit('select', String(data.id))
      return
    }
    if (params.dataType === 'edge') return
    emit('clear')
  }
  zrClick = (event) => {
    if (!event.target) emit('clear')
  }
  chart.on('click', chartClick as never)
  chart.getZr().on('click', zrClick)
  clickBound = true
}

const applyHighlight = () => {
  if (!chart) return
  chart.dispatchAction({ type: 'downplay', seriesIndex: 0 })
  if (!props.selectedId) return
  const index = props.nodes.findIndex((node) => node.uid === props.selectedId)
  if (index < 0) return
  chart.dispatchAction({ type: 'highlight', seriesIndex: 0, dataIndex: index })
}

const paint = (mode: 'full' | 'style') => {
  if (!chart || !hostRef.value) return
  const width = Math.max(hostRef.value.clientWidth, 1)
  const height = Math.max(hostRef.value.clientHeight, 1)
  if (width < 8 || height < 8) return
  const option = buildOption(width, height)
  if (mode === 'style' && chart.getOption()) {
    const current = chart.getOption() as { series?: Array<{ data?: Array<{ id?: string; x?: number; y?: number }> }> }
    const laid = current.series?.[0]?.data || []
    const byId = new Map(laid.map((item) => [String(item.id), item]))
    const series = option.series as Array<{ data: Array<{ id: string; x: number; y: number; layout?: string }> }>
    series[0].data = series[0].data.map((item) => {
      const prev = byId.get(item.id)
      return prev && Number.isFinite(prev.x) && Number.isFinite(prev.y)
        ? { ...item, x: prev.x as number, y: prev.y as number }
        : item
    })
    ;(option.series as Array<Record<string, unknown>>)[0].layout = 'none'
    ;(option.series as Array<Record<string, unknown>>)[0].force = undefined
  }
  chart.setOption(option, { notMerge: mode === 'full' })
  applyHighlight()
}

const initChart = async (taskId: number) => {
  const host = hostRef.value
  if (!host) return
  try {
    const echarts = await loadEcharts()
    if (taskId !== generation) return
    if (!host.isConnected || host.clientWidth < 8 || host.clientHeight < 8) return
    if (chart) {
      unbind()
      chart.dispose()
      chart = null
    }
    chart = echarts.init(host)
    if (taskId !== generation) {
      chart.dispose()
      chart = null
      return
    }
    paint('full')
    bind()
    enterReady.value = true
    emit('ready')
  } catch (error) {
    console.warn('[graph] echarts init failed', error)
    if (taskId === generation) emit('loadError')
  }
}

const resetView = () => {
  if (!chart || !hostRef.value) return
  const width = hostRef.value.clientWidth
  const height = hostRef.value.clientHeight
  chart.setOption({
    series: [
      {
        id: 'inspiration-graph',
        zoom: 1,
        center: [width / 2, height / 2],
      },
    ],
  })
}

watch(
  () => [props.nodes, props.edges, props.reduceMotion] as const,
  () => {
    if (chart) paint('full')
  }
)

watch(
  () => props.selectedId,
  () => {
    if (!chart) return
    paint('style')
  }
)

watch(resolvedTheme, () => {
  if (chart) paint('style')
})

onMounted(async () => {
  const taskId = ++generation
  await nextTick()
  observer = new ResizeObserver(() => {
    if (!chart) {
      void initChart(generation)
      return
    }
    chart.resize()
  })
  if (hostRef.value) observer.observe(hostRef.value)
  await initChart(taskId)
})

onUnmounted(() => {
  generation += 1
  observer?.disconnect()
  observer = null
  unbind()
  chart?.dispose()
  chart = null
})

defineExpose({ resetView })
</script>

<style scoped>
.graph-canvas {
  min-height: 22rem;
  height: min(36rem, 70vh);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  overflow: hidden;
}

.graph-canvas__host {
  width: 100%;
  height: 100%;
}

.graph-canvas.is-enter {
  animation: graph-enter 480ms var(--ease-standard);
}

@keyframes graph-enter {
  from {
    opacity: 0;
    transform: scale(0.98);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .graph-canvas.is-enter {
    animation: none;
  }
}
</style>
