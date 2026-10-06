# TravelAI 登录与账号隔离执行文档（交给 Cursor）

版本：1.0 / 2026-10-06。项目根目录：`D:\实习日报\TravelAI`。

本文件是实施规格，不代表账号功能已经实现。本轮仅编写文档，不修改应用源码、依赖、数据库或 `.env`。

## 0. 执行方式与完成定义

**必须分阶段执行。每次只完成用户明确指定的一个阶段，验收后停止，等待下一条指令。首次只执行 L0，不得一次实现整份文档。**

每阶段交付：修改文件清单、关键决策/契约对照、实际命令和退出结果、测试证据、未验证项及阻塞。不得把构建通过、模拟 API 或静态截图当作真实账号隔离通过。

保留当前大量未提交的前端改造；不 reset/checkout/覆盖用户修改，不自动 commit/push。不读取或输出 `.env` 的值，不写死管理员密码，不打印登录请求体、Cookie、CSRF token、密码哈希。真实模型调用不属于账号自动测试，使用 stub；如需要付费联调，先获得本次实施的明确授权。

旧重设计任务的“不得改后端”不适用于本功能：真正的登录和账号隔离必须改后端。但本任务只允许增加认证/授权与所有权，不能改变行程算法、预算计算、地图厂商优先级、旅游字段或导出内容。

### 0.1 固定产品范围

- 用户名 + 密码，自助注册；注册成功自动登录。没有邮件/短信依赖。
- 一个账号对应一个服务端用户 UUID；同账号可以多个设备登录，每个设备独立会话。
- **这不是实名制**：不接手机号/实名系统就无法证明一个自然人只注册一个账号。本版承诺的是账号唯一、数据按账号隔离，不能宣传“禁止一人注册多个账号”。
- 游客可以看首页介绍和规划表单；不能生成、看私人历史、进入结果、聊天或导出。
- 两个角色：`user`、`admin`。公开注册只产生 user。管理员仅通过本机维护命令创建，不提供角色提升接口。
- 包含：登录、注册、退出、刷新恢复登录、账号页查看基本资料/修改密码、未登录拦截、过期反馈、跨账号数据隔离。
- 不包含：OAuth、验证码、邮件验证、短信、找回密码邮件、头像上传、收费套餐、完整管理员后台、账号注销、行程共享链接、强制单设备登录。
- 忘记密码：显示“请联系部署维护者重置密码”，不放无功能链接；维护者先核实身份，再通过本机命令重置并撤销全部会话。不向访客暴露用户列表。
- 行程生成记录和偏好归账号；聊天仍是当前浏览器当前计划的临时会话；日程/预算编辑仍是前端本地，不新增服务器编辑保存。换设备能恢复已生成的原计划，但不能承诺同步本地修改/聊天。

## 1. 已核实的项目现状

| 位置 | 现状 | 本任务影响 |
|---|---|---|
| `frontend/src/main.ts` | Vue Router 在此创建，只有 `/`、`/result`，页面懒加载 | 抽到新 router 文件并加认证路由/守卫；不能保留第二个 Router |
| `frontend/src/services/api.ts` | axios 实例动态读取 API 地址，未设认证；`getOrCreateUserId()` 生成浏览器匿名 ID | 停止信任匿名 ID，统一 Cookie/CSRF/401 处理 |
| 同上 | POST plan 带浏览器 user_id；memory 接口带 user_id query | 后端从会话取身份，不能由客户端决定 |
| `backend/app/api/routes/trip.py` | JobStore + `backend/data/trip_tasks/*.json`；history 扫描全部文件；status/WS 按任务 ID 读取 | 创建/持久化 owner；history/status/WS 全部做所有权检查 |
| `backend/app/core/job_store.py` | 单实例内存任务缓存，有 TTL；磁盘回读 | 缓存仍需 owner 校验；不能只保护磁盘分支 |
| `backend/app/api/routes/memory_routes.py` | list/add/delete/clear 接受任意 user_id | 强制绑定会话用户；包括记忆模块关闭分支 |
| `backend/app/memory/sqlite_store.py` | 偏好存储按 user_id 分区，可选 SQLite | 保留存储语义，新用户使用服务端 UUID |
| `backend/app/api/routes/settings.py` | GET/PUT 是全局运行配置，重置共享模型/地图实例 | 必须仅 admin；不是每个用户的私有设置 |
| `frontend/src/components/AIChat.vue` | 直接 axios POST，绕过统一实例 | 必须接共享认证客户端 |
| `useAttractionPhotos.ts` | fetch + 图片代理 URL | Cookie/401 和跨域图片加载必须补齐 |
| `useTravelMap.ts` | 地图缺 Google Key 时读取完整 settings | 普通用户改读只含公开浏览器配置的 client-config |
| `useTripPlanState.ts` | 优先 session 计划，按 planSourceKey 隔离计划 | 增加账户边界，不能在确认身份/owner 前显示缓存 |
| `Landing.vue` / `Result.vue` | 直接写 session 三键 | 统一经过 account-scoped storage helper |
| `AppShell.vue` | 唯一 NavBar、main、背景、主题 provider | 登录页复用壳层；不能再叠导航/main/背景 |
| 后端依赖 | 已有 aiosqlite，无密码散列库 | 仅新增 argon2-cffi；不引入 JWT/Redis/ORM |
| 后端测试 | pytest + TestClient，已有外部服务 stub 与临时目录 | 加真实认证测试，不整体 override 身份绕过授权 |

现有 `travelai.user_id` **不是认证凭证**；UUID 难猜也不能替代授权。当前接口和历史文件没有可靠账号 owner，这些风险必须同时解决。

## 2. 技术方案（不要自行替换）

### 2.1 后端会话 + HttpOnly Cookie

选用服务端 opaque session，不用 JWT。理由：本项目是 FastAPI 单实例 + SQLite/文件存储，服务端会话可以立即退出/撤销，避免浏览器 localStorage 中存 access/refresh token。

- cookie 名 `travelai_session`；值为 `secrets.token_urlsafe(32)`，数据库只存 SHA-256 摘要。
- `HttpOnly=true`、`SameSite=Lax`、`Path=/`、无 Domain（host-only）。生产 `Secure=true`；本地 HTTP 才允许 false。
- 普通登录：绝对有效期 7 天，闲置超过 24 小时失效；不做“记住我”复选框。每次有效认证更新 last_seen，频率限制为最多每 5 分钟持久化一次。
- 预登录会话最长 30 分钟，无 user_id，不具备访问业务 API 的权限。
- 登录/注册成功轮换 session ID 和 CSRF token，撤销当前预登录/旧会话；不能将匿名 session 原样升级，以防 session fixation。
- 用户被禁用、会话被撤销、绝对/闲置过期均返回 401。
- 修改密码/维护命令重置密码：撤销该用户所有会话；当前用户也重新登录，不偷偷保留旧 cookie。
- DB 与 Cookie 期限同时生效；不能仅看 cookie 是否存在。启动/定时清除过期 session/rate-limit 行，不删除账号或行程。
- 不建立 AUTH_ENABLED=false 的匿名绕过模式；测试使用真实测试账号。

