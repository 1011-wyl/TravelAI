import { theme } from 'ant-design-vue'
import type { ThemeConfig } from 'ant-design-vue/es/config-provider/context'
import type { ResolvedMotion, ResolvedTheme } from './preferences'

const lightPalette = {
  colorPrimary: '#147D72',
  colorInfo: '#2F6FA3',
  colorSuccess: '#1E7A55',
  colorWarning: '#9A5B0A',
  colorError: '#B23A3A',
  colorText: '#16302B',
  colorTextSecondary: '#5D726D',
  colorBgBase: '#F5F7F2',
  colorBgContainer: '#FFFFFF',
  colorBorder: '#CAD8D3',
}

const darkPalette = {
  colorPrimary: '#64C7B8',
  colorInfo: '#86BCE8',
  colorSuccess: '#63C696',
  colorWarning: '#F0B869',
  colorError: '#FF8D8D',
  colorText: '#F2F7F4',
  colorTextSecondary: '#A6BBB5',
  colorBgBase: '#071916',
  colorBgContainer: '#102D29',
  colorBorder: '#285048',
}

export const createAntdTheme = (mode: ResolvedTheme, motion: ResolvedMotion): ThemeConfig => {
  const palette = mode === 'dark' ? darkPalette : lightPalette
  const duration = motion === 'reduce' ? '0.001s' : '0.24s'

  return {
    algorithm: mode === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      ...palette,
      colorTextLightSolid: mode === 'dark' ? '#071916' : '#ffffff',
      borderRadius: 16,
      controlHeight: 44,
      controlHeightLG: 52,
      fontSize: 16,
      motionDurationMid: duration,
      motionDurationFast: motion === 'reduce' ? '0.001s' : '0.18s',
      motionDurationSlow: motion === 'reduce' ? '0.001s' : '0.36s',
    },
  }
}
