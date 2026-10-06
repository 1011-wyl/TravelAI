# TravelAI 前端重设计验收记录（更新至阶段 9.4）

> 更新日期：2026-10-06。§1–§12 是各轮历史记录，其中“后端不可用 / 未调用模型”仅指当时；当前结果以 §13–§16 为准。
> 用户已授权沿用现有配置。真实规划、WS、历史恢复、聊天、高德地图和 PNG 导出已验证；隔离模拟证据另列。
> 前端实现与可执行自动化验收已补齐。**人工读屏、手机真机软键盘及 Lighthouse 尚未完成，不作全部发布验收通过的声明。**

## 1. 审查时的代码版本 / 工作区状态

| 项 | 值 |
|---|---|
| Git HEAD | `1053a56e743201c51c3083b8bb766c3957294804`（Initial commit） |
| 分支 | `main` |
| 工作区 | 大量未提交前端改造（约 34 条 status 行：修改/删除/新增） |
| 后端 diff | 未发现后端目录变更；变更集中在 `frontend/` 与 `docs/FRONTEND_REDESIGN_EXECUTION.md` |
| 依赖变更 | 仅移除 `swiper`（`package.json` / `package-lock.json`） |
| 临时脚本 | `frontend/` 下无改造遗留 `.cjs/.mjs` 临时脚本 |
| Composable 调用方 | `useTripPlanState` / `useBudgetEditor` / `useTravelMap` / `useTripExport` / `useKnowledgeGraph` / `useTheme` / `useMotionPreference` / `useResultSection` / `useAttractionPhotos` / `useItineraryEditor` 均有实际调用方 |

**未执行**：git commit / push / reset。

---

## 2. 工程检查结果

| 检查项 | 状态 | 说明 |
|---|---|---|
| `npm run type-check` | 已执行并通过 | 沿用阶段 7.2；本轮未改源码/构建配置，未重跑 |
| `npm run build` | 已执行并通过 | 沿用阶段 7.2；产物含 `echarts` / `maps` / `html2canvas` 独立 chunk |
| lint / test | 未执行 | `frontend/package.json` 无 `lint` / `test` 脚本；未新建脚本 |
| Swiper 运行时引用 | 已执行并通过 | `frontend/src` 与构建配置无 swiper；lockfile 无 swiper |
| Paper Kit / `global.css` | 已执行并通过 | 文件已删，`main.ts` 无入口 |
| 远程 Web Font / 装饰背景 | 仅代码检查 | `index.html` 无 Google Fonts；首页用本地 `topographic-lines.svg` |
| 动态 import 触发条件 | 仅代码检查 | ECharts：`GraphCanvas` 内；html2canvas：导出确认后；地图：`MapSection`/`ExportMapHost` 挂载时 `initMap` |
| 预算图 | 仅代码检查 | CSS 条形图，不加载 ECharts（符合“进入图谱才加载 ECharts”） |

---

## 3. 八条业务链审查结果与文件定位

状态说明：本轮为静态代码审查为主；标注「仅代码检查」者未做浏览器交互验证。

### 3.1 首页 → 规划

| 项 | 状态 | 证据 |
|---|---|---|
| 字段/默认值/枚举/校验/payload | 仅代码检查 | `Landing.vue` + `landingModel.ts` + `TripPlannerForm.vue`：多城市、出发日、交通/住宿/兴趣/特殊需求；`generateTripPlan(requestData)` 含 `city/cities/start_date/end_date/travel_days/.../language` |
| WS 回调与错误 | 仅代码检查 | `onTaskCreated` / `onTaskEvent`；失败清理 session 三键；`generateError` 持久展示且可重试 |
| 成功写入与跳转 | 仅代码检查 | 成功写 `tripPlan`/`graphData`/`planId` 后 `router.push({ path:'/result', query:{ plan_id } })` |
| 无自动轮询恢复 | 仅代码检查 | Landing 无 WS 失败自动轮询逻辑 |

定位：`frontend/src/views/Landing.vue`，`frontend/src/components/landing/*`，`frontend/src/services/api.ts`

### 3.2 历史 → 结果恢复

| 项 | 状态 | 证据 |
|---|---|---|
| plan_id 与缓存优先级 | 仅代码检查 | `openHistoryPlan` 清 `tripPlan`/`graphData`、写 `planId`；`hydrate`：queryId \|\| storedPlanId；缓存仅在 planId 匹配或缺失时使用 |
| 缺缓存回补 | 仅代码检查 | `pollTaskStatus(planId)` → `restoreTripPlanFromResponse` |
| 错误/空态区分 | 仅代码检查 | `missing` / `restore-failed` / `parse-failed` / `ready` → `ResultStatePanel` |
| 旧异步失效（照片） | 仅代码检查 | `useAttractionPhotos` 用 `loadId` + `planKey` watch 清空 |

定位：`Landing.vue` `openHistoryPlan`；`useTripPlanState.ts` `hydrate`

**问题见 §4.2-A：Result 未监听 `plan_id` 变化。**

### 3.3 结果分区

| 项 | 状态 | 证据 |
|---|---|---|
| section 唯一来源 | 仅代码检查 | `route.query.section`；`useResultSection` |
| push/replace、别名、保留 plan_id | 仅代码检查 | `writePublicSection` 展开 `...route.query`；别名 `days→itinerary`、`knowledge-graph→graph` |
| 前进后退 | 仅代码检查 | 依赖 router query；无第二份 activeSection |
| 分区挂载 | 仅代码检查 | 地图/图谱 `v-if`；概览/预算/日程/天气 `v-show` |

定位：`useResultSection.ts`，`resultSection.ts`，`Result.vue`

### 3.4 预算与日程

| 项 | 状态 | 证据 |
|---|---|---|
| 同一份 tripPlan | 仅代码检查 | `useBudgetEditor(tripPlan)` + `useItineraryEditor(tripPlan)` |
| 重算/取消/保存/session | 仅代码检查 | 保存走 `writePlanState`；预算 `persist` 写 `tripPlan`；取消回滚 `originalPlan` 并 `clearBudgetUndo` |
| 删除/撤销/排序 | 仅代码检查 | 预算 undo 6s；日程删景点校验至少保留 1 个 |
| 地图刷新 | 仅代码检查 | 预算联动 `invalidate`；保存后若在地图区 `refreshMap` |

定位：`useBudgetEditor.ts`，`useItineraryEditor.ts`，`Result.vue`

### 3.5 地图

