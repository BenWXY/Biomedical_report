# 架构设计

English version: [architecture.md](architecture.md)。

本项目是一个围绕生物医药靶点的竞争情报原型。用户输入 `HER2`、`PD-L1` 等靶点后，系统会采集公开临床试验和文献数据，进行标准化整理，可选地调用 LLM 生成核心正文分析，并输出 Markdown/HTML 报告。

## 1. 运行流程

1. CLI 接收靶点、输出格式、报告语言，以及可选的 `--offline` / `--verbose` 参数。
2. `Settings.from_env()` 从环境变量读取缓存路径、报告路径、数据源条数限制、API 超时、PubMed 配置和可选 LLM 配置。
3. `IntelligencePipeline.from_settings()` 创建缓存、HTTP 客户端、数据源列表、LLM 分析器和报告渲染器。
4. 每个 `DataSource` 根据靶点抓取数据，并返回 `SourceResult`。
5. 管线将记录拆分为 `TrialRecord` 和 `PublicationRecord`，去重后生成 `IntelligenceBundle`。
6. `LLMReportAnalyzer` 可选地通过 OpenAI Python SDK 调用 OpenAI-compatible Chat Completions API。
7. 如果 LLM 调用成功，报告的四个核心章节使用 LLM 输出；如果未配置 key 或调用失败，则自动使用本地规则化摘要。
8. `ReportRenderer` 将报告写入 `reports/`，支持 Markdown、HTML 或两者同时输出。
9. `CacheStore.record_report()` 记录报告版本元数据，便于追踪。

## 2. 核心模块

- `research_intel.__main__`：命令行参数解析、日志配置、管线调用和终端输出。
- `research_intel.config`：从环境变量读取缓存、报告、公开 API 和 LLM Provider 配置。
- `research_intel.app`：管线编排、数据源执行、记录去重、LLM 分析交接和报告版本记录。
- `research_intel.models`：定义 `TrialRecord`、`PublicationRecord`、`SourceResult` 和 `IntelligenceBundle`。
- `research_intel.http`：供实时公开数据源使用的轻量 HTTP 客户端。
- `research_intel.cache`：SQLite 缓存；当 SQLite 不可用时回退到 JSON 文件。
- `research_intel.llm`：基于 OpenAI SDK 的可选 LLM 报告分析器，支持 OpenAI-compatible Provider，包括 DashScope compatible mode。
- `research_intel.report`：本地规则化摘要、表格、内嵌 SVG 图表、Markdown 输出，以及不依赖额外库的 Markdown-to-HTML 渲染。
- `research_intel.sources`：基于 `DataSource` 接口的可插拔数据采集器。
- `tests`：离线测试，覆盖管线编排和报告生成。

## 3. 数据源

当前实时模式包含：

- `ClinicalTrialsSource`：查询 ClinicalTrials.gov v2，并标准化为 `TrialRecord`。
- `PubMedSource`：查询 PubMed E-utilities，并标准化为 `PublicationRecord`。

离线模式会替换为：

- `OfflineDemoSource`：返回内置 HER2 示例数据，便于无网络测试和评分。

所有数据源都实现：

```python
def fetch(self, target: str) -> SourceResult:
```

`SourceResult` 包含标准化记录、数据源警告，以及结果是否来自缓存。当前管线会直接渲染 `TrialRecord` 和 `PublicationRecord`。如果后续加入批准、专利、会议摘要、公司管线页面等新类型，可以先映射到现有记录类型，也可以新增模型并扩展报告渲染器。

## 4. 缓存与持久化

`CacheStore` 默认使用 SQLite，并创建两个表：

- `cache_entries`：按数据源和查询参数缓存 API payload，并通过 TTL 控制复用时间。
- `report_versions`：记录已生成报告的靶点、格式、路径和生成时间。

如果 SQLite 初始化或访问失败，系统会自动使用同路径旁边的 JSON 文件作为回退缓存。这让原型在受限环境中仍然可以运行。

默认缓存路径是 `.cache/research_intel.sqlite3`，可通过 `RESEARCH_INTEL_CACHE` 修改。默认报告目录是 `reports/`，可通过 `RESEARCH_INTEL_REPORTS` 修改。

## 5. LLM 分析

LLM 层是可选的，只影响报告正文分析，不负责数据采集。

