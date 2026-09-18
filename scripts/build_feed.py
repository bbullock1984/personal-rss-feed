#!/usr/bin/env python3
"""
Builds docs/feed.xml from the topic config in topics.py.

Run by the daily GitHub Action (.github/workflows/daily-feed.yml), but
safe to run locally too: `python scripts/build_feed.py` from the repo root.

How "never repeats" works:
  - Every included headline's normalized title is recorded in
    data/history.json with the date it was shown.
  - Any headline whose normalized title was already shown in the last
    HISTORY_RETENTION_DAYS is skipped.
  - History older than that window is pruned automatically, so a topic
    that's been quiet for a while can resurface.

How "doesn't go too deep" works:
  - Each topic pulls a small, randomized number of items per run
    (see min_items/max_items in topics.py) — headlines + a short
    snippet + link, never full article text.

How "dynamic as interests shift" works:
  - Everything content-related lives in topics.py. Add, remove, or
    reweight a topic there and the very next run reflects it.
"""
import calendar
import hashlib
import json
import random
import re
import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

import feedparser
import requests

sys.path.insert(0, str(Path(__file__).parent))
from topics import CORE_TOPICS, DISCOVERY_TOPICS, LOCAL_TOPICS, FEED_TITLE, FEED_LINK, FEED_DESCRIPTION

REPO_ROOT = Path(__file__).parent.parent
HISTORY_PATH = REPO_ROOT / "data" / "history.json"
OUTPUT_PATH = REPO_ROOT / "docs" / "feed.xml"
HISTORY_RETENTION_DAYS = 30
MAX_TOTAL_ITEMS = 70
REQUEST_TIMEOUT = 12
DISCOVERY_TOPICS_PER_RUN = (2, 4)
USER_AGENT = (
    "Mozilla/5.0 (compatible; PersonalRSSBuilder/1.0; "
    "+https://github.com/bbullock1984/personal-rss-feed)"
)


def normalize_title(title):
    t = title.lower()
    t = re.sub(r"[^a-z0-9\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def load_history():
    if HISTORY_PATH.exists():
        try:
            return json.loads(HISTORY_PATH.read_text())
        except json.JSONDecodeError:
            print("  [warn] history.json unreadable, starting fresh", file=sys.stderr)
    return {}


def save_history(history):
    cutoff = datetime.now(timezone.utc) - timedelta(days=HISTORY_RETENTION_DAYS)
    pruned = {}
    for k, v in history.items():
        try:
            if datetime.fromisoformat(v) > cutoff:
                pruned[k] = v
        except ValueError:
            continue
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(pruned, indent=2, sort_keys=True))


def fetch_feed(url):
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
        return parsed.entries
    except Exception as e:
        print(f"  [warn] failed to fetch {url}: {e}", file=sys.stderr)
        return []


def entry_summary(entry):
    summary = entry.get("summary", "") or entry.get("description", "")
    summary = re.sub(r"<[^>]+>", "", summary)
    summary = re.sub(r"\s+", " ", summary).strip()
    if len(summary) > 280:
        summary = summary[:280].rsplit(" ", 1)[0] + "…"
    return summary


def entry_pubdate(entry):
    for key in ("published_parsed", "updated_parsed"):
        val = entry.get(key)
        if val:
            try:
                return datetime.fromtimestamp(calendar.timegm(val), tz=timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)


def matches_keywords(text, keywords):
    if not keywords:
        return True
    text_l = text.lower()
    return any(kw.lower() in text_l for kw in keywords)


def collect_topic_items(topic, history, seen_today, cap):
    collected = []
    for feed_url in topic["feeds"]:
        if len(collected) >= cap:
            break
        entries = fetch_feed(feed_url)
        for entry in entries:
            title = (entry.get("title") or "").strip()
            link = (entry.get("link") or "").strip()
            if not title or not link:
                continue
            summary = entry_summary(entry)
            haystack = f"{title} {summary}"
            if not matches_keywords(haystack, topic.get("keywords")):
                continue
            norm = normalize_title(title)
            if norm in seen_today or norm in history:
                continue
            collected.append({
                "title": title,
                "link": link,
                "summary": summary,
                "pubdate": entry_pubdate(entry),
                "category": topic["label"],
                "norm": norm,
            })
            seen_today.add(norm)
            if len(collected) >= cap:
                break
    return collected


def build_items(history):
    seen_today = set()
    items = []

    for topic in CORE_TOPICS:
        cap = random.randint(topic.get("min_items", 1), topic.get("max_items", 4))
        items.extend(collect_topic_items(topic, history, seen_today, cap))

    for topic in LOCAL_TOPICS:
        cap = random.randint(topic.get("min_items", 2), topic.get("max_items", 6))
        items.extend(collect_topic_items(topic, history, seen_today, cap))

    discovery_pool = list(DISCOVERY_TOPICS)
    random.shuffle(discovery_pool)
    n_discovery = random.randint(*DISCOVERY_TOPICS_PER_RUN)
    for topic in discovery_pool[:n_discovery]:
        cap = random.randint(1, topic.get("max_items", 2))
        items.extend(collect_topic_items(topic, history, seen_today, cap))

    random.shuffle(items)
    return items[:MAX_TOTAL_ITEMS]


def xml_escape(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def build_rss(items):
    now = datetime.now(timezone.utc)
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0"><channel>',
        f"<title>{xml_escape(FEED_TITLE)}</title>",
        f"<link>{xml_escape(FEED_LINK)}</link>",
        f"<description>{xml_escape(FEED_DESCRIPTION)}</description>",
        f"<lastBuildDate>{format_datetime(now)}</lastBuildDate>",
        "<language>en-us</language>",
    ]
    for it in sorted(items, key=lambda x: x["pubdate"], reverse=True):
        guid = hashlib.sha256(it["link"].encode()).hexdigest()
        pub = it["pubdate"]
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        title_line = f"[{it['category']}] {it['title']}"
        parts.append("<item>")
        parts.append(f"<title>{xml_escape(title_line)}</title>")
        parts.append(f"<link>{xml_escape(it['link'])}</link>")
        parts.append(f'<guid isPermaLink="false">{guid}</guid>')
        parts.append(f"<pubDate>{format_datetime(pub)}</pubDate>")
        parts.append(f"<category>{xml_escape(it['category'])}</category>")
        parts.append(f"<description>{xml_escape(it['summary'])}</description>")
        parts.append("</item>")
    parts.append("</channel></rss>")
    return "\n".join(parts)


def main():
    history = load_history()
    items = build_items(history)
    rss = build_rss(items)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(rss, encoding="utf-8")

    now_iso = datetime.now(timezone.utc).isoformat()
    for it in items:
        history[it["norm"]] = now_iso
    save_history(history)

    print(f"Wrote {len(items)} items to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