| 项 | 状态 | 证据 |
|---|---|---|
| Key / Google 优先 / 5 秒 | 仅代码检查 | `GOOGLE_TIMEOUT_MS = 5000`；`Promise.race`；失败后 AMap |
| 迟到结果 / 离开分区 | 仅代码检查 | `generation` + `isActive`；`onUnmounted` → `invalidate` |
| 可见 vs 离屏容器 | 仅代码检查 | 默认 `google-map-container`；导出 `export-google-map-container` / `export-amap-container` + `quiet` |
| 文字路线 | 仅代码检查 | `TextRouteFallback` + `collectMapStops` |

定位：`useTravelMap.ts`，`MapSection.vue`，`ExportMapHost.vue`

### 3.6 图谱

| 项 | 状态 | 证据 |
|---|---|---|
| 节点/边与列表 | 仅代码检查 | `useKnowledgeGraph` + `GraphListView` |
| graph/list 偏好 | 仅代码检查 | Result `graphViewMode`；`planUiKey` 变化时置 `null`（回默认） |
| dispose / 主题 | 仅代码检查 | `GraphCanvas` `dispose`；watch theme/nodes |
| reduced motion | 仅代码检查 | `layout: none`，关闭 force 动画 |

定位：`KnowledgeGraphSection.vue`，`GraphCanvas.vue`

### 3.7 聊天

| 项 | 状态 | 证据 |
|---|---|---|
| 请求/history/重试 | 仅代码检查 | `POST ${apiBase}/api/chat/ask`，body `{ message, trip_plan, history }`；`history` 为成功消息 `slice(0,-1)` |
| 会话隔离 | 仅代码检查 | `watch(planKey)` → `resetSession()`；卸载 `requestSeq++` |
| 关闭保留 | 仅代码检查 | 关闭只改 `open`；消息保留在组件实例内 |
| aria-expanded | 仅代码检查 | `TripActionBar` 绑 `askOpen` ← `chatOpen`；面板 id `result-ai-chat-panel` |

定位：`AIChat.vue`，`TripActionBar.vue`，`Result.vue`

**问题见 §4.2-B：`planUiKey` 无 planId 时的指纹碰撞。**

### 3.8 导出

| 项 | 状态 | 证据 |
|---|---|---|
| 内容与浅色 | 仅代码检查 | `TripExportDocument` + `export.css` |
| 确认时快照 | 仅代码检查 | `runExport` 深拷贝 plan/photos |
| 分片限制 canvas | 仅代码检查 | `createExportCanvas` 预创建尺寸再 `html2canvas({ canvas, height })` |
| 任务有效性 | 仅代码检查 | `taskId` / `isLive`；下载前检查 |
| 地图失败选择 | 仅代码检查 | `map-failed` → 重试/不含地图/取消 |
| 清理 | 仅代码检查 | `invalidateWork` 清快照与离屏地图；图片 wait 清 timer |

定位：`useTripExport.ts`，`ResultExportPanel.vue`，`TripExportDocument.vue`

---

## 4. 问题清单

### 4.1 阻断功能的问题

（本轮静态审查未发现确定的构建阻塞或必现崩溃。）

无。

### 4.2 重要交互或可访问性问题

#### A. Result 不监听 `plan_id` 查询变化

- **状态**：**已修复**（阶段 8.2）
- **修复**：`Result.vue` 以 `watch(() => normalizeQueryPlanId(route.query.plan_id), …, { immediate: true })` 作为唯一 hydrate 入口（去掉 `onMounted` 重复调用）；`section` 变化不触发 hydrate。
- **竞态**：`useTripPlanState.hydrate` 使用 `hydrateSeq` + `disposed`；迟到结果不回写 `tripPlan` / `graphData` / `planId` / session / status。

#### B. `planUiKey` 在无 `planId` 时退化为「城市|日期」指纹

- **状态**：**已修复**（阶段 8.2）
- **修复**：`useTripPlanState` 提供页面内 `planSourceKey`（`src:N` 序号）；仅在成功 **adopt** 计划时递增；切换开始时先置 `''` 立即失效在途任务。`Result` 的 `planUiKey` 直接使用 `planSourceKey`，不再使用 `city|start|end`。
- **下游**：聊天 / 照片 / 导出 / 图谱偏好 / 日程展开 / 地图 invalidate 均跟该键；预算或日程字段编辑走 `applyTripPlanPayload` 且不 `adopt`，不更新版本。

#### C. `planUiKey` 变化时未重置编辑模式

- **状态**：**已修复**（阶段 8.2）
- **修复**：`useItineraryEditor.discardEdit()` 退出编辑并丢弃 `originalPlan`，不回滚到当前 `tripPlan`；`Result` 在 `planSourceKey` 变化时调用 `discardEdit` + `clearBudgetUndo`。

### 4.3 一般视觉问题

- 移除 `global.css` 后的标题 margin / Ant 级联：**未执行**浏览器对照
- light/dark、动效、200% 缩放、多断点：**未执行**

### 4.4 原有行为 / 限制

| 项 | 说明 |
|---|---|
| WS 失败无自动轮询 | 设计文档明确保留 |
| 地图 Key 来自设置/localStorage | 无仓库内 `.env`；本机未检测到 `VITE_*` |
| 导出 html2canvas 无法真正 abort | 仅阻止迟到下载（阶段 6.2/7.1 契约） |
| 后端本轮不可达 | `localhost:8000` 探测超时；阻塞真实规划/聊天/历史/回补 |
| 无 lint/test 脚本 | 工程限制，非回归失败 |

---

## 5. 浏览器、后端、地图可用条件

### 5.1 浏览器能力（本机探测）

| 能力 | 结论 |
|---|---|
| Chrome | 已安装：`C:\Program Files\Google\Chrome\Application\chrome.exe` |
| Edge | 已安装：`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` |
| Playwright CLI | 存在：`D:\Python39\Scripts\playwright.exe`（未验证是否已安装浏览器内核；本轮未 `playwright install`） |
| 截图 | **可以**：headless Chrome + 独立 `--user-data-dir` 临时 profile；落地 ` %TEMP%\travelai-qa-landing.png`（约 236KB） |
| DOM dump / 交互自动化 | **部分可以**：Chrome `--dump-dom` / Playwright 具备潜力；本轮 dump 遇 profile 占用，未完成稳定 DOM 自动化脚本 |
| 控制台与网络面板 | **可以**（需 DevTools/CDP 或 Playwright；本轮未接） |
| 下载文件验证 | **可以**（需自动化监听 downloads；本轮未做） |
| 完全无法启动浏览器 | **否** |

本轮最小 smoke：

