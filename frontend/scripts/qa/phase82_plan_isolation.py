"""
Phase 8.2 plan-isolation browser regression (isolated mock responses).

Uses Playwright async API + Chrome channel. Does NOT hit a real backend.
Not a production test entry — run manually / from QA scripts only.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

from playwright.async_api import async_playwright

from fixtures_plan_ab import GRAPH_A, GRAPH_B, PLAN_A, PLAN_B, status_payload

BASE = os.environ.get("TRAVELAI_QA_BASE", "http://127.0.0.1:4173")
OUT_DIR = Path(os.environ.get("TRAVELAI_QA_OUT", tempfile.gettempdir())) / "travelai-qa-8.2"
API_HOST = "http://localhost:8000"

RESULTS: list[dict] = []
CONSOLE: list[str] = []
PAGE_ERRORS: list[str] = []


def record(name: str, ok: bool, detail: str) -> None:
    RESULTS.append({"name": name, "ok": ok, "detail": detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


async def spa_goto(page, path_query: str) -> None:
    """Prefer same-document navigation so Result instance is reused."""
    await page.evaluate(
        """(url) => {
          const next = new URL(url, location.origin);
          // history.state may carry vue-router markers; popstate is enough for HTML5 history.
          history.pushState(history.state, '', next.pathname + next.search + next.hash);
          window.dispatchEvent(new PopStateEvent('popstate', { state: history.state }));
        }""",
        path_query,
    )
    # Fallback: if router ignored synthetic popstate, hard-navigate.
    ok = await page.evaluate(
        """(url) => {
          const next = new URL(url, location.origin);
          return location.pathname === next.pathname && location.search === next.search;
        }""",
        path_query,
    )
    if not ok:
        await page.goto(f"{BASE}{path_query}", wait_until="commit")


async def seed_session(page, plan: dict, graph: dict, plan_id: str | None) -> None:
    await page.evaluate(
        """({ plan, graph, planId }) => {
          sessionStorage.setItem('tripPlan', JSON.stringify(plan));
          sessionStorage.setItem('graphData', JSON.stringify(graph));
          if (planId) sessionStorage.setItem('planId', planId);
          else sessionStorage.removeItem('planId');
        }""",
        {"plan": plan, "graph": graph, "planId": plan_id},
    )


async def wait_ready_marker(page, marker: str, timeout: float = 20000) -> None:
    await page.wait_for_function(
        """(m) => document.body && document.body.innerText.includes('UNIQUE-' + m + '-ATTR')""",
        arg=marker,
        timeout=timeout,
    )


async def body_has(page, text: str) -> bool:
    return bool(await page.evaluate("(t) => document.body.innerText.includes(t)", text))


def marker_for_plan_id(plan_id: str) -> str:
    pid = plan_id.lower()
    if "plan-a" in pid or pid.endswith("-a") or pid == "a":
        return "A"
    if "plan-b" in pid or pid.endswith("-b") or pid == "b":
        return "B"
    if "probe" in pid:
        return "B"
    return "B"


async def install_routes(page, state: dict) -> None:
    async def on_api(route):
        url = route.request.url
        if "/api/trip/status/" in url:
            plan_id = url.rstrip("/").split("/")[-1]
            state["status_calls"] = state.get("status_calls", 0) + 1
            state.setdefault("status_ids", []).append(plan_id)
            delay = float(state.get("delay", {}).get(plan_id, 0))
            if delay:
                await asyncio.sleep(delay)
            gate = state.get("gate", {}).get(plan_id)
            if gate is not None:
                for _ in range(400):
                    if gate["release"]:
                        break
                    await asyncio.sleep(0.05)
            marker = marker_for_plan_id(plan_id)
            payload = status_payload(plan_id, marker)
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(payload, ensure_ascii=False),
            )
            return

        if "/api/chat/ask" in url:
            state["chat_calls"] = state.get("chat_calls", 0) + 1
            delay = float(state.get("chat_delay", 0))
            if delay:
                await asyncio.sleep(delay)
            body = route.request.post_data or "{}"
            try:
                msg = json.loads(body).get("message", "")
            except Exception:
                msg = ""
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"success": True, "reply": f"MOCK-CHAT-REPLY::{msg}"}, ensure_ascii=False),
            )
            return

        if "/api/poi/photo" in url:
            state["photo_calls"] = state.get("photo_calls", 0) + 1
            delay = float(state.get("photo_delay", 0))
            if delay:
                await asyncio.sleep(delay)
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"success": True, "data": {"photo_url": "https://example.com/p.jpg"}}),
            )
            return

        if "/api/poi/image" in url:
            await route.fulfill(status=200, content_type="image/png", body=b"")
            return

        if "/api/settings" in url:
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"success": True, "data": {}}),
            )
            return

        if "/api/trip/history" in url:
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"items": []}),
            )
            return

        await route.fulfill(status=404, body='{"detail":"mock unused"}')

    await page.route(f"{API_HOST}/api/**", on_api)
    await page.route("**/api/**", on_api)


def attach_logging(page) -> None:
    page.on("console", lambda msg: CONSOLE.append(f"{msg.type}: {msg.text}"))
    page.on("pageerror", lambda err: PAGE_ERRORS.append(str(err)))


async def test_same_instance_switch(page, state: dict) -> None:
    state["status_calls"] = 0
    await page.goto(f"{BASE}/result?plan_id=plan-a", wait_until="networkidle")
    await wait_ready_marker(page, "A")
    record("1a-open-A", await body_has(page, "UNIQUE-A-ATTR"), "A marker visible")

    await spa_goto(page, "/result?plan_id=plan-b")
    await wait_ready_marker(page, "B")
    ok = (await body_has(page, "UNIQUE-B-ATTR")) and not (await body_has(page, "UNIQUE-A-ATTR"))
    session_id = await page.evaluate("() => sessionStorage.getItem('planId')")
    record(
        "1-same-instance-switch",
        ok and session_id == "plan-b",
        f"B visible, A gone, session planId={session_id}",
    )
    await page.screenshot(path=str(OUT_DIR / "01-switch-b.png"), full_page=True)


async def test_restore_race(page, state: dict) -> None:
    # Delay A so B can finish first; no sync gate (keeps Playwright event loop free).
    state["delay"] = {"plan-a": 3.0, "plan-b": 0.0}
    state["gate"] = {}
    await page.goto(f"{BASE}/", wait_until="domcontentloaded")
    await page.evaluate("() => { sessionStorage.clear(); }")

    # Wait until hydration actually starts; 150ms after document commit can run
    # before Vue Router boots on a busy machine and would not test a real race.
    async with page.expect_request('**/api/trip/status/plan-a') as started:
        await page.goto(f"{BASE}/result?plan_id=plan-a", wait_until="domcontentloaded")
    await started.value
    await spa_goto(page, "/result?plan_id=plan-b")
    await wait_ready_marker(page, "B", timeout=20000)
    # Wait out A's delayed response; it must not overwrite B.
    await asyncio.sleep(3.5)
    ok = (await body_has(page, "UNIQUE-B-ATTR")) and not (await body_has(page, "UNIQUE-A-ATTR"))
    session_id = await page.evaluate("() => sessionStorage.getItem('planId')")
    session_plan = await page.evaluate("() => sessionStorage.getItem('tripPlan') || ''")
    ok = (
        ok
        and session_id == "plan-b"
        and "UNIQUE-B-ATTR" in session_plan
        and "UNIQUE-A-ATTR" not in session_plan
    )
    record("2-restore-race", ok, f"final session planId={session_id}; A late discarded")
    await page.screenshot(path=str(OUT_DIR / "02-race-b.png"), full_page=True)
    state["delay"] = {}


async def test_section_no_rehydrate(page, state: dict) -> None:
    await page.goto(f"{BASE}/result?plan_id=plan-b", wait_until="networkidle")
    await wait_ready_marker(page, "B")
    before = state.get("status_calls", 0)
    await spa_goto(page, "/result?plan_id=plan-b&section=budget")
    await page.wait_for_function("() => location.search.includes('section=budget')", timeout=8000)
    await asyncio.sleep(0.35)
    await spa_goto(page, "/result?plan_id=plan-b&section=overview")
    await asyncio.sleep(0.25)
    await page.go_back()
    await asyncio.sleep(0.25)
    await page.go_forward()
    await asyncio.sleep(0.35)
    after = state.get("status_calls", 0)
    still_b = await body_has(page, "UNIQUE-B-ATTR")
    record(
        "3-section-no-rehydrate",
        still_b and after == before,
        f"status_calls before={before} after={after}; still B={still_b}",
    )


async def test_edit_isolation(page, state: dict) -> None:
    await page.goto(f"{BASE}/result?plan_id=plan-a", wait_until="networkidle")
    await wait_ready_marker(page, "A")
    await spa_goto(page, "/result?plan_id=plan-a&section=itinerary")
    await asyncio.sleep(0.4)
    await page.get_by_role("button", name="编辑行程").click()
    await page.get_by_role("button", name="保存修改").wait_for(timeout=5000)
    inputs = page.locator("textarea, input[type='text']")
    if await inputs.count() > 0:
        await inputs.first.fill("DRAFT-FROM-A-SHOULD-NOT-LEAK")
    await spa_goto(page, "/result?plan_id=plan-b")
    await wait_ready_marker(page, "B")
    has_save = await page.get_by_role("button", name="保存修改").count() > 0
    has_edit = await page.get_by_role("button", name="编辑行程").count() > 0
    leaked = await body_has(page, "DRAFT-FROM-A-SHOULD-NOT-LEAK")
    ok = (not has_save) and has_edit and (not leaked) and (await body_has(page, "UNIQUE-B-ATTR"))
    record("4-edit-isolation", ok, f"editMode exited={not has_save}; draft leaked={leaked}")

    await spa_goto(page, "/result?plan_id=plan-b&section=itinerary")
    await asyncio.sleep(0.3)
    await page.get_by_role("button", name="编辑行程").click()
    await page.get_by_role("button", name="取消编辑").click()
    await page.get_by_role("button", name="编辑行程").wait_for(timeout=5000)
    await page.get_by_role("button", name="编辑行程").click()
    await page.get_by_role("button", name="保存修改").click()
    await page.get_by_role("button", name="编辑行程").wait_for(timeout=5000)
    record("4b-edit-on-B", await body_has(page, "UNIQUE-B-ATTR"), "B edit cancel/save ok")
    await page.screenshot(path=str(OUT_DIR / "04-edit-b.png"), full_page=True)


async def test_same_city_no_plan_id(page, state: dict) -> None:
    await page.goto(f"{BASE}/", wait_until="domcontentloaded")
    await page.evaluate("() => { sessionStorage.clear(); }")
    await seed_session(page, PLAN_A, GRAPH_A, None)
    await page.goto(f"{BASE}/result", wait_until="networkidle")
    await wait_ready_marker(page, "A")

    ask = page.get_by_role("button", name="问旅行助手")
    if await ask.count() > 0:
        await ask.first.click()
        await asyncio.sleep(0.3)
        composer = page.locator("textarea").last
        if await composer.count():
            await composer.fill("关于A的问题")
            await page.keyboard.press("Enter")
            await page.wait_for_function(
                """() => document.body.innerText.includes('MOCK-CHAT-REPLY')""",
                timeout=10000,
            )

    await seed_session(page, PLAN_B, GRAPH_B, None)
    await spa_goto(page, "/result?plan_id=probe-for-b")
    await wait_ready_marker(page, "B")
    chat_polluted = (await body_has(page, "MOCK-CHAT-REPLY")) or (await body_has(page, "关于A的问题"))
    ok = (
        (await body_has(page, "UNIQUE-B-ATTR"))
        and not (await body_has(page, "UNIQUE-A-ATTR"))
        and not chat_polluted
    )
    record(
        "5-same-city-no-planId-isolation",
        ok,
        f"B adopted; chat polluted={chat_polluted}; mock session + spa hydrate",
    )
    await page.screenshot(path=str(OUT_DIR / "05-no-id-b.png"), full_page=True)


async def test_inflight_tasks(page, state: dict) -> None:
    downloads: list[str] = []
    page.on("download", lambda d: downloads.append(d.suggested_filename))

    await page.goto(f"{BASE}/result?plan_id=plan-a", wait_until="networkidle")
    await wait_ready_marker(page, "A")
    state["chat_delay"] = 2.5
    ask = page.get_by_role("button", name="问旅行助手")
    if await ask.count() > 0:
        await ask.first.click()
        await asyncio.sleep(0.2)
        box = page.locator("textarea").last
        await box.fill("慢回复A")
        await page.keyboard.press("Enter")
        await asyncio.sleep(0.2)
    await spa_goto(page, "/result?plan_id=plan-b")
    await wait_ready_marker(page, "B")
    await asyncio.sleep(3.0)
    chat_ok = not (await body_has(page, "MOCK-CHAT-REPLY::慢回复A")) and not (
        await body_has(page, "慢回复A")
    )
    record("6a-inflight-chat", chat_ok, "late A chat did not pollute B")

    state["photo_delay"] = 2.0
    state["chat_delay"] = 0
    await page.goto(f"{BASE}/result?plan_id=plan-a", wait_until="networkidle")
    await wait_ready_marker(page, "A")
    await asyncio.sleep(0.25)
    await spa_goto(page, "/result?plan_id=plan-b")
    await wait_ready_marker(page, "B")
    await asyncio.sleep(2.5)
    photo_ok = (await body_has(page, "UNIQUE-B-ATTR")) and not (await body_has(page, "UNIQUE-A-ATTR"))
    record("6b-inflight-photos", photo_ok, "late A photos did not keep A content")
    state["photo_delay"] = 0

    await page.goto(f"{BASE}/result?plan_id=plan-a", wait_until="networkidle")
    await wait_ready_marker(page, "A")
    export_btn = page.get_by_role("button", name="导出攻略")
    await export_btn.first.click()
    await asyncio.sleep(0.4)
    confirm = page.get_by_role("button", name="开始导出")
    if await confirm.count() > 0:
        await confirm.last.click()
    await asyncio.sleep(0.2)
    await spa_goto(page, "/result?plan_id=plan-b")
    await wait_ready_marker(page, "B")
    await asyncio.sleep(2.5)
    record("6c-export-invalidated", len(downloads) == 0, f"downloads after switch={downloads}")
    await page.screenshot(path=str(OUT_DIR / "06-inflight.png"), full_page=True)


async def amain() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    profile = Path(tempfile.mkdtemp(prefix="travelai-qa-profile-"))
    print(f"BASE={BASE}")
    print(f"OUT_DIR={OUT_DIR}")
    print(f"PROFILE={profile}")
    print("NOTE: isolated mock API responses — not real backend acceptance")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            headless=True,
            channel="chrome",
            accept_downloads=True,
            viewport={"width": 1280, "height": 900},
        )
        page = context.pages[0] if context.pages else await context.new_page()
        attach_logging(page)
        state: dict = {"delay": {}, "gate": {}}
        await install_routes(page, state)

        tests = [
            ("same-instance-switch", test_same_instance_switch),
            ("restore-race", test_restore_race),
            ("section-no-rehydrate", test_section_no_rehydrate),
            ("edit-isolation", test_edit_isolation),
            ("same-city-no-planId", test_same_city_no_plan_id),
            ("inflight-tasks", test_inflight_tasks),
        ]
        for name, fn in tests:
            try:
                state["delay"] = {}
                state["gate"] = {}
                state["chat_delay"] = 0
                state["photo_delay"] = 0
                await fn(page, state)
            except Exception as exc:
                record(f"fatal:{name}", False, f"{exc}\n{traceback.format_exc()}")
                try:
                    await page.screenshot(path=str(OUT_DIR / f"fatal-{name}.png"), full_page=True)
                except Exception:
                    pass
        await context.close()
        shutil.rmtree(profile, ignore_errors=True)

    app_errors = [e for e in PAGE_ERRORS if "mock" not in e.lower()]
    summary = {
        "results": RESULTS,
        "page_errors": PAGE_ERRORS,
        "console_sample": CONSOLE[-50:],
        "app_page_errors": app_errors,
        "mode": "isolated-mock-api",
        "out_dir": str(OUT_DIR),
    }
    (OUT_DIR / "report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"failed": [r for r in RESULTS if not r["ok"]], "page_errors": PAGE_ERRORS}, ensure_ascii=False, indent=2))
    return 0 if RESULTS and all(r["ok"] for r in RESULTS) and not app_errors else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(amain()))
