# DeepSeek Star Filter 🌟

基于 **DeepSeek API** 的微博热搜娱乐明星智能过滤工具。自动抓取微博热搜数据，并利用大语言模型双层判断机制，精准筛选出与娱乐明星相关的热搜条目。

---

## 功能特性

- 🔍 **微博热搜抓取** — 自动从 [weibotop.cn](https://www.weibotop.cn/) 抓取指定日期范围的微博热搜数据，支持 AES 加解密通信
- 🤖 **DeepSeek AI 分类** — 调用 DeepSeek API，智能判断热搜标题是否与娱乐明星相关
- 🧠 **双层判断机制**：
  - **第一层 — 直接识别**：判断标题中是否直接提及娱乐明星
  - **第二层 — 关联推断（增强模式）**：对未直接提及明星的标题，推断其背后最相关的娱乐明星（如影视作品名 → 主演）
- 📊 **关键词历史数据** — 可选抓取每个热搜关键词的排名与热度变化历史
- 🧵 **多线程并发抓取** — 支持配置并发线程数，大幅提升日期范围抓取速度
- 📁 **灵活的数据格式兼容** — 自动识别多种 JSON 结构（顶层列表、容器键、按日期索引等）
- 📝 **完整日志记录** — 同时输出到控制台和日志文件，便于调试与追踪
- ✅ **单元测试覆盖** — 核心模块均有对应测试用例

---

## 项目结构

```
star_filter/
├── config/
│   ├── __init__.py
│   └── settings.py              # 全局配置（API密钥、提示词、路径、日志等）
├── core/
│   ├── __init__.py
│   ├── api_client.py             # DeepSeek API 客户端封装
│   ├── classifier.py             # 第一层：直接明星分类器
│   ├── related_classifier.py     # 第二层：关联明星推断器（增强模式）
│   ├── data_processor.py         # 数据加载、处理、过滤、保存
│   ├── fetcher.py                # 微博热搜数据抓取器（含 AES 加解密）
│   └── orchestrator.py           # 流程编排器（串联 抓取→处理→保存）
├── data/
│   ├── raw.json                  # 抓取的原始数据
│   ├── weibo_raw.json            # 微博热搜原始数据
│   ├── filtered.json             # 过滤后的数据
│   └── weibo_filtered.json       # 微博热搜过滤后的数据
├── logs/
│   └── star_filter.log           # 运行日志
├── scripts/
│   ├── fetch_and_filter.py       # 入口脚本：一键抓取 + 过滤
│   └── filter_trends.py          # 入口脚本：对已有 JSON 文件进行过滤
├── tests/
│   ├── init.py
│   ├── test_classifier.py        # 分类器单元测试
│   ├── test_data_processor.py    # 数据处理器单元测试
│   ├── test_fetcher.py           # 抓取器单元测试
│   └── test_orchestrator.py      # 编排器集成测试
├── utils/
│   ├── __init__.py
│   ├── file_utils.py             # 文件操作工具（安全读写 JSON、备份等）
│   └── logger.py                 # 日志配置工具（控制台 + 文件双输出）
├── requirements.txt              # Python 依赖
└── README.md                     # 本文件
```

---

## 整体工作流程

```
┌──────────────────┐     ┌──────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│  ① 数据抓取       │────▶│  ② 保存原始数据    │────▶│  ③ AI 智能过滤       │────▶│  ④ 保存过滤结果   │
│  fetcher.py      │     │  file_utils.py   │     │  classifier.py      │     │  data_processor  │
│                  │     │                  │     │  related_classifier │     │                  │
│  weibotop.cn     │     │  → data/         │     │  DeepSeek API 判断   │     │  → data/         │
│  AES 加密通信     │     │    raw.json      │     │  是否明星相关        │     │    filtered.json  │
└──────────────────┘     └──────────────────┘     └─────────────────────┘     └──────────────────┘
```

### 详细流程说明

#### 步骤 ① — 数据抓取（`core/fetcher.py`）

1. `WeiboHotSearchFetcher` 根据指定日期范围，通过 **AES-ECB 加密参数**向 `api.weibotop.cn` 发起请求
2. 先调用 `/getclosesttime` 获取目标日期对应的 `timeid`
3. 再调用 `/currentitems?timeid=xxx` 获取该时刻的微博热搜列表
4. 使用 `ThreadPoolExecutor` **多线程并发**抓取多天数据，默认 10 线程
5. 可选开启 `--with-history`，额外调用 `/getrankhistory` 抓取每个关键词的排名/热度变化曲线
6. 内置**自动重试机制**（最多 3 次），应对网络波动

#### 步骤 ② — 保存原始数据（`utils/file_utils.py`）

1. 抓取到的数据按**日期索引结构**保存为 JSON（如 `data/weibo_raw.json`）
2. 非历史模式下额外生成**简化版文件**（`*_simplified.json`），仅保留排名、标题、热度、链接
3. 使用 `save_json_safely()` 确保目录自动创建、编码为 UTF-8、格式化缩进

#### 步骤 ③ — AI 智能过滤（`core/classifier.py` + `core/related_classifier.py`）

**第一层 — 直接识别（`TitleClassifier`）**：
1. 逐条将热搜标题发送至 DeepSeek API
2. 系统提示词严格限定判断范围为**娱乐明星**（演员、歌手、偶像、网红、主持人、模特、导演等）
3. 明确排除体育明星、政治人物、企业家、科学家等
4. 模型仅返回 `YES` 或 `NO`，解析后决定保留或丢弃

**第二层 — 关联推断（`RelatedCelebrityClassifier`，需启用 `--enhanced`）**：
1. 对第一层判断为"非明星"的标题，进一步调用 AI 分析其关联的娱乐明星
2. 例如：标题为某部电影名 → 推断出该电影的主演/导演
3. 返回结构化 JSON，包含 `related_celebrity`（明星姓名）和 `reasoning`（推理原因）
4. 若无法推断出明确明星则丢弃该条目

#### 步骤 ④ — 保存过滤结果（`core/data_processor.py`）

1. 将过滤后的记录按**原始数据结构回写**（兼容按日期索引、容器键、顶层列表等格式）
2. 每条保留的记录附加标记字段：
   - `filter_reason: "direct_celebrity"` — 直接识别为明星
   - `filter_reason: "inferred_celebrity"` — 增强模式推断出关联明星
   - `inference_reasoning` — 增强模式下的推断理由
3. 终端输出统计：总记录数、保留数、过滤数、保留比例

#### 流程编排（`core/orchestrator.py`）

- `fetch_and_process()` 函数将上述 4 步串联为一条**自动化流水线**
- 由 `scripts/fetch_and_filter.py` 脚本调用，用户无需手动介入各环节

---

## 安装

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd star_filter
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 依赖说明

| 包名 | 用途 |
|------|------|
| `openai` | 调用 DeepSeek API（兼容 OpenAI SDK） |
| `python-dotenv` | 从 `.env` 文件加载环境变量 |
| `requests` | HTTP 请求（微博数据抓取） |
| `tqdm` | 终端进度条显示 |
| `pycryptodome` | AES 加解密（微博 API 通信） |
| `pandas` | （可选）进一步数据分析 |
| `jq` | （可选）JSON 数据查看 |

---

## 配置

在项目根目录创建 `.env` 文件：

```env
# ═══════ 必填 ═══════
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# ═══════ 可选 ═══════
# DeepSeek API 地址（默认 https://api.deepseek.com）
DEEPSEEK_BASE_URL=https://api.deepseek.com

# DeepSeek 模型名称（默认 deepseek-chat）
DEEPSEEK_MODEL=deepseek-chat

# 微博数据抓取密钥
SECRET_KEY=your_secret_key_here

# 日志级别：DEBUG / INFO / WARNING / ERROR（默认 INFO）
LOG_LEVEL=INFO
```

> ⚠️ **重要**：`DEEPSEEK_API_KEY` 为必填项。未设置将无法运行 AI 过滤功能。
> 可在 [DeepSeek 官网](https://platform.deepseek.com/) 申请 API Key。

---

## 使用方法

本项目提供**两种入口脚本**，适用于不同场景：

---

### 方式一：一键抓取 + 过滤（推荐）

> 脚本：`scripts/fetch_and_filter.py`
> 流程：自动完成 **抓取微博热搜 → 保存原始数据 → AI 过滤 → 保存结果** 全流程

#### 基础用法

```bash
python scripts/fetch_and_filter.py --start 2025-12-20 --end 2025-12-24
```

#### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|:----:|--------|------|
| `--start` | ✅ | — | 开始日期，格式 `YYYY-MM-DD` |
| `--end` | ✅ | — | 结束日期，格式 `YYYY-MM-DD` |
| `--raw` | ❌ | `data/weibo_raw.json` | 原始数据保存路径 |
| `--output` | ❌ | `data/weibo_filtered.json` | 过滤结果保存路径 |
| `--with-history` | ❌ | 关闭 | 抓取每个关键词的排名/热度历史（较慢） |
| `--workers` | ❌ | `10` | 并发抓取线程数（开启历史时建议调至 3~5） |
| `--model` | ❌ | `deepseek-chat` | 指定 DeepSeek 模型名称 |
| `--enhanced` | ❌ | 关闭 | 启用增强模式（双层判断 + 关联明星推断） |

#### 典型示例

```bash
# 1) 抓取一天的数据并过滤
python scripts/fetch_and_filter.py --start 2025-12-20 --end 2025-12-20

# 2) 抓取一周数据，含关键词历史，启用增强模式
python scripts/fetch_and_filter.py \
  --start 2025-12-20 \
  --end 2025-12-26 \
  --with-history \
  --enhanced \
  --workers 5

# 3) 自定义输入输出路径
python scripts/fetch_and_filter.py \
  --start 2025-12-20 \
  --end 2025-12-24 \
  --raw data/my_raw.json \
  --output data/my_filtered.json

# 4) 使用其他模型
python scripts/fetch_and_filter.py \
  --start 2025-12-20 \
  --end 2025-12-20 \
  --model deepseek-reasoner
```

---

### 方式二：仅对已有 JSON 文件进行过滤

> 脚本：`scripts/filter_trends.py`
> 场景：已有本地 JSON 数据文件，只需执行 AI 明星过滤（无需再次抓取）

#### 基础用法

```bash
python scripts/filter_trends.py data/weibo_raw.json -o data/weibo_filtered.json
```

#### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|:----:|--------|------|
| `input`（位置参数） | ❌ | `trends_export.json` | 输入 JSON 文件路径 |
| `-o` / `--output` | ❌ | `trends_export_filtered.json` | 输出文件路径 |
| `--delay` | ❌ | `0.5` | API 请求间隔（秒） |
| `--model` | ❌ | `deepseek-chat` | 指定 DeepSeek 模型 |
| `--no-delay` | ❌ | 关闭 | 禁用请求延迟（不推荐，可能触发 API 限流） |
| `--enhanced` | ❌ | 关闭 | 启用增强模式（双层判断） |

#### 典型示例

```bash
# 1) 基础过滤
python scripts/filter_trends.py data/weibo_raw.json

# 2) 增强模式 + 自定义延迟
python scripts/filter_trends.py data/weibo_raw.json \
  -o data/result.json \
  --enhanced \
  --delay 1.0

# 3) 无延迟快速处理（注意限流风险）
python scripts/filter_trends.py data/weibo_raw.json --no-delay
```

---

## 支持的输入 JSON 格式

`DataProcessor` 能自动识别以下 JSON 结构，无需手动转换：

**格式 A — 按日期索引（微博抓取默认格式）**

```json
{
  "2025-12-20": {
    "items": [
      { "keyword": "某某明星官宣", "rank": 1 },
      { "keyword": "今日天气", "rank": 2 }
    ]
  }
}
```

**格式 B — 带容器键的字典**

```json
{
  "items": [
    { "title": "标题1" },
    { "title": "标题2" }
  ]
}
```

**格式 C — 顶层列表**

```json
[
  { "title": "标题1" },
  { "title": "标题2" }
]
```

标题字段自动识别优先级：`keyword` → `raw_data[0]` → `title` / `name` / `text` / `headline` / `topic`

---

## 输出数据说明

过滤后每条被保留的记录会附加以下字段：

| 字段 | 说明 |
|------|------|
| `filter_reason` | `"direct_celebrity"`（直接识别）或 `"inferred_celebrity"`（关联推断） |
| `original_title` | 增强模式下保留的原始标题文本 |
| `inference_reasoning` | 增强模式下的推断理由（如 "《某某》电影的主演"） |

---

## 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行单个模块测试
python -m pytest tests/test_classifier.py -v
python -m pytest tests/test_data_processor.py -v
python -m pytest tests/test_fetcher.py -v
python -m pytest tests/test_orchestrator.py -v
```

---

## 日志

运行日志同时输出到：
- **控制台** — 实时查看处理进度（含 tqdm 进度条）
- **日志文件** — `logs/star_filter.log`

通过 `.env` 中的 `LOG_LEVEL` 调整日志级别（`DEBUG` / `INFO` / `WARNING` / `ERROR`）。

---

## 核心模块一览

| 模块 | 类 / 函数 | 职责 |
|------|-----------|------|
| `core/api_client.py` | `DeepSeekClient` | 封装 DeepSeek API 客户端，管理密钥与连接 |
| `core/classifier.py` | `TitleClassifier` | 第一层分类：判断标题是否直接涉及娱乐明星 |
| `core/related_classifier.py` | `RelatedCelebrityClassifier` | 第二层推断：从非直接标题中推断关联明星 |
| `core/data_processor.py` | `DataProcessor` | 数据加载 / 标题提取 / 批量过滤 / 结果保存 |
| `core/fetcher.py` | `WeiboHotSearchFetcher` | 微博热搜抓取（AES 加密通信 / 多线程 / 历史数据） |
| `core/orchestrator.py` | `fetch_and_process()` | 全流程编排：抓取 → 保存 → 过滤 → 输出 |
| `utils/logger.py` | `setup_logger()` | 日志配置（控制台 + 文件双输出） |
| `utils/file_utils.py` | `save_json_safely()` 等 | JSON 安全读写 / 文件备份 / 路径验证 |
| `config/settings.py` | — | 全局配置项：API 参数 / 分类器提示词 / 文件路径 / 日志格式 |

---

## 常见问题

### Q: 报错 `DeepSeek API密钥未提供`

确保在项目根目录创建了 `.env` 文件，并正确填写了 `DEEPSEEK_API_KEY`。

### Q: 抓取数据为空

- 检查网络是否可以访问 `api.weibotop.cn`
- 确认日期范围内确实存在热搜数据
- 尝试减小 `--workers` 并发数（如 `--workers 3`）

### Q: 增强模式与普通模式有什么区别？

| | 普通模式 | 增强模式（`--enhanced`） |
|--|----------|------------------------|
| 判断层数 | 仅第一层（直接识别） | 两层（直接识别 + 关联推断） |
| API 调用量 | ≈ 条目总数 | 最多 ≈ 条目总数 × 2 |
| 覆盖范围 | 仅标题直接提及明星 | 可捕获间接相关内容（如作品名、梗、事件） |
| 速度 | 较快 | 较慢 |

### Q: 如何减少 API 调用费用？

- 使用普通模式（不加 `--enhanced`）
- 增大 `--delay` 参数降低请求频率
- 缩小日期范围，减少数据量
- 先用 `filter_trends.py` 对小样本测试，确认效果后再大批量处理
