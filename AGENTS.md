# AGENTS.md

本文件指导 coding agent 在 IPMatrix 仓库中进行 Vibe coding 开发。除特定术语、命令、文件名、字段名和代码标识外，面向用户和文档的表达尽量使用中文。

## 项目定位

IPMatrix 是一个 local-first 论文内容流水线项目。当前 MVP 的核心链路是：

```text
scan -> select -> analyze -> review -> publish
```

第一版只支持 `agent-memory` 主题和 arXiv 来源，但代码、配置和数据目录必须保持可扩展到多主题、多来源。

当前发布能力是 dry-run。任何真实微信公众号发布、真实 LLM 生成、外部账号写入和不可逆操作，都必须作为后续显式任务处理，不能在普通改动中顺手接入。

## 优先级

开发时按以下顺序取舍：

1. 可运行闭环优先于功能完整。
2. 本地可追溯文件优先于隐藏状态。
3. 行为测试优先于实现细节测试。
4. dry-run 安全线优先于真实外部副作用。
5. README 和规划文档同步优先于“代码先行、以后再补”。

## 工作流

每次改动采用小步 Vibe coding 节奏：

1. 先读相关文档和现有代码。
2. 明确本次只改哪一段行为。
3. 先写能失败的行为测试。
4. 写最小实现让测试通过。
5. 运行相关单测。
6. 必要时运行端到端 smoke test。
7. 更新 README、设计文档或 Vibe coding 规划。
8. 最后检查 git diff，确认没有混入运行产物。

不要为了“顺手优化”重构无关模块。若发现架构问题，先记录到文档或后续计划，除非它直接阻塞当前任务。

## 常用命令

运行完整测试：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

离线扫描 fixture：

```bash
PYTHONPATH=src python3 -m ipmatrix.pipeline.cli scan agent-memory --from-file tests/fixtures/arxiv_atom_sample.xml --today 2026-07-31
```

真实扫描 arXiv：

```bash
PYTHONPATH=src python3 -m ipmatrix.pipeline.cli scan agent-memory
```

继续本地流程：

```bash
PYTHONPATH=src python3 -m ipmatrix.pipeline.cli select agent-memory 2026-07-31_7d
PYTHONPATH=src python3 -m ipmatrix.pipeline.cli analyze agent-memory 2026-07-31_7d
PYTHONPATH=src python3 -m ipmatrix.pipeline.cli review agent-memory 2026-07-31_7d
PYTHONPATH=src python3 -m ipmatrix.pipeline.cli publish agent-memory 2026-07-31_7d
PYTHONPATH=src python3 -m ipmatrix.pipeline.cli status agent-memory 2026-07-31_7d
```

## 目录职责

- `configs/topics/`：主题配置。新增主题时先复制现有结构，再调整关键词和来源。
- `src/ipmatrix/pipeline/config.py`：主题配置读取和轻量 YAML 解析。
- `src/ipmatrix/pipeline/storage.py`：Run 目录、JSON 记录、SQLite 索引和状态推进。
- `src/ipmatrix/pipeline/discovery.py`：arXiv 查询构造、Atom 解析和 Candidate 生成。
- `src/ipmatrix/pipeline/scan.py`：Topic scan 编排、来源快照、候选写入和状态推进。
- `src/ipmatrix/pipeline/selection.py`：本地 HTML 选择页。
- `src/ipmatrix/pipeline/analysis.py`：dry-run Markdown Artifact 生成。
- `src/ipmatrix/pipeline/review.py`：dry-run 复核关口。
- `src/ipmatrix/pipeline/publishing.py`：dry-run 微信发布结果。
- `src/ipmatrix/pipeline/cli.py`：命令入口和阶段编排。
- `tests/`：行为测试和离线 fixture。
- `docs/`：设计、计划和产品化思路。

运行产物目录：

- `data/`
- `drafts/`
- `outputs/`

这些目录已被 `.gitignore` 忽略。不要把本地 SQLite、运行 JSON、生成 Markdown 和 publish result 提交进仓库，除非用户明确要求保存样例产物。

## 状态机约束

Run 状态应按以下方向推进：

```text
created
  -> candidates_ready
  -> selected
  -> analyzed
  -> reviewed
  -> sent_to_wechat
```

发布阶段只能接受已 `reviewed` 的 Artifact。后续如果增加 `needs_revision`、`failed`、`retryable` 等状态，需要同时更新：

- `README.md`
- `docs/paper-content-pipeline-design.md`
- `docs/vibe-coding-development-plan.md`
- `src/ipmatrix/pipeline/storage.py`
- 相关测试

## 数据模型约束

Markdown 是 Artifact，不是唯一事实来源。

每个阶段都应优先写入结构化记录：

