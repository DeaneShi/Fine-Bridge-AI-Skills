# 律师事务所智能体系统 · 架构设计文档

**版本**：v1.0
**适用项目**：Fine Bridge Legal Firm AI Agent
**最后更新**：2026-05-10
**状态**：设计稿（待评审）

---

## 0. 设计目标与范围

### 0.1 业务目标
为 3-5 人小型律师团队提供一套**所内私有部署 + 浏览器访问**的 AI 辅助办案系统，覆盖案件全生命周期，将本仓库已有的 `legal-firm-agent` Skill 落地为可日常使用的产品。

### 0.2 MVP 范围（确认）

| # | 模块 | 优先级 | 说明 |
| --- | --- | --- | --- |
| 1 | **案件管理** | P0 | 系统底座，承载其他模块的数据 |
| 2 | **账户管理** | P0 | 用户、角色、权限、登录 |
| 3 | **卷宗上传** | P0 | 文件存储、OCR、版本管理 |
| 4 | **智能问答** | P0 | Claude 驱动，结合卷宗上下文 |
| 5 | **文件输出** | P0 | 调用 Skill 模板生成 Word/PDF |
| 6 | **商务报价** | P1 | 复用现有 quotation-review Skill |
| 7 | **虚拟法庭** | P1 | Claude 多角色扮演的庭审模拟 |
| 8 | **使用手册** | P0 | 内嵌帮助中心 + 上下文帮助 + 导出 PDF 用户手册 |

**二期**：日程提醒、利益冲突检查、审计日志、法律检索接入、客户门户、知识库、计费、财务。

### 0.3 非目标（明确不做）
- 不做移动 App（用浏览器访问）
- 不做多租户（单律所私有部署）
- 不做实时音视频虚拟法庭（一期为文字流式）
- 不做本地大模型（统一走 Claude API）

---

## 1. 硬件与网络拓扑

### 1.1 硬件清单

| 角色 | 设备 | 配置建议 | 用途 |
| --- | --- | --- | --- |
| 服务器 | MacBook Pro M5 | 32GB RAM / 1TB SSD / 外接 2TB SSD | Web/API/DB/对象存储 |
| 客户端 ×3-5 | MacBook Pro/Air、其他笔电 | macOS 15+ 或 Windows 11 | Safari/Chrome 浏览器 |
| 必备外设 | UPS（不间断电源） | ≥ 500VA | 防断电导致 PG 损坏 |
| 必备外设 | 外置 SSD | 2TB 以上 | 卷宗存储 + 增量备份 |
| 可选 | NAS / 同型号 Mac | | 异地热备 |

### 1.2 网络拓扑

```
                        ┌───────────────────────────┐
                        │  Anthropic Claude API     │
                        │  (api.anthropic.com)      │
                        └─────────────▲─────────────┘
                                      │ HTTPS (出向)
                                      │
       ┌───────────────────── 律所局域网 (LAN) ──────────────────────┐
       │                                                              │
       │   ┌────────────────────────┐                                 │
       │   │ MacBook Pro M5 (Server)│                                 │
       │   │  Caddy :443            │◀──── HTTPS ────┐                │
       │   │  Next.js :3000         │                │                │
       │   │  FastAPI :8000         │                │                │
       │   │  PostgreSQL :5432      │                │                │
       │   │  Redis :6379           │                │                │
       │   │  MinIO :9000           │                │                │
       │   └────────────────────────┘                │                │
       │              │                              │                │
       │              ▼                              │                │
       │     ┌──────────────────┐         ┌─────────┴─────────┐       │
       │     │ 外置 SSD 备份    │         │ 客户端 ×3-5       │       │
       │     │ (每日增量)       │         │ MacBook / Win/iPad│       │
       │     └──────────────────┘         └───────────────────┘       │
       └──────────────────────────────────────────────────────────────┘
                                      │
                                      │ Tailscale (异地办公)
                                      ▼
                         ┌────────────────────────┐
                         │ 出差律师笔电            │
                         │ (Tailscale 客户端)     │
                         └────────────────────────┘
```

