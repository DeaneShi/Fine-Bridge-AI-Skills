# 律师事务所智能体系统 · 架构设计文档

**版本**：v1.0
**适用项目**：Fine Bridge Legal Firm AI Agent
**最后更新**：2026-05-10
**状态**：设计稿（待评审）

---

## 0. 设计目标与范围

### 0.1 业务目标
为 3-5 人小型律师团队提供一套**所内私有部署 + 浏览器访问**的 AI 辅助办案系统，按律所**三大业务线**组织，覆盖各业务线的全生命周期，将本仓库已有的 `legal-firm-agent` Skill 落地为可日常使用的产品。

### 0.1bis 三大业务线（核心组织原则）

律所的全部业务沿三条业务线展开。系统的顶层导航、数据模型与 AI Skill 都按这三条线组织：

| 业务线 | 业务特征 | 核心交付物 | 系统中的承载 |
| --- | --- | --- | --- |
| **① 常年法律顾问** | 长期持续服务，按年度合同 | 合同审查、法律意见书、定期工作汇报、法律咨询答复 | 法律顾问模块（§3.7） |
| **② 诉讼仲裁案件代理** | 单次案件代理，有审限与法定期限 | 案件分析、起诉/答辩/上诉/反诉/管辖权异议等司法文书、模拟法庭打磨 | 案件管理（§3.1）+ 文件输出（§3.5）+ 虚拟法庭（§3.8） |
| **③ 非诉法律项目** | 项目制（M&A、IPO、私募、重组、合规等） | 尽调清单、尽调报告、法律意见书、交易文本、配套文本 | 非诉法律项目模块（§3.7B） |

**跨业务线的通用能力**：账户、客户、卷宗、智能问答、文件输出、商务模块、使用手册——服务于所有三条业务线。

> **业主的业务定位**：以非诉并购见长，因此非诉法律项目模块是**核心差异化模块**，其优先级与质量要求不应低于诉讼仲裁模块。

### 0.2 MVP 范围（确认）

按"业务线 ↔ 共享能力"双层组织：

**通用底座（跨业务线）**

| # | 模块 | 优先级 | 说明 |
| --- | --- | --- | --- |
| 1 | **账户管理** | P0 | 用户、角色、权限、登录 |
| 2 | **客户与卷宗** | P0 | 客户档案 + 文件存储 + OCR + 全文索引 + 版本 |
| 3 | **智能问答** | P0 | Claude 驱动，按业务线注入不同 Skill 上下文 |
| 4 | **文件输出** | P0 | 模板填充 + AI 自由生成，按业务线分类 |
| 5 | **商务模块** | P1 | 客户级 CRM + 报价 + 委托合同 + 收款台账 |
| 6 | **使用手册** | P0 | 内嵌帮助中心 + 上下文帮助 + 导出 PDF 用户手册 |

**三大业务线模块**

| # | 模块 | 业务线 | 优先级 | 说明 |
| --- | --- | --- | --- | --- |
| 7 | **法律顾问服务模块** | ① 常法 | P0 | 顾问单位、服务记录、合同审查、法律意见、定期工作汇报、法律咨询、续约 |
| 8 | **诉讼仲裁案件管理** | ② 诉讼仲裁 | P0 | 案件档案、案件分析与资料处理、司法文书全套、案件台账 |
| 9 | **非诉法律项目模块** | ③ 非诉 | P0 | 项目档案、尽调清单、尽调报告、法律意见书、交易文本、配套文本 |
| 10 | **虚拟法庭（外脑）** | ② 诉讼仲裁 | P1 | Claude 多角色扮演的庭审打磨工具 |

**MVP 模块总数：10**

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

### 3.1 诉讼仲裁案件管理（Litigation & Arbitration Case Management）

**业务线**：② 诉讼仲裁。**对应 Skill**：`legal-firm-agent`。

**三大子需求**（业主明确要求）：

#### 3.1.1 案件分析与资料处理
- 案件档案 CRUD（创建/列表/详情/编辑/归档）
- 案件状态机：`接案中 → 立案 → 答辩期 → 举证期 → 开庭 → 判决 → 上诉 → 执行 → 结案 → 归档`
- 多维筛选：案由、当事人、承办律师、状态、法院、日期范围
- 案件详情聚合页：基本信息 + 当事人 + 卷宗 + 时间线 + 期限提醒 + 文书 + 报价 + 收款
- **资料处理**：上传卷宗 → OCR → 全文索引 → AI 抽取关键信息（标的额、关键日期、当事人）→ 自动构建时间线
- AI 辅助：争议焦点识别、请求权基础分析、诉讼时效核查、管辖判断

#### 3.1.2 司法文书输出（详见 §3.5 文件输出）
诉讼仲裁业务线必须支持的文书类型（业主明确列出）：
- ✅ 起诉状
- ✅ 答辩状
- ✅ 上诉状
- ✅ **反诉状**（新增）
- ✅ **管辖权异议申请书**（新增）
- ✅ **证据目录**（新增，结构化）
- ✅ **证据整理表 / 三性分析**（新增，结构化）
- ✅ 代理意见 / 代理词
- ✅ 法律意见书
- ✅ 律师函
- ✅ **再审申请书 / 申诉书**（新增）
- ✅ **执行申请书**（新增）
- ✅ **保全申请书**（新增）
- ✅ **仲裁申请书 / 仲裁答辩书**（新增）
- ✅ **各类司法程序中的规范性文件**（如调取证据申请、鉴定申请、回避申请、撤诉申请、延期申请等）

#### 3.1.3 模拟法庭（外脑打磨，详见 §3.8 虚拟法庭）
业主明确表达："我需要一个外脑来和我一起对这个案件进行打磨"——即在开庭前用 AI 多角色扮演（审判长、对方代理人、证人）对自己的论证体系做压力测试，发现漏洞、补强主辩点。

**核心实体**：`case`、`party`（当事人）、`case_party`、`case_timeline`、`case_files`、`documents`。

**与 Claude 的关系**：每次智能问答和文件输出都必须**绑定一个案件**，案件信息（含已上传卷宗）作为上下文注入。

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

**按业务线组织模板库**（生成时根据业务线自动加载相应模板）：

#### 3.5.1 诉讼仲裁业务线模板（业主明确要求全部支持）

| 类别 | 模板 |
| --- | --- |
| 起诉与答辩 | 民事起诉状、行政起诉状、民事答辩状、**反诉状** |
| 二审与再审 | 民事上诉状、刑事上诉状、**再审申请书 / 申诉书** |
| **管辖与程序异议** | **管辖权异议申请书**、回避申请、延期举证申请、调取证据申请、鉴定申请、撤诉申请、保全申请书 |
| **证据组卷** | **证据目录**（结构化，自动编号）、**证据整理表 / 三性分析**（按待证事实组织）、举证清单 |
| 代理与意见 | 民/刑/行 代理意见、辩护词、法律意见书 |
| 仲裁专用 | **仲裁申请书**、**仲裁答辩书**、仲裁庭前意见 |
| 执行 | **执行申请书**、终本异议、参与分配申请 |
| 函件 | 律师函、催告函、解约通知 |

#### 3.5.2 法律顾问业务线模板

| 类别 | 模板 |
| --- | --- |
| 合同审查意见 | 合同审查报告、修改建议清单（红黑线版） |
| 法律意见 | 专项法律意见书、合规意见书、争议解决建议 |
| 工作汇报 | 月度服务报告、季度复盘、年度服务总结 |
| 咨询答复 | 法律咨询答复书（邮件版 / 正式版） |

