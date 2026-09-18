# Ben's Daily Digest (personal RSS feed)

A personalized, daily-refreshing RSS feed for Reeder, built from public
publisher RSS feeds — no scraping, no API keys, no ongoing cost.

**Feed URL (add this in Reeder):**
`https://bbullock1984.github.io/personal-rss-feed/feed.xml`

## How it works

- `scripts/topics.py` — your topic list: core interests, heavily-weighted
  local (Montclair/NYC metro) topics, and a rotating "may interest you"
  discovery pool. This is the only file you (or Claude, on your behalf)
  need to edit to change what shows up.
- `scripts/build_feed.py` — pulls fresh items from each topic's source
  feeds, filters by keyword where configured, skips anything shown in the
  last 30 days (`data/history.json`), caps how much space any one topic
  takes up, and writes `docs/feed.xml`.
- `.github/workflows/daily-feed.yml` — runs the build automatically once
  a day (10:00 UTC ≈ 6am ET) via GitHub Actions, and commits the updated
  feed back to the repo.
- `docs/feed.xml` — served as a static file via GitHub Pages (Settings →
  Pages → Deploy from branch → `main` / `/docs`). This is the URL Reeder
  polls.

## Changing your interests

Edit `scripts/topics.py`:
- Add/remove a topic dict from `CORE_TOPICS`, `LOCAL_TOPICS`, or
  `DISCOVERY_TOPICS`.
- `feeds`: source RSS URLs (needs to be real, publicly available feeds).
- `keywords`: only items whose title/summary contain one of these are
  kept. Leave empty to take everything from that topic's feed(s).
- `min_items`/`max_items` (or `max_items` alone for discovery topics):
  controls how much daily "real estate" a topic gets.

Commit the change (or ask Claude to do it for you) — the next scheduled
run picks it up automatically, no other changes needed.

## Running it manually

From the "Actions" tab on GitHub, choose "Build daily RSS feed" →
"Run workflow" to trigger an immediate rebuild instead of waiting for
the schedule.

You can also run it locally:
```
pip install -r requirements.txt
python scripts/build_feed.py
```

## Maintenance notes

- Source feed URLs occasionally change or go away. If a topic looks thin
  for a while, check the Action's run log (Actions tab → latest run →
  "Build feed" step) for `[warn] failed to fetch ...` lines, and swap in
  a replacement feed URL in `topics.py`.
- History (`data/history.json`) auto-prunes anything older than 30 days,
  so a topic that's been quiet can resurface later without needing a
  reset.