### 1.3 域名与 TLS
- **所内访问**：使用 `legal.fb.local`（写入服务器 `/etc/hosts` 或所内 DNS），由 Caddy 自动签发自签证书（首次访问由用户安装根证书）。
- **异地访问**：Tailscale MagicDNS，访问 `legal.tail-xxxx.ts.net`，Tailscale 自动颁发受信任 TLS。
- **不做公网暴露**（已确认范围）。

---

## 2. 软件技术栈

| 层 | 技术 | 选型理由 |
| --- | --- | --- |
| 前端 | **Next.js 15** + React 19 + TypeScript | SSR + API Route，开发节奏快；TS 提升大型项目可维护性 |
| UI 组件 | **shadcn/ui** + Tailwind CSS | 低运行时、易定制、无运行时依赖 |
| 状态管理 | **TanStack Query** + Zustand | 服务器状态用 Query，UI 状态用 Zustand |
| 富文本/编辑器 | **TipTap** | 文书编辑、可控字段、可导出 |
| 后端 | **Python 3.12 + FastAPI** | Anthropic SDK 一等公民；类型安全；性能足够 |
| 异步任务 | **Celery + Redis** | OCR、文档生成、Claude 长任务后台执行 |
| 定时任务 | **APScheduler** | 期限提醒、备份触发 |
| 数据库 | **PostgreSQL 17** | 关系强、JSONB 支持、全文检索 |
| 对象存储 | **MinIO**（S3 兼容） | 卷宗/证据/输出文件统一存储；将来易迁云 |
| 缓存 | **Redis** | 会话、Claude 响应缓存、Celery broker |
| 反向代理 | **Caddy 2** | 自动 TLS、配置极简、native macOS 友好 |
| OCR | **PaddleOCR**（CPU 模式）| 中文 OCR 第一梯队，本地离线运行 |
| 文档生成 | **python-docx** + **WeasyPrint** | Word + PDF 双格式输出 |
| Claude SDK | **anthropic-python** ≥ 最新版 | 官方 SDK，支持 Prompt Caching、Streaming、Tool Use |
| 鉴权 | **FastAPI Users** + JWT | 标准方案；MFA 二期接入 TOTP |
| 进程管理 | **launchd**（macOS 原生） | 比 PM2 更可靠地随系统启动 |
| 日志 | **Loguru** + 文件轮转 | 简单可读 |
| 监控 | **Uptime Kuma**（Docker） | 一键起，邮件/微信告警 |

### 2.1 部署方式
统一使用 **docker-compose**（macOS 上跑 Docker Desktop 或 OrbStack），唯一例外是 PostgreSQL 推荐用 **Postgres.app**（macOS 原生，性能更好）。

```yaml
# 概览：docker-compose.yml 编排的服务
services:
  caddy:        # :443 反向代理 + TLS
  web:          # Next.js 前端
  api:          # FastAPI 后端
  worker:       # Celery worker
  scheduler:    # APScheduler
  redis:        # 会话 + 任务队列
  minio:        # 对象存储
  uptime-kuma:  # 监控
# postgres: 单独装 Postgres.app（不在 compose 内）
```

---

## 3. 模块设计（MVP 7 大模块）

### 3.1 案件管理（Case Management）

**核心实体**：`case`、`party`（当事人）、`case_party`（关联表，含角色）。

**功能清单**：
- [x] 案件 CRUD（创建/列表/详情/编辑/归档）
- [x] 案件状态机：`接案中 → 进行中 → 已结案 → 已归档`
- [x] 多维筛选：案由、当事人、承办律师、状态、日期范围
- [x] 案件详情聚合页：基本信息 + 卷宗 + 时间线 + 提醒 + 报价 + 文书
- [x] 案件标签（自定义分类）

**与 Claude 的关系**：每次智能问答和文件输出都必须**绑定一个案件**，案件信息作为上下文注入。

### 3.2 账户管理（Account Management）

**角色与权限**（RBAC）：

| 角色 | 权限范围 |
| --- | --- |
| `admin` | 全部，含用户管理、系统设置、备份恢复 |
| `partner`（合伙人） | 全部案件可见可编辑 |
| `lawyer`（律师） | 仅自己主办/协办的案件 |
| `assistant`（助理） | 仅被分配的案件，受限编辑 |
| `client`（当事人，二期） | 仅自己案件的有限视图 |