### 2.2 CSRF 与 Origin

Cookie 会自动随浏览器发送，所以 CSRF 是必做项，不能只加 withCredentials。

1. `GET /api/auth/csrf`：有效现有会话返回其 CSRF；没有会话时创建预登录会话并 Set-Cookie，返回 `{csrf_token}`。
2. 客户端 token 只存在内存。数据库可存随机 CSRF token 原值（非 session bearer）；不记录到日志。
3. 所有 POST/PUT/PATCH/DELETE 必须提供 `X-CSRF-Token`，后端用 constant-time compare 与该 cookie 对应记录比较；登录/注册也如此。
4. 浏览器写请求还必须有严格允许的 `Origin`，与配置的前端 origin 完全匹配；没有 Origin/不允许 Origin 返回 403。CLI/TestClient 也显式提供 Origin，不设置“本地免检”。
5. GET 无副作用；`/csrf` 只创建低权限短期会话，限流。跨域 Origin 若存在且不在白名单，不能返回 token；无 Origin 的 GET 不允许写业务数据。
6. CORS 仅显式 origin + allow_credentials，绝不能 `*`。允许的请求头包括 Content-Type、X-CSRF-Token；OPTIONS 不要求登录。
7. CSRF 不匹配返回 `403/CSRF_INVALID`，客户端刷新 token 后提示用户重试；**不自动重放规划、聊天、注册等写请求**。
8. 登录/注册密码校验完成后，事务内再次确认预登录 session 未被撤销；不能用退出前已验证的旧预登录身份签发迟到会话。

### 2.3 开发与部署地址约束

- 本地优先使用前端 `http://localhost:5173` + 后端 `http://localhost:8000`，同 host 不同端口，是 same-site；CORS 仍要允许 5173。
- 不混用 `127.0.0.1` 前端和 `localhost` 后端来测试 Cookie，否则 same-site 策略会造成看似登录成功却持续 401。若选择 127，两端都统一为 127。
- 生产同源 HTTPS，前端 API 使用相对 `/api`，WS 使用同 origin 的 wss；由现有反向代理/后端 SPA 提供路由 fallback。
- 不通过放宽为 SameSite=None 或禁用 CSRF 解决本地地址问题。真正跨站部署属于单独方案，本版不支持。
- 在 `backend/app/config.py` 增加 `AUTH_DB_PATH`、`AUTH_COOKIE_SECURE`、`AUTH_ALLOWED_ORIGINS`、`AUTH_SESSION_DAYS`（默认 7）、`AUTH_IDLE_HOURS`（默认 24）、`AUTH_REGISTRATION_ENABLED`（默认 true）；默认 auth origins 使用现有 CORS 的明确列表。
- production 环境配置 secure=false 或非 HTTPS 外部 origin 时启动 fail-closed，给出无密钥的配置错误。
- 不改现有模型/地图/XHS 配置值；新增非密钥配置只写示例/部署文档。实际 `.env` 调整先列出必要项请用户确认。
- 成员不能在页面随意修改 API base URL；共享客户端只向固定部署 API origin 发送 cookie/CSRF。管理员的本地调试地址变更仅允许预配置白名单，变更必须清会话 UI 并重新 bootstrap，禁止带凭证跳任意域名。

### 2.4 密码与账号规则

- username：trim 后只允许 ASCII `[a-zA-Z0-9_]{3,32}`，统一 lower-case 存储；登录大小写不敏感。展示名称与用户名分开。
- display_name：可选，trim 后 1–40 Unicode 字符；为空使用用户名；仅按文本插值显示，不支持 HTML。
- password：12–128 Unicode code points，UTF-8 长度≤512 bytes；允许空格、粘贴、密码管理器；**不得 trim/截断/转小写**。不要求强制大小写/符号组合，不作真假安全强度打分。
- 前端计数字符用 `Array.from(value).length`，UTF-8 长度用 TextEncoder；后端 len/encode 同步规则。确认密码只在前端，不能持久化。
- argon2-cffi，Argon2id：memory_cost=65536 KiB、time_cost=3、parallelism=1；随机 salt 由库生成，保存完整编码 hash。验证后按库 needs_rehash 升级。
- 哈希/验证放线程池，限制最多 2 个并发，避免阻塞 async event loop 或堆叠内存。未知用户名也验证一次固定 dummy hash，避免明显时序差。
- 密码错误、账号不存在、禁用：相同 `401/AUTH_INVALID_CREDENTIALS`，文案“用户名或密码不正确”，不区分用户是否存在。
- 注册重名 `409/AUTH_USERNAME_UNAVAILABLE`。这是本版明确的用户名可用性信息，不承诺防止用户名枚举；无邮件地址泄漏。
- 注册 body 禁止 `role`、`is_admin`、`id` 等额外字段；服务端默认 user，绝不能信客户端字段。
- 请求体大小上限 1MiB（含既有聊天上下文），auth body 上限 8KiB；错误不回显输入。

### 2.5 限流与费用边界

SQLite 中事务性限流，不能重启即清空；不硬锁账号导致永久拒绝服务。

| 操作 | 固定窗口默认限制 | 返回 |
|---|---|---|
| 登录尝试 | 每 username 5 次/15min；每 IP 20 次/15min | 429 + Retry-After 秒 |
| 注册 | 每 IP 5 次/小时 | 同上 |
| 获取预登录 CSRF | 每 IP 60 次/分钟 | 同上 |
| 修改密码 | 每账号 5 次/15min | 同上 |
| 规划提交 | 每账号 10 次/小时，最多 2 个在途任务 | 429，不创建新任务 |
| 聊天 | 每账号 60 次/小时 | 429，不调用模型 |

登录成功清该 username 失败计数但不清 IP 总计数。认证限流在 Argon2 前执行；已登录业务限流在调用付费服务之前执行。保存窗口/计数，限流键使用摘要，不日志输出 IP/用户名/密码；不信任未配置代理的 X-Forwarded-For。

这只是基础滥用保护，不是付费配额系统。公开注册并不能阻止多账号滥用；公网部署前由维护者确认允许注册范围，可通过 AUTH_REGISTRATION_ENABLED 关闭注册并用本机命令创建账号。功能禁止注册时 UI 与 API 同步，不用仅隐藏按钮。

## 3. 数据库、所有权与旧数据

### 3.1 Auth SQLite（新增，不替换 memory.db）

默认绝对路径 `backend/data/auth/auth.sqlite3`，不能随 shell cwd 漂移。aiosqlite、参数化 SQL、foreign_keys=ON、busy_timeout=5000、WAL。添加版本化迁移 `001_auth.sql` 和 schema_migrations；初始化进 lifespan，不在 route import 时重复建库。

