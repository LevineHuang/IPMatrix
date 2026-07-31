# 论文内容流水线设计

日期：2026-07-31

## 背景

这个项目希望自动化一套周期性工作流：发现、筛选、分析学术论文，并发布中文解读文章。最初的使用场景是追踪 arXiv / alphaXiv 论文，但整体设计应保持足够通用，以便后续支持多个主题、多个论文来源和产品化。

目标工作流如下：

1. 每隔 N 天，按配置主题检索过去 N 天内的论文。
2. 候选论文数量不超过 N * 3 篇。
3. 提供简洁元数据，方便人工浏览和选择。
4. 对选中的论文生成：
   - 一篇批次级中文综述文章。
   - 每篇论文各一篇中文解读文章。
5. 保留每个生成 Markdown 文件与原始论文之间的直接可追溯关系。
6. 将人工复核后的本地 Markdown 文件发送到用户个人微信公众号草稿箱。

## 核心建议

把系统设计成一条论文内容流水线，而不是一组松散脚本。稳定的领域对象应包括：

- Topic：需要持续监控的主题。
- Run：某个主题的一次定时检索周期。
- Paper：一篇规范化后的源论文。
- Candidate：某篇论文在某次 Run 中的候选记录。
- Selection：人工对候选论文做出的纳入或排除决定。
- Artifact：生成的 Markdown 文章或其他输出。
- Review：发布前的人工或自动检查。
- PublishJob：将 Artifact 发送到发布目标的请求。
- PublishResult：发布方返回的结果。

Markdown 文件应被视为 Artifact，而不是唯一事实来源。它们可以携带用于识别的 frontmatter，但结构化元数据也应单独保存在 YAML / JSON 中，后续再迁移到 SQLite 或 Postgres。

## 改进后的工作流

```text
Topic configuration
  -> scheduled Run
  -> Candidate papers
  -> human Selection
  -> Paper ingestion
  -> batch Overview + paper Interpretations
  -> Review
  -> WeChat draft publishing
```

建议的 Run 状态：

```text
created
discovered
candidates_ready
selected
ingested
analyzed
reviewed
sent_to_wechat
archived
```

发布模块只应接收状态为 `reviewed` 的 Artifact。

## 工作流改进点

### 1. 在发现阶段加入推荐排序

候选列表不应只是按时间倒序排列。每个 Candidate 应包含：

- `relevance_score`
- `novelty_score`
- `recommendation_reason`
- `paper_type`，例如 method、survey、benchmark、system、application 或 position paper
- 重复或近似重复提示

这样选择页面会更容易快速浏览。

### 2. 分析前保存源材料快照

生成任何文章之前，先保存：

- 源元数据
- PDF
- 解析后的全文
- 可提取时保存图表
- 源 URL
- 检索时间戳

这样后续才能重新生成、事实核查和比较 prompt 效果。

### 3. 将元数据保存在 Markdown 之外

每个 Markdown Artifact 都应在 frontmatter 中包含 ID，但规范流程状态应保存在结构化文件和数据库中。

Markdown 适合编辑和发布，但不适合作为工作流状态的唯一索引。

### 4. 保留来源追踪信息

每个生成的 Artifact 都应记录：

- 源论文 ID
- 主题 ID
- Run ID
- 使用的 skill
- prompt 版本
- 模型名称
- 生成时间戳
- 源 URL
- 复核状态
- 发布结果，如果已经发布

### 5. 拆分选择、分析、复核和发布

不要在同一步里同时生成和发布。建议设置以下关口：

1. 人工选择候选论文。
2. 人工复核生成的 Markdown。
3. 在微信公众号草稿箱预览后再最终发布。

## 推荐仓库结构

```text
IPMatrix/
  README.md
  pyproject.toml / package.json

  configs/
    topics/
      embodied-ai.yml
      ai-agent.yml
      multimodal-llm.yml
    skills.yml
    publishing.yml

  data/
    db/
      pipeline.sqlite
      schema.sql
    runs/
      embodied-ai/
        2026-07-31_7d/
          run.yml
          candidates.json
          selection.json
          analysis.json
          publish.json

  library/
    papers/
      arxiv-2507-12345/
        paper.yml
        source.pdf
        source.txt
        figures/
          fig-01.png
          fig-02.png
        notes.md

  drafts/
    embodied-ai/
      2026-07-31_7d/
        overview.md
        papers/
          arxiv-2507-12345.md
          arxiv-2507-67890.md

  reviews/
    embodied-ai/
      2026-07-31_7d/
        fact-check.json
        human-notes.md

  outputs/
    wechat/
      embodied-ai/
        2026-07-31_7d/
          publish-results.json

  prompts/
    overview/
    paper-interpretation/
    fact-check/

  src/
    pipeline/
      discovery/
      selection/
      ingestion/
      analysis/
      review/
      publishing/
      storage/

  apps/
    cli/
    web/
```

目录职责：

