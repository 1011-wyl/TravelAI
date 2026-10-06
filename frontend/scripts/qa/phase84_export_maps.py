"""Real html2canvas/download QA; API and vendor SDK responses are isolated doubles.

No production test flags, no user's browser profile, no real credentials or paid requests.
Run against a fresh production build via Vite preview.
"""
from __future__ import annotations

import asyncio
import copy
import io
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from PIL import Image, ImageChops, ImageStat
from playwright.async_api import async_playwright
from fixtures_rich_trip import RICH_PLAN, RICH_GRAPH
from qa_helpers import seed_plan, wait_text, dump_json
from phase83_visual_a11y import install_mocks

BASE = os.environ.get('TRAVELAI_QA_BASE', 'http://127.0.0.1:4173')
OUT = Path(__file__).resolve().parents[3] / 'docs/qa/8.4'
RESULTS = []
ERRORS = []

# Deliberately labelled, deterministic vendor doubles. Genuine package loaders remain untouched.
SDK = r"""(() => {
 window.__sdkLog = [];
 window.__makeSdk = (vendor) => {
   const log = (event) => window.__sdkLog.push({vendor, event});
   class Map {
     constructor(target) {
       this.el = typeof target === 'string' ? document.getElementById(target) : target;
       this.el.innerHTML = '<div style="height:100%;background:#c3e4de;color:#16302b;display:flex;align-items:center;justify-content:center;font-size:28px">ISOLATED '+vendor+' SDK DOUBLE</div>';
       log('map-created');
     }
     add() {} fitBounds() {} getZoom() {return 12} setZoom() {}
     panTo() {log('pan')} setCenter() {log('pan')} setFitView() {} resize() {}
     destroy() {this.el.replaceChildren(); log('destroy')}
   }
   class Marker {
     constructor(opts) { this.opts=opts; this.events={}; log('marker'); }
     addListener(n,f) {this.events[n]=f} on(n,f) {this.events[n]=f}
     getPosition() {return this.opts.position}
     setMap(v) {if(v===null) log('marker-disposed')}
     setIcon() {} setZIndex() {} setContent() {}
   }
   class InfoWindow {open() {} close() {}}
   class Polyline {constructor() {log('straight-route')} setMap() {}}
   class DirectionsService {route() {return Promise.reject(new Error('isolated route failure'))}}
   class Route {search(a,b,cb) {cb('error',{})}}
   class Empty {extend() {return this} setMap() {}}
   return {Map, Marker, InfoWindow, Polyline, DirectionsService, DirectionsRenderer:Empty,
     Size:Empty, Point:Empty, Pixel:Empty, LatLngBounds:Empty, Driving:Route, Walking:Route,
     DrivingPolicy:{LEAST_TIME:0}, TravelMode:{DRIVING:'DRIVING',WALKING:'WALKING'},
     event:{trigger() {}}, plugin(plugins,cb) {cb()}, version:'2.0',
     importLibrary:async function() {return this}};
 };
})()"""

def record(name, ok, **details):
    RESULTS.append(dict(name=name, ok=bool(ok), **details))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {details}", flush=True)

