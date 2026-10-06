import { nextTick, ref, type Ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import type { Attraction, TripPlan } from '@/types'
import {
  getBackendRuntimeSettings,
  getRuntimeGoogleMapsApiKey,
  getRuntimeMapJsKey,
  setRuntimeGoogleMapsApiKey,
} from '@/services/api'

export const OPEN_SETTINGS_EVENT = 'travelai:open-settings'

export type TravelMapStatus =
  | 'checking-key'
  | 'loading-google'
  | 'fallback-amap'
  | 'loading-amap'
  | 'missing-key'
  | 'failed'
  | 'ready'

export type TravelMapProvider = 'google' | 'amap'

export type MapStop = {
  id: string
  dayIndex: number
  attrIndex: number
  globalIndex: number
  name: string
  address: string
  visit_duration: number
  description: string
  locatable: boolean
  location?: { longitude: number; latitude: number }
}

type RouteMode = 'driving' | 'walking' | 'straight'
type RoutePoint = [number, number]

const GOOGLE_CONTAINER_ID = 'google-map-container'
const AMAP_CONTAINER_ID = 'amap-container'
const GOOGLE_TIMEOUT_MS = 5000

const ROUTE_STYLE_PRESETS: Record<
  RouteMode,
  {
    strokeColor: string
    strokeWeight: number
    strokeOpacity: number
    strokeStyle: 'solid' | 'dashed'
    strokeDasharray?: number[]
    lineJoin?: 'round' | 'miter' | 'bevel'
    lineCap?: 'butt' | 'round' | 'square'
    outlineColor?: string
    borderWeight?: number
  }
> = {
  driving: {
    strokeColor: '#37b4ff',
    strokeWeight: 3.5,
    strokeOpacity: 0.92,
    strokeStyle: 'solid',
    lineJoin: 'round',
    lineCap: 'round',
    outlineColor: 'rgba(4, 19, 32, 0.7)',
    borderWeight: 1,
  },
  walking: {
    strokeColor: '#6ad38f',
    strokeWeight: 3,
    strokeOpacity: 0.9,
    strokeStyle: 'dashed',
    strokeDasharray: [12, 8],
    lineJoin: 'round',
    lineCap: 'round',
    outlineColor: 'rgba(8, 32, 20, 0.5)',
    borderWeight: 0.8,
  },
  straight: {
    strokeColor: '#ffffff',
    strokeWeight: 1.5,
    strokeOpacity: 0.62,
    strokeStyle: 'solid',
    strokeDasharray: [10, 10],
    lineJoin: 'round',
    lineCap: 'round',
    outlineColor: 'rgba(33, 17, 8, 0.45)',
    borderWeight: 0.8,
  },
}

export const collectMapStops = (plan: TripPlan | null): MapStop[] => {
  if (!plan) return []
  const stops: MapStop[] = []
  let globalIndex = 0
  plan.days.forEach((day, dayIndex) => {
    day.attractions.forEach((attraction, attrIndex) => {
      globalIndex += 1
      const location = attraction.location
      const locatable = Boolean(location && location.longitude && location.latitude)
      stops.push({
        id: `d${dayIndex}-a${attrIndex}`,
        dayIndex,
        attrIndex,
        globalIndex,
        name: attraction.name,
        address: attraction.address,
        visit_duration: attraction.visit_duration,
        description: attraction.description,
        locatable,
        location: locatable ? location : undefined,
      })
    })
  })
  return stops
}

const locatableAttractions = (plan: TripPlan) => {
  const all: Array<Attraction & { dayIndex: number; attrIndex: number; globalIndex: number }> = []
  let globalIndex = 0
  plan.days.forEach((day, dayIndex) => {
    day.attractions.forEach((attraction, attrIndex) => {
      globalIndex += 1
      if (attraction.location && attraction.location.longitude && attraction.location.latitude) {
        all.push({ ...attraction, dayIndex, attrIndex, globalIndex })
      }
    })
  })
  return all
}

const escapeHtml = (value: unknown): string => {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

export const openSettingsDrawer = () => {
  window.dispatchEvent(new CustomEvent(OPEN_SETTINGS_EVENT))
}

export const useTravelMap = (
  tripPlan: Ref<TripPlan | null>,
  options: {
    localeTag: Ref<string>
    selectedStopId: Ref<string | null>
    onSelectStop: (id: string) => void
    containerIds?: { google: string; amap: string }
    quiet?: boolean
  }
) => {
  const googleContainerId = options.containerIds?.google || GOOGLE_CONTAINER_ID
  const amapContainerId = options.containerIds?.amap || AMAP_CONTAINER_ID
  const { t } = useI18n()
  const status = ref<TravelMapStatus>('checking-key')
  const provider = ref<TravelMapProvider | null>(null)
  const settingsReadFailed = ref(false)
  const refreshing = ref(false)

  let map: any = null
  let googleMap: google.maps.Map | null = null
  let googleMarkers: google.maps.Marker[] = []
  let googlePolylines: google.maps.Polyline[] = []
  let googleInfoWindows: google.maps.InfoWindow[] = []
  let googleDirectionsRenderers: google.maps.DirectionsRenderer[] = []
  let mapInitGeneration = 0
  let googleAbandonedGeneration = -1
  const markerById = new Map<string, { google?: google.maps.Marker; amap?: any }>()

  const isActive = (generation: number) => generation === mapInitGeneration
  const googleDropped = (generation: number) => googleAbandonedGeneration === generation

  const destroyCurrentMap = () => {
    googleInfoWindows.forEach((iw) => {
      try {
        iw.close()
      } catch {
        /* ignore */
      }
    })
    googleInfoWindows = []
    googleMarkers.forEach((item) => {
      try {
        item.setMap(null)
      } catch {
        /* ignore */
      }
    })
    googleMarkers = []
    googlePolylines.forEach((item) => {
      try {
        item.setMap(null)
      } catch {
        /* ignore */
      }
    })
    googlePolylines = []
    googleDirectionsRenderers.forEach((item) => {
      try {
        item.setMap(null)
      } catch {
        /* ignore */
      }
    })
    googleDirectionsRenderers = []
    googleMap = null
    if (map) {
      try {
        map.destroy()
      } catch {
        /* ignore */
      }
      map = null
    }
    markerById.clear()
    provider.value = null
  }

  const invalidate = () => {
    mapInitGeneration += 1
    googleAbandonedGeneration = mapInitGeneration
    destroyCurrentMap()
    status.value = 'checking-key'
  }

  const detectRouteMode = (transportation: string): RouteMode => {
    const normalized = (transportation || '').toLowerCase()
    if (/(步行|徒步|散步|walk|walking)/i.test(normalized)) return 'walking'
    if (/(驾车|开车|自驾|打车|出租车|car|drive|driving|taxi)/i.test(normalized)) return 'driving'
    return 'driving'
  }

  const toRoutePoint = (raw: any): RoutePoint | null => {
    if (!raw) return null
    if (Array.isArray(raw) && raw.length >= 2) {
      const lng = Number(raw[0])
      const lat = Number(raw[1])
      return Number.isFinite(lng) && Number.isFinite(lat) ? [lng, lat] : null
    }
    if (typeof raw.getLng === 'function' && typeof raw.getLat === 'function') {
      const lng = Number(raw.getLng())
      const lat = Number(raw.getLat())
      return Number.isFinite(lng) && Number.isFinite(lat) ? [lng, lat] : null
    }
    if ('lng' in raw && 'lat' in raw) {
      const lng = Number(raw.lng)
      const lat = Number(raw.lat)
      return Number.isFinite(lng) && Number.isFinite(lat) ? [lng, lat] : null
    }
    if ('longitude' in raw && 'latitude' in raw) {
      const lng = Number(raw.longitude)
      const lat = Number(raw.latitude)
      return Number.isFinite(lng) && Number.isFinite(lat) ? [lng, lat] : null
    }
    return null
  }

  const parsePolylineString = (polyline: string): RoutePoint[] => {
    if (!polyline) return []
    return polyline
      .split(';')
      .map((pair) => pair.split(','))
      .map((parts) => {
        const lng = Number(parts[0])
        const lat = Number(parts[1])
        return Number.isFinite(lng) && Number.isFinite(lat) ? ([lng, lat] as RoutePoint) : null
      })
      .filter((point): point is RoutePoint => Boolean(point))
  }

  const dedupeRoutePath = (points: RoutePoint[]): RoutePoint[] => {
    if (points.length <= 1) return points
    return points.filter((point, index, array) => {
      if (index === 0) return true
      const prev = array[index - 1]
      return point[0] !== prev[0] || point[1] !== prev[1]
    })
  }

  const extractRoutePath = (result: any): RoutePoint[] => {
    const route = result?.routes?.[0] || result?.route?.paths?.[0] || result?.route?.routes?.[0] || null
    if (!route) return []
    const steps = route.steps || []
    const points: RoutePoint[] = []
    steps.forEach((step: any) => {
      if (Array.isArray(step?.path)) {
        step.path.forEach((node: any) => {
          const point = toRoutePoint(node)
          if (point) points.push(point)
        })
        return
      }
      if (typeof step?.polyline === 'string') {
        points.push(...parsePolylineString(step.polyline))
      }
    })
    if (points.length > 1) return dedupeRoutePath(points)
    if (typeof route?.polyline === 'string') {
      const fromRoute = dedupeRoutePath(parsePolylineString(route.polyline))
      if (fromRoute.length > 1) return fromRoute
    }
    return []
  }

  const searchRoutePath = (
    AMap: any,
    mode: Exclude<RouteMode, 'straight'>,
    start: RoutePoint,
    end: RoutePoint
  ): Promise<RoutePoint[] | null> => {
    return new Promise((resolve) => {
      const ServiceCtor = mode === 'walking' ? AMap.Walking : AMap.Driving
      if (!ServiceCtor) {
        resolve(null)
        return
      }
      const service =
        mode === 'driving'
          ? new ServiceCtor({ policy: AMap.DrivingPolicy?.LEAST_TIME ?? 0 })
          : new ServiceCtor({})
      service.search(start, end, (statusText: string, result: any) => {
        if (statusText !== 'complete') {
          resolve(null)
          return
        }
        const path = extractRoutePath(result)
        resolve(path.length > 1 ? path : null)
      })
    })
  }

  const buildMarkerContent = (dayNo: number, stopNo: number, selected: boolean): string => {
    const scale = selected ? 'scale(1.12)' : 'scale(1)'
    return `
    <div class="travelai-map-marker${selected ? ' is-selected' : ''}" style="transform:${scale}">
      <span class="travelai-map-marker__core" aria-hidden="true">
        <svg fill="#ffffff" width="30px" height="30px" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
          <path d="M231.4248,109.2041,169.36426,86.63574,146.7959,24.57422a19.99984,19.99984,0,0,0-37.5918.001L86.63574,86.63574,24.57422,109.2041a19.99984,19.99984,0,0,0,.001,37.5918l62.06054,22.56836,22.56836,62.06152a19.99984,19.99984,0,0,0,37.5918-.001l22.56836-62.06054,62.06152-22.56836a19.99984,19.99984,0,0,0-.001-37.5918Zm-72.01562,38.24219a19.95591,19.95591,0,0,0-11.96289,11.96289l.001-.001L128,212.88672l-19.44629-53.47754A19.95279,19.95279,0,0,0,96.5918,147.44727L43.11328,128l53.47754-19.44629A19.95279,19.95279,0,0,0,108.55273,96.5918L128,43.11328l19.44629,53.47754a19.95279,19.95279,0,0,0,11.96191,11.96191L212.88672,128Z"/>
        </svg>
      </span>
      <span class="travelai-map-marker__index" aria-hidden="true">${dayNo}-${stopNo}</span>
    </div>`
  }

  const buildInfoWindowContent = (attraction: Attraction & { dayIndex: number; attrIndex: number }): string => {
    const name = escapeHtml(attraction.name || t('common.noData'))
    const address = escapeHtml(attraction.address || t('common.noData'))
    const visitDuration = Number.isFinite(attraction.visit_duration) ? attraction.visit_duration : '—'
    const dayAttractionText = escapeHtml(
      t('result.mapInfo.dayAttraction', { day: attraction.dayIndex + 1, index: attraction.attrIndex + 1 })
    )
    const minuteUnit = escapeHtml(t('result.minuteUnit'))
    return `
    <div class="travelai-map-tooltip travelai-map-tooltip--plain">
      <p class="travelai-map-tooltip__line travelai-map-tooltip__line--title">${name}</p>
      <p class="travelai-map-tooltip__line">${dayAttractionText}</p>
      <p class="travelai-map-tooltip__line">${address}</p>
      <p class="travelai-map-tooltip__line">${visitDuration}${minuteUnit}</p>
    </div>`
  }

  const googleIcon = (attraction: { dayIndex: number; attrIndex: number }, selected: boolean) => {
    const markerText = `${attraction.dayIndex + 1}-${attraction.attrIndex + 1}`
    const size = selected ? 38 : 34
    const svgIcon =
      `data:image/svg+xml;charset=UTF-8,` +
      encodeURIComponent(`
      <svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size + 8}" viewBox="0 0 34 42">
        <path d="M17 0C7.6 0 0 7.6 0 17C0 29.8 17 42 17 42C17 42 34 29.8 34 17C34 7.6 26.4 0 17 0Z" fill="#147d72" stroke="#fff" stroke-width="${selected ? 3 : 2}"/>
        <text x="17" y="22" font-family="sans-serif" font-size="12" font-weight="bold" fill="white" text-anchor="middle">${markerText}</text>
      </svg>`)
    return {
      url: svgIcon,
      scaledSize: new google.maps.Size(size, size + 8),
      anchor: new google.maps.Point(size / 2, size + 8),
    }
  }

  const drawGoogleRoutes = async (attractions: ReturnType<typeof locatableAttractions>, generation: number) => {
    if (attractions.length < 2 || !tripPlan.value || !googleMap) return
    if (!isActive(generation) || googleDropped(generation)) return
    const dayGroups: Record<number, typeof attractions> = {}
    attractions.forEach((attr) => {
      if (!dayGroups[attr.dayIndex]) dayGroups[attr.dayIndex] = []
      dayGroups[attr.dayIndex].push(attr)
    })
    const directionsService = new google.maps.DirectionsService()
    for (const dayAttractions of Object.values(dayGroups)) {
      if (!isActive(generation) || googleDropped(generation)) return
      if (dayAttractions.length < 2) continue
      dayAttractions.sort((a, b) => a.attrIndex - b.attrIndex)
      const dayIndex = dayAttractions[0].dayIndex
      const transportation = tripPlan.value.days?.[dayIndex]?.transportation || ''
      const preferredMode = detectRouteMode(transportation)
      let gTravelMode = google.maps.TravelMode.DRIVING
      if (preferredMode === 'walking') gTravelMode = google.maps.TravelMode.WALKING
      for (let i = 0; i < dayAttractions.length - 1; i++) {
        if (!isActive(generation) || googleDropped(generation) || !googleMap) return
        const start = dayAttractions[i]
        const end = dayAttractions[i + 1]
        const origin = { lat: start.location.latitude, lng: start.location.longitude }
        const destination = { lat: end.location.latitude, lng: end.location.longitude }
        if (preferredMode === 'straight') {
          googlePolylines.push(
            new google.maps.Polyline({
              path: [origin, destination],
              strokeColor: '#ffffff',
              strokeWeight: 1.5,
              strokeOpacity: 0.62,
              map: googleMap,
              zIndex: 90,
            })
          )
          continue
        }
        try {
          const response = await directionsService.route({
            origin,
            destination,
            travelMode: gTravelMode,
          })
          if (!isActive(generation) || googleDropped(generation) || !googleMap) return
          googleDirectionsRenderers.push(
            new google.maps.DirectionsRenderer({
              map: googleMap,
              directions: response,
              suppressMarkers: true,
              polylineOptions: {
                strokeColor: preferredMode === 'walking' ? '#6ad38f' : '#37b4ff',
                strokeWeight: preferredMode === 'walking' ? 3 : 3.5,
                zIndex: 90,
              },
            })
          )
        } catch {
          if (!isActive(generation) || googleDropped(generation) || !googleMap) return
          googlePolylines.push(
            new google.maps.Polyline({
              path: [origin, destination],
              strokeColor: '#ffffff',
              strokeWeight: 1.5,
              strokeOpacity: 0.62,
              map: googleMap,
              zIndex: 90,
            })
          )
        }
      }
    }
  }

  const addGoogleAttractionMarkers = async (generation: number) => {
    if (!tripPlan.value || !googleMap) return
    const allAttractions = locatableAttractions(tripPlan.value)
    const bounds = new google.maps.LatLngBounds()
    allAttractions.forEach((attraction, index) => {
      const position = { lat: attraction.location.latitude, lng: attraction.location.longitude }
      bounds.extend(position)
      const stopId = `d${attraction.dayIndex}-a${attraction.attrIndex}`
      const marker = new google.maps.Marker({
        position,
        map: googleMap,
        icon: googleIcon(attraction, options.selectedStopId.value === stopId),
        zIndex: 120 + index,
      })
      const infoWindow = new google.maps.InfoWindow({
        content: buildInfoWindowContent(attraction),
        disableAutoPan: true,
      })
      marker.addListener('mouseover', () => {
        infoWindow.open({ anchor: marker, map: googleMap })
      })
      marker.addListener('mouseout', () => {
        infoWindow.close()
      })
      marker.addListener('click', () => {
        options.onSelectStop(stopId)
        infoWindow.open({ anchor: marker, map: googleMap })
      })
      googleMarkers.push(marker)
      googleInfoWindows.push(infoWindow)
      markerById.set(stopId, { google: marker })
    })
    if (!isActive(generation) || googleDropped(generation)) return
    await drawGoogleRoutes(allAttractions, generation)
    if (!isActive(generation) || googleDropped(generation)) return
    if (allAttractions.length > 0 && googleMap) {
      googleMap.fitBounds(bounds)
      const currentZoom = googleMap.getZoom()
      if (currentZoom && currentZoom > 15) googleMap.setZoom(15)
    }
  }

  const drawAMapRoutes = async (AMap: any, attractions: ReturnType<typeof locatableAttractions>, generation: number) => {
    if (attractions.length < 2 || !tripPlan.value) return []
    const dayGroups: Record<number, typeof attractions> = {}
    attractions.forEach((attr) => {
      if (!dayGroups[attr.dayIndex]) dayGroups[attr.dayIndex] = []
      dayGroups[attr.dayIndex].push(attr)
    })
    const polylines: any[] = []
    for (const dayAttractions of Object.values(dayGroups)) {
      if (!isActive(generation)) return []
      if (dayAttractions.length < 2) continue
      dayAttractions.sort((a, b) => a.attrIndex - b.attrIndex)
      const dayIndex = dayAttractions[0].dayIndex
      const transportation = tripPlan.value.days?.[dayIndex]?.transportation || ''
      const preferredMode = detectRouteMode(transportation)
      for (let i = 0; i < dayAttractions.length - 1; i++) {
        if (!isActive(generation)) return []
        const start = dayAttractions[i]
        const end = dayAttractions[i + 1]
        const startPoint: RoutePoint = [start.location.longitude, start.location.latitude]
        const endPoint: RoutePoint = [end.location.longitude, end.location.latitude]
        const plannedPath =
          preferredMode === 'straight'
            ? null
            : await searchRoutePath(AMap, preferredMode as Exclude<RouteMode, 'straight'>, startPoint, endPoint)
        if (!isActive(generation)) return []
        const usePlannedRoute = Array.isArray(plannedPath) && plannedPath.length > 1
        const routeModeForStyle: RouteMode = usePlannedRoute ? preferredMode : 'straight'
        const path = usePlannedRoute ? plannedPath : [startPoint, endPoint]
        const style = ROUTE_STYLE_PRESETS[routeModeForStyle]
        polylines.push(
          new AMap.Polyline({
            path,
            ...style,
            showDir: true,
            zIndex: 90,
          })
        )
      }
    }
    if (polylines.length > 0 && map) map.add(polylines)
    return polylines
  }

  const addAMapMarkers = async (AMap: any, generation: number) => {
    if (!tripPlan.value || !map) return
    const markers: any[] = []
    const allAttractions = locatableAttractions(tripPlan.value)
    allAttractions.forEach((attraction, index) => {
      const stopId = `d${attraction.dayIndex}-a${attraction.attrIndex}`
      const marker = new AMap.Marker({
        position: [attraction.location.longitude, attraction.location.latitude],
        content: buildMarkerContent(
          attraction.dayIndex + 1,
          attraction.attrIndex + 1,
          options.selectedStopId.value === stopId
        ),
        anchor: 'center',
        offset: new AMap.Pixel(0, 0),
        zIndex: 120 + index,
      })
      const infoWindow = new AMap.InfoWindow({
        isCustom: true,
        content: buildInfoWindowContent(attraction),
        offset: new AMap.Pixel(0, -18),
        closeWhenClickMap: true,
      })
      marker.on('mouseover', () => {
        infoWindow.open(map, marker.getPosition())
      })
      marker.on('mouseout', () => {
        infoWindow.close()
      })
      marker.on('click', () => {
        options.onSelectStop(stopId)
        infoWindow.open(map, marker.getPosition())
      })
      markers.push(marker)
      markerById.set(stopId, { amap: marker })
    })
    map.add(markers)
    if (!isActive(generation)) return
    const routePolylines = await drawAMapRoutes(AMap, allAttractions, generation)
    if (!isActive(generation)) return
    if (allAttractions.length > 0) {
      const overlaysForFit = routePolylines.length > 0 ? [...markers, ...routePolylines] : markers
      map.setFitView(overlaysForFit)
    }
  }

  const initGoogleMap = async (apiKey: string, generation: number) => {
    if (!isActive(generation) || googleDropped(generation)) return
    provider.value = 'google'
    await nextTick()
    if (!isActive(generation) || googleDropped(generation)) return
    const { Loader } = await import('@googlemaps/js-api-loader')
    if (!isActive(generation) || googleDropped(generation)) return
    const loader = new Loader({
      apiKey,
      version: 'weekly',
      language: options.localeTag.value,
    })
    const googleApi = await loader.importLibrary('maps')
    if (!isActive(generation) || googleDropped(generation)) return
    const { Map } = googleApi as google.maps.MapsLibrary
    await loader.importLibrary('routes')
    await loader.importLibrary('marker')
    if (!isActive(generation) || googleDropped(generation)) return
    const container = document.getElementById(googleContainerId)
    if (!container) throw new Error('map-container-missing')
    googleMap = new Map(container, {
      center: { lat: 39.916527, lng: 116.397128 },
      zoom: 12,
      mapTypeId: 'roadmap',
      disableDefaultUI: true,
      zoomControl: true,
      styles: [
        { elementType: 'geometry', stylers: [{ color: '#242f3e' }] },
        { elementType: 'labels.text.stroke', stylers: [{ color: '#242f3e' }] },
        { elementType: 'labels.text.fill', stylers: [{ color: '#746855' }] },
        { featureType: 'administrative.locality', elementType: 'labels.text.fill', stylers: [{ color: '#d59563' }] },
        { featureType: 'poi', elementType: 'labels.text.fill', stylers: [{ color: '#d59563' }] },
        { featureType: 'poi.park', elementType: 'geometry', stylers: [{ color: '#263c3f' }] },
        { featureType: 'poi.park', elementType: 'labels.text.fill', stylers: [{ color: '#6b9a76' }] },
        { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#38414e' }] },
        { featureType: 'road', elementType: 'geometry.stroke', stylers: [{ color: '#212a37' }] },
        { featureType: 'road', elementType: 'labels.text.fill', stylers: [{ color: '#9ca5b3' }] },
        { featureType: 'road.highway', elementType: 'geometry', stylers: [{ color: '#746855' }] },
        { featureType: 'road.highway', elementType: 'geometry.stroke', stylers: [{ color: '#1f2835' }] },
        { featureType: 'road.highway', elementType: 'labels.text.fill', stylers: [{ color: '#f3d19c' }] },
        { featureType: 'transit', elementType: 'geometry', stylers: [{ color: '#2f3948' }] },
        { featureType: 'transit.station', elementType: 'labels.text.fill', stylers: [{ color: '#d59563' }] },
        { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#17263c' }] },
        { featureType: 'water', elementType: 'labels.text.fill', stylers: [{ color: '#515c6d' }] },
        { featureType: 'water', elementType: 'labels.text.stroke', stylers: [{ color: '#17263c' }] },
      ],
    })
    await addGoogleAttractionMarkers(generation)
    if (!isActive(generation) || googleDropped(generation)) return
    status.value = 'ready'
    if (!options.quiet) message.success(t('result.messages.mapLoaded'))
  }

  const initAMap = async (generation: number) => {
    if (!isActive(generation)) return
    const mapJsKey = getRuntimeMapJsKey()
    if (!mapJsKey) {
      status.value = settingsReadFailed.value ? 'failed' : 'missing-key'
      if (provider.value === 'google') status.value = 'failed'
      return
    }
    status.value = 'loading-amap'
    provider.value = 'amap'
    await nextTick()
    if (!isActive(generation)) return
    const AMapLoader = (await import('@amap/amap-jsapi-loader')).default
    if (!isActive(generation)) return
    const AMap = await AMapLoader.load({
      key: mapJsKey,
      version: '2.0',
      plugins: ['AMap.Marker', 'AMap.Polyline', 'AMap.InfoWindow', 'AMap.Driving', 'AMap.Walking'],
    })
    if (!isActive(generation)) return
    map = new AMap.Map(amapContainerId, {
      zoom: 12,
      center: [116.397128, 39.916527],
      viewMode: '3D',
      mapStyle: 'amap://styles/darkblue',
      WebGLParams: { preserveDrawingBuffer: true },
    })
    await addAMapMarkers(AMap, generation)
    if (!isActive(generation)) return
    status.value = 'ready'
    if (!options.quiet) message.success(t('result.messages.mapLoaded'))
  }

  const initMap = async () => {
    const generation = ++mapInitGeneration
    googleAbandonedGeneration = -1
    settingsReadFailed.value = false
    destroyCurrentMap()
    status.value = 'checking-key'
    await nextTick()
    if (!isActive(generation)) return

    let googleKey = getRuntimeGoogleMapsApiKey()
    if (!googleKey) {
      try {
        const backendSettings = await getBackendRuntimeSettings()
        if (!isActive(generation)) return
        if (backendSettings.google_maps_api_key) {
          googleKey = backendSettings.google_maps_api_key
          setRuntimeGoogleMapsApiKey(googleKey)
        }
      } catch {
        if (!isActive(generation)) return
        settingsReadFailed.value = true
      }
    }

    if (!isActive(generation)) return

    if (googleKey) {
      status.value = 'loading-google'
      let timeoutHandle: ReturnType<typeof setTimeout> | undefined
      try {
        const timeoutPromise = new Promise<never>((_, reject) => {
          timeoutHandle = setTimeout(() => reject(new Error('google-timeout')), GOOGLE_TIMEOUT_MS)
        })
        await Promise.race([initGoogleMap(googleKey, generation), timeoutPromise])
        return
      } catch {
        if (!isActive(generation)) return
        googleAbandonedGeneration = generation
        status.value = 'fallback-amap'
        destroyCurrentMap()
        await nextTick()
      } finally {
        clearTimeout(timeoutHandle)
      }
    }

    if (!isActive(generation)) return
    const amapKey = getRuntimeMapJsKey()
    if (!googleKey && !amapKey) {
      status.value = settingsReadFailed.value ? 'failed' : 'missing-key'
      return
    }
    if (!amapKey) {
      status.value = 'failed'
      return
    }
    try {
      await initAMap(generation)
    } catch {
      if (!isActive(generation)) return
      status.value = 'failed'
      if (!options.quiet) message.error(t('result.messages.mapLoadFailed'))
    }
  }

  const resize = () => {
    if (status.value !== 'ready') return
    if (provider.value === 'google' && googleMap) {
      google.maps.event.trigger(googleMap, 'resize')
      return
    }
    if (provider.value === 'amap' && map && typeof map.resize === 'function') {
      map.resize()
    }
  }

  const refresh = async () => {
    if (refreshing.value) return
    refreshing.value = true
    try {
      destroyCurrentMap()
      await nextTick()
      await initMap()
    } catch {
      status.value = 'failed'
      if (!options.quiet) message.error(t('result.messages.mapLoadFailed'))
    } finally {
      refreshing.value = false
    }
  }

  const focusStop = (id: string) => {
    const reduce = document.documentElement.getAttribute('data-motion') === 'reduce'
    const entry = markerById.get(id)
    if (entry?.google && googleMap) {
      const pos = entry.google.getPosition()
      if (pos) googleMap.panTo(pos)
      if (!reduce) googleMap.setZoom(Math.max(googleMap.getZoom() || 12, 14))
      return
    }
    if (entry?.amap && map) {
      const pos = entry.amap.getPosition()
      if (pos) map.setCenter(pos)
    }
  }

  const syncSelectedMarker = (id: string | null) => {
    markerById.forEach((entry, stopId) => {
      const selected = stopId === id
      const parts = stopId.match(/^d(\d+)-a(\d+)$/)
      if (entry.google) {
        const dayIndex = Number(parts?.[1] || 0)
        const attrIndex = Number(parts?.[2] || 0)
        entry.google.setIcon(googleIcon({ dayIndex, attrIndex }, selected))
        entry.google.setZIndex(selected ? 200 : 120)
      }
      if (entry.amap && parts) {
        entry.amap.setContent(buildMarkerContent(Number(parts[1]) + 1, Number(parts[2]) + 1, selected))
      }
    })
  }

  const getMapElement = (): HTMLElement | null => {
    if (status.value !== 'ready') return null
    const id = provider.value === 'google' ? googleContainerId : amapContainerId
    const el = document.getElementById(id)
    if (!el || el.clientHeight === 0) return null
    return el
  }

  return {
    status,
    provider,
    settingsReadFailed,
    refreshing,
    initMap,
    refresh,
    invalidate,
    destroyCurrentMap,
    resize,
    focusStop,
    syncSelectedMarker,
    getMapElement,
  }
}
