#!/usr/bin/env python3
"""喝水提醒 — 发送飞书消息"""
import json
import os
import sys
import random
import urllib.request
from datetime import datetime

MSGS = [
    "💧 起来走走，喝杯水！已经坐了 1.5 小时了。",
    "🥤 该补水了！站起来活动一下筋骨。",
    "🚰 喝水时间到！眼睛也离开屏幕休息 30 秒。",
    "💦 补充水分！身体缺水大脑会变慢。",
    "🧊 去接杯水，顺便看看窗外。",
    "☕ 喝口水，别等渴了再喝。",
    "🍵 起来倒杯茶/水，拉伸一下。",
    "💙 水是生命之源，现在就去喝！",
]

EMOJIS = ["💧", "🥤", "🚰", "💦", "🧊", "☕", "🍵", "💙", "🌊", "🧋"]


def get_webhook_urls():
    multi = os.environ.get("FEISHU_WEBHOOK_URLS", "")
    if multi:
        return [u.strip() for u in multi.split(",") if u.strip()]
    single = os.environ.get("FEISHU_WEBHOOK_URL", "")
    if single:
        return [single.strip()]
    return []


def send_text(webhook_url, text):
    payload = {"msg_type": "text", "content": {"text": text}}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook_url, data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("StatusCode") == 0 or result.get("code") == 0
    except Exception as e:
        print(f"[water] 发送失败: {e}", file=sys.stderr)
        return False


def main():
    urls = get_webhook_urls()
    if not urls:
        print("[water] 未配置 Webhook URL，跳过", file=sys.stderr)
        sys.exit(0)

    now = datetime.now().strftime("%H:%M")
    emoji = random.choice(EMOJIS)
    msg = random.choice(MSGS)
    text = f"{emoji} {now} {msg}"

    for url in urls:
        ok = send_text(url, text)
        if ok:
            print(f"[water] 已发送: {text}", file=sys.stderr)
        else:
            print("[water] 发送失败", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