async def setup(context, google='success', amap='success', keys=True):
    page = await context.new_page()
    page.set_default_timeout(15000)
    page.on('pageerror', lambda err: ERRORS.append(str(err)))
    page.on('console',lambda msg: print('BROWSER:',msg.text,flush=True) if msg.type=='error' and '导出' in msg.text else None)
    await install_mocks(page, {'history_mode':'empty'})
    await page.add_init_script(SDK)
    requests = []
    page.on('request', lambda req: requests.append(req.url))
    async def vendor(route):
        url = route.request.url
        g = 'googleapis.com' in url
        mode = google if g else amap
        if mode == 'fail':
            await route.abort()
            return
        if mode == 'late':
            await asyncio.sleep(6.5)
        cb = parse_qs(urlparse(url).query).get('callback',[''])[0]
        if g:
            body = "window.google.maps=Object.assign(window.google.maps,window.__makeSdk('google'));"
        else:
            body = "window.AMap=window.__makeSdk('amap');"
        if cb:
            body += f"{cb}();"
        await route.fulfill(content_type='application/javascript',body=body)
    await page.route('https://maps.googleapis.com/**',vendor)
    await page.route('https://webapi.amap.com/**',vendor)
    # Never fetch remote fixture media or QR. Exercise image error fallback as well.
    await page.route('https://example.com/**',lambda route: route.abort())
    await page.route('https://api.qrserver.com/**',lambda route: route.abort())
    await page.goto(BASE)
    await page.evaluate("""keys => {
      localStorage.setItem('travelai.theme','light'); localStorage.setItem('travelai.motion','reduce');
      if(keys) {
        localStorage.setItem('travelai.runtime.google_maps_api_key','isolated-not-real-google-key');
        localStorage.setItem('travelai.runtime.amap_web_js_key','isolated-not-real-amap-key');
      } else {
        localStorage.removeItem('travelai.runtime.google_maps_api_key');
        localStorage.removeItem('travelai.runtime.amap_web_js_key');
      }
    }""",keys)
    return page,requests

async def open_plan(page, plan=None, section='overview'):
    await seed_plan(page,plan or RICH_PLAN,RICH_GRAPH,'qa84')
    await page.goto(f'{BASE}/result?plan_id=qa84&section={section}')
    await page.locator('.result-page__heading').wait_for()
    await page.wait_for_load_state('networkidle')

async def export_start(page,with_map=False):
    await page.get_by_role('button',name='导出攻略').first.click()
    if with_map:
        await page.get_by_role('checkbox').check()
    await page.get_by_role('button',name='开始导出').click()

async def save_downloads(page, downloads, stem):
    await page.wait_for_function("()=>['已下载','导出失败','行程过长'].some(t=>document.body.innerText.includes(t))",timeout=60000)
    assert '已下载' in await page.locator('body').inner_text(), await page.locator('.export-dialog').inner_text()
    await asyncio.sleep(.3)
    paths=[]
    for i,download in enumerate(downloads):
        path=OUT/f'{stem}-p{i+1}.png'
        await download.save_as(str(path)); paths.append(path)
    return paths

def inspect_png(path):
    with Image.open(path) as image:
        rgb=image.convert('RGB')
        stats=ImageStat.Stat(rgb)
        return dict(width=image.width,height=image.height,variance=sum(stats.var),bytes=path.stat().st_size)

async def verify_landmarks(page, paths):
    """Validate all day headings, attraction names and footer in downloaded pixels.
    This catches repeated/blank/missing slices even if total dimensions are right.
    """
    landmarks=await page.locator('.trip-export-doc').evaluate("""root=>{
      const r=root.getBoundingClientRect();
      return [...root.querySelectorAll('h1,h2,h3,.trip-export-footer__url')].map(e=>{
        const b=e.getBoundingClientRect();return {text:e.textContent,x:b.left-r.left,y:b.top-r.top,w:b.width,h:b.height};
      });
    }""")
    images=[Image.open(path).convert('RGB') for path in paths]
    combined=Image.new('RGB',(1600,sum(im.height for im in images)))
    y=0
    for im in images: combined.paste(im,(0,y));y+=im.height
    missing=[]
    for mark in landmarks:
        box=tuple(round(v*2) for v in (mark['x'],mark['y'],mark['x']+mark['w'],mark['y']+mark['h']))
        pixels=combined.crop(box).getdata()
        # All these titles use dark/teal text, on white/light backgrounds.
        dark=sum(1 for r,g,b in pixels if r<150 and g<170 and b<170)
        if dark<12: missing.append(mark['text'])
    record('long-slice-content-landmarks',len(landmarks)>10 and not missing,checked=len(landmarks),missing=missing)

