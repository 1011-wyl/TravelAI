import { computed, nextTick, onUnmounted, ref, watch, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Attraction, TripPlan } from '@/types'
import type { ExportPlan } from '@/components/result/export/TripExportDocument.vue'

export type ExportPhase =
  | 'idle'
  | 'options'
  | 'preparing'
  | 'images'
  | 'map'
  | 'rendering'
  | 'downloading'
  | 'done'
  | 'failed'
  | 'map-failed'
  | 'oversized'

type Html2CanvasFn = (typeof import('html2canvas'))['default']

const EXPORT_WIDTH = 800
const EXPORT_SCALE = 2
const MAX_CANVAS_PIXELS = 16_000_000
const IMAGE_WAIT_MS = 8000
const MAP_WAIT_MS = 20000
const MAP_SETTLE_MS = 400
const SLICE_HEIGHT = 4000

let html2canvasModule: Html2CanvasFn | null = null

const clonePlan = (plan: TripPlan): ExportPlan => JSON.parse(JSON.stringify(plan)) as ExportPlan

const wait = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms))

const canvasPixels = (cssHeight: number) => EXPORT_WIDTH * EXPORT_SCALE * cssHeight * EXPORT_SCALE

const createExportCanvas = (cssWidth: number, cssHeight: number) => {
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(1, Math.floor(cssWidth * EXPORT_SCALE))
  canvas.height = Math.max(1, Math.floor(cssHeight * EXPORT_SCALE))
  return canvas
}

const downloadCanvas = (canvas: HTMLCanvasElement, filename: string) => {
  const link = document.createElement('a')
  link.download = filename
  link.href = canvas.toDataURL('image/png')
  link.click()
}

const waitForImages = async (root: HTMLElement, isLive: () => boolean) => {
  const images = Array.from(root.querySelectorAll('img'))
  await Promise.all(
    images.map((img) => {
      if (img.complete || !isLive()) return Promise.resolve()
      return new Promise<void>((resolve) => {
        const finish = () => {
          window.clearTimeout(timer)
          img.removeEventListener('load', finish)
          img.removeEventListener('error', finish)
          resolve()
        }
        const timer = window.setTimeout(finish, IMAGE_WAIT_MS)
        img.addEventListener('load', finish)
        img.addEventListener('error', finish)
      })
    })
  )
}

