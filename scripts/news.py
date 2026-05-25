#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified News Aggregator
合并 RSS (stdlib) + Web scraping (requests+bs4) + API 源
覆盖中文新闻、全球 AI 资讯、科技社区、财经数据
"""
import argparse
import json
import sys
import re
import io
import html as html_mod
import time
import concurrent.futures
import urllib.request
import urllib.error
from xml.etree import ElementTree as ET
from datetime import datetime
from urllib.parse import urljoin

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
TIMEOUT = 10

# ── Optional imports ─────────────────────────────────────────
try:
    import requests as req_lib
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


# ═══════════════════════════════════════════════════════════════
# SOURCE DEFINITIONS
# ═══════════════════════════════════════════════════════════════

# type: rss (stdlib xml), web (bs4 scraping), api (json endpoint)
ALL_SOURCES = {
    # ── Chinese Tech ──
    "36kr": {
        "name": "36氪", "type": "rss", "cat": ["tech", "hot"],
        "url": "https://36kr.com/feed",
    },
    "ithome": {
        "name": "IT之家", "type": "rss", "cat": ["tech", "hot"],
        "url": "https://www.ithome.com/rss/",
    },
    # ── Chinese Finance ──
    "sinanews": {
        "name": "新浪财经", "type": "api", "cat": ["finance", "hot"],
        "url": "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=20&page=1&r=0.1&callback=",
    },
    "eastmoney": {
        "name": "东方财富", "type": "web", "cat": ["finance", "hot"],
        "url": "https://www.eastmoney.com/",
    },
    # ── Chinese General ──
    "chinanews": {
        "name": "中国新闻网", "type": "rss", "cat": ["society", "hot"],
        "url": "https://www.chinanews.com/rss/scroll-news.xml",
    },
    "thepaper": {
        "name": "澎湃新闻", "type": "rss", "cat": ["society"],
        "url": "https://www.thepaper.cn/rss_newslist_all.xml",
    },
    # ── Chinese World ──
    "huanqiu": {
        "name": "环球网", "type": "rss", "cat": ["world"],
        "url": "https://world.huanqiu.com/rss/world.xml",
    },
    "cankaoxiaoxi": {
        "name": "参考消息", "type": "rss", "cat": ["world"],
        "url": "http://www.cankaoxiaoxi.com/rss/roll.xml",
    },
    "chinanews-world": {
        "name": "中国新闻网国际", "type": "rss", "cat": ["world"],
        "url": "https://www.chinanews.com/rss/world.xml",
    },
    # ── Sports / Entertainment ──
    "sina-sports": {
        "name": "新浪体育", "type": "web", "cat": ["sports"],
        "url": "https://sports.sina.com.cn/",
    },
    "hupu": {
        "name": "虎扑", "type": "web", "cat": ["sports"],
        "url": "https://www.hupu.com/",
    },
    "sina-ent": {
        "name": "新浪娱乐", "type": "web", "cat": ["entertainment"],
        "url": "https://ent.sina.com.cn/",
    },
    # ── Hacker News / Product Hunt (RSS versions as fallback) ──
    "hn-rss": {
        "name": "Hacker News", "type": "rss", "cat": ["tech", "ai"],
        "url": "https://hnrss.org/frontpage",
    },
    "producthunt": {
        "name": "Product Hunt", "type": "rss", "cat": ["products", "ai"],
        "url": "https://www.producthunt.com/feed",
    },
    # ── AI / ML Blogs (English) ──
    "mit-tr": {
        "name": "MIT Tech Review", "type": "rss", "cat": ["ai"],
        "url": "https://www.technologyreview.com/feed/",
    },
    "openai": {
        "name": "OpenAI Blog", "type": "rss", "cat": ["ai"],
        "url": "https://openai.com/blog/rss.xml",
    },
    "google-ai": {
        "name": "Google AI Blog", "type": "rss", "cat": ["ai"],
        "url": "https://blog.google/technology/ai/rss/",
    },
    "deepmind": {
        "name": "DeepMind Blog", "type": "rss", "cat": ["ai"],
        "url": "https://deepmind.google/blog/rss.xml",
    },
    "latentspace": {
        "name": "Latent Space", "type": "rss", "cat": ["ai"],
        "url": "https://www.latent.space/feed",
    },
    "interconnects": {
        "name": "Interconnects", "type": "rss", "cat": ["ai"],
        "url": "https://www.interconnects.ai/feed",
    },
    "oneusefulthing": {
        "name": "One Useful Thing", "type": "rss", "cat": ["ai"],
        "url": "https://www.oneusefulthing.org/feed",
    },
    "kdnuggets": {
        "name": "KDnuggets", "type": "rss", "cat": ["ai"],
        "url": "https://www.kdnuggets.com/feed",
    },
    "ai-news-daily": {
        "name": "AI News Daily", "type": "rss", "cat": ["ai"],
        "url": "https://buttondown.com/ainews/rss",
    },
    "sebastian-raschka": {
        "name": "Sebastian Raschka", "type": "rss", "cat": ["ai"],
        "url": "https://magazine.sebastianraschka.com/feed",
    },
    "techcrunch": {
        "name": "TechCrunch", "type": "rss", "cat": ["ai", "tech"],
        "url": "https://techcrunch.com/feed/",
    },
    "theverge": {
        "name": "The Verge", "type": "rss", "cat": ["ai", "tech"],
        "url": "https://www.theverge.com/rss/index.xml",
    },
    "arstechnica": {
        "name": "Ars Technica", "type": "rss", "cat": ["ai", "tech"],
        "url": "https://feeds.arstechnica.com/arstechnica/index",
    },
    # ── Cryptocurrency ──
    "coindesk": {
        "name": "CoinDesk", "type": "rss", "cat": ["crypto"],
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    },
    "cointelegraph": {
        "name": "CoinTelegraph", "type": "rss", "cat": ["crypto"],
        "url": "https://cointelegraph.com/rss",
    },
    "blockworks": {
        "name": "Blockworks", "type": "rss", "cat": ["crypto"],
        "url": "https://blockworks.co/feed",
    },
    "decrypt": {
        "name": "Decrypt", "type": "rss", "cat": ["crypto"],
        "url": "https://decrypt.co/feed",
    },
    "jinse": {
        "name": "金色财经", "type": "web", "cat": ["crypto"],
        "url": "https://www.jinse.com/",
    },
    "wublock": {
        "name": "吴说区块链", "type": "rss", "cat": ["crypto"],
        "url": "https://wublock.substack.com/feed",
    },
    "8btc": {
        "name": "巴比特", "type": "rss", "cat": ["crypto"],
        "url": "https://www.8btc.com/rss",
    },
    # ── A-Share Announcements ──
    "eastmoney-ann": {
        "name": "东方财富公告", "type": "web", "cat": ["a-stock", "finance"],
        "url": "https://np-anotice-stock.eastmoney.com/api/security/ann?page_size=30&page_index=1&ann_type=A",
    },
    "cninfo": {
        "name": "巨潮资讯网", "type": "web", "cat": ["a-stock"],
        "url": "http://www.cninfo.com.cn/new/hisAnnouncement/query",
    },
    "xueqiu": {
        "name": "雪球热帖", "type": "web", "cat": ["a-stock"],
        "url": "https://xueqiu.com/v4/statuses/public_timeline_by_category.json?category_id=6",
    },
    # ── Web scraping sources (require requests+bs4) ──
    "hackernews": {
        "name": "Hacker News", "type": "web", "cat": ["tech"],
        "url": "https://news.ycombinator.com",
    },
    "github": {
        "name": "GitHub Trending", "type": "web", "cat": ["tech", "opensource"],
        "url": "https://github.com/trending",
    },
    "weibo": {
        "name": "微博热搜", "type": "web", "cat": ["society", "hot"],
        "url": "https://weibo.com/ajax/side/hotSearch",
    },
    "v2ex": {
        "name": "V2EX", "type": "web", "cat": ["tech"],
        "url": "https://www.v2ex.com/api/topics/hot.json",
    },
    "tencent": {
        "name": "腾讯新闻", "type": "web", "cat": ["tech", "hot"],
        "url": "https://i.news.qq.com/web_backend/v2/getTagInfo?tagId=aEWqxLtdgmQ%3D",
    },
    "wallstreetcn": {
        "name": "华尔街见闻", "type": "web", "cat": ["finance", "hot"],
        "url": "https://api-one.wallstcn.com/apiv1/content/information-flow?channel=global-channel&accept=article&limit=30",
    },
}

CATEGORIES = {
    "hot": {
        "name": "综合资讯",
        "sources": ["36kr", "ithome", "sinanews", "eastmoney", "chinanews", "weibo", "tencent", "wallstreetcn"],
    },
    "tech": {
        "name": "科技",
        "sources": ["36kr", "ithome", "hackernews", "v2ex", "github", "techcrunch", "theverge", "arstechnica"],
    },
    "ai": {
        "name": "AI 技术",
        "sources": ["mit-tr", "openai", "google-ai", "deepmind", "latentspace", "interconnects",
                    "oneusefulthing", "kdnuggets", "ai-news-daily", "sebastian-raschka",
                    "techcrunch", "theverge", "arstechnica", "hn-rss"],
    },
    "finance": {
        "name": "财经",
        "sources": ["sinanews", "eastmoney", "wallstreetcn"],
    },
    "world": {
        "name": "国际",
        "sources": ["huanqiu", "cankaoxiaoxi", "chinanews-world"],
    },
    "society": {
        "name": "社会",
        "sources": ["chinanews", "thepaper", "weibo"],
    },
    "sports": {
        "name": "体育",
        "sources": ["sina-sports", "hupu"],
    },
    "entertainment": {
        "name": "娱乐",
        "sources": ["sina-ent"],
    },
    "products": {
        "name": "新产品",
        "sources": ["producthunt"],
    },
    "opensource": {
        "name": "开源项目",
        "sources": ["github"],
    },
    "crypto": {
        "name": "加密货币",
        "sources": ["coindesk", "cointelegraph", "blockworks", "decrypt", "jinse", "wublock", "8btc"],
    },
    "a-stock": {
        "name": "A股公告",
        "sources": ["eastmoney-ann", "cninfo", "xueqiu"],
    },
}


# ═══════════════════════════════════════════════════════════════
# NETWORK UTILITIES
# ═══════════════════════════════════════════════════════════════

def fetch_stdlib(url, timeout=TIMEOUT, retry=2):
    """stdlib urllib fetch, returns text or None"""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(retry):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                for enc in ('utf-8', 'gbk', 'gb2312', 'latin-1'):
                    try:
                        return data.decode(enc)
                    except (UnicodeDecodeError, LookupError):
                        continue
                return data.decode('utf-8', errors='replace')
        except urllib.error.HTTPError as e:
            if attempt < retry - 1:
                time.sleep(1)
                continue
            print(f"  ⚠️  HTTP {e.code}: {url}", file=sys.stderr)
            return None
        except Exception as e:
            if attempt < retry - 1:
                time.sleep(1)
                continue
            print(f"  ⚠️  网络错误: {url}", file=sys.stderr)
            return None
    return None


def fetch_bs4(url, timeout=TIMEOUT):
    """requests-based fetch, returns text or None"""
    if not HAS_BS4:
        return None
    try:
        resp = req_lib.get(url, headers={"User-Agent": UA}, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════
# RSS PARSING (stdlib xml)
# ═══════════════════════════════════════════════════════════════

def _text(el, tag):
    child = el.find(tag)
    return child.text if child is not None and child.text else None


def _clean(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = html_mod.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _parse_time(time_str):
    if not time_str:
        return ""
    for fmt in ('%a, %d %b %Y %H:%M:%S %z', '%a, %d %b %Y %H:%M:%S GMT',
                '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            dt = datetime.strptime(time_str.strip(), fmt)
            return dt.strftime('%m-%d %H:%M')
        except ValueError:
            continue
    return time_str[:16]


def parse_rss(xml_text, source_name):
    """Parse RSS 2.0 / Atom XML, return list of news items"""
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items

    # RSS 2.0
    for item in root.iter('item'):
        title = _text(item, 'title')
        link = _text(item, 'link')
        pub = _text(item, 'pubDate')
        desc = _text(item, 'description')
        content = None
        for tag in ('{http://purl.org/rss/1.0/modules/content/}encoded', 'content:encoded'):
            content = _text(item, tag)
            if content:
                break
        body = _clean(content) if content else (_clean(desc) if desc else "")
        if title and link:
            items.append({
                "title": _clean(title), "url": link.strip(),
                "source": source_name, "time": _parse_time(pub),
                "summary": body, "heat": "",
            })

    # Atom
    if not items:
        for entry in root.iter('{http://www.w3.org/2005/Atom}entry'):
            title = _text(entry, '{http://www.w3.org/2005/Atom}title')
            link_el = entry.find('{http://www.w3.org/2005/Atom}link')
            link = link_el.get('href', '') if link_el is not None else ''
            pub = _text(entry, '{http://www.w3.org/2005/Atom}published') or \
                  _text(entry, '{http://www.w3.org/2005/Atom}updated')
            content = _text(entry, '{http://www.w3.org/2005/Atom}content') or \
                      _text(entry, '{http://www.w3.org/2005/Atom}summary') or ""
            if title and link:
                items.append({
                    "title": _clean(title), "url": link.strip(),
                    "source": source_name, "time": _parse_time(pub),
                    "summary": _clean(content), "heat": "",
                })
    return items


# ═══════════════════════════════════════════════════════════════
# API / JSON PARSING
# ═══════════════════════════════════════════════════════════════

def parse_sina_api(text, source_name):
    """新浪财经滚动新闻 API (JSONP)"""
    items = []
    try:
        text_clean = re.sub(r'^[^{]*', '', text)
        text_clean = re.sub(r'[^}]*$', '', text_clean)
        data = json.loads(text_clean)
        for item in data.get('result', {}).get('data', []):
            title = item.get('title', '')
            link = item.get('url', '')
            ctime = item.get('ctime', '')
            if title and link:
                items.append({
                    "title": _clean(title), "url": link,
                    "source": source_name, "time": ctime,
                    "summary": _clean(item.get('intro', ''))[:200], "heat": "",
                })
    except (json.JSONDecodeError, KeyError):
        pass
    return items


# ═══════════════════════════════════════════════════════════════
# WEB SCRAPERS (require requests+bs4)
# ═══════════════════════════════════════════════════════════════

def scrape_hackernews(limit=10, keyword=None):
    """Scrape Hacker News frontpage"""
    if not HAS_BS4:
        return []
    items = []
    page = 1
    while len(items) < limit and page <= 5:
        url = f"https://news.ycombinator.com/news?p={page}"
        text = fetch_bs4(url)
        if not text:
            break
        soup = BeautifulSoup(text, 'html.parser')
        rows = soup.select('.athing')
        if not rows:
            break
        for row in rows:
            try:
                id_ = row.get('id')
                title_line = row.select_one('.titleline a')
                if not title_line:
                    continue
                title = title_line.get_text()
                link = title_line.get('href')
                score_span = soup.select_one(f'#score_{id_}')
                score = score_span.get_text() if score_span else "0 points"
                age_span = soup.select_one(f'.age a[href="item?id={id_}"]')
                time_str = age_span.get_text() if age_span else ""
                if link and link.startswith('item?id='):
                    link = f"https://news.ycombinator.com/{link}"
                items.append({
                    "title": title, "url": link or "",
                    "source": "Hacker News", "time": time_str,
                    "heat": score, "summary": "",
                })
            except Exception:
                continue
        page += 1
        time.sleep(0.3)
    return _filter_keyword(items, keyword)[:limit]


def scrape_weibo(limit=10, keyword=None):
    """Weibo hot search API"""
    if not HAS_BS4:
        return []
    try:
        resp = req_lib.get("https://weibo.com/ajax/side/hotSearch", headers={
            "User-Agent": UA, "Referer": "https://weibo.com/"
        }, timeout=10)
        data = resp.json()
        items = []
        for item in data.get('data', {}).get('realtime', []):
            title = item.get('note', '') or item.get('word', '')
            if not title:
                continue
            heat = item.get('num', 0)
            url = f"https://s.weibo.com/weibo?q={req_lib.utils.quote(title)}&Refer=top"
            items.append({
                "title": title, "url": url,
                "source": "微博热搜", "time": "实时",
                "heat": f"{heat}", "summary": "",
            })
        return _filter_keyword(items, keyword)[:limit]
    except Exception:
        return []


def scrape_github(limit=10, keyword=None):
    """GitHub Trending"""
    if not HAS_BS4:
        return []
    try:
        text = fetch_bs4("https://github.com/trending")
        if not text:
            return []
        soup = BeautifulSoup(text, 'html.parser')
        items = []
        for article in soup.select('article.Box-row'):
            try:
                h2 = article.select_one('h2 a')
                if not h2:
                    continue
                title = h2.get_text(strip=True).replace('\n', '').replace(' ', '')
                link = "https://github.com" + h2['href']
                desc_el = article.select_one('p')
                desc_text = desc_el.get_text(strip=True) if desc_el else ""
                stars_tag = article.select_one('a[href$="/stargazers"]')
                stars = stars_tag.get_text(strip=True) if stars_tag else ""
                items.append({
                    "title": f"{title} - {desc_text}", "url": link,
                    "source": "GitHub Trending", "time": "今日",
                    "heat": f"{stars} stars", "summary": desc_text,
                })
            except Exception:
                continue
        return _filter_keyword(items, keyword)[:limit]
    except Exception:
        return []


def scrape_v2ex(limit=10, keyword=None):
    """V2EX hot topics"""
    if not HAS_BS4:
        return []
    try:
        data = req_lib.get("https://www.v2ex.com/api/topics/hot.json",
                           headers={"User-Agent": UA}, timeout=10).json()
        items = []
        for t in data:
            items.append({
                "title": t['title'], "url": t['url'],
                "source": "V2EX", "time": "热门",
                "heat": f"{t.get('replies', 0)} replies", "summary": "",
            })
        return _filter_keyword(items, keyword)[:limit]
    except Exception:
        return []


def scrape_tencent(limit=10, keyword=None):
    """Tencent News tech channel"""
    if not HAS_BS4:
        return []
    try:
        url = "https://i.news.qq.com/web_backend/v2/getTagInfo?tagId=aEWqxLtdgmQ%3D"
        data = req_lib.get(url, headers={"Referer": "https://news.qq.com/"}, timeout=10).json()
        items = []
        for news in data['data']['tabs'][0]['articleList']:
            items.append({
                "title": news['title'],
                "url": news.get('url') or news.get('link_info', {}).get('url', ''),
                "source": "腾讯新闻", "time": news.get('pub_time', '') or news.get('publish_time', ''),
                "summary": "", "heat": "",
            })
        return _filter_keyword(items, keyword)[:limit]
    except Exception:
        return []


def scrape_wallstreetcn(limit=10, keyword=None):
    """WallStreetCN information flow"""
    if not HAS_BS4:
        return []
    try:
        url = "https://api-one.wallstcn.com/apiv1/content/information-flow?channel=global-channel&accept=article&limit=30"
        data = req_lib.get(url, timeout=10).json()
        items = []
        for item in data['data']['items']:
            res = item.get('resource')
            if res and (res.get('title') or res.get('content_short')):
                ts = res.get('display_time', 0)
                time_str = datetime.fromtimestamp(ts).strftime('%m-%d %H:%M') if ts else ""
                items.append({
                    "title": res.get('title') or res.get('content_short'),
                    "url": res.get('uri', ''),
                    "source": "华尔街见闻", "time": time_str,
                    "summary": _clean(res.get('content_short', ''))[:200],
                    "heat": "",
                })
        return _filter_keyword(items, keyword)[:limit]
    except Exception:
        return []


def scrape_eastmoney_ann(limit=10, keyword=None):
    """东方财富 A股公告 API"""
    if not HAS_BS4:
        return []
    try:
        url = "https://np-anotice-stock.eastmoney.com/api/security/ann?page_size=30&page_index=1&ann_type=A"
        resp = req_lib.get(url, headers={"User-Agent": UA, "Referer": "https://data.eastmoney.com/"}, timeout=10)
        data = resp.json()
        items = []
        for ann in data.get('data', {}).get('list', []):
            title = ann.get('title', '')
            code = ann.get('security_code', '')
            name = ann.get('security_name_short', '')
            notice_date = ann.get('notice_date', '')
            url = f"https://data.eastmoney.com/notices/detail/{code}/{ann.get('art_code', '')}.html"
            summary = ann.get('summary', '')
            # Format: "[股票代码 股票名] 公告标题"
            display_title = f"[{code} {name}] {title}" if code else title
            if title:
                items.append({
                    "title": display_title, "url": url,
                    "source": "东方财富公告", "time": str(notice_date),
                    "summary": _clean(summary)[:200] if summary else "",
                    "heat": "",
                })
        return _filter_keyword(items, keyword)[:limit]
    except Exception:
        return []


def scrape_cninfo(limit=10, keyword=None):
    """巨潮资讯网 A股公告 (官方披露平台)"""
    if not HAS_BS4:
        return []
    try:
        url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
        headers = {
            "User-Agent": UA,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
        }
        data = {"pageNum": 1, "pageSize": 30, "column": "szse", "tabName": "fulltext", "plate": "", "stock": "", "searchkey": "", "secid": "", "category": "", "trade": "", "seDate": ""}
        resp = req_lib.post(url, headers=headers, data=data, timeout=10)
        result = resp.json()
        items = []
        for ann in result.get('announcements', []) or result.get('data', []):
            title = ann.get('announcementTitle', '') or ann.get('title', '')
            code = ann.get('secCode', '') or ann.get('sec_code', '')
            name = ann.get('secName', '') or ann.get('sec_name', '')
            date = ann.get('announcementTime', '') or ann.get('notice_date', '')
            ann_id = ann.get('announcementId', '') or ann.get('id', '')
            adjunct = ann.get('adjunctUrl', '') or ann.get('adjunct_url', '')
            display_title = f"[{code} {name}] {title}" if code else title
            if title:
                items.append({
                    "title": _clean(display_title), "url": f"http://www.cninfo.com.cn/new/disclosure/detail?announcementId={ann_id}&orgId={adjunct}" if ann_id else "http://www.cninfo.com.cn/",
                    "source": "巨潮资讯网", "time": str(date)[:10] if date else "",
                    "summary": "", "heat": "",
                })
        return _filter_keyword(items, keyword)[:limit]
    except Exception:
        return []


def scrape_xueqiu(limit=10, keyword=None):
    """雪球热帖"""
    if not HAS_BS4:
        return []
    try:
        url = "https://xueqiu.com/v4/statuses/public_timeline_by_category.json?category_id=6&page=1&size=20"
        headers = {"User-Agent": UA, "Referer": "https://xueqiu.com/"}
        resp = req_lib.get(url, headers=headers, timeout=10)
        data = resp.json()
        items = []
        for st in data.get('list', []):
            title = _clean(st.get('title', '') or st.get('text', '') or '')
            if not title:
                continue
            # Truncate long titles
            if len(title) > 100:
                title = title[:100] + "..."
            sid = st.get('id', '')
            uid = st.get('user', {}).get('id', '')
            ts = st.get('created_at', 0)
            time_str = datetime.fromtimestamp(ts / 1000).strftime('%m-%d %H:%M') if ts else ""
            reply = st.get('reply_count', 0)
            items.append({
                "title": title, "url": f"https://xueqiu.com/{uid}/{sid}",
                "source": "雪球", "time": time_str,
                "heat": f"{reply} 评论" if reply else "",
                "summary": "",
            })
        return _filter_keyword(items, keyword)[:limit]
    except Exception:
        return []


def scrape_web_titles(html_text, source_name, base_url):
    """Generic web scraper: extract titles/links from HTML <a> tags"""
    items = []
    pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]{8,80})</a>'
    seen = set()
    for match in re.finditer(pattern, html_text):
        link, title = match.group(1), match.group(2)
        title = _clean(title)
        if not title or len(title) < 8:
            continue
        if any(skip in title for skip in ('首页', '登录', '注册', '关于我们', '联系', '广告', '下载', '客户端', '反馈')):
            continue
        if link.startswith('//'):
            link = 'https:' + link
        elif link.startswith('/'):
            link = urljoin(base_url, link)
        elif not link.startswith('http'):
            continue
        if title in seen:
            continue
        seen.add(title)
        items.append({
            "title": title, "url": link,
            "source": source_name, "time": "",
            "summary": "", "heat": "",
        })
    return items


# ═══════════════════════════════════════════════════════════════
# DEEP FETCH (article content extraction)
# ═══════════════════════════════════════════════════════════════

def fetch_article_content(url):
    """Download and extract text from a URL. Truncate to 3000 chars."""
    if not url or not url.startswith('http'):
        return ""
    if not HAS_BS4:
        return ""
    try:
        resp = req_lib.get(url, headers={"User-Agent": UA}, timeout=8)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.extract()
        text = soup.get_text(separator=' ', strip=True)
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text[:3000]
    except Exception:
        return ""


def enrich_items(items, max_workers=10):
    """Deep-fetch article content for all items concurrently"""
    if not items or not HAS_BS4:
        return items
    print(f"  📥 深度抓取 {len(items)} 篇文章正文...", file=sys.stderr)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_article_content, item['url']): item for item in items}
        for future in concurrent.futures.as_completed(futures):
            item = futures[future]
            try:
                content = future.result()
                if content:
                    item['content'] = content
            except Exception:
                item['content'] = ""
    return items


# ═══════════════════════════════════════════════════════════════
# TRANSLATION (Google Translate free API, no key required)
# ═══════════════════════════════════════════════════════════════

def _has_cjk(text):
    """Detect if text contains Chinese/Japanese/Korean characters"""
    if not text:
        return False
    cjk_count = 0
    for ch in text:
        cp = ord(ch)
        if (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or
            0x3040 <= cp <= 0x309F or 0xAC00 <= cp <= 0xD7AF):
            cjk_count += 1
    return cjk_count > len(text) * 0.3  # > 30% CJK → already translated-ish


def _needs_translate(text):
    """Check if text needs translation (non-empty, contains meaningful latin content)"""
    if not text or not text.strip():
        return False
    if _has_cjk(text):
        return False
    # Count latin letters
    latin = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    return latin > 10


def translate_text(text):
    """Translate text to Chinese using free Google Translate API. Returns original on failure."""
    if not _needs_translate(text):
        return text
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": "auto", "tl": "zh-CN", "dt": "t", "q": text[:1000]}
        resp = req_lib.get(url, params=params, headers={"User-Agent": UA}, timeout=5)
        data = resp.json()
        parts = []
        for block in data[0]:
            if block[0]:
                parts.append(block[0])
        return "".join(parts) if parts else text
    except Exception:
        return text


def translate_items(items, fields=("title", "summary")):
    """Translate specified fields of all items to Chinese. Modifies items in-place."""
    if not HAS_BS4:
        return items
    print(f"  🌐 翻译 {len(items)} 条内容...", file=sys.stderr)
    for item in items:
        for field in fields:
            text = item.get(field, "")
            if _needs_translate(text):
                item[field] = translate_text(text)
    return items


# ═══════════════════════════════════════════════════════════════
# FILTERING & HELPERS
# ═══════════════════════════════════════════════════════════════

def _filter_keyword(items, keyword):
    if not keyword:
        return items
    keywords = [k.strip() for k in keyword.split(',') if k.strip()]
    if not keywords:
        return items
    pattern = '|'.join([r'\b' + re.escape(k) + r'\b' for k in keywords])
    regex = re.compile(r'(?i)(' + pattern + r')')
    return [item for item in items
            if regex.search(item.get('title', '')) or regex.search(item.get('summary', ''))]


def _fetch_one_source(src_def):
    """Fetch a single source by its definition. Returns list of items."""
    name = src_def["name"]
    stype = src_def["type"]
    url = src_def["url"]
    limit = src_def.get("_limit", 10)
    keyword = src_def.get("_keyword", None)

    print(f"  📡 正在获取 {name}...", file=sys.stderr)

    try:
        if stype == "rss":
            if 'feed.mix.sina.com.cn' in url:
                # Special case: sina finance API disguised as RSS
                text = fetch_stdlib(url)
                if not text:
                    print(f"  ❌ {name} 获取失败", file=sys.stderr)
                    return []
                items = parse_sina_api(text, name)
            else:
                text = fetch_stdlib(url)
                if not text:
                    print(f"  ❌ {name} 获取失败", file=sys.stderr)
                    return []
                items = parse_rss(text, name)

        elif stype == "api":
            text = fetch_stdlib(url)
            if not text:
                print(f"  ❌ {name} 获取失败", file=sys.stderr)
                return []
            if 'sina.com.cn' in url:
                items = parse_sina_api(text, name)
            else:
                try:
                    data = json.loads(text)
                    items = []
                    # Generic API parsing — subclasses handle specifics
                except json.JSONDecodeError:
                    items = []

        elif stype == "web":
            if not HAS_BS4:
                print(f"  ⚠️  {name} 需要 requests+bs4，已跳过", file=sys.stderr)
                return []
            # Map source name to scraper function
            scraper_map = {
                "Hacker News": scrape_hackernews,
                "微博热搜": scrape_weibo,
                "GitHub Trending": scrape_github,
                "V2EX": scrape_v2ex,
                "腾讯新闻": scrape_tencent,
                "华尔街见闻": scrape_wallstreetcn,
                "东方财富公告": scrape_eastmoney_ann,
                "巨潮资讯网": scrape_cninfo,
                "雪球": scrape_xueqiu,
            }
            if name in scraper_map:
                items = scraper_map[name](limit=limit, keyword=keyword)
            else:
                text = fetch_bs4(url)
                if not text:
                    print(f"  ❌ {name} 获取失败", file=sys.stderr)
                    return []
                items = scrape_web_titles(text, name, url)
        else:
            return []

        print(f"  ✅ {name} 获取成功 ({len(items)} 条)", file=sys.stderr)
        return items

    except Exception as e:
        print(f"  ❌ {name} 异常: {type(e).__name__}: {e}", file=sys.stderr)
        return []


# ═══════════════════════════════════════════════════════════════
# CORE LOGIC
# ═══════════════════════════════════════════════════════════════

def fetch_news(sources=None, category=None, keyword=None, limit=10, deep=False, translate=False):
    """Main entry point: fetch news from specified sources or category."""
    # Resolve sources
    if category:
        cat_info = CATEGORIES.get(category)
        if not cat_info:
            print(f"未知分类: {category}", file=sys.stderr)
            return []
        source_ids = cat_info["sources"]
        cat_name = cat_info["name"]
    elif sources:
        source_ids = [s.strip() for s in sources.split(',')]
        cat_name = "自定义"
    else:
        source_ids = CATEGORIES["hot"]["sources"]
        cat_name = "综合资讯"

    # Build source definitions with runtime params
    resolved = []
    for sid in source_ids:
        if sid in ALL_SOURCES:
            src = dict(ALL_SOURCES[sid])  # copy
            src["_limit"] = limit
            src["_keyword"] = keyword
            src["_id"] = sid
            resolved.append(src)
        else:
            print(f"  ⚠️  未知源: {sid}", file=sys.stderr)

    if not resolved:
        print("没有可用的新闻源", file=sys.stderr)
        return []

    print(f"\n🔍 开始获取 {cat_name} 新闻 ({len(resolved)} 个源)...", file=sys.stderr)

    # Concurrent fetch
    all_items = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(resolved), 8)) as pool:
        futures = {pool.submit(_fetch_one_source, src): src for src in resolved}
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result(timeout=20)
                all_items.extend(result)
            except Exception as e:
                src = futures[future]
                print(f"  ❌ {src['name']} 超时: {e}", file=sys.stderr)

    # Deduplicate by title
    seen = set()
    unique = []
    for item in all_items:
        if item["title"] not in seen:
            seen.add(item["title"])
            unique.append(item)

    # Sort by time (newest first), no-time items at end
    def sort_key(item):
        t = item.get("time", "")
        if not t:
            return "99-99 99:99"
        return t

    unique.sort(key=sort_key, reverse=True)

    # Keyword filter (already applied per-source, but double-check)
    if keyword:
        unique = _filter_keyword(unique, keyword)

    # Diversify: interleave sources so no single source dominates
    if len(unique) > limit:
        by_source = {}
        for item in unique:
            s = item.get("source", "Unknown")
            by_source.setdefault(s, []).append(item)
        diversified = []
        while len(diversified) < limit and by_source:
            for s in list(by_source.keys()):
                if by_source[s]:
                    diversified.append(by_source[s].pop(0))
                    if len(diversified) >= limit:
                        break
                else:
                    del by_source[s]
        unique = diversified
    else:
        unique = unique[:limit]

    # Deep fetch if requested
    if deep and unique:
        unique = enrich_items(unique)

    # Translate if requested
    if translate and unique:
        unique = translate_items(unique)

    return unique


# ═══════════════════════════════════════════════════════════════
# OUTPUT FORMATTING
# ═══════════════════════════════════════════════════════════════

def format_news(items, title="新闻", summary_len=100):
    """Format news items for terminal display."""
    lines = [f"📰 {title} (共 {len(items)} 条)\n"]
    for i, item in enumerate(items, 1):
        time_str = f" | {item['time']}" if item.get('time') else ""
        heat_str = f" | 🔥 {item['heat']}" if item.get('heat') else ""
        lines.append(f"  {i}. {item['title']}")
        lines.append(f"     📌 {item['source']}{time_str}{heat_str}")
        lines.append(f"     🔗 {item['url']}")
        if item.get('summary') and summary_len != 0:
            text = item['summary']
            if summary_len > 0 and len(text) > summary_len:
                text = text[:summary_len] + "..."
            lines.append(f"     📝 {text}")
        if item.get('content') and summary_len == -1:
            text = item['content']
            if len(text) > 500:
                text = text[:500] + "..."
            lines.append(f"     📄 {text}")
        lines.append("")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def cmd_hot(args):
    items = fetch_news(category="hot", keyword=args.keyword, limit=args.limit, deep=args.deep, translate=args.translate)
    if not items:
        print("暂无新闻数据")
        return
    if args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
    else:
        print(format_news(items, "综合资讯", summary_len=args.detail))


def cmd_category(args):
    if args.cat not in CATEGORIES:
        print(f"不支持的分类: {args.cat}", file=sys.stderr)
        print(f"支持: {', '.join(CATEGORIES.keys())}", file=sys.stderr)
        sys.exit(1)
    items = fetch_news(category=args.cat, keyword=args.keyword, limit=args.limit, deep=args.deep, translate=args.translate)
    if not items:
        print(f"暂无 {CATEGORIES[args.cat]['name']} 新闻")
        return
    if args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
    else:
        print(format_news(items, CATEGORIES[args.cat]['name'], summary_len=args.detail))


def cmd_source(args):
    """Fetch from specific named source(s)"""
    source_ids = args.src
    # Validate
    valid = []
    for sid in source_ids.split(','):
        sid = sid.strip()
        if sid in ALL_SOURCES:
            valid.append(sid)
        else:
            print(f"未知源: {sid}", file=sys.stderr)

    if not valid:
        print(f"可用源: {', '.join(ALL_SOURCES.keys())}", file=sys.stderr)
        return

    items = fetch_news(sources=','.join(valid), keyword=args.keyword,
                       limit=args.limit, deep=args.deep, translate=args.translate)
    if not items:
        print("暂无数据")
        return
    if args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
    else:
        print(format_news(items, "自定义源", summary_len=args.detail))


def cmd_all(args):
    """Fetch from ALL sources"""
    all_ids = list(ALL_SOURCES.keys())
    items = fetch_news(sources=','.join(all_ids), keyword=args.keyword,
                       limit=args.limit, deep=args.deep, translate=args.translate)
    if not items:
        print("暂无数据")
        return
    if args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
    else:
        print(format_news(items, "全网扫描", summary_len=args.detail))


def cmd_sources(args):
    """List all sources and categories"""
    print("📡 新闻分类:\n")
    for cat_id, cat_info in CATEGORIES.items():
        source_names = []
        for sid in cat_info["sources"]:
            if sid in ALL_SOURCES:
                source_names.append(ALL_SOURCES[sid]["name"])
        print(f"  {cat_info['name']} ({cat_id}): {', '.join(source_names)}")
    print(f"\n📡 全部源 (共 {len(ALL_SOURCES)} 个):\n")
    for sid, src in ALL_SOURCES.items():
        req = " 📦" if src["type"] == "web" and not HAS_BS4 else ""
        print(f"  {sid:25s} {src['name']:20s} [{src['type']}]{req}")
    if not HAS_BS4:
        print("\n  ⚠️  安装 requests + beautifulsoup4 可解锁 web 源:")
        print("     pip install requests beautifulsoup4")
    print()


def cmd_menu(args):
    """Display interactive menu from templates.md"""
    import os
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates.md")
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print("templates.md 不存在")


def main():
    parser = argparse.ArgumentParser(
        description='📰 统一新闻聚合器 — RSS + Web Scraping + API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s hot                             综合资讯
  %(prog)s category --cat ai                AI 技术新闻
  %(prog)s category --cat tech              科技新闻
  %(prog)s category --cat finance           财经新闻
  %(prog)s source --src hackernews          单个源
  %(prog)s source --src github,weibo        多个源
  %(prog)s all                              全网扫描
  %(prog)s hot --keyword AI,GPT             关键词过滤
  %(prog)s hot --deep                       深度抓取正文
  %(prog)s sources                          查看所有源
  %(prog)s menu                             交互菜单
""")
    sub = parser.add_subparsers(dest='command', help='命令')

    # hot
    hp = sub.add_parser('hot', help='综合资讯')
    hp.add_argument('--keyword', '-k', help='关键词 (逗号分隔)')
    hp.add_argument('--limit', '-n', type=int, default=10)
    hp.add_argument('--detail', '-d', type=int, default=100, help='摘要长度 (0=不显示, -1=全文)')
    hp.add_argument('--deep', action='store_true', help='深度抓取正文')
    hp.add_argument('--translate', action='store_true', help='自动翻译英文内容为中文')
    hp.add_argument('--json', action='store_true', help='JSON 输出')

    # category
    cp = sub.add_parser('category', help='按分类获取')
    cp.add_argument('--cat', '-c', required=True, choices=list(CATEGORIES.keys()), help='分类')
    cp.add_argument('--keyword', '-k', help='关键词')
    cp.add_argument('--limit', '-n', type=int, default=10)
    cp.add_argument('--detail', '-d', type=int, default=100)
    cp.add_argument('--deep', action='store_true')
    cp.add_argument('--translate', action='store_true', help='自动翻译英文内容为中文')
    cp.add_argument('--json', action='store_true')

    # source
    sp = sub.add_parser('source', help='指定源')
    sp.add_argument('--src', '-s', required=True, help='源 ID (逗号分隔)')
    sp.add_argument('--keyword', '-k', help='关键词')
    sp.add_argument('--limit', '-n', type=int, default=10)
    sp.add_argument('--detail', '-d', type=int, default=100)
    sp.add_argument('--deep', action='store_true')
    sp.add_argument('--translate', action='store_true', help='自动翻译英文内容为中文')
    sp.add_argument('--json', action='store_true')

    # all
    ap = sub.add_parser('all', help='全网扫描 (所有源)')
    ap.add_argument('--keyword', '-k', help='关键词')
    ap.add_argument('--limit', '-n', type=int, default=10)
    ap.add_argument('--detail', '-d', type=int, default=100)
    ap.add_argument('--deep', action='store_true')
    ap.add_argument('--translate', action='store_true', help='自动翻译英文内容为中文')
    ap.add_argument('--json', action='store_true')

    # sources
    sub.add_parser('sources', help='查看所有源和分类')

    # menu
    sub.add_parser('menu', help='交互菜单')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    dispatch = {
        'hot': cmd_hot, 'category': cmd_category, 'source': cmd_source,
        'all': cmd_all, 'sources': cmd_sources, 'menu': cmd_menu,
    }
    dispatch[args.command](args)


if __name__ == '__main__':
    main()