**强制项**：
- 密码策略：≥ 12 位、大小写+数字+符号
- 登录失败 5 次锁定 15 分钟
- 会话默认 8 小时过期
- 二期：TOTP 多因素认证（Google Authenticator）

### 3.3 卷宗上传（Case File Upload）

**支持格式**：PDF、Word（doc/docx）、图片（jpg/png/heic）、Excel、txt、邮件（eml）。

**处理流水线**：
```
上传 → 病毒扫描 (clamav) → 存入 MinIO → 提取文本 (pdfplumber/python-docx)
   → 图片走 OCR (PaddleOCR) → 存全文索引 (Postgres tsvector)
   → 生成缩略图 → 标记完成
```

**特性**：
- 文件分类：起诉材料 / 证据原件 / 法律意见 / 通讯记录 / 其他
- 版本管理：替换文件保留历史版本
- 全文搜索：基于 Postgres `tsvector` + jieba 分词
- 单文件上限 100MB，单案件配额 5GB（可调）
- **脱敏预览**：自动检测身份证号、银行卡号、电话号，预览时打码

### 3.4 智能问答（AI Q&A）

**最关键的模块**。设计要点如下：

#### 3.4.1 上下文构造
```
系统提示 = SKILL.md 全文 (legal-firm-agent)
       + 案件元信息 (案由/当事人/我方身份)
       + 案件时间线 (摘要)
       + 已上传卷宗的全文索引 (检索式注入，最相关 5 段)

用户消息 = 当前问题
```

#### 3.4.2 Claude API 集成

**模型选择策略**：

| 场景 | 模型 | 原因 |
| --- | --- | --- |
| 日常问答、检索式回答 | `claude-sonnet-4-6` | 性价比最优 |
| 法律意见书、复杂文书 | `claude-opus-4-7` | 推理深度 |
| 自动分类、字段提取、利冲匹配 | `claude-haiku-4-5` | 快速、便宜 |
| 虚拟法庭多角色扮演 | `claude-opus-4-7` | 角色一致性 |

**必须启用的特性**：
1. **Prompt Caching（关键降本）**
   - 缓存 SKILL.md 系统提示（每次调用都用，cache hit 率接近 100%）
   - 缓存案件卷宗（同一案件多轮对话，cache hit 率 > 80%）
   - 预计可降低 80%+ 输入 token 成本
2. **Streaming**：所有用户可见的回答都用流式返回，前端打字机效果
3. **Tool Use**：让 Claude 主动调用以下工具
   - `search_case_files(case_id, query)` — 检索本案卷宗
   - `lookup_statute(law_name, article)` — 查法条全文（接知识库或 web 检索）
   - `compute_deadline(start_date, period_type)` — 期限计算
   - `check_conflict(party_name)` — 利冲查询
   - `save_to_case_timeline(case_id, event)` — 把对话产出沉淀到时间线
4. **Extended Thinking**：法律意见书生成时启用，提升论证质量
5. **System Prompt 版本化**：SKILL.md 改动时记录版本号，便于追溯回答的提示版本