- `configs/`：长期配置。
- `data/`：工作流状态、Run 记录和数据库文件。
- `library/`：规范化论文资产。同一篇 Paper 即使出现在多个 Topic 中，也只保存一次。
- `drafts/`：按 Topic 和 Run 分组的生成文章。
- `reviews/`：自动复核和人工复核记录。
- `outputs/`：按发布方保存的输出记录。
- `prompts/`：带版本管理的 prompt 模板。
- `src/`：实现代码。
- `apps/`：CLI 和未来 web UI 入口。

## Topic 配置示例

```yaml
id: embodied-ai
name: 具身智能
enabled: true

schedule:
  interval_days: 7
  lookback_days: 7
  max_candidates_multiplier: 3

sources:
  - arxiv
  - alphaxiv

query:
  include:
    - embodied AI
    - vision language action
    - robotics foundation model
  exclude:
    - surgical robot
    - medical robotics

ranking:
  prefer_recent: true
  min_relevance_score: 0.65
  prefer_institution_keywords:
    - Stanford
    - MIT
    - Google DeepMind
    - NVIDIA

skills:
  batch_overview: arxiv-batch-overview
  paper_interpretation: arxiv-paper-interpretation
  publisher: lvjun-post-to-wechat

publishing:
  target: wechat
  theme: editorial-signal
  account: default
```

## Run 元数据示例

```yaml
id: 2026-07-31_7d
topic_id: embodied-ai
window_start: 2026-07-24
window_end: 2026-07-31
max_candidates: 21
status: candidates_ready
created_at: 2026-07-31T09:00:00+08:00
```

## Paper 元数据示例

```yaml
paper_id: arxiv-2507-12345
source: arxiv
source_url: https://arxiv.org/abs/2507.12345
pdf_url: https://arxiv.org/pdf/2507.12345

title: Example Paper Title
authors:
  - name: Alice Zhang
    affiliation: Example University
  - name: Bob Lee
    affiliation: Example Lab

published_date: 2026-07-29
updated_date:
abstract: "..."
keywords: []
categories:
  - cs.AI
  - cs.RO

related_topics:
  - embodied-ai

first_seen_at: 2026-07-31T09:02:00+08:00
```

## Markdown Artifact Frontmatter

Paper 级解读：

```yaml
---
title: "某篇论文的中文解读"
artifact_id: embodied-ai__2026-07-31_7d__arxiv-2507-12345
artifact_type: paper_interpretation

topic_id: embodied-ai
run_id: 2026-07-31_7d
paper_id: arxiv-2507-12345

source_url: https://arxiv.org/abs/2507.12345
pdf_url: https://arxiv.org/pdf/2507.12345

status: reviewed
generated_by_skill: arxiv-paper-interpretation
prompt_version: 2026-07-31
generated_at: 2026-07-31T11:00:00+08:00

wechat:
  sent: false
  media_id:
  draft_url:
---
```

批次综述：

```yaml
---
title: "过去 7 天具身智能论文观察"
artifact_id: embodied-ai__2026-07-31_7d__overview
artifact_type: batch_overview

topic_id: embodied-ai
run_id: 2026-07-31_7d
paper_ids:
  - arxiv-2507-12345
  - arxiv-2507-67890

status: reviewed
generated_by_skill: arxiv-batch-overview
prompt_version: 2026-07-31
generated_at: 2026-07-31T10:30:00+08:00
---
```

## 产品化数据模型

第一版实现可以使用文件加 SQLite。后续同一模型可以迁移到 Postgres。

建议的数据表：

- `topics`
- `runs`
- `papers`
- `candidates`
- `selections`
- `artifacts`
- `reviews`
- `publish_jobs`
- `publish_results`

文件存储继续负责 PDF、图片、解析文本和 Markdown。数据库负责索引、工作流状态、对象关系和审计记录。

## 建议 CLI

第一版命令：

```bash
pipeline scan embodied-ai
pipeline select embodied-ai 2026-07-31_7d
pipeline analyze embodied-ai 2026-07-31_7d
pipeline review embodied-ai 2026-07-31_7d
pipeline publish embodied-ai 2026-07-31_7d
```

预期行为：

- `scan`：创建 Run，检索候选论文，排序，并写入 `candidates.json`。
- `select`：打开本地选择页面或终端选择器，并写入 `selection.json`。
- `analyze`：摄取已选论文，调用配置好的 skills，并写入 Markdown Artifact。
- `review`：运行事实核查 prompt，并允许用户将 Artifact 标记为 `reviewed`。
- `publish`：只把已复核 Artifact 发送到微信公众号草稿箱，并记录发布方结果。

## 建议的第一个里程碑

先构建一个 local-first MVP：

- CLI 应用。
- SQLite 元数据存储。
- YAML / JSON 文件，用于保存透明的工作流记录。
- 本地 HTML 候选选择页面。
- 通过现有 skills 生成 Markdown。
- 通过现有发布 skill 发送到微信公众号。

开始阶段不要构建完整 SaaS 或复杂 web dashboard。等多个 Topic 跑过多个周期后，再把选择、复核和发布界面升级成更完整的 web UI。
