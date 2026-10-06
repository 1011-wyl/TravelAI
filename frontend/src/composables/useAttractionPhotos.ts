import { onUnmounted, ref, watch, type Ref } from 'vue'
import type { Attraction, TripPlan } from '@/types'
import { getRuntimeApiBaseUrl } from '@/services/api'

export const useAttractionPhotos = (options: {
  plan: Ref<TripPlan | null>
  planKey: Ref<string>
}) => {
  const attractionPhotos = ref<Record<string, string>>({})
  let loadId = 0

  const toProxiedPhotoUrl = (url?: string | null): string => {
    if (!url) return ''
    return `${getRuntimeApiBaseUrl()}/api/poi/image?url=${encodeURIComponent(url)}`
  }

  const getAttractionImage = (name: string, _index = 0): string => {
    if (attractionPhotos.value[name]) {
      return attractionPhotos.value[name]
    }

    const bg = '#1a262f'
    const textColor = 'rgba(255,255,255,0.4)'
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">
    <rect width="400" height="300" fill="${bg}"/>
    <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="${textColor}">${name}</text>
  </svg>`

    return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg)))}`
  }

  const itineraryImage = (attraction: Attraction, index: number) => {
    return toProxiedPhotoUrl(attraction.image_url) || getAttractionImage(attraction.name, index)
  }

  const resolvePhoto = (attraction: Attraction) => {
    return toProxiedPhotoUrl(attraction.image_url) || attractionPhotos.value[attraction.name] || ''
  }

  const loadAttractionPhotos = async () => {
    const plan = options.plan.value
    if (!plan) return

    const currentLoad = ++loadId
    const apiBase = getRuntimeApiBaseUrl()
    const city = plan.city
    const uniqueNames = Array.from(
      new Set(plan.days.flatMap((day) => day.attractions.map((attraction) => attraction.name)))
    ).filter((name) => name && !attractionPhotos.value[name])

    if (uniqueNames.length === 0) return

    const concurrencyLimit = 4
    let currentIndex = 0

    const loadNextPhoto = async () => {
      while (currentIndex < uniqueNames.length) {
        if (currentLoad !== loadId) return
        const index = currentIndex
        currentIndex += 1
        const name = uniqueNames[index]

        try {
          const response = await fetch(
            `${apiBase}/api/poi/photo?name=${encodeURIComponent(name)}&city=${encodeURIComponent(city)}`
          )
          const data = await response.json()
          if (currentLoad !== loadId) return
          if (data.success && data.data.photo_url) {
            attractionPhotos.value[name] = `${apiBase}/api/poi/image?name=${encodeURIComponent(name)}`
          }
        } catch (err) {
          console.error(`获取${name}图片失败:`, err)
        }
      }
    }

    const workers = Array.from(
      { length: Math.min(concurrencyLimit, uniqueNames.length) },
      () => loadNextPhoto()
    )
    await Promise.all(workers)
  }

  watch(
    () => options.planKey.value,
    (next, prev) => {
      // Invalidate as soon as the key changes (including switch-start empty key).
      if (next === prev) return
      if (prev == null && !next) return
      loadId += 1
      attractionPhotos.value = {}
    }
  )

  onUnmounted(() => {
    loadId += 1
  })

  return {
    attractionPhotos,
    toProxiedPhotoUrl,
    getAttractionImage,
    itineraryImage,
    resolvePhoto,
    loadAttractionPhotos,
  }
}