| 表 | 字段/约束 |
|---|---|
| users | id TEXT UUID PK；username TEXT UNIQUE NOT NULL；display_name TEXT NOT NULL；password_hash TEXT NOT NULL；role TEXT CHECK(user/admin)；is_active INTEGER；created_at/updated_at INTEGER UTC 秒 |
| auth_sessions | session_hash TEXT PK；user_id TEXT NULL FK users(id)；csrf_token TEXT NOT NULL；created_at/expires_at/last_seen_at INTEGER；revoked_at INTEGER NULL；user_id 为 NULL 仅预登录 |
| auth_rate_limits | scope TEXT、key_hash TEXT、window_start INTEGER 复合主键；count INTEGER；expires_at INTEGER |
| schema_migrations | version INTEGER PK；applied_at INTEGER |

注册 username 插入与 session 创建使用事务，唯一冲突明确捕获；并发注册同名只有一个成功。管理员密码修改/禁用与 session 撤销同事务。不要用字符串拼 SQL；SQLite busy 返回可重试 503，不暴露 DB 路径。

新增 `.gitignore`：仅忽略 `backend/data/auth/` 的运行库/备份（或整个此运行目录），含 sqlite/WAL/SHM，不能误忽略代码 migrations。数据库/备份按 OS 权限只允许部署账户读取。

### 3.2 任务所有权

继续使用现有 JSON 任务存储，本版不把行程迁移到新数据库。

- 新任务内部新增 `owner_user_id`，来自 current_user.id；写入 `_create_task_state`、`_persist_task_state`、`_normalize_loaded_task`，所有读写/重启/内存路径都保留。
- owner 是任务元数据，不放入 TripPlan 内容，不让客户端提交/修改，也不暴露在 WS/result DTO。
- 内存 `_get_task` 与磁盘返回都必须经过 `_require_owned_task(task_id,current_user)`。访问他人任务和不存在任务统一 404。
- history 必须先按 owner 过滤，再判断 completed、排序、limit；否则别人的记录会占据 limit 或泄露摘要。
- task id 使用新的 UUID hex 32 字符；接受旧 8 位 hex 和新 32 位 hex，路径读取前校验，拒绝 `..`、斜杠、任意字符串，避免路径穿越。
- 请求中 legacy `user_id` 可暂时兼容接收，但后端覆盖为 current_user.id 后才调用 agent、记忆读取与隐式偏好写入。前端不再发送该字段。
- 创建任务应确认初次 owner 持久化成功，失败返回 503，不能返回“已提交”却只有无法恢复的内存任务。现有后续持久化流程保留但不得漏 owner。
- 后台 task 捕获固定 owner，绝不能回头读取“当前全局登录用户”；退出后任务可继续完成，记录仍归原账号。
- admin 也不自动获得所有人的业务行程浏览权限；业务所有权仍只允许本人。

### 3.3 旧匿名数据策略

- 无 owner 的历史 JSON 和旧匿名偏好 **保留原文件/记录，默认不出现在任何新账号历史中**。
- 不依据 request_payload.user_id、浏览器 travelai.user_id 或“知道 plan_id”自动认领；这些都是可伪造信息。
- 不把所有旧数据自动送给第一个注册用户/管理员。
- 提供本机维护命令 `assign_legacy_trip.py --task-id ... --username ... --dry-run`，只列 ID/拟归属，不输出行程正文或密钥；真正执行前必须有用户明确授权并做独立备份。
- 仅认领指定 owner 缺失的文件；已有 owner 拒绝改归属；原子替换并记录无敏感内容的审计结果。备份路径不能覆盖原文件。
- 偏好旧记录不自动迁移；以后需要迁移必须单独确认源匿名 ID 与目标账户，不能由网页登录接口认领。
- L0 可以统计旧文件数量与 owner 有/无，不读取报告中的行程/用户私密字段；本次实现测试不对真实旧数据执行归属命令。

## 4. 后端 API 契约

统一新 auth JSON：成功 `{success:true,data:...}`；失败 `{success:false,error_code,message,detail:null}`，字段校验额外 `errors:[{field,code}]`。前端按 error_code 做三语，不依赖服务器自然语言。不得回显密码/哈希/token/输入。204 不返回 JSON。

公开用户对象：`{id,username,display_name,role,created_at}`；created_at 为 ISO8601 UTC；不含 hash、IP 或其他人的信息。

| 方法/路径 | 输入 | 成功 | 权限 |
|---|---|---|---|
| GET `/api/auth/csrf` | 无 | 200 data `{csrf_token}`；必要时预登录 cookie | 公开/限流 |
| GET `/api/auth/options` | 无 | 200 data `{registration_enabled}` | 公开，无服务密钥 |
| POST `/api/auth/register` | `{username,display_name?,password}` | 201 data `{user,csrf_token}` + 新 cookie | 预登录 CSRF/Origin，注册开启 |
| POST `/api/auth/login` | `{username,password}` | 200 data `{user,csrf_token}` + 新 cookie | CSRF/Origin |
| GET `/api/auth/me` | cookie | 200 data `{user,csrf_token}` | 当前有效用户，未登录 401 |
| POST `/api/auth/logout` | 空 JSON | 204，撤销当前 session + 清 cookie | CSRF/Origin；有效预登录也可撤销 |
| POST `/api/auth/change-password` | `{current_password,new_password}` | 204，撤销全部 session + 清 cookie | 当前用户 + CSRF/Origin |
| GET `/api/client-config` | cookie | 200 data `{amap_web_js_key,google_maps_api_key}` | 已登录；只含浏览器 SDK 所需公开 Key |

其他 auth 错误：422 AUTH_VALIDATION_ERROR，403 CSRF_INVALID/ORIGIN_FORBIDDEN/AUTH_REGISTRATION_DISABLED，429 AUTH_RATE_LIMITED，503 AUTH_SERVICE_UNAVAILABLE。普通业务未登录使用 401 AUTH_REQUIRED；admin 不足 403 AUTH_FORBIDDEN；不向用户暴露角色校验内部细节。

管理员 GET/PUT `/api/settings` 保留原字段与后端 masked secret 行为，但加 require_admin；PUT 还加 CSRF。浏览器 SDK Key 本来需要前端，client-config 可以返回；LLM key、XHS Cookie、高德 Web 服务 Key、代理地址/模型服务地址均不进入 client-config。

### 4.1 接口保护矩阵（不能漏掉分支）