#### 3.4.3 SDK 调用示例（Python，伪代码）

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    system=[
        {
            "type": "text",
            "text": SKILL_MD_FULL,
            "cache_control": {"type": "ephemeral"},  # 缓存 Skill
        },
        {
            "type": "text",
            "text": case_context_brief,
            "cache_control": {"type": "ephemeral"},  # 缓存案件上下文
        },
    ],
    tools=[search_case_files_tool, lookup_statute_tool, ...],
    messages=conversation_history + [{"role": "user", "content": user_question}],
    stream=True,
)
```

#### 3.4.4 答案落地
每个回答都附带：
- 引用的法条/卷宗位置（可点击跳转）
- 模型版本 + 提示版本（可追溯）
- "标记为不准确"按钮 → 进入待人工复核队列

### 3.5 文件输出（Document Generation）

**两种生成模式**：

1. **模板填充模式**（首选，可控性高）
   - 基于 `templates/legal-document-drafting.md` 中的模板
   - 用 python-docx 填充字段（当事人、金额、日期、法条）
   - Claude 仅负责生成"事实与理由"段落
   - 输出：Word（.docx）+ PDF（WeasyPrint 转换）

2. **自由生成模式**（用于代理意见、法律意见书）
   - Claude 直接产出 Markdown
   - 转 Word：pandoc / md → docx
   - 律师在富文本编辑器中二次修改

**强制项**：
- 输出前显示"待律师审核"水印（可在最终签发时去除）
- 自动校验：金额、日期、人名前后一致（基于规则引擎）
- 生成历史归档到案件目录

### 3.6 商务报价（Quotation）

**与现有 `quotation-review` Skill 协同**：本所自身对客户报价时，复用同一份审查框架。

**字段**：
- 基础律师费（计时/阶段/固定）
- 风险代理（合规校验：禁用案由自动拦截）
- 预估办案成本（差旅/调档/鉴定/保全担保）
- 折扣与备注
- 报价有效期

**输出**：标准报价单 PDF + 电子签接入（二期：DocuSign / 法大大）。

### 3.7 虚拟法庭（Virtual Court）

一期实现为**多角色文字流式对话**，作为庭审准备的演练工具。

**预设角色**（由同一个 Opus 模型扮演不同 system prompt）：
- 审判长（中立、程序主导）
- 对方代理人（强势、寻找漏洞）
- 关键证人（按预设事实回答，可被交叉询问）
- 旁观点评（庭后给出律师表现评估）

**流程**：
```
律师选择案件 → 系统加载卷宗与争议焦点
→ 进入庭审场景（开庭/法庭调查/质证/辩论/最后陈述）
→ 律师文字输入 → AI 多角色响应 → 全程录制
→ 庭后生成《模拟庭审复盘报告》：发问质量、辩论强度、漏掉的辩点
```

**模型**：`claude-opus-4-7`，启用 Extended Thinking。

**二期**：接 TTS（如 ElevenLabs）做语音化身。

### 3.8 使用手册（User Manual / Help Center）

**双形态交付**：
1. **系统内嵌帮助中心**：`/help` 路由，可全文检索、按模块导航、按角色推荐
2. **可导出 PDF 手册**：一键生成《Fine Bridge 律所智能体使用手册 v{x.y}》供新人入职、培训、审计留档

**功能清单**：
- [x] **三层文档结构**：快速入门 / 模块详解 / 故障排查
- [x] **角色化首页**：管理员、合伙人、律师、助理 各看到不同重点
- [x] **上下文帮助**：每个业务页面右上角"?"图标 → 直达该页对应的手册章节
- [x] **可搜索**：基于 Postgres 全文检索，关键词高亮
- [x] **图文 + 视频**：截图、流程动图（GIF）、可选嵌入培训视频（二期）
- [x] **版本与变更日志**：手册随系统版本同步发布；显示"本章节最近更新于 YYYY-MM-DD"
- [x] **反馈机制**：每篇文末"本文是否对您有帮助？" → 写入反馈库
- [x] **离线导出**：导出为 PDF / EPUB；可分模块或整本导出
- [x] **Claude 驱动的智能助手**：手册顶栏内置"问问助手"按钮，调用 Claude 基于手册内容回答用户问题（与业务问答区分开）

**数据来源**：
- 手册内容存储在仓库 `docs/user-manual/` 下的 Markdown 文件
- 应用启动时加载到数据库，写入 `help_articles` 表
- 编辑时通过后台界面（仅管理员）或直接改 Markdown + 重新部署

**技术实现**：
| 层 | 实现 |
| --- | --- |
| 内容源 | Markdown + Front Matter（YAML 头标注 module/role/version） |
| 渲染 | MDX（支持嵌入交互组件，如"试试看"沙盒） |
| 检索 | Postgres `tsvector` + jieba 中文分词 |
| 上下文帮助 | 业务页面声明 `helpKey="case.create"` → 帮助中心按 key 跳转 |
| PDF 导出 | pandoc `md → pdf`（中文支持需配字体） |

**目录结构（MVP）**：
```
docs/user-manual/
├── 00-overview.md              # 系统总览
├── 01-quick-start/
│   ├── for-admin.md
│   ├── for-lawyer.md
│   └── for-assistant.md
├── 02-modules/
│   ├── account.md
│   ├── case-management.md
│   ├── case-files.md
│   ├── ai-qa.md
│   ├── document-generation.md
│   ├── quotation.md
│   └── mock-court.md
├── 03-workflows/
│   ├── new-case-end-to-end.md  # 从接案到结案完整走查
│   └── litigation-checklist.md
├── 04-faq.md
├── 05-troubleshooting.md
└── 99-changelog.md
```

**与 SKILL.md 的关系**：使用手册面向"系统使用"，SKILL.md 面向"AI 行为"。手册中的"AI 问答最佳实践"章节会摘录 SKILL.md 关键准则，提示用户如何提问能获得更好结果。

---

## 4. 数据库 Schema（MVP）

### 4.1 ER 概览

```
users ──┬── cases ──┬── case_files
        │           ├── case_parties ── parties
        │           ├── case_timeline
        │           ├── conversations ── messages
        │           ├── documents (输出文件)
        │           └── quotations
        │
        └── audit_logs (二期)
