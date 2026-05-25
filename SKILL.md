---
name: news-aggregator
description: 统一新闻聚合器。一站式覆盖 40+ 全球信息源（中文新闻、AI 技术博客、科技社区、财经数据、A股公告、加密货币、GitHub 热榜、微博热搜、Product Hunt 等），支持分类查询、关键词过滤、深度正文抓取、AI 智能解读。当用户询问最新新闻、AI 动态、科技资讯、A股公告、币圈行情、开源项目、行业热点时使用。
---

# 统一新闻聚合器 (News Aggregator)

融合 RSS 订阅 + 网页抓取 + API 数据源，40+ 信息源一站式覆盖。

## 无需 API Key

开箱即用，纯 Python 实现。基础功能零依赖（纯标准库），安装 `requests` + `beautifulsoup4` 可解锁 web 抓取源（微博、GitHub、华尔街见闻等）和深度正文抓取。

## 命令行调用

```bash
# 综合资讯（默认）
python scripts/news.py hot --limit 10

# 按分类查询
python scripts/news.py category --cat ai --limit 10
python scripts/news.py category --cat tech
python scripts/news.py category --cat finance
python scripts/news.py category --cat world
python scripts/news.py category --cat society
python scripts/news.py category --cat sports
python scripts/news.py category --cat entertainment
python scripts/news.py category --cat products
python scripts/news.py category --cat opensource

# 指定单个/多个源
python scripts/news.py source --src hackernews --limit 10
python scripts/news.py source --src github,weibo,v2ex --limit 10

# 加密货币
python scripts/news.py category --cat crypto --limit 10

# A股公告（股东变更、公司公告等）
python scripts/news.py category --cat a-stock --limit 10

# 全网扫描（所有 40+ 源）
python scripts/news.py all --limit 15

# 关键词过滤（支持逗号分隔，自动扩展）
python scripts/news.py hot --keyword "AI,GPT,LLM"
python scripts/news.py category --cat ai --keyword "OpenAI,DeepSeek"

# 深度抓取（下载文章正文进行 AI 分析）
python scripts/news.py hot --deep --limit 5

# 控制摘要长度
python scripts/news.py hot --detail 500    # 500 字符摘要
python scripts/news.py hot --detail -1     # RSS 全文
python scripts/news.py hot --detail 0      # 不显示摘要

# JSON 输出（程序化处理）
python scripts/news.py hot --json

# 查看所有源和分类
python scripts/news.py sources

# 交互菜单
python scripts/news.py menu
```

## 支持的新闻分类

### 中文资讯

| 分类 | 参数 | 来源 |
|------|------|------|
| 综合资讯 | `hot` | 36氪、IT之家、新浪财经、东方财富、中国新闻网、微博热搜、腾讯新闻、华尔街见闻 |
| 科技 | `tech` | 36氪、IT之家、Hacker News、V2EX、GitHub Trending、TechCrunch、The Verge、Ars Technica |
| 财经 | `finance` | 新浪财经、东方财富、华尔街见闻 |
| 国际 | `world` | 环球网、参考消息、中国新闻网国际 |
| 社会 | `society` | 中国新闻网、澎湃新闻、微博热搜 |
| 体育 | `sports` | 新浪体育、虎扑 |
| 娱乐 | `entertainment` | 新浪娱乐 |

### 加密货币

| 分类 | 参数 | 来源 |
|------|------|------|
| 加密货币 | `crypto` | CoinDesk、CoinTelegraph、Blockworks、Decrypt、金色财经、吴说区块链、巴比特 |

### A股市场

| 分类 | 参数 | 来源 |
|------|------|------|
| A股公告 | `a-stock` | 东方财富公告（股东变更/公司公告）、巨潮资讯网（官方披露）、雪球热帖 |

### AI / 科技

| 分类 | 参数 | 来源 |
|------|------|------|
| AI 技术 | `ai` | MIT Tech Review、OpenAI、Google AI、DeepMind、Latent Space、Interconnects、One Useful Thing、KDnuggets、AI News Daily、Sebastian Raschka、TechCrunch、The Verge、Ars Technica、Hacker News |
| 新产品 | `products` | Product Hunt |
| 开源项目 | `opensource` | GitHub Trending |

## AI 调用场景

用户说"今天有什么新闻"：
```bash
python scripts/news.py hot --limit 10
```

用户说"最近 AI 有什么新动态"：
```bash
python scripts/news.py category --cat ai --limit 10
```

用户说"GitHub 上有什么热门项目"：
```bash
python scripts/news.py source --src github --limit 10
```

用户说"微博上在讨论什么"：
```bash
python scripts/news.py source --src weibo --limit 10
```

用户说"搜一下关于 DeepSeek 的新闻"：
```bash
python scripts/news.py all --keyword "DeepSeek" --limit 15
```

用户说"最近币圈有什么消息"：
```bash
python scripts/news.py category --cat crypto --limit 10
```

用户说"A 股最近有什么公告"：
```bash
python scripts/news.py category --cat a-stock --limit 10
```

用户想深入了解某条新闻：
```bash
python scripts/news.py category --cat ai --keyword "OpenAI" --deep --limit 5
```

获取新闻后，整理为简洁列表返回给用户，包含标题、来源和链接。英文内容可适当翻译摘要。

### 深入阅读策略

1. **首选：`--deep`** — 下载并提取文章正文（需要 requests+bs4）
2. **备选：`--detail -1`** — 从 RSS 获取全文（纯标准库）
3. **不要对 AI 博客网站使用 web_fetch** — OpenAI、Google AI、DeepMind、MIT Tech Review 等会返回 403/404

## 依赖

```bash
# 基础功能（纯 Python 标准库，零依赖）
python scripts/news.py hot

# 完整功能（推荐）
pip install requests beautifulsoup4
```

## 注意事项

- RSS 源可能因网站调整而失效，脚本会自动跳过失败的源
- AI 博客多为英文，返回时可适当翻译摘要
- Web 抓取源（微博、GitHub、华尔街见闻等）需 `requests` + `beautifulsoup4`
- 深度抓取（`--deep`）需 `requests` + `beautifulsoup4`
- 环球网 RSS 可能不稳定，国际新闻建议用 `category --cat world` 自动 fallback