| 接口 | 必须实施 |
|---|---|
| `/health`、静态 assets、SPA 页面 | 公开；不读私人缓存；OPTIONS 公开 |
| `/api/trip/health`、`/api/map/health` | 已登录，避免游客触发外部服务初始化/泄露配置；运维使用公开 /health |
| POST `/api/trip/plan` | current_user + CSRF + account rate limit；owner 服务端赋值 |
| GET `/api/trip/history` | current_user；只返回本人 completed |
| GET `/api/trip/status/{task_id}` | current_user + task owner；别人的处理/失败/完成均 404 |
| WS `/api/trip/ws/{task_id}` | Cookie 会话 + 严格 Origin + task owner，见下节 |
| POST `/api/chat/ask` | current_user + CSRF + rate limit；保留 message/trip_plan/history 契约 |
| `/api/memory/list/add-explicit/item/clear` | current_user；legacy user_id 不可信，统一绑定本人；写操作 CSRF |
| `/api/settings` GET/PUT | admin；PUT CSRF；普通用户不能调用/读取 |
| `/api/client-config` | current_user；严格字段白名单 |
| `/api/map/poi/weather/route` | current_user；POST route CSRF；不改变路线字段 |
| GET `/api/poi/detail/{poi_id}`、`/api/poi/search`、`/api/poi/photo`、`/api/poi/image` | current_user；图像不含私有行程，但接口需登录防滥用；保留现有 XHS URL 白名单 |

Chat 目前仅处理客户端提交的行程文本、不按 ID 读取服务器记录，所以本版只加身份、CSRF、限流；不能假装检查了客户端文本的归属，也不新加 plan_id 改变本地编辑聊天逻辑。测试需证明无法通过 history/status/WS 获得别人服务器行程再交给聊天。

### 4.2 WebSocket（HTTP 登录守卫不能替代）

- 浏览器 WebSocket 自动发送匹配 host/path 的 cookie；不在 URL 放 session/CSRF/token，不新增 localStorage token。
- 连接前校验 Origin（必须存在且允许）、会话、task owner。无权时在握手拒绝；若所用 Starlette 测试/代理必须 accept 后 close，则只能发送关闭码（4401 未登录、4404 不可用），**不能先发 task 快照/错误正文**。
- 验证通过才 append queue/send snapshot。user_id 固定，不能接受 query impersonation。
- 等待队列使用最多 15 秒超时唤醒检查 session；每次发送事件前也检查会话有效性。退出/改密码撤销会话后≤15秒关闭旧 WS。队列 finally 移除、任务继续服务原 owner。
- Origin 错误拒绝，不靠 CORS（CORS 不保护 WS）。不能给账号增加 WS 失败自动轮询/重复创建任务。
- 前端 4401 触发身份重新确认/登录提示；404 式关闭显示“行程不存在或无权访问”。普通网络错误保持原业务失败/恢复规则，不一律误判退出。

### 4.3 日志与异常红线

`main.py` 现有 validation handler 会打印 `exc.errors()`，其中可能带密码 input，必须按 auth 路径单独净化：只保留字段名/类型错误码，日志不含 input/ctx/body。error response 同样不含 input。

禁止记录 Cookie、Set-Cookie、CSRF、Authorization、password、hash；不 stringify 整个 axios error/config，不把登录表单放 URL/query、存储或截图。新增 auth 路径/匿名 options/csrf 禁缓存；所有身份/历史/状态响应 `Cache-Control:no-store`，图片改 `private`，不由公共 CDN 缓存带账号请求。

## 5. 前端状态与账号边界

### 5.1 文件与职责

新增以下模块，名称固定；使用 Vue 模块级共享状态，不为了登录引入 Pinia。

| 新文件 | 职责 |
|---|---|
| `frontend/src/router/index.ts` | 唯一 router，routes/guard、安全 redirect、afterEach 焦点 |
| `frontend/src/router/meta.d.ts` | guestOnly/requiresAuth 路由 meta 类型 |
| `frontend/src/services/httpClient.ts` | axios Cookie/CSRF、超时、认证事件、authEpoch 请求标签 |
| `frontend/src/services/authApi.ts` | auth 接口薄封装，与业务 API 无循环依赖 |
| `frontend/src/composables/useAuth.ts` | user/status/bootstrap/login/register/logout/invalidations |
| `frontend/src/auth/accountBoundary.ts` | authEpoch、所有账户私有状态的同步失效事件；不 import router |
| `frontend/src/auth/planStorage.ts` | session owner 验证/读写/清理的唯一入口 |
| `frontend/src/types/auth.ts` | User、AuthStatus、auth payload/response/error 类型 |
| `frontend/src/views/Login.vue` / `Register.vue` / `Account.vue` | 页面编排，不处理 Cookie 原文 |
| `frontend/src/components/auth/AuthScenicPanel.vue` | 本地路线插图/品牌说明，无外部请求 |
| `frontend/src/components/auth/AuthFormFrame.vue` | 标题/表单/错误摘要/次操作；不创造第二套 main |
| `frontend/src/components/auth/PasswordField.vue` | label、显示密码、autocomplete、错误关联 |
| `frontend/src/components/auth/AccountMenu.vue` | 用户名、账号页、退出；管理员配置入口 |

修改 `main.ts` 引用新 router；旧 routes 删除。AppShell/主题/语言沿用，只有导航按身份分支。UI 用现有 Ant Form/Input、AppButton、InlineNotice、ContentSkeleton；不新增 UI/动画/表单库。

### 5.2 useAuth 状态机

`status = unknown | checking | authenticated | guest | unavailable`，`user:User|null`、内存 csrfToken、authEpoch 整数、bootstrapPromise。

- bootstrap 只调用 `/me`，并发守卫/组件共享一个 Promise；200 authenticated，401 guest，网络/5xx unavailable。不能把后端故障当作密码错误/游客退出。
- guest 到登录页面后请求 `/csrf` 与 `/options`。已有 authenticated 直接跳安全 redirect 或 `/`。
- bootstrap 请求≤10秒，失败提供“重试连接”，不无限 spinner/重定向循环。
- 任何账号变更/退出/认证失效先同步递增 authEpoch、发失效事件、清私有缓存，然后切换用户或路由。登录表单提交时不得并发发送第二次 auth 写请求。
- 账号 API 请求有独立 15 秒超时；不把旅行生成业务客户端原有 timeout:0 改为 15 秒。
- 401：排除预期 `/me` 未登录与登录失败；业务 401 先冻结私人视图，单次 `/me` 确认身份。如果账户变了，先清边界再采用新用户。若仍是同账号但某业务 401，报告该操作失败，不重复全局退出。
- 原始 error status/code 必须能传到统一层，不被业务 catch 包成无信息 Error；403/404/429/网络错误不触发登录跳转。
- 所有请求捕获启动时 authEpoch；返回后 epoch 变更的响应/错误不更新 UI/storage。不能只依靠组件卸载。axios shared client 不 import useAuth，使用回调/事件接线防循环。

### 5.3 路由、首页与安全 redirect