1. `npm run preview -- --host 127.0.0.1 --port 4173`（基于已有 dist）
2. Chrome headless 打开 `http://127.0.0.1:4173/`
3. HTTP 拿到含 `#app` / TravelAI 标记的 HTML；**同时**生成非空 PNG 截图（不只凭 200）
4. HTML 中未见 `fonts.googleapis` / `swiper`
5. 已停止本轮 preview 进程

### 5.2 后端

| 项 | 状态 |
|---|---|
| `http://localhost:8000` | **外部条件阻塞**（连接超时） |
| 真实规划 / 历史 / 聊天 / plan 回补 | 阻塞 |

### 5.3 地图

| 项 | 状态 |
|---|---|
| 前端 `.env` / `.env.local` | 无 |
| 进程环境 `VITE_*` | 未检测到 |
| Key 运行时来源 | 设置抽屉 → localStorage（`travelai.runtime.*`） |
| 双地图真机验证 | **外部条件阻塞**（需用户已配置 Key + 后端或静态结果数据） |

---

## 6. 下一轮需要实际执行的验证

§4.2 A/B/C 已在阶段 8.2 修复并用隔离模拟响应做浏览器回归。下一轮仍待：

1. 浏览器：首页表单校验、提交失败态（**真实后端**可用时完整规划）。
2. 历史打开 → 结果六分区 → 前进后退（真实后端）。
3. 预算增删改撤销；日程编辑保存/取消（真实数据）。
4. 地图：有 Key / 缺 Key / Google 超时回退 AMap。
5. 图谱 graph/list、reduced motion。
6. 聊天成功/失败/重试与 `aria-expanded`（真实后端）。
7. 导出：无地图、含地图失败分支、长行程分片的**内容**验收（本轮仅验证切换时任务失效，未验收导出成品）。
8. 键盘全流程、移动宽度、light/dark、reduced motion。
9. 全站视觉与响应式对照。

---

## 7. 当前状态总表（禁止把未执行勾为通过）

| 域 | 状态 |
|---|---|
| 工程 type-check/build | 本轮重新执行并通过，标准构建与无密钥隔离构建分别记录 |
| Git/依赖范围审查 | 已执行并通过（8.1） |
| 八条业务链 | 仅代码检查（8.1） |
| 设计系统/a11y 实现接线 | 代码检查 + 浏览器回归；补齐 Drawer 焦点管理和按钮/图谱对比度 |
| 键盘/视觉/响应式 | 已执行：Chrome、Edge、七种尺寸、主题/减动、原生 200% 缩放；见 §9 |
| 人工读屏 | 未执行；DOM/焦点测试不等于 NVDA/VoiceOver 验收 |
| 首页 headless 截图 smoke | 已执行并通过（8.1） |
| 计划切换隔离浏览器回归 | **已执行并通过（8.2，隔离模拟响应，非真实后端）** |
| 前端交互自动化 | 隔离 API/WS 下已执行；预算真实弹窗、聊天 IME、图谱失败、导出实际 PNG 均有证据 |
| 后端联调 | 9.1：8000 `/health` 仍不可达；依赖不齐未能加载应用；未调用真实模型 |
| 地图双厂商 | 真实高德底图/标记/PNG 通过；Google 成功/回退/超时仅 SDK 替身，真实 Google Key 未配置 |
| 全站最终验收 | **前端可执行项目已完成；外部服务/人工验收仍有条件限制**，见 §11 |

---

## 8. 阶段 8.2：计划切换隔离修复与回归

> 性质：针对 §4.2 A/B/C 的修复 + Playwright 交互回归  
> **全部浏览器用例使用隔离模拟 API 响应**，不是真实后端验收。  
> type-check/build 通过 ≠ 浏览器回归通过（二者分别记录）。

### 8.1 修复文件与处理方式

| 问题 | 文件 | 处理 |
|---|---|---|
| A hydrate / 竞态 | `useTripPlanState.ts`, `Result.vue` | `normalizeQueryPlanId`；`watch(plan_id,{immediate})` 唯一入口；`hydrateSeq`/`disposed`；切换时 `beginPlanSwitch` 清空可编辑结果并 `status=loading` |
| B 来源标识 | `useTripPlanState.ts`, `Result.vue`, `ItinerarySection.vue`, `useAttractionPhotos.ts`, `AIChat.vue`, `useTripExport.ts` | `planSourceKey`；adopt 时递增；切换开始置空以失效在途任务；日程展开改跟 `planKey` |
| C 编辑隔离 | `useItineraryEditor.ts`, `Result.vue` | `discardEdit()`；`planSourceKey` 变化时丢弃草稿，不走 `cancelEdit` 回滚 |
| 工程顺带 | `CityRouteEditor.vue` | 修复阻塞 `vue-tsc` 的 InputNumber `update:value` 类型（非业务规则变更） |

### 8.2 回归环境

