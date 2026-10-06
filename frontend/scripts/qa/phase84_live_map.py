"""Optional real AMap smoke using existing build-time settings only.
Never reads/prints keys; trip/settings/chat responses remain isolated. No LLM calls.
"""
import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright
from fixtures_rich_trip import RICH_PLAN,RICH_GRAPH
from phase83_visual_a11y import install_mocks
from qa_helpers import dump_json,seed_plan

BASE=os.environ.get('TRAVELAI_LIVE_QA_BASE','http://127.0.0.1:4173')
OUT=Path(__file__).resolve().parents[3]/'docs/qa/8.4'

async def main():
    result={'mode':'real-AMap-existing-config-isolated-trip-no-LLM','real_google':'no-configured-key'}
    async with async_playwright() as p:
        browser=await p.chromium.launch(channel='chrome',headless=True)
        context=await browser.new_context(viewport={'width':1440,'height':900},locale='zh-CN',accept_downloads=True)
        page=await context.new_page()
        await install_mocks(page,{})
        # Fixture media never needs a real remote request.
        await page.route('https://example.com/**',lambda route:route.abort())
        await page.route('https://api.qrserver.com/**',lambda route:route.abort())
        await page.goto(BASE)
        await page.evaluate("localStorage.setItem('travelai.motion','reduce')")
        await seed_plan(page,RICH_PLAN,RICH_GRAPH,'real-amap-fixture')
        await page.goto(BASE+'/result?plan_id=real-amap-fixture&section=map')
        try:
            await page.wait_for_function("""()=>{
              const overlay=document.querySelector('.map-state-overlay');
              return document.querySelector('#amap-container .amap-maps') && !overlay;
            }""",timeout=30000)
            result['amap_ready']=True
            await asyncio.sleep(3)
            result['map_probe']=await page.locator('#amap-container').evaluate("""e=>({
              canvases:e.querySelectorAll('canvas').length,
              markers:e.querySelectorAll('.amap-marker').length,
              images:[...e.querySelectorAll('img')].map(i=>({loaded:i.complete&&i.naturalWidth>0}))
            })""")
            await page.screenshot(path=str(OUT/'real-amap.png'))
            await page.locator('#amap-container').screenshot(path=str(OUT/'real-amap-canvas.png'))
            downloads=[];page.on('download',lambda d:downloads.append(d))
            await page.get_by_role('button',name='导出攻略').first.click()
            await page.get_by_role('checkbox').check()
            await page.get_by_role('button',name='开始导出').click()
            await page.wait_for_function("()=>['已下载','导出失败','地图未能加入导出'].some(t=>document.body.innerText.includes(t))",timeout=45000)
            await asyncio.sleep(.5)
            result['real_map_export']=bool(downloads) and await page.locator('.trip-export-map').count()==1
            result['export_ui']=await page.locator('.export-dialog').inner_text()
            await page.screenshot(path=str(OUT/'real-amap-export-state.png'))
            for index,download in enumerate(downloads):
                await download.save_as(str(OUT/f'real-amap-export-p{index+1}.png'))
        except Exception as e:
            # Avoid serialising SDK errors / request URLs which may contain keys.
            result['amap_ready']=False
            result['limitation']=type(e).__name__
            overlay=page.locator('.map-state-overlay')
            if await overlay.count(): result['ui_state']=await overlay.inner_text()
            result['sdk_present']=await page.evaluate('()=>!!window.AMap')
            await page.screenshot(path=str(OUT/'real-amap-limitation.png'))
        await context.close();await browser.close()
    dump_json(OUT/'live-map-report.json',result)
    print(result)

if __name__=='__main__': asyncio.run(main())
