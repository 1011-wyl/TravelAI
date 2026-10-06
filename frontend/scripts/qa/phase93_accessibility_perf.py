"""Stage 9.3/9.4: real local API, Chrome AX tree and measured cold-page timings.

No model calls, API mocks, secret dumps, screen-reader claims or Lighthouse scores.
"""
import asyncio
import base64
import io
import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit
from playwright.async_api import async_playwright
from PIL import Image, ImageStat
from qa_helpers import dump_json, layout_audit, wait_text

BASE = os.environ.get('TRAVELAI_QA_BASE', 'http://127.0.0.1:5173')
PLAN = os.environ.get('TRAVELAI_QA_PLAN_ID', 'ba313607')
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'docs/qa/9.3'
PERF_OUT = ROOT / 'docs/qa/9.4'
RESULTS = []
ERRORS = []
PERFORMANCE = []


def record(name, ok, **details):
    RESULTS.append(dict(name=name, ok=bool(ok), **details))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {details}", flush=True)


async def ax_audit(page, name):
    cdp = await page.context.new_cdp_session(page)
    tree = await cdp.send('Accessibility.getFullAXTree')
    controls = []
    for node in tree['nodes']:
        if node.get('ignored'):
            continue
        role = node.get('role', {}).get('value')
        if role in ('button', 'link', 'textbox', 'combobox', 'spinbutton', 'checkbox', 'radio', 'dialog', 'progressbar'):
            control = dict(role=role, name=node.get('name', {}).get('value', ''))
            if not control['name'].strip() and node.get('backendDOMNodeId'):
                described = await cdp.send('DOM.describeNode', {'backendNodeId':node['backendDOMNodeId']})
                attrs = described['node'].get('attributes', [])
                control['element'] = described['node']['nodeName']
                control['attributes'] = {attrs[i]:attrs[i+1] for i in range(0,len(attrs),2)
                                         if attrs[i] in ('id','class','type','placeholder','role','aria-label','aria-labelledby')}
            controls.append(control)
    missing = [row for row in controls if not row['name'].strip()]
    record(name + '-ax-control-names', not missing, missing=missing, controls=len(controls))
    headings = await page.locator('h1,h2,h3,h4,h5,h6').evaluate_all("""els => els.filter(e=>e.getClientRects().length && getComputedStyle(e).visibility!=='hidden')
      .map(e=>({level:Number(e.tagName[1]),text:e.innerText}))""")
    skips = [headings[i] for i in range(1, len(headings)) if headings[i]['level'] > headings[i-1]['level'] + 1]
    record(name + '-heading-order', not skips, skips=skips)
    record(name + '-main-landmark', await page.locator('main#main-content').count() == 1)
    dump_json(OUT / (name + '-semantics.json'), dict(controls=controls, headings=headings))
    await cdp.detach()


async def goto_result(page, section='overview'):
    await page.goto(f'{BASE}/result?plan_id={PLAN}&section={section}', wait_until='domcontentloaded')
    await wait_text(page, '远行摘要', timeout=30000)


OBSERVER = """(() => {
  window.__qaVitals = {lcp:0,cls:0,longTasks:[]};
  for (const type of ['largest-contentful-paint','layout-shift','longtask']) {
    new PerformanceObserver(list => { for(const e of list.getEntries()) {
      if(type==='largest-contentful-paint') window.__qaVitals.lcp=e.startTime;
      if(type==='layout-shift'&&!e.hadRecentInput) window.__qaVitals.cls+=e.value;
      if(type==='longtask') window.__qaVitals.longTasks.push(e.duration);
    }}).observe({type,buffered:true});
  }
})();"""