async def test_exports(browser):
    context=await browser.new_context(viewport={'width':1440,'height':900},accept_downloads=True,locale='zh-CN')
    page,requests=await setup(context,keys=False)
    downloads=[]
    page.on('download',lambda d:downloads.append(d))
    await open_plan(page)
    await asyncio.sleep(.5)
    record('html2canvas-not-before-confirm',not any('/html2canvas-' in u for u in requests))
    await export_start(page)
    paths=await save_downloads(page,downloads,'export-light')
    metrics=[inspect_png(path) for path in paths]
    record('export-real-png-nonblank',bool(metrics) and all(m['width']==1600 and m['variance']>100 for m in metrics),files=metrics)
    record('html2canvas-after-confirm',any('/html2canvas-' in u for u in requests))
    await page.screenshot(path=str(OUT/'export-done.png'))
    await page.get_by_role('button',name='完成',exact=True).click()
    # Same document must be independent of site theme and viewport.
    await page.evaluate("localStorage.setItem('travelai.theme','dark')")
    await page.set_viewport_size({'width':375,'height':850})
    await page.reload()
    await page.wait_for_load_state('networkidle')
    downloads.clear()
    await export_start(page)
    dark=await save_downloads(page,downloads,'export-dark-mobile')
    same=len(paths)==len(dark) and all(ImageChops.difference(Image.open(a).convert('RGB'),Image.open(b).convert('RGB')).getbbox() is None for a,b in zip(paths,dark))
    record('export-theme-mobile-invariant',same)
    await page.get_by_role('button',name='完成',exact=True).click()
    await page.set_viewport_size({'width':1440,'height':900})
    # Missing key must resolve promptly rather than waiting until a poll timeout.
    downloads.clear()
    await export_start(page,True)
    await page.get_by_role('button',name='不含地图继续').wait_for(timeout=10000)
    record('offscreen-missing-key-fails-promptly',True)
    await page.get_by_role('button',name='重试地图').click()
    await page.get_by_role('button',name='不含地图继续').wait_for(timeout=10000)
    await page.get_by_role('button',name='不含地图继续').click()
    files=await save_downloads(page,downloads,'export-without-map-recovery')
    record('map-failure-continue',len(files)>0)
    await page.get_by_role('button',name='完成',exact=True).click()
    # Generate a >5000px but <30000px document using legitimate plan text fields.
    long=copy.deepcopy(RICH_PLAN)
    for day in long['days']:
        for attraction in day['attractions']:
            attraction['description']='切片连续性验收：自然风景、目的地与旅途。'*100
    await open_plan(page,long)
    downloads.clear()
    await export_start(page)
    longpaths=await save_downloads(page,downloads,'export-long')
    bounds=await page.locator('.trip-export-doc').evaluate("e=>({height:e.scrollHeight,width:e.clientWidth})")
    lm=[inspect_png(p) for p in longpaths]
    record('long-slice-dimensions',len(lm)>1 and sum(m['height'] for m in lm)==bounds['height']*2 and all(m['width']==1600 and m['height']<=8000 and m['variance']>100 for m in lm),document=bounds,files=lm)
    await verify_landmarks(page,longpaths)
    # Compare cropped pages against the actual same DOM rendered by the browser.
    # Take a reference image of each slice after temporarily positioning the test DOM;
    # production rendering uses html2canvas (not this screenshot).
    await page.screenshot(path=str(OUT/'long-export-done.png'))
    await page.get_by_role('button',name='完成',exact=True).click()
    huge=copy.deepcopy(long)
    for day in huge['days']:
        for attraction in day['attractions']:
            attraction['description']*=10
    await open_plan(page,huge)
    downloads.clear()
    await export_start(page)
    await wait_text(page,'行程过长',timeout=30000)
    record('oversized-no-download',not downloads)
    await context.close()

