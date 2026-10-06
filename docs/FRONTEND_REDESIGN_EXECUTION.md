# TravelAI 前端重设计执行文档

> 文档定位：交给 Cursor 直接执行的唯一设计与改造依据  
> 设计主题：会呼吸的远行地图（Living Atlas）  
> 技术边界：Vue 3 + TypeScript + Vite；保留现有接口、数据结构和业务逻辑  
> 本文基于 frontend-design、web-design-guidelines、ui-ux-pro-max 三套规范，以及当前仓库页面、组件、服务层、样式和现有截图的完整审查

## 文档导航

Cursor 应按以下逻辑顺序理解和执行，即使编辑器折叠或重排了长文档，也不要跳过前置约束：

1. A. 现状盘点与重设计依据
2. B. 设计方向：会呼吸的远行地图
3. C. 量化设计系统
4. D. 页面级改造说明
5. E. 公共组件与交互规范
6. F. 样式与前端架构落地
7. G. Cursor 分阶段实施计划
8. H. 文件级变更总表
9. I. 验收标准
10. J. 实施前后的最终核对

## 0. Cursor 执行总则

1. 本次是前端表现层与交互层的完整重做，不是给现有页面换色。所有页面必须共享同一个设计系统、空间语言和动效语法。
2. 不改变任何后端接口路径、请求方法、WebSocket 协议、字段名称、字段含义、业务判断和存储键。现有 tripPlan、graphData、planId 等会话数据必须兼容。
3. 保持 Vue 3、TypeScript、Vite、Vue Router、Vue I18n、Ant Design Vue、ECharts、Google Maps/AMap 的技术栈。不得改成 React，不引入第二套 UI 框架。
4. 不新增 GSAP、Framer Motion 等动效库。使用 CSS 变量、Vue Transition/TransitionGroup 和 Web Animations API；优先 transform 与 opacity。
5. 保留 Ant Design Vue 作为无障碍基础设施，但外观必须由统一 token 覆盖，禁止继续混用 Paper Kit 风格。
6. 新页面不得依赖远程背景照片。氛围由 CSS 渐变、SVG 等高线、路线纹理和真实目的地图片内容共同形成。
7. 非对称来自信息优先级和路线叙事，不允许用随机偏移制造混乱。每个视口最多一个持续环境动画。
8. 所有交互同时支持鼠标、键盘与触摸；不得只在 hover 时暴露关键操作。
9. 每完成一个阶段都在 `frontend/` 目录运行 `npm run type-check` 与 `npm run build`。`frontend/package.json` 已提供 `type-check`（`vue-tsc --noEmit`）；不得改脚本、不得跳过 vue-tsc，也不得把已有类型错误归因于重设计后跳过。
10. 除下文明确留给内容数据驱动的部分外，Cursor 不需要自行决定颜色、字号、间距、圆角、动画、响应式或组件状态。

### 0.1 仓库路径与验证规则

前端不在仓库根目录。所有实施与验证必须遵守：

| 含义 | 实际位置 |
|---|---|
| 前端工程根 | `frontend/` |
| 应用源码 | `frontend/src/` |
| 入口 HTML | `frontend/index.html` |
| 依赖与脚本 | `frontend/package.json`、`frontend/package-lock.json` |
| 路由定义 | `frontend/src/main.ts` 中的 `createRouter`；**没有**独立 `frontend/src/router` 目录，重设计不得为了目录完整而新增路由工程 |
| 全局旧样式 | `frontend/src/styles/global.css`（Paper Kit 2，约 8,884 行） |
| i18n | `frontend/src/i18n/index.ts`、`frontend/src/i18n/messages.ts`、`frontend/src/i18n/locales/zh.json`、`en.json`、`ja.json`（中/英/日必须同步） |
| 接口封装 | `frontend/src/services/api.ts` |
| 数据类型 | `frontend/src/types/index.ts` |

规则：

- 下文文件清单一律写完整路径（以 `frontend/` 开头）。不要把 `src/...` 理解成仓库根路径。
- 所有 `npm` 命令在 `frontend/` 执行，使用现有 lockfile；不升级、不新增、不运行 `npm audit fix`。
- 文中单独出现的 `src/` 一律指 `frontend/src/`。

---

## A. 现状盘点与重设计依据

### A1. 当前技术与信息架构

#### 路由

| URL | 路由页面 | 当前职责 | 结论 |
|---|---|---|---|
| / | frontend/src/views/Landing.vue（约 1338 行） | 多城市行程表单、偏好、历史行程、发起规划、规划进度 | 保留路由，页面完整重构并拆分组件 |
| /result | frontend/src/views/Result.vue（约 4715 行） | 行程概览、预算、地图、日程、知识图谱、天气、导出、AI 助手 | 保留路由，拆成壳层 + 独立分区组件 |
| 无路由 | frontend/src/views/Home.vue（约 886 行） | 旧版首页/旧版表单逻辑 | 迁移确认后删除，避免双份业务逻辑 |

路由在 `frontend/src/main.ts` 用 `createRouter` / `createWebHistory` 注册上述两条路径；不存在独立 router 目录。当前没有 404/路由错误页；本轮不扩展业务路由，但必须在 App 壳层中为未知路径或结果数据缺失提供明确恢复入口。

#### 当前公共组件

| 文件 | 当前职责 | 主要问题 | 新去向 |
|---|---|---|---|
| frontend/src/components/NavBar.vue | 顶部导航、品牌、语言；设置目前是 NavBar 内 `a-modal`，调用 `getRuntimeSettings` / `saveRuntimeSettings` | 与页面氛围脱节，状态反馈弱，小屏层级不清 | 重构为全局 AppHeader；设置迁到 SettingsDrawer，请求与字段不变 |
| frontend/src/components/OverviewAttractionCard.vue | 概览景点卡片 | 视觉层级和图片状态不足，操作偏 hover 驱动 | 重构为 RoutePostcard，并保留兼容 props |
| frontend/src/components/AIChat.vue | 悬浮 AI 对话。直接 axios POST 到 /api/chat/ask，body 为 message、trip_plan、history | 1260×1100 面板通过 scale(.3) 缩小；15 个 3D 感应区；缺失 dialog、焦点和移动端语义 | 重构为 Ant Drawer/Sheet；不得改 payload，不得擅自重写 api.ts |

#### 页面内隐式组件

`frontend/src/views/Landing.vue`（约 1338 行）与 `frontend/src/views/Result.vue`（约 4715 行）内包含大量应独立维护的结构：多城市字段、规划状态、历史记录、结果分区导航、预算编辑、地图、每日行程、知识图谱、天气、导出状态和各种弹窗。它们目前通过单文件内大量 ref、computed、watch 和 scoped CSS 耦合，造成视觉和逻辑均难以统一。

#### 状态管理

- 没有 Pinia/Vuex；使用 Vue ref、reactive、computed、watch。
- sessionStorage 业务键（必须兼容）：`tripPlan`、`graphData`、`planId`。
- localStorage 现有业务键（必须兼容，不得改名）：
  - `travelai.runtime.api_base_url`
  - `travelai.runtime.amap_web_js_key`
  - `travelai.runtime.google_maps_api_key`
  - `travelai.user_id`
  - `travelai-locale`
- 本轮不引入 Pinia。按职责提取 composable，继续使用原有存储键，避免扩大迁移面。
- 新增一个纯前端偏好键 `travelai.theme`，值仅允许 system、light、dark；主题首访跟随系统。
- 新增一个纯前端偏好键 `travelai.motion`，值仅允许 system、reduce、full；默认 system。
- 结果页活动分区：现状内存键为 `overview`、`budget`、`map`、`days`、`knowledge-graph`、`weather`，且不写入 URL。重设计将活动分区同步到查询参数 `section`，URL 值为 `overview`、`budget`、`map`、`itinerary`、`graph`、`weather`。映射仅用于前端展示状态：`days` → `itinerary`，`knowledge-graph` → `graph`。不改变路由路径，不改变 tripPlan / graphData 业务字段。

#### 接口与外部能力

