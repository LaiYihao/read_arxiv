# arXiv Report — 天体物理日报生成器

自动生成 arXiv 天体物理日报。默认检索前一日 astro-ph 新论文，按加权关键词匹配过滤并评分。高分论文走 Deep Dive 深度解读（含核心贡献、方法亮点、方法论质量评估、可借鉴内容），低分论文走 Quick Summary 快速扫描（含 EIC 评估、中文摘要），最终输出结构化 Markdown 日报。

## 特性

- 📰 **自动日报生成** — 支持每日自动或按指定日期生成天体物理论文日报
- 🔍 **智能关键词筛选** — JSON 配置文件定义关键词、权重和别名，自动评分分流
- 🤖 **DeepSeek AI 评审** — 使用 DeepSeek v4-pro/flash API（OpenAI SDK），含结构化 JSON 输出
- 🚀 **5 阶段流水线** — 配置 → 抓取 → 评分 → 评审 → 报告
- 💾 **智能缓存** — arXiv 数据缓存 `cache/{date}.json`，避免重复抓取
- 🎯 **并行处理** — `config.json` 中可配置 `max_workers`（默认 5）
- 📝 **Markdown 输出** — 含 `[TOC]` 自动目录，Deep Dive 完整方法论评估

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt openai
# 或创建 conda 环境
conda env create -f environment.yml && conda activate arxiv-report

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 3. 生成前一日报告
python main.py

# 4. 生成指定日期报告
python main.py --date 2026-05-18
python main.py -d 2026-05-18      # 简写

# 5. 其他模式
python main.py --dry-run            # 干运行（不调用 API）
python main.py --no-review          # 仅抓取评分，不评审
python main.py --config my.json    # 使用自定义配置
```

## 前置条件

- Python >= 3.10
- DeepSeek API Key（从 https://platform.deepseek.com 获取）

## 配置

### 关键词配置 (`config.json`)

```json
{
  "keywords": [
    {"term": "blue loop", "weight": 10, "aliases": ["blue loops"]},
    {"term": "X-ray binary", "weight": 8, "aliases": ["X-ray binaries", "XRB"]},
    {"term": "mass transfer", "weight": 6, "aliases": ["Roche lobe overflow", "RLOF"]}
  ],
  "deep_dive_threshold": 8,
  "arxiv_categories": ["astro-ph.SR", "astro-ph.HE", "astro-ph.GA"],
  "max_papers_per_day": 200,
  "max_workers": 5,
  "cache_max_days": 7
}
```

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `keywords[].term` | 主关键词 | — |
| `keywords[].weight` | 权重（3-10） | — |
| `keywords[].aliases` | 同义词列表 | `[]` |
| `deep_dive_threshold` | >= 此分的论文走 Deep Dive | 8 |
| `arxiv_categories` | 检索的 arXiv 分类 | `astro-ph.SR/HE/GA` |
| `max_papers_per_day` | 每日最大检索数 | 200 |
| `max_workers` | 并行 API 请求数 | 5 |
| `cache_max_days` | 缓存保留天数 | 7 |

### 环境变量 (`.env`)

```bash
DEEPSEEK_API_KEY=sk-your-api-key
DEEPSEEK_MODEL_FLASH=deepseek-v4-flash
DEEPSEEK_MODEL_PRO=deepseek-v4-pro
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
```

## 输出

日报保存在 `outputs/` 目录：

```
outputs/
├── arxiv-report-2026-05-20.md
└── ...
```

### 日报结构

```markdown
# arXiv 天体物理日报 — YYYY-MM-DD
[TOC]
## 今日概况
## 深度解读
### [1] Paper Title
  - arXiv ID, 作者, 关键词(分数), 评审模式, 相关度 ★★★★★
  - 核心贡献 / 方法亮点 / 方法论质量评估
  - 与研究方向关联 / 可借鉴内容 / 潜在问题 & 局限性
## 快速扫描
### [1] Paper Title
  - EIC 快速评估 / 兴趣关联 / 中文摘要
```

## 工作流程

### 5 阶段流水线

```
Phase 1: 配置加载 → Phase 2: 数据抓取 → Phase 3: 关键词评分
→ Phase 4: DeepSeek API 评审 → Phase 5: Markdown 生成
```

**Phase 1: 配置加载**
- 加载 `config.json`（不存在则使用内置默认配置）

**Phase 2: 数据抓取**
- 查询 arXiv API，按日期和分类过滤
- 结果缓存到 `cache/{date}.json`

**Phase 3: 关键词评分**
- 对 title + abstract 进行关键词匹配
- 标题命中 x1.5，摘要命中 x1.0
- 按阈值分流: >= threshold → Deep Dive, 0 < score < threshold → Quick Summary

**Phase 4: DeepSeek API 评审**
- **Deep Dive** (`is_deep_dive=True`)
  - 使用 DeepSeek v4-pro，含 thinking 推理
  - 返回：核心贡献、方法亮点、方法论质量(含星级)、研究方向关联、可借鉴内容、局限、EIC 评估、中文摘要
- **Quick Summary** (`is_deep_dive=False`)
  - 使用 DeepSeek v4-flash
  - 返回：EIC 快速评估、兴趣关联、中文摘要、推荐度

**Phase 5: 报告生成**
- 按得分降序排列，生成 Markdown 日报
- 输出 `outputs/arxiv-report-{date}.md`

## 缓存

- **arXiv 数据缓存**: `cache/{date}.json` — 避免重复查询 arXiv API
- **缓存清理**: 早于 `cache_max_days` 的缓存文件自动清理

## 错误处理

| 错误 | 处理方式 |
|------|---------|
| arXiv API 失败 | 重试 3 次（指数退避），仍失败则报错退出 |
| DeepSeek API 错误 | 单篇标记"评审失败"，不阻塞其他论文 |
| JSON 解析失败 | 尝试提取 markdown 代码块、直接JSON、花括号匹配等 |
| 无相关论文 | 生成"今日无相关论文"的空报告 |

## 语言规则

| 内容 | 语言 |
|------|------|
| 报告描述、解读、评估、摘要 | 中文 |
| 论文标题、作者名、arXiv ID | 英文 |
| 学术术语 | 英文（可附中文翻译） |

## 许可证

MIT License — 详见 [LICENSE](./LICENSE)