#### 3.5.3 非诉法律项目业务线模板（详见 §3.7B）

| 类别 | 模板 |
| --- | --- |
| 尽调阶段 | 尽调清单（按项目类型分版本：股权并购 / 资产收购 / IPO / 私募 / 重组）、尽调资料请求函、尽调问题清单、尽调访谈提纲 |
| 尽调成果 | 法律尽职调查报告（结构化模板，含执行摘要、调查范围、主要发现、风险评级） |
| 法律意见 | 项目法律意见书、专项法律意见、合规法律意见 |
| 交易文本 | 意向书 / Term Sheet、框架协议、股权转让协议、增资协议、资产收购协议、股东协议、公司章程修订 |
| 配套文本 | 股东会决议、董事会决议、工商变更登记申请、通知函、同意函、信息披露文件、对赌 / 回购 / 锁箱协议、保密协议（NDA） |

#### 3.5.4 两种生成模式

1. **模板填充模式**（首选，可控性高）
   - 基于 `templates/` 中的模板
   - 用 python-docx 填充字段（当事人、金额、日期、法条）
   - Claude 仅负责生成"事实与理由""主要发现"等需要论证的段落
   - 输出：Word（.docx）+ PDF（WeasyPrint 转换）

2. **自由生成模式**（用于代理意见、尽调报告主体、法律意见书）
   - Claude 直接产出 Markdown
   - 转 Word：pandoc / md → docx
   - 律师在富文本编辑器中二次修改

**强制项**：
- 输出前显示"待律师审核"水印（可在最终签发时去除）
- 自动校验：金额、日期、人名前后一致（基于规则引擎）
- 生成历史归档到对应案件 / 顾问单位 / 项目目录

### 3.6 商务模块（Commercial Module）

**业务范围**：把"客户关系 + 报价 + 委托合同 + 收款"这一商务全链路集中到一个模块，避免散落在 Excel、微信和合伙人脑海里。

**子功能**：

#### 3.6.1 客户管理（CRM）
- 客户档案：自然人 / 法人（含统一社会信用代码、行业、规模）
- 客户分类：潜在客户 / 正式客户 / 顾问客户 / 历史客户
- 客户来源：转介绍 / 自然客流 / 老客户 / 营销活动
- 客户级别：VIP / 一般 / 观察（用于服务优先级与报价折扣策略）
- 客户与案件 / 顾问单位 / 报价 / 收款的关联视图

#### 3.6.2 商务报价（Quotation，原有功能保留）
- 三种计费模式：计时 / 固定 / 阶段
- 风险代理：禁用案由（婚姻、刑事、行政、劳动报酬追索）系统层强制拦截
- 办案成本预估：差旅 / 调档 / 鉴定 / 保全担保
- 报价单 PDF 生成；状态：草稿 / 已发送 / 已接受 / 已拒绝 / 过期
- 与现有 `quotation-review` Skill 协同复用审查框架

#### 3.6.3 委托代理合同（Engagement Letter）
- 模板：民事代理 / 刑事辩护 / 行政代理 / 法律顾问 / 专项顾问 / 仲裁代理
- 字段自动填充：当事人、代理事项、收费、期限、双方权利义务
- 输出 .docx + .pdf；可走电子签（二期接 DocuSign / 法大大）
- 合同与报价的状态联动（报价已接受 → 自动生成合同草稿）

#### 3.6.4 收款台账与发票（Receivables）
- 应收登记：合同金额 / 已收金额 / 应收余额 / 账期
- 收款记录：日期、金额、方式（转账 / 现金 / 票据）、凭证编号
- 催收提醒：账期到期前 7 日 / 当日提醒
- 发票登记（一期手工录入：开票日期、发票号、税率、金额）；票据系统集成在二期

**与其他模块的关系**：
- 与**案件管理**：案件创建时强制选择客户；案件结案时自动同步收款进度
- 与**法律顾问模块**：顾问客户复用商务模块的客户档案与收款台账
- 与**账户管理**：合伙人审批高额报价 / 折扣（设可配置阈值）

### 3.7 法律顾问服务模块（Legal Counsel Service Module）

**业务线**：① 常年法律顾问。

**业主明确的四大核心子功能**：合同审查 / 法律意见书出具 / 定期工作汇报 / 常规法律咨询解答。系统在此基础上增加顾问单位档案、续约、看板等运营底盘功能。

#### 3.7.1 顾问单位档案与基础设施
- 基本信息：单位名称、统一社会信用代码、行业、规模、对接人（含 KP 与日常联系人）
- 顾问类型：常年法律顾问 / 专项法律顾问 / 项目顾问
- 服务期限、年度费用、付款节奏
- 服务限额：每月咨询次数 / 合同审查份数 / 上门次数 / 出具意见书份数
- 主办律师与协办团队（决定权限）

#### 3.7.2 合同审查（业主明确子功能 ①）
- 客户上传 / 律师代上传待审合同（Word / PDF）
- AI 自动审查（结合 `quotation-review` Skill 风格）：
  - 条款拆解：识别主体、标的、权利义务、违约责任、争议解决、生效条件
  - 风险点清单：按高 / 中 / 低分级
  - 修改建议：原条款 → 建议条款（red-line 比对视图）
  - 缺失条款提示
  - 法律依据：每条建议附条文引用
- 律师审核与定稿：在系统内修改 AI 输出，出具正式《合同审查意见》
- 输出：审查意见书 PDF + 修订版合同（Track Changes / 红黑线版）
- 自动计入服务记录与限额消耗

#### 3.7.3 法律意见书出具（业主明确子功能 ②）
- 按需求类型选择模板：专项法律意见、合规意见、争议解决建议、交易结构意见
- 信息收集表单 → 律师填写背景、问题、依据
- AI 辅助生成：意见书初稿（含事实背景、法律分析、结论建议）
- 律师审核 → 合伙人复核 → 加水印 / 盖电子章 → 出具
- 版本管理：保留所有修订版本
- 自动归档到顾问单位卷宗

#### 3.7.4 定期工作汇报（业主明确子功能 ③）
- 自动汇总周期内（月 / 季 / 年）的服务记录
- 报告类型：
  - **月度服务报告**：每月 1 日自动生成上月报告草稿
  - **季度复盘**：每季度末自动生成季度服务总结
  - **年度服务总结**：续约前自动生成年度报告
- 报告内容：服务次数统计、按类型分布、主要服务事项摘要、关联文件清单、限额使用情况、下周期建议
- 主办律师审核后一键发送至客户对接人邮箱
- 输出：PDF（含本所抬头、盖章位、签字位）

#### 3.7.5 常规法律咨询解答（业主明确子功能 ④）
- 顾问单位提交咨询 → 系统生成工单 → 自动 / 手动分配律师
- 律师在工单页面调用智能问答辅助（AI 上下文限定为该顾问单位的全部历史卷宗与服务记录）
- 答复支持：纯文字 / 附法条 / 附案例 / 附参考文件
- 一键发送邮件 + 系统留底
- 自动计入服务记录与限额消耗

#### 3.7.6 续约管理（运营底盘）
- 合同到期前 60 / 30 / 7 日自动提醒主办律师
- 续约工作流：年度服务复盘 → 收费方案 → 续约谈判 → 新合同生成
- 流失预警：服务记录数连续 2 月低于均值 50% 的单位标红

#### 3.7.7 顾问业务数据看板
- 在管顾问单位数 / 总年费 / 续约率 / 服务饱和度
- 各律师的顾问业务量
- TOP 10 高价值顾问单位

