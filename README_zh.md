# 生物医药竞争情报原型

这是一个可运行的 Python 原型项目，用于围绕疾病靶点或生物标志物生成生物医药竞争情报报告。系统会从公开数据源采集信息，标准化记录，缓存查询结果，并输出结构化的 Markdown 或 HTML 报告。

报告默认使用中文生成。如需英文报告，可以在命令中加入 `--language english`。如果配置了 LLM API key，报告四个核心章节会优先使用 LLM 对采集数据的分析与归纳；如果未配置或调用失败，则自动回退到本地规则化摘要。

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

## 运行测试

```powershell
python -m unittest discover -s tests
```

## 项目结构

```text
research_intel/
  __main__.py        CLI 入口
  app.py             管线编排
  cache.py           SQLite 缓存和报告版本记录
  config.py          环境变量配置
  http.py            标准库 HTTP 客户端
  llm.py             LLM 分析器
  models.py          标准化数据模型
  report.py          Markdown/HTML 报告渲染器
  sources/           可插拔数据采集器
docs/
  architecture.md    系统设计文档
reports/
  sample_HER2.md     离线演示报告样例
tests/
```

## 当前限制

- 离线演示数据经过简化，主要用于证明完整流程可运行。
- 公开数据库结果会随时间变化。
- LLM 输出受 API 可用性和模型行为影响，重要结论仍应由合格专家复核。
- 公开来源可能不包含付费数据库、保密公司策略或最新会议进展。