| 路由 | 行为 |
|---|---|
| `/` | 公开说明/表单；未登录历史区显示登录邀请，不调用 history；提交在字段合法后再去登录 |
| `/login` | guestOnly，支持安全 redirect；有过期提示但不泄露原计划内容 |
| `/register` | guestOnly；关闭注册时显示维护者联系说明，不显示无效表单 |
| `/account` | requiresAuth；显示用户名/显示名/创建时间、修改密码，不显示全站密钥 |
| `/result` | requiresAuth；保留 plan_id/section 与前进后退语义 |

redirect 只允许 Vue Router 内部 `/`、`/result`、`/account` 的路径，query 类型/长度校验，总长≤2048；拒绝 `//`、协议、反斜杠、控制字符及 login/register 自循环。保留合法 plan_id/section，不允许外部 URL/open redirect。用 router.resolve 验证匹配路径后 router.replace，不能 window.location=用户输入。

游客提交后返回首页：保留当前表单在内存或以 userId=null 的短期草稿 helper（10min）中，**不包含密码/任何已有私人计划**；登录回来恢复输入但不自动提交/消费模型。最简单实现是模块内存草稿，刷新丢失可接受，UI说明。登录到别人 plan_id 后后端 404，不能改为展示缓存计划。

### 5.4 sessionStorage 与缓存

- 保留既有三键 `tripPlan/graphData/planId`，新增 `travelai.planOwnerId`。只能由 planStorage helper 写/读，字段格式不变。
- bootstrap 身份确认前不读私人缓存。owner 缺失或不等于 user.id，立即删除三键和 owner；老版本匿名缓存不能按“当前账号”自动加 owner。
- 即使 owner 匹配，结果首次恢复仍必须先 GET status 验证服务器所有权，再允许采用本地编辑快照。404/401 时清缓存，绝不能先渲染旧内容再检查。无 planId 的匿名缓存不作为已登录结果使用。
- 本地编辑缓存保留只限同账号且服务器 task 有权限；服务端返回原生成计划与本地编辑的选择明确，避免覆盖同账号已保存的本地修改。
- `Landing.vue`、`Result.vue`、`useTripPlanState` 的每个直接读写都迁到 helper；搜索其余预算、编辑与导出相关写入，不遗漏旧快捷路径。
- authBoundary 清空聊天、照片/blob、历史列表、预算撤销、编辑快照、图谱偏好、地图实例/SDK业务引用、导出任务/离屏文档。保留 theme/motion/locale 三个外观偏好。
- `planSourceKey` 扩展为 `user.id + ':' + adoptionSerial`；退出/切换开始为空，保留原 hydration generation。账号切换先 discardEdit，不 cancelEdit 回滚 A 的快照到 B。
- 停止使用/发送 travelai.user_id；可以仅删除此旧匿名键，但不以此清除服务器旧偏好/行程。
- 后端所有权是安全边界；前端 owner 键只是缓存防串号机制，可被 DevTools 改写，不能据此授权。

### 5.5 Cookie、图片、地图与聊天接线

- 所有业务 axios 走 httpClient，`withCredentials:true`；写操作加内存 csrf header，仅发给允许的 API origin。禁止在 localhost 与 127 分别创建两套不一致登录状态。
- AIChat 改共享客户端，body/history/reply 保持现有，加入 authEpoch 与旧 requestSeq 双检查。
- fetch `/api/poi/photo` 必须 credentials:'include' 或改共享 axios；不要只修主 api.ts。
- 受保护图片不能假定 `img crossorigin=anonymous` 会携带跨域 cookie。统一由共享 client `responseType:'blob'` 获取 `/api/poi/image`，创建 object URL 给图片/导出；并发≤4，失败用现有占位。
- `image_url` 原旅游字段不回写成 blob URL；blob 是展示映射，导出准备读取同一映射并等待加载。切计划/账号/卸载先使导出任务失效，再 revoke blob URL；临时失败也释放。
- 保留原 XHS URL 白名单代理，不改成任意 URL 代理、不往 img URL 拼 session token。后端图片响应 private cache；不要缓存鉴权 401为“永久无图”。
- useTravelMap 不再为普通用户 GET `/api/settings`，改 GET `/api/client-config`。公开浏览器 Key 可以存在内存；账号切换清读取缓存，不在 config 中泄漏服务端 Key。
- 地图缺 Key 时：admin 可打开现有设置 Drawer；user 显示“地图暂不可用，请联系维护者”+文字路线，不提供全局密钥输入。天气/预算/图谱仍可用。
- 退出不能只是 router.push：关闭 WS、作废 xhr结果、取消导出（渲染不能真 abort，但不能再下载）、卸载地图/图表；后端任务是否继续与前端退出分开。

### 5.6 跨标签页与退出失败

- BroadcastChannel `travelai.auth`，发送不带凭证的 `{type:'auth-changed'}`；不广播行程/user对象/password/session/token。无 BroadcastChannel 用 localStorage `travelai.auth.event` 时间戳随机nonce事件，不能存登录token。
- 收到事件立即冻结/清账户 UI，再请求 `/me` 获得真实新身份；不信任消息声称的 userId。窗口 focus/visibility 重新确认会话，定时可每60s一次，仅可见窗口执行。
- 同一浏览器 cookie 会在 tabs 共享，不能同时宣称 Tab A 登录 A、Tab B 登录 B：B 登录后 A tab 必须失效/更新为 B，并清 A 的内存/session。
- auth 请求串行；测试登录/退出网络延迟与跨 tab 竞态。客户端丢弃旧 payload不能代替服务端撤销 session，也不能阻止浏览器应用迟到 Set-Cookie；必须复核 `/me`。
- 退出点击后立刻屏蔽私人内容；只有服务端204或确认会话已失效才能显示“已退出”。网络失败进入“退出未完成，请重试”遮罩/安全状态，不能声称 HttpOnly cookie 已删除；不自动后台发规划/聊天。
- 即使网断，清本地私人缓存；恢复后优先完成退出/确认，再开放业务。修改密码失败不清有效会话，成功必须重新登录。

## 6. 登录/注册/账号页设计规范

采用现有 Living Atlas，不生成另一套网站。设计母题：出发前的“旅行通行卡”，左侧是一条尚未出发的路线，右侧为清晰的登录表单；不用城市大图、广告轮播、假用户评价或随机渐变字。

UI/UX Pro Max 搜索的 Organic Biophilic 有机曲线方向适用；搜索返回的营销 testimonials、远程字体和新灰色板不适合本项目，因此**不采纳**。使用现有 token 和系统字体，保留身份感且不增加远程依赖。

### 6.1 布局与量化值