**与其他模块的关系**：
- **诉讼仲裁案件管理**：顾问单位偶有诉讼需求时，在案件中标注"由顾问业务转化"，关联回顾问档案
- **非诉法律项目**：顾问单位的项目类业务（如重组、合规审查）走非诉项目模块
- **商务模块**：顾问客户档案、合同、收款均复用商务模块
- **智能问答**：顾问咨询走智能问答（限定顾问单位上下文）
- **文件输出**：合同审查意见、法律意见书走通用文件输出

### 3.7B 非诉法律项目模块（Non-Litigation Legal Project Module）

**业务线**：③ 非诉法律项目。**业主以并购非诉见长，本模块为核心差异化能力**。

#### 3.7B.0 模块定位（核心哲学，业主明确）

> "非诉项目，律师的作用在于**理解并优化交易的商业实质**，清晰界定并完善我方的**商业诉求**，通过律师服务，促进委托人的**商业利益**得以实现。"

本模块**不是法律文档工厂**——它是 **"项目大脑（Project Brain）"**：帮助律师管理一笔交易从商业诉求到商业利益实现的全流程。文书（SPA、配套文本等）是工作成果的**固化形式**，不是工作的核心。

**律师的工作模式（业主明确的四阶段）**：

```
A 客户沟通讨论 → B 多轮次对手方谈判 → C 谈判成果书面固化 → D 程序性流程闭环
   （理解商业实质     （在我方诉求与对方       （以法律文本               （工商、税务、外汇、
   清晰商业诉求）       诉求之间寻找平衡）       锁定双方共识）             反垄断申报等）
```

模块按这四阶段组织功能，每阶段都有 AI 辅助：

| 阶段 | 律师做什么 | 系统支持 | AI 价值 |
| --- | --- | --- | --- |
| **A 商业诉求** | 与客户多轮访谈，把商业目标拆解为可执行的法律请求 | 商业诉求清单、利益相关方分析、交易结构选项分析、立场矩阵 | 帮律师把模糊商业诉求结构化、提示遗漏维度、对比交易架构利弊 |
| **B 谈判管理** | 多轮次与对方谈判，跟踪议题进展，记录策略与让步 | 议题追踪器、谈判轮次管理、立场矩阵、会议纪要、策略 playbook | 起草发问提纲、风险点识别、对方立场分析、让步路径建议 |
| **C 成果固化** | 把谈判共识落到 SPA、SHA、章程、披露函等文本 | 议题 ↔ 条款映射、文本版本控制、条款级追溯 | 起草条款、红黑线对比、条款合规与异常识别、披露函生成 |
| **D 程序闭环** | 完成工商变更、税务、外汇、反垄断申报等程序 | 程序清单（按交易类型）、办理状态、凭证归档 | 程序所需文件清单生成、申请书起草、监管时点提醒 |

**贯穿四阶段的横向能力**：
- 项目档案与阶段管理
- 客户决策记录（每个关键决策都留痕，含授权范围与决定）
- 法律尽职调查（**为商业诉求与谈判提供事实基础**，不是孤立产物）
- 项目交付物追踪（dashboard 视图）
- 项目预算与计费

**项目类型（首批支持）**：
- **股权并购（Equity M&A）** ⭐ 业主主战场，作为首批落地的标杆模板
- 资产收购 / 业务收购
- 私募融资 / 股权融资
- IPO 上市辅导
- 重组与重整
- 公司合规
- 跨境交易
- 其他

每种项目类型有独立的阶段配置、商业诉求维度、尽调清单、交付物清单、程序清单模板。

**项目阶段（v2.1 调整以贴合四工作阶段）**：
```
立项 → 商业诉求确认 → 尽调 → 谈判 → 成果固化 → 签约 → 交割 → 程序闭环 → 交割后整合
        (阶段 A)              (阶段 B) (阶段 C)         (阶段 D)
```
- 每个阶段都有标准交付物 checklist 与"过门检查"
- 项目看板（Kanban）按阶段聚合所有事项与文件
- 阶段切换需主办律师确认（避免遗漏关键产出物）

---

### 阶段 A：商业诉求拆解（业主新增 ⭐ 律师价值核心）

#### 3.7B.A1 商业诉求清单（Commercial Demands List）

> 律师与客户多轮访谈后，把客户脑海里"我想买（卖）这家公司、要 XXX 价格、希望 XXX 条件"等模糊期望，拆解为**结构化、可谈判、可法律实现**的诉求清单。

**字段**：
- 诉求编号 / 诉求标题
- 诉求描述（客户原话 + 律师改写后的法律可执行版）
- 维度：交易结构 / 价款与支付 / 控制权与治理 / 陈述与保证 / 赔偿与限额 / 过渡期安排 / 不竞争与不挖角 / 知识产权 / 关键人员 / 政府审批 / 退出机制 / 其他
- **优先级**：必须达成（Must）/ 期望达成（Should）/ 可让步（Nice to Have）/ 可放弃（Walk-Away If Lost）
- **底线 / 目标 / 理想**（三档定位）
- 法律实现路径：要在哪份文本的哪一条款中体现
- 风险与依赖：是否依赖某项尽调发现、是否需要政府审批配合
- 状态：待澄清 / 已确认 / 谈判中 / 已落地 / 放弃
- 客户决策时点 / 决策人 / 决策依据

**功能**：
- AI 辅助拆解：律师粘贴客户访谈记录或邮件 → AI 抽取潜在商业诉求 → 律师审核入库
- AI 辅助"维度提醒"：对比该项目类型的标准诉求清单，提示遗漏维度
- AI 辅助"路径映射"：建议每条诉求应落在哪份文本、哪个条款类型上

#### 3.7B.A2 交易结构选项分析

> 同一个商业目标可能有多种交易结构（股权 vs 资产收购、一步 vs 分阶段、含/不含对赌等），不同架构对客户的税务、风险、控制权影响不同。

- 选项 CRUD：每个候选结构 + 优劣对比表
- AI 辅助生成对比矩阵（税务影响、合规复杂度、交易速度、风险分担、退出灵活性）
- 客户决策记录：选择哪个结构、决策依据

#### 3.7B.A3 立场矩阵（Position Matrix）

把诉求清单转化为可在谈判桌上使用的"我方立场表"。

| 议题 | 我方理想 | 我方目标 | 我方底线 | 预测对方立场 | ZOPA | 让步换取条件 |
| --- | --- | --- | --- | --- | --- | --- |

---

### 阶段 B：谈判过程管理（业主新增 ⭐ "多轮次地和交易对手方进行沟通谈判"）

#### 3.7B.B1 谈判轮次管理（Negotiation Rounds）

每一轮谈判都要留痕：

- 轮次编号（R1、R2、R3...）
- 时间 / 地点 / 形式（视频 / 现场 / 邮件 / 电话）
- 我方参与人 / 对方参与人
- 议题清单（本轮讨论的）
- 会议纪要：谈拢的、悬而未决的、新出现的、恶化的
- 当轮立场变化（哪些议题立场松动 / 哪些固化）
- 下一步行动与负责人
- 关联文件（会议邀请、对方提案、本方反提案）

#### 3.7B.B2 议题追踪器（Issue Tracker）

> 一笔 M&A 交易往往有 30-100 个议题在谈，必须有专门的追踪器。

**字段**（每个议题一条）：
- 议题编号 / 标题 / 描述
- 关联商业诉求（来自 §3.7B.A1）
- 类别（与诉求维度对齐）
- 状态：未提出 / 提出中 / 谈判中 / 双方一致 / 搁置 / 放弃
- 我方当前立场 / 对方当前立场 / 差距分析
- 谈判轮次足迹（在哪几轮中讨论过、各轮变化）
- 优先级 / 紧迫度
- 责任律师
- 落到文本：哪份文本的哪一条款（关联到 §3.7B.C1）
- 解决日期

