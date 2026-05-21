# arXiv Report Skill — 运行逻辑全览

## 触发方式

```
方式 A：全自动（launchd + Claude Cron）
  每天 8:00 → launchd 跑 arxiv_fetcher.py → 拉 JSON 到 cache/
  每天 8:05 → Claude Cron 触发 /arxiv-report → 评分 → Agent → 报告

方式 B：手动触发（Claude Code 内）
  /arxiv-report              → 今日报告
  /arxiv-report 2026-05-19   → 回溯指定日期

方式 C：终端（仅拉数据，不生成报告）
  python3 scripts/arxiv_fetcher.py --date 2026-05-19
```

## 五阶段流水线

```
Phase 1          Phase 2          Phase 3           Phase 4                    Phase 5
加载配置   →    数据抓取    →    关键词评分   →    并行 SubAgent          →   汇总生成 .md
```

## Phase 1: 加载配置

读取 `~/arxiv-reports/config.json`（不存在则用 skill 内置默认值），拿到：

- 10 个关键词，每个带 weight(3-10) + aliases
- `deep_dive_threshold: 8`
- `arxiv_categories: [astro-ph.SR, astro-ph.HE, astro-ph.GA]`

## Phase 2: 数据抓取

检查 `~/arxiv-reports/cache/{date}.json` 是否存在。存在 → 跳过。不存在 → 调 `arxiv_fetcher.py` 查 arXiv API：

```
Query: (cat:astro-ph.SR OR cat:astro-ph.HE OR cat:astro-ph.GA)
       AND submittedDate:[YYYYMMDD0000 TO YYYYMMDD2359]
Sort:   by SubmittedDate
Output: ~/arxiv-reports/cache/{date}.json
```

## Phase 3: 关键词评分

对每篇论文的 title + abstract 做大小写不敏感匹配：

```
标题命中关键词     → score += weight × 1.5
摘要命中关键词     → score += weight × 1.0
同关键词多次命中   → 不重复计分
aliases 等价于主关键词
```

```
总分 = 0           → 丢弃（不相关）
0 < 总分 < 8       → Quick Summary
总分 ≥ 8           → Deep Dive
```

## Phase 4: 并行 SubAgent

每篇相关论文构造一份 JSON，全部同时启动：

```
┌─ score ≥ 8 ──→ Agent "arxiv-deep-dive"
│                Model: opus
│                Skill: academic-paper-reviewer → methodology-focus
│                流程: curl 下载 TeX → tar 解压 → 通读全文
│                      → field_analyst + eic + methodology_reviewer
│                      → 蒸馏为: 核心贡献/方法亮点/方法论质量/关联/可借鉴/局限
│
├─ 0 < score < 8 → Agent "arxiv-quick-summary"
│                Model: haiku
│                Skill: academic-paper-reviewer → quick
│                流程: curl 下载 TeX → tar 解压 → 通读全文
│                      → field_analyst + eic
│                      → 蒸馏为: EIC快速评估 + 中文摘要
│
└─ score = 0     → 丢弃
```

## Phase 5: 汇总生成 Markdown

收集所有 Agent 返回，按 score 降序排列，写入 `~/arxiv-reports/arxiv-report-{date}.md`：

```
┌─────────────────────────────────┐
│ # arXiv 天体物理日报 — YYYY-MM-DD │
│                                 │
│ ## 今日概况                      │
│ 检索 N 篇 / 相关 M 篇            │
│ Deep Dive: X 篇 / Quick: Y 篇    │
│                                 │
│ ## 深度解读 (Deep Dive)          │
│ 核心贡献 / 方法亮点 / 关联 / ... │
│                                 │
│ ## 快速扫描 (Quick Summary)      │
│ 表格: EIC评估 + 中文摘要         │
│                                 │
│ *由 arxiv-report 生成于 ...*    │
└─────────────────────────────────┘
```

## 语言规则

| 内容 | 语言 |
|------|------|
| 报告描述、解读、评估、摘要 | 中文 |
| 论文标题、作者名、arXiv ID | 英文 |
| 学术术语 | 英文（正文中可附中文翻译） |

## 错误降级链

```
arXiv API 请求失败     → 重试 3 次（指数退避 5s/10s/15s），仍失败 → 报错退出
单篇 Agent 失败        → 标注"评审失败"，不阻塞其他论文
论文无 TeX 源码        → 降级为 abstract-based 评审
全部不相关 (score=0)   → 报告"今日无相关论文"
周末/节假日            → 报告"今日 arXiv 无新论文发布"
```

## 关键词权重配置

```json
[
  { "term": "blue loop",        "weight": 10 },
  { "term": "X-ray binary",     "weight": 8  },
  { "term": "mass transfer",    "weight": 6  },
  { "term": "binary evolution", "weight": 5  },
  { "term": "common envelope",  "weight": 5  },
  { "term": "stellar evolution","weight": 4  },
  { "term": "accretion",        "weight": 3  },
  { "term": "supernova",        "weight": 3  },
  { "term": "neutron star",     "weight": 3  },
  { "term": "black hole",       "weight": 3  }
]

deep_dive_threshold: 8
```

## 文件结构

```
~/.agents/skills/arxiv-report/     ← Skill 本体
├── SKILL.md                         # AI 入口 (name: arxiv-report → /arxiv-report)
├── README.md                        # 人类文档
├── agents/
│   ├── deep-dive-agent.md           # opus + methodology-focus
│   └── quick-summary-agent.md       # haiku + quick
├── config/config.json               # 默认配置
├── scripts/
│   ├── arxiv_fetcher.py             # arXiv 数据抓取
│   └── setup.sh                     # 一键安装
└── templates/com.arxiv-report.plist # launchd 模板

~/arxiv-reports/                   ← 运行时数据
├── config.json                      # 用户配置
├── cache/YYYY-MM-DD.json           # 原始数据
└── arxiv-report-YYYY-MM-DD.md      # 日报
```

## 依赖

| 类型 | 名称 | 说明 |
|------|------|------|
| Claude Skill | academic-paper-reviewer ≥ 1.9.0 | 多视角学术评审引擎 |
| Python | json (stdlib) | 配置文件解析 |
| Python | openai ≥ 1.0.0 | DeepSeek API 客户端 |
| 系统 | macOS (launchd) / Linux (cron) | 定时调度 |