| 项 | 值 |
|---|---|
| 前端 | `npm run build` 后 `npm run preview -- --host 127.0.0.1 --port 4173` |
| 浏览器 | Playwright async + Chrome channel，独立临时 profile（结束后删除） |
| 后端 | **未使用真实后端**；拦截 `localhost:8000/api/**` 与 `**/api/**` |
| 夹具 | `frontend/scripts/qa/fixtures_plan_ab.py`（同城同日、内容不同的 A/B） |
| 脚本 | `frontend/scripts/qa/phase82_plan_isolation.py` |
| 行为单测（非浏览器） | `frontend/scripts/qa/plan_source_behavior_test.mjs`（mirror 规则；**不是** UI 回归） |
| 产物目录 | `%TEMP%\travelai-qa-8.2\`（`report.json` + PNG） |

### 8.3 各路径结果

| # | 路径 | 条件 | 结果 |
|---|---|---|---|
| 1 | 同实例切换 A→B | SPA `pushState`+`popstate` 改 `plan_id`；mock status | **PASS**：显示 B，session `planId=plan-b` |
| 2 | 恢复竞态 | A status 延迟 3s，先完成 B 再放行 A | **PASS**：页面与 session 仍为 B |
| 3 | 分区切换 | 同 `plan_id` 改 section + 前进后退 | **PASS**：`status_calls` 无新增；仍为 B |
| 4 | 编辑隔离 | A 进入编辑并改草稿后切 B | **PASS**：退出编辑；草稿未泄漏；B 上取消/保存可用 |
| 5 | 同城同日无 planId | session 换 B 后 SPA hydrate；聊天不应沿用 | **PASS**（浏览器）；另有 `plan_source_behavior_test.mjs` **PASS** |
| 6 | 在途任务 | 慢聊天/慢照片/导出确认后切 B | **PASS**：无 A 聊天污染；内容为 B；无 download |

控制台：`page_errors=[]`（见 `report.json`）。  
截图：`01-switch-b.png` / `02-race-b.png` / `04-edit-b.png` / `05-no-id-b.png` / `06-inflight.png`。

### 8.4 工程检查（8.2）

| 检查 | 结果 |
|---|---|
| `npm run type-check` | 通过 |
| `npm run build` | 通过 |
| 依赖 / lockfile | **未改** |
| Git commit / push | **未执行** |

### 8.5 残余与未验证

- 真实后端规划 / 历史 / 聊天 / 导出成品：未验证  
- 全站视觉、键盘、响应式、light/dark、reduced motion：未验证  
- 地图双厂商真机：未验证  
- 本轮 preview 进程已关闭；临时 browser profile 已清理

---

## 9. 阶段 8.3：视觉、响应式与键盘验收补齐

### 9.1 接手时的实际完成度

已有 `phase83_visual_a11y.py`、截图与 report，但 QA 主文档停在 8.2。原报告含首页进度、删除弹窗两个 fatal；另存在 `or True`、强制点击/禁用遮罩、仅修改 dataset 而不更新 ConfigProvider、预算“编辑”误匹配“编辑行程”等误判风险。因此接手时不能视为 8.3 已完成。

修正测试后重新执行，不沿用旧 PASS。历史 `run.log`、`fatal-*.png` 保留作基线；**当前结果以三个最新 JSON 报告及本文引用的截图为准**。

### 9.2 实际修复

| 问题 | 文件 | 修复 |
|---|---|---|
| 结果页失去内容边距 | `frontend/src/views/Result.vue` | `max-width: var(--content-max)`、居中、token gutter；标题增加 sticky 避让 |
| Hero 等高线生硬黑色 | `frontend/src/components/result/TripSummaryHero.vue` | SVG 改 mask + `--color-contour`，不新增持续动画 |
| dark 实心按钮白字不达标 | `frontend/src/styles/tokens.css`, `components/ui/AppButton.vue`, `theme/antdTheme.ts` | 新增 on-primary/on-accent/on-error；light 白字，dark `#071916`；Ant 同步实心文字 token |
| 图谱浅色节点白字不达标 | `frontend/src/components/result/graph/GraphCanvas.vue` | 按相对亮度选择白字/`#16302b`，不改节点类型或颜色语义 |
| Drawer Tab 越出背景 | `frontend/src/composables/useDrawerFocus.ts`（新建）；AIChat、SettingsDrawer、MobileNavDrawer | 共用 Tab/Shift+Tab 边界与 focusin 管理；尊重嵌套 Modal；卸载清监听；dialog 命名；关闭后回原触发器 |
| 手机菜单→设置关闭后焦点错误 | SettingsDrawer、NavBar | 等关闭过渡完成再归还焦点；原触发器已隐藏时回菜单入口，不抢回另一设置按钮 |
| 聊天在途 Esc 失效 | `frontend/src/components/AIChat.vue` | 请求开始禁用当前控件导致焦点移到 body 时，转入标题；不取消后端请求 |

这次使用 frontend-design 保持 Living Atlas 的布局/等高线语言；web-design-guidelines 与 ui-ux-pro-max 促使补齐焦点、对比度、减动和实际截图验收。主色板与业务规则未换。

### 9.3 浏览器覆盖与证据

- Chrome：首页与六分区，320×568、375×812、430×932、768×1024、1024×768、1440×900、1920×1080。布局检查不只看 document overflow，也检查可见元素溢出与 sticky 遮挡，不计隐藏 v-show 分区；允许明确的横向滚动轨道。
- light/dark 截图、system 跟随与刷新持久化；系统 reduced-motion 优先、光晕停止；直接读取真实 ECharts option 验证 `layout:none`、无 force、坐标不随时间变化。
- 首页校验、模拟 WS 进度/持久失败/有效重试、历史空/失败/成功；设置 GET/PUT 失败保留草稿；聊天失败/重试/在途关闭/关闭保留会话。
- 键盘跳转主要内容、分区标题焦点、日程折叠、真实预算金额 Modal 的 Esc/取消、删除确认/撤销（22→21→22）；聊天 Enter/Shift+Enter/IME 组合不误发。
- 聊天、设置、手机导航 Tab 圈闭；Esc 返回触发器；手机菜单→设置→关闭的交接。不是仅假定 Ant Drawer 自带圈闭。
- ECharts 库请求缺失时能改用完整列表；手机初始列表不请求 ECharts。与仅验证 chunk 存在区分。
- 原生 Chrome 200%：临时 profile 的 `partition.default_zoom_level.x = log(2)/log(1.2)`；不使用 CSS zoom、transform、deviceScaleFactor。实测 outerWidth=1440、innerWidth=711、devicePixelRatio=2；首页/预算无横溢出。
- Edge：七种尺寸首页；320/1440 六分区。英文/日文手机首页布局另测。
- 对比度报告覆盖可见文本的实色/透明叠加背景；梯度/照片和人工读屏不是此算法的“全通过”范围。主题切换先等过渡结束，避免测到过渡中间色。

证据：

- `docs/qa/8.3/report.json`：全量状态/布局套件，91 项通过；`page_errors=[]`。
- `docs/qa/8.3/targeted-report.json`：最终交互精确选择器复测，20 项通过、`page_errors=[]`；等待真实 Modal 原生焦点进入后测试 Esc，以真实预算 Modal 结果覆盖早期误匹配用例。
- `docs/qa/8.3/extended-report.json`：38 项通过、`page_errors=[]`；预算金额取消/保存、三类 Drawer 圈闭、IME、原生 zoom、Edge、英/日文。
- 代表截图：`overview-1440-light.png`、`landing-375-dark.png`、`mobile-budget-edit-modal.png`、`native-zoom-200-home.png`、`native-zoom-200-budget.png`。

---

## 10. 阶段 8.4：地图、导出成品与业务集成回归

### 10.1 已修复的实际导出问题

- Vue 会自动解包组件 `defineExpose` 中的 ref。原 `getMapHost()?.status.value` 因此不能可靠取到 ready/failed，导致离屏地图已完成仍等 20 秒。改为明确的 `getStatus(): string` 接口，调用方与 TS 类型同步（ExportMapHost / ResultExportPanel / useTripExport）。
- 导出照片失败时转为静态名称占位，不保留破图的大块空间（TripExportDocument）。不修改照片代理 API。
- 实际 PNG 验证确认 html2canvas 的 x/y 是元素 bounds 的相对偏移；**没有盲改离屏坐标或切片算法**。分片继续使用既有 800px、scale 2、4000px CSS 高度、总量 cap。