async def measure(browser, width, path, name):
    ctx = await browser.new_context(viewport={'width': width, 'height': 900}, locale='zh-CN')
    page = await ctx.new_page()
    await page.add_init_script(OBSERVER)
    await page.goto(BASE + path, wait_until='domcontentloaded')
    await wait_text(page, '远行摘要' if 'result?' in path else '远方，不必从空白开始', timeout=30000)
    await asyncio.sleep(3)
    data = await page.evaluate("""() => {
      const n=performance.getEntriesByType('navigation')[0], p=performance.getEntriesByType('paint');
      const assets=performance.getEntriesByType('resource').filter(e=>e.initiatorType==='script'||e.initiatorType==='link');
      return {viewport:innerWidth,ttfb:n.responseStart,fcp:p.find(e=>e.name==='first-contentful-paint')?.startTime,
        ...window.__qaVitals,assets:assets.map(e=>({path:new URL(e.name).pathname,bytes:e.transferSize})),
        build:'Vite production preview; real local API; no CPU/network throttling; isolated cold context'};
    }""")
    data['case'] = name
    PERFORMANCE.append(data)
    await page.screenshot(path=str(PERF_OUT / (name + '.png')))
    print(f"[MEASURE] {name}: FCP={data['fcp']:.0f}ms LCP={data['lcp']:.0f}ms CLS={data['cls']:.4f}", flush=True)
    await ctx.close()


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PERF_OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel='chrome', headless=True)
        if os.environ.get('TRAVELAI_QA_PERF_ONLY') == '1':
            for run in range(1, 4):
                for width in [375,1440]:
                    await measure(browser,width,'/',f'home-{width}-run{run}')
                    await measure(browser,width,f'/result?plan_id={PLAN}&section=overview',f'result-{width}-run{run}')
            dump_json(PERF_OUT / 'browser-performance.json', dict(mode='measured-browser-not-Lighthouse', cases=PERFORMANCE))
            await browser.close()
            return 0
        ctx = await browser.new_context(viewport={'width':1440, 'height':900}, locale='zh-CN')
        page = await ctx.new_page()
        page.on('pageerror', lambda err: ERRORS.append(str(err)))
        requests = []
        page.on('request', lambda req: requests.append(urlsplit(req.url).path))
        await page.goto(BASE, wait_until='domcontentloaded')
        await wait_text(page, '远方，不必从空白开始')
        record('home-heavy-libraries-deferred', not any(re.search(r'/(echarts|maps|html2canvas)-', u) for u in requests))
        await ax_audit(page, 'home')
        await page.get_by_role('button', name='开始规划旅程').click()
        await page.locator('.ant-form-item-explain-error').first.wait_for()
        focused_invalid = await page.evaluate("() => Boolean(document.activeElement?.closest('.ant-form-item-has-error'))")
        record('invalid-submit-focus-first-field', focused_invalid)
        await goto_result(page)
        await ax_audit(page, 'overview')
        record('initial-heavy-libraries-deferred', not any(re.search(r'/(echarts|maps|html2canvas)-', u) for u in requests))
        nav = page.get_by_role('navigation', name='结果分区')
        for section, label in [('budget','预算明细'),('itinerary','每日行程'),('weather','天气信息')]:
            await nav.get_by_role('button', name=label).click()
            await ax_audit(page, section)
        await nav.get_by_role('button', name='灵感图谱').click()
        await page.locator('.graph-canvas__host canvas').wait_for(timeout=30000)
        record('echarts-only-after-graph', any('/echarts-' in u for u in requests))
        await page.get_by_role('radio', name='列表', exact=True).check()
        await ax_audit(page, 'graph-list')
        await page.get_by_role('button', name='问旅行助手').first.click()
        await page.locator('#chat-composer-input').wait_for()
        await ax_audit(page, 'chat')
        await page.get_by_role('button', name='关闭助手').click()
        await page.get_by_role('button', name='打开配置').click()
        await page.locator('.settings-drawer__body input').first.wait_for()
        await ax_audit(page, 'settings')
        await page.get_by_role('button', name='关闭配置').click()
        await nav.get_by_role('button', name='景点地图').click()
        await page.locator('#amap-container canvas').first.wait_for(timeout=60000)
        variance = 0
        for _ in range(30):
            data_url = await page.locator('#amap-container canvas').first.evaluate('el => el.toDataURL()')
            map_image = Image.open(io.BytesIO(base64.b64decode(data_url.split(',')[1]))).convert('RGB')
            variance = sum(ImageStat.Stat(map_image).var) / 3
            if variance > 5:
                break
            await asyncio.sleep(.5)
        record('real-map-canvas-pixels-nonblank', variance > 5, variance=variance)
        await page.locator('#amap-container').screenshot(path=str(OUT / 'real-map-pixels.png'))
        record('maps-only-after-map', any('/maps-' in u for u in requests))
        # Do not include vendor-generated controls in the app's AX audit.
        record('map-list-keyboard-alternative', await page.locator('.route-stop-list__item').count() > 0)
        await nav.get_by_role('button', name='行程概览').click()
        await page.get_by_role('button', name='导出攻略').first.click()
        await page.get_by_role('button', name='开始导出').wait_for()
        record('html2canvas-before-confirm-not-requested', not any('/html2canvas-' in u for u in requests))
        async with page.expect_download(timeout=120000):
            await page.get_by_role('button', name='开始导出').click()
        record('html2canvas-after-confirm-requested', any('/html2canvas-' in u for u in requests))
        await page.get_by_role('button', name='完成', exact=True).click()
        await ctx.close()

        for width, height in [(375,812),(812,375)]:
            ctx = await browser.new_context(viewport={'width':width,'height':height}, is_mobile=True, has_touch=True, locale='zh-CN')
            page = await ctx.new_page()
            chat_requests = []
            async def block_chat(route):
                chat_requests.append('attempted-chat-post')
                await route.abort()
            await page.route('**/api/chat/ask', block_chat)
            await goto_result(page)
            await page.get_by_role('button', name='问旅行助手').first.click()
            field = page.locator('#chat-composer-input')
            await field.fill('组合输入测试')
            await field.dispatch_event('compositionstart')
            await field.press('Enter')
            record(f'mobile-ime-no-send-{width}', await page.locator('.chat-message.is-user').count() == 0)
            await field.dispatch_event('compositionend', {'data':'组合输入测试'})
            await field.press('Enter')
            record(f'mobile-enter-newline-{width}', '\n' in await field.input_value() and not chat_requests)
            font = await field.evaluate('e=>parseFloat(getComputedStyle(e).fontSize)')
            record(f'mobile-input-no-ios-autozoom-{width}', font >= 16, font_size=font)
            hidden = await page.locator('label[for="chat-composer-input"]').evaluate("""e => {
              const r=e.getBoundingClientRect(),s=getComputedStyle(e);
              return s.position==='absolute'&&r.width<=1&&r.height<=1;
            }""")
            record(f'mobile-chat-label-visually-hidden-{width}', hidden)
            audit = await layout_audit(page)
            record(f'mobile-sheet-layout-{width}', audit['pageOverflowX'] == 0, audit=audit)
            await page.screenshot(path=str(OUT / f'mobile-chat-{width}.png'))
            await ctx.close()
        for width in [375,1440]:
            await measure(browser,width,'/',f'home-{width}')
            await measure(browser,width,f'/result?plan_id={PLAN}&section=overview',f'result-{width}')
        await browser.close()
    dump_json(OUT / 'report.json', dict(mode='real-API-Chrome-AX-and-DOM-not-human-screen-reader; keyboard-only chat POST blocked', results=RESULTS,
      page_errors=ERRORS, human_screen_reader='pending', physical_phone='pending'))
    dump_json(PERF_OUT / 'browser-performance.json', dict(mode='measured-browser-not-Lighthouse', cases=PERFORMANCE))
    return 0 if not ERRORS and all(r['ok'] for r in RESULTS) else 1


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