| 项目 | 固定规格 |
|---|---|
| 壳层 | 唯一 AppShell；72px 顶栏；沿用唯一背景光晕/本地等高线 |
| ≥1024 | 页面 max-width1088px，左右5:7，gap48px，左右32px；表单内部max-width440px；上/下64px |
| 768–1023 | 表单居中max-width480px，插图压缩为标题旁路线；外边距24px |
| <768 | 单列，外边距16px；短品牌说明→标题→表单→注册/返回；插图不占首屏大片高度 |
| 高度 | min-height:calc(100dvh - 72px)，正常文档滚动；不能固定整页高度导致软键盘遮挡 |
| 表单容器 | radius-organic；surface背景，1px border，shadow-1；桌面padding32px，手机24px；不透明表单 |
| 字体 | h1=36px/1.15（手机28px/1.2）；说明16px/1.6；label14px/1.5/600；输入16px/1.6；帮助12px/1.45 |
| 间距 | 标题→说明12；说明→表单24；字段间24；label→input8；input→helper8；次操作16 |
| 控件 | 输入/主按钮52px；显示密码与其他小控件至少44×44；间隔≥8px |
| 色彩 | 主#147D72、底#F5F7F2、正文#16302B、次文本#5D726D、错误#B23A3A；暗色完全跟tokens.css映射 |
| 动效 | 主卡首次translateY(8px)→0+opacity，360ms ease-standard；路线stroke绘制480ms一次；hover按钮≤-2px/180ms；不摇晃错误输入 |
| 减少动态 | route/卡片/路线直接最终状态，loading用静态状态文案；系统reduce优先 |

不得改 tokens 全局值来适配登录页。长英文/日文允许换行、grid min-width:0，320px和200%缩放无横溢出。独立 auth 路由不下载地图/ECharts/html2canvas/景点图。

### 6.2 登录

```text
现有导航：品牌                 语言 / 主题
main
  左：旅行从这里继续             右：欢迎回来
      一条本地路线                   登录后，找回属于你的旅程。
      无地图 SDK                     用户名 [             ]
                                     密码   [          显示]
                                     就地错误（存在时）
                                     [ 登录并继续 ]
                                     还没有账号？创建账号
                                     忘记密码？联系部署维护者
                                     返回首页
```

- 输入 username autocomplete=username、autocapitalize=none、spellcheck=false；密码 current-password。页面不强制初始 autofocus，路由完成聚焦 h1，Tab进入字段。
- Enter 提交，但 isComposing/keyCode229时不提交；提交中按钮loading且单飞，不禁用整页滚动/语言。
- 前端校验失败：错误摘要role=alert、tabindex=-1、链接到字段；聚焦摘要一次，保留行内aria-describedby/invalid。
- 错误凭证显示同一就地提示；保留用户名、清空密码并聚焦密码。网络错误保留密码在当前内存以便重试，不持久化；页面离开清空。
- 429显示可理解等待及Retry-After倒计时；不每秒live播报，只首次/结束。后端不可用显示重试，不伪登录成功。
- 成功不叠两种提示，不延迟2秒；采用返回路径并聚焦目标main/h1。

### 6.3 注册

同框架，字段顺序：用户名→显示名称（选填）→密码→确认密码→“创建账号并继续”。永久帮助显示 username规则/密码长度；confirmation autocomplete=new-password。

两次密码比较在前端；后台不接受role。提交前校验不在每按键时打断；重名提示用户名字段，密码保留当前内存。注册关闭显示联系维护者说明和登录/返回首页；不发注定失败请求。不虚构“同意隐私协议”勾选框或不存在的条款页。

### 6.4 账号页与导航

- `/account`：用户名只读、显示名只读、加入时间、本地聊天/编辑不跨设备同步说明、修改密码表单（当前/新/确认）、退出动作。暂不做修改display_name API。
- 导航游客显示登录/创建账号，隐藏全局配置入口；首页规划CTA可保留但提交时鉴权。
- 成员导航显示 display_name（超长可换行或max-width160px视觉省略并可见完整菜单文本）、账号页、外观/语言、退出。
- admin额外显示运行配置。SettingsDrawer 对 user 不发 `/settings`，但外观/语言偏好保持可用：提取 `AppearancePreferences.vue` 给菜单/账号页复用，不复制 theme 状态。
- 手机菜单沿用 MobileNavDrawer，点击账号项先关菜单再导航，Esc/焦点返回既有；退出与普通跳转之间留分隔，不把退出当primaryCTA。

### 6.5 三语键清单

`zh/en/ja` 同步新增 auth.*，不要出现裸中文 fallback：

`loginTitle/loginSubtitle/registerTitle/accountTitle/username/displayName/password/confirmPassword/currentPassword/newPassword/showPassword/hidePassword/login/register/logout/changePassword/backHome/contactMaintainer/registrationClosed/sessionExpired/serviceUnavailable/retry/invalidCredentials/usernameUnavailable/usernameHelp/passwordHelp/passwordMismatch/rateLimited/logoutIncomplete/privateHistoryPrompt/localChangesNotice`。

中文标题固定“欢迎回来”“创建你的旅行账号”；英文“Welcome back”“Create your travel account”；日文“おかえりなさい”“旅のアカウントを作成”。按钮英文“Sign in and continue”“Create account and continue”，日文“ログインして続ける”“アカウントを作成して続ける”。剩余自然翻译，含参数的倒计时保持同名占位符。

## 7. 文件级实施阶段

路径一律相对项目根目录。前端命令在 `frontend/` 执行 `npm run type-check` / `npm run build`；后端命令在 `backend/` 使用现有 `.venv\Scripts\python.exe -m pytest ...`，不要误用系统 Python。需要 pytest 等开发依赖时只按已有 `requirements-dev.txt` 安装到项目虚拟环境，记录安装结果，不升级无关依赖。下文 `python -m pytest` 均指这份虚拟环境解释器。

### L0 — 冻结基线与实施确认（首次仅此阶段）

只读应用源码，允许创建 `docs/LOGIN_ACCOUNT_PROGRESS.md`，不改账号代码、不装包、不改数据/配置。

1. 读本文件、相关旧重设计 QA、查 AGENTS；记录 dirty范围和 HEAD，不清工作区。
2. 核对所有 API、实际 session写入、Map/Chat/fetch/img 请求、路由、后端lifespan；差异记录为“规格校正”，不能静默换设计。
3. 核对后端pytest/Argon2是否可用，仅记录有无；前端type-check/build跑基线，后端测试隔离目录/外部服务再跑，禁止触发真实模型。
4. 统计旧任务owner缺失数量，不认领、不删除；检查备份与数据库持久卷方案。
5. 在进度文档写明确：本版username/password、session Cookie、注册开关、admin维护CLI、不迁移旧匿名数据、不承诺编辑同步。若用户要手机号或真正一人一号，此处停止澄清。

验收：基线命令原始结果、实际路径、非密钥配置计划、没有业务修改。报告后停止。

### L1 — Auth数据库与密码安全层

创建：

- `backend/app/auth/__init__.py`
- `backend/app/auth/database.py`
- `backend/app/auth/passwords.py`
- `backend/app/auth/repository.py`
- `backend/app/auth/rate_limit.py`
- `backend/app/auth/migrations/001_auth.sql`
- `backend/app/models/auth.py`
- `backend/tests/test_auth_storage.py`