### 10.2 真实 html2canvas + 隔离 API/SDK

脚本 `frontend/scripts/qa/phase84_export_maps.py`；报告 `docs/qa/8.4/report.json`。26 项已通过，`page_errors=[]`。

| 域 | 实际验证 |
|---|---|
| 懒加载 | 用户确认前不请求 html2canvas；确认后真实动态 import/render/download；进地图前不请求厂商 SDK |
| 正常导出 | 真 PNG 下载，宽 1600px、像素有内容；纯前端下载，不是把下载事件或白画布算成功 |
| 主题/手机 | 等图片请求稳定后用同一份数据；dark+375px 与 light+1440px 的导出逐像素相同 |
| 长图 | 文档 13903px → 8000/8000/8000/3806px 四个 PNG；拼接高度=文档高度×2；在下载像素中核对 16 个标题/景点/页脚位置，防止重复/漏片 |
| 超限 | 超过 9600 万像素进 oversized，无下载 |
| 缺地图 | 离屏 missing-key 及时返回；重试地图后仍失败可不含地图继续 |
| 地图状态 | Google 成功；失败/5 秒超时回退 AMap；迟到 Google 不创建实例；双失败保留文字路线 |
| 生命周期 | 离开分区释放标记/地图；可见地图与离屏地图都能导出；取消准备无迟到下载、离屏文档卸载、session 行程不变 |

厂商 SDK 在该套件中是**有明确标识的网络层替身**，真正的 loader 包、Vue 组件与 html2canvas 都在运行。报告不能用于宣称真实 Google 认证/网络通过。

### 10.3 真实高德验证（不调用 AI）

另运行 `frontend/scripts/qa/phase84_live_map.py`，使用标准构建已有的本地地图配置。只给行程/设置接口提供隔离响应；**没有替换高德 SDK**、没有创建或打印密钥、没有访问个人浏览器 profile。

- 高德真实底图可见、7 个地点标记、1 个地图 canvas；截图 `docs/qa/8.4/real-amap-canvas.png`。
- 实际“包含地图截图”导出完成；PNG 中可看到真实高德底图/地点；`real-amap-export-p1.png`，约 1.95MB。
- `docs/qa/8.4/live-map-report.json`：`amap_ready=true`、`real_map_export=true`。
- Google 本地 Key 未配置；其真实厂商链路未验收。高德固定 darkblue 底图仍是既定限制，没有额外修改业务地图风格。

### 10.4 业务隔离与计算

- 重跑 `phase82_plan_isolation.py`：同实例切换、恢复竞态、section 不重请求、编辑隔离、同城同日来源隔离、在途聊天/照片/导出失效均通过，`page_errors=[]`。
- 修正原竞态测试的 150ms 假定：必须等 A 的真实 status 请求启动后才切 B，避免机器负载高时在 Router 启动前导航。
- 预算实际金额 Modal：取消不改 session；首个住宿金额 +100 后，酒店合计相应增加，总额按现有四项求和，写回 session。既有重算丢弃城际交通额的行为保留，未悄悄修业务计算。
- 本轮不改 `api.ts`、后端、DTO、聊天 payload、规划规则、存储键；不新增依赖；未 commit/push/reset。

---

## 11. 复现命令、工程结果与剩余外部条件

### 11.1 工程

- `frontend/` 下 `npm run type-check`、标准 `npm run build` 通过。
- 主 CSS 约 29.00kB；Result 约 340 行，仍 ≤350。
- ECharts / maps / html2canvas 仍是独立异步 chunk；ECharts ~1044kB 的既有体积警告不是构建失败。
- 没有 lint/test npm 脚本；没有安装新依赖或浏览器。

### 11.2 隔离复现（PowerShell）

在 `frontend/` 下，以**单独 shell 进程**构建，空白字符串经应用 trim 后为空，覆盖现有 .env，不编辑用户配置：

```powershell
$env:VITE_AMAP_WEB_JS_KEY=' '
$env:VITE_AMAP_SECURITY_JS_CODE=' '
npm run build -- --outDir dist-qa
node node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port 4174 --strictPort --outDir dist-qa
```

另一个 shell（本机已有 `D:\Python39` 的 Playwright + Pillow，使用已安装 Chrome/Edge）：

```powershell
$env:TRAVELAI_QA_BASE='http://127.0.0.1:4174'
$env:PYTHONIOENCODING='utf-8'
D:\Python39\python.exe -u scripts/qa/phase83_visual_a11y.py
D:\Python39\python.exe -u scripts/qa/phase83_extended.py
D:\Python39\python.exe -u scripts/qa/phase84_export_maps.py
D:\Python39\python.exe -u scripts/qa/phase82_plan_isolation.py
```

针对交互的短复测可增加 `TRAVELAI_QA_GROUPS='overlays-mobile,keyboard,chat-states,settings-fail,contrast-zoom'`、`TRAVELAI_QA_REPORT='targeted-report.json'`。默认运行仍是全量套件。

真实高德脚本需在未设置上述空白 env 的独立 shell 跑标准 build、启动 4173 preview，然后执行 `phase84_live_map.py`。脚本只读取应用已有配置，不声称生成了可用 Key。

收尾：本轮启动的 4173/4174 preview 已关闭；仅删除本轮生成的 `frontend/dist-qa` 隔离构建（可按上述命令重建）。标准 `frontend/dist`、用户配置、脚本、JSON 报告与截图证据均保留。

### 11.3 不能伪造的外部验收

| 项目 | 本轮事实 | 下一步需要 |
|---|---|---|
| 真实规划/WS/历史/聊天 | `127.0.0.1:8000/health` 连接失败；本轮未启动后端、未调用模型。模拟流程已验收 | 后端正常运行，并确认可使用现有模型配置做真实请求后再联调 |
| 真实 Google Maps | 后端 .env 的 Google Key 为空；没有借用/虚构 Google Key | 用户提供/配置可用 Google JS Key，验证域名/厂商授权与网络 |
| 真机软键盘/读屏 | IME 组合与键盘/DOM 已自动化；没有做 NVDA/VoiceOver 或真机软键盘体验 | 人工读屏及手机真机验收 |
| Lighthouse | 未运行；没有虚构 95/90 分 | 在确定部署/网络基线上另做 Lighthouse 与性能对照 |