- `run.json`
- `candidates.json`
- `selection.json`
- `analysis.json`
- `review.json`
- `publish.json`

SQLite 负责索引、状态、关系和审计线索。不要让 SQLite 成为唯一状态存储，也不要只靠 Markdown frontmatter 推断流程状态。

## arXiv 接入约束

第一版只接 arXiv。改 `discovery.py` 时要保持：

- 查询 URL 可测试。
- 查询包含 Topic 的 `lookback_days` 时间窗口，使用 arXiv `submittedDate:[... TO ...]`。
- Atom 解析可离线测试。
- `paper_id` 规范化为 `arxiv-2507-12345` 这类稳定形式。
- `source_url` 和 `pdf_url` 保留直接来源。
- 候选数量不超过 Topic 的 `max_candidates`。
- scan 阶段保存 `sources/arxiv.atom.xml` 和 `scan.json`，方便复现。

新增来源时，不要把多来源逻辑硬塞进 `ArxivClient`。应新增来源客户端，并让 `scan.py` 按 Topic sources 调用。alphaXiv 当前可作为后续来源接入；如果使用 alphaXiv MCP 或需要 API key，必须保持默认测试离线可跑。

## 选择页约束

本地 HTML 页面应服务人工快速选择，而不是变成完整 dashboard。

选择页必须：

- 展示标题、作者、发布日期、来源链接、摘要和推荐理由。
- 展示分类、相关度、新颖度、PDF 链接等帮助快速浏览的信息。
- 支持关键词过滤、只看已选、全选、清空和实时 `selection.json` 预览。
- 默认可生成 `selection.json`。
- 保持无后端依赖。

如果要增加更复杂交互，先确保现有 CLI 流程仍可运行。

## dry-run 生成和发布约束

`analysis.py` 当前只生成 dry-run Markdown。接入真实生成能力时必须保留 dry-run 模式，并记录：

- `generated_by_skill`
- `prompt_version`
- `model_name`
- `generated_at`
- `source_url`
- `pdf_url`

`publishing.py` 当前只写 dry-run 微信发布结果。接入真实 WeChat publisher 时必须：

- 默认仍可 dry-run。
- 不在测试中调用真实外部接口。
- 不提交任何 token、cookie、AppSecret 或账号私密信息。
- 失败时写入可审计错误记录。
- 只接受 `reviewed` Artifact。

## 测试标准

新增行为必须有测试。优先写：

- 配置解析测试。
- 存储和状态推进测试。
- arXiv URL 构造和 Atom 解析测试。
- HTML 输出关键内容测试。
- dry-run 端到端流程测试。

测试中优先使用 `tests/fixtures/`，避免依赖实时网络。真实网络请求可以手动验证，但不能作为默认测试的必要条件。

完成前至少运行：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

如果改动 CLI 编排，还要跑一次离线 smoke test。

## 文档标准

改动行为时同步更新相关文档：

- 用户如何运行：更新 `README.md`。
- 产品或架构取舍：更新 `docs/paper-content-pipeline-design.md`。
- 迭代路线和开发节奏：更新 `docs/vibe-coding-development-plan.md`。
- agent 协作规则：更新本文件。

文档以中文为主。保留必要英文术语，例如 arXiv、dry-run、Artifact、Run、Topic、CLI、SQLite、frontmatter、prompt、skill。

## 安全边界

不要在未明确要求时执行以下动作：

- 真实发布到微信公众号。
- 调用真实付费模型生成大量内容。
- 删除用户数据、运行记录或草稿。
- 提交本地运行产物。
- 写入仓库外目录。
- 添加长期后台任务或定时任务。

需要清理运行产物时，先说明要删除哪些路径，并确认它们只属于本地可再生结果。

## 代码风格

- 优先使用 Python 标准库，除非新依赖显著降低复杂度。
- 保持模块小而清晰，每个模块只负责一类行为。
- 对外部副作用使用清晰边界：fetch、write、publish 都要可测试或可 dry-run。
- 不要把 CLI 参数解析、业务逻辑和文件写入混在一个大函数里继续扩张。
- 注释只解释不明显的设计原因，不解释显而易见的代码。

## 接手任务时的检查清单

开始前：

- 读 `README.md`、本文件和相关 `docs/` 文档。
- 看 `git status --short`，不要覆盖用户未提交改动。
- 找到本次要改的最小模块。

开发中：

- 先写测试，再写实现。
- 只改当前任务需要的文件。
- 保持 dry-run 默认安全。

完成前：

- 跑完整测试。
- 如涉及 CLI，跑离线 smoke test。
- 检查 `git status --short --ignored`，确认 `data/`、`drafts/`、`outputs/` 没有进入暂存。
- 总结改动、验证结果和未做事项。
