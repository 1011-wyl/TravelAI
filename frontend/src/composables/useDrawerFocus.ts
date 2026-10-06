import { nextTick, onMounted, onUnmounted, watch, type Ref } from 'vue'

const focusable = 'a[href],button:not(:disabled),input:not(:disabled),textarea:not(:disabled),select:not(:disabled),[tabindex]:not([tabindex="-1"])'

/** Ant 4.x Drawer handles Esc, but unlike Modal it has no Tab sentinels. */
export const useDrawerFocus = (open: Ref<boolean>, rootSelector: string, fallbackSelector?: string) => {
  let trigger: HTMLElement | null = null
  const root = () => document.querySelector<HTMLElement>(`${rootSelector}.ant-drawer-open .ant-drawer-content`)
  const visible = (el: HTMLElement) => el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden' && !el.closest('[inert]')
  const items = (el: HTMLElement) => Array.from(el.querySelectorAll<HTMLElement>(focusable)).filter(visible)
  // A nested Ant Modal owns focus while open; do not compete with its sentinels.
  const modalOpen = () => Array.from(document.querySelectorAll<HTMLElement>('.ant-modal-wrap')).some(visible)
  const onKeydown = (event: KeyboardEvent) => {
    const el = root()
    if (!open.value || !el || modalOpen() || event.key !== 'Tab') return
    const controls = items(el)
    const index = controls.indexOf(document.activeElement as HTMLElement)
    if (!controls.length) { event.preventDefault(); el.focus(); return }
    if (index < 0 || (!event.shiftKey && index === controls.length - 1) || (event.shiftKey && index === 0)) {
      event.preventDefault()
      controls[event.shiftKey ? controls.length - 1 : 0].focus()
    }
  }
  const onFocus = (event: FocusEvent) => {
    const el = root()
    if (!open.value || !el || modalOpen() || el.contains(event.target as Node)) return
    ;(items(el)[0] || el).focus()
  }
  watch(open, (value) => {
    if (value) trigger = document.activeElement instanceof HTMLElement ? document.activeElement : null
  }, { flush: 'sync' })
  const afterOpenChange = async (value: boolean) => {
    await nextTick()
    if (value) {
      const el = root()
      if (el) {
        el.setAttribute('role', 'dialog')
        el.setAttribute('aria-modal', 'true')
        const heading = el.querySelector<HTMLElement>('h2[id], .mobile-nav-drawer__title[id]')
        if (heading) el.setAttribute('aria-labelledby', heading.id)
        el.tabIndex = -1
        if (!el.contains(document.activeElement)) (items(el)[0] || el).focus()
      }
    } else if (!document.querySelector('.ant-drawer-open') && !modalOpen()) {
      const fallback = fallbackSelector ? document.querySelector<HTMLElement>(fallbackSelector) : null
      const target = trigger?.isConnected && visible(trigger) ? trigger : fallback
      if (target && visible(target)) target.focus()
    }
  }
  onMounted(() => {
    document.addEventListener('keydown', onKeydown, true)
    document.addEventListener('focusin', onFocus, true)
  })
  onUnmounted(() => {
    document.removeEventListener('keydown', onKeydown, true)
    document.removeEventListener('focusin', onFocus, true)
  })
  return { afterOpenChange }
}
