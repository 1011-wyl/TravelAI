"""
Phase 9.2 live backend E2E.

Uses a real local API/WebSocket. Isolated Chrome profile.
Does not mock /api. Does not print secrets.
Not a Google Maps vendor acceptance.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import os
import re
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

from playwright.async_api import async_playwright
from PIL import Image, ImageStat

from qa_helpers import body_has, dump_json, screenshot, set_viewport, wait_text

BASE = os.environ.get("TRAVELAI_QA_BASE", "http://127.0.0.1:5173")
OUT_DIR = Path(os.environ.get("TRAVELAI_QA_OUT", str(Path(__file__).resolve().parents[3] / "docs" / "qa" / "9.2")))
GENERATE_TIMEOUT_MS = int(os.environ.get("TRAVELAI_QA_GENERATE_MS", "480000"))
ONLY = {part.strip() for part in os.environ.get("TRAVELAI_QA_ONLY", "").split(",") if part.strip()}
REPORT_NAME = os.environ.get("TRAVELAI_QA_REPORT", "report.json")

RESULTS: list[dict] = []
PAGE_ERRORS: list[str] = []
CONSOLE: list[str] = []
NETWORK: list[str] = []
WS_EVENTS: list[dict] = []
URL_PATTERN = re.compile(r'https?://[^\s]+')


def websocket_frame(payload) -> None:
    try:
        event = json.loads(payload)
        WS_EVENTS.append({key: event.get(key) for key in ('task_id', 'status', 'stage', 'progress')})
    except (ValueError, TypeError):
        pass


def record(name: str, ok: bool, detail: str, **extra) -> None:
    row = {"name": name, "ok": ok, "detail": detail, **extra}
    RESULTS.append(row)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}", flush=True)


async def close_layers(page) -> None:
    for _ in range(3):
        await page.keyboard.press("Escape")
        await asyncio.sleep(0.2)


async def fill_min_trip(page) -> None:
    await page.get_by_placeholder("输入城市名称，例如：中国-杭州").first.fill("杭州")
    await page.locator('.city-route__control input[role="spinbutton"]').first.fill('1')
    await page.get_by_placeholder("选择出发日").click()
    await page.locator(".ant-picker-cell-in-view:not(.ant-picker-cell-disabled)").first.click()
    await page.keyboard.press("Escape")
    await page.locator(".interest-selector__chip", has_text="历史文化").click()


async def wait_generate_outcome(page) -> str:
    """Return success|fail|timeout."""
    try:
        await page.wait_for_function(
            """() => {
              const t = document.body ? document.body.innerText : '';
              if (t.includes('远行摘要')) return 'success';
              if (t.includes('重新生成') || t.includes('生成旅行计划失败')) return 'fail';
              return false;
            }""",
            timeout=GENERATE_TIMEOUT_MS,
        )
        text = await page.evaluate("() => document.body.innerText")
        if "远行摘要" in text:
            return "success"
        return "fail"
    except Exception:
        return "timeout"


async def session_ids(page) -> dict:
    return await page.evaluate(
        """() => ({
          href: location.href,
          planQuery: new URLSearchParams(location.search).get('plan_id'),
          sessionPlanId: sessionStorage.getItem('planId'),
          hasTrip: Boolean(sessionStorage.getItem('tripPlan')),
        })"""
    )


async def test_landing_and_generate(page) -> str | None:
    await set_viewport(page, 1440, 900)
    await page.goto(f"{BASE}/", wait_until="domcontentloaded")
    await wait_text(page, "远方，不必从空白开始", timeout=20000)
    await screenshot(page, OUT_DIR / "01-landing.png")

    await page.get_by_role("button", name="开始规划旅程").click()
    await wait_text(page, "请输入目的地城市")
    record("form-validate-city", await body_has(page, "请输入目的地城市"), "empty submit shows city error")

    await fill_min_trip(page)
    submit = page.locator(".trip-planner__submit")
    await submit.click()
    await asyncio.sleep(0.6)
    form_gone = await page.locator(".trip-planner__submit").count() == 0
    journey = await body_has(page, "正在初始化") or await body_has(page, "理解期待") or await body_has(page, "本次提交")
    record("anti-double-submit", form_gone and journey, f"form_gone={form_gone} journey={journey}")
    await screenshot(page, OUT_DIR / "02-generating.png")

    outcome = await wait_generate_outcome(page)
    live_progress = [event for event in WS_EVENTS if event.get('status') not in ('completed', 'failed')]
    record("ws-progress-ui", bool(live_progress) and journey, f"real WS processing frames={len(live_progress)}")
    record("generate-outcome", outcome == "success", f"outcome={outcome}")
    await screenshot(page, OUT_DIR / f"03-generate-{outcome}.png", full_page=True)
    if outcome != "success":
        return None
    ids = await session_ids(page)
    ok_ids = bool(ids.get("planQuery")) and ids.get("planQuery") == ids.get("sessionPlanId") and ids.get("hasTrip")
    record("plan-id-session", ok_ids, json.dumps({k: ids.get(k) for k in ("planQuery", "sessionPlanId", "hasTrip")}))
    return ids.get("planQuery")


async def test_result_navigation(page, plan_id: str) -> None:
    sections = [
        ("overview", "行程概览"),
        ("budget", "预算明细"),
        ("map", "景点地图"),
        ("itinerary", "每日行程"),
        ("graph", "灵感图谱"),
        ("weather", "天气信息"),
    ]
    for key, label in sections:
        await page.get_by_role("navigation", name="结果分区").get_by_role("button", name=label).click()
        await wait_text(page, label, timeout=15000)
        href = await page.evaluate("() => location.search")
        record(f"section-{key}", f"section={key}" in href or key in href, f"query={href}")
    await screenshot(page, OUT_DIR / "04-sections.png")

    await page.go_back()
    await asyncio.sleep(0.4)
    await page.go_forward()
    await asyncio.sleep(0.4)
    ids = await session_ids(page)
    record("history-bf", ids.get("planQuery") == plan_id, f"planQuery={ids.get('planQuery')}")

    await page.reload(wait_until="domcontentloaded")
    await wait_text(page, "远行摘要", timeout=30000)
    ids2 = await session_ids(page)
    record("refresh-restore", ids2.get("planQuery") == plan_id and ids2.get("hasTrip"), json.dumps(ids2))
    await screenshot(page, OUT_DIR / "05-refresh.png")


async def test_history_open(page, plan_id: str) -> None:
    response = await page.context.request.get('http://127.0.0.1:8000/api/trip/history?limit=8')
    items = (await response.json()).get('items', [])
    index = next((i for i, item in enumerate(items) if item.get('plan_id') == plan_id), None)
    if index is None:
        raise AssertionError('Expected live plan absent from history')
    await page.goto(f"{BASE}/", wait_until="domcontentloaded")
    await wait_text(page, "再次出发", timeout=20000)
    await page.locator(".trip-ticket__open").first.scroll_into_view_if_needed()
    await screenshot(page, OUT_DIR / "06-history-list.png")
    opener = page.locator(".trip-ticket").nth(index)
    await opener.click()
    await wait_text(page, "远行摘要", timeout=30000)
    ids = await session_ids(page)
    record("history-open", ids.get("planQuery") == plan_id, json.dumps(ids))


async def test_budget_and_itinerary(page) -> None:
    await page.get_by_role("navigation", name="结果分区").get_by_role("button", name="预算明细").click()
    await wait_text(page, "预算明细")
    before = await page.evaluate("() => sessionStorage.getItem('tripPlan')")
    edit_btn = page.locator(".budget-table__grid .budget-table__actions").get_by_role("button", name="编辑", exact=True).first
    await edit_btn.scroll_into_view_if_needed()
    await edit_btn.click()
    await page.locator('.budget-item-form').wait_for(state='visible')
    await page.wait_for_function("() => Boolean(document.activeElement?.closest('.ant-modal'))")
    await page.keyboard.press("Escape")
    await page.locator('.budget-item-form').wait_for(state='hidden')
    after_cancel = await page.evaluate("() => sessionStorage.getItem('tripPlan')")
    record("budget-cancel", before == after_cancel, "cancel did not rewrite session")

    await edit_btn.click()
    amount = page.locator('.budget-item-form input[role="spinbutton"]')
    await amount.wait_for(state="visible")
    raw = await amount.input_value()
    try:
        nxt = str(int(float(raw or "0")) + 8)
    except ValueError:
        nxt = "108"
    await amount.click()
    await amount.fill(nxt)
    await page.locator(".ant-modal-footer .ant-btn-primary").last.click()
    await asyncio.sleep(0.8)
    after_save = await page.evaluate("() => sessionStorage.getItem('tripPlan')")
    saved = json.loads(after_save)
    expected = sum(max(0, float(a.get('ticket_price') or 0)) for d in saved['days'] for a in d.get('attractions', []))
    expected += sum(max(0, float((d.get('hotel') or {}).get('estimated_cost') or 0)) for d in saved['days'])
    expected += sum(max(0, float(m.get('estimated_cost') or 0)) for d in saved['days'] for m in d.get('meals', []))
    expected += max(0, float(saved['budget'].get('total_transportation') or 0))
    record("budget-save", after_save != before and abs(saved['budget']['total'] - round(expected, 2)) < .011,
           f"amount saved {raw}->{nxt}; total matches original four-category contract")

    rows_before = await page.locator('.budget-table__grid tbody tr').count()
    await page.locator(".budget-table__grid .budget-table__actions").get_by_role("button", name="删除").first.click()
    await page.locator(".ant-modal-footer .ant-btn-dangerous, .ant-modal-footer .ant-btn-primary").last.wait_for(state="visible")
    await page.locator(".ant-modal-footer button").last.click()
    await wait_text(page, "撤销删除")
    await page.get_by_role("button", name="撤销删除").click()
    rows_after = await page.locator('.budget-table__grid tbody tr').count()
    undo_plan = json.loads(await page.evaluate("sessionStorage.getItem('tripPlan')"))
    record("budget-undo", rows_before == rows_after and saved == undo_plan, "deleted row and data restored, no whole-plan rollback")
    await screenshot(page, OUT_DIR / "07-budget.png")

    await page.get_by_role("navigation", name="结果分区").get_by_role("button", name="每日行程").click()
    await wait_text(page, "每日行程")
    edit_trip = page.get_by_role("button", name="编辑行程")
    if await edit_trip.count():
        original_names = [a['name'] for a in saved['days'][0]['attractions']]
        await edit_trip.first.click()
        field = page.locator('.itinerary-stop__edit input:not([role="spinbutton"])').first
        original_address = await field.input_value()
        await field.fill(original_address + ' QA-CANCEL')
        await page.get_by_role("button", name="取消编辑").click()
        await edit_trip.first.click()
        record("itinerary-cancel", await field.input_value() == original_address and
               json.loads(await page.evaluate("sessionStorage.getItem('tripPlan')")) == saved,
               "draft address rolled back; session not rewritten")
        expand = page.get_by_role("button", name="展开")
        if await expand.count():
            await expand.first.click()
        down = page.locator('.day-timeline').first.get_by_role("button", name="下移", exact=True).first
        if await down.count():
            await down.first.click()
        save = page.get_by_role("button", name="保存修改")
        if await save.count():
            await save.first.click()
            updated = json.loads(await page.evaluate("sessionStorage.getItem('tripPlan')"))
            new_names = [a['name'] for a in updated['days'][0]['attractions']]
            expected_names = original_names[:]
            if len(expected_names) > 1:
                expected_names[0], expected_names[1] = expected_names[1], expected_names[0]
            record("itinerary-save", len(original_names) > 1 and new_names == expected_names, "actual order change persisted")
        else:
            record("itinerary-save", False, "no save control")
    else:
        record("itinerary-cancel", False, "no 编辑行程")
        record("itinerary-save", False, "skipped")
    await screenshot(page, OUT_DIR / "08-itinerary.png")


async def test_map_chat_export(page) -> None:
    await page.get_by_role("navigation", name="结果分区").get_by_role("button", name="景点地图").click()
    await wait_text(page, "景点地图", timeout=20000)
    await page.locator('#amap-container canvas').first.wait_for(state='visible', timeout=60000)
    await page.wait_for_function("() => document.querySelectorAll('#amap-container .amap-marker').length > 0", timeout=60000)
    # SDK-ready and marker DOM do not mean the asynchronous base tiles painted.
    # Wait for actual nonblank WebGL pixels before taking map evidence.
    map_variance = 0
    for _ in range(40):
        map_url = await page.locator('#amap-container canvas').first.evaluate('el => el.toDataURL()')
        map_image = Image.open(io.BytesIO(base64.b64decode(map_url.split(',')[1]))).convert('RGB')
        map_variance = sum(ImageStat.Stat(map_image).var) / 3
        if map_variance > 5:
            break
        await asyncio.sleep(.5)
    info = await page.evaluate(
        """() => {
          const t = document.body.innerText;
          return {
            amap: Boolean(document.querySelector('#amap-container canvas')),
            missing: t.includes('还没有配置可用的地图密钥'),
            textRoute: t.includes('文字路线'),
            canvas: document.querySelectorAll('#amap-container canvas').length,
            markers: document.querySelectorAll('#amap-container .amap-marker').length,
          };
        }"""
    )
    record("amap-live", bool(info.get("amap")) and not info.get("missing") and map_variance > 5, json.dumps(info, ensure_ascii=False))
    await screenshot(page, OUT_DIR / "09-map.png", full_page=True)
    stop = page.locator('.route-stop-list__item').first
    await stop.click()
    record('map-list-selection', await stop.evaluate("el => el.classList.contains('is-current')"), 'real list selects its marker')

    await close_layers(page)
    await page.get_by_role("button", name="问旅行助手").first.click()
    await wait_text(page, "行程智能问答")
    await page.locator("textarea").last.fill("第一天午餐在哪")
    async with page.expect_response(lambda r: '/api/chat/ask' in r.url and r.request.method == 'POST', timeout=150000) as reply_info:
        await page.get_by_role("button", name="发送", exact=True).click()
        await page.get_by_role('button', name='关闭助手').click()
    reply_response = await reply_info.value
    reply = await reply_response.json()
    payload = reply_response.request.post_data_json
    record('chat-request-contract', set(payload) == {'message', 'trip_plan', 'history'} and payload['history'] == [],
           'original payload and first-message history preserved')
    await page.get_by_role('button', name='问旅行助手').first.click()
    try:
        await page.locator('.chat-message.is-assistant.is-success').wait_for(timeout=15000)
        content = await page.locator('.chat-message.is-assistant.is-success .chat-message__body').inner_text()
        record("chat-live", reply_response.status == 200 and reply.get('success') is True and
               bool(reply.get('reply')) and content == reply['reply'], "actual backend reply rendered after in-flight close")
    except Exception as exc:
        record("chat-live", False, str(exc)[:240])
    await screenshot(page, OUT_DIR / "10-chat.png")
    await close_layers(page)
    await page.get_by_role("button", name="问旅行助手").first.click()
    kept = await body_has(page, "第一天午餐在哪")
    record("chat-keep-session", kept, "composer history kept after reopen")
    await close_layers(page)

    await page.get_by_role("button", name="导出攻略").first.click()
    await wait_text(page, "开始导出")
    await page.locator('.export-dialog__option input').check()
    exported_plan = json.loads(await page.evaluate("sessionStorage.getItem('tripPlan')"))
    async with page.expect_download(timeout=120000) as dl_info:
        await page.get_by_role("button", name="开始导出").click()
        try:
            download = await dl_info.value
            dest = OUT_DIR / (download.suggested_filename or "export.png")
            await download.save_as(str(dest))
            size = dest.stat().st_size if dest.exists() else 0
            image = Image.open(dest).convert('RGB')
            variance = sum(ImageStat.Stat(image).var) / 3
            record("export-live", size > 20000 and image.width == 1600 and variance > 100,
                   f"real PNG bytes={size}; size={image.size}; nonblank variance={variance:.1f}")
        except Exception as exc:
            record("export-live", False, str(exc)[:240])
            await screenshot(page, OUT_DIR / "11-export-fail.png")
            return
    await screenshot(page, OUT_DIR / "11-export.png")
    record('export-map-included', await page.locator('.trip-export-map').count() == 1, 'actual map image in export document')
    doc_text = await page.locator('.trip-export-doc').inner_text()
    names = [a['name'] for d in exported_plan['days'] for a in d.get('attractions', [])]
    record('export-content-contract', all(name in doc_text for name in names) and
           str(exported_plan['budget']['total']) in doc_text and '天气' in doc_text and 'TravelAI' in doc_text,
           'all attractions, edited total, weather and footer present in snapshot')


async def amain() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    profile = Path(tempfile.mkdtemp(prefix="travelai-qa92-"))
    print(f"BASE={BASE}", flush=True)
    print(f"OUT_DIR={OUT_DIR}", flush=True)
    print("NOTE: live local API — real model/WS/history; not Google Maps vendor pass", flush=True)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            headless=True,
            channel="chrome",
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
            accept_downloads=True,
        )
        page = context.pages[0] if context.pages else await context.new_page()
        page.set_default_timeout(15000)
        page.on("pageerror", lambda err: PAGE_ERRORS.append(str(err)))
        page.on('websocket', lambda ws: ws.on('framereceived', websocket_frame) if '/api/trip/ws/' in ws.url else None)
        page.on("console", lambda msg: CONSOLE.append(f"{msg.type}: {URL_PATTERN.sub('[URL]', msg.text)}") if len(CONSOLE) < 80 else None)
        page.on(
            "response",
            lambda resp: NETWORK.append(f"{resp.status} {resp.request.method} {resp.url.split('?')[0]}")
            if "/api/" in resp.url and len(NETWORK) < 120
            else None,
        )
        plan_id = os.environ.get("TRAVELAI_QA_PLAN_ID") or None
        try:
            if plan_id:
                await set_viewport(page, 1440, 900)
                await page.goto(f"{BASE}/result?plan_id={plan_id}", wait_until="domcontentloaded")
                await wait_text(page, "远行摘要", timeout=40000)
                ids = await session_ids(page)
                record(
                    "resume-live-plan",
                    ids.get("planQuery") == plan_id and ids.get("hasTrip"),
                    "resumed existing live plan; no extra model call",
                )
            else:
                plan_id = await test_landing_and_generate(page)
            if plan_id:
                for name, fn in [
                    ("result-navigation", lambda: test_result_navigation(page, plan_id)),
                    ("history-open", lambda: test_history_open(page, plan_id)),
                    ("budget-itinerary", lambda: test_budget_and_itinerary(page)),
                    ("map-chat-export", lambda: test_map_chat_export(page)),
                ]:
                    if ONLY and name not in ONLY:
                        continue
                    try:
                        await fn()
                    except Exception as exc:
                        record(f"fatal:{name}", False, f"{exc}\n{traceback.format_exc()}")
                        try:
                            await screenshot(page, OUT_DIR / f"fatal-{name}.png", full_page=True)
                        except Exception:
                            pass
            else:
                record("remaining-live-flows", False, "skipped: generate did not succeed")
        except Exception as exc:
            record("fatal", False, f"{exc}\n{traceback.format_exc()}")
            try:
                await screenshot(page, OUT_DIR / "fatal.png", full_page=True)
            except Exception:
                pass
        await context.close()
        shutil.rmtree(profile, ignore_errors=True)

    summary = {
        "mode": "live-local-backend",
        "google_maps": "not-this-phase",
        "results": RESULTS,
        "page_errors": PAGE_ERRORS,
        "console_sample": CONSOLE[-40:],
        "network_sample": NETWORK,
        "ws_events": WS_EVENTS,
        "out_dir": str(OUT_DIR),
    }
    dump_json(OUT_DIR / REPORT_NAME, summary)
    failed = [r for r in RESULTS if not r["ok"]]
    print(json.dumps({"failed": [{"name": r["name"], "detail": r["detail"][:400]} for r in failed]}, ensure_ascii=False, indent=2), flush=True)
    return 0 if RESULTS and not failed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(amain()))
