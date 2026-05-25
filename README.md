# News Aggregator Skill

全网科技/金融/社会新闻聚合助手。40+ 信息源一站式覆盖，支持 AI 智能解读。

## 功能特性

- **多源聚合**：RSS + Web Scraping + API，覆盖中文新闻、全球 AI 博客、科技社区、财经数据、加密货币、A股公告
- **分类查询**：综合资讯、科技、AI、财经、国际、社会、体育、娱乐、新产品、开源项目、加密货币、A股公告
- **深度阅读**：`--deep` 模式自动下载文章正文，支持全文 AI 分析
- **关键词过滤**：支持多关键词组合搜索
- **零依赖**：基础功能纯 Python 标准库，安装 `requests` + `beautifulsoup4` 解锁全部功能
- **交互菜单**：`python scripts/news.py menu` 唤醒交互式菜单

## 信息源 (30+)

### 中文新闻
- 36氪、IT之家 — 科技创投
- 新浪财经、东方财富 — 金融市场
- 中国新闻网、澎湃新闻 — 社会民生
- 环球网、参考消息 — 国际新闻
- 新浪体育、虎扑 — 体育
- 新浪娱乐 — 娱乐

### AI / 科技博客
- MIT Technology Review — AI 与前沿技术
- OpenAI Blog — 模型发布与研究
- Google AI Blog — Google AI 研究
- DeepMind Blog — DeepMind 进展
- Latent Space — AI 工程师社区
- Interconnects — Nathan Lambert 深度分析
- One Useful Thing — Ethan Mollick AI 实践
- KDnuggets — AI/ML 技术聚合
- AI News Daily — 每日 AI 汇总
- Sebastian Raschka — ML 技术博客
- TechCrunch / The Verge / Ars Technica

### 科技社区
- Hacker News — 硅谷科技圈
- GitHub Trending — 开源热榜
- Product Hunt — 新产品发现
- V2EX — 中文开发者社区
- 微博热搜 — 社会热点
- 腾讯新闻 — 科技频道
- 华尔街见闻 — 金融市场快讯

### 加密货币
- CoinDesk / CoinTelegraph — 全球币圈要闻
- 金色财经 — 中文币圈快讯
- 吴说区块链 (Substack) — 深度分析
- 巴比特 — 区块链技术社区

### A股市场
- 东方财富公告 — 股东变更、公司公告、财报披露
- 巨潮资讯网 — 证监会官方指定披露平台
- 雪球热帖 — 投资者热议话题

## 快速开始

```bash
# 安装依赖（可选，解锁 web 源 + 深度抓取）
pip install requests beautifulsoup4

# 综合资讯
python scripts/news.py hot --limit 10

# AI 新闻
python scripts/news.py category --cat ai --limit 10

# GitHub 热榜
python scripts/news.py source --src github --limit 10

# 全网扫描
python scripts/news.py all --limit 15

# 查看所有源
python scripts/news.py sources
```

## 安装到 Claude Code

```bash
# 克隆仓库
git clone https://github.com/YOUR_USER/news-aggregator.git

# 安装到 Claude Code skills 目录
cp -r news-aggregator ~/.claude/skills/

# 或通过 npx
npx skills add https://github.com/YOUR_USER/news-aggregator
```

## 依赖

- Python 3.8+
- `requests` + `beautifulsoup4` (可选，解锁 web 抓取 + 深度阅读)

## 从旧版迁移

本 Skill 合并了以下三个 Skill 的功能：

| 旧 Skill | 功能 | 迁移方式 |
|----------|------|----------|
| `news` | 中文 RSS 新闻 + AI 博客 | `python scripts/news.py category --cat <分类>` |
| `newsgod` | Web 抓取 (HN, GitHub, 微博等) | `python scripts/news.py source --src <源ID>` |
| `news-sentiment-engine` | 英文科技 RSS + 情绪分析 | `python scripts/news.py category --cat ai` |

现在所有功能统一在一个脚本中。

## License

MIT