export const useTripExport = (options: {
  plan: Ref<TripPlan | null>
  photos: Ref<Record<string, string>>
  planKey: Ref<string>
  resolvePhoto: (attraction: Attraction) => string
  getVisibleMapElement: () => HTMLElement | null
  getDocumentEl: () => HTMLElement | null
  getMapHost: () => {
    getStatus: () => string
    getMapElement: () => HTMLElement | null
    refresh: () => Promise<void>
  } | null
}) => {
  const { t } = useI18n()
  const dialogOpen = ref(false)
  const phase = ref<ExportPhase>('idle')
  const includeMap = ref(false)
  const wantMap = ref(false)
  const useOffscreenMap = ref(false)
  const errorText = ref('')
  const filename = ref('')
  const snapshot = ref<ExportPlan | null>(null)
  const snapshotPhotos = ref<Record<string, string>>({})
  const mapDataUrl = ref('')
  let taskId = 0

  const exporting = computed(() =>
    ['preparing', 'images', 'map', 'rendering', 'downloading'].includes(phase.value)
  )

  const isLive = (currentTask: number) => currentTask === taskId

  const invalidateWork = () => {
    taskId += 1
    useOffscreenMap.value = false
    mapDataUrl.value = ''
    snapshot.value = null
    snapshotPhotos.value = {}
  }

  const closeDialog = () => {
    invalidateWork()
    dialogOpen.value = false
    phase.value = 'idle'
    errorText.value = ''
  }

  const openDialog = () => {
    if (!options.plan.value || exporting.value) return
    includeMap.value = false
    wantMap.value = false
    errorText.value = ''
    filename.value = ''
    dialogOpen.value = true
    phase.value = 'options'
  }

  const captureMapElement = async (html2canvas: Html2CanvasFn, el: HTMLElement) => {
    await wait(MAP_SETTLE_MS)
    const canvas = await html2canvas(el, {
      backgroundColor: '#eaf1ed',
      scale: EXPORT_SCALE,
      logging: false,
      useCORS: true,
      allowTaint: false,
      imageTimeout: IMAGE_WAIT_MS,
      ignoreElements: (element) => {
        const className = typeof element.className === 'string' ? element.className : ''
        return className.includes('gmnoprint') || className.includes('amap-controls')
      },
    })
    return canvas.toDataURL('image/png')
  }

  const waitOffscreenMap = async (currentTask: number) => {
    const started = Date.now()
    while (Date.now() - started < MAP_WAIT_MS) {
      if (!isLive(currentTask)) return false
      const status = options.getMapHost()?.getStatus()
      if (status === 'ready') return true
      if (status === 'failed' || status === 'missing-key') return false
      await wait(200)
    }
    return false
  }

  const captureDocumentSlice = async (
    html2canvas: Html2CanvasFn,
    root: HTMLElement,
    y: number,
    sliceHeight: number
  ) => {
    const canvas = createExportCanvas(EXPORT_WIDTH, sliceHeight)
    return html2canvas(root, {
      canvas,
      backgroundColor: '#f5f7f2',
      scale: EXPORT_SCALE,
      logging: false,
      useCORS: true,
      allowTaint: false,
      imageTimeout: IMAGE_WAIT_MS,
      x: 0,
      y,
      width: EXPORT_WIDTH,
      height: sliceHeight,
      windowWidth: EXPORT_WIDTH,
      windowHeight: sliceHeight,
      scrollX: 0,
      scrollY: -y,
    })
  }

  const renderAndDownload = async (html2canvas: Html2CanvasFn, currentTask: number) => {
    const root = options.getDocumentEl()
    if (!root) throw new Error('export-root-missing')
    phase.value = 'images'
    await waitForImages(root, () => isLive(currentTask))
    if (!isLive(currentTask)) return

    const height = Math.max(root.scrollHeight, root.clientHeight, 1)
    const totalPixels = canvasPixels(height)
    if (totalPixels > MAX_CANVAS_PIXELS * 6) {
      phase.value = 'oversized'
      errorText.value = t('result.export.oversizedDesc')
      return
    }

    phase.value = 'rendering'
    const stamp = new Date().getTime()
    const city = snapshot.value?.city || 'trip'
    const prefix = `${t('result.export.filePrefix')}_${city}_${stamp}`
    const files: string[] = []

    if (totalPixels <= MAX_CANVAS_PIXELS) {
      const canvas = await captureDocumentSlice(html2canvas, root, 0, height)
      if (!isLive(currentTask)) return
      phase.value = 'downloading'
      const name = `${prefix}.png`
      downloadCanvas(canvas, name)
      files.push(name)
    } else {
      const slices = Math.ceil(height / SLICE_HEIGHT)
      for (let index = 0; index < slices; index += 1) {
        if (!isLive(currentTask)) return
        const y = index * SLICE_HEIGHT
        const sliceHeight = Math.min(SLICE_HEIGHT, height - y)
        const canvas = await captureDocumentSlice(html2canvas, root, y, sliceHeight)
        if (!isLive(currentTask)) return
        phase.value = 'downloading'
        const name = `${prefix}_p${index + 1}.png`
        downloadCanvas(canvas, name)
        files.push(name)
      }
    }

    if (!isLive(currentTask)) return
    filename.value = files.join(', ')
    phase.value = 'done'
  }

  const runExport = async (withMap: boolean) => {
    if (!options.plan.value) return
    const currentTask = ++taskId
    wantMap.value = withMap
    snapshot.value = clonePlan(options.plan.value)
    snapshotPhotos.value = {}
    Object.entries(options.photos.value).forEach(([name, url]) => {
      snapshotPhotos.value[name] = url
    })
    snapshot.value.days.forEach((day) => {
      day.attractions.forEach((attraction) => {
        const resolved = options.resolvePhoto(attraction)
        if (resolved) snapshotPhotos.value[attraction.name] = resolved
      })
    })
    mapDataUrl.value = ''
    useOffscreenMap.value = false
    phase.value = 'preparing'
    errorText.value = ''
    await nextTick()
    if (!isLive(currentTask)) return

    try {
      const html2canvas = html2canvasModule || (await import('html2canvas')).default
      html2canvasModule = html2canvas
      if (!isLive(currentTask)) return

      if (withMap) {
        phase.value = 'map'
        const visible = options.getVisibleMapElement()
        if (visible) {
          try {
            const dataUrl = await captureMapElement(html2canvas, visible)
            if (!isLive(currentTask)) return
            mapDataUrl.value = dataUrl
          } catch (error) {
            console.warn('地图截图失败', error)
            if (!isLive(currentTask)) return
            phase.value = 'map-failed'
            errorText.value = t('result.export.mapFailedDesc')
            return
          }
        } else {
          useOffscreenMap.value = true
          await nextTick()
          if (!isLive(currentTask)) return
          const ready = await waitOffscreenMap(currentTask)
          if (!isLive(currentTask)) return
          const hostEl = options.getMapHost()?.getMapElement()
          if (!ready || !hostEl) {
            useOffscreenMap.value = false
            phase.value = 'map-failed'
            errorText.value = t('result.export.mapFailedDesc')
            return
          }
          try {
            const dataUrl = await captureMapElement(html2canvas, hostEl)
            if (!isLive(currentTask)) return
            mapDataUrl.value = dataUrl
          } catch (error) {
            console.warn('地图截图失败', error)
            if (!isLive(currentTask)) return
            phase.value = 'map-failed'
            errorText.value = t('result.export.mapFailedDesc')
            return
          } finally {
            if (isLive(currentTask)) useOffscreenMap.value = false
          }
        }
      }

      await nextTick()
      if (!isLive(currentTask)) return
      await renderAndDownload(html2canvas, currentTask)
    } catch (error) {
      console.error('导出图片失败:', error)
      if (!isLive(currentTask)) return
      phase.value = 'failed'
      errorText.value = t('result.export.failedDesc')
    }
  }

  const confirm = (withMap: boolean) => {
    includeMap.value = withMap
    void runExport(withMap)
  }

  const retry = () => {
    void runExport(wantMap.value)
  }

  const retryMap = () => {
    void runExport(true)
  }

  const continueWithoutMap = () => {
    useOffscreenMap.value = false
    mapDataUrl.value = ''
    wantMap.value = false
    void runExport(false)
  }

  const cancel = () => {
    if (
      phase.value === 'done' ||
      phase.value === 'options' ||
      phase.value === 'failed' ||
      phase.value === 'map-failed' ||
      phase.value === 'oversized' ||
      phase.value === 'idle'
    ) {
      closeDialog()
      return
    }
    if (phase.value === 'preparing' || phase.value === 'images' || phase.value === 'map') {
      closeDialog()
    }
  }

  watch(
    () => options.planKey.value,
    (next, prev) => {
      // Invalidate export work as soon as plan switch starts (empty key).
      if (next === prev) return
      if (prev == null && !next) return
      if (prev !== undefined) closeDialog()
    }
  )

  onUnmounted(() => {
    invalidateWork()
  })

  return {
    dialogOpen,
    phase,
    includeMap,
    errorText,
    filename,
    snapshot,
    snapshotPhotos,
    mapDataUrl,
    useOffscreenMap,
    exporting,
    openDialog,
    confirm,
    retry,
    retryMap,
    continueWithoutMap,
    cancel,
    closeDialog,
    exportWidth: EXPORT_WIDTH,
    exportScale: EXPORT_SCALE,
  }
}