| 调用 | 用途 | 新设计中的呈现要求 |
|---|---|---|
| GET /api/settings | 读取设置 | 设置抽屉加载骨架；失败显示行内错误并允许重试 |
| PUT /api/settings | 保存设置 | 保存按钮具备 saving/success/error 状态，不允许只用全局 toast |
| POST /api/trip/plan | 创建规划任务 | 表单提交进入“旅程正在生长”进度叙事 |
| WS /api/trip/ws/{task_id} | 接收规划进度 | 将原始阶段映射为稳定的旅程节点，不改变消息协议 |
| GET /api/trip/status/{task_id} | 查询任务状态。Result 在 session 缓存不可用时用它回补已完成计划；`resumeTripPlan` 封装了“先 status 再挂 WS”，但 Landing **没有调用** | 保持现有调用面。Landing 的 `generateTripPlan` 在 WS 失败后不会自动轮询；重设计不得擅自增加轮询或任务中止。连接失败要有明确反馈，恢复入口仅限现有能力（例如错误提示后重新提交、历史入口、Result 已有的 status 回补） |
| GET /api/trip/history | 历史行程 | 以可恢复、可扫描的行程票根列表展示 |
| GET /api/poi/photo | POI 照片 | 统一图片骨架、失败渐变与替代文本 |
| GET /api/poi/image | POI 图片 | 同上；避免布局跳动 |
| POST /api/chat/ask | AI 问答。现状由 AIChat.vue 直接 axios 调用，不经 api.ts | 对话流显示发送、生成、失败、重试；payload 保持 { message, trip_plan, history } |
| /health | 健康检查封装 | 现有 UI 未暴露；本轮不新增业务入口 |
| /api/memory/* | 记忆能力封装 | 现有 UI 未暴露；本轮不新增业务入口 |

地图策略保持 Google Maps 优先，加载失败或 5 秒未完成时切换 AMap。重设计必须把等待、缺 Key、Google 失败、AMap 回退、双地图均失败做成明确状态，不能留下空白矩形。

当前调用方（业务归属，完成时只允许组件搬家）：GET/PUT `/api/settings` → NavBar；POST `/api/trip/plan` + WS → Landing 的 `generateTripPlan`；GET `/api/trip/status/{id}` → Result 缓存缺失时；GET `/api/trip/history` → Landing；GET `/api/poi/photo` 与 `/api/poi/image` → Result；POST `/api/chat/ask` → AIChat axios；`/health` 与 `/api/memory/*` → 仅 api.ts 封装、UI 未用。

### A2. 当前页面和交互流程

#### 首页

当前流程：填写多城市及各城停留天数、出发日期、交通偏好、住宿偏好、兴趣、特殊需求 → 提交 → 表单被进度步进器替换 → 成功后进入结果页；另有历史行程入口。表单没有独立出发地、人数、总预算或返程日期输入。总天数由各城停留天数求和；结束日期由出发日期加总天数减 1 算出，仅用于请求 payload 与展示，不是可编辑字段。

当前视觉以远程 Creative Tim/Paper Kit 图片、深色玻璃块和多套样式混合为主。真实控件和拟态卡片的对比关系不稳定，用户难以快速识别“必须填什么”和“下一步是什么”。

#### 结果页

当前通过页面内 `activeSection` 切换承载（**现状键名**，未写入 URL）：

1. `overview` 概览：行程摘要与景点轮播。
2. `budget` 预算：费用分类、图表、条目编辑（结果数据，不是首页输入）。
3. `map` 景点地图：地图标点、地点列表与路径。
4. `days` 每日行程：按天展示景点与安排。
5. `knowledge-graph` 知识图谱：ECharts 图谱及相关信息。
6. `weather` 天气：多日期天气卡片和图形动效。
7. 导出与 AI 助手：跨分区浮层能力。

当前活动分区不进入 URL，刷新/分享不能恢复视图。重设计的 URL `section` 映射见 A1 状态管理。各分区像来自不同产品：圆角、阴影、颜色、控件密度和空状态均不统一。

### A3. 必须解决的问题

#### 视觉系统

- frontend/src/styles/global.css 约 8,884 行，主体为 Paper Kit 2，再叠加 Ant Design、页面 scoped CSS、硬编码颜色与行内 SVG，缺少唯一设计源。
- 多处重复字体导入与远程资源；首页 HTTP 背景资源存在混合内容、失效和性能风险。
- 深色玻璃块中次级文字对比度不足；结果页主次不清。
- 过度重复“相同圆角卡片 + 相同阴影”，旅游氛围依靠图片而非系统化视觉语言。
- 移动端经常只是桌面版压缩，缺少内容重排策略。

#### 交互与无障碍

- 兴趣选项使用 `a-checkbox-group`，但 label 上 `@click.prevent` 自行 toggle，真实 checkbox 的键盘与读屏语义不完整。
- 天气日期使用可点击 li，不是 button。
- 概览关键操作只在 hover 出现，触屏不可发现。
- 预算图标按钮约 22px，小于 44px 触控目标，并使用 window.prompt/confirm。
- AIChat 缺少对话框语义、焦点圈闭、Esc 关闭和触发器状态。
- 多处 outline: none/0，无等价 focus-visible。
- 大量 transition: all 和无限动画，没有 prefers-reduced-motion。
- 加载、空、错误常常只是文本、旋转图标或空白区域，没有恢复路径。

#### 架构与性能

- Result.vue 过大，视觉、请求、地图、图表、导出和编辑逻辑耦合。
- 结果页首屏同步加载 ECharts、html2canvas、Swiper、地图加载器，首屏成本高。
- AIChat 以超大面板整体缩放，文本与点击区可能模糊、错位。
- 地图和图表容器尺寸/失败态不稳定；图片缺少统一比例和占位。
- Home.vue 与 Landing.vue 形成旧逻辑分叉；App.vue 留有注释掉的旧 header/footer。

---

## B. 设计方向：会呼吸的远行地图

### B1. 核心隐喻

统一视觉母题由五个元素组成：

1. 路线：一条从输入、规划、概览到每日行程持续出现的路径线。
2. 等高线：低对比 SVG 背景，暗示地形与探索；绝不抢文字。
3. 日出：暖珊瑚色局部光晕表示开始、行动和抵达。
4. 天气层：青绿、天蓝、沙金的透明叠层表示远方的空气。
5. 旅程节点：小圆点、停靠点、日期与目的地成为统一进度语言。

页面不采用粗野主义、纯直角零圆角或瞬时跳变。可以保留高变化度、橙色与青绿色的张力、进度叙事，但整体必须温暖、有机、可读。

### B2. 体验原则

- 呼吸不是所有东西都动：每个视口只允许一个环境光晕缓慢移动，业务内容保持稳定。
- 生命力来自响应：hover 轻浮、按下微缩、加载节点跳动、成功路线生长、错误状态轻微回收。
- 过渡必须有空间因果：抽屉从触发边进入；卡片详情从卡片位置扩展；分区内容沿路线方向切换。
- 非对称必须可解释：首页文案与规划器 5:7；结果摘要与关键动作 7:5；内容流可交替，但表单对齐保持规整。
- 真实信息优先于装饰：预算、时间、地点、天气是视觉主角，光晕和等高线只能做底层环境。
- 状态也是页面的一部分：每个异步区域在 loading、empty、error、partial、success 下都必须占有稳定布局。

---

## C. 量化设计系统

### C1. 主题与颜色

#### 晨光主题 light

| Token | 色值 | 使用范围 |
|---|---|---|
| --color-canvas | #F5F7F2 | 页面底色 |
| --color-canvas-alt | #EAF1ED | 分区底色、地图替代面 |
| --color-surface | #FFFFFF | 主要内容面 |
| --color-surface-raised | #FFFFFF | 抽屉、弹窗、浮层 |
| --color-text | #16302B | 主文字；在 canvas 上约 13.05:1 |
| --color-text-muted | #5D726D | 次级文字；在 canvas 上约 4.76:1 |
| --color-border | #CAD8D3 | 常规边框 |
| --color-border-strong | #9DB5AE | 强边界、分隔 |
| --color-primary | #147D72 | 主操作；白字约 4.99:1 |
| --color-primary-hover | #106B62 | 主操作 hover |
| --color-primary-soft | #D8EFEB | 选中底、标签底 |
| --color-accent | #F26A4F | 日出强调；配深色文字约 4.66:1 |
| --color-accent-strong | #C84531 | 强调按钮；白字约 4.83:1 |
| --color-sky | #3B74A8 | 天气、链接、信息 |
| --color-sand | #D4A866 | 预算与地形辅助 |
| --color-success | #1E7A55 | 成功 |
| --color-warning | #9A5B0A | 警告 |
| --color-error | #B23A3A | 错误 |
| --color-info | #2F6FA3 | 信息 |

#### 夜航主题 dark

| Token | 色值 | 使用范围 |
|---|---|---|
| --color-canvas | #071916 | 页面底色 |
| --color-canvas-alt | #0B2320 | 分区底色 |
| --color-surface | #102D29 | 卡片与控件 |
| --color-surface-raised | #163A34 | 抽屉、弹窗、浮层 |
| --color-text | #F2F7F4 | 主文字；约 16.72:1 |
| --color-text-muted | #A6BBB5 | 次级文字；约 8.97:1 |
| --color-border | #285048 | 常规边框 |
| --color-border-strong | #3B6A61 | 强边界 |
| --color-primary | #64C7B8 | 主操作；配深色文字约 8.97:1 |
| --color-primary-hover | #7CD7C9 | 主操作 hover |
| --color-primary-soft | #173F39 | 选中底、标签底 |
| --color-accent | #FF8C70 | 日出强调；配深色文字约 7.97:1 |
| --color-accent-strong | #FFAA92 | 强调 hover |
| --color-sky | #79AEE0 | 天气、链接、信息 |
| --color-sand | #E6BE7A | 预算与地形辅助 |
| --color-success | #63C696 | 成功 |
| --color-warning | #F0B869 | 警告 |
| --color-error | #FF8D8D | 错误 |
| --color-info | #86BCE8 | 信息 |

规则：

- 主按钮只用 primary；高情绪的“生成行程/开始旅程”可用 accent-strong，但一个视口最多一个 accent 实心按钮。
- 正文不可直接使用品牌色。正文只用 text 或 text-muted。
- 状态不能只靠颜色：同时使用图标、标题和文字。
- 等高线在 light 使用 rgba(20,125,114,.08)，dark 使用 rgba(100,199,184,.07)。
- 光晕只使用 primary/accent/sky，透明度 light 8%–14%，dark 10%–18%。
- 图片上的文字必须置于从 rgba(7,25,22,.82) 到透明的渐变遮罩之上。

### C2. 字体与排版

不新增字体下载依赖，使用系统字体栈：

- UI/正文：Outfit, PingFang SC, Hiragino Sans GB, Microsoft YaHei, Noto Sans CJK SC, sans-serif。
- 展示/目的地标题：Iowan Old Style, Noto Serif CJK SC, Songti SC, serif。
- 数字、预算和日期启用 font-variant-numeric: tabular-nums。

| 层级 | 桌面 | 移动 | 字重 | 行高 | 用途 |
|---|---:|---:|---:|---:|---|
| Display XL | clamp(48px, 7vw, 96px) | clamp(42px, 13vw, 64px) | 600 | .98 | 首页主标题，最多两行 |
| Display L | 48px | 36px | 600 | 1.08 | 结果目的地标题 |
| H1 | 36px | 30px | 650 | 1.15 | 页面标题 |
| H2 | 28px | 24px | 650 | 1.2 | 分区标题 |
| H3 | 22px | 20px | 650 | 1.3 | 卡片组标题 |
| Body L | 18px | 18px | 400 | 1.65 | 引导文本 |
| Body | 16px | 16px | 400 | 1.6 | 默认正文 |
| Body S | 14px | 14px | 400/500 | 1.5 | 辅助信息 |
| Caption | 12px | 12px | 500 | 1.45 | 标签、时间、图注 |

限制：

- 正文每行 45–75 个中文字符；说明区 max-width 68ch。
- 全大写只允许用于 3–12 字符的英文状态标签，并设置 letter-spacing: .08em。
- 禁止用极细字重表现次级信息；次级靠颜色与位置降级。
- 按钮文字最小 14px/600；输入内容最小 16px，避免移动端浏览器缩放。

### C3. 空间、尺寸与响应式

基础间距：4、8、12、16、24、32、48、64、96px。

语义 token：

| Token | 值 |
|---|---:|
| --space-1 | 4px |
| --space-2 | 8px |
| --space-3 | 12px |
| --space-4 | 16px |
| --space-6 | 24px |
| --space-8 | 32px |
| --space-12 | 48px |
| --space-16 | 64px |
| --space-24 | 96px |
| --content-max | 1440px |
| --content-readable | 1088px |
| --control-h-sm | 36px |
| --control-h-md | 44px |
| --control-h-lg | 52px |

断点与页面边距：

| 范围 | 页面 gutter | 规则 |
|---|---:|---|
| <640px | 16px | 单列；底部动作区；抽屉全屏 |
| 640–767px | 24px | 单列宽卡；允许两列小指标 |
| 768–1023px | 32px | 6 列网格；侧栏转顶部 |
| 1024–1279px | 32px | 12 列网格 |
| 1280–1439px | 48px | 12 列网格 |
| ≥1440px | 48px | 内容最大 1440px，居中 |

所有可点击目标至少 44×44px，目标间距至少 8px。移动端固定底栏需使用 env(safe-area-inset-bottom)。

### C4. 圆角、边框与阴影

| Token | 值 | 用途 |
|---|---:|---|
| --radius-sm | 10px | 标签、紧凑控件 |
| --radius-md | 16px | 输入、按钮、小卡 |
| --radius-lg | 24px | 常规卡片 |
| --radius-xl | 32px | 大面板、抽屉 |
| --radius-pill | 999px | 状态胶囊；不可用于所有按钮 |
| --radius-organic | 24px 24px 36px 18px | 仅用于主视觉/目的地卡 |

边框统一 1px solid var(--color-border)；focus-visible 使用 3px rgba 主色环并留 2px offset。

| 阴影 | light | dark | 用途 |
|---|---|---|---|
| --shadow-1 | 0 6px 18px rgba(22,48,43,.08) | 0 8px 20px rgba(0,0,0,.24) | 静态卡片 |
| --shadow-2 | 0 14px 36px rgba(22,48,43,.13) | 0 16px 42px rgba(0,0,0,.34) | hover、浮动导航 |
| --shadow-3 | 0 28px 72px rgba(22,48,43,.18) | 0 30px 80px rgba(0,0,0,.46) | 抽屉、弹窗 |

禁止给每张卡片都加阴影。默认靠底色和边框分层；只有可交互卡片 hover 后进入 shadow-2。

### C5. 动效规范

#### 时长与曲线

| Token | 值 | 用途 |
|---|---:|---|
| --duration-instant | 120ms | 按下、颜色反馈 |
| --duration-fast | 180ms | hover、focus、图标 |
| --duration-base | 240ms | 控件状态、tooltip |
| --duration-slow | 360ms | 卡片/区域进入 |
| --duration-scene | 480ms | 页面分区、抽屉 |
| --ease-standard | cubic-bezier(.2,.8,.2,1) | 常规 |
| --ease-emphasized | cubic-bezier(.2,.9,.25,1) | 场景切换 |
| --ease-spring | cubic-bezier(.34,1.56,.64,1) | 小尺度回弹，禁止大面板 |

#### 交互参数

- 可交互卡 hover：translateY(-2px)，shadow-1 → shadow-2，180ms standard。
- 主按钮 hover：translateY(-1px)，亮度 +3%，180ms；active：scale(.985)，120ms。
- 图标按钮 hover：图标 rotate 或 translate 不超过 4deg/2px；不旋转设置齿轮超过 8deg。
- 输入 focus：边框切 primary，外环 3px，180ms；不能改变控件尺寸。
- Tooltip：延迟 400ms，进入 160ms；有文字标签的按钮不重复显示。
- 卡片列表进入：translateY(12px) → 0、opacity 0 → 1，360ms；相邻延迟 40ms，最多 6 项，之后不递增。
- 分区切换：旧内容 translateX(-12px) + opacity 0，新内容 translateX(16px) → 0，360ms；方向需随导航前后变化。
- Drawer：480ms emphasized；桌面从右侧，移动端从底部升起。
- Modal：scale(.98) + translateY(8px) → 1/0，240ms；禁止弹簧过冲。
- 路线绘制：SVG stroke-dashoffset，480–900ms，只在首次完成规划或分区首次进入时触发一次。
- 加载节点：三个节点按 0/120/240ms 相位做 translateY(-3px)，单次循环 1.2s。
- 环境光晕：18s 与 24s 两套，位移不超过容器尺寸 2%，缩放不超过 1.04；每视口只运行一套。

#### reduced motion

当系统 prefers-reduced-motion: reduce 或用户选择“减少动态”时：

- 所有动画和过渡降至 1ms 或直接关闭。
- 关闭光晕漂移、路线绘制、节点跳动、图表入场、视差。
- 保留颜色、边框、文本等非位移状态反馈。
- 滚动行为改为 auto，不使用 smooth。
- Swiper/自动轮播不得自动推进；本方案会移除 Swiper。

### C6. 生命力风格落地清单

| 场景 | 视觉与动效 | 精确参数 |
|---|---|---|
| 全局背景 | 两层径向光晕 + 等高线 | 光晕 18/24s、2% 位移、8%–18% 透明度 |
| 首页路线 | 城市列表首城到末城的曲线路径（不是新的出发地字段） | 提交成功后 720ms 绘制 |
| 规划进度 | 节点依次点亮并向前推进 | 状态变化 360ms；当前节点 1.2s 呼吸 |
| 目的地卡 | 图片轻微上移、路线节点生长 | 卡 -2px；图 1.02；节点 6→8px，180ms |
| 分区切换 | 沿路线方向位移 | 12–16px，360ms |
| 成功 | 路线到达并出现暖色日出点 | 480ms，执行一次 |
| 加载 | 有形状的 skeleton 和跳动旅程节点 | shimmer 1.6s；节点 1.2s |
| 空态 | 断开的虚线路径与明确下一步 | 无循环；按钮可行动 |
| 错误 | 路线在错误点停止，提供重试/返回 | 160ms 轻微横移 3px，一次，不抖动循环 |

---

## D. 页面级改造说明

### D0. 全局 App 壳层与导航

#### 当前问题

- App.vue 仍有注释掉的旧 header/footer，页面自行承担背景和顶层间距。
- NavBar 与首页、结果页分别使用不同视觉语法；滚动后缺少位置与状态反馈。
- 语言、主题、设置入口的层级与移动端行为不统一。

#### 新设计

全局壳层负责主题、背景、跳转到主内容、导航和全局状态。顶部导航呈“浮在路线之上”的轻薄导航带，而不是深色玻璃条。

桌面结构：

    ┌──────────────────────────────────────────────────────────────┐
    │ TravelAI ●   规划旅程   我的行程        语言  主题  设置     │
    └──────────────────────────────────────────────────────────────┘
                      main#main-content

- 高度 72px，页面顶端透明；滚动超过 24px 后背景变为 surface 88% + backdrop-filter blur(16px)，并出现 1px 下边界。
- 品牌标志由“路线节点 + TravelAI”组成；点击回首页。
- 当前页使用文字加下方 24px 长路线段，不只改变颜色。
- 主题按钮在 system/light/dark 间通过设置菜单选择；图标按钮必须有 aria-label。
- 导航后第一个元素是“跳到主要内容”链接，键盘聚焦时显示。
- 小于 768px：保留品牌、主题和菜单按钮；菜单使用 Drawer，不在窄屏硬塞横向导航。

#### 状态和动效

- 顶部透明→实体：240ms，只变背景/边框/阴影。
- 品牌节点 hover：路线末端前进 2px，180ms。
- 当前项切换：下划路线段用 scaleX，240ms；reduced motion 直接切换。
- 导航抽屉打开后焦点进入首项，关闭后回到触发按钮；Esc 可关闭。

#### 文件

- 修改 frontend/src/App.vue：挂载 AppShell、跳转链接、RouterView 过渡、主题初始化；删除旧注释。
- 重构 frontend/src/components/NavBar.vue。
- 创建 frontend/src/components/layout/AppShell.vue。
- 创建 frontend/src/components/layout/MobileNavDrawer.vue。
- 创建 frontend/src/composables/useTheme.ts。
- 创建 frontend/src/composables/useMotionPreference.ts。

### D1. 首页 / Landing

#### 当前问题

- 首页依赖外部 Creative Tim/Paper Kit 背景图，品牌感不独立，资源失败时首屏坍塌。
- 主标题、说明、表单、兴趣选择和历史行程竞争注意力。
- 表单提交后上下文断裂，用户不易确认自己刚提交的行程。
- 规划进度以技术阶段为主，不像旅行准备过程。
- 隐藏 checkbox、紧凑点击区、反馈不完整。

#### 新结构

首屏桌面采用 5:7 非对称构图，移动端按“情绪 → 行动 → 信任”排序。

    ┌─────────────────────────────────────────────────────────────┐
    │  左：目的地叙事 5列       右：旅程规划器 7列               │
    │  远方不必从空白开始       城市1 ──────● 城市N               │
    │  一句简短价值说明          出发日期 / 总天数（只读摘要）      │
    │  动态路线与日出点          交通 / 住宿 / 兴趣 / 特殊需求     │
    │                             [开始规划我的旅程]               │
    ├─────────────────────────────────────────────────────────────┤
    │  规划中：只读摘要 + 旅程节点进度 + 可理解的当前动作          │
    ├─────────────────────────────────────────────────────────────┤
    │  最近旅程票根（横向可滚动但不自动轮播）                      │
    └─────────────────────────────────────────────────────────────┘

#### Hero

- 背景使用 canvas 与 canvas-alt 叠层；左上青绿雾、右下珊瑚日出，配 topographic-lines.svg。
- 主标题使用 Display XL，建议文案“远方，不必从空白开始”；不得再叠加英文大字水印。
- 副文案最多 2 行、max-width 34ch。
- 路线插画用内联 SVG：两个节点和一条贝塞尔曲线。初次加载只做一次 720ms 绘制，之后静止。
- 不用纯装饰大图，避免首屏加载外部资源。

#### 规划表单

- 面板使用 surface，radius-xl，左上和右下可用 organic radius；内边距桌面 32px、移动 20px。
- 表单按语义分成三段，**只使用现有字段，不新增输入**：
  1. 去哪里：多城市列表（每城名称 + 停留天数）；可添加/删除/排序城市。没有独立「出发地」字段；路线节点用城市列表顺序表达。
  2. 什么时候：出发日期（现有 `start_date`）。总天数 = 各城停留天数之和；结束日期按原规则由出发日期 + 总天数 - 1 计算，只读展示，写入现有 `end_date` / `travel_days` payload。
  3. 怎样旅行：交通偏好、住宿偏好、兴趣、特殊需求（`free_text_input`）。不新增人数、总预算或节奏输入。预算只出现在结果页既有分区。
- label 始终显示在输入上方，不用 placeholder 代替 label。
- 必填标记同时提供视觉星号和读屏说明；校验错误放在字段下方并通过 aria-describedby 关联。
- 城市路线编辑器：
  - 每个城市是 52px 高的路线节点行。
  - 拖拽把手仅是增强能力；同时提供“上移/下移”按钮。
  - 删除按钮 44×44px；最后一个目的地不可删时置 disabled 并说明原因。
  - 拖动完成后使用 aria-live 礼貌播报新顺序。
- 兴趣选择使用真实 checkbox：
  - 外观是 44px 高 chip；未选 surface + border，hover primary-soft，选中 primary-soft + 2px primary 边界 + check。
  - focus-visible 明确；不隐藏到无法聚焦。
- 主按钮高度 52px，宽度移动端 100%，桌面至少 220px；仅表单有效时启用。
- 提交时按钮文本改为“正在启程…”，保留宽度，左侧出现路线节点加载图；禁止重复提交。

#### 规划进度

提交后表单不消失，收拢为只读 TripBrief：城市顺序、各城停留天数、出发日期、计算得到的结束日期与总天数、交通、住宿、兴趣。现有逻辑在生成期间用 loading 覆盖表单，没有「修改计划 / 中止任务」入口；重设计不得新增任务中止、confirm 中止或 WS 失败后的自动轮询。生成失败后沿用现有错误提示，用户可再次提交。

进度区命名为“你的旅程正在生长”，将后端已有阶段映射到以下展示节点；映射仅在前端完成，未知阶段统一落入当前节点说明，不改协议：

1. 理解期待。
2. 寻找沿途灵感。
3. 编排每日路线。
4. 平衡时间与预算。
5. 打包完整旅程。

- 已完成节点：primary 实心 + check。
- 当前节点：accent 环 + 1.2s 呼吸；右侧显示后端实际状态的自然语言。
- 未开始：border 圆点。
- 若能得到进度百分比，用长度进度条；不能得到时不伪造百分比。
- WS 失败或断开：显示明确错误（可用“连接暂时中断”一类文案），**不**自动轮询 `/api/trip/status`，**不**调用当前未被 Landing 使用的 `resumeTripPlan`。用户恢复路径仅限现有能力（重新提交、历史行程）。
- 长任务超过 10 秒，补充“你可以留在这里，我们会持续更新”；超时与重试遵循既有 `generateTripPlan` / WebSocket 行为，不许新增业务超时。
- 生成完成时路线抵达第 5 节点，显示“查看完整行程”，自动跳转只在原逻辑本就自动跳转时保留。

#### 历史行程

- 标题“再次出发”，右侧显示总数（若已有数据）。
- 卡片采用“票根”语义而非同质网格：左侧日期条，中央目的地与摘要，右侧箭头。
- 桌面 3 列，平板 2 列，移动单列；内容不足时不拉伸。
- hover -2px；整卡可点击，但卡内删除/其他动作必须独立停止冒泡。
- loading：3 个固定高度骨架；empty：断开的路线 + “还没有保存的旅程” + 聚焦规划器按钮；error：行内重试。

#### 文件

- 重构 frontend/src/views/Landing.vue，使其只负责编排和页面级状态，目标不超过 300 行。
- 创建 frontend/src/components/landing/TripHero.vue。
- 创建 frontend/src/components/landing/TripPlannerForm.vue。
- 创建 frontend/src/components/landing/CityRouteEditor.vue。
- 创建 frontend/src/components/landing/InterestSelector.vue。
- 创建 frontend/src/components/landing/PlanningJourney.vue。
- 创建 frontend/src/components/landing/TripHistory.vue。
- 创建 frontend/src/components/trip/TripBrief.vue。
- 复用现有 service 和类型；不改接口签名。

### D2. 结果页壳层 / Result

#### 当前问题

- 单文件超过 4,700 行，分区切换、请求、编辑、图表、地图、导出强耦合。
- 分区入口像普通按钮组；当前分区不可分享、刷新后不可恢复。
- ECharts、地图、html2canvas、Swiper 等重依赖首屏加载。
- 各分区页头、状态、动作位置不同，用户需要反复学习。

#### 新结构

    ┌──────────────── TripSummaryHero ────────────────────────────┐
    │ 返回规划  城市路线 / 日期 / 天数           导出  问助手    │
    │ 一条横跨摘要的路线与 3 个关键指标                           │
    └─────────────────────────────────────────────────────────────┘
    ┌──────── ResultSectionNav（桌面 sticky / 移动横向滚动） ─────┐
    │ 概览  预算  地图  每日行程  灵感图谱  天气                 │
    └─────────────────────────────────────────────────────────────┘
    ┌──────────────── active section ─────────────────────────────┐
    │ 分区标题 + 一句话说明 + 分区操作                             │
    │ loading / empty / error / content                           │
    └─────────────────────────────────────────────────────────────┘

#### 行为

- 从 sessionStorage 读取既有 tripPlan/graphData/planId，读取失败时显示 ResultStatePanel，不渲染半空页面。
- 无数据：标题“这段旅程还没有装进行囊”，操作“回到首页重新规划”。
- 数据损坏：说明本地行程无法读取，提供返回首页；开发环境记录解析错误，生产不暴露堆栈。
- section 查询值只允许 overview、budget、map、itinerary、graph、weather；无效值回退 overview 并 replace URL。
- 现状内存分区到 URL 的映射（仅前端展示状态，不改业务数据）：`overview`→`overview`，`budget`→`budget`，`map`→`map`，`days`→`itinerary`，`knowledge-graph`→`graph`，`weather`→`weather`。
- 用户点击分区用 `router.push` 更新 `?section=`（缺省/非法/别名用 `replace` 规范化），保留其他查询参数（包括现有 `plan_id`）；同一分区不重复写入历史。浏览器前进/后退同步内容。路由定义仍在 `frontend/src/main.ts`，不新增 router 目录。
- 分区切换后把焦点移到分区 h2（tabindex=-1），读屏能感知上下文变化；不强制滚动到页面顶端。
- 导出和 AI 助手是跨分区全局动作，始终放在摘要区，不在每区重复。
- 首屏只加载概览。地图、ECharts、html2canvas 在用户进入相关分区/执行导出时 dynamic import。

#### 摘要 Hero

- 桌面 7:5：左侧目的地/城市标题与路线，右侧日期、天数（及现有行程已有指标）与动作。不展示人数；行程类型中没有该字段。
- 有封面图时仅占右后方 40%，必须有深色遮罩；无图使用地形渐变，不发送额外请求阻塞首屏。
- 返回按钮是带文字的次级按钮；导出、问助手均 44px 以上。
- 小于 768px 变单列，跨分区动作成为底部 sticky action bar，但不得遮挡内容。

#### 文件

- 重构 frontend/src/views/Result.vue 为壳层，目标不超过 350 行。
- 创建 frontend/src/components/result/TripSummaryHero.vue。
- 创建 frontend/src/components/result/ResultSectionNav.vue。
- 创建 frontend/src/components/result/TripActionBar.vue。
- 创建 frontend/src/components/result/ResultStatePanel.vue。
- 创建 frontend/src/composables/useTripPlanState.ts。
- 创建 frontend/src/composables/useTripExport.ts。

### D3. 概览分区

#### 当前问题

- 当前轮播偏视觉演示，信息可扫描性弱；关键操作 hover 才出现。
- Swiper/Coverflow 带来额外依赖与运动，却没有为内容理解服务。
- 行程重点、路线关系和每日安排之间缺少连接。

#### 新设计

概览回答三个问题：去哪里、为什么值得、每天大致怎样走。

    [行程一句话摘要 + 总里程/景点/节奏指标]
             ╲ 路线 SVG ╱
    [Day 1 目的地明信片]—[Day 2]—[Day 3] ...
    [每日速览列表：上午 / 下午 / 晚上]
    [实用提醒：交通、预约、节奏]

- 顶部使用 3 个指标，不超过 4 个；只有后端已有数据才展示，不推导虚假精度。
- 景点改为“路线明信片”scroll-snap 列表，不自动播放：
  - 卡片桌面宽 360px、移动 82vw、图片 4:3。
  - 上方显示 Day/序号，下方标题、地点、停留时间和可见操作。
  - 左右按钮带文字替代名，禁用态明确；键盘可滚动。
- 路线线段连接明信片顶部节点，使用 CSS/SVG 装饰，不能成为唯一的顺序表达。
- 每日速览是结构化列表；移动端折叠，但当天标题和关键地点始终可见。
- 图片 loading 固定 4:3 骨架；error 使用目的地渐变、地图针图标和地点名。
- 移除 Swiper 依赖和相关样式。

#### 动效

- 分区首次进入，路线从左至右绘制 720ms；卡片按 40ms 阶梯进入，最多 6 张。
- 横向滚动使用用户原生滚动，不做滚动劫持或自动居中。
- hover 图片 scale(1.02)，卡片 translateY(-2px)，180ms。

#### 文件

- 重构 frontend/src/components/OverviewAttractionCard.vue，或保留薄兼容层并创建 frontend/src/components/result/overview/RoutePostcard.vue。
- 创建 frontend/src/components/result/overview/OverviewSection.vue。
- 创建 frontend/src/components/result/overview/RoutePostcardRail.vue。
- 创建 frontend/src/components/result/overview/DailyOverviewList.vue。
- 创建 frontend/src/components/result/overview/TravelTipsPanel.vue。

### D4. 预算分区

#### 当前问题

- 22px 左右的图标按钮不可触摸；编辑/删除依赖 prompt/confirm。
- 图表、总额、分类和明细之间层级不足；编辑后反馈不清晰。
- 金额可能因比例动画或重排造成视觉跳动。

#### 新结构

    [总预算 / 已规划支出 / 分类合计]   [编辑预算]
    [分类条形/环形图 7列]             [分类图例 5列]
    [明细表：类别 | 项目 | 金额 | 操作]

- 总额使用 36px 展示数字、tabular-nums；币种和单位 14px。
- 图表优先水平条形图，便于比较；若保留环形图，中心显示总额并提供旁边的数据表。
- 图表颜色固定映射：
  - 交通 sky
  - 住宿 primary
  - 餐饮 accent
  - 门票 sand
  - 购物 #8E79B5（light）/#B7A4E5（dark）
  - 其他 text-muted
- 图表必须有 aria-label 和可访问的同数据表格，不能只靠颜色。
- 明细桌面为表格，移动端为带 label 的列表卡；禁止横向挤压到不可读。
- 编辑使用 BudgetItemModal：
  - 字段：类别、名称、金额，沿用现有字段和校验。
  - 金额输入 inputmode=decimal，错误就地显示。
  - 删除使用 Modal，标题包含条目名，主按钮为危险色。
  - 删除成功后底部显示 6 秒 Undo；撤销仅作用于本地现有编辑逻辑，不新增后端协议。
- 所有编辑按钮至少 44×44px，并有可见文字或 tooltip + aria-label。

#### 状态

- loading：三个指标骨架 + 固定高 280px 图表骨架 + 5 行表格骨架。
- empty：“还没有预算明细”，操作“添加第一笔预算”。
- error：保留最后一次可用数据（若有），顶部显示非阻塞错误条和重试。
- 保存中：弹窗主按钮 loading；关闭/重复提交受控。
- 成功：更新数字以 240ms 颜色过渡，不用数字滚动造成误读。

#### 文件

- 创建 frontend/src/components/result/budget/BudgetSection.vue。
- 创建 frontend/src/components/result/budget/BudgetSummary.vue。
- 创建 frontend/src/components/result/budget/BudgetChart.vue。
- 创建 frontend/src/components/result/budget/BudgetTable.vue。
- 创建 frontend/src/components/result/budget/BudgetItemModal.vue。
- 创建 frontend/src/composables/useBudgetEditor.ts。
- 不使用 window.prompt 或 window.confirm。

### D5. 景点地图分区

#### 当前问题

- 地图加载、缺 Key、SDK 失败可能只留下空白矩形。
- 地点列表与地图选择态缺少强连接；键盘用户缺少等价路线。
- Google→AMap 回退发生在后台，用户不知道当前状态。

#### 新结构

桌面 4:8，移动端列表优先：

    ┌──────── 地点路线 4列 ────────┬──────── 地图 8列 ──────────┐
    │ 1  景点 A  时间/地址          │  标记、路线、地图控件       │
    │ 2  景点 B  时间/地址          │                             │
    │ 3  景点 C  时间/地址          │                             │
    └───────────────────────────────┴─────────────────────────────┘

- 左侧是真实有序列表，每项是 button；包含序号、名称、时间和地址摘要。
- 选中地点使用 3px primary 左边界 + primary-soft 背景，地图标记同步放大 1.12。
- 地图容器桌面最小 560px 高，平板 480px，移动 360px；地图上方保留“列表/地图”分段控件。
- 移动端默认列表，可切到地图；选择地图标记后出现底部地点 sheet。
- 地图下方始终提供“文字路线”，包括顺序和地点信息，这是 SDK 不可用及无障碍用户的等价内容。
- 自定义地图标记使用路线节点语义，选中后不靠颜色单独表达，增加外环和序号。

#### 加载与失败状态

状态必须明确、互斥并有标题：

1. checking-key：“正在检查地图配置”。
2. loading-google：“正在展开 Google 地图”。
3. fallback-amap：“Google 地图暂时不可用，正在切换备用地图”。
4. loading-amap：“正在展开高德地图”。
5. missing-key：“还没有配置可用的地图密钥” + 打开设置按钮。
6. failed：“地图没有成功抵达” + 重试 + 使用文字路线。
7. ready：显示提供方小标签，不遮挡地图法定标识。

使用 AbortController/现有清理机制避免分区离开后更新已卸载组件。地图 SDK 仅进入该分区时加载；5 秒回退规则保持不变。

#### 文件

- 创建 frontend/src/components/result/map/MapSection.vue。
- 创建 frontend/src/components/result/map/RouteStopList.vue。
- 创建 frontend/src/components/result/map/TravelMap.vue。
- 创建 frontend/src/components/result/map/MapStateOverlay.vue。
- 创建 frontend/src/components/result/map/TextRouteFallback.vue。
- 创建 frontend/src/composables/useTravelMap.ts。

### D6. 每日行程分区

#### 当前问题

- 日程内容量大但卡片之间关系弱，容易变成重复白块。
- 天与天、时段与时段的路线逻辑不直观。
- 折叠状态、焦点和滚动定位未形成稳定规则。

#### 新设计

使用纵向路线时间轴。桌面左侧 240px sticky 日目录，右侧内容；移动端日目录变为顶端横向日期条。

    Day 1  抵达与城市初见
      ● 09:00  景点/活动
      │          地点、时长、交通、说明
      ● 12:30  午餐
      │
      ● 15:00  景点/活动

- 每天标题包含 Day、日期、主题、城市和当日强度标签。
- 节点卡按“时间 → 活动名称 → 地点/交通 → 说明/提醒”排序。
- 时间轴线使用 border，不用绝对定位贯穿未知高度。
- 节点类型用图标 + 文字：景点、餐饮、交通、住宿、自由活动；颜色仅做辅助。
- 默认展开当前/第一天；其他天是否折叠沿用数据量策略：少于等于 3 天全展开，大于 3 天仅第一天展开。
- URL 不新增 day 查询要求，但日目录点击需滚动到对应 h3，使用 scroll-margin-top 140px。
- 折叠按钮使用 aria-expanded/aria-controls；折叠后摘要保留景点数、时长和城市。
- “在地图查看”切换到 section=map，并把既有选中地点状态传入前端共享 composable；如果当前架构无法无损共享，只切分区，不改变数据结构。

#### 动效

- 展开/折叠优先使用 CSS grid-template-rows 0fr→1fr，360ms；内容高度很大时直接显示，避免性能抖动。
- 当天首次进入路线 480ms 生长；节点 40ms 阶梯，最多 6 个。
- 目录 active 状态用路线点移动 240ms，不做持续跟随动画。

#### 文件

- 创建 frontend/src/components/result/itinerary/ItinerarySection.vue。
- 创建 frontend/src/components/result/itinerary/DayNavigator.vue。
- 创建 frontend/src/components/result/itinerary/DayTimeline.vue。
- 创建 frontend/src/components/result/itinerary/ItineraryStop.vue。

### D7. 知识图谱 / 灵感图谱分区

#### 当前问题

- ECharts 图谱视觉吸引力强，但节点含义、选择状态和键盘替代不足。
- 图谱可能成为“炫技孤岛”，与实际行程关联弱。
- 小屏密集节点难操作。

#### 新设计

面向用户命名为“灵感图谱”，内部代码和接口仍保留 graph 命名。

    [图谱 / 列表] [节点类型筛选] [重置视图]
    ┌──────────── 图谱 8列 ───────────┬── 详情 4列 ──┐
    │ 目的地—景点—文化—美食关系       │ 选中节点信息  │
    └──────────────────────────────────┴──────────────┘

- 顶部提供“图谱/列表”视图切换。移动端默认列表，用户可选择图谱。
- 节点按现有类型映射固定形状/颜色；未知类型使用中性圆点，不丢弃。
- 节点大小只表达真实数据权重；没有权重时统一大小，禁止随意制造重要性。
- 选中节点：外环 2px + 相邻边加粗；右侧详情显示名称、类型、关联关系和已有描述。
- 点击空白取消选择；Esc 关闭详情；重置视图按钮恢复缩放。
- 列表模式按节点类型分组，每条包含名称和关联数量，是图谱的完整无障碍替代。
- ECharts 容器具备 aria-label，旁边提供可聚焦说明；不声称 canvas 本身完全可访问。
- ECharts 只在进入图谱模式时 dynamic import；ResizeObserver 驱动 resize，卸载时 dispose。

#### 动效

- 图谱首次进入使用 480ms opacity + scale(.99)；不做节点无限漂浮。
- hover 只高亮一度关系，150ms；选择变化 240ms。
- reduced motion 下关闭 ECharts 初始动画与 force layout 动态迭代展示，直接到稳定布局。

#### 文件

- 创建 frontend/src/components/result/graph/KnowledgeGraphSection.vue。
- 创建 frontend/src/components/result/graph/GraphCanvas.vue。
- 创建 frontend/src/components/result/graph/GraphListView.vue。
- 创建 frontend/src/components/result/graph/GraphNodeDetail.vue。
- 创建 frontend/src/composables/useKnowledgeGraph.ts。

### D8. 天气分区

#### 当前问题

- 日期使用 li 承担点击，缺少 button 语义。
- 天气动效可能持续抢占注意力或消耗性能。
- 天气与行程建议分离，信息价值不够直接。

#### 新结构

    [日期按钮轨道：周一 18°/晴 | 周二 16°/雨 | ...]
    [当前天气场景 7列] [对行程的影响 5列]
    [逐日详情表：高低温、降水、风、建议]

- 日期项必须是 button，最小 64×56px；aria-pressed 表示选中。
- 当前天气大卡只运行一个轻量 CSS 场景：
  - 晴：暖色光晕缓慢位移。
  - 多云：两个低透明形状 24s 位移。
  - 雨：最多 8 条 transform 线，且只在卡片可见时。
  - 雪/风等未知：使用静态插画，不新增复杂粒子。
- 动效不是天气信息本身；必须显示文字描述、温度、降水概率、风和日期。
- “对行程的影响”只根据已有天气/行程数据展示已有或确定性规则文案；不要通过前端生成新的业务结论。无法可靠映射时展示中性提示。
- 日期超过 7 天时使用原生横向滚动 + scroll-snap，不自动轮播。
- reduced motion 全部改为静态图形。

#### 状态

- loading：日期轨道骨架 + 大卡骨架。
- empty：“还没有可展示的天气数据”，不伪造默认晴天。
- error：保留行程内容，天气区显示重试，不影响其他分区。

#### 文件

- 创建 frontend/src/components/result/weather/WeatherSection.vue。
- 创建 frontend/src/components/result/weather/WeatherDayRail.vue。
- 创建 frontend/src/components/result/weather/WeatherScene.vue。
- 创建 frontend/src/components/result/weather/WeatherImpact.vue。

### D9. AI 旅行助手

#### 当前问题

- AIChat 以 1260×1100 面板整体 scale(.3) 缩小，容易造成模糊与点击坐标问题。
- 15 个 3D hover 感应区不具备业务价值，增加性能和维护成本。
- 缺少 dialog 语义、焦点管理、发送/生成/失败的清晰状态。
- 部分按钮无有效功能或触摸目标不足。

#### 新设计

- 桌面为右侧 Drawer，宽 min(440px, 100vw)；移动端为全屏底部 Sheet。
- 触发器：
  - 桌面在 TripSummaryHero 中是“问旅行助手”文字按钮。
  - 页面滚动后可显示 48px 浮动节点按钮，但与固定底栏互斥。
  - aria-expanded、aria-controls 完整。
- Drawer 头部：标题、当前行程简述、关闭按钮。
- 消息区：用户消息右侧 primary-soft，助手消息左侧 surface-alt；最大宽度 86%，正文 15px/1.6。
- 建议问题在空对话时显示为真实 button；发送后不一直占空间。
- 输入区：textarea 自动增长 1–5 行；Enter 发送、Shift+Enter 换行，移动端回车行为保持平台习惯。
- 发送按钮 44×44px；空内容或请求中 disabled。
- 生成中使用三个旅程节点跳动，同时 aria-live=polite 播报“助手正在整理建议”。
- 请求失败的消息气泡内显示“重新发送”，保留原输入。
- 长回答保持可选择文本；不把 Markdown 内容作为不安全 HTML 注入。沿用当前渲染策略时必须审查 XSS。
- 打开后焦点进入输入或标题；Tab 被 Drawer 组件圈闭；Esc 关闭；关闭后焦点回触发器。

#### 删除

- 删除所有 3D 感应区域。
- 删除 transform: scale(.3) 方案。
- 删除没有绑定功能的视觉按钮；若业务确实需要，补齐行为后再保留。

#### 文件

- 完整重构 `frontend/src/components/AIChat.vue`。
- 如需拆分，创建 `frontend/src/components/chat/ChatMessage.vue`、`ChatComposer.vue`、`ChatEmptyState.vue`。
- 保留现状请求：AIChat 使用 axios，URL 为 runtime API Base + `/api/chat/ask`，body 字段为 `message`、`trip_plan`、`history`。拆分时不得改字段名，不得擅自重写服务层；若迁入 `api.ts`，必须是等价封装。

### D10. 设置、导出及全局反馈

#### 设置 Drawer

- 现状：设置在 `frontend/src/components/NavBar.vue` 的 `a-modal` 中，加载/保存走 `getRuntimeSettings` / `saveRuntimeSettings`（即 GET/PUT `/api/settings`，并写入上述 localStorage 键）。
- 新设计改为右侧 Drawer，分为外观、语言、服务配置三个 section；不得改变现有设置字段、请求与存储逻辑。
- 外观：主题 system/light/dark；动态 system/reduce/full，使用 RadioGroup。
- 语言沿用现有 i18n 值；更改后即时生效。
- API Base、AMap Key、Google Key 沿用现有字段与存储逻辑；密钥默认 password，不回显完整值。
- 保存按钮具备 idle/saving/saved/error；成功文案“设置已保存”，2 秒后回 idle。
- 加载失败时保留抽屉并显示重试，不直接关闭。

#### 导出

- 仅用户点击时加载 html2canvas。
- 导出过程显示 modal/进度状态：“正在整理行程画布”，允许在安全阶段取消。
- 导出使用固定 light print theme，避免 dark 截图可读性不稳定。
- 导出区域隐藏导航、按钮、AI 浮层和动画，展开需要输出的折叠内容。
- 成功给文件名与完成提示；失败保留页面并给重试。
- 不改变现有导出内容业务范围。

#### 全局反馈

- Toast 只用于非阻塞、已完成反馈；错误必须靠近发生区域并带恢复动作。
- 同一动作不要同时弹 Toast 和行内成功文案。
- 全局网络断开可在导航下方显示 36px 状态条；恢复后自动消失，但不承诺后端未支持的离线编辑。

#### 文件

- 创建 frontend/src/components/settings/SettingsDrawer.vue。
- 创建 frontend/src/components/feedback/AppToastHost.vue（仅在现有 message 能力不足时）。
- 创建 frontend/src/components/feedback/InlineNotice.vue。
- 创建 frontend/src/components/feedback/ContentSkeleton.vue。
- 创建 frontend/src/components/feedback/EmptyJourneyState.vue。
- 创建 frontend/src/components/feedback/ErrorJourneyState.vue。

---

## E. 公共组件与交互规范

### E1. Button

尺寸：

| Size | 高度 | 水平内边距 | 字号 | 图标 |
|---|---:|---:|---:|---:|
| sm | 36px | 12px | 14px | 16px |
| md | 44px | 16px | 14px | 18px |
| lg | 52px | 22px | 16px | 20px |
| icon | 44×44px | 0 | — | 18–20px |

变体：

- primary：primary 底色；用于每个区域唯一主要动作。
- accent：accent-strong 底色；只用于“开始规划”等情绪峰值动作。
- secondary：surface 底 + border；用于返回、筛选、普通动作。
- ghost：透明底；用于导航和低优先级动作。
- danger：error 底或 error 文字；必须搭配明确危险文案。

状态：

| 状态 | 规范 |
|---|---|
| normal | 文本与图标垂直居中，gap 8px |
| hover | translateY(-1px)，180ms；颜色按 token 变化 |
| active | scale(.985)，120ms |
| focus-visible | 3px focus ring + 2px offset |
| disabled | opacity .48，cursor not-allowed；不触发动效 |
| loading | 保留原宽度；左侧节点 loader；aria-disabled=true |
| success | 可短暂显示 check + 原动作完成文案，不改变尺寸 |
| error | 按钮本身不持续变红抖动；在邻近区域解释错误 |

禁止仅图标且无 aria-label 的按钮，禁止把 div/span 当按钮。

### E2. Input、Select、DatePicker、Textarea

- 默认高度 44px，大型规划字段 52px；圆角 radius-md。
- label 在控件上方 8px，14px/600；可选字段显示“可选”，不用省略 label。
- placeholder 使用 text-muted，且不能承载格式要求的唯一说明。
- normal：surface + border；hover：border-strong；focus：primary border + focus ring。
- error：error border + 图标 + 字段下 12–14px 文本；同时 aria-invalid=true。
- disabled：canvas-alt 背景，文字仍满足 4.5:1，说明不可用原因。
- loading Select：右侧节点 loader，保留当前值。
- textarea resize: vertical；聊天输入例外，由内容高度自动增长。
- 日期范围不得只靠颜色表示起止，显示“出发/返程”文字。
- Ant Design 下拉层、日期层、Modal、Drawer 的 z-index 统一定义，不在页面局部随意增加。

### E3. Checkbox、Radio、Chip 与分段控件

- 使用原生 input 或 Ant Design 语义组件，视觉层可自定义但 input 仍可访问。
- Checkbox/Radio 点击区域至少 44px 高；标签本身也触发选择。
- Chip 未选 surface/border；hover primary-soft；选中 primary-soft + 2px primary + check。
- disabled 透明度 .5，不允许点击；只读状态不是 disabled，要以文本摘要呈现。
- 分段控件只用于 2–4 个互斥视图；role/aria-pressed 或 RadioGroup 语义完整。
- 选中滑块 240ms 位移；reduced motion 立即切换。

### E4. Card

只定义三类，禁止每个模块新造一套：

1. ContentCard：信息容器，surface + 1px border + radius-lg，无默认阴影。
2. InteractiveCard：可点击，具备 hover/focus/active，整卡可用 button/link 语义。
3. FeatureCard：目的地/大视觉专用，organic radius + 图片 + 渐变遮罩。

状态：

- loading：骨架保持最终尺寸，避免 CLS。
- empty：不用空 Card 嵌套空 Card；直接使用统一 EmptyState。
- error：保留标题和空间，内部 InlineNotice + retry。
- selected：2px primary 边界 + primary-soft，不能只加阴影。
- disabled：不响应 hover；说明原因。

### E5. Navigation 与 Tabs

- 结果分区导航使用 nav + 可访问的 link/button，不依赖 div click。
- 桌面 sticky top 值为 AppHeader 实际高度 + 12px；移动端可横向滚动，隐藏视觉滚动条但保留滚动能力。
- 当前项 aria-current=page；文字、路线段、对比三重表达。
- 水平导航两侧在可滚动时显示柔和遮罩和可选箭头；箭头 44px。
- Tab 切换不应丢失每个分区合理的内部状态，除非原业务就是重新加载。

### E6. Modal、Drawer、Popover、Tooltip

- 优先复用 Ant Design Vue 的语义、焦点管理和 portal 能力。
- Modal 桌面最大宽 560px；危险确认 440px；移动端 margin 16px。
- Drawer 桌面设置 420px、聊天 440px；移动端 100vw/100dvh。
- 打开后 body 滚动锁定；关闭后焦点回触发器。
- 标题必须由 aria-labelledby 关联，描述由 aria-describedby 关联。
- 关闭按钮始终可见、44×44px；点击遮罩关闭仅用于非破坏流程。
- Tooltip 不承载关键操作说明；触摸设备不能依赖 hover tooltip。
- Popover 中若含表单或多动作，升级为 Drawer/Modal。

### E7. Loading、Empty、Error、Success

#### Loading

- 页面级：摘要骨架 + 分区骨架，不能只放中央 spinner。
- 区域级：ContentSkeleton 形状匹配真实内容。
- 动作级：按钮 loader，禁止页面整体锁死。
- 超过 1 秒显示文字；超过 10 秒提供上下文；具体超时和重试遵循既有业务。
- Skeleton shimmer 使用 background-position，1.6s；reduced motion 使用静态底色。

#### Empty

固定结构：静态路线插画（64–96px）→ 20px 标题 → 最多两行说明 → 一个主要动作 + 可选次要动作。不得使用责备用户的措辞。

#### Error

固定结构：错误点路线插画 → 发生了什么 → 数据是否保留 → 重试/返回。技术堆栈不得展示给生产用户。

#### Success

优先在原位置确认；需要 Toast 时 3–5 秒自动关闭且可手动关闭。不会因为成功自动抢焦点，除非进入新步骤。

### E8. Image、Icon 与数据可视化

- 图片必须指定 width/height 或 aspect-ratio；卡片图默认 4:3，Hero 可 16:9。
- 使用 loading=lazy，但首屏关键视觉可 eager；不得所有图片 eager。
- alt 描述目的地/场景；纯装饰图 alt=""。
- 图片失败使用地点名 + 地形渐变，不显示破图图标。
- 图标统一使用现有 @ant-design/icons-vue 或本项目 SVG；不使用 emoji 作为功能图标。
- 所有数据图表必须提供文字标题、单位、图例和等价表格/列表。
- 图表 tooltip 键盘不可达时，旁边的列表必须提供完整信息。

### E9. 状态矩阵：所有公共组件必须覆盖

| 组件 | normal | hover/focus | active/selected | disabled | loading | empty | error |
|---|---|---|---|---|---|---|---|
| Button | 必须 | 必须 | 必须 | 必须 | 必须 | 不适用 | 邻近提示 |
| Input | 必须 | 必须 | 输入中 | 必须 | 可选 | 空值 | 必须 |
| Select/Date | 必须 | 必须 | 展开/选中 | 必须 | 必须 | 无选项 | 必须 |
| Card | 必须 | 可交互时 | 选择卡必须 | 可选 | 必须 | 统一空态 | 必须 |
| Nav/Tab | 必须 | 必须 | aria-current | 可选 | 不适用 | 不适用 | 不适用 |
| Modal/Drawer | 关闭 | 触发器 focus | 打开/焦点圈闭 | 触发器可禁用 | 保存中 | 内容空态 | 保存错误 |
| Chart/Map | 数据态 | 高亮 | 选中 | 不适用 | 必须 | 必须 | 必须 |
| Chat | 消息态 | 操作反馈 | 会话打开 | 发送禁用 | 生成中 | 建议问题 | 单条重试 |

---

## F. 样式与前端架构落地

### F1. 新样式入口

创建：

- frontend/src/styles/tokens.css：上文颜色、排版、间距、圆角、阴影、z-index、断点相关自定义属性。
- frontend/src/styles/base.css：reset、body、链接、标题、图片、focus-visible、selection、滚动与容器基础。
- frontend/src/styles/motion.css：过渡 class、keyframes、reduced-motion 总开关。
- frontend/src/styles/antd-theme.css：Ant 组件结构性覆盖，限制在 :root/[data-theme]。
- frontend/src/theme/antdTheme.ts：如果当前 Ant 版本支持 ConfigProvider theme token，在此映射同一套 token。
- frontend/src/assets/topographic-lines.svg：低对比、无文本、可重复的等高线资产。

导入顺序固定：

1. tokens.css
2. base.css
3. motion.css
4. antd-theme.css
5. 页面/组件 scoped CSS

禁止继续导入 Paper Kit。迁移结束后删除 frontend/src/styles/global.css 的应用入口；若文件中仍有被业务依赖的少量规则，先迁移到对应新文件，再删除原文件。不得把 8,884 行旧 CSS 整包复制到 legacy.css。

### F2. Token 映射

Ant Design Vue 至少映射：

| Ant token | 项目 token |
|---|---|
| colorPrimary | --color-primary |
| colorInfo | --color-info |
| colorSuccess | --color-success |
| colorWarning | --color-warning |
| colorError | --color-error |
| colorText | --color-text |
| colorTextSecondary | --color-text-muted |
| colorBgBase | --color-canvas |
| colorBgContainer | --color-surface |
| colorBorder | --color-border |
| borderRadius | 16 |
| controlHeight | 44 |
| controlHeightLG | 52 |
| fontSize | 16 |
| motionDurationMid | 0.24s |

主题切换通过 document.documentElement.dataset.theme = light/dark。system 模式监听 matchMedia 变化。首屏在应用挂载前用最小内联脚本或同步初始化确定 data-theme，防止闪烁；脚本只读取 travelai.theme，不执行网络请求。

### F3. 推荐目录

    frontend/src/
      assets/
        topographic-lines.svg
      components/
        layout/
          AppShell.vue
          MobileNavDrawer.vue
        ui/
          AppButton.vue
          AppIconButton.vue
          AppCard.vue
          AppSectionHeader.vue
          AppSegmentedControl.vue
        feedback/
          ContentSkeleton.vue
          InlineNotice.vue
          EmptyJourneyState.vue
          ErrorJourneyState.vue
        landing/
          TripHero.vue
          TripPlannerForm.vue
          CityRouteEditor.vue
          InterestSelector.vue
          PlanningJourney.vue
          TripHistory.vue
        trip/
          TripBrief.vue
        result/
          TripSummaryHero.vue
          ResultSectionNav.vue
          TripActionBar.vue
          ResultStatePanel.vue
          overview/
          budget/
          map/
          itinerary/
          graph/
          weather/
        chat/
          ChatMessage.vue
          ChatComposer.vue
          ChatEmptyState.vue
        settings/
          SettingsDrawer.vue
      composables/
        useTheme.ts
        useMotionPreference.ts
        useTripPlanState.ts
        useBudgetEditor.ts
        useTravelMap.ts
        useKnowledgeGraph.ts
        useTripExport.ts
      styles/
        tokens.css
        base.css
        motion.css
        antd-theme.css
      theme/
        antdTheme.ts

不要求为了目录完整而创建空组件。按阶段创建，但最终职责边界应与此一致。

### F4. Props、事件和数据边界

- 页面负责取数/路由/顶层状态，展示组件通过 typed props 接收数据并 emit 意图。
- 子组件不得重新请求页面已经拥有的数据。
- composable 包装现有逻辑，不发明新的后端 DTO；优先直接复用 frontend/src/types 中现有类型。
- 禁止用 any 快速绕过拆分；未知外部数据用 unknown + type guard。
- UI 展示映射（图标、颜色、自然语言）单独定义为只读映射，未知枚举必须有 fallback。
- 所有计时器、ResizeObserver、地图实例、ECharts 实例、WebSocket 监听在 onBeforeUnmount 清理。
- 路由 section 与内部 activeSection 只有一个事实源，避免 watch 双向循环。

### F5. 依赖决策

#### 保留

- Ant Design Vue：保留无障碍基础组件和现有迁移成本优势。
- ECharts：仅图谱/预算确有数据可视化价值，改为按需异步加载。
- html2canvas：仅用户导出时异步加载。
- Google Maps 与 AMap：保留现有双提供方策略。
- @ant-design/icons-vue：统一功能图标。

#### 移除

- Swiper：概览改为 CSS scroll-snap，可访问性、体积和控制感更好。
- Paper Kit 2 全局样式：与新 token 冲突且体积巨大。
- 远程 Creative Tim 首页背景与重复字体导入。

#### 不新增

- 不新增第二套 UI 框架。
- 不新增 GSAP；当前动效规模用 CSS/Vue/Web Animations 足够。
- 不新增 Pinia；当前跨页状态由已有 storage/route 足够承载。
- 不新增 Web Font 请求，降低中文字体加载和隐私风险。

如果移除依赖会触及 `frontend/package.json` 与 `frontend/package-lock.json`，先用 rg 确认全仓无引用，再删除依赖并在 `frontend/` 按 lockfile 重装；不得仅删除 import 而遗留包，也不得在仍有引用时强删。不得升级无关依赖。

---

## G. Cursor 分阶段实施计划

### 阶段 0：建立基线，不改视觉

操作均在 `frontend/` 执行：

1. 如缺 `node_modules`，使用现有 lockfile 执行 `npm ci`（不升级、不新增、不 `npm audit fix`）。
2. 记录 `npm run type-check` 与 `npm run build`。前端无 lint/test 脚本；不要跑后端测试冒充前端基线。
3. 用 `docs/images/` 现有截图尺寸记录首页与结果六分区。
4. 列出 `frontend/src/views/Landing.vue`、`frontend/src/views/Result.vue`、`frontend/src/components/AIChat.vue` 中所有事件、请求、watch、storage 读写和弹窗，拆分时逐项勾选。

修改文件：无应用源码。允许校正本执行文档。

验证：

- 开发服务器可启动，首页 HTML 能返回。
- 不把后端不可用时的规划失败写成前端缺陷；不伪造规划成功。
- Landing 规划进度依赖 WS；WS 失败后**没有**自动轮询。Result 仅在 session 缓存不可用时用 status 回补。
- 结果六分区现状键为 overview / budget / map / days / knowledge-graph / weather。
- 地图 fallback、聊天、预算编辑、导出都有基线记录。

### 阶段 1：设计 token、主题与全局壳层

创建：

- frontend/src/styles/tokens.css
- frontend/src/styles/base.css
- frontend/src/styles/motion.css
- frontend/src/styles/antd-theme.css
- frontend/src/theme/antdTheme.ts
- frontend/src/assets/topographic-lines.svg
- frontend/src/composables/useTheme.ts
- frontend/src/composables/useMotionPreference.ts
- frontend/src/components/layout/AppShell.vue
- frontend/src/components/layout/MobileNavDrawer.vue

修改：

- frontend/src/main.ts：按固定顺序导入新样式，配置 Ant theme。
- frontend/src/App.vue：AppShell、跳转链接、RouterView。
- frontend/src/components/NavBar.vue：新导航。
- frontend/src/i18n/locales/zh.json、en.json、ja.json：补齐主题、动态、状态文本；三种语言同步，不删除旧键。必要时同步 frontend/src/i18n/index.ts、messages.ts。
- 可选：frontend/index.html 做挂载前 data-theme 防闪，脚本只读 travelai.theme。

此阶段暂不删除 `frontend/src/styles/global.css`，先把新壳层隔离完成，防止一次性回归难定位。

验证：

- light/dark/system 正常并持久化。
- 首屏无明显主题闪烁。
- prefers-reduced-motion 和应用设置均生效。
- 320、768、1024、1440px 下导航不溢出。
- 键盘能跳到 main。
- 类型检查、build 通过。

### 阶段 2：基础 UI 与反馈组件

创建：

- frontend/src/components/ui/AppButton.vue
- frontend/src/components/ui/AppIconButton.vue
- frontend/src/components/ui/AppCard.vue
- frontend/src/components/ui/AppSectionHeader.vue
- frontend/src/components/ui/AppSegmentedControl.vue
- frontend/src/components/feedback/ContentSkeleton.vue
- frontend/src/components/feedback/InlineNotice.vue
- frontend/src/components/feedback/EmptyJourneyState.vue
- frontend/src/components/feedback/ErrorJourneyState.vue
- frontend/src/components/settings/SettingsDrawer.vue

修改：

- 把 NavBar 和设置入口迁移到公共组件。
- 将 Ant Modal/Drawer/Input/Button 外观映射到统一 token。

验证：

- 组件逐一覆盖 E9 状态矩阵。
- focus-visible 清晰，禁用状态不触发。
- Modal/Drawer 焦点圈闭、Esc、返回焦点正确。
- light/dark 均达到文本对比度。
- 类型检查、build 通过。

### 阶段 3：首页完整重构

创建：

- frontend/src/components/landing/TripHero.vue
- frontend/src/components/landing/TripPlannerForm.vue
- frontend/src/components/landing/CityRouteEditor.vue
- frontend/src/components/landing/InterestSelector.vue
- frontend/src/components/landing/PlanningJourney.vue
- frontend/src/components/landing/TripHistory.vue
- frontend/src/components/trip/TripBrief.vue

修改：

- frontend/src/views/Landing.vue：变为编排层，保持现有提交、进度、历史逻辑。
- 必要时把纯 UI 状态映射放入 frontend/src/constants 或局部 readonly map。
- locale 文件（zh / en / ja）补齐自然语言阶段，三种语言同步。

验证：

- 所有原有字段、默认值、校验和接口 payload 完全不变（多城市及停留天数、出发日期、交通、住宿、兴趣、特殊需求）。
- 城市增删、排序、兴趣选择、出发日期、提交均支持键盘。不出现人数、总预算、返程日期等新输入。
- 提交期间不能重复提交；失败后重试遵循原逻辑（重新提交），不新增中止任务。
- WS 失败时给出明确错误，不自动轮询。
- 历史 loading/empty/error/success 完整。
- 320–430px 无横向滚动。
- 类型检查、build 通过。

### 阶段 4：结果壳层与概览

创建：

- frontend/src/components/result/TripSummaryHero.vue
- frontend/src/components/result/ResultSectionNav.vue
- frontend/src/components/result/TripActionBar.vue
- frontend/src/components/result/ResultStatePanel.vue
- frontend/src/components/result/overview/OverviewSection.vue
- frontend/src/components/result/overview/RoutePostcard.vue
- frontend/src/components/result/overview/RoutePostcardRail.vue
- frontend/src/components/result/overview/DailyOverviewList.vue
- frontend/src/components/result/overview/TravelTipsPanel.vue
- frontend/src/composables/useTripPlanState.ts

修改：

- frontend/src/views/Result.vue：先抽壳层和概览，不同时迁移所有分区。
- frontend/src/components/OverviewAttractionCard.vue：转换为兼容层或直接替换引用。
- frontend/src/main.ts 中的 createRouter：不新增路径、不新增 router 目录；只确保 query 导航（section、既有 plan_id）正确。

验证：

- 无 sessionStorage、损坏数据、完整数据三种场景正确。
- ?section=overview 可分享/刷新；非法值回退。
- 用户点击分区写入 history（push）；规范化 URL 用 replace。浏览器前进/后退恢复分区。
- scroll-snap 支持触摸/键盘，不自动轮播。
- 关键操作无需 hover。
- 类型检查、build 通过。
- 预算/地图/每日行程/图谱/天气仍使用 Result.vue 内原实现，本阶段不迁移。

### 阶段 5：结果业务分区逐一迁移

执行顺序固定为预算 → 每日行程 → 天气 → 地图 → 图谱。每迁移一个分区就删除 Result.vue 内对应旧模板、逻辑和样式，不保留两套并行实现。

#### 5.1 预算

创建 budget 目录五个组件与 useBudgetEditor.ts；替换 prompt/confirm。

验证：金额、分类、总额与原数据一致；新增/编辑/删除/撤销；移动列表；图表等价数据表。

#### 5.2 每日行程

创建 itinerary 目录四个组件。

验证：每天、每节点和原页面数据一一对应；折叠 ARIA；日导航定位；移动布局。

#### 5.3 天气

创建 weather 目录四个组件。

验证：日期按钮语义；无数据不伪造；动画可关闭；所有原天气字段保留。

#### 5.4 地图

创建 map 目录五个组件与 useTravelMap.ts；延迟加载 SDK。

验证：Google 成功、5 秒回退 AMap、缺 Key、双失败、离开页面清理、文本路线可用。

#### 5.5 图谱

创建 graph 目录四个组件与 useKnowledgeGraph.ts；延迟加载 ECharts。

验证：图谱/列表数据一致；筛选、选择、重置；resize/dispose；reduced motion。

每个小阶段都必须单独运行类型检查和 build，不能等全部拆完再排错。

### 阶段 6：AI 助手与导出

创建：

- frontend/src/components/chat/ChatMessage.vue
- frontend/src/components/chat/ChatComposer.vue
- frontend/src/components/chat/ChatEmptyState.vue
- frontend/src/composables/useTripExport.ts

修改：

- frontend/src/components/AIChat.vue：重写为 Drawer/Sheet，保留现有 axios 请求与 payload。
- Result 结果壳层：接入 Chat 和 Export 入口。
- 导出相关样式：增加 data-exporting 或 print class。

验证：

- 对话打开/关闭/焦点/键盘/移动端正常。
- 发送、生成、失败、重试完整；请求 payload 不变。
- 无 scale(.3) 与 3D 感应区。
- html2canvas 只在点击导出后进入网络 chunk。
- light/dark 下导出结果均为可读的固定 light 主题。
- 类型检查、build 通过。

### 阶段 7：清理旧系统与依赖

在 rg 确认无引用后：

- 删除 `frontend/src/views/Home.vue`。
- 删除 `frontend/src/styles/global.css` 在 `frontend/src/main.ts` 的入口；迁移完成后删除不再使用的旧 CSS/资产。
- 删除重复字体 import。
- 删除远程 Creative Tim 背景引用。
- 删除 Swiper import、初始化、CSS 和 package 依赖。
- 删除 App.vue 注释旧 header/footer。
- 删除 Result.vue 已迁移的旧 scoped CSS、内联 SVG 和死状态。
- 删除 AIChat 3D 区域与无功能按钮。

目标：

- Result.vue ≤350 行。
- Landing.vue ≤300 行。
- 组件样式不再出现未经说明的硬编码品牌色。
- 不存在 transition: all。
- 不存在没有替代 focus 样式的 outline: none/0。

验证：

- rg 全仓检查旧 class、Swiper、Paper Kit、远程背景、prompt/confirm、transition: all。
- npm install/lockfile 一致。
- 类型检查、build 通过。
- Git diff 不包含后端、接口字段或业务规则变化。

### 阶段 8：最终 QA

浏览器/尺寸：

- Chrome、Edge 最新版。
- 320×568、375×812、430×932、768×1024、1024×768、1440×900、1920×1080。
- light、dark、系统主题；正常动态、reduced motion。

流程：

1. 首次进入 → 完整规划 → 进度 → 结果。
2. 表单校验错误 → 修复 → 提交。
3. WS 中断 → Landing 显示失败并允许按现有方式重新提交；不要期望自动轮询恢复。Result 无缓存时仍可用既有 status 回补。
4. 历史为空/失败/成功 → 打开历史行程。
5. 结果数据缺失/损坏/完整。
6. 六分区切换、刷新、前进后退。
7. 预算增删改与取消。
8. 两家地图、缺 Key 与双失败。
9. 图谱/列表、天气日期与每日行程。
10. 聊天成功/失败/重试。
11. 导出成功/失败。
12. 全流程仅键盘完成，200% 缩放检查。

工程验证：

- 在 `frontend/` 执行 `npm run type-check` 与 `npm run build`。
- 若已有 lint/test，全部执行且通过。前端当前没有这些脚本。
- 构建产物确认 ECharts、地图、html2canvas 为异步 chunk。
- Lighthouse 建议目标：Accessibility ≥95、Best Practices ≥90；Performance 以当前网络环境为基线，重设计不得明显回退。

---

## H. 文件级变更总表

### 必须修改

| 文件 | 修改内容 |
|---|---|
| frontend/src/main.ts | 新样式入口、Ant 主题；路由仍在此文件维护 query |
| frontend/src/App.vue | App 壳层、主题初始化、路由过渡、移除旧注释 |
| frontend/src/components/NavBar.vue | 新全局导航；设置从 Modal 迁出时保持原请求 |
| frontend/src/views/Landing.vue | 拆成编排层，保留现有表单字段与 generateTripPlan 行为 |
| frontend/src/views/Result.vue | 拆成结果壳层，保留数据流；分区 URL 映射 days→itinerary、knowledge-graph→graph |
| frontend/src/components/OverviewAttractionCard.vue | RoutePostcard 化或兼容代理 |
| frontend/src/components/AIChat.vue | Drawer/Sheet 全量重构；axios payload 不变 |
| frontend/src/i18n/locales/zh.json | 新 UI 与状态文案 |
| frontend/src/i18n/locales/en.json | 与中文同步 |
| frontend/src/i18n/locales/ja.json | 与中文同步 |
| frontend/package.json 与 frontend/package-lock.json | 最后确认无引用后移除 Swiper；不新增 UI/动效库 |

### 必须创建

完整创建清单以 F3 目录为准；至少包括四个 style 文件、主题文件、topographic SVG、七个 composable、layout/ui/feedback/landing/result/chat/settings 组件。

### 迁移完成后删除

| 文件/内容 | 前置条件 |
|---|---|
| frontend/src/views/Home.vue | rg 确认无路由和 import |
| frontend/src/styles/global.css 的应用入口及迁完后的无用旧 CSS | 所有仍需规则已迁到 tokens/base/motion/antd-theme 或组件 scoped |
| Swiper 代码、样式和依赖 | 概览 scroll-snap 验证完成 |
| 远程 Creative Tim 背景引用 | CSS/SVG 背景就位 |
| 重复字体 import | 系统字体栈生效 |
| Result.vue 旧分区实现 | 对应新分区回归通过 |
| AIChat 3D sensing areas | 新 Drawer 完成 |

严禁删除现有服务层、类型、接口封装、存储键或后端相关文件。

---

## I. 验收标准

### I1. 生命力风格检查清单

- [ ] light 是“晨光”、dark 是“夜航”，不是简单颜色反相。
- [ ] 全站能看到统一的路线、节点、等高线、日出/天气层视觉母题。
- [ ] 首页、规划进度、概览、每日行程使用同一条“路线叙事”，但没有复制同一组件造成机械重复。
- [ ] 每个视口最多一个持续环境动画。
- [ ] hover 有不超过 2px 的轻浮或 1.02 图片生长，按下有 .985 反馈。
- [ ] 页面/分区过渡有明确方向和因果，不是统一淡入。
- [ ] 加载是有形状、有语义的旅程状态，不是全站旋转圈。
- [ ] 空态和错误态有温度、有明确恢复动作，不是空白或仅“出错了”。
- [ ] 非对称由信息优先级产生，表单和数据表仍对齐整齐。
- [ ] 没有通用 SaaS 式“同尺寸卡片海”。
- [ ] 没有过量胶囊、随机渐变文字、巨大英文水印和装饰性眉题。
- [ ] 动效被克制使用，不妨碍阅读、输入、地图和图表操作。

### I2. 页面与功能

- [ ] / 首页保留原字段：多城市及停留天数、出发日期、交通、住宿、兴趣、特殊需求；校验、提交、历史和生成流程不变。不新增出发地、人数、总预算、返程日期输入。
- [ ] /result 在无数据、损坏数据和完整数据下都有确定结果。
- [ ] URL `section` 使用 overview、budget、map、itinerary、graph、weather，且可分享/刷新；对应现状键 days→itinerary、knowledge-graph→graph。
- [ ] 浏览器前进/后退与分区状态同步。
- [ ] 原后端路径、方法、payload、响应读取和 WS 协议没有变化。Landing 不新增 WS 失败自动轮询。
- [ ] 原 sessionStorage 键 tripPlan、graphData、planId 与 localStorage 键 travelai.runtime.api_base_url、travelai.runtime.amap_web_js_key、travelai.runtime.google_maps_api_key、travelai.user_id、travelai-locale 全部兼容。允许新增 travelai.theme、travelai.motion。
- [ ] Google Maps→5 秒→AMap 的规则保留。
- [ ] 预算不再使用 prompt/confirm，所有编辑值与原逻辑一致。
- [ ] 概览不再依赖自动轮播，关键操作一直可发现。
- [ ] AI 助手不再缩放超大面板，无 3D 感应区。
- [ ] 导出内容完整、固定浅色且不含 UI 操作控件。

### I3. 设计系统一致性

- [ ] 所有颜色来自 tokens.css；数据驱动图片色除外。
- [ ] 字号只使用 12/14/16/18/22/28/36 和规定 Display clamp。
- [ ] 间距只使用 4/8/12/16/24/32/48/64/96。
- [ ] 控件默认高度 44px，主要规划控件 52px。
- [ ] 点击/触摸目标至少 44×44px，间隔至少 8px。
- [ ] 圆角只使用 10/16/24/32/999 和唯一 organic 值。
- [ ] 阴影只使用三层 token，不给所有卡片默认重阴影。
- [ ] 不存在 transition: all。
- [ ] 不存在多个页面自行定义同义主色。
- [ ] Ant 组件与自研组件在颜色、圆角、高度、焦点上统一。

### I4. 可访问性

- [ ] 所有功能可仅用键盘完成。
- [ ] 可见 focus-visible 始终存在；焦点顺序与视觉顺序一致。
- [ ] Modal/Drawer 圈闭焦点、Esc 关闭、关闭后返回触发器。
- [ ] 表单有永久 label、错误关联、必填语义和提交状态。
- [ ] 兴趣使用真实 checkbox；天气日期使用 button。
- [ ] 当前导航使用 aria-current，折叠使用 aria-expanded/controls。
- [ ] 状态变化由 aria-live 适度播报，不重复轰炸。
- [ ] 正文对比度至少 4.5:1，大字至少 3:1；非文字控件边界至少 3:1。
- [ ] 状态不只依赖颜色。
- [ ] 图片有正确 alt 或空 alt，图表有等价列表/表格。
- [ ] 200% 页面缩放无内容丢失；320px 宽无非必要横向滚动。
- [ ] prefers-reduced-motion 生效，应用内也能选择减少动态。
- [ ] 触屏不依赖 hover，Tooltip 不承载必要内容。

### I5. 性能与稳定性

- [ ] 首页不再请求远程装饰背景和重复 Web Font。
- [ ] 图片有尺寸/aspect-ratio、懒加载和失败替代，CLS 可控。
- [ ] ECharts 仅进入图谱/预算需要时加载。
- [ ] 地图 SDK 仅进入地图分区加载。
- [ ] html2canvas 仅点击导出后加载。
- [ ] Swiper 已移除且 lockfile 一致。
- [ ] 环境动画只使用 transform/opacity/background-position，数量受控。
- [ ] 页面不可见时天气/环境动画暂停或由浏览器自然停止。
- [ ] ResizeObserver、地图、图表、WebSocket、timer 均正确清理。
- [ ] loading/empty/error 不改变主体容器尺寸导致大幅跳动。
- [ ] npm run build 与类型检查通过，无新增控制台错误/警告。

### I6. Cursor 完成定义

只有同时满足以下条件才算完成：

1. G 阶段 0–8 均执行并记录验证结果。
2. I1–I5 所有条目完成，无法完成的条目必须在 PR/交付说明中写明原因与风险，不能静默跳过。
3. 与改造前逐页对照，确认业务功能和数据没有丢失。
4. 至少完成一次键盘全流程、一次移动端全流程、一次 reduced-motion 全流程。
5. Result.vue 和 Landing.vue 达到目标职责与规模，不只是把旧模板包一层。
6. Git diff 不包含后端接口、DTO、业务规则变更。

---

## J. 实施前后的最终核对

Cursor 开始编码前先回答并记录（阶段 0 基线）：

- 当前每个接口由哪个组件/composable 调用？见 A1「当前调用方」。
- 每个 storage 键在哪里读、在哪里写？sessionStorage 三键由 Landing 写入、Result 读写；localStorage 五键由 `frontend/src/services/api.ts` 与 `frontend/src/i18n/index.ts` 读写，设置保存经 NavBar。
- Result 六个分区原始数据源：概览/预算/地图/日程/天气来自 `tripPlan`；图谱来自 `graphData`。
- 可能为空：budget、weather_info、graphData、城市列表外的可选字段。WS 状态来自 Landing `onTaskEvent` 的 stage / progress / message。
- 导出：html2canvas 离屏 HTML（日程、餐饮、天气、酒店等）加可选地图截图。地图：Google 优先，5 秒或失败后 AMap。聊天 payload：`{ message, trip_plan, history }`。

Cursor 完成编码后再次回答同样五个问题。两次答案的业务部分必须一致，只允许组件归属和展示方式变化。

最终人工观感应是：用户从首页看到一条尚未出发的路线，规划时看见旅程逐步生长，进入结果后路线变成可探索的概览、每日节点和地图；预算、知识和天气是同一段旅程的不同观察层。界面有空气、有温度、有轻微响应，但内容始终稳定、可读、可操作。
