# 律师事务所智能体项目 · 文档索引

本目录是 **Fine Bridge Legal Firm AI Agent** 项目的全部交付文档入口。

## 项目三大正式交付文档

| # | 文档 | 用途 | 适合谁先看 |
| --- | --- | --- | --- |
| 1 | [`requirements.md`](./requirements.md) | **智能体需求说明书** —— 业务背景、功能/非功能需求、约束、风险 | 业务方、合伙人、项目发起人 |
| 2 | [`architecture.md`](./architecture.md) | **解决方案** —— 硬件、技术栈、模块设计、Claude 集成、Schema、API、部署、成本 | 技术负责人、开发团队、IT |
| 3 | [`acceptance-and-training.md`](./acceptance-and-training.md) | **验收与培训计划** —— 验收用例、安全自查、培训日程、通关考核、交接清单 | 项目经理、培训师、合伙人 |

## 合伙人评审入口（开工前必读）

| 文档 | 用途 |
| --- | --- |
| [`review-package.md`](./review-package.md) | **合伙人评审包** —— 执行摘要 + 12 项决策清单（含推荐方案）+ 红线核查 + 签字表。**开工前 30 分钟阅读决策。** |

## 阅读顺序建议

```
新加入项目的合伙人 / 律师：
   requirements.md (§1-3 业务) → architecture.md (§0 范围) → user-manual/

新加入项目的开发：
   requirements.md (全文) → architecture.md (全文) → acceptance-and-training.md (§4 用例)

新加入项目的 IT / admin：
   architecture.md (§1,§7) → acceptance-and-training.md (§7 安全清单, §10 admin 培训)

新人入职试用：
   user-manual/01-quick-start/ → user-manual/02-modules/
```

## 关联资源

### Claude Skill（AI 行为准则）
| 文件 | 说明 |
| --- | --- |
| [`../skills/legal-firm-agent/SKILL.md`](../skills/legal-firm-agent/SKILL.md) | 律师事务所智能体的核心 Skill，定义 AI 八阶段工作流与必守原则 |

### 工作流模板（律师手工或 AI 辅助填写）

**业务线 ② 诉讼仲裁案件代理**
| 文件 | 阶段 |
| --- | --- |
| [`../templates/legal-case-intake.md`](../templates/legal-case-intake.md) | ① 接案 |
| [`../templates/legal-case-analysis.md`](../templates/legal-case-analysis.md) | ② 案情梳理 + ③ 法律检索 |
| [`../templates/legal-evidence-checklist.md`](../templates/legal-evidence-checklist.md) | ④ 证据组织 |
| [`../templates/legal-document-drafting.md`](../templates/legal-document-drafting.md) | ⑤ 司法文书全套（v2.0 扩展：反诉/管辖异议/证据目录/三性/再审/执行/保全/仲裁/规范性文件） |
| [`../templates/legal-trial-preparation.md`](../templates/legal-trial-preparation.md) | ⑥ 庭审准备 |
| [`../templates/legal-case-tracking.md`](../templates/legal-case-tracking.md) | ⑦ 案件跟踪 |
| [`../templates/legal-case-closure.md`](../templates/legal-case-closure.md) | ⑧ 结案归档 |

**业务线 ③ 非诉法律项目（v2.0 新增；v2.1 按四阶段哲学校正）**
| 文件 | 内容 |
| --- | --- |
| [`../templates/legal-non-litigation-project.md`](../templates/legal-non-litigation-project.md) | 项目立项 / 尽调清单（M&A 通用版）/ 资料请求函 / 尽调报告结构化模板 / SPA 骨架 / 配套文本清单 / 项目交付物追踪表 / 自检清单 |
| [`../templates/legal-negotiation-management.md`](../templates/legal-negotiation-management.md) | **v2.1 新增**：业主四阶段工作法工作底稿 — A 客户访谈记录、商业诉求清单、交易结构选项、立场矩阵；B 议题追踪器、谈判轮次记录、客户决策记录、谈判预案；C 议题↔条款映射、文本闭合检查、版本管理；D 程序清单（M&A 标准 8 项）、申请文件清单、闭环验收 |

### 用户手册（开发期编写中）

```
user-manual/                     # 系统内嵌帮助中心源文件
├── 00-overview.md
├── 01-quick-start/
│   ├── for-admin.md
│   ├── for-lawyer.md
│   └── for-assistant.md
├── 02-modules/                  # 8 大模块逐一讲解
├── 03-workflows/                # 端到端流程示例
├── 04-faq.md
├── 05-troubleshooting.md
└── 99-changelog.md
```

> 用户手册源文件随各模块开发**并行**完成，详见 `architecture.md` §3.8 与 §9 排期。

## 文档变更纪律

| 规则 | 说明 |
| --- | --- |
| **改需求 → 改架构 → 改验收** | 三份文档保持联动，避免脱节 |
| **每次改动写入修订历史** | 文档末尾的"修订历史"表格每次更新都要追加 |
| **重大变更必须评审签字** | requirements.md 的变更需合伙人 + 技术负责人共同签字 |
| **版本号语义** | v{大版本}.{小版本}：MVP 上线为 v1.0，二期为 v2.0 |

## 项目状态速览

| 项 | 状态 |
| --- | --- |
| 需求说明 | ✅ v2.1 待评审 |
| 架构设计 | ✅ v2.1 待评审（10 大模块；非诉按四阶段重组） |
| 验收与培训 | ✅ v2.1 待评审 |
| 合伙人评审包 | ✅ v2.1 等待合伙人评审（含 20 项决策） |
| Claude Skill | ✅ v1.2 含非诉项目业务线 7 项 AI 行为基准 |
| 工作流模板（诉讼仲裁） | ✅ 7 份已交付（v2.0 扩展诉讼文书全套） |
| 工作流模板（非诉项目） | ✅ 2 份已交付（项目档案+尽调+SPA / 谈判管理四阶段工作底稿） |
| 用户手册 | ⬜ 待开发期编写 |
| 系统开发 | ⬜ 未启动（合伙人签字后 + 20 周） |

---

**维护**：Fine Bridge Technology (Thailand) Co., Ltd.
**最后更新**：2026-05-10
