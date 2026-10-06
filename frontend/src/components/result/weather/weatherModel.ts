import type { WeatherInfo } from '@/types'

export type WeatherIconKind =
  | 'sun-shower'
  | 'thunder-storm'
  | 'cloudy'
  | 'flurries'
  | 'sunny'
  | 'rainy'
  | 'unknown'

export const weatherDayKey = (item: WeatherInfo, index: number): string => {
  const date = item.date?.trim()
  return date || `__idx-${index}`
}

export const localeTagFromI18n = (locale: string): string => {
  const currentLocale = String(locale || 'en').toLowerCase()
  if (currentLocale.startsWith('zh')) return 'zh-CN'
  if (currentLocale.startsWith('ja')) return 'ja-JP'
  return 'en-US'
}

export const parseWeatherDate = (rawDate: string): Date | null => {
  if (!rawDate) return null

  const normalized = rawDate
    .replace(/年/g, '-')
    .replace(/月/g, '-')
    .replace(/日/g, '')
    .replace(/[./]/g, '-')
    .trim()

  const parsedDate = new Date(normalized)
  if (!Number.isNaN(parsedDate.getTime())) return parsedDate

  const matched = rawDate.match(/(\d{4})\D+(\d{1,2})\D+(\d{1,2})/)
  if (!matched) return null
  const [, year, month, day] = matched
  const fallbackDate = new Date(Number(year), Number(month) - 1, Number(day))
  return Number.isNaN(fallbackDate.getTime()) ? null : fallbackDate
}

export const formatWeatherDate = (rawDate: string, locale: string): string => {
  const date = parseWeatherDate(rawDate)
  if (!date) return rawDate || '--'
  return new Intl.DateTimeFormat(localeTagFromI18n(locale), {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date)
}

export const formatWeatherWeekday = (rawDate: string, locale: string, short = false): string => {
  const date = parseWeatherDate(rawDate)
  if (!date) return rawDate || '--'
  return new Intl.DateTimeFormat(localeTagFromI18n(locale), {
    weekday: short ? 'short' : 'long',
  }).format(date)
}

export const formatWeatherTemp = (temperature: number | null | undefined): string => {
  if (!Number.isFinite(Number(temperature))) return '--'
  return `${Math.round(Number(temperature))}°C`
}

export const getWeatherIconKind = (weatherText: string): WeatherIconKind => {
  const text = (weatherText || '').trim()
  if (!text) return 'unknown'

  const hasRain = /(雨|rain|shower|drizzle|sprinkle|阵雨|小雨|中雨|大雨|暴雨)/i.test(text)
  const hasSun = /(晴|sun|clear)/i.test(text)

  if (/(雷|thunder|storm|lightning|雷暴|雷阵雨)/i.test(text)) return 'thunder-storm'
  if (/(雪|snow|sleet|hail|冰雹|冻雨|雨夹雪)/i.test(text)) return 'flurries'
  if (hasRain && hasSun) return 'sun-shower'
  if (hasRain) return 'rainy'
  if (/(云|阴|cloud|overcast|雾|霾|fog|mist|haze|wind|breeze|gale)/i.test(text)) return 'cloudy'
  if (hasSun) return 'sunny'
  return 'unknown'
}

export const getWeatherPrecipitation = (weatherText: string): string => {
  const text = (weatherText || '').toLowerCase()
  if (/(雷|thunder|暴雨|storm)/.test(text)) return '85%'
  if (/(雨|rain|shower|drizzle)/.test(text)) return '65%'
  if (/(雪|snow|sleet|hail)/.test(text)) return '55%'
  if (/(阴|cloud|overcast)/.test(text)) return '30%'
  return '10%'
}

export const getWeatherHumidity = (weatherText: string): string => {
  const text = (weatherText || '').toLowerCase()
  if (/(雷|thunder|暴雨|storm)/.test(text)) return '88%'
  if (/(雨|rain|shower|drizzle)/.test(text)) return '78%'
  if (/(雪|snow|sleet|hail)/.test(text)) return '72%'
  if (/(阴|cloud|overcast|雾|霾|fog|mist|haze)/.test(text)) return '62%'
  return '42%'
}

export const getWeatherWind = (weather: WeatherInfo | null): string => {
  if (!weather) return '--'
  const direction = weather.wind_direction?.trim() || '--'
  const power = weather.wind_power?.trim() || '--'
  return `${direction} ${power}`.trim()
}

export const combinedWeatherText = (item: WeatherInfo): string => {
  return `${item.day_weather || ''} ${item.night_weather || ''}`
}