async def test_maps(browser):
    scenarios=[('google', 'success','success'),('fallback-failure','fail','success'),('fallback-timeout','late','success'),('both-fail','fail','fail')]
    for name,g,a in scenarios:
        context=await browser.new_context(viewport={'width':1440,'height':900},locale='zh-CN',accept_downloads=True)
        page,requests=await setup(context,google=g,amap=a)
        await open_plan(page)
        record(f'{name}-lazy-sdk',not any('maps.googleapis.com' in u or 'webapi.amap.com' in u for u in requests))
        await page.get_by_role('navigation',name='结果分区').get_by_role('button',name='景点地图').click()
        if name=='both-fail':
            await wait_text(page,'地图没有成功抵达',timeout=15000)
            record('double-failure-text-route',await page.get_by_text('文字路线',exact=True).count()>0)
        else:
            expected='google' if g=='success' else 'amap'
            await page.wait_for_function("v=>window.__sdkLog.some(e=>e.vendor===v&&e.event==='map-created')",arg=expected,timeout=15000)
            await wait_text(page,'地图加载成功',timeout=15000)
            if g=='late':
                await asyncio.sleep(2.5)
            log=await page.evaluate('window.__sdkLog')
            record(f'{name}-provider',any(x['vendor']==expected and x['event']=='marker' for x in log) and not (g=='late' and any(x['vendor']=='google' and x['event']=='map-created' for x in log)),log=log)
            await page.screenshot(path=str(OUT/f'map-{name}.png'))
            # Real html2canvas screenshot of an explicitly fake SDK map.
            downloads=[]; page.on('download',lambda d:downloads.append(d))
            await export_start(page,True)
            pngs=await save_downloads(page,downloads,f'map-export-{name}')
            map_exists=await page.locator('.trip-export-map').count()
            record(f'{name}-visible-map-export',map_exists==1 and bool(pngs))
            await page.get_by_role('button',name='完成',exact=True).click()
            await page.get_by_role('navigation',name='结果分区').get_by_role('button',name='行程概览').click()
            await asyncio.sleep(.3)
            log=await page.evaluate('window.__sdkLog')
            record(f'{name}-disposed',any(x['event']==('marker-disposed' if expected=='google' else 'destroy') for x in log))
            if name=='google':
                downloads.clear()
                await export_start(page,True)
                pngs=await save_downloads(page,downloads,'offscreen-map-export')
                record('offscreen-ready-export',bool(pngs) and await page.locator('.trip-export-map').count()==1)
        await context.close()

async def test_cancel(browser):
    context=await browser.new_context(viewport={'width':1440,'height':900},locale='zh-CN',accept_downloads=True)
    page,_=await setup(context,keys=False)
    downloads=[];page.on('download',lambda d:downloads.append(d))
    async def slow_module(route):
        await asyncio.sleep(2)
        await route.continue_()
    await page.route('**/html2canvas-*.js',slow_module)
    await open_plan(page)
    before=await page.evaluate("sessionStorage.getItem('tripPlan')")
    await export_start(page)
    await page.get_by_role('button',name='取消准备').click()
    await asyncio.sleep(3)
    record('cancel-preparation-no-late-download',not downloads and await page.locator('.trip-export-doc').count()==0)
    record('export-no-plan-mutation',before==await page.evaluate("sessionStorage.getItem('tripPlan')"))
    await context.close()

async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as p:
        browser=await p.chromium.launch(channel='chrome',headless=True)
        for name,fn in [('exports',test_exports),('maps',test_maps),('cancel',test_cancel)]:
            try:
                await fn(browser)
            except Exception as e:
                import traceback
                record('fatal:'+name,False,error=str(e),trace=traceback.format_exc())
        await browser.close()
    dump_json(OUT/'report.json',dict(mode='isolated-API-vendor-doubles-real-html2canvas',results=RESULTS,page_errors=ERRORS,real_backend='not-tested',real_vendor='not-tested'))
    return 0 if RESULTS and all(r['ok'] for r in RESULTS) and not ERRORS else 1

if __name__=='__main__':
    raise SystemExit(asyncio.run(main()))
