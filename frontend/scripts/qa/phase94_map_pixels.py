"""Verify actual AMap base tiles survive a real PNG export; no model call."""
import asyncio
import base64
import io
import os
from pathlib import Path
from PIL import Image, ImageStat
from playwright.async_api import async_playwright
from qa_helpers import dump_json, wait_text

OUT=Path(__file__).resolve().parents[3]/'docs/qa/9.4'
BASE=os.environ.get('TRAVELAI_QA_BASE','http://127.0.0.1:5173')
PLAN=os.environ.get('TRAVELAI_QA_PLAN_ID','ad39599a')

def dark_ratio(data_url):
    im=Image.open(io.BytesIO(base64.b64decode(data_url.split(',')[1]))).convert('RGB').resize((80,50))
    return sum(sum(pixel)<180 for pixel in im.getdata())/4000

def variance(data_url):
    im=Image.open(io.BytesIO(base64.b64decode(data_url.split(',')[1]))).convert('RGB')
    return sum(ImageStat.Stat(im).var)/3

async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as p:
        browser=await p.chromium.launch(channel='chrome',headless=True)
        ctx=await browser.new_context(viewport={'width':1440,'height':900},locale='zh-CN',accept_downloads=True)
        page=await ctx.new_page()
        await page.goto(f'{BASE}/result?plan_id={PLAN}&section=map')
        await wait_text(page,'远行摘要')
        await page.locator('#amap-container canvas').first.wait_for(timeout=60000)
        original_ratio=0
        for _ in range(40):
            canvas_url=await page.locator('#amap-container canvas').first.evaluate('e=>e.toDataURL()')
            original_ratio=dark_ratio(canvas_url)
            if original_ratio>.3 and variance(canvas_url)>5:
                break
            await asyncio.sleep(.5)
        await page.locator('#amap-container').screenshot(path=str(OUT/'map-before-export.png'))
        await page.get_by_role('button',name='导出攻略').first.click()
        await page.locator('.export-dialog__option input').check()
        async with page.expect_download(timeout=120000) as download_info:
            await page.get_by_role('button',name='开始导出').click()
        download=await download_info.value
        await download.save_as(str(OUT/'real-plan-map-export.png'))
        map_url=await page.locator('.trip-export-map').get_attribute('src')
        ratio=dark_ratio(map_url)
        source_variance=variance(canvas_url)
        export_variance=variance(map_url)
        ok=original_ratio>.3 and ratio>.3 and source_variance>5 and export_variance>5
        report={'mode':'real-plan-real-AMap-real-html2canvas-no-LLM','ok':ok,'source_dark_ratio':original_ratio,
                'export_map_dark_ratio':ratio,'source_variance':source_variance,'export_variance':export_variance}
        dump_json(OUT/'map-pixel-report.json',report)
        print(report,flush=True)
        await ctx.close();await browser.close()
        return 0 if ok else 1

if __name__=='__main__':
    raise SystemExit(asyncio.run(main()))
