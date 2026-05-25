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


def build_post_content(items, title, category="hot"):
    """构建飞书 post 富文本消息内容"""
    zh_cn_content = [[{"tag": "text", "text": f"{title}  ({len(items)} 条)\n\n"}]]

    for i, item in enumerate(items, 1):
        item_title = item.get("title", "")
        url = item.get("url", "")
        source = item.get("source", "")
        time_str = item.get("time", "")
        summary = item.get("summary", "")[:300]
        heat = item.get("heat", "")

        # 序号 + 标题 (带链接)
        line = []
        if url:
            line.append({"tag": "a", "text": f"{i}. {item_title}", "href": url})
        else:
            line.append({"tag": "text", "text": f"{i}. {item_title}"})

        zh_cn_content.append(line)

        # 元信息行
        meta_parts = []
        if source:
            meta_parts.append(f"📌 {source}")
        if time_str:
            meta_parts.append(time_str)
        if heat:
            meta_parts.append(f"🔥 {heat}")

        if meta_parts:
            zh_cn_content.append([{"tag": "text", "text": " | ".join(meta_parts)}])

        # 摘要
        if summary:
            zh_cn_content.append([{"tag": "text", "text": f"\n{summary[:200]}"}])

        # 分隔
        zh_cn_content.append([{"tag": "text", "text": "\n\n"}])

    # 添加 footer
    from datetime import datetime
    footer = f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')} · 由 GitHub Actions 自动推送"
    zh_cn_content.append([{"tag": "text", "text": footer}])

    # 检查总长度，超出则截断
    body = json.dumps(zh_cn_content, ensure_ascii=False)
    if len(body) > FEISHU_MSG_LIMIT:
        # 截取前 N 条
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
            "title": title,
            "content": zh_cn_content,
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
    parser.add_argument("json_file", help="news.py 输出的 JSON 文件路径")
    parser.add_argument("title", help="消息标题")
    parser.add_argument("--category", "-c", default="hot", help="新闻分类")
    args = parser.parse_args()

    urls = load_webhook_urls()
    if not urls:
        sys.exit(0)

    with open(args.json_file, "r", encoding="utf-8") as f:
        items = json.load(f)

    if not items:
        print(f"[feishu] 没有 {args.category} 新闻数据 — 跳过", file=sys.stderr)
        sys.exit(0)

    post_content = build_post_content(items, args.title, args.category)

    for url in urls:
        ok = send_feishu(url, post_content)
        if ok:
            print(f"[feishu] 发送成功 → {args.title} ({len(items)} 条)", file=sys.stderr)
        else:
            print(f"[feishu] 发送失败", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
