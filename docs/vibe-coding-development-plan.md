# Vibe coding 开发规划

日期：2026-07-31

## 开发原则

先做 local-first 闭环，再扩展能力。每个阶段都要能独立运行、能留下文件证据、能被测试覆盖。

## 第一阶段：MVP 数据流

目标：跑通 `scan -> select -> analyze -> review -> publish`。

范围：

- 单主题 `agent-memory`。
- 多主题目录结构。
- arXiv 作为唯一论文来源。
- `scan` 使用 arXiv API 的 `submittedDate` 时间窗口真实获取候选论文。
- 本地 HTML 选择页。
- dry-run Markdown 生成。
- dry-run 微信发布结果。
- JSON + SQLite 双轨记录。

验收：

- 命令行可以依次跑完整流程。
- 每一步都生成对应文件。
- Run 状态按顺序推进。
- 测试覆盖核心模块。

## 第二阶段：真实生成能力

目标：把 dry-run Markdown 替换为真实论文解读。

范围：

- 保存 PDF、源元数据和解析文本。
- 接入 batch overview 和 paper interpretation skill。
- 请生成 batch paper overview skill，对过去一段时间围绕某一主题的 paper，按照一定的逻辑顺序，进行观察性概览介绍，介绍每篇文章时表明文章标题、作者、原文链接以及发表时间。
- 为每个 Artifact 记录 prompt 版本、skill 名称和生成时间。
- 对失败生成保留可重试状态。

## 第三阶段：复核体验

目标：让人工复核从“看文件”升级为“看页面”。

范围：

- 本地 review HTML 页面。
- 展示论文来源、摘要、生成内容和核查项。
- 支持将 Artifact 标记为 `reviewed` 或 `needs_revision`。

## 第四阶段：真实发布

目标：接入微信公众号草稿箱。

范围：

- 保留 dry-run 模式。
- 增加真实 publisher。
- 保存 `media_id`、`draft_url`、发布时间和错误信息。
- 发布入口只接受 `reviewed` Artifact。

## 第五阶段：多主题和更多来源

目标：把 MVP 从单主题扩展为可持续运营工具。

范围：

- 增加更多 Topic 配置。
- 接入 alphaXiv。alphaXiv 当前优先通过独立来源客户端接入，不与 `ArxivClient` 混写。
- 增加重复检测和推荐排序。
- 累积多周期运行记录，用于调整主题关键词。

## Vibe coding 节奏

每次迭代保持小步快跑：

1. 先写一条能失败的行为测试。
2. 写最小实现让测试通过。
3. 跑单测。
4. 更新 README 或规划文档。
5. 跑完整验证。

这个节奏能让项目一直保持“可运行”，同时允许快速调整方向。
