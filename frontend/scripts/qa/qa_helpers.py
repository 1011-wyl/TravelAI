"""Shared Playwright helpers for isolated frontend QA (no production mock switches)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from playwright.async_api import Page

CONTRAST_JS = r"""
() => {
  const parse = (raw) => {
    if (!raw) return null;
    const m = String(raw).match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([0-9.]+))?\)/);
    if (!m) return null;
    const a = m[4] === undefined ? 1 : Number(m[4]);
    return { r: Number(m[1]), g: Number(m[2]), b: Number(m[3]), a };
  };
  const blend = (fg, bg) => {
    const a = fg.a;
    return {
      r: fg.r * a + bg.r * (1 - a),
      g: fg.g * a + bg.g * (1 - a),
      b: fg.b * a + bg.b * (1 - a),
    };
  };
  const lin = (c) => {
    const s = c / 255;
    return s <= 0.04045 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  };
  const lum = (rgb) => 0.2126 * lin(rgb.r) + 0.7152 * lin(rgb.g) + 0.0722 * lin(rgb.b);
  const ratio = (a, b) => {
    const L1 = lum(a);
    const L2 = lum(b);
    const hi = Math.max(L1, L2);
    const lo = Math.min(L1, L2);
    return (hi + 0.05) / (lo + 0.05);
  };
  const pickBg = (el) => {
    let node = el;
    while (node && node !== document.documentElement) {
      const cs = getComputedStyle(node);
      const bg = parse(cs.backgroundColor);
      if (bg && bg.a > 0.01) return bg;
      node = node.parentElement;
    }
    return parse(getComputedStyle(document.body).backgroundColor) || { r: 255, g: 255, b: 255, a: 1 };
  };
  const sample = (el) => {
    if (!el) return null;
    const cs = getComputedStyle(el);
    const fg = parse(cs.color);
    const bg = pickBg(el);
    if (!fg || !bg) return null;
    const solid = blend(fg, bg);
    const bgSolid = { r: bg.r, g: bg.g, b: bg.b };
    const fontSize = parseFloat(cs.fontSize) || 16;
    const bold = Number(cs.fontWeight) >= 700;
    const large = fontSize >= 24 || (fontSize >= 18.66 && bold);
    const r = ratio(solid, bgSolid);
    return {
      text: (el.innerText || '').slice(0, 80),
      ratio: Number(r.toFixed(2)),
      large,
      pass: large ? r >= 3 : r >= 4.5,
      color: cs.color,
      background: `rgb(${Math.round(bgSolid.r)}, ${Math.round(bgSolid.g)}, ${Math.round(bgSolid.b)})`,
      fontSize,
    };
  };
  const selectors = [
    'h1',
    'h2',
    '.result-page__heading',
    '.trip-hero-summary__title',
    '.result-section-nav__item.is-current',
    'p',
    '.app-header__link',
    'button',
  ];
  const items = [];
  for (const sel of selectors) {
    const el = document.querySelector(sel);
    const row = sample(el);
    if (row) items.push({ selector: sel, ...row });
  }
  const muted = document.querySelector('.trip-hero-summary__kicker, .result-section-nav__item:not(.is-current), .color-muted');
  if (muted) {
    const row = sample(muted);
    if (row) items.push({ selector: 'muted-sample', ...row });
  }
  return {
    theme: document.documentElement.dataset.theme || '',
    motion: document.documentElement.dataset.motion || '',
    items,
    fails: items.filter((i) => !i.pass),
  };
}
"""

LAYOUT_JS = r"""
() => {
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const pageOverflowX = document.documentElement.scrollWidth - vw;
  const clipped = [];
  const overflowing = [];
  const nodes = Array.from(document.querySelectorAll('h1, h2, h3, button, th, td, p, a, .result-section-nav, .trip-action-bar, table, input, textarea'));
  const inScrollX = (el) => {
    let node = el.parentElement;
    while (node && node !== document.body) {
      const cs = getComputedStyle(node);
      if ((cs.overflowX === 'auto' || cs.overflowX === 'scroll') && node.scrollWidth > node.clientWidth + 1) {
        return true;
      }
      node = node.parentElement;
    }
    return false;
  };
  for (const el of nodes.slice(0, 220)) {
    const cs = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    if (el.scrollWidth > el.clientWidth + 2 && (cs.overflowX === 'hidden' || cs.textOverflow === 'ellipsis')) {
      const text = (el.innerText || '').trim();
      if (text.length > 12) {
        clipped.push({ tag: el.tagName, className: el.className?.toString?.().slice(0, 80), text: text.slice(0, 60) });
      }
    }
    if (rect.right > vw + 8 && rect.width > 20 && cs.visibility !== 'hidden' && cs.display !== 'none') {
      if (!inScrollX(el)) {
        overflowing.push({ tag: el.tagName, className: el.className?.toString?.().slice(0, 80), right: Math.round(rect.right) });
      }
    }
  }
  const header = document.querySelector('.app-header, header');
  const sectionNav = document.querySelector('.result-section-nav');
  const heading = document.getElementById('result-section-heading');
  const stickyOverlap = [];
  if (header && sectionNav) {
    const a = header.getBoundingClientRect();
    const b = sectionNav.getBoundingClientRect();
    if (a.bottom > b.top + 4 && b.bottom > a.top) {
      stickyOverlap.push('header-vs-section-nav');
    }
  }
  if (heading && sectionNav) {
    const h = heading.getBoundingClientRect();
    const n = sectionNav.getBoundingClientRect();
    if (n.bottom > h.top + 2 && h.bottom > n.top && h.top < 120) {
      stickyOverlap.push('section-nav-covers-heading');
    }
  }
  const hiddenFocused = (() => {
    const el = document.activeElement;
    if (!el || el === document.body) return null;
    const cs = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    if (cs.visibility === 'hidden' || cs.display === 'none' || (rect.width === 0 && rect.height === 0)) {
      return { tag: el.tagName, className: el.className?.toString?.().slice(0, 80) };
    }
    if (el.closest('[aria-hidden="true"]')) {
      return { tag: el.tagName, reason: 'aria-hidden ancestor' };
    }
    return null;
  })();
  return {
    vw,
    vh,
    pageOverflowX,
    clipped: clipped.slice(0, 12),
    overflowing: overflowing.slice(0, 12),
    stickyOverlap,
    hiddenFocused,
    animations: document.getAnimations({ subtree: true }).filter((a) => a.playState === 'running').length,
  };
}
"""


async def screenshot(page: Page, path: Path, full_page: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(path), full_page=full_page)


async def set_viewport(page: Page, width: int, height: int = 900) -> None:
    await page.set_viewport_size({"width": width, "height": height})


async def wait_text(page: Page, text: str, timeout: float = 15000) -> None:
    await page.wait_for_function(
        "(t) => document.body && document.body.innerText.includes(t)",
        arg=text,
        timeout=timeout,
    )


async def body_has(page: Page, text: str) -> bool:
    return bool(await page.evaluate("(t) => document.body.innerText.includes(t)", text))


async def seed_plan(page: Page, plan: dict[str, Any], graph: dict[str, Any] | None, plan_id: str) -> None:
    await page.evaluate(
        """({ plan, graph, planId }) => {
          sessionStorage.setItem('tripPlan', JSON.stringify(plan));
          if (graph) sessionStorage.setItem('graphData', JSON.stringify(graph));
          else sessionStorage.removeItem('graphData');
          sessionStorage.setItem('planId', planId);
        }""",
        {"plan": plan, "graph": graph, "planId": plan_id},
    )


async def contrast_audit(page: Page) -> dict[str, Any]:
    return await page.evaluate(CONTRAST_JS)


async def layout_audit(page: Page) -> dict[str, Any]:
    return await page.evaluate(LAYOUT_JS)


async def glow_animation_state(page: Page) -> dict[str, Any]:
    return await page.evaluate(
        """() => {
          const glow = document.querySelector('.app-atmosphere__glow');
          if (!glow) return { present: false };
          const anims = glow.getAnimations();
          return {
            present: true,
            running: anims.filter((a) => a.playState === 'running').length,
            names: anims.map((a) => a.animationName || ''),
            motion: document.documentElement.dataset.motion || '',
          };
        }"""
    )


async def heading_focus_ok(page: Page) -> dict[str, Any]:
    return await page.evaluate(
        """() => {
          const el = document.getElementById('result-section-heading');
          if (!el) return { present: false };
          const rect = el.getBoundingClientRect();
          const header = document.querySelector('.app-header, header');
          const nav = document.querySelector('.result-section-nav');
          let covered = false;
          if (header) {
            const h = header.getBoundingClientRect();
            if (h.bottom > rect.top + 4 && document.activeElement === el) covered = true;
          }
          if (nav) {
            const n = nav.getBoundingClientRect();
            if (n.bottom > rect.top + 4 && n.top < rect.bottom && document.activeElement === el) covered = true;
          }
          return {
            present: true,
            focused: document.activeElement === el,
            top: Math.round(rect.top),
            covered,
          };
        }"""
    )


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