结论：8.3 与 8.4 的前端可执行任务、发现的实现缺陷和可复现证据已补齐；真实高德地图/截图也已补验。**这不是所有外部服务与人工可访问性均已通过的发布批准。**

---

## 12. 阶段 9.1：环境与真实联调准备

> 历史准备记录：本节的缺依赖、后端不可用及待授权状态已被 §13 的实际联调结果取代。保留本节用于解释早期失败，不应重复配置 `.env`。

> 本轮只做环境核对、健康检查与条件整理。  
> **未进入 9.2**，未提交真实规划/聊天，未安装依赖，未改用户 `.env`，未 commit/push/reset。  
> 仓库无 `AGENTS.md`。

### 12.1 已有完成项（不重复大改）

| 项 | 状态 |
|---|---|
| 首页 / 结果六分区 / 设置 / 聊天 / 导出实现 | 已完成（工作区未提交改造） |
| 8.2 计划隔离 | 隔离 mock **PASS**，非真实后端 |
| 8.3 视觉/响应式/键盘 | 文档与 `docs/qa/8.3/` 证据已记录 |
| 8.4 导出 + 真实高德底图/标记/含地图 PNG | `docs/qa/8.4/` 已记录；Google 真实验证非阻塞 |
| Git HEAD | `1053a56`（Initial commit），分支 `main`，大量未提交 `frontend/` + `docs/` |
| 本轮源码 | **未改业务代码**；删除临时探测脚本 `frontend/scripts/qa/_phase91_env_presence.py` |

### 12.2 后端启动方式与本机环境

按 `README.md`：`cd backend` → `uv venv .venv` → 激活 → `uv pip install -r requirements.txt` → `uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload`。健康检查：`GET /health`、`GET /api/trip/health`、`GET /api/map/health`。WS：`/api/trip/ws/{task_id}`。

| 检查 | 结果 |
|---|---|
| `backend/.env` | 文件存在 |
| `backend/.venv` | **不存在** |
| `backend/node_modules`（小红书签名） | **不存在** |
| `uv` | 已安装 `0.12.1`（`C:\Users\USER\.local\bin\uv.exe`） |
| `backend/uv.lock` | 仅 4 行占位，`requires-python = ">=3.14"`，**不能当完整锁文件用** |
| 当前默认 Python | `D:\Python311\python.exe` 3.11.9 |
| 已能 import | `fastapi` / `uvicorn` / `pydantic` / `dotenv` / `httpx` |
| **缺失** | `pydantic_settings`（`app/config.py` 启动即失败）、`aiohttp`、`loguru`、`aiosqlite` |
| 本轮是否安装依赖 | **否**（9.1 禁止自行安装） |

先前曾用系统 Python 拉起 uvicorn reloader：监听进程出现过，但 worker 因 `ModuleNotFoundError: No module named 'pydantic_settings'` 退出。该失败进程现已不在；**当前 8000 无健康服务**。

### 12.3 配置存在性（只记有/无，不写内容）

读取 `backend/.env` 与 `frontend/.env` 的键是否非空、是否仍为 example 占位；不输出值。

| 键 | 结果 |
|---|---|
| 模型密钥（`LLM_API_KEY` / `OPENAI_API_KEY`） | **已配置** |
| 模型地址（`LLM_BASE_URL` / `OPENAI_BASE_URL`） | **已配置** |
| 模型名（`LLM_MODEL_ID` / `OPENAI_MODEL*`） | **已配置** |
| 后端高德 Web 服务 Key（`VITE_AMAP_WEB_KEY`） | **已配置** |
| 后端高德 JS Key（`VITE_AMAP_WEB_JS_KEY`） | **未配置（缺键）**；前端 JS Key 另在 `frontend/.env` |
| Google Maps Key | **未配置**（可选，非 9.2 阻塞） |
| 小红书 Cookie | **已配置**（存在非空值；未验证是否仍有效） |
| 前端 `VITE_API_BASE_URL` | **已配置**，指向本机 `localhost:8000` |
| 前端 `VITE_AMAP_WEB_JS_KEY` | **已配置** |
| 前端 `VITE_AMAP_SECURITY_JS_CODE` | **已配置** |

「已配置」≠ 密钥有效、≠ 模型可调用、≠ 高德配额可用。

### 12.4 前端与接口探测

`frontend/vite.config.ts`：`server.proxy['/api'] → http://localhost:8000`。`api.ts` 默认 `getRuntimeApiBaseUrl()` 在已设 `VITE_API_BASE_URL` 时直连 8000；Vite 代理用于相对 `/api` 请求。

本轮启动：`frontend/` 下 `npm run dev -- --host 127.0.0.1 --port 5173`。

| 探测 | 结果 | 分层 |
|---|---|---|
| `GET http://127.0.0.1:5173/` | HTTP 200，返回开发页 HTML（含 `#app`） | **服务已启动** |
| `GET http://127.0.0.1:8000/health` | 连接失败（curl 7） | 后端服务 **未就绪** |
| `GET http://127.0.0.1:8000/api/trip/health` | 连接失败 | 同上 |
| `GET http://127.0.0.1:5173/api/settings` | HTTP 500；Vite 日志 `http proxy error ... ECONNREFUSED` | 代理接线存在，**不是**设置接口正常 |
| `GET http://127.0.0.1:5173/api/trip/history` | 同上 500 + ECONNREFUSED | **不是**历史接口正常 |
| WebSocket `/api/trip/ws/...` | 未测通（无健康后端） | **不可连接** |
| 真实规划 / 真实聊天 | **未执行** | **真实生成未验证** |

### 12.5 阶段 9.2 所需真实条件

| 条件 | 当前 | 9.2 是否可开始 |
|---|---|---|
| 后端可用性 | 否：依赖不齐，`/health` 失败 | **阻塞** |
| WebSocket 可连接 | 否 | **阻塞** |
| 模型配置文件存在 | 是 | 仍须用户授权后才允许真实调用 |
| 高德配置存在 | 后端 Web Key 与前端 JS Key/安全码：是；Google：否 | 高德侧具备配置，未在本轮做真实 SDK 再测 |
| 设置/历史接口真实 200 | 否 | **阻塞** |

**阻塞项**：在禁止自行安装依赖的前提下，无法创建 `backend/.venv` / 补齐 `pydantic_settings` 等包，因此不能把后端变成健康服务。9.2 不能假装联调通过。

若你允许安装依赖，建议最小操作为（需你明确同意后才执行）：

