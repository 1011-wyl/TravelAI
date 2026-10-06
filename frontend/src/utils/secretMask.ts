const SECRET_MASK_CHAR = '\u2022'

export const isMaskedSecret = (value: string): boolean => value.includes(SECRET_MASK_CHAR)

/** 与后端设置页一致：仅保留少量首尾字符，点开眼睛也不还原完整密钥。 */
export const maskSecret = (value: string | null | undefined): string => {
  const text = String(value ?? '').trim()
  if (!text) return ''
  if (isMaskedSecret(text)) return text
  if (text.length <= 8) return SECRET_MASK_CHAR.repeat(8)
  return `${text.slice(0, 4)}${SECRET_MASK_CHAR.repeat(8)}${text.slice(-4)}`
}
