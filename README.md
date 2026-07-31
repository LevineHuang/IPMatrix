# IPMatrix

IPMatrix 是一个 local-first 论文内容流水线项目。第一版目标是先跑通“发现论文、人工选择、生成 dry-run Markdown、复核、dry-run 发布”的完整数据流，再逐步接入真实生成能力和微信公众号发布能力。

## 当前 MVP 范围

- 主题：先内置 `agent-memory`，但目录和数据模型按多主题设计。
- 来源：第一版只接 arXiv。
- 生成：第一版只生成 dry-run Markdown，用来验证文件结构和状态机。
- 选择：生成本地 HTML 页面，方便人工浏览候选论文。
- 发布：第一版只生成 dry-run 微信公众号发布结果，不实际发送。
- 存储：JSON 文件作为透明工作流记录，SQLite 作为结构化索引。

## 快速开始

给 coding agent 的开发指南见 [AGENTS.md](AGENTS.md)。开始 Vibe coding 前请先阅读它。

运行测试：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

扫描 arXiv。`scan` 会按 Topic 的 `lookback_days` 生成 Run 时间窗口，并把窗口写进 arXiv `submittedDate` 查询：

```bash
PYTHONPATH=src python3 -m ipmatrix.pipeline.cli scan agent-memory
```

如果已经有 arXiv Atom XML 文件，也可以离线扫描：

```bash
PYTHONPATH=src python3 -m ipmatrix.pipeline.cli scan agent-memory --from-file /path/to/arxiv.xml --today 2026-07-31
```

扫描阶段会生成：

- `data/runs/<topic>/<run_id>/scan.json`
- `data/runs/<topic>/<run_id>/candidates.json`
- `data/runs/<topic>/<run_id>/sources/arxiv.atom.xml`

后续流程：

```bash
PYTHONPATH=src python3 -m ipmatrix.pipeline.cli select agent-memory 2026-07-31_7d
PYTHONPATH=src python3 -m ipmatrix.pipeline.cli analyze agent-memory 2026-07-31_7d
PYTHONPATH=src python3 -m ipmatrix.pipeline.cli review agent-memory 2026-07-31_7d
PYTHONPATH=src python3 -m ipmatrix.pipeline.cli publish agent-memory 2026-07-31_7d
PYTHONPATH=src python3 -m ipmatrix.pipeline.cli status agent-memory 2026-07-31_7d
```

`select` 会生成本地 HTML 论文筛选页：

- 以卡片形式展示标题、作者、发布日期、分类、推荐理由、摘要、arXiv 链接和 PDF 链接。
- 支持关键词过滤、只看已选、全选、清空。
- 勾选状态会实时更新右侧 `selection.json` 预览。
- 点击“保存 selection.json”可下载人工选择结果，并作为 `analyze` 的输入。

## 目录结构

- `configs/topics/`：主题配置。
- `data/runs/`：每次 Run 的透明记录，包括 `run.json`、`candidates.json`、`selection.json`、`analysis.json`、`review.json` 和 `publish.json`。
- `data/db/pipeline.sqlite`：SQLite 索引。
- `drafts/`：dry-run Markdown 文章。
- `outputs/wechat/`：dry-run 发布结果。
- `docs/`：设计文档和开发规划。
- `src/ipmatrix/pipeline/`：流水线实现。
- `tests/`：行为测试。

技术方案与数据流说明见 [docs/technical-architecture-and-data-flow.md](docs/technical-architecture-and-data-flow.md)。

## 状态流

```text
created
  -> candidates_ready
  -> selected
  -> analyzed
  -> reviewed
  -> sent_to_wechat
```

发布阶段只接受已经 `reviewed` 的 Artifact。

## 后续方向

1. 接入真实生成能力，替换 dry-run Markdown。
2. 增加事实核查和人工复核页面。
3. 接入真实微信公众号草稿箱发布。
4. 扩展 alphaXiv 和更多主题。alphaXiv 当前优先作为后续可插拔来源接入，MVP 的默认实时获取先使用 arXiv API。
5. 将选择、复核、发布升级为更完整的 web UI。