修改：`backend/requirements.txt`（仅增加argon2-cffi，锁定经验证的兼容版本）、`backend/app/config.py`（新增非密钥auth配置）、`backend/app/api/main.py`（lifespan初始化/清理）、`backend/tests/conftest.py`（auth临时库/内存任务隔离）、`.gitignore`。

不修改真实.env/数据库，测试参数指临时目录。记录新依赖理由：安全密码散列；拒绝自己实现散列或用SHA-256密码。

验收：同名并发注册唯一、hash不等于原密码、不同salt、正确/错误/dummy验证、重启会话/限流数据保留、迁移幂等、约束/过期清理。`python -m pytest tests/test_auth_storage.py -q`通过后停止。

### L2 — Auth API、会话、CSRF与维护CLI

创建：

- `backend/app/auth/service.py`
- `backend/app/auth/dependencies.py`（get_current_user/require_admin/CSRF/WS helpers）
- `backend/app/api/routes/auth.py`
- `backend/scripts/manage_accounts.py`（create-admin/create-user/reset-password/disable-user）
- `backend/tests/test_auth_api.py`
- `backend/tests/test_auth_security.py`

修改：main.py（router/净化auth异常与no-store）、models/auth.py、config.py。

CLI密码用getpass两次确认，不作命令行参数/日志；仅终端本机维护，不提供公开引导admin接口。create-admin拒绝覆盖已有username；disable/reset先显示目标用户名并要求维护者确认。正式账户命令不由Cursor自动执行，测试在临时库执行。

验收：注册/登录/me/退出/改密码、session轮换、防重放、绝对+闲置过期、CSRF登录/写请求、Origin、不存在和错密码一致、限流Retry-After、角色注入拒绝；日志/422不含密码；无真实LLM请求。使用真实TestClient Cookie，不全部override auth dependencies。通过后停止。

### L3 — 保护现有业务与旧数据隔离

创建：`backend/app/api/routes/client_config.py`、`backend/scripts/assign_legacy_trip.py`、`backend/tests/test_account_isolation.py`、`backend/tests/test_auth_websocket.py`。

修改：trip.py、memory_routes.py、chat.py、settings.py、map.py、poi.py、main.py、schemas.py（legacy user_id描述/内部赋值）、tests/test_api.py及其他受影响API测试。

以本文件§3–§4为准，任务owner在内存与持久化路径都实现；WS在发首包前授权及撤销后关闭；member不读完整settings；公开client-config字段白名单。给既有API测试真实user/admin fixture和CSRF，不关闭认证让旧测试“全绿”。

**中间版本尚无前端登录，不能部署给用户。**

验收：A/B全部处理/失败/完成status与WS隔离；history先owner后limit；mem伪造ID无效；匿名/普通user/admin矩阵；服务重启owner保留；legacy无owner隐藏且文件未被改；CLI dry-run无写入。完整pytest通过后停止。

### L4 — 前端认证基础与账户清理

创建§5.1的router/types/httpClient/authApi/useAuth/accountBoundary/planStorage（本阶段不画完整登录页面，可用最小占位路由说明避免循环）。

修改：main.ts、services/api.ts、Landing.vue、Result.vue、useTripPlanState.ts、useItineraryEditor.ts、useAttractionPhotos.ts、useTripExport.ts、useTravelMap.ts、AIChat.vue、SettingsDrawer.vue、NavBar.vue、MobileNavDrawer.vue。

实现cookie/CSRF/401 bootstrap、安全redirect、服务端确认owner后使用缓存、所有async accountEpoch、私有状态清理和blob生命周期。业务body不随意改，只去掉前端user_id；写操作不自动retry。

验收：type-check/build；专门搜索axios/fetch/WebSocket/sessionStorage入口，逐个说明认证接线；旧匿名ID不发送；未登录不读历史/缓存、不发规划；切账号旧回包不写storage/下载。占位不冒充功能完成。通过后停止。

### L5 — 登录、注册、账号页面与导航

创建§5.1的Login/Register/Account、AuthScenicPanel/AuthFormFrame/PasswordField/AccountMenu，另建 `components/settings/AppearancePreferences.vue`。

修改：router/index.ts、NavBar.vue、MobileNavDrawer.vue、SettingsDrawer.vue、AppShell.vue（仅身份checking/unavailable shell反馈，不叠壳）、zh/en/ja、components.d.ts（生成）。

实现§6确定布局与全部状态，后台register关闭即时遵循，账户改密与失败状态真实；不新增远程字体/图片/SDK、不修改全站token。

验收：320/375/768/1024/1440、明暗/减动、200%缩放、键盘、密码管理器/粘贴/显示隐藏、IME、导航角色；无假OAuth/忘记密码按钮；auth页无重库请求。type-check/build通过后停止。

### L6 — 双账号端到端与回归

创建：

- `frontend/scripts/qa/auth_fixtures.py`
- `frontend/scripts/qa/auth_e2e.py`
- `frontend/scripts/qa/auth_security_browser.py`
- `docs/LOGIN_ACCOUNT_QA.md`
- 证据目录 `docs/qa/auth/`（不得保存cookie/密码/私人真实行程）

升级旧QA脚本：模拟server同时提供真实格式的auth/me/csrf/options；夹具storage标注账号owner。旧前端模拟套件仍只说明UI逻辑，不能替代真实FastAPI认证测试。

启动独立测试后端/SQLite/任务目录、两套Chrome context、stub planner/chat/map，运行下节用例。不要让stub覆盖auth/ownership逻辑。以外部服务stub + 真实后端auth为主要验收，必要的真实模型/地图检查另获授权。

验收：完整pytest + type-check/build；报告分清“真实认证/stub模型”“纯浏览器mock”“真人未测”。发现漏洞回到对应阶段修复并复测，不把待办删除。通过后停止。

### L7 — 部署说明与交付（不自动上线）

创建 `docs/ACCOUNT_DEPLOYMENT.md`，更新 README.md/README_en.md 的账号启动/维护/数据边界；完善进度/QA文档。

记录：HTTPS/same-origin、CORS/Origin列表、secure cookie、持久化auth卷与trip文件卷、首个admin安全CLI、注册开关、版本化迁移与备份恢复、用户编辑不同步说明、限流与公网风险。

测试Docker/后端静态SPA部署 `/login`、`/register`、`/account`、`/result?...` 深链接fallback；未知API返回404而不是index.html。不得将auth.sqlite、备份、trip JSON放到frontend/dist或静态目录。

账号DB+任务数据一致性备份：维护窗口暂停提交/写入，SQLite backup API（不直接拷贝运行中的WAL主文件），备份任务目录，验证恢复到临时环境。未经授权不操作真实生产数据、不创建正式admin、不开放公网注册、不上线。

回滚：保存改造前代码/数据备份与迁移版本；恢复时不能把带私人owner的新数据交给旧“全历史公开”的服务。旧匿名版本只可离线/限制访问恢复，不能公开回滚以绕过安全门。

