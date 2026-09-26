# Ben's Daily Digest (personal RSS feed)

A personalized, daily-refreshing RSS feed for Reeder, built from public
publisher RSS feeds — no scraping, no API keys, no ongoing cost.

**Feed URL (add this in Reeder):**
`https://bbullock1984.github.io/personal-rss-feed/feed.xml`

## Format

Each day's feed item is **one consolidated "digest" post** — styled like a
morning newsletter (colored masthead, a bulleted preview of what's inside,
then one section per topic with headline + short snippet + link) — not a
separate post per headline. The feed keeps roughly the last two weeks of
daily digests as separate items, so Reeder shows normal feed history; a
re-run on the same day updates that day's entry instead of duplicating it.

## How it works

- `scripts/topics.py` — your topic list: hobby/core interests (ordered by
  priority — they render top to bottom in that order), a light-touch local
  (Montclair/NYC metro) section, and a rotating "may interest you"
  discovery pool. This is the only file you (or Claude, on your behalf)
  need to edit to change what shows up or how much space it gets.
- `scripts/build_feed.py` — pulls fresh items per topic, filters by
  keyword where configured, skips anything shown in the last 30 days
  (`data/history.json`), renders the day's sections into one styled HTML
  digest, stores it in `data/digests.json` (keyed by date, ~14-day rolling
  window), and writes the whole thing out as `docs/feed.xml`.
- `.github/workflows/daily-feed.yml` — runs the build automatically once
  a day (10:00 UTC ≈ 6am ET) via GitHub Actions, and commits the updated
  files back to the repo.
- `docs/feed.xml` — served as a static file via GitHub Pages (Settings →
  Pages → Deploy from branch → `main` / `/docs`). This is the URL Reeder
  polls.

## Changing your interests

Edit `scripts/topics.py`:
- Add/remove a topic dict from `CORE_TOPICS`, `LOCAL_TOPICS`, or
  `DISCOVERY_TOPICS`. Order in `CORE_TOPICS` = order it renders in the
  digest, so put higher-priority hobbies first.
- `feeds`: source RSS URLs (needs to be real, publicly available feeds).
- `keywords`: only items whose title/summary contain one of these are
  kept. Leave empty to take everything from that topic's feed(s) —
  only do this for a feed that's already dedicated to the topic (a
  general/high-volume feed left unfiltered will crowd out everything
  else, which is what happened with Tech & AI and local news at first).
- `min_items`/`max_items` (or `max_items` alone for discovery topics):
  controls how much daily "real estate" a topic gets.

No terminal needed to make a change: on GitHub.com, open the file, click
the pencil (edit) icon, make your change, and commit directly to `main`.
The next scheduled run (or a manual one — see below) picks it up
automatically.

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
- `data/history.json` (headline-level dedupe) auto-prunes anything older
  than 30 days; `data/digests.json` (the daily posts themselves) auto-prunes
  anything older than 14 days. Neither needs manual resetting.
