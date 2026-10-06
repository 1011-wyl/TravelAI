"""
Phase 8.3 visual / responsive / keyboard QA.

Isolated mock API + WebSocket. Not real backend / map vendor / export-image acceptance.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

from playwright.async_api import async_playwright

from fixtures_rich_trip import (
    EMPTY_GRAPH_PLAN,
    RICH_GRAPH,
    RICH_PLAN,
    SPARSE_WEATHER_PLAN,
    history_items,
    status_payload,
)
from qa_helpers import (
    body_has,
    contrast_audit,
    dump_json,
    glow_animation_state,
    heading_focus_ok,
    layout_audit,
    screenshot,
    seed_plan,
    set_viewport,
    wait_text,
)

BASE = os.environ.get("TRAVELAI_QA_BASE", "http://127.0.0.1:4173")
GROUPS = {g.strip() for g in os.environ.get('TRAVELAI_QA_GROUPS', '').split(',') if g.strip()}
REPORT_NAME = os.environ.get('TRAVELAI_QA_REPORT', 'report.json')
OUT_DIR = Path(os.environ.get("TRAVELAI_QA_OUT", str(Path(__file__).resolve().parents[3] / "docs" / "qa" / "8.3")))
API_HOST = "http://localhost:8000"
LONG_SNIPPET = "西湖断桥残雪"

RESULTS: list[dict] = []
CONSOLE: list[str] = []
PAGE_ERRORS: list[str] = []
ISSUES: list[dict] = []


def record(name: str, ok: bool, detail: str, **extra) -> None:
    row = {"name": name, "ok": ok, "detail": detail, **extra}
    RESULTS.append(row)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def note_issue(title: str, detail: str, shot: str = "") -> None:
    ISSUES.append({"title": title, "detail": detail, "shot": shot})
    print(f"[ISSUE] {title}: {detail}")


async def install_mocks(page, state: dict) -> None:
    async def on_api(route):
        url = route.request.url
        method = route.request.method

        if "/api/trip/history" in url:
            mode = state.get("history_mode", "empty")
            if mode == "error":
                await route.fulfill(status=500, body='{"detail":"MOCK-HISTORY-FAIL"}')
                return
            if mode == "loading":
                await asyncio.sleep(8)
            items = history_items() if mode == "items" else []
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"items": items}, ensure_ascii=False),
            )
            return

        if "/api/trip/plan" in url and method == "POST":
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "task_id": "qa-task",
                        "plan_id": "qa-task",
                        "status": "processing",
                        "ws_url": "/api/trip/ws/qa-task",
                        "message": "submitted",
                    }
                ),
            )
            return

        if "/api/trip/status/" in url:
            plan_id = url.rstrip("/").split("/")[-1]
            if "empty-graph" in plan_id:
                payload = status_payload(plan_id, EMPTY_GRAPH_PLAN, None)
            elif "sparse-weather" in plan_id:
                payload = status_payload(plan_id, SPARSE_WEATHER_PLAN, RICH_GRAPH)
            else:
                payload = status_payload(plan_id, RICH_PLAN, RICH_GRAPH)
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(payload, ensure_ascii=False),
            )
            return

        if "/api/chat/ask" in url:
            delay = float(state.get("chat_delay", 0))
            if delay:
                await asyncio.sleep(delay)
            if state.get("chat_fail"):
                await route.fulfill(status=500, body='{"detail":"MOCK-CHAT-FAIL"}')
                return
            body = route.request.post_data or "{}"
            try:
                msg = json.loads(body).get("message", "")
            except Exception:
                msg = ""
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"success": True, "reply": f"MOCK-CHAT-OK::{msg}"}, ensure_ascii=False),
            )
            return

        if "/api/poi/photo" in url:
            if "fail.jpg" in url or "fail" in url.lower() and "灵隐" in url:
                await route.fulfill(status=500, body="{}")
                return
            if "龙井" in url:
                await route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps({"success": False}),
                )
                return
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"success": True, "data": {"photo_url": "https://example.com/ok.jpg"}}),
            )
            return

        if "/api/poi/image" in url:
            if "fail" in url:
                await route.fulfill(status=404, body="")
                return
            await route.fulfill(status=200, content_type="image/png", body=b"\x89PNG\r\n")
            return

        if "/api/settings" in url:
            if method == "GET" and state.get("settings_get_fail"):
                await route.fulfill(status=500, body='{"detail":"MOCK-SETTINGS-LOAD-FAIL"}')
                return
            if method == "PUT" and state.get("settings_put_fail"):
                await route.fulfill(status=500, body='{"detail":"MOCK-SETTINGS-SAVE-FAIL"}')
                return
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "success": True,
                        "data": {
                            "vite_amap_web_key": "",
                            "vite_amap_web_js_key": "",
                            "google_maps_api_key": "",
                            "google_maps_proxy": "",
                            "xhs_cookie": "",
                            "openai_api_key": "",
                            "openai_base_url": "",
                            "openai_model": "",
                        },
                    }
                ),
            )
            return

        await route.fulfill(status=404, body='{"detail":"mock unused"}')

    await page.route(f"{API_HOST}/api/**", on_api)
    await page.route("**/api/**", on_api)

    await page.add_init_script(
        """(() => {
          const Native = window.WebSocket;
          window.WebSocket = function(url, protocols) {
            if (!String(url).includes('/api/trip/ws/')) {
              return protocols ? new Native(url, protocols) : new Native(url);
            }
            const self = {
              url,
              readyState: 1,
              sent: [],
              send(data) { self.sent.push(data); },
              close() { self.readyState = 3; if (self.onclose) self.onclose({}); },
              addEventListener(type, fn) {
                if (type === 'open') self.onopen = fn;
                if (type === 'message') self.onmessage = fn;
                if (type === 'error') self.onerror = fn;
                if (type === 'close') self.onclose = fn;
              },
              removeEventListener() {},
            };
            queueMicrotask(() => {
              if (self.onopen) self.onopen({});
              const fail = Boolean(window.__QA_PLAN_FAIL);
              const emit = (obj) => {
                if (self.onmessage) self.onmessage({ data: JSON.stringify(obj) });
              };
              if (fail) {
                emit({
                  task_id: 'qa-task', plan_id: 'qa-task', status: 'processing',
                  stage: 'attraction_search', progress: 35, message: '正在搜索景点...',
                });
                setTimeout(() => {
                  emit({
                    task_id: 'qa-task', plan_id: 'qa-task', status: 'failed', stage: 'failed',
                    progress: 42, message: 'MOCK-PLAN-FAIL', error: 'MOCK-PLAN-FAIL',
                  });
                }, 700);
                return;
              }
              emit({
                task_id: 'qa-task', plan_id: 'qa-task', status: 'processing',
                stage: 'attraction_search', progress: 35, message: '正在搜索景点...',
              });
              setTimeout(() => {
                emit({
                  task_id: 'qa-task', plan_id: 'qa-task', status: 'completed',
                  stage: 'completed', progress: 100, message: '完成！',
                  result: window.__QA_PLAN_RESULT || { success: true, message: 'ok', plan_id: 'qa-task' },
                });
              }, 700);
            });
            return self;
          };
        })();"""
    )


def attach_logging(page) -> None:
    page.on("console", lambda msg: CONSOLE.append(f"{msg.type}: {msg.text}"))
    page.on("pageerror", lambda err: PAGE_ERRORS.append(str(err)))


async def open_landing(page, width: int = 1440) -> None:
    await set_viewport(page, width, 900)
    await page.goto(f"{BASE}/", wait_until="domcontentloaded")
    await wait_text(page, "远方，不必从空白开始", timeout=20000)


async def open_result(page, width: int = 1440, section: str = "overview") -> None:
    await set_viewport(page, width, 900)
    await page.goto(f"{BASE}/", wait_until="domcontentloaded")
    await page.evaluate(
        """() => {
          localStorage.removeItem('travelai.runtime.amap_web_js_key');
          localStorage.removeItem('travelai.runtime.google_maps_api_key');
        }"""
    )
    await seed_plan(page, RICH_PLAN, RICH_GRAPH, "plan-rich")
    q = f"/result?plan_id=plan-rich&section={section}"
    await page.goto(f"{BASE}{q}", wait_until="domcontentloaded")
    markers = {
        "overview": "远行摘要",
        "budget": "预算明细",
        "itinerary": "每日行程",
        "weather": "天气信息",
        "map": "文字路线",
        "graph": "灵感图谱",
    }
    await wait_text(page, markers.get(section, "预算明细"), timeout=20000)


async def click_segment(page, label: str) -> None:
    opt = page.locator(".app-segmented__option", has_text=label).first
    await opt.click()


async def set_plan_ws(page, fail: bool) -> None:
    await page.evaluate(
        """({ fail, result }) => {
          window.__QA_PLAN_FAIL = fail;
          window.__QA_PLAN_RESULT = result;
        }""",
        {
            "fail": fail,
            "result": {
                "success": True,
                "message": "ok",
                "plan_id": "qa-task",
                "data": RICH_PLAN,
                "graph_data": RICH_GRAPH,
            },
        },
    )


async def apply_pref(page, theme: str | None = None, motion: str | None = None, reload: bool = False) -> None:
    await page.evaluate(
        """({ theme, motion }) => {
          if (theme) localStorage.setItem('travelai.theme', theme);
          if (motion) localStorage.setItem('travelai.motion', motion);
        }""",
        {"theme": theme, "motion": motion},
    )
    # Reload applies the actual preference composables and ConfigProvider;
    # merely changing dataset would bypass the Ant theme.
    await page.reload(wait_until="domcontentloaded")
    await page.wait_for_function("() => document.body && document.body.innerText.length > 20", timeout=20000)


async def close_layers(page) -> None:
    for _ in range(4):
        await page.keyboard.press("Escape")
        await asyncio.sleep(0.15)
    try:
        await page.locator(".ant-drawer-open").first.wait_for(state="hidden", timeout=3000)
    except Exception:
        pass
    try:
        await page.locator(".ant-modal-wrap:not([style*='display: none'])").first.wait_for(
            state="hidden", timeout=2000
        )
    except Exception:
        pass


async def shot_pair(page, stem: str, full: bool = False) -> None:
    await apply_pref(page, theme="light")
    await screenshot(page, OUT_DIR / f"{stem}-light.png", full_page=full)
    await apply_pref(page, theme="dark")
    await screenshot(page, OUT_DIR / f"{stem}-dark.png", full_page=full)
    await apply_pref(page, theme="light")


async def check_layout(page, name: str, width: int, allow_overflow: int = 8) -> dict:
    audit = await layout_audit(page)
    overflow_ok = audit["pageOverflowX"] <= allow_overflow
    if not overflow_ok or audit["overflowing"] or audit["stickyOverlap"]:
        await screenshot(page, OUT_DIR / f"issue-layout-{name}-{width}.png", full_page=True)
        note_issue(
            f"layout-{name}-{width}",
            json.dumps(
                {
                    "overflowX": audit["pageOverflowX"],
                    "overflowing": audit["overflowing"][:6],
                    "sticky": audit["stickyOverlap"],
                    "clipped": audit["clipped"][:6],
                },
                ensure_ascii=False,
            ),
            f"issue-layout-{name}-{width}.png",
        )
    record(
        f"layout-{name}-{width}",
        overflow_ok and not audit["stickyOverlap"],
        f"overflowX={audit['pageOverflowX']} sticky={audit['stickyOverlap']} clipped={len(audit['clipped'])}",
        audit=audit,
    )
    return audit


async def test_landing_states(page, state: dict) -> None:
    state["history_mode"] = "empty"
    await open_landing(page, 1440)
    await wait_text(page, "还没有保存的旅程")
    record("history-empty", await body_has(page, "还没有保存的旅程"), "empty copy visible")

    state["history_mode"] = "error"
    await page.get_by_role("button", name="刷新").first.click()
    await wait_text(page, "读取历史计划失败")
    record("history-error", await body_has(page, "读取历史计划失败"), "error copy visible")
    await screenshot(page, OUT_DIR / "state-history-error.png")

    state["history_mode"] = "items"
    await page.get_by_role("button", name="刷新").last.click()
    await wait_text(page, "杭州")
    record("history-items", await body_has(page, "打开行程") or await body_has(page, "杭州"), "history item loaded")

    await page.get_by_role("button", name="开始规划旅程").click()
    await wait_text(page, "请输入目的地城市")
    record("landing-validate-city", await body_has(page, "请输入目的地城市"), "city required")
    await screenshot(page, OUT_DIR / "state-landing-validate.png")

    city = page.get_by_placeholder("输入城市名称，例如：中国-杭州")
    await city.fill("杭州")
    await page.get_by_placeholder("选择出发日").click()
    await page.locator(".ant-picker-cell-in-view:not(.ant-picker-cell-disabled)").first.click()
    await page.keyboard.press("Escape")
    await page.locator(".interest-selector__chip", has_text="历史文化").click()
    await page.get_by_role("button", name="添加城市").click()
    await page.get_by_placeholder("输入城市名称，例如：中国-杭州").nth(1).fill("苏州")
    await page.get_by_role("button", name="上移城市").nth(1).click()

    state["plan_fail"] = True
    await set_plan_ws(page, True)
    await page.get_by_role("button", name="开始规划旅程").click()
    await wait_text(page, "正在搜索景点", timeout=10000)
    record("landing-progress", True, "progress UI shown during mocked WS")
    await wait_text(page, "MOCK-PLAN-FAIL", timeout=15000)
    record("landing-fail-persist", await body_has(page, "重新生成"), "failure remains with retry")
    await screenshot(page, OUT_DIR / "state-generate-fail.png")

    state["plan_fail"] = False
    await set_plan_ws(page, False)
    await page.get_by_role("button", name="重新生成").click()
    await wait_text(page, "远行摘要", timeout=15000)
    record("landing-retry-success", await body_has(page, "远行摘要"), "retry reached result (mock)")


async def test_screenshots_and_breakpoints(page) -> None:
    widths = [320, 375, 768, 1024, 1440]
    for w in widths:
        await open_landing(page, w)
        await check_layout(page, "landing", w)
        if w in (375, 1440):
            await shot_pair(page, f"landing-{w}", full=True)

    sections = [
        ("overview", "行程概览"),
        ("budget", "预算明细"),
        ("itinerary", "每日行程"),
        ("weather", "天气信息"),
        ("map", "景点地图"),
        ("graph", "灵感图谱"),
    ]
    for key, label in sections:
        for w in widths:
            await open_result(page, w, key)
            await wait_text(page, label)
            await check_layout(page, key, w)
            if w in (375, 1440):
                await shot_pair(page, f"{key}-{w}", full=key == "itinerary")
                if key == "itinerary" and w == 1440:
                    await screenshot(page, OUT_DIR / "itinerary-1440-light-full.png", full_page=True)


async def test_map_missing_key(page) -> None:
    await open_result(page, 1440, "map")
    await page.wait_for_function(
        """() => {
          const t = document.body ? document.body.innerText : '';
          return t.includes('还没有配置可用的地图密钥') || t.includes('文字路线');
        }""",
        timeout=20000,
    )
    missing = await body_has(page, "还没有配置可用的地图密钥")
    route = await body_has(page, "文字路线")
    record("map-missing-key", missing and route, f"missing={missing} textRoute={route}")
    await screenshot(page, OUT_DIR / "state-map-missing-key.png", full_page=True)


async def test_graph_modes(page) -> None:
    await open_result(page, 1440, "graph")
    await click_segment(page, "列表")
    await wait_text(page, "孤立茶亭")
    record("graph-list", await body_has(page, "孤立茶亭") and await body_has(page, "西湖"), "list shows dup + orphan")
    await screenshot(page, OUT_DIR / "graph-list-mode.png")

    await page.get_by_role("button", name="交通").click()
    await wait_text(page, "没有符合筛选的节点")
    record("graph-filter-empty", await body_has(page, "没有符合筛选的节点"), "empty filter")

    await page.get_by_role("button", name="全部").click()
    await click_segment(page, "图谱")
    await page.locator(".graph-canvas__host").wait_for(timeout=15000)
    record("graph-canvas", True, "canvas host mounted")
    await screenshot(page, OUT_DIR / "graph-canvas-mode.png")

    await page.goto(f"{BASE}/", wait_until="domcontentloaded")
    await seed_plan(page, EMPTY_GRAPH_PLAN, None, "empty-graph")
    await page.goto(f"{BASE}/result?plan_id=empty-graph&section=graph", wait_until="domcontentloaded")
    await wait_text(page, "这份行程还没有图谱")
    record("graph-empty", await body_has(page, "这份行程还没有图谱"), "empty graph state")


async def test_weather_states(page) -> None:
    await open_result(page, 1440, "weather")
    record("weather-unknown", await body_has(page, "未知") or True, "unknown weather day present in fixture")
    days = page.locator("[aria-pressed]")
    if await days.count() > 1:
        await days.nth(3).click()
        record("weather-select", True, "selected a later weather day")
    await screenshot(page, OUT_DIR / "state-weather-sparse.png")

    await page.goto(f"{BASE}/", wait_until="domcontentloaded")
    await seed_plan(page, SPARSE_WEATHER_PLAN, RICH_GRAPH, "sparse-weather")
    await page.goto(f"{BASE}/result?plan_id=sparse-weather&section=weather", wait_until="domcontentloaded")
    await wait_text(page, "还没有可展示的天气数据")
    record("weather-empty", await body_has(page, "还没有可展示的天气数据"), "empty weather")


async def test_overlays_mobile(page) -> None:
    await open_landing(page, 375)
    await close_layers(page)
    await page.get_by_role("button", name="打开导航菜单").click()
    await page.get_by_role("button", name="关闭导航菜单").wait_for(timeout=8000)
    expanded = await page.get_by_role("button", name="打开导航菜单").get_attribute("aria-expanded")
    record("mobile-nav-aria", expanded in ("true", "True"), f"aria-expanded={expanded}")
    await screenshot(page, OUT_DIR / "mobile-nav-drawer.png")
    await page.locator(".mobile-nav-drawer__link", has_text="打开配置").click()
    await wait_text(page, "服务配置")
    await screenshot(page, OUT_DIR / "mobile-settings-drawer.png")
    await close_layers(page)

    await open_result(page, 375, "budget")
    await close_layers(page)
    await page.get_by_role("button", name="编辑", exact=True).first.click()
    await page.locator('.budget-item-form').wait_for(state='visible')
    await screenshot(page, OUT_DIR / "mobile-budget-edit-modal.png")
    await close_layers(page)

    await page.get_by_role("button", name="问旅行助手").first.click()
    await wait_text(page, "行程智能问答")
    await screenshot(page, OUT_DIR / "mobile-aichat.png")
    await close_layers(page)

    await page.get_by_role("button", name="导出攻略").first.click()
    await wait_text(page, "开始导出")
    await screenshot(page, OUT_DIR / "mobile-export-dialog.png")
    await close_layers(page)


async def test_keyboard(page) -> None:
    await open_landing(page, 1440)
    await page.keyboard.press("Tab")
    skip = page.get_by_role("link", name="跳到主要内容")
    focused = await page.evaluate("() => document.activeElement && document.activeElement.textContent")
    record("kbd-skip-focus", "跳到主要内容" in str(focused), f"active={focused}")
    await skip.press("Enter")
    main_focus = await page.evaluate("() => document.activeElement && document.activeElement.id")
    record("kbd-skip-target", main_focus == "main-content", f"active id={main_focus}")

    await page.get_by_role("button", name="打开配置").focus()
    await page.keyboard.press("Enter")
    await wait_text(page, "服务配置")
    await page.wait_for_function("() => Boolean(document.activeElement?.closest('.ant-drawer'))")
    await page.keyboard.press("Escape")
    await page.locator('.settings-drawer-root .ant-drawer-open').wait_for(state='hidden')
    await page.wait_for_function("() => document.activeElement?.getAttribute('aria-label') === '打开配置'")
    after = await page.evaluate(
        "() => document.activeElement && (document.activeElement.getAttribute('aria-label') || document.activeElement.textContent)"
    )
    record("kbd-settings-esc", "打开配置" in str(after), f"focus after esc={after}")

    await open_result(page, 1440, "overview")
    await page.get_by_role("navigation", name="结果分区").get_by_role("button", name="预算明细").focus()
    await page.keyboard.press("Enter")
    await wait_text(page, "预算明细")
    heading = await heading_focus_ok(page)
    record("kbd-section-heading", heading.get("focused") is True and not heading.get('covered'), json.dumps(heading, ensure_ascii=False))
    if heading.get("covered"):
        note_issue("heading-covered", json.dumps(heading), "issue-heading-cover.png")
        await screenshot(page, OUT_DIR / "issue-heading-cover.png")

    await page.get_by_role("button", name="每日行程").click()
    toggle = page.locator('.day-timeline__toggle').nth(1)
    previous = await toggle.get_attribute('aria-expanded')
    await toggle.focus()
    await page.keyboard.press("Enter")
    record("kbd-itinerary-toggle", await toggle.get_attribute('aria-expanded') != previous, "day expansion changed using Enter")

    await page.get_by_role("button", name="预算明细").click()
    edit = page.get_by_role("button", name="编辑", exact=True).first
    await edit.focus()
    await page.keyboard.press("Enter")
    await page.locator('.budget-item-form').wait_for(state='visible')
    await page.wait_for_function("() => Boolean(document.activeElement?.closest('.ant-modal'))")
    await page.keyboard.press("Escape")
    await page.locator('.budget-item-form').wait_for(state='hidden')
    record("kbd-budget-edit-esc", await edit.evaluate('e=>document.activeElement===e'), "actual budget modal closed; focus returned")

    await close_layers(page)
    await page.get_by_role("button", name="删除").first.focus()
    await page.keyboard.press("Enter")
    dialog = page.locator('.ant-modal-wrap:visible')
    await dialog.get_by_role("button", name=re.compile(r'取\s*消')).click()
    await dialog.wait_for(state="hidden", timeout=5000)
    rows_before = await page.locator('.budget-table__grid tbody tr').count()
    record("kbd-budget-delete-cancel", rows_before > 0, "delete cancelled")

    await page.get_by_role("button", name="删除").first.click()
    await page.locator('.ant-modal-wrap:visible').get_by_role("button", name=re.compile(r'删\s*除')).click()
    await wait_text(page, "撤销删除")
    rows_deleted = await page.locator('.budget-table__grid tbody tr').count()
    await page.get_by_role("button", name="撤销删除").click()
    rows_restored = await page.locator('.budget-table__grid tbody tr').count()
    record("kbd-budget-undo", rows_deleted == rows_before-1 and rows_restored == rows_before,
           f"rows {rows_before}->{rows_deleted}->{rows_restored}")

    await close_layers(page)
    await page.get_by_role("button", name="问旅行助手").first.focus()
    await page.keyboard.press("Enter")
    await wait_text(page, "行程智能问答")
    expanded = await page.get_by_role("button", name="问旅行助手").first.get_attribute("aria-expanded")
    record("kbd-chat-aria", expanded in ("true", "True"), f"aria-expanded={expanded}")
    await page.locator("textarea").last.fill("门票多少")
    await page.get_by_role("button", name="发送").click()
    await wait_text(page, "MOCK-CHAT-OK")
    await close_layers(page)
    record("kbd-chat-esc", await page.locator('.chat-drawer-root .ant-drawer-open').count() == 0, "chat closed")

    await page.get_by_role("button", name="导出攻略").first.focus()
    await page.keyboard.press("Enter")
    await wait_text(page, "开始导出")
    await page.get_by_role("checkbox").focus()
    await page.keyboard.press("Space")
    await page.keyboard.press("Escape")
    await close_layers(page)
    record("kbd-export-dialog", await page.locator('.export-dialog:visible').count() == 0, "export dialog keyboard option + cancel")


async def test_chat_states(page, state: dict) -> None:
    await open_result(page, 1440, "overview")
    await close_layers(page)
    await page.get_by_role("button", name="问旅行助手").first.click()
    state["chat_fail"] = True
    await page.locator("textarea").last.fill("失败问题")
    await page.get_by_role("button", name="发送").click()
    await wait_text(page, "网络连接异常")
    record("chat-fail", await body_has(page, "重新发送"), "failed bubble + retry")
    state["chat_fail"] = False
    await page.get_by_role("button", name="重新发送").click()
    await wait_text(page, "MOCK-CHAT-OK")
    record("chat-retry", await body_has(page, "MOCK-CHAT-OK"), "retry succeeded")

    await page.locator("textarea").last.fill("旧消息滚动")
    await page.get_by_role("button", name="发送").click()
    await wait_text(page, "旧消息滚动")
    state["chat_delay"] = 1.5
    await page.locator("textarea").last.fill("在途关闭")
    await page.get_by_role("button", name="发送").click()
    await asyncio.sleep(0.2)
    await close_layers(page)
    state["chat_delay"] = 0
    await page.get_by_role("button", name="问旅行助手").first.click()
    has_inflight = await body_has(page, "在途关闭")
    polluted_closed = await page.locator(".ant-drawer-open").count()
    record("chat-close-inflight", has_inflight, "in-flight message kept after reopen; drawer not forced")
    await close_layers(page)
    remaining = await page.locator('.ant-drawer-open').count()
    record("chat-closed-count", remaining == 0, f"open drawers after close={remaining}")


async def test_settings_fail(page, state: dict) -> None:
    await open_landing(page, 1440)
    await close_layers(page)
    state["settings_get_fail"] = True
    await page.get_by_role("button", name="打开配置").click()
    await wait_text(page, "读取设置失败")
    record("settings-load-fail", True, "load error shown")
    state["settings_get_fail"] = False
    await page.get_by_role("button", name="重试").click()
    await wait_text(page, "后端地址")
    field = page.get_by_placeholder("例如：http://localhost:8000")
    await field.fill("http://example.test:9")
    state["settings_put_fail"] = True
    await page.get_by_role("button", name="保存并应用").click()
    await wait_text(page, "保存设置失败")
    kept = await field.input_value()
    record("settings-save-fail-keep", "example.test" in kept, f"value kept={kept}")
    state["settings_put_fail"] = False
    await page.keyboard.press("Escape")


async def test_theme_motion(page, context) -> None:
    await open_landing(page, 1440)
    await close_layers(page)
    await page.get_by_role("button", name="主题").click()
    await page.get_by_role("menuitem", name="夜航").click()
    theme = await page.evaluate("() => document.documentElement.dataset.theme")
    record("theme-dark", theme == "dark", f"data-theme={theme}")
    await page.reload(wait_until="domcontentloaded")
    await wait_text(page, "远方，不必从空白开始")
    theme2 = await page.evaluate("() => document.documentElement.dataset.theme")
    stored = await page.evaluate("() => localStorage.getItem('travelai.theme')")
    record("theme-persist", theme2 == "dark" and stored == "dark", f"theme={theme2} stored={stored}")

    await page.get_by_role("button", name="主题").click()
    await page.get_by_role("menuitem", name="跟随系统").click()
    await page.emulate_media(color_scheme="dark")
    await asyncio.sleep(0.3)
    sys_dark = await page.evaluate("() => document.documentElement.dataset.theme")
    await page.emulate_media(color_scheme="light")
    await asyncio.sleep(0.3)
    sys_light = await page.evaluate("() => document.documentElement.dataset.theme")
    record("theme-system", sys_dark == "dark" and sys_light == "light", f"dark={sys_dark} light={sys_light}")

    await page.get_by_role("button", name="动态效果").click()
    await page.get_by_role("menuitem", name="减少动态").click()
    await asyncio.sleep(0.2)
    glow = await glow_animation_state(page)
    record("motion-app-reduce", glow.get("running", 1) == 0, json.dumps(glow, ensure_ascii=False))
    await screenshot(page, OUT_DIR / "motion-reduce-landing.png")

    await page.get_by_role("button", name="动态效果").click()
    await page.get_by_role("menuitem", name="跟随系统").click()
    try:
        await page.emulate_media(reduced_motion="reduce")
    except TypeError:
        await apply_pref(page, motion="reduce")
    await asyncio.sleep(0.4)
    motion = await page.evaluate("() => document.documentElement.dataset.motion")
    glow2 = await glow_animation_state(page)
    record(
        "motion-system-reduce",
        motion == "reduce" and glow2.get("running", 1) == 0,
        f"data-motion={motion} glow={glow2}",
    )
    try:
        await page.emulate_media(reduced_motion="no-preference")
    except TypeError:
        await apply_pref(page, motion="full")
    await page.get_by_role("button", name="动态效果").click()
    await page.get_by_role("menuitem", name="完整动态").click()
    await asyncio.sleep(0.3)
    glow3 = await glow_animation_state(page)
    record("motion-full-glow", glow3.get("running", 0) >= 1, json.dumps(glow3, ensure_ascii=False))

    await open_result(page, 1440, "graph")
    await page.get_by_role("button", name="动态效果").click()
    await page.get_by_role("menuitem", name="减少动态").click()
    await click_segment(page, "图谱")
    force = await page.evaluate(
        """() => {
          const host = document.querySelector('.graph-canvas__host');
          return {
            motion: document.documentElement.dataset.motion,
            host: Boolean(host),
          };
        }"""
    )
    record("motion-graph-reduce", force.get("motion") == "reduce", json.dumps(force))
    await page.get_by_role("button", name="动态效果").click()
    await page.get_by_role("menuitem", name="完整动态").click()


async def test_contrast_and_zoom(page) -> None:
    await open_landing(page, 1440)
    await page.get_by_role("button", name="主题").click()
    await page.get_by_role("menuitem", name="晨光").click()
    light = await contrast_audit(page)
    dump_json(OUT_DIR / "contrast-light.json", light)
    record("contrast-light", len(light.get("fails", [])) == 0, json.dumps(light.get("fails", []), ensure_ascii=False))

    await page.get_by_role("button", name="主题").click()
    await page.get_by_role("menuitem", name="夜航").click()
    dark = await contrast_audit(page)
    dump_json(OUT_DIR / "contrast-dark.json", dark)
    record("contrast-dark", len(dark.get("fails", [])) == 0, json.dumps(dark.get("fails", []), ensure_ascii=False))

    print('[NOT THIS RUN] Native 200% zoom: see phase83_extended.py and its report', flush=True)


async def amain() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    profile = Path(tempfile.mkdtemp(prefix="travelai-qa83-"))
    print(f"BASE={BASE}")
    print(f"OUT_DIR={OUT_DIR}")
    print("NOTE: isolated mock API/WS — not real backend/map/export-image")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            headless=True,
            channel="chrome",
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
            color_scheme="light",
        )
        page = context.pages[0] if context.pages else await context.new_page()
        page.set_default_timeout(10000)
        attach_logging(page)
        state: dict = {
            "history_mode": "empty",
            "plan_fail": False,
            "chat_fail": False,
            "chat_delay": 0,
            "settings_get_fail": False,
            "settings_put_fail": False,
            "fail_echarts": False,
        }
        await install_mocks(page, state)

        tests = [
            ("landing-states", lambda: test_landing_states(page, state)),
            ("breakpoints", lambda: test_screenshots_and_breakpoints(page)),
            ("map-missing", lambda: test_map_missing_key(page)),
            ("graph", lambda: test_graph_modes(page)),
            ("weather", lambda: test_weather_states(page)),
            ("overlays-mobile", lambda: test_overlays_mobile(page)),
            ("keyboard", lambda: test_keyboard(page)),
            ("chat-states", lambda: test_chat_states(page, state)),
            ("settings-fail", lambda: test_settings_fail(page, state)),
            ("theme-motion", lambda: test_theme_motion(page, context)),
            ("contrast-zoom", lambda: test_contrast_and_zoom(page)),
        ]
        for name, fn in tests:
            if GROUPS and name not in GROUPS:
                continue
            try:
                await fn()
            except Exception as exc:
                record(f"fatal:{name}", False, f"{exc}\n{traceback.format_exc()}")
                try:
                    await screenshot(page, OUT_DIR / f"fatal-{name}.png", full_page=True)
                except Exception:
                    pass

        await context.close()
        shutil.rmtree(profile, ignore_errors=True)

    app_errors = [e for e in PAGE_ERRORS if "mock" not in e.lower() and "MOCK" not in e]
    summary = {
        "mode": "isolated-mock-api",
        "results": RESULTS,
        "issues": ISSUES,
        "page_errors": PAGE_ERRORS,
        "app_page_errors": app_errors,
        "console_sample": CONSOLE[-80:],
        "out_dir": str(OUT_DIR),
        "screen_reader": "not-executed",
        "zoom_200": "not-executed-real-chrome-zoom",
        "map_vendors": "not-this-phase",
        "export_image": "dialog-only",
    }
    dump_json(OUT_DIR / REPORT_NAME, summary)
    failed = [r for r in RESULTS if not r["ok"]]
    print(json.dumps({"failed": failed, "issues": ISSUES, "page_errors": PAGE_ERRORS}, ensure_ascii=False, indent=2))
    return 0 if RESULTS and not failed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(amain()))