**视图**：Kanban 看板 / 优先级仪表盘 / 议题演变时间线。

#### 3.7B.B3 谈判策略与让步管理

- 让步路径预案：在 议题 X 上让步以换取议题 Y 的进展
- 红线提醒：尝试触碰我方底线时系统提示
- 谈判 playbook：常用让步话术、僵局突破策略（基于知识库沉淀）

#### 3.7B.B4 客户决策记录（Client Decision Log）

> 每个关键决策都必须留痕——这既是律师执业留底，也是客户授权链。

- 决策编号 / 时间 / 决策人（客户方姓名 / 职务）
- 决策事项（链接到具体议题 / 文本条款）
- 决策内容
- 决策依据（律师建议 / 商业考虑 / 客户原因）
- 授权范围（律师可在 ±X% 范围内自行决定 / 必须客户拍板）
- 留痕方式：会议纪要 / 邮件确认 / 微信截图 / 客户书面授权
- 关联文件

---

### 阶段 C：成果固化（"将相关的谈判成果以书面的形式予以固定"）

#### 3.7B.C1 议题 ↔ 条款映射

> 谈判共识必须**清晰落到文本的具体条款**，每条款必须能追溯到对应议题与商业诉求。

- 文本（如 SPA）的每个条款建立对应关系：
  - 来源议题（链接到 §3.7B.B2）
  - 来源商业诉求（链接到 §3.7B.A1）
  - 谈判轮次足迹（哪几轮、什么变化）
  - 客户决策记录（链接到 §3.7B.B4）
- **文本闭合检查**：是否所有"双方一致"议题都已写入文本？是否有文本条款无对应议题？

#### 3.7B.C2 交易文本起草与版本管理（业主明确要求"全套"）

- 模板库（M&A 标准）：意向书 / Term Sheet、SPA、增资协议、SHA、章程修订、资产收购协议、业务转让协议
- 字段化模板：当事人、标的、对价、对赌、保证、不竞争、违约责任
- 版本管理：与对方往来修订留痕；红黑线对比视图
- AI 异常识别：遗漏条款、不寻常约定

#### 3.7B.C3 配套文本（业主明确要求）

- 公司决议：股东会、董事会、监事会
- 政府文件：工商变更登记申请、外汇登记、反垄断申报、其他备案
- 通知与同意函：股东放弃优先购买权同意书、债权人通知、银行同意函
- 特殊条款协议：对赌协议、回购协议、锁箱协议、过渡期协议
- 披露函（Disclosure Letter）
- 保密协议（NDA）、独家谈判协议、Walk-away Agreement

---

### 阶段 D：程序性流程闭环（业主新增 ⭐ "完成相关的程序性流程，如工商税务手续等"）

#### 3.7B.D1 程序清单生成（按交易类型）

> 程序闭环 = 交易真正完成。律师必须把"签约"和"交付"分清——签约只是开始，交割与程序完成才是终点。

**程序模板（M&A 标准清单）**：

| # | 程序 | 触发条件 | 申请人 | 办理机关 | 所需文件 | 周期 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 工商变更登记（股东 / 法定代表人 / 注册资本 / 章程） | 签约后 | 标的公司 | 市场监督管理局 | 决议、章程修正案、SPA、新股东身份证明 | 3-7 工作日 |
| 2 | 税务备案与个税申报（股权转让所得税） | 股权转让 | 转让方 / 受让方 | 主管税务机关 | SPA、评估报告、计税资料 | 7-15 日 |
| 3 | 外汇登记（涉外资） | 涉境外股东 | 标的公司 | 国家外汇管理局 | 商务部 / 发改委备案、外汇登记申请、相关文件 | 视情况 |
| 4 | 反垄断经营者集中申报 | 达申报标准 | 收购方 | 国家市场监督管理总局 | 申报书、协议、营业额证明 | 立案后 30-180 日 |
| 5 | 行业主管部门审批 | 行业准入 | 标的公司 / 收购方 | 行业主管部门（金融、教育、医疗、电信等） | 视行业 | 视行业 |
| 6 | 国资监管审批 | 涉国资 | 转让方 | 国资委 / 财政厅 | 评估、产权交易、批复 | 视情况 |
| 7 | 章程备案、组织机构、银行预留印鉴变更 | 工商变更后 | 标的公司 | 银行 / 相关部门 | 新章程、营业执照、决议 | 1-2 周 |
| 8 | 行业资质 / 许可证变更 | 影响许可的变更 | 标的公司 | 相关许可机关 | 视许可类型 | 视情况 |

**功能**：
- 系统按项目类型自动生成程序清单，律师按需勾选适用项
- 每项程序：状态（未启动 / 准备中 / 已申请 / 在办 / 已完成 / 阻塞）、负责人、计划日期、实际日期、办理凭证
- 程序所需文件清单：与项目卷宗联动，缺失文件自动标红
- 关键时点提醒：申报前 N 日提醒
- 程序完成 → 上传凭证（受理回执、批复、新营业执照、税务回执等）

#### 3.7B.D2 程序申请书与办理文件生成

- 工商变更登记申请书（股东、法定代表人、注册资本、章程等）
- 税务备案表
- 外汇登记申请
- 反垄断经营者集中申报书
- 行业准入审批申请

#### 3.7B.D3 程序闭环看板

- 项目维度：每笔交易的程序进度一览
- 律师维度：手头所有项目的程序待办
- 风险维度：超期未办、文件缺失的程序

---

### 横向能力（贯穿四阶段）

#### 3.7B.X1 法律尽职调查（业主明确要求）

> **重要重定位**：尽调不是孤立产物，而是为**商业诉求拆解（A）和谈判（B）提供事实基础**——发现的风险点会直接转化为商业诉求（如调价、特殊陈述与保证、保留款）。

- 立项后或商业诉求确认后启动
- 清单结构（M&A 模板示例）：公司基本资料、重大合同、财产权属、员工与劳动、税务与海关、合规与诉讼、资质与许可、关联方、历史融资、对赌
- 每项条目状态：未发出 / 已发出 / 已收到 / 已审阅 / 有问题待跟进 / 已关闭
- 与对方接口人协作：导出对方版（隐藏内部备注）
- **尽调发现 → 商业诉求 / 议题转化机制**：每个高风险发现一键转为商业诉求或谈判议题
- 现场访谈管理：访谈提纲、访谈记录、与清单条目关联
- 资料审阅：每项资料填写"主要发现 / 风险等级 / 建议"

#### 3.7B.X2 法律尽职调查报告（业主明确要求）

- 结构化模板：执行摘要 / 调查范围与方法 / 公司基本情况 / 重大事项分类报告 / 主要风险与建议 / 附件
- AI 辅助生成：基于已审阅的尽调资料与已登记的尽调发现，自动生成报告初稿
- 律师精修 + 合伙人审核
- 输出：PDF + Word，含保密水印

#### 3.7B.X3 法律意见书（业主明确要求）

- 项目法律意见、专项法律意见、合规法律意见
- 信息收集 → AI 辅助生成 → 律师精修 → 出具
- 与尽调报告 / 商业诉求 / 谈判议题联动，可作为论证依据

#### 3.7B.X4 项目交付物追踪

- 项目级 dashboard：每项交付物的状态（未开始 / 进行中 / 待审核 / 已交付）
- 阶段切换的"过门检查"：必交付物未完成时阻止进入下一阶段
- 客户视图（受限）：客户可看到项目进度、已交付清单、待客户配合事项
- 交付物归档：项目结束自动打包 ZIP 归档（可作客户最终交付包）

