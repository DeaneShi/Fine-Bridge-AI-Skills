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
| 文件 | 阶段 |
| --- | --- |
| [`../templates/legal-case-intake.md`](../templates/legal-case-intake.md) | ① 接案 |
| [`../templates/legal-case-analysis.md`](../templates/legal-case-analysis.md) | ② 案情梳理 + ③ 法律检索 |
| [`../templates/legal-evidence-checklist.md`](../templates/legal-evidence-checklist.md) | ④ 证据组织 |
| [`../templates/legal-document-drafting.md`](../templates/legal-document-drafting.md) | ⑤ 文书起草 |
| [`../templates/legal-trial-preparation.md`](../templates/legal-trial-preparation.md) | ⑥ 庭审准备 |
| [`../templates/legal-case-tracking.md`](../templates/legal-case-tracking.md) | ⑦ 案件跟踪 |
| [`../templates/legal-case-closure.md`](../templates/legal-case-closure.md) | ⑧ 结案归档 |

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
| 需求说明 | ✅ v1.1 待评审 |
| 架构设计 | ✅ v1.1 待评审（含 9 大模块） |
| 验收与培训 | ✅ v1.1 待评审 |
| 合伙人评审包 | ✅ v1.1 等待合伙人评审（含 14 项决策） |
| Claude Skill | ✅ v1.0 已交付 |
| 工作流模板 | ✅ 7 份已交付 |
| 用户手册 | ⬜ 待开发期编写 |
| 系统开发 | ⬜ 未启动（合伙人签字后 + 14.5 周） |

---

**维护**：Fine Bridge Technology (Thailand) Co., Ltd.
**最后更新**：2026-05-10
