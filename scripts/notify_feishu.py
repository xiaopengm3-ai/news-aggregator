#!/usr/bin/env python3
"""
飞书 Webhook 通知脚本
读取 news.py 输出的 JSON，格式化为飞书富文本消息并发送

使用方式:
  python scripts/notify_feishu.py /tmp/hot_news.json "📰 综合资讯" --category hot

环境变量:
  FEISHU_WEBHOOK_URL  飞书自定义机器人 Webhook 地址（必填）
  FEISHU_WEBHOOK_URLS 多个 Webhook URL，逗号分隔（可选，优先级高于单个 URL）
"""
import json
import os
import sys
import argparse
import urllib.request

FEISHU_MSG_LIMIT = 20000  # 飞书消息单条上限字符数


def load_webhook_urls():
    """从环境变量加载 Webhook URL 列表"""
    multi = os.environ.get("FEISHU_WEBHOOK_URLS", "")
    if multi:
        return [u.strip() for u in multi.split(",") if u.strip()]

    single = os.environ.get("FEISHU_WEBHOOK_URL", "")
    if single:
        return [single.strip()]

    print("[feishu] FEISHU_WEBHOOK_URL 或 FEISHU_WEBHOOK_URLS 未设置 — 跳过发送", file=sys.stderr)
    return []


def _build_section(items, emoji, title):
    """构建单个新闻板块的富文本内容片段"""
    blocks = [[{"tag": "text", "text": f"{emoji} {title}（{len(items)} 条）\n"}]]

    for i, item in enumerate(items, 1):
        item_title = item.get("title", "")
        url = item.get("url", "")
        source = item.get("source", "")
        time_str = item.get("time", "")
        summary = item.get("summary", "")[:300]
        heat = item.get("heat", "")

        if url:
            blocks.append([{"tag": "a", "text": f"  {i}. {item_title}", "href": url}])
        else:
            blocks.append([{"tag": "text", "text": f"  {i}. {item_title}"}])

        meta_parts = []
        if source:
            meta_parts.append(source)
        if time_str:
            meta_parts.append(time_str)
        if heat:
            meta_parts.append(heat)
        if meta_parts:
            blocks.append([{"tag": "text", "text": f"     {' · '.join(meta_parts)}"}])

        blocks.append([{"tag": "text", "text": "\n"}])

    return blocks


def build_combined_post(sections, report_title="📰 每日早报"):
    """将多个新闻板块合并为一条飞书 post 消息"""
    zh_cn_content = [[{"tag": "text", "text": f"{report_title}\n"}]]
    total = sum(len(items) for items, _, _ in sections)
    zh_cn_content.append([{"tag": "text", "text": f"━━━━ 共 {total} 条新闻 ━━━━\n\n"}])

    for items, emoji, title in sections:
        if not items:
            continue
        zh_cn_content.extend(_build_section(items, emoji, title))
        zh_cn_content.append([{"tag": "text", "text": "\n"}])

    from datetime import datetime
    footer = f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')} · 由 GitHub Actions 自动推送"
    zh_cn_content.append([{"tag": "text", "text": footer}])

    body = json.dumps(zh_cn_content, ensure_ascii=False)
    if len(body) > FEISHU_MSG_LIMIT:
        truncated = []
        char_count = 0
        for block in zh_cn_content:
            block_str = json.dumps(block, ensure_ascii=False)
            if char_count + len(block_str) > FEISHU_MSG_LIMIT - 200:
                truncated.append([{"tag": "text", "text": "\n... 内容过长已截断"}])
                break
            truncated.append(block)
            char_count += len(block_str)
        zh_cn_content = truncated

    return {
        "zh_cn": {
            "title": report_title,
            "content": zh_cn_content,
        }
    }


def build_post_content(items, title, category="hot"):
    """构建飞书 post 富文本消息内容（单一类别，保留兼容）"""
    emoji = title.split(" ", 1)[0] if " " in title else "📌"
    clean_title = title.split(" ", 1)[1] if " " in title else title
    blocks = _build_section(items, emoji, clean_title)
    return {
        "zh_cn": {
            "title": clean_title,
            "content": blocks,
        }
    }


def send_feishu(webhook_url, post_content):
    """发送飞书 post 消息"""
    payload = {
        "msg_type": "post",
        "content": {"post": post_content},
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("StatusCode") == 0 or result.get("code") == 0
    except Exception as e:
        print(f"[feishu] 发送失败: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="飞书通知脚本")
    parser.add_argument("args", nargs="*", help="JSON 文件路径 + 标题 (成对使用)")
    parser.add_argument("--combined", action="store_true", help="合并模式：多个 (json_file title) 对合并为一条消息")
    parser.add_argument("--category", "-c", default="hot", help="新闻分类 (单文件模式)")

    opts = parser.parse_args()

    urls = load_webhook_urls()
    if not urls:
        sys.exit(0)

    if opts.combined:
        # combined mode: args are pairs of (json_file, title)
        if len(opts.args) % 2 != 0:
            print("[feishu] --combined 需要偶数个参数: json_file title ...", file=sys.stderr)
            sys.exit(1)

        sections = []
        for i in range(0, len(opts.args), 2):
            json_file = opts.args[i]
            title = opts.args[i + 1]
            emoji = title.split(" ", 1)[0]
            clean_title = title.split(" ", 1)[1] if " " in title else title

            with open(json_file, "r", encoding="utf-8") as f:
                items = json.load(f)
            if items:
                sections.append((items, emoji, clean_title))
                print(f"[feishu] 加载 {clean_title}: {len(items)} 条", file=sys.stderr)

        if not sections:
            print("[feishu] 没有新闻数据 — 跳过", file=sys.stderr)
            sys.exit(0)

        post_content = build_combined_post(sections)

        for url in urls:
            ok = send_feishu(url, post_content)
            if ok:
                total = sum(len(s[0]) for s in sections)
                print(f"[feishu] 合并发送成功 → 共 {total} 条 ({len(sections)} 个板块)", file=sys.stderr)
            else:
                print("[feishu] 发送失败", file=sys.stderr)
                sys.exit(1)
        return

    # single-file mode (backward compatible)
    if len(opts.args) < 2:
        parser.error("单文件模式需要 json_file 和 title 参数")
    json_file = opts.args[0]
    title = opts.args[1]

    with open(json_file, "r", encoding="utf-8") as f:
        items = json.load(f)

    if not items:
        print(f"[feishu] 没有 {opts.category} 新闻数据 — 跳过", file=sys.stderr)
        sys.exit(0)

    post_content = build_post_content(items, title, opts.category)

    for url in urls:
        ok = send_feishu(url, post_content)
        if ok:
            print(f"[feishu] 发送成功 → {title} ({len(items)} 条)", file=sys.stderr)
        else:
            print("[feishu] 发送失败", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