#### 3.7B.X5 项目数据看板

- 在办项目数 / 项目金额 / 各阶段分布
- 主办律师项目工作量
- 项目周期分析（同类项目平均耗时）
- **谈判轮次中位数、议题平均解决周期**（v2.1 新增）
- **程序闭环耗时分布**（v2.1 新增）

**与其他模块的关系**：
- **客户与卷宗**：项目共享客户档案与卷宗体系
- **智能问答**：项目级 AI 问答（上下文限定为项目卷宗、尽调发现、商业诉求、谈判议题）
- **文件输出**：尽调报告、法律意见、交易文本、配套文本、程序申请文件均走文件输出
- **商务模块**：项目报价、合同、收款均走商务模块
- **法律顾问模块**：顾问单位的项目可在两个模块间联动

### 3.8 虚拟法庭（Virtual Court）

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

### 3.9 使用手册（User Manual / Help Center）

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

### 4.1 ER 概览（按业务线组织）

```
users ──┬── cases (诉讼仲裁) ──┬── case_files
        │                       ├── case_parties ── parties
        │                       ├── case_timeline
        │                       └── documents
        │
        ├── projects (非诉项目) ──┬── project_phases
        │                          ├── dd_checklists ── dd_items ── dd_responses
        │                          ├── dd_findings (尽调发现)
        │                          ├── transaction_documents (交易文本)
        │                          ├── project_deliverables (交付物追踪)
        │                          └── project_files
        │
        ├── advisor_clients (顾问) ──┬── advisor_services
        │                             ├── advisor_renewals
        │                             ├── advisor_monthly_reports
        │                             ├── contract_reviews
        │                             ├── legal_opinions
        │                             └── advisor_queries (咨询工单)
        │
        ├── clients ──┬── cases / projects / advisor_clients
        │             ├── quotations
        │             ├── engagement_letters
        │             └── receivables ── payments
        │
        ├── conversations ── messages (跨业务线)
        ├── documents (跨业务线，按 source_type 区分归属)
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

-- 客户（商务模块的客户档案，与诉讼当事人 parties 区分）
CREATE TABLE clients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type TEXT NOT NULL CHECK (type IN ('person','org')),
  name TEXT NOT NULL,
  industry TEXT,
  scale TEXT,                               -- small/medium/large
  source TEXT,                              -- referral/inbound/老客户/marketing
  level TEXT DEFAULT 'normal',              -- vip/normal/watch
  status TEXT DEFAULT 'lead',               -- lead/active/advisor/historical
  primary_contact JSONB,                    -- 姓名/职务/电话/邮箱
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 报价
CREATE TABLE quotations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID REFERENCES cases(id) ON DELETE SET NULL,
  client_id UUID REFERENCES clients(id),
  fee_model TEXT,                           -- hourly/fixed/staged/contingency
  base_fee NUMERIC(12,2),
  contingency_pct NUMERIC(5,2),
  estimated_costs JSONB,
  discount_pct NUMERIC(5,2),
  total NUMERIC(12,2),
  valid_until DATE,
  status TEXT DEFAULT 'draft',              -- draft/sent/accepted/rejected/expired
  approved_by UUID REFERENCES users(id),    -- 高额折扣需合伙人审批
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 委托代理合同
CREATE TABLE engagement_letters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID REFERENCES cases(id) ON DELETE SET NULL,
  client_id UUID REFERENCES clients(id),
  quotation_id UUID REFERENCES quotations(id),
  template_type TEXT,                       -- civil/criminal/admin/advisor/special/arbitration
  storage_key TEXT,                         -- 生成的合同文件
  signed_at DATE,
  start_date DATE,
  end_date DATE,
  total_fee NUMERIC(12,2),
  status TEXT DEFAULT 'draft',              -- draft/sent/signed/terminated
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 应收账款
CREATE TABLE receivables (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES clients(id),
  case_id UUID REFERENCES cases(id) ON DELETE SET NULL,
  engagement_letter_id UUID REFERENCES engagement_letters(id),
  total_amount NUMERIC(12,2),
  paid_amount NUMERIC(12,2) DEFAULT 0,
  due_date DATE,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 收款记录
CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  receivable_id UUID REFERENCES receivables(id) ON DELETE CASCADE,
  amount NUMERIC(12,2) NOT NULL,
  paid_at DATE NOT NULL,
  method TEXT,                              -- transfer/cash/check
  voucher_no TEXT,
  invoice_no TEXT,
  invoice_date DATE,
  recorded_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 顾问单位档案
CREATE TABLE advisor_clients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES clients(id) NOT NULL,
  advisor_type TEXT NOT NULL,               -- annual/special/project
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  auto_renewal BOOLEAN DEFAULT FALSE,
  annual_fee NUMERIC(12,2),
  payment_schedule TEXT,                    -- annual/semi-annual/quarterly
  service_quotas JSONB,                     -- {consulting:50/月, contract_review:10/月, on-site:4/年}
  scope TEXT,                               -- 服务范围描述
  lead_lawyer_id UUID REFERENCES users(id),
  team_lawyer_ids UUID[],
  status TEXT DEFAULT 'active',             -- active/expired/terminated
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 顾问服务记录
CREATE TABLE advisor_services (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  advisor_client_id UUID REFERENCES advisor_clients(id) ON DELETE CASCADE,
  service_date DATE NOT NULL,
  service_type TEXT NOT NULL,               -- phone/email/onsite/contract_review/opinion/training/drafting
  duration_minutes INT,
  summary TEXT NOT NULL,                    -- 客户可见
  internal_notes TEXT,                      -- 仅本所可见
  related_file_ids UUID[],                  -- 关联 case_files / documents
  count_against_quota BOOLEAN DEFAULT TRUE,
  extra_billable BOOLEAN DEFAULT FALSE,
  served_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 顾问月度报告
CREATE TABLE advisor_monthly_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  advisor_client_id UUID REFERENCES advisor_clients(id) ON DELETE CASCADE,
  year INT NOT NULL,
  month INT NOT NULL,
  storage_key TEXT,                         -- PDF 文件
  stats JSONB,                              -- {total_services, by_type, quota_usage}
  status TEXT DEFAULT 'draft',              -- draft/sent
  sent_at TIMESTAMPTZ,
  UNIQUE (advisor_client_id, year, month)
);

-- 顾问续约
CREATE TABLE advisor_renewals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  advisor_client_id UUID REFERENCES advisor_clients(id) ON DELETE CASCADE,
  current_end_date DATE NOT NULL,
  alert_60d_sent BOOLEAN DEFAULT FALSE,
  alert_30d_sent BOOLEAN DEFAULT FALSE,
  alert_7d_sent BOOLEAN DEFAULT FALSE,
  proposed_new_fee NUMERIC(12,2),
  status TEXT DEFAULT 'pending',            -- pending/negotiating/renewed/lost
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 非诉法律项目
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_no TEXT UNIQUE NOT NULL,           -- FB-2026-PRJ-001
  name TEXT NOT NULL,
  client_id UUID REFERENCES clients(id),
  project_type TEXT NOT NULL,                -- m_and_a/asset_acquisition/private_placement/ipo/restructuring/compliance/cross_border/other
  our_role TEXT,                             -- 买方/卖方/标的公司/中立顾问
  counterparty TEXT,                         -- 交易对方
  deal_size NUMERIC(18,2),
  status TEXT DEFAULT 'initiation',          -- initiation/dd/negotiation/signing/closing/post_closing/closed/terminated
  start_date DATE,
  expected_closing_date DATE,
  actual_closing_date DATE,
  lead_lawyer_id UUID REFERENCES users(id),
  team_lawyer_ids UUID[],
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_type ON projects(project_type);

-- 项目阶段
CREATE TABLE project_phases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  phase_name TEXT NOT NULL,                  -- initiation/dd/negotiation/signing/closing/post_closing
  status TEXT DEFAULT 'pending',             -- pending/in_progress/completed
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  notes TEXT
);

-- 尽调清单
CREATE TABLE dd_checklists (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  template_type TEXT,                        -- m_and_a/asset_acquisition/...
  version INT DEFAULT 1,
  generated_at TIMESTAMPTZ DEFAULT now(),
  generated_by UUID REFERENCES users(id)
);

-- 尽调清单条目
CREATE TABLE dd_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  checklist_id UUID REFERENCES dd_checklists(id) ON DELETE CASCADE,
  category TEXT NOT NULL,                    -- 公司基本/重大合同/财产/员工/税务/合规/资质/其他
  sub_category TEXT,
  item_no TEXT,                              -- 1.1, 1.2, 2.1...
  request_text TEXT NOT NULL,                -- 资料请求描述
  priority TEXT DEFAULT 'normal',            -- critical/high/normal/optional
  status TEXT DEFAULT 'not_sent',            -- not_sent/sent/received/under_review/issue/closed
  assignee_id UUID REFERENCES users(id),
  due_date DATE,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 对方对尽调清单的回应
CREATE TABLE dd_responses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dd_item_id UUID REFERENCES dd_items(id) ON DELETE CASCADE,
  response_type TEXT,                        -- file/text/declined
  file_id UUID REFERENCES case_files(id),    -- 复用 case_files 但 source_type='project'
  text_response TEXT,
  responded_at TIMESTAMPTZ DEFAULT now(),
  notes TEXT
);

-- 尽调发现（律师审阅资料后记录）
CREATE TABLE dd_findings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  dd_item_id UUID REFERENCES dd_items(id),
  category TEXT,
  finding TEXT NOT NULL,                     -- 主要发现描述
  risk_level TEXT,                           -- high/medium/low/none
  recommendation TEXT,                       -- 建议措施
  reviewed_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 交易文本（含版本）
CREATE TABLE transaction_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  doc_type TEXT NOT NULL,                    -- term_sheet/spa/sha/articles/asset_purchase/notice/resolution/...
  title TEXT NOT NULL,
  version INT DEFAULT 1,
  storage_key TEXT,                          -- 存于 MinIO
  status TEXT DEFAULT 'draft',               -- draft/sent_to_counterparty/received_revision/agreed/signed
  parent_version_id UUID REFERENCES transaction_documents(id),
  redline_storage_key TEXT,                  -- 红黑线版本
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_tx_docs_project ON transaction_documents(project_id);

-- 项目交付物追踪
CREATE TABLE project_deliverables (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  category TEXT,                             -- dd_checklist/dd_report/legal_opinion/transaction_doc/supporting_doc
  title TEXT NOT NULL,
  required_by_phase TEXT,                    -- 哪个阶段需交付
  status TEXT DEFAULT 'not_started',         -- not_started/in_progress/under_review/delivered
  delivered_at TIMESTAMPTZ,
  delivered_doc_id UUID,                     -- 关联到 documents 或 transaction_documents
  notes TEXT
);

-- 顾问业务的合同审查（独立于一般文件）
CREATE TABLE contract_reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  advisor_client_id UUID REFERENCES advisor_clients(id) ON DELETE CASCADE,
  contract_title TEXT NOT NULL,
  original_file_id UUID REFERENCES case_files(id),
  ai_findings JSONB,                         -- AI 输出的风险点 + 建议
  reviewed_by UUID REFERENCES users(id),
  review_opinion_doc_id UUID,                -- 关联出具的审查意见
  redline_file_id UUID,                      -- 红黑线版
  status TEXT DEFAULT 'submitted',           -- submitted/reviewing/completed
  service_record_id UUID REFERENCES advisor_services(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 顾问业务的法律意见
CREATE TABLE legal_opinions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_type TEXT NOT NULL,                 -- advisor/project/case
  source_id UUID NOT NULL,                   -- 多态外键
  title TEXT NOT NULL,
  opinion_type TEXT,                         -- 专项/合规/争议解决/交易结构
  storage_key TEXT,
  version INT DEFAULT 1,
  issued_at DATE,
  issued_by UUID REFERENCES users(id),
  reviewed_by_partner UUID REFERENCES users(id),
  status TEXT DEFAULT 'draft',               -- draft/under_review/issued
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 顾问咨询工单
CREATE TABLE advisor_queries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  advisor_client_id UUID REFERENCES advisor_clients(id) ON DELETE CASCADE,
  query_text TEXT NOT NULL,
  submitted_by_external TEXT,                -- 客户对接人
  submitted_at TIMESTAMPTZ DEFAULT now(),
  assigned_to UUID REFERENCES users(id),
  response_text TEXT,
  responded_at TIMESTAMPTZ,
  status TEXT DEFAULT 'open',                -- open/in_progress/answered/closed
  service_record_id UUID REFERENCES advisor_services(id)
);

-- ============================================================
-- 非诉项目 v2.1 新增：商业诉求 / 谈判 / 客户决策 / 程序闭环
-- ============================================================

-- 商业诉求清单（阶段 A）
CREATE TABLE commercial_demands (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  demand_no TEXT NOT NULL,                   -- D1, D2, D3...
  title TEXT NOT NULL,
  description_raw TEXT,                      -- 客户原话
  description_legal TEXT,                    -- 律师改写后的法律可执行版
  dimension TEXT NOT NULL,                   -- structure/price/control/reps/indemnity/transition/non_compete/ip/key_person/approvals/exit/other
  priority TEXT NOT NULL,                    -- must/should/nice/walk_away
  walk_away_position TEXT,                   -- 底线
  target_position TEXT,                      -- 目标
  ideal_position TEXT,                       -- 理想
  legal_implementation_path TEXT,            -- 落到哪份文本哪一条款
  depends_on_dd_finding_ids UUID[],
  depends_on_approvals TEXT,
  status TEXT DEFAULT 'draft',               -- draft/confirmed/negotiating/landed/abandoned
  client_decision_id UUID,                   -- 关联客户决策记录
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_demands_project ON commercial_demands(project_id);
CREATE INDEX idx_demands_priority ON commercial_demands(priority);

-- 交易结构选项分析（阶段 A）
CREATE TABLE structure_options (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  option_name TEXT NOT NULL,                 -- 如 "一步股权收购"、"先增资后转让"
  description TEXT,
  pros JSONB,                                -- 优势列表
  cons JSONB,                                -- 劣势列表
  tax_impact TEXT,
  compliance_complexity TEXT,                -- low/medium/high
  estimated_timeline TEXT,
  is_selected BOOLEAN DEFAULT FALSE,
  selection_rationale TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 立场矩阵（阶段 A，常按议题展开）
CREATE TABLE position_matrix (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  issue_id UUID,                             -- 关联议题
  ideal TEXT,
  target TEXT,
  walk_away TEXT,
  predicted_counterparty_position TEXT,
  zopa TEXT,                                 -- Zone of Possible Agreement
  concession_trade TEXT,                     -- 让步换取条件
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 谈判轮次（阶段 B）
CREATE TABLE negotiation_rounds (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  round_no INT NOT NULL,                     -- R1, R2...
  scheduled_at TIMESTAMPTZ,
  location TEXT,
  format TEXT,                               -- video/onsite/email/phone
  our_attendees TEXT[],
  counterparty_attendees TEXT[],
  agenda TEXT,
  minutes TEXT,                              -- 会议纪要
  outcome_summary TEXT,                      -- 当轮总结
  next_actions TEXT,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (project_id, round_no)
);

-- 议题追踪器（阶段 B）
CREATE TABLE negotiation_issues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  issue_no TEXT NOT NULL,                    -- I1, I2...
  title TEXT NOT NULL,
  description TEXT,
  related_demand_id UUID REFERENCES commercial_demands(id),
  category TEXT,                             -- 与诉求维度对齐
  status TEXT DEFAULT 'not_raised',          -- not_raised/proposed/negotiating/agreed/parked/abandoned
  our_current_position TEXT,
  counterparty_current_position TEXT,
  gap_analysis TEXT,
  priority TEXT,
  urgency TEXT,
  responsible_lawyer_id UUID REFERENCES users(id),
  resolved_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (project_id, issue_no)
);
CREATE INDEX idx_issues_project_status ON negotiation_issues(project_id, status);

-- 议题在某轮谈判中的状态变化（多对多）
CREATE TABLE issue_round_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  issue_id UUID REFERENCES negotiation_issues(id) ON DELETE CASCADE,
  round_id UUID REFERENCES negotiation_rounds(id) ON DELETE CASCADE,
  status_before TEXT,
  status_after TEXT,
  position_change TEXT,                      -- 描述当轮我方/对方立场变化
  notes TEXT,
  recorded_at TIMESTAMPTZ DEFAULT now()
);

-- 客户决策记录（贯穿四阶段）
CREATE TABLE client_decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  decision_no TEXT NOT NULL,                 -- DEC-1, DEC-2...
  decided_at TIMESTAMPTZ NOT NULL,
  decided_by_external TEXT,                  -- 客户方姓名 / 职务
  subject TEXT NOT NULL,                     -- 决策事项
  related_demand_id UUID REFERENCES commercial_demands(id),
  related_issue_id UUID REFERENCES negotiation_issues(id),
  related_clause TEXT,                       -- 关联文本条款
  decision_content TEXT NOT NULL,
  rationale TEXT,
  authority_scope TEXT,                      -- 律师授权范围
  evidence_type TEXT,                        -- meeting_minutes/email/wechat/written_authorization
  evidence_file_id UUID REFERENCES case_files(id),
  recorded_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 议题 ↔ 条款映射（阶段 C）
CREATE TABLE issue_clause_mapping (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  issue_id UUID REFERENCES negotiation_issues(id) ON DELETE CASCADE,
  document_id UUID REFERENCES transaction_documents(id) ON DELETE CASCADE,
  clause_label TEXT,                         -- 第 X 条第 Y 款
  clause_excerpt TEXT,                       -- 条款摘录
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (issue_id, document_id, clause_label)
);

-- 程序性流程清单（阶段 D）
CREATE TABLE procedural_filings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  filing_type TEXT NOT NULL,                 -- aic_change/tax_filing/forex/antitrust/industry_approval/soe_approval/license_change/bank_change/other
  title TEXT NOT NULL,
  authority TEXT,                            -- 办理机关
  trigger_condition TEXT,                    -- 触发条件
  applicant TEXT,                            -- 申请人（标的公司 / 转让方 / 收购方）
  required_files JSONB,                      -- 所需文件清单
  expected_duration_days INT,
  planned_start_date DATE,
  planned_end_date DATE,
  actual_start_date DATE,
  actual_end_date DATE,
  status TEXT DEFAULT 'not_started',         -- not_started/preparing/submitted/in_progress/completed/blocked
  responsible_lawyer_id UUID REFERENCES users(id),
  receipt_file_id UUID REFERENCES case_files(id),
  approval_file_id UUID REFERENCES case_files(id),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_filings_project_status ON procedural_filings(project_id, status);
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

### 5.6 商务模块
| Method | Path | 说明 |
| --- | --- | --- |
| GET | `/clients?status=&level=&q=` | 客户列表 |
| POST | `/clients` | 创建客户 |
| GET | `/clients/{id}` | 客户详情（聚合：报价/合同/收款/案件/顾问） |
| POST | `/quotations` | 创建报价 |
| POST | `/quotations/{id}/send` | 发送给客户 |
| POST | `/quotations/{id}/accept` | 客户接受 → 自动生成合同草稿 |
| POST | `/engagement-letters` | 生成委托代理合同 |
| POST | `/engagement-letters/{id}/sign` | 标记签订 |
| GET | `/receivables?overdue=true` | 应收账款（可筛选逾期） |
| POST | `/receivables/{id}/payments` | 登记收款 |

### 5.7 法律顾问模块
| Method | Path | 说明 |
| --- | --- | --- |
| GET | `/advisor-clients?status=&lead=` | 顾问单位列表 |
| POST | `/advisor-clients` | 创建顾问关系（基于已有 client） |
| GET | `/advisor-clients/{id}` | 详情（含服务统计、限额使用） |
| POST | `/advisor-clients/{id}/services` | 登记一条服务记录 |
| GET | `/advisor-clients/{id}/services?from=&to=&type=` | 服务记录查询 |
| POST | `/advisor-clients/{id}/contract-reviews` | 提交合同审查（子功能 ①） |
| GET | `/contract-reviews/{id}` | 审查详情（AI 发现 + 律师意见） |
| POST | `/advisor-clients/{id}/legal-opinions` | 出具法律意见书（子功能 ②） |
| POST | `/advisor-clients/{id}/reports/{year}/{month}/generate` | 生成月度工作汇报（子功能 ③） |
| POST | `/advisor-clients/{id}/reports/{report_id}/send` | 发送报告给客户 |
| POST | `/advisor-clients/{id}/queries` | 法律咨询工单（子功能 ④） |
| POST | `/advisor-queries/{id}/answer` | 律师答复咨询 |
| GET | `/advisor-renewals?within_days=60` | 续约预警列表 |
| GET | `/advisor-clients/dashboard` | 顾问业务数据看板 |

### 5.8 非诉法律项目模块
| Method | Path | 说明 |
| --- | --- | --- |
| **项目档案** | | |
| GET | `/projects?type=&status=&lead=` | 项目列表 |
| POST | `/projects` | 创建项目（指定类型自动配置阶段、诉求维度、尽调清单、程序清单） |
| GET | `/projects/{id}` | 项目详情聚合（阶段 / 诉求 / 议题 / 谈判轮次 / 文本 / 程序 / 交付物） |
| PATCH | `/projects/{id}/phase` | 切换项目阶段（含过门检查） |
| GET | `/projects/dashboard` | 项目数据看板 |
| **阶段 A：商业诉求** | | |
| GET | `/projects/{id}/demands` | 商业诉求清单 |
| POST | `/projects/{id}/demands` | 新增商业诉求 |
| POST | `/projects/{id}/demands/extract-from-text` | AI 从访谈记录 / 邮件抽取候选诉求 |
| POST | `/projects/{id}/demands/check-completeness` | AI 提示遗漏维度 |
| POST | `/projects/{id}/structure-options` | 添加交易结构候选方案 |
| POST | `/projects/{id}/structure-options/compare` | AI 生成对比矩阵 |
| GET/PUT | `/projects/{id}/position-matrix` | 立场矩阵 CRUD |
| **阶段 B：谈判管理** | | |
| GET | `/projects/{id}/negotiation-rounds` | 谈判轮次列表 |
| POST | `/projects/{id}/negotiation-rounds` | 新建一轮谈判记录 |
| POST | `/negotiation-rounds/{id}/minutes` | 上传 / 编辑会议纪要 |
| GET | `/projects/{id}/issues?status=&priority=` | 议题追踪器 |
| POST | `/projects/{id}/issues` | 新建议题 |
| PATCH | `/issues/{id}` | 更新议题状态 / 立场 |
| POST | `/issues/{id}/round-log` | 记录议题在某轮的变化 |
| GET | `/projects/{id}/issues/timeline` | 议题演变时间线 |
| POST | `/issues/{id}/ai-suggest` | AI 建议立场分析 / 让步路径 |
| GET | `/projects/{id}/decisions` | 客户决策记录 |
| POST | `/projects/{id}/decisions` | 登记客户决策 |
| **阶段 C：成果固化** | | |
| POST | `/projects/{id}/transaction-documents` | 创建交易文本 |
| POST | `/transaction-documents/{id}/versions` | 上传新版本 |
| GET | `/transaction-documents/{id}/redline?against={other_id}` | 红黑线对比 |
| POST | `/transaction-documents/{id}/clauses/{label}/map` | 映射条款 ↔ 议题 |
| GET | `/projects/{id}/text-closure-check` | 文本闭合检查（议题与条款一致性） |
| **阶段 D：程序闭环** | | |
| GET | `/projects/{id}/procedural-filings` | 程序清单 |
| POST | `/projects/{id}/procedural-filings/generate` | 按项目类型自动生成程序清单 |
| PATCH | `/procedural-filings/{id}` | 更新程序状态 |
| POST | `/procedural-filings/{id}/upload-receipt` | 上传办理凭证 |
| POST | `/procedural-filings/{id}/generate-application` | 生成申请书草稿 |
| **横向能力** | | |
| POST | `/projects/{id}/dd-checklists/generate` | 按项目类型生成尽调清单 |
| GET/PATCH | `/dd-items/{id}` | 尽调条目操作 |
| POST | `/dd-items/{id}/responses` | 上传对方回应 |
| GET | `/projects/{id}/dd-checklists/{cl_id}/export` | 导出对方版（脱敏） |
| POST | `/projects/{id}/dd-findings` | 登记尽调发现 |
| POST | `/dd-findings/{id}/convert-to-demand` | 一键转为商业诉求 |
| POST | `/dd-findings/{id}/convert-to-issue` | 一键转为谈判议题 |
| POST | `/projects/{id}/dd-report/generate` | 生成尽调报告 |
| POST | `/projects/{id}/legal-opinions` | 出具项目法律意见书 |
| GET | `/projects/{id}/deliverables` | 交付物清单与状态 |

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
| Sprint 0 | 基础设施 + CI + 部署 + 业务线导航骨架 | 1 周 |
| Sprint 1 | 账户 + 客户档案 + 诉讼仲裁案件管理 | 2 周 |
| Sprint 2 | 卷宗上传 + OCR + 全文搜索（跨业务线） | 1.5 周 |
| Sprint 3 | 智能问答（含 Tool Use + Caching，按业务线注入 Skill） | 2 周 |
| Sprint 4 | 文件输出（**诉讼模板全套**：起诉/答辩/反诉/管辖异议/证据目录/证据三性/再审/执行/仲裁/规范性文件） | 2 周 |
| Sprint 5 | 商务模块（CRM + 报价 + 合同 + 收款） | 1.5 周 |
| Sprint 6 | 法律顾问服务模块（档案 + 服务 + **合同审查 + 法律意见 + 月度汇报 + 咨询响应** + 续约） | 2 周 |
| Sprint 7 | **非诉项目 - 阶段 A 商业诉求**：项目档案 + 阶段管理 + **商业诉求清单** + 交易结构选项 + 立场矩阵 + 尽调清单 + 尽调发现 | 2 周 |
| Sprint 8 | **非诉项目 - 阶段 B 谈判管理**：**谈判轮次** + **议题追踪器** + 立场分析 + **客户决策记录** + AI 议题转化 | 1.5 周 |
| Sprint 9 | **非诉项目 - 阶段 C 成果固化**：交易文本 + 配套文本 + 红黑线 + **议题↔条款映射** + **文本闭合检查** + 尽调报告 + 法律意见书 | 2 周 |
| Sprint 10 | **非诉项目 - 阶段 D 程序闭环**：程序清单 + 申请书生成 + 凭证归档 + 程序看板 ｜ + 项目交付物 dashboard | 1 周 |
| Sprint 11 | 虚拟法庭（外脑）+ 使用手册（内嵌帮助 + PDF 导出） | 2 周 |
| Sprint 12 | UAT + 加固 + 培训交付 | 1.5 周 |
| **合计** | **MVP 上线** | **20 周** |

> **说明**（v2.1 哲学校正）：
> - 非诉模块按业主四个工作阶段（商业诉求 / 谈判 / 固化 / 程序）独立组织 Sprint，强化"律师价值在商业实质与谈判过程"，不只是输出文档。
> - **Sprint 8 谈判管理**和 **Sprint 10 程序闭环**是 v2.1 新增的核心 Sprint。
> - **若需压缩工期至 18-19 周**：可将"程序闭环"中的程序申请书生成移至 v2（保留清单与状态追踪），或将"虚拟法庭"暂缓至 v2。
> - 客户档案（`clients` 表）在 Sprint 1 与诉讼仲裁案件管理一起建立，后续商务、顾问、非诉项目均复用。
> - 使用手册的 Markdown 内容编写在 Sprint 1-10 期间**与各模块开发并行**完成。

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

**修订历史**：

| 版本 | 日期 | 修订内容 |
| --- | --- | --- |
| v1.0 | 2026-05-10 | 初稿（8 大模块） |
| v1.1 | 2026-05-10 | 商务报价 → 商务模块（CRM + 报价 + 合同 + 收款）；新增法律顾问模块；MVP 模块数 8 → 9；工期 12.5 → 14.5 周 |
| v2.0 | 2026-05-10 | **重大架构调整**：按律所"三大业务线"（常法 / 诉讼仲裁 / 非诉项目）重新组织顶层结构；新增非诉法律项目模块（含尽调清单、尽调报告、法律意见书、交易文本、配套文本，业主以并购非诉见长）；扩展诉讼仲裁文书模板（新增反诉状、管辖权异议、证据目录、证据三性、再审、执行、仲裁、规范性文件等）；法律顾问模块明确 4 大子功能（合同审查 / 法律意见 / 定期汇报 / 法律咨询）；MVP 模块数 9 → 10；工期 14.5 → 18.5 周 |
| v2.1 | 2026-05-10 | **非诉模块哲学校正**（业主明确律师价值在"理解并优化交易商业实质，清晰界定我方商业诉求，促进委托人商业利益实现"）：模块按业主四个工作阶段重组 —— **阶段 A 商业诉求拆解**（新增商业诉求清单、交易结构选项分析、立场矩阵）；**阶段 B 谈判过程管理**（新增谈判轮次、议题追踪器、客户决策记录）；**阶段 C 成果固化**（新增议题↔条款映射、文本闭合检查）；**阶段 D 程序闭环**（新增工商/税务/外汇/反垄断/行业审批等程序清单与办理追踪）。数据库新增 9 张表（commercial_demands、structure_options、position_matrix、negotiation_rounds、negotiation_issues、issue_round_log、client_decisions、issue_clause_mapping、procedural_filings）。工期 18.5 → 20 周 |

**评审记录**：（待评审后追加）