```

### 4.2 关键表（精简版）

```sql
-- 用户
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  display_name TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('admin','partner','lawyer','assistant')),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT now(),
  last_login_at TIMESTAMPTZ
);

-- 案件
CREATE TABLE cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_no TEXT UNIQUE NOT NULL,             -- 所内编号 FB-2026-CV-001
  name TEXT NOT NULL,                       -- 案件名称
  cause TEXT,                               -- 案由
  our_role TEXT,                            -- 我方身份
  status TEXT NOT NULL DEFAULT 'intake',    -- intake/active/closed/archived
  lead_lawyer_id UUID REFERENCES users(id),
  metadata JSONB DEFAULT '{}',              -- 灵活扩展字段
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  archived_at TIMESTAMPTZ
);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_lead ON cases(lead_lawyer_id);

-- 当事人
CREATE TABLE parties (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type TEXT NOT NULL CHECK (type IN ('person','org')),
  name TEXT NOT NULL,
  id_number_encrypted BYTEA,                -- 加密存储身份证号
  contact JSONB DEFAULT '{}',               -- 电话、地址、邮箱
  notes TEXT
);

-- 案件-当事人关联
CREATE TABLE case_parties (
  case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
  party_id UUID REFERENCES parties(id),
  role TEXT NOT NULL,                       -- plaintiff/defendant/third_party/我方/对方
  PRIMARY KEY (case_id, party_id, role)
);