```text
cd backend
uv venv .venv
.venv\Scripts\activate
uv pip install -r requirements.txt
npm install   # 小红书签名引擎，若规划依赖 XHS
uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload
```

然后先测 `/health` 再谈真实规划。`uv.lock` 不完整，应跟 `requirements.txt`，不要按残缺 lock 去 sync。

### 12.6 首次真实模型调用前的最小方案（待你授权）

真实规划和聊天会消耗现有 LLM 配额/费用。**本轮未调用模型、未改模型名、未新增 Key。**

建议 9.2 只做 **1 条**最小行程，避免重复付费：

1. 首页：单城（已有测试习惯用杭州即可）、最短天数、1 个兴趣，提交一次。  
2. 观察真实 WS 进度 → 成功则进结果页；核对 `plan_id` 与 session。  
3. 同一计划：六分区点一遍 + 浏览器后退前进 + 刷新。  
4. 历史列表打开刚才这一条（不再新规划）。  
5. 预算改 1 笔后取消；再改 1 笔保存；删除后撤销。日程只做一次进入编辑/取消。  
6. 地图分区看高德列表/标记（不测 Google）。  
7. 聊天只发 1 条短问题；关闭后再打开看是否保留。  
8. 导出 1 次当前行程（含地图若已 ready）。

失败态、竞态、无效密钥 **不**用真实模型重复打；沿用 8.2/8.3/8.4 隔离结果并标注模拟。

请明确回复其一：

- **允许使用现有 `backend/.env` 模型配置做上述最小真实调用**（可同时允许安装后端依赖）；或  
- **不允许真实模型调用**（9.2 只能做到健康检查/历史只读，规划/聊天标为阻塞）；或  
- **继续阶段 9.2**（若未允许安装依赖且后端仍不健康，将继续报告阻塞，不会伪造 PASS）。

### 12.7 9.1 分层结论

| 分层 | 结论 |
|---|---|
| 服务已启动 | **部分**：前端 `127.0.0.1:5173` 已启动；后端应用 **未**健康启动 |
| 接口响应正常 | **否**：settings/history 经代理 500（后端拒绝连接），不是业务 JSON |
| 真实生成已验证 | **否** |

本阶段停止，等待「继续阶段 9.2」以及是否授权安装依赖 / 真实模型调用。

---

## 13. 阶段 9.2：真实后端端到端联调（已完成）

### 13.1 当前环境与授权

- 用户明确允许使用现有配置。沿用 `backend/.env` 和前端已有高德配置，没有重填密钥、改模型、修改后端源码/接口/DTO。
- 本轮开始时 `backend/.venv` 与依赖已存在；本轮未重复安装依赖。使用该环境启动本机后端。
- `/health`、`/api/trip/health`、`/api/map/health` 实际 HTTP 200；设置、历史、任务恢复接口实际 200。
- 生产 preview 使用 `127.0.0.1:5173`，与既有 CORS 配置兼容。4173 的 CORS 失败属于测试端口选择问题，未通过修改后端绕过。
- 创建一次新的最小计划：杭州、1 天，`plan_id=ad39599a`。测试计划保留在真实历史中，未清除用户数据。真实聊天调用消耗现有配置配额；主 E2E 发一条短问题，早期横屏输入检查曾额外触发一条，后续输入测试已拦截聊天 POST，避免重复付费。

### 13.2 实际结果

规范证据：`docs/qa/9.2/final/report.json`：**27 项 PASS，page_errors=[]**。

| 链路 | 实际验证 |
|---|---|
| 首页 → 提交 | 原字段校验、防重复提交、生成状态 |
| WS → 结果 | 5 个真实 processing 事件 + 1 个 completed；plan_id 与 session 一致 |
| 六分区 | overview/budget/map/itinerary/graph/weather、前进后退、刷新 |
| 历史恢复 | 打开指定的刚生成计划，不以“出现任意结果”当作通过 |
| 预算 | 草稿取消、保存后四类合计核对、删除及撤销对象/行数核对 |
| 日程 | 实际地址修改后取消回滚、排序后 session 顺序核对 |
| 聊天 | 原 payload/history、真实回复内容、请求中关闭后再打开保留结果 |
| 导出 | 浏览器真实下载 PNG；尺寸 1600×4462，非空像素；快照中景点、编辑后总额、天气及页脚 |

预算补测 `docs/qa/9.2/budget-final-report.json`：6 项 PASS。失败/竞态通过隔离模拟回归验证，不用反复真实调用模型。

早期 E2E 地图截图可能早于底图绘制完成，不能单独证明瓦片完整；真实稳定底图的成品验证以 §15.2 为准。旧失败报告/截图保留为调试历史，不应混作当前结论。

## 14. 阶段 9.3：可访问性、输入与交互修复

### 14.1 本轮实际缺陷修复

| 文件 | 修复 |
|---|---|
| `components/NavBar.vue` | 语言 combobox 使用真实关联 label，而非仅在 Ant 外层挂 aria-label |
| `components/landing/CityRouteEditor.vue` | 停留天数关联 Form name/label |
| `components/landing/TripPlannerForm.vue` | 无效提交后 nextTick 聚焦首个错误输入，滚动定位 |
| `components/settings/SettingsDrawer.vue` | 原设置字段均有真实 label/input 关联，payload 不变 |
| `components/landing/PlanningJourney.vue` | progressbar 有可访问名称 |
| `components/chat/ChatComposer.vue` | 输入 16px、按 5 行自适应；粗指针设备横屏也 Enter 换行，保留桌面发送规则及 IME 防误发 |
| `components/AIChat.vue` | 长会话 log 不整体 live 播报；保留短 polite 状态 |
| `components/result/graph/KnowledgeGraphSection.vue` | 类型筛选公开 aria-pressed |
| `components/result/map/RouteStopList.vue` | 地点选择公开 aria-pressed |
| `styles/antd-theme.css` | 弹层/消息区滚动边界 overscroll containment |
| `styles/base.css` | 补全全局 sr-only，修复导航标签可见及聊天标签占据 grid 单元；未隐藏 skip-link |

这些修复遵循 Web Interface Guidelines / UI-UX Pro Max 的标签、语义、触屏输入和焦点规范；沿用既有 Living Atlas 设计，不重新设计主题或业务。

### 14.2 证据边界

