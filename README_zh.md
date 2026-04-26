# 生物医药竞争情报原型

这是一个可运行的 Python 原型项目，用于围绕疾病靶点或生物标志物生成生物医药竞争情报报告。系统会从公开数据源采集信息，标准化记录，缓存查询结果，并输出结构化的 Markdown 或 HTML 报告。

报告默认使用中文生成。如需英文报告，可以在命令中加入 `--language english`。如果配置了 LLM API key，报告四个核心章节会优先使用 LLM 对采集数据的分析与归纳；如果未配置或调用失败，则自动回退到本地规则化摘要。

架构文档：中文 [architecture_zh.md](docs/architecture_zh.md) / English [architecture.md](docs/architecture.md)。

更详细的英文说明见 [README_detailed.md](README_detailed.md)。

## 项目用途

当研发、战略或医学团队关注一个靶点时，通常需要快速回答：

> 围绕这个靶点，其他研究者和公司已经在做什么？

本项目可以输入类似 `HER2`、`PD-L1`、`KRAS G12C` 的靶点名称，然后自动整理公开数据库中的临床试验和文献记录，生成便于阅读的竞争情报初筛报告。

## 功能特性

- 支持 ClinicalTrials.gov v2 API 临床试验数据采集。
- 支持 PubMed E-utilities 文献数据采集。
- 内置 HER2 离线演示数据，便于无网络环境下测试。
- 使用可选 LLM 分析层生成靶点概述、在研管线概览、近期研究动态和竞争格局判断。
- 输出 Markdown 和 HTML 报告。
- HTML 报告会将 LLM 返回的常见 Markdown 格式转换为真正的 HTML。
- 默认生成中文报告，并保留英文报告选项。
- 在报告中嵌入简单 SVG 图表，展示试验阶段分布和文献发表趋势。
- 使用 SQLite 缓存查询结果，并记录报告版本元数据。
- 对网络和 API 错误进行容错处理。
- 采用可插拔数据源架构，便于后续扩展 FDA、专利、会议摘要等来源。

## 快速开始

在项目根目录创建虚拟环境并安装项目：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