验收：已执行结果与人工未执行明确；源码不含密码/凭证；启动说明可复现；不自动commit/push。报告最终矩阵后停止。

## 8. 必测用例（L6必须逐项记录）

| 编号 | 操作 | 预期 |
|---|---|---|
| A01 | 注册alice，注册ALICE | 第二次409，仅一条数据库user |
| A02 | 正确/错误密码、未知/禁用用户 | 正确登录，其余同401/同文案 |
| A03 | 刷新、绝对/闲置过期、后端重启 | 有效恢复；过期登录；重启有效会话仍可用 |
| A04 | 登录前后session、CSRF比较 | 全部轮换，旧session不能访问 |
| A05 | 缺/错CSRF、错误/缺Origin | 所有写操作403，未调用业务/stub |
| A06 | 注册注入role=admin | 422，无admin创建 |
| A07 | 重复点击、IME Enter | 请求单飞，IME不误发，用户名/密码粘贴可用 |
| A08 | 429与Retry-After | 等待提示真实，倒计时不反复读屏 |
| B01 | A生成计划，B列history | B无A摘要；limit也不能被A占据 |
| B02 | B猜A处理/失败/完成ID | HTTP均404，不泄露result/error/request_payload |
| B03 | B连接A WS、伪造Origin | 无snapshot，拒绝连接；队列不残留 |
| B04 | A退出但WS等待中 | ≤15s关闭；A后台计划仍只归A |
| B05 | 伪造body/query user_id | 记忆读写和生成只归已认证本人 |
| B06 | 普通用户GET/PUT settings | 403，无全局配置/LLM/XHS密钥泄露 |
| B07 | 普通用户client-config/地图 | 仅浏览器Key，原Google→高德/文字路线可用 |
| B08 | 无owner旧任务/匿名session | 不展示给任何新账号，原文件未损坏 |
| C01 | A退出→B登录同tab | A计划/聊天/撤销/地图/导出均不可见 |
| C02 | A迟到chat/photo/status/generate/export | 不写B UI/storage、不触发下载 |
| C03 | Tab1 A、Tab2 B登录 | Tab1清A状态并按/me采用B，不信广播payload |
| C04 | 改密码，另一个设备session/WS | 全撤销，两端必须重登 |
| C05 | 退出网络失败 | 私人视图冻结，明确未完成退出，可重试 |
| C06 | 缓存owner被手改/旧planId | 服务端权限验证后才渲染，404不回退旧缓存 |
| C07 | 有效会话下后端临时断开 | unavailable，不误报密码错误/静默游客 |
| C08 | 外部redirect/协议/反斜杠/循环 | 拒绝，返回首页；内部合法deep link保留query |
| D01 | 手机软键盘、横屏、中日IME | 输入/主按钮可见，不误发、不自动缩放 |
| D02 | keyboard/读屏、密码显示 | label真实，状态读出，焦点不被导航遮挡 |
| D03 | 明暗/减动/200%/320px | 可读可操作，无非必要横溢出 |
| D04 | auth首屏network | 无地图/ECharts/html2canvas/远程字体 |
| D05 | 受保护图片与导出 | 携带cookie取得blob，PNG内容完整，卸载revoke |
| E01 | API异常/validation日志 | 不含原密码、cookie、csrf、输入值 |
| E02 | 新机器/独立cwd启动 | DB路径稳定，迁移幂等，不创建散落auth.db |
| E03 | 数据备份在隔离环境恢复 | users/session/owner一致，旧无owner仍隐藏 |
| E04 | 六分区/预算编辑/日程/导出回归 | 旅游字段/预算规则/导出顺序与登录前一致 |

真实手机/真人读屏没设备时标为“未执行”，保留人工步骤，不能拿模拟viewport替代。不得将A/B仅是两条前端localStorage UID当作双账号测试。

## 9. 最终验收与明确不做的事

- [ ] 用户数据库持久化，密码Argon2id，客户端无认证token持久化。
- [ ] Cookie/CSRF/Origin/CORS/限流/日志脱敏全部通过实际测试。
- [ ] 当前用户身份只由服务器会话确定，权限不依赖user_id/plan_id不可猜。
- [ ] history/status/WS/memory/settings权限没有遗漏，所有旧/新/内存/磁盘分支一致。
- [ ] 旧匿名数据保留且不自动认领，迁移维护工具默认dry-run。
- [ ] frontend bootstrap、redirect、401、账号切换、跨tab和迟到回包边界通过。
- [ ] 前端私有状态清理不删除外观偏好；图片blob/SDK/WS/导出生命周期正确。
- [ ] 登录页延续Living Atlas，三语、明暗、reduce、表单/a11y、移动输入全覆盖。
- [ ] 没有虚构OAuth、邮件找回、全设备编辑/聊天同步、实名一人一号。
- [ ] 前后端工程/安全/回归报告可复现，stub与真实条件分清。
- [ ] 生产部署安全说明齐全，不因“本地通过”擅自上线。

不接受：只写一个Login.vue；前端存username算登录；拿客户端匿名UUID当数据库主身份；JWT/token放localStorage；只隐藏按钮不保护API；只保护status不保护WS；把全局.env配置当每用户设置；默认admin/admin密码；“知道旧plan_id就能认领”；关闭认证/CSRF让测试通过。

## 10. 直接发给 Cursor 的启动提示词

```text
请读取 docs/LOGIN_ACCOUNT_EXECUTION.md，严格按该文档为当前 TravelAI 项目实现用户名密码登录与账号数据隔离。

本次只执行 L0：核对基线、实际接口/存储路径、测试条件，并创建 docs/LOGIN_ACCOUNT_PROGRESS.md。不要进入 L1，不写登录/认证代码、不装包、不改.env或真实数据、不自动commit/push/reset。

现有大量未提交前端改造必须保留。不要只实现一个前端登录页，也不要用travelai.user_id模拟账号。后续实现采用FastAPI服务端opaque session + HttpOnly cookie + CSRF，账号身份由服务端判定；旧匿名历史不自动认领；全局配置仅admin。

L0完成后输出：实际现状与文档差异、基线命令结果、预计文件清单、旧数据归属风险、阻塞/未验证项，然后停止，等我指定下一阶段。
```

后续每次发送（将 L1 替换为本次阶段，不能合并）：

```text
继续执行 docs/LOGIN_ACCOUNT_EXECUTION.md 的 L1，仅完成本阶段。先读进度文档，核对上一阶段验收与当前dirty changes；保留所有用户改动。只修改本阶段清单内所需文件，遇到规格冲突先记录并说明，不擅自扩大功能。
完成本阶段对应测试，更新 docs/LOGIN_ACCOUNT_PROGRESS.md，输出修改清单、实际验收证据、未验证项与下一阶段条件。停止，不进入 L2，不commit/push、不操作真实旧数据。
```