- `scripts/qa/phase93_accessibility_perf.py` 检查实际 Chrome AX 树：非 ignored 控件的名称、标题层级、唯一 main。
- 覆盖首页、概览、预算、日程、天气、图谱列表、聊天、设置；不把第三方地图 SDK 生成的控件当作自研 UI。
- 移动模拟 375×812 与 812×375：IME、Enter 换行、16px 输入、页面横溢出、sr-only 布局。该套件禁止 `/api/chat/ask`，不新增真实聊天。
- 最新规范报告：`docs/qa/9.3/report.json`：**43 项 PASS，page_errors=[]**；语义 JSON 与 `mobile-chat-375.png` / `mobile-chat-812.png` 同目录。
- AX 自动检查 **不是人工读屏**，has_touch/mobile viewport **不是物理手机/真实软键盘**。剩余真人步骤见 `FRONTEND_REDESIGN_MANUAL_QA.md`。

## 15. 阶段 9.4：动态加载、地图导出与工程回归

### 15.1 运行时延迟加载

发现并修复：旧 maps manualChunk 吸入共享 CommonJS helper，导致首屏提前请求地图 loader。`vite.config.ts` 把 helper 单独放在 `vendor-helpers`，不改变地图 Google→AMap 规则。

最初尝试 `onlyExplicitManualChunks` 会造成运行时循环初始化错误；该方案已撤回。最终生产构建以共享 helper 独立分包验证，不仅看 chunk 文件存在。

测试从**首次冷导航之前**监听请求，不以缓存后的 reload 假装首屏延迟加载。核对首页/结果概览无 ECharts/maps/html2canvas；进入图谱、地图和确认导出后才各自请求库。证据同 `docs/qa/9.3/report.json`。

### 15.2 真实高德底图进入成品

`scripts/qa/phase94_map_pixels.py` 复用实际 `ad39599a`，不 mock、不调用 LLM，等待 canvas 像素绘制后导出。

证据：`docs/qa/9.4/map-pixel-report.json`、`map-before-export.png`、`real-plan-map-export.png`。

- 源地图与导出地图都检查深色底图比例 **及像素方差**，不能靠纯黑占位假 PASS。
- 已目视检查 PNG：真实杭州高德道路/地名、蓝色路线、3 个景点标记可见，预算/日程/天气/二维码页脚可读。
- 浅色导出是既定规范；深色地图沿用原 SDK 样式，并未宣称自动匹配站点主题。
- Google 真 Key 未配置，不阻塞当前高德方案。Google 超时/回退/迟到响应沿用隔离测试，不能声称完成 Google 真实厂商验收。

### 15.3 隔离回归与脚本可靠性

- `docs/qa/9.4/travelai-qa-8.2/report.json`：10 项 PASS，同实例切计划、恢复竞态、编辑快照、聊天/照片/导出过期任务隔离。
- `docs/qa/9.4/regression/regression-report.json`：**27 项 PASS，issues=[]，page_errors=[]**；针对首页状态、移动弹层、键盘、聊天失败、设置失败、对比度的回归，与真实 API 结果分开。
- 修复旧测试：WS 注入实际执行、等待真实焦点后 Esc、去掉 force click/遮罩禁用、配置经实际 composable 生效、验证撤销后的行数与对象。
- 当前短回归没有重跑原生 200% 缩放；原生 zoom 的早期证据在 §9 与 `phase83_extended.py`，不再生成无条件 PASS。
- `scripts/qa/phase92_live_e2e.py` 使用真实响应与内容断言，不只检验气泡/Toast/下载事件出现。每条链路不写入真实 storage 模拟数据；隔离套件只在独立 browser context 中使用夹具。

### 15.4 性能方法与限制

`docs/qa/9.4/browser-performance.json`：真实 Chrome PerformanceObserver、生产 preview、真实本机 API、独立冷 context；首页/结果概览 ×375/1440，每组合 3 次。

记录 FCP/LCP/CLS/long tasks 与资源 transferSize。无 CPU/网络节流，不是 Lighthouse，不代表低端手机/公网速度；不存在改造前同条件基线，不能声称性能提高某百分比。Lighthouse 下载运行尚待授权，未写任何分数。

最终构建的 3 次中位数（毫秒，2026-10-06）：

| 页面 / 宽度 | FCP 中位数 | LCP 中位数 | LCP 范围 | CLS |
|---|---:|---:|---:|---:|
| 首页 / 375 | 712 | 1948 | 1608–3896 | 0 |
| 概览 / 375 | 512 | 1064 | 908–1680 | 0 |
| 首页 / 1440 | 680 | 1860 | 1712–2132 | 0 |
| 概览 / 1440 | 744 | 1764 | 1280–3420 | 0 |

保留慢样本，没有为了好看剔除离群值。仍有主线程 long tasks，不能据中位数宣称所有访问都达到 LCP≤2.5s；后续正式部署应节流复测。最终 12 个冷启动样本未提前下载地图/ECharts/html2canvas。

### 15.5 工程与范围

- 最终标准 `npm run build`（内部含 vue-tsc）通过；独立 `npm run type-check` 通过。
- 主 CSS 29.28kB；`Result.vue` 340 行，仍 ≤350。
- maps / ECharts / html2canvas 均有异步 chunk；ECharts ~1044kB 既有警告仍在，不视为失败。
- 无新增项目依赖；package/lock 的既有差异仅 Swiper 移除。后端源码、API service、DTO、`.env` 未改；未 commit/push/reset。
- 本轮正常产物 `dist`、脚本、报告和截图保留；仅关闭本轮创建的服务，未删除用户历史或配置。

## 16. 当前完成矩阵与交付边界

| 工作 | 当前状态 | 证据/剩余条件 |
|---|---|---|
| 9.1 环境 | 已恢复可用并完成联调 | §13；不再需要重配 .env |
| 9.2 真实规划/WS/历史/聊天/导出 | 完成 | 27 项真实 E2E PASS |
| 9.3 代码/AX/浏览器键盘/模拟触屏 | 完成可执行部分 | §14；主报告与截图 |
| 9.4 工程/延迟加载/高德成品/浏览器性能 | 完成可执行部分 | §15；运行时请求及像素证据 |
| 真人读屏 | 未完成 | 需要真人与读屏工具；人工清单 §2 |
| 物理手机/软键盘 | 未完成 | 需要真实设备；人工清单 §3 |
| Lighthouse 建议分数 | 未运行 | 需要允许临时下载工具；不改项目依赖 |
| Google 真厂商 Key | 可选、非阻塞 | 当前使用真实高德，无须重复配置 Google |

结论：前端重设计实现、已发现缺陷与本机可执行验收已完成；**不能把剩余人工项/未运行 Lighthouse 写成 PASS，也不能宣称全部发布条件已满足。**