-- 卷宗
CREATE TABLE case_files (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
  category TEXT NOT NULL,                   -- evidence/pleading/correspondence/...
  filename TEXT NOT NULL,
  mime_type TEXT,
  size_bytes BIGINT,
  storage_key TEXT NOT NULL,                -- MinIO 对象 key
  sha256 TEXT NOT NULL,
  ocr_text TEXT,                            -- 提取出的全文
  ocr_search_vector TSVECTOR,               -- 全文搜索索引
  version INT DEFAULT 1,
  uploaded_by UUID REFERENCES users(id),
  uploaded_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_case_files_search ON case_files USING GIN(ocr_search_vector);

-- 时间线
CREATE TABLE case_timeline (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
  event_date DATE NOT NULL,
  event_type TEXT,                          -- intake/filing/hearing/judgment/...
  title TEXT NOT NULL,
  description TEXT,
  evidence_refs UUID[],                     -- 关联 case_files.id
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 对话会话
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
  title TEXT,
  model TEXT,                               -- 使用的模型 ID
  skill_version TEXT,                       -- 使用的 SKILL.md 版本
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  role TEXT NOT NULL,                       -- user/assistant/tool
  content JSONB NOT NULL,                   -- 兼容多模态、tool_use
  tokens_input INT,
  tokens_output INT,
  cache_read_tokens INT,
  cache_creation_tokens INT,
  cost_usd NUMERIC(10,6),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 输出文件（生成的文书）
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
  doc_type TEXT,                            -- complaint/answer/appeal/opinion/...
  title TEXT NOT NULL,
  storage_key TEXT NOT NULL,
  format TEXT,                              -- docx/pdf/md
  generated_from_template TEXT,
  conversation_id UUID REFERENCES conversations(id),
  reviewed BOOLEAN DEFAULT FALSE,
  reviewed_by UUID REFERENCES users(id),
  reviewed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 报价
CREATE TABLE quotations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
  client_party_id UUID REFERENCES parties(id),
  fee_model TEXT,                           -- hourly/fixed/contingency
  base_fee NUMERIC(12,2),
  contingency_pct NUMERIC(5,2),
  estimated_costs JSONB,
  total NUMERIC(12,2),
  valid_until DATE,
  status TEXT DEFAULT 'draft',              -- draft/sent/accepted/rejected
  created_at TIMESTAMPTZ DEFAULT now()
);
```

### 4.3 加密策略
- **静态加密**：磁盘整体启用 FileVault；身份证号、银行卡号字段在应用层用 AES-256-GCM 加密（密钥存 macOS Keychain）。
- **传输加密**：全程 HTTPS（Caddy 自签 + Tailscale）。
- **备份加密**：备份文件 GPG 加密后再写入外置 SSD 或 iCloud。

---

## 5. API 设计（节选）

REST 风格，统一前缀 `/api/v1/`。鉴权用 `Authorization: Bearer <jwt>`。

### 5.1 案件
| Method | Path | 说明 |
| --- | --- | --- |
| GET | `/cases?status=&lead=&q=` | 列表 + 筛选 |
| POST | `/cases` | 创建（自动触发利冲检查 - 二期） |
| GET | `/cases/{id}` | 详情聚合 |
| PATCH | `/cases/{id}` | 局部更新 |
| POST | `/cases/{id}/archive` | 归档 |

### 5.2 卷宗
| Method | Path | 说明 |
| --- | --- | --- |
| POST | `/cases/{id}/files` | 上传（multipart） |
| GET | `/cases/{id}/files` | 列表 |
| GET | `/files/{id}` | 元数据 |
| GET | `/files/{id}/download` | 下载（带签名 URL） |
| GET | `/files/{id}/preview` | 预览（脱敏后） |
| POST | `/cases/{id}/search` | 全文搜索 |

### 5.3 智能问答
| Method | Path | 说明 |
| --- | --- | --- |
| POST | `/cases/{id}/conversations` | 新建会话 |
| GET | `/conversations/{id}/messages` | 历史消息 |
| POST | `/conversations/{id}/messages` | 发消息 → SSE 流式响应 |
| POST | `/conversations/{id}/feedback` | 标记不准确/有用 |

**SSE 响应示例**：
```
event: message_start
data: {"id":"msg_xxx","model":"claude-sonnet-4-6"}

event: content_block_delta
data: {"delta":{"text":"根据《民法典》第 675 条..."}}

event: tool_use
data: {"name":"search_case_files","input":{"query":"借款合同"}}

event: message_stop
data: {"usage":{"input_tokens":1234,"output_tokens":567,"cache_read_input_tokens":8000}}
```

### 5.4 文件输出
| Method | Path | 说明 |
| --- | --- | --- |
| POST | `/cases/{id}/documents/generate` | 生成文书（template + 字段） |
| GET | `/documents/{id}` | 详情 |
| GET | `/documents/{id}/download` | 下载 docx/pdf |
| POST | `/documents/{id}/review` | 标记已审核 |

### 5.5 虚拟法庭
| Method | Path | 说明 |
| --- | --- | --- |
| POST | `/cases/{id}/mock-trials` | 新建模拟庭审 |
| POST | `/mock-trials/{id}/turn` | 律师发言 → AI 多角色响应 |
| GET | `/mock-trials/{id}/report` | 复盘报告 |

---

## 6. 安全与合规

### 6.1 强制要求
| 项 | 措施 |
| --- | --- |
| 操作审计 | 所有"案件/卷宗/输出/导出"操作写入 `audit_logs`（二期） |
| 数据脱敏 | 卷宗预览自动打码身份证、银行卡、手机号 |
| 权限隔离 | RBAC 严格执行，律师只能见自己的案件 |
| API 限流 | 单用户 60 req/min；Claude 调用 10 req/min |
| 备份策略 | 每日 02:00 PG dump + MinIO 增量同步到外置 SSD；每周一全量到 iCloud（GPG 加密） |
| 灾备演练 | 每季度从备份恢复一次到测试库 |
| 密钥管理 | Anthropic API Key 存 macOS Keychain，FastAPI 启动时通过 `security` 命令读取 |
| Claude 数据传输声明 | 用户协议明确告知"案件内容会发送至 Claude API"；提供"敏感案件不上 AI"开关 |

### 6.2 律所合规
- 律师执业行为规范：所有 AI 输出加水印"待执业律师审核"
- 个人信息保护法：当事人信息收集需明确告知用途
- 国家秘密：禁止上传"涉密"标签案件至 Claude（系统层强制拦截）

### 6.3 风险点
| 风险 | 缓解 |
| --- | --- |
| Claude 编造法条/案号 | Tool Use 强制走法条库；输出加"待复核"提示 |
| 单点服务器故障 | 异地备份 + 季度恢复演练；考虑同型号 Mac 热备 |
| API Key 泄漏 | 仅服务端持有；启用 Anthropic 控制台用量告警 |
| 内部员工越权 | RBAC + 审计日志 + 离职即时禁用 |
| 当事人数据外泄 | 不开公网；Tailscale 仅授权设备；导出操作走二人复核（二期） |

---

## 7. 部署与运维

### 7.1 目录结构（部署侧）

```
/Users/legal/fb-legal/
├── docker-compose.yml
├── .env                       # 环境变量（不入库）
├── caddy/
│   └── Caddyfile
├── data/
│   ├── postgres/             # Postgres.app 默认目录
│   ├── minio/                # 对象存储
│   └── redis/
├── backups/
│   ├── daily/
│   └── weekly/
├── logs/
└── scripts/
    ├── backup.sh
    ├── restore.sh
    └── healthcheck.sh
```

### 7.2 启动序列（launchd）
```
1. Postgres.app（GUI 自动启动）
2. Docker Desktop / OrbStack（GUI 自动启动）
3. com.fb.legal.compose.plist (launchd) → docker compose up -d
4. Caddy 监听 :443
5. 监控：Uptime Kuma 每 60s 探测 /healthz
```

### 7.3 备份脚本（每日 02:00）
```bash
# 节选
pg_dump -Fc legal | gpg --encrypt -r backup@fb.local > daily/legal-$(date +%F).dump.gpg
mc mirror --overwrite local/legal /Volumes/BackupSSD/minio/
```

### 7.4 监控与告警
- **服务健康**：Uptime Kuma 检测 web/api/db
- **资源**：Activity Monitor + 自写脚本日报（CPU/内存/磁盘 阈值告警 → 邮件）
- **Claude 用量**：每天汇总入库 token + 费用 → 仪表盘卡片
- **错误日志**：Loguru 写入 `logs/api.log`，超过 ERROR 级别 → 邮件

### 7.5 macOS 服务器加固清单
- [ ] 关闭自动更新（`softwareupdate --schedule off`）
- [ ] 禁用睡眠（`pmset -a sleep 0 disksleep 0`）
- [ ] 启用 FileVault
- [ ] 关闭 Spotlight 索引数据库目录
- [ ] 防火墙仅放行 443 / Tailscale
- [ ] SSH 仅密钥登录（如需远程维护）
- [ ] 系统时间 NTP 同步（影响期限计算）
- [ ] 接 UPS 并配 `pmset` 自动安全关机

---

## 8. 成本估算

### 8.1 一次性
| 项 | 金额（参考，CNY） |
| --- | --- |
| MacBook Pro M5 32GB/1TB | ¥25,000 |
| 外置 SSD 2TB | ¥1,200 |
| UPS 500VA | ¥800 |
| 域名（如启用） | ¥80/年 |
| 开发投入（自建/外包） | 见下表 |

### 8.2 月度运营
| 项 | 估算（USD） |
| --- | --- |
| Claude API（启用 Prompt Caching） | $200 - $800（取决于使用强度） |
| Tailscale | $0（个人版免费 ≤ 100 设备） |
| 备份云存储（iCloud 2TB） | $10 |
| **合计** | **$210 - $810** |

### 8.3 Prompt Caching 节省测算
假设：每次问答平均 30k input tokens，其中 25k 来自 SKILL + 案件上下文（可缓存），5k 来自当前问题。
- 不开缓存：30k × $3/M = $0.09/次
- 开缓存（命中）：25k × $0.30/M + 5k × $3/M = $0.0225/次
- **节省约 75%**

### 8.4 开发工期（单全栈工程师）
| 阶段 | 内容 | 工期 |
| --- | --- | --- |
| Sprint 0 | 基础设施 + CI + 部署 | 1 周 |
| Sprint 1 | 账户 + 案件管理 | 1.5 周 |
| Sprint 2 | 卷宗上传 + OCR + 全文搜索 | 1.5 周 |
| Sprint 3 | 智能问答（含 Tool Use + Caching） | 2 周 |
| Sprint 4 | 文件输出（模板 + 自由生成） | 1.5 周 |
| Sprint 5 | 商务报价 | 1 周 |
| Sprint 6 | 虚拟法庭 | 1.5 周 |
| Sprint 7 | 使用手册（内嵌帮助 + PDF 导出 + 上下文帮助） | 1 周 |
| Sprint 8 | UAT + 加固 + 培训交付 | 1.5 周 |
| **合计** | **MVP 上线** | **12.5 周** |

> **说明**：使用手册的 Markdown 内容编写在 Sprint 1-6 期间**与各模块开发并行**完成（每个模块 Owner 同步产出对应章节），Sprint 7 集中做帮助中心 UI、检索、PDF 导出和上下文跳转。

---

## 9. 开发路线图

### 9.1 MVP（前 11 周）
按上节 Sprint 推进，Sprint 结束即所内试用。

### 9.2 二期（第 12-20 周）
- 期限提醒（关键，与 SKILL.md 中的台账打通）
- 利益冲突自动检查
- 审计日志
- 法律检索接入（北大法宝/威科 API 或 web 检索）
- TOTP 多因素认证

### 9.3 三期（第 21 周起）
- 客户门户 + 电子签
- 知识库 / RAG（沉淀本所案例作为私有语料）
- 财务模块
- 虚拟法庭语音化身（TTS）
- 移动端 PWA 优化

---

## 10. 待决问题（需要客户/合伙人确认）

1. **数据合规**：是否能接受案件内容走 Claude API（在 Anthropic 服务器处理）？是否需要为涉密/敏感案件提供"不上 AI"开关？
2. **域名与备案**：是否完全不暴露公网（推荐），还是需要支持公网访问？
3. **预算审批**：Claude API 月度上限设多少（建议先设 $500，超额自动降级到 Haiku）？
4. **数据导入**：现有历史案件（纸质/电子）是否需要历史数据迁移？规模？
5. **培训与支持**：上线后由谁负责一线技术支持？
6. **二期模块的优先级**：期限提醒 vs 利冲 vs 法律检索，哪个优先？

---

## 附录 A：相关文件位置

| 文件 | 路径 |
| --- | --- |
| 律师事务所智能体 Skill | `skills/legal-firm-agent/SKILL.md` |
| 接案模板 | `templates/legal-case-intake.md` |
| 案情分析模板 | `templates/legal-case-analysis.md` |
| 证据清单模板 | `templates/legal-evidence-checklist.md` |
| 文书起草模板 | `templates/legal-document-drafting.md` |
| 庭审准备模板 | `templates/legal-trial-preparation.md` |
| 案件台账模板 | `templates/legal-case-tracking.md` |
| 结案归档模板 | `templates/legal-case-closure.md` |
| 项目需求说明 | `docs/requirements.md` |
| 验收与培训计划 | `docs/acceptance-and-training.md` |
| 文档索引 | `docs/README.md` |
| 用户手册（编写中） | `docs/user-manual/` |

---

**文档维护**：Fine Bridge Technology (Thailand) Co., Ltd.
**评审记录**：（待评审后追加）
