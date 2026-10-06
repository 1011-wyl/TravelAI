"""Extra a11y, real browser zoom, graph failure/lazy/static checks (isolated API)."""
import asyncio
import json
import math
import re
import tempfile
from pathlib import Path
from playwright.async_api import async_playwright
from phase83_visual_a11y import install_mocks as install_api_mocks, open_result, open_landing, click_segment
from qa_helpers import dump_json, layout_audit, wait_text

OUT=Path(__file__).resolve().parents[3]/'docs/qa/8.3'
RESULTS=[]
ERRORS=[]

async def install_mocks(page,state):
    page.on('pageerror',lambda err:ERRORS.append(str(err)))
    await install_api_mocks(page,state)

def record(name,ok,**details):
    RESULTS.append(dict(name=name,ok=bool(ok),**details))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {details}",flush=True)

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(channel='chrome',headless=True)
        context=await browser.new_context(viewport={'width':375,'height':812},locale='zh-CN')
        page=await context.new_page()
        await install_mocks(page,{})
        requests=[]
        page.on('request',lambda r:requests.append(r.url))
        await open_result(page,375,'graph')
        await wait_text(page,'孤立茶亭')
        record('mobile-graph-no-echarts',not any('/echarts-' in u for u in requests))
        await page.emulate_media(reduced_motion='reduce')
        await click_segment(page,'图谱')
        await page.locator('.graph-canvas__host canvas').wait_for(timeout=20000)
        # Use the real imported ECharts instance to inspect the actual production option.
        module=next(u for u in requests if '/echarts-' in u)
        option=await page.evaluate("""async u=>{
          const m=await import(u), ec=m.getInstanceByDom(document.querySelector('.graph-canvas__host'));
          const s=ec.getOption().series[0];
          return {layout:s.layout,force:!!s.force,animation:s.animation,xy:s.data.map(n=>[n.x,n.y])};
        }""",module)
        await asyncio.sleep(.6)
        option2=await page.evaluate("""async u=>{const m=await import(u);return m.getInstanceByDom(document.querySelector('.graph-canvas__host')).getOption().series[0].data.map(n=>[n.x,n.y])}""",module)
        record('reduced-graph-actual-static',option['layout']=='none' and not option['force'] and option['xy']==option2,option=option)
        await context.close()
        context=await browser.new_context(viewport={'width':1440,'height':900},locale='zh-CN')
        page=await context.new_page(); await install_mocks(page,{})
        await page.route('**/echarts-*.js',lambda route:route.abort())
        await open_result(page,1440,'graph')
        await wait_text(page,'画布',timeout=20000)
        await page.get_by_role('button',name='使用列表').wait_for(timeout=20000)
        await page.get_by_role('button',name='使用列表').click()
        await wait_text(page,'孤立茶亭')
        record('echarts-load-failure-list-recovery',await page.locator('.graph-canvas__host').count()==0)
        await context.close()
        context=await browser.new_context(viewport={'width':1440,'height':900},locale='zh-CN')
        page=await context.new_page(); await install_mocks(page,{})
        await open_result(page,1440,'overview')
        await page.get_by_role('navigation',name='结果分区').get_by_role('button',name='预算明细').click()
        before=await page.evaluate("sessionStorage.getItem('tripPlan')")
        await page.get_by_role('button',name='编辑',exact=True).first.click()
        amount=page.locator('.budget-item-form .ant-input-number-input')
        await amount.fill('1234')
        await page.get_by_role('dialog').get_by_role('button',name=re.compile(r'取\s*消')).click()
        await page.locator('.budget-item-form').wait_for(state='hidden')
        record('budget-edit-cancel-no-mutation',before==await page.evaluate("sessionStorage.getItem('tripPlan')"))
        await page.get_by_role('button',name='编辑',exact=True).first.click()
        value=float(await amount.input_value())
        await amount.fill(str(value+100))
        await page.get_by_role('dialog').get_by_role('button',name=re.compile(r'保\s*存'),exact=True).click()
        await page.locator('.budget-item-form').wait_for(state='hidden')
        updated=json.loads(await page.evaluate("sessionStorage.getItem('tripPlan')"))['budget']
        old=json.loads(before)['budget']
        record('budget-edit-save-local-calculation',updated['total_hotels']==old['total_hotels']+100 and updated['total']==sum(updated[key] for key in ('total_attractions','total_hotels','total_meals','total_transportation')),budget=updated)
        await page.get_by_role('navigation',name='结果分区').get_by_role('button',name='行程概览').click()
        await page.get_by_role('button',name='问旅行助手').first.click()
        await page.locator('#chat-composer-input').wait_for()
        await asyncio.sleep(.4)
        escaped=[]
        for _ in range(16):
            await page.keyboard.press('Tab')
            inside=await page.evaluate("()=>!!document.activeElement.closest('.ant-drawer-content-wrapper')")
            if not inside: escaped.append(await page.evaluate('()=>document.activeElement.outerHTML.slice(0,160)'))
        record('chat-tab-focus-trap',not escaped,escaped=escaped)
        field=page.locator('#chat-composer-input')
        await field.fill('拼音组合')
        await field.dispatch_event('compositionstart')
        await field.press('Enter')
        record('chat-ime-no-premature-send',await page.locator('.chat-message.is-user').count()==0)
        await field.dispatch_event('compositionend',{'data':'拼音组合'})
        await field.press('Shift+Enter')
        record('chat-shift-enter-newline','\n' in await field.input_value())
        await field.press('Enter');await wait_text(page,'MOCK-CHAT-OK')
        record('chat-enter-one-send',await page.locator('.chat-message.is-user').count()==1)
        await page.keyboard.press('Escape'); await page.get_by_role('button',name='关闭助手').wait_for(state='hidden')
        trigger=await page.evaluate("()=>document.activeElement?.getAttribute('aria-controls')")
        record('chat-esc-return-trigger',trigger=='result-ai-chat-panel',active=trigger)
        await page.get_by_role('button',name='打开配置').click()
        await wait_text(page,'后端地址')
        await asyncio.sleep(.4)
        escaped=[]
        for _ in range(48):
            await page.keyboard.press('Tab')
            if not await page.evaluate("()=>!!document.activeElement.closest('.settings-drawer-root')"):escaped.append('outside')
        record('settings-tab-focus-trap',not escaped)
        named=await page.locator('.settings-drawer-root [role=dialog]').get_attribute('aria-labelledby')
        record('settings-named-dialog',named=='settings-drawer-title')
        await page.keyboard.press('Escape');await page.get_by_role('button',name='关闭配置').wait_for(state='hidden')
        await open_landing(page,375)
        await page.get_by_role('button',name='打开导航菜单').click()
        await page.get_by_role('button',name='关闭导航菜单').wait_for()
        await asyncio.sleep(.4)
        escaped=[]
        for _ in range(16):
            await page.keyboard.press('Tab')
            if not await page.evaluate("()=>!!document.activeElement.closest('.mobile-nav-drawer-root')"):escaped.append('outside')
        record('mobile-nav-tab-focus-trap',not escaped)
        await page.get_by_role('button',name='打开配置').last.click()
        await page.get_by_role('button',name='关闭配置').wait_for()
        await asyncio.sleep(.4)
        await page.keyboard.press('Escape');await page.get_by_role('button',name='关闭配置').wait_for(state='hidden')
        await asyncio.sleep(.4)
        record('mobile-settings-focus-return',await page.get_by_role('button',name='打开导航菜单').evaluate('e=>e===document.activeElement'),active=await page.evaluate('()=>document.activeElement.outerHTML.slice(0,180)'))
        for locale in ('en','ja'):
            await page.evaluate("v=>localStorage.setItem('travelai-locale',v)",locale)
            await page.reload();await page.locator('.trip-planner').wait_for()
            audit=await layout_audit(page)
            record(f'{locale}-mobile-home',not audit['overflowing'] and audit['pageOverflowX']==0)
            await page.screenshot(path=str(OUT/f'{locale}-mobile-home.png'),full_page=True)
        await context.close(); await browser.close()
        # Set Chrome's native profile zoom preference; NOT CSS zoom or DPR emulation.
        # A temporary browser profile is owned only by this test.
        with tempfile.TemporaryDirectory(prefix='travelai-native-zoom-') as profile:
            default=Path(profile)/'Default';default.mkdir()
            (default/'Preferences').write_text(json.dumps({'partition':{'default_zoom_level':{'x':math.log(2)/math.log(1.2)}}}))
            context=await p.chromium.launch_persistent_context(profile,channel='chrome',headless=True,no_viewport=True,args=['--window-size=1440,1000'],locale='zh-CN')
            page=context.pages[0];await install_mocks(page,{})
            # Do not call set_viewport_size here: it would overwrite native zoom layout.
            from phase83_visual_a11y import BASE
            await page.goto(BASE);await wait_text(page,'远方，不必从空白开始')
            dims=await page.evaluate('()=>({width:innerWidth,outer:outerWidth,dpr:devicePixelRatio,screen:screen.width})')
            record('native-chrome-200-percent',dims['dpr']==2 and dims['width']<800,dimensions=dims)
            audit=await layout_audit(page)
            record('native-zoom-home-layout',not audit['overflowing'] and audit['pageOverflowX']==0,audit=audit)
            await page.screenshot(path=str(OUT/'native-zoom-200-home.png'),full_page=True)
            from fixtures_rich_trip import RICH_PLAN,RICH_GRAPH
            from qa_helpers import seed_plan
            await seed_plan(page,RICH_PLAN,RICH_GRAPH,'native-zoom')
            await page.goto(BASE+'/result?plan_id=native-zoom&section=budget')
            await wait_text(page,'预算明细')
            audit=await layout_audit(page)
            record('native-zoom-budget-layout',not audit['overflowing'] and audit['pageOverflowX']==0,audit=audit)
            await page.screenshot(path=str(OUT/'native-zoom-200-budget.png'),full_page=True)
            await context.close()
        edge=await p.chromium.launch(channel='msedge',headless=True)
        context=await edge.new_context(locale='zh-CN')
        page=await context.new_page();await install_mocks(page,{})
        for width in (320,375,430,768,1024,1440,1920):
            await open_landing(page,width)
            audit=await layout_audit(page)
            record(f'edge-home-{width}',not audit['overflowing'] and not audit['stickyOverlap'] and audit['pageOverflowX']==0)
        for section in ('overview','budget','itinerary','weather','map','graph'):
            for width in (320,1440):
                await open_result(page,width,section)
                audit=await layout_audit(page)
                record(f'edge-{section}-{width}',not audit['overflowing'] and not audit['stickyOverlap'] and audit['pageOverflowX']==0)
        await context.close();await edge.close()
    dump_json(OUT/'extended-report.json',dict(results=RESULTS,page_errors=ERRORS))
    return 0 if all(r['ok'] for r in RESULTS) and not ERRORS else 1

if __name__=='__main__':
    raise SystemExit(asyncio.run(main()))