如果 PowerShell 阻止激活脚本，可以直接使用虚拟环境中的 Python：

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
```

## 配置 LLM 分析

配置 OpenAI-compatible Chat Completions API key 后，报告正文会优先使用 LLM 分析结果：

```powershell
$env:OPENAI_API_KEY="your-api-key"
```

也可以使用 DashScope 的 OpenAI-compatible endpoint：

```powershell
$env:DASHSCOPE_API_KEY="your-dashscope-api-key"
$env:RESEARCH_INTEL_LLM_MODEL="qwen-plus"
$env:RESEARCH_INTEL_LLM_ENDPOINT="https://dashscope.aliyuncs.com/compatible-mode/v1"
```

可选配置：

```powershell
$env:RESEARCH_INTEL_LLM_MODEL="gpt-4o-mini"
$env:RESEARCH_INTEL_LLM_ENDPOINT="https://api.openai.com/v1"
```

项目不会硬编码 API key。未配置 key 或调用失败时，系统仍会生成报告，但会使用本地规则化摘要作为回退。

## 离线演示

使用内置 HER2 数据生成离线演示报告：

```powershell
python -m research_intel --target HER2 --offline --format both
```

生成文件会写入 `reports/` 目录，文件名类似：

```text
reports/HER2_YYYYMMDD_HHMMSS.md
reports/HER2_YYYYMMDD_HHMMSS.html
```

## 生成英文报告

中文是默认语言。如果用户明确要求英文报告，使用 `--language english`：

```powershell
python -m research_intel --target HER2 --offline --format both --language english
```

实时调用公开 API 时也可以使用同样的语言参数：

```powershell
python -m research_intel --target "PD-L1" --format both --language english
```

## 实时数据源运行

默认非离线模式会调用公开数据源：

```powershell
python -m research_intel --target "PD-L1" --format both
```

可以通过环境变量配置 PubMed 的 email 和 tool 标识：

```powershell
$env:PUBMED_EMAIL="your.email@example.com"
$env:PUBMED_TOOL="research-intel-prototype"
```

## 常用命令选项

- `--target HER2`：指定要研究的靶点或生物标志物。
- `--offline`：使用内置演示数据，不访问外部 API。
- `--format markdown|html|both`：指定输出 Markdown、HTML 或两者都输出。
- `--language chinese|english`：指定报告语言；省略时默认为 `chinese`。
- `--verbose`：输出调试日志。

也可以使用安装后的控制台命令：

```powershell
research-intel --target HER2 --offline --format markdown
```

## 报告内容

生成的报告包含以下核心部分：

- **靶点概述**：靶点基本信息与作用机制。
- **在研管线概览**：按研发阶段分布的项目统计、主要竞争企业及其产品。
- **近期研究动态**：近期关键文献发现的摘要与解读。
- **竞争格局判断**：当前竞争态势、潜在风险与机会。

报告不是医疗建议，而是帮助分析人员更快开始研究的辅助输出。

如果 LLM 返回的正文中包含 Markdown 风格内容，HTML 报告会转换常见格式，包括标题、项目符号列表、编号列表、链接、粗体、斜体和行内代码。

## 添加更多数据源

项目通过 `research_intel/sources/base.py` 中的 `DataSource` 接口扩展数据源。每个数据源需要实现 `fetch(target: str) -> SourceResult`，并把外部数据转换成 `research_intel/models.py` 中的标准记录。

添加新数据源的一般步骤：

1. 在 `research_intel/sources/` 下创建新的模块，例如 `fda.py`、`conference.py` 或 `patent.py`。
2. 定义一个数据源类，设置清晰的 `name`。
3. 实现 `fetch(target: str) -> SourceResult`。
4. 在 `fetch` 中查询外部 API、本地文件或内部数据集。
5. 将结果转换为现有模型，通常是 `TrialRecord` 或 `PublicationRecord`。
6. 对 API 错误、字段缺失、限流或部分结果，在 `warnings` 中说明。
7. 如果需要从包级别导入，在 `research_intel/sources/__init__.py` 中注册。
8. 在 `IntelligencePipeline.from_settings()` 的非离线 `sources` 列表中加入新的数据源。

适合后续扩展的数据源包括 FDA 批准和说明书、EMA/NMPA 监管记录、ASCO/ESMO 会议摘要、专利数据库、公司管线页面和新闻稿。

当前管线会直接汇总和渲染 `TrialRecord` 与 `PublicationRecord`。如果新数据源返回的是批准、专利或会议等新类型信息，可以先映射到最接近的现有记录类型；如果需要更正式的结构，则应新增模型，并同步更新 `IntelligencePipeline` 和 `ReportRenderer`。

## 运行测试

```powershell
python -m unittest discover -s tests
```

## 项目结构

```text
.
  pyproject.toml     包元数据和命令行入口配置
  requirements.txt   运行时依赖列表
  written_test.md    原始项目需求说明
research_intel/
  __init__.py        包标记文件
  __main__.py        CLI 入口
  app.py             管线编排
  cache.py           SQLite 缓存和报告版本记录
  config.py          环境变量配置
  http.py            标准库 HTTP 客户端
  llm.py             LLM 分析器
  models.py          标准化数据模型
  report.py          Markdown/HTML 报告渲染器
  sources/           可插拔数据采集器
    base.py              DataSource 接口
    clinical_trials.py   ClinicalTrials.gov 数据采集器
    offline.py           内置离线演示数据源
    pubmed.py            PubMed 数据采集器
docs/
  architecture.md       英文系统设计文档
  architecture_zh.md    中文系统设计文档
reports/
  sample_HER2.md        离线演示报告样例
  *.md / *.html         生成的报告输出
tests/
  test_pipeline.py      离线管线和报告测试
```

## 当前限制

- 离线演示数据经过简化，主要用于证明完整流程可运行。
- 公开数据库结果会随时间变化。
- LLM 输出受 API 可用性和模型行为影响，重要结论仍应由合格专家复核。
- 公开来源可能不包含付费数据库、保密公司策略或最新会议进展。
