"""Isolated settings secret-peek check. Does not print stored keys."""
from pathlib import Path

from playwright.sync_api import sync_playwright

DUMMY_JS = "JsKeyTestValueABCDEF123456"
MASK = "\u2022"
EXPECTED_JS_PEEK = f"{DUMMY_JS[:4]}{MASK * 8}{DUMMY_JS[-4:]}"
WEB_MASKED = f"c45f{MASK * 8}cbd9"
OUT = Path(__file__).resolve().parents[3] / "docs" / "qa" / "settings-mask"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        page.route(
            "**/api/settings",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=(
                    '{"success":true,"data":{"vite_amap_web_key":"%s",'
                    '"vite_amap_web_js_key":"","google_maps_api_key":"",'
                    '"google_maps_proxy":"","xhs_cookie":"",'
                    '"openai_api_key":"","openai_base_url":"",'
                    '"openai_model":""}}' % WEB_MASKED
                ),
            ),
        )
        page.add_init_script(
            """() => {
              localStorage.setItem('travelai.runtime.amap_web_js_key', %r);
              localStorage.setItem('travelai.runtime.api_base_url', 'http://127.0.0.1:8000');
            }"""
            % DUMMY_JS
        )
        page.goto("http://127.0.0.1:5173/", wait_until="networkidle", timeout=60000)
        page.get_by_role("button", name="打开配置").click()
        page.locator(".settings-drawer").wait_for()
        page.locator(".runtime-settings-form").wait_for()

        load_error = page.locator(".settings-drawer").inner_text()
        has_load_failed = "读取" in load_error or "失败" in load_error

        js_wrap = page.locator(".secret-peek-input").nth(0)
        js_input = js_wrap.locator("input")
        hidden_len = len(js_input.input_value())
        hidden_type = js_input.get_attribute("type")
        js_wrap.locator(".secret-peek-input__toggle").click()
        js_input = page.locator(".secret-peek-input").nth(0).locator("input")
        js_value = js_input.input_value()
        js_type = js_input.get_attribute("type")
        page.screenshot(path=str(OUT / "js-key-peek.png"))

        stored_len = page.evaluate(
            "() => (localStorage.getItem('travelai.runtime.amap_web_js_key') || '').length"
        )
        flags = {
            "has_load_failed": has_load_failed,
            "stored_len": stored_len,
            "hidden_type": hidden_type,
            "hidden_len": hidden_len,
            "revealed_type": js_type,
            "revealed_len": len(js_value),
            "has_mask": MASK in js_value,
            "equals_dummy": js_value == DUMMY_JS,
            "empty": js_value == "",
        }
        peek_ok = (
            flags["revealed_type"] == "text"
            and flags["has_mask"]
            and flags["revealed_len"] == 16
            and not flags["equals_dummy"]
            and not flags["empty"]
            and flags["hidden_type"] == "password"
        )
        web_wrap = page.locator(".secret-peek-input").nth(1)
        web_wrap.locator(".secret-peek-input__toggle").click()
        web_input = page.locator(".secret-peek-input").nth(1).locator("input")
        web_value = web_input.input_value()
        flags["web_has_mask"] = MASK in web_value
        flags["web_len"] = len(web_value)
        flags["web_type"] = web_input.get_attribute("type")
        page.screenshot(path=str(OUT / "web-key-peek.png"))
        peek_ok = peek_ok and flags["web_has_mask"] and flags["web_type"] == "text"
        if peek_ok:
            print("ok", flags)
        else:
            print("fail", flags)
            raise SystemExit(1)
        context.close()
        browser.close()


if __name__ == "__main__":
    main()
