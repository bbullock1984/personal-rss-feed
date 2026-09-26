#!/usr/bin/env python3
"""
Builds docs/feed.xml from the topic config in topics.py.

Run by the daily GitHub Action (.github/workflows/daily-feed.yml), but
safe to run locally too: `python scripts/build_feed.py` from the repo root.

Format: ONE RSS item per day — a single consolidated "digest" post with a
Morning-Brew-style HTML layout (masthead, a bulleted "in today's digest"
preview, then one section per topic with headline+link+snippet cards).
This intentionally replaces an earlier version that emitted one RSS item
per headline, which fragmented into dozens of separate posts in Reeder.

How "never repeats" works:
  - Every included headline's normalized title is recorded in
    data/history.json with the date it was shown.
  - Any headline whose normalized title was already shown in the last
    HISTORY_RETENTION_DAYS is skipped.
  - History older than that window is pruned automatically, so a topic
    that's been quiet for a while can resurface.

How "one story, refreshed daily, with real history" works:
  - Each day's full digest (title + teaser + rendered HTML) is saved to
    data/digests.json, keyed by date. Re-running on the same day
    overwrites that day's entry rather than duplicating it.
  - Entries older than DIGEST_RETENTION_DAYS are pruned.
  - docs/feed.xml is regenerated from that store every run: one <item>
    per retained day, newest first — so Reeder shows a normal-looking
    feed history instead of a single ever-changing post.

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
from topics import (
    CORE_TOPICS, DISCOVERY_TOPICS, LOCAL_TOPICS, DISCOVERY_TOPICS_PER_RUN,
    FEED_TITLE, FEED_LINK, FEED_DESCRIPTION,
)

REPO_ROOT = Path(__file__).parent.parent
HISTORY_PATH = REPO_ROOT / "data" / "history.json"
DIGESTS_PATH = REPO_ROOT / "data" / "digests.json"
OUTPUT_PATH = REPO_ROOT / "docs" / "feed.xml"
HISTORY_RETENTION_DAYS = 30
DIGEST_RETENTION_DAYS = 14
REQUEST_TIMEOUT = 12
USER_AGENT = (
    "Mozilla/5.0 (compatible; PersonalRSSBuilder/1.0; "
    "+https://github.com/bbullock1984/personal-rss-feed)"
)

# Brand colors for the digest template (not tied to any third-party brand).
ACCENT = "#3B6FE0"
ACCENT_LIGHT = "#EAF0FE"
TEXT_DARK = "#111827"
TEXT_MUTED = "#6B7280"
TEXT_FOOTER = "#9CA3AF"
BORDER = "#E5E7EB"


def normalize_title(title):
    t = title.lower()
    t = re.sub(r"[^a-z0-9\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def load_json(path):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            print(f"  [warn] {path} unreadable, starting fresh", file=sys.stderr)
    return {}


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True))


def prune_history(history):
    cutoff = datetime.now(timezone.utc) - timedelta(days=HISTORY_RETENTION_DAYS)
    pruned = {}
    for k, v in history.items():
        try:
            if datetime.fromisoformat(v) > cutoff:
                pruned[k] = v
        except ValueError:
            continue
    return pruned


def prune_digests(digests):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=DIGEST_RETENTION_DAYS)).date()
    pruned = {}
    for date_iso, entry in digests.items():
        try:
            if datetime.fromisoformat(date_iso).date() >= cutoff:
                pruned[date_iso] = entry
        except ValueError:
            continue
    return pruned


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
    if len(summary) > 200:
        summary = summary[:200].rsplit(" ", 1)[0] + "…"
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
                "norm": norm,
            })
            seen_today.add(norm)
            if len(collected) >= cap:
                break
    return collected


def build_sections(history):
    """Returns an ordered list of {label, items} dicts, skipping empty
    sections, in the order hobbies -> general -> local -> discovery."""
    seen_today = set()
    sections = []

    for topic in CORE_TOPICS:
        cap = random.randint(topic.get("min_items", 1), topic.get("max_items", 3))
        items = collect_topic_items(topic, history, seen_today, cap)
        if items:
            sections.append({"label": topic["label"], "items": items})

    for topic in LOCAL_TOPICS:
        cap = random.randint(topic.get("min_items", 1), topic.get("max_items", 2))
        items = collect_topic_items(topic, history, seen_today, cap)
        if items:
            sections.append({"label": topic["label"], "items": items})

    discovery_pool = list(DISCOVERY_TOPICS)
    random.shuffle(discovery_pool)
    n_discovery = random.randint(*DISCOVERY_TOPICS_PER_RUN)
    for topic in discovery_pool[:n_discovery]:
        cap = random.randint(1, topic.get("max_items", 2))
        items = collect_topic_items(topic, history, seen_today, cap)
        if items:
            sections.append({"label": f"You Might Also Like: {topic['label']}", "items": items})

    return sections


def html_escape(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_digest_html(sections, date_label):
    """Renders the day's sections into a single self-contained, inline-
    styled HTML document (Morning-Brew-inspired layout: colored masthead,
    bold greeting, a bulleted preview of what's inside, then one card
    per headline grouped under a section eyebrow label)."""
    parts = []
    parts.append(
        f'<div style="max-width:640px;margin:0 auto;font-family:-apple-system,'
        f'BlinkMacSystemFont,Helvetica,Arial,sans-serif;background:#ffffff;'
        f'border:1px solid {BORDER};border-radius:12px;overflow:hidden;">'
    )
    # Masthead
    parts.append(
        f'<div style="background:{ACCENT};padding:28px 24px;text-align:center;">'
        f'<div style="color:#ffffff;font-size:22px;font-weight:800;'
        f'letter-spacing:0.5px;">{html_escape(FEED_TITLE.upper())}</div>'
        f'<div style="color:{ACCENT_LIGHT};font-size:13px;margin-top:6px;">'
        f'{html_escape(date_label)}</div></div>'
    )
    # Body
    parts.append('<div style="padding:24px;">')
    parts.append(
        f'<p style="font-size:15px;color:{TEXT_DARK};line-height:1.5;margin:0 0 16px 0;">'
        f'<strong>Good morning, Ben.</strong> Here’s what’s happening '
        f'across your interests today.</p>'
    )
    if sections:
        parts.append(
            f'<p style="font-size:14px;color:{TEXT_DARK};margin:0 0 4px 0;">'
            f'<strong>In today’s digest:</strong></p>'
        )
        parts.append(
            f'<ul style="font-size:14px;color:{TEXT_MUTED};line-height:1.8;'
            f'padding-left:20px;margin:0 0 20px 0;">'
        )
        for section in sections:
            parts.append(f'<li>{html_escape(section["label"])}</li>')
        parts.append('</ul>')
        parts.append(f'<hr style="border:none;border-top:1px solid {BORDER};margin:0 0 20px 0;">')

        for i, section in enumerate(sections):
            parts.append('<div style="margin-bottom:6px;">')
            parts.append(
                f'<div style="color:{ACCENT};font-size:12px;font-weight:700;'
                f'letter-spacing:0.8px;text-transform:uppercase;margin-bottom:10px;">'
                f'{html_escape(section["label"])}</div>'
            )
            for item in section["items"]:
                parts.append('<div style="margin-bottom:14px;">')
                parts.append(
                    f'<a href="{html_escape(item["link"])}" style="font-size:15px;'
                    f'font-weight:700;color:{TEXT_DARK};text-decoration:none;">'
                    f'{html_escape(item["title"])}</a>'
                )
                if item["summary"]:
                    parts.append(
                        f'<p style="font-size:13px;color:{TEXT_MUTED};margin:4px 0 0 0;'
                        f'line-height:1.4;">{html_escape(item["summary"])}</p>'
                    )
                parts.append('</div>')
            parts.append('</div>')
            if i < len(sections) - 1:
                parts.append(f'<hr style="border:none;border-top:1px solid {BORDER};margin:8px 0 20px 0;">')
    else:
        parts.append(
            f'<p style="font-size:14px;color:{TEXT_MUTED};">No fresh headlines cleared '
            f'the dedupe filter today — check back tomorrow.</p>'
        )

    parts.append(
        f'<p style="font-size:12px;color:{TEXT_FOOTER};margin-top:24px;border-top:1px solid '
        f'{BORDER};padding-top:16px;">Built fresh every morning from your topics.py — '
        f'tell Claude anytime your interests shift.</p>'
    )
    parts.append('</div></div>')
    return "".join(parts)


def build_teaser(sections):
    if not sections:
        return "No fresh headlines today."
    bits = []
    for section in sections:
        if section["items"]:
            bits.append(f'{section["label"]}: {section["items"][0]["title"]}')
    return " • ".join(bits[:4])


def xml_escape(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def build_rss(digests):
    now = datetime.now(timezone.utc)
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">'
        '<channel>',
        f"<title>{xml_escape(FEED_TITLE)}</title>",
        f"<link>{xml_escape(FEED_LINK)}</link>",
        f"<description>{xml_escape(FEED_DESCRIPTION)}</description>",
        f"<lastBuildDate>{format_datetime(now)}</lastBuildDate>",
        "<language>en-us</language>",
    ]
    for date_iso in sorted(digests.keys(), reverse=True):
        entry = digests[date_iso]
        pub = datetime.fromisoformat(entry["pubdate_iso"])
        guid = hashlib.sha256(f"daily-digest-{date_iso}".encode()).hexdigest()
        parts.append("<item>")
        parts.append(f"<title>{xml_escape(entry['title'])}</title>")
        parts.append(f"<link>{xml_escape(FEED_LINK)}</link>")
        parts.append(f'<guid isPermaLink="false">{guid}</guid>')
        parts.append(f"<pubDate>{format_datetime(pub)}</pubDate>")
        parts.append(f"<description>{xml_escape(entry['teaser'])}</description>")
        parts.append(f"<content:encoded><![CDATA[{entry['html']}]]></content:encoded>")
        parts.append("</item>")
    parts.append("</channel></rss>")
    return "\n".join(parts)


def main():
    history = load_json(HISTORY_PATH)
    digests = load_json(DIGESTS_PATH)

    sections = build_sections(history)

    now = datetime.now(timezone.utc)
    date_iso = now.strftime("%Y-%m-%d")
    try:
        date_label = now.strftime("%B %-d, %Y")  # e.g. "September 26, 2026" (Linux/Mac)
    except ValueError:
        date_label = now.strftime("%B %d, %Y").replace(" 0", " ")  # Windows fallback

    html = build_digest_html(sections, date_label)
    teaser = build_teaser(sections)

    digests[date_iso] = {
        "title": f"{FEED_TITLE} — {date_label}",
        "pubdate_iso": now.isoformat(),
        "teaser": teaser,
        "html": html,
    }
    digests = prune_digests(digests)

    rss = build_rss(digests)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(rss, encoding="utf-8")

    for section in sections:
        for item in section["items"]:
            history[item["norm"]] = now.isoformat()
    history = prune_history(history)

    save_json(HISTORY_PATH, history)
    save_json(DIGESTS_PATH, digests)

    total_items = sum(len(s["items"]) for s in sections)
    print(f"Built digest for {date_iso}: {len(sections)} sections, {total_items} headlines.")
    print(f"Feed now holds {len(digests)} daily digest item(s).")


if __name__ == "__main__":
    main()
