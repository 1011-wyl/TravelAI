/*
 * Generate the screenshots embedded by README.md from the current frontend.
 *
 * Usage:
 *   1. Start `npm run preview -- --host 127.0.0.1` in frontend/.
 *   2. Make Playwright resolvable (or set PLAYWRIGHT_MODULE explicitly).
 *   3. Run `node scripts/capture_readme.cjs`.
 */

const { execFileSync } = require('node:child_process')
const fs = require('node:fs')
const path = require('node:path')

const projectRoot = path.resolve(__dirname, '..')
const outputDir = path.join(projectRoot, 'docs', 'images')
const baseUrl = process.env.TRAVELAI_PREVIEW_URL || 'http://127.0.0.1:4173'
const playwrightModule = process.env.PLAYWRIGHT_MODULE || 'playwright'
const python = process.env.PYTHON || 'python'
const { chromium } = require(playwrightModule)

const fixtureScript = [
  'import json, sys',
  `sys.path.insert(0, ${JSON.stringify(path.join(projectRoot, 'frontend', 'scripts', 'qa'))})`,
  'from fixtures_rich_trip import RICH_PLAN, RICH_GRAPH, history_items',
  'print(json.dumps({"plan": RICH_PLAN, "graph": RICH_GRAPH, "history": history_items()}, ensure_ascii=False))',
].join('; ')

const fixture = JSON.parse(
  execFileSync(python, ['-c', fixtureScript], {
    encoding: 'utf8',
    env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
  }),
)

async function installMocks(page) {
  await page.route('**/api/**', async (route) => {
    const url = route.request().url()
    if (url.includes('/api/trip/history')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: fixture.history }),
      })
      return
    }
    if (url.includes('/api/settings')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: {} }),
      })
      return
    }
    if (url.includes('/api/poi/')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: false }),
      })
      return
    }
    await route.fulfill({ status: 404, body: '{}' })
  })
}

async function preparePage(browser) {
  const page = await browser.newPage({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
    locale: 'zh-CN',
    colorScheme: 'light',
    reducedMotion: 'reduce',
  })
  await installMocks(page)
  await page.addInitScript(() => {
    localStorage.setItem('travelai-locale', 'zh')
    localStorage.setItem('travelai.theme', 'light')
    localStorage.setItem('travelai.motion', 'reduce')
  })
  return page
}

async function captureResult(page, section, fileName, marker, fullPage = false, settleMs = 0) {
  await page.goto(`${baseUrl}/`, { waitUntil: 'domcontentloaded' })
  await page.evaluate(({ plan, graph }) => {
    sessionStorage.setItem('tripPlan', JSON.stringify(plan))
    sessionStorage.setItem('graphData', JSON.stringify(graph))
    sessionStorage.setItem('planId', 'readme-demo')
  }, fixture)
  await page.goto(`${baseUrl}/result?plan_id=readme-demo&section=${section}`, {
    waitUntil: 'domcontentloaded',
  })
  await page.getByText(marker, { exact: true }).first().waitFor({ timeout: 20_000 })
  if (settleMs) await page.waitForTimeout(settleMs)
  await page.screenshot({
    path: path.join(outputDir, fileName),
    fullPage,
    animations: 'disabled',
  })
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true })
  const browser = await chromium.launch({ channel: 'chrome', headless: true })
  const page = await preparePage(browser)

  await page.goto(`${baseUrl}/`, { waitUntil: 'domcontentloaded' })
  await page.getByText('远方，不必从空白开始', { exact: true }).waitFor({ timeout: 20_000 })
  await page.screenshot({
    path: path.join(outputDir, 'home.png'),
    fullPage: true,
    animations: 'disabled',
  })

  await captureResult(page, 'overview', 'result-overview.png', '行程概览')
  await captureResult(page, 'budget', 'budget.png', '预算明细')
  await captureResult(page, 'itinerary', 'daily-itinerary.png', '每日行程', true)
  await captureResult(page, 'map', 'attraction-map.png', '景点地图', false, 10_000)
  await captureResult(page, 'graph', 'knowledge-graph.png', '灵感图谱', false, 1_500)
  await captureResult(page, 'weather', 'weather.png', '天气信息')

  await browser.close()
  process.stdout.write(`README screenshots written to ${outputDir}\n`)
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
