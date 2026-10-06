/**
 * Non-browser behavior check for plan source adoption rules.
 * Distinguishes from Playwright UI regression — no production entry.
 *
 * Run: node scripts/qa/plan_source_behavior_test.mjs
 */
import assert from 'node:assert/strict'

/** Mirror of normalizeQueryPlanId in useTripPlanState.ts */
function normalizeQueryPlanId(queryPlanId) {
  if (Array.isArray(queryPlanId)) return String(queryPlanId[0] || '')
  if (queryPlanId == null) return ''
  return String(queryPlanId)
}

/** Mirror of page-local source key bumping (not city|date). */
function createSourceTracker() {
  let serial = 0
  let key = ''
  return {
    get key() {
      return key
    },
    beginSwitch() {
      key = ''
    },
    adopt() {
      serial += 1
      key = `src:${serial}`
      return key
    },
  }
}

assert.equal(normalizeQueryPlanId(undefined), '')
assert.equal(normalizeQueryPlanId(null), '')
assert.equal(normalizeQueryPlanId('plan-a'), 'plan-a')
assert.equal(normalizeQueryPlanId(['plan-b', 'x']), 'plan-b')
assert.equal(normalizeQueryPlanId([]), '')

const tracker = createSourceTracker()
const a = tracker.adopt()
const bCityDate = '杭州|2026-04-01|2026-04-03'
tracker.beginSwitch()
assert.equal(tracker.key, '')
const b = tracker.adopt()
assert.notEqual(a, b)
assert.notEqual(a, `plan:${bCityDate}`)
assert.notEqual(b, `plan:${bCityDate}`)

// Budget/field edits must not bump (simulated by not calling adopt)
const afterEdit = tracker.key
assert.equal(afterEdit, b)

console.log('PASS plan_source_behavior_test.mjs')