`LLMReportAnalyzer` 接收最终的 `IntelligenceBundle`，构造包含试验和文献记录的结构化 prompt，然后调用：

```python
client.chat.completions.create(...)
```

模型需要返回 JSON，并包含以下 key：

- `target_overview`
- `pipeline_overview`
- `research_dynamics`
- `competitive_assessment`

当 `bundle.metadata["analysis_source"] == "llm"` 时，报告渲染器使用这些字段。否则使用本地规则化摘要。

Provider 配置方式：

- OpenAI：`OPENAI_API_KEY`，可选 `RESEARCH_INTEL_LLM_MODEL` 和 `RESEARCH_INTEL_LLM_ENDPOINT`。
- DashScope compatible mode：`DASHSCOPE_API_KEY`，通常配合 `qwen-plus` 和 `https://dashscope.aliyuncs.com/compatible-mode/v1`。
- 显式覆盖：`RESEARCH_INTEL_LLM_API_KEY`、`RESEARCH_INTEL_LLM_MODEL`、`RESEARCH_INTEL_LLM_ENDPOINT`、`RESEARCH_INTEL_LLM_TIMEOUT`。

代码既支持 `https://api.openai.com/v1` 这样的 base URL，也兼容旧写法 `https://api.openai.com/v1/chat/completions`，后者会被自动转换为 SDK 需要的 base URL。

## 6. 报告生成

报告渲染器会输出：

- Markdown 报告，便于审阅、比较和编辑。
- HTML 报告，便于浏览器查看。
- 内嵌 SVG 图表，用于展示临床试验阶段分布和文献年份趋势。

报告默认使用中文。`--language english` 会切换章节标签和正文语言。如果存在 LLM 输出，四个核心章节会使用 LLM 结果；表格、图表、数据源说明和本地统计仍由程序生成。

HTML 渲染器内置了轻量 Markdown 转 HTML 逻辑。这样可以在不增加额外依赖的情况下，处理本地摘要或 LLM 输出中常见的 Markdown 格式，包括标题、项目符号列表、编号列表、链接、粗体、斜体、行内代码、表格和内嵌 SVG 图表。

## 7. 错误处理

项目优先保证可降级运行：

- 实时 API 异常会尽量转为数据源警告。
- 缓存减少重复网络请求。
- 离线模式支持无网络确定性运行。
- LLM 未配置或调用失败时自动回退到本地摘要。
- `--verbose` 可以开启调试日志，帮助定位数据源和管线问题。

## 8. 添加新数据源

添加数据源的一般步骤：

1. 在 `research_intel/sources/` 下创建新模块。
2. 实现 `DataSource.fetch(target)`。
3. 将结果标准化为现有模型；如果新数据值得独立成章，则新增模型。
4. 返回包含记录和警告的 `SourceResult`。
5. 如需包级导入，在 `research_intel/sources/__init__.py` 中注册。
6. 在 `IntelligencePipeline.from_settings()` 的实时数据源列表中加入它。
7. 使用离线 fixture 或模拟 payload 增加针对性测试。

适合扩展的方向包括 FDA 批准和说明书、EMA/NMPA 监管记录、ASCO/ESMO/AACR 会议摘要、专利数据库、公司管线页面和新闻稿。

## 9. 风险与缓解

- 公开数据库可能滞后于公司披露。缓解方式：保留数据源警告，并要求分析人员复核。
- API schema 可能变化。缓解方式：把解析逻辑隔离在数据源模块，并测试标准化逻辑。
- 网络不稳定可能影响实时运行。缓解方式：缓存、日志、警告和离线 fixture。
- 重复记录可能扭曲统计。缓解方式：通过 NCT ID、PMID 等稳定标识去重。
- LLM 可能产生幻觉或过度推断。缓解方式：输入结构化数据、要求 JSON、在 system prompt 中禁止编造事实，并保留本地规则化回退。
- 凭据存在泄漏风险。缓解方式：API key 只从环境变量读取，不写入代码。

## 10. 后续扩展

- 为批准、专利、会议和公司披露增加专用模型与报告章节。
- 针对大结果集实现排序和分阶段摘要。
- 构建保留引用的 LLM evidence block。
- PDF 导出。
- Web UI，支持靶点历史、报告比较和数据源下钻。
- 后台任务，用于耗时较长的实时数据采集。
