"""
Topic configuration for Ben's personalized daily RSS feed.

Edit this file any time your interests shift — the next scheduled run
will pick up the changes automatically. No other files need to change
for a normal topic edit.

Each topic is a dict with:
  key         short internal id
  label       section heading shown in the daily digest
  feeds       list of source RSS feed URLs to pull from
  keywords    (optional) only include an article if its title+summary
              contains at least one of these (case-insensitive).
              Omit/empty = take everything the feed(s) publish.
  min_items / max_items   how many fresh items to pull per run (a random
              number in this range is chosen each day, which is part of
              why the feed doesn't feel identical day to day)

Ordering matters: CORE_TOPICS renders top-to-bottom in that order in the
digest, so your top-priority hobbies are listed first, general/local
sections last. (Rebalanced 2026-09-26 per feedback: hobbies — BJJ,
surfing, etc. — were getting crowded out by high-volume tech and local
feeds. Tech/local caps are now intentionally small.)
"""

FEED_TITLE = "Ben's Daily Digest"
FEED_LINK = "https://bbullock1984.github.io/personal-rss-feed/"
FEED_DESCRIPTION = (
    "A personalized daily digest across Ben's core interests, a light touch "
    "of local NYC-metro news, and a rotating set of adjacent topics."
)

# ---------------------------------------------------------------------------
# CORE TOPICS — things you're "definitely interested" in, covered every day.
# Hobby topics lead; broad/high-volume topics (tech) are deliberately capped
# low so they don't crowd out everything else.
# ---------------------------------------------------------------------------
CORE_TOPICS = [
    {
        "key": "bjj",
        "label": "BJJ & Grappling",
        "feeds": [
            "https://www.bjjee.com/feed/",
        ],
        "keywords": [],  # dedicated BJJ news site — take everything
        "min_items": 2, "max_items": 5,
    },
    {
        "key": "surfing",
        "label": "Surfing",
        "feeds": [
            "https://www.theinertia.com/feed/",
        ],
        "keywords": [],  # dedicated surf/outdoor site — take everything
        "min_items": 2, "max_items": 4,
    },
    {
        "key": "soccer",
        "label": "Soccer",
        "feeds": [
            "http://feeds.bbci.co.uk/sport/football/rss.xml",
            "https://www.espn.com/espn/rss/soccer/news",
            "https://www.skysports.com/rss/12040",
        ],
        "keywords": [
            "arsenal", "atletico madrid", "atlético madrid", "la liga",
            "champions league", "premier league", "new york red bulls",
            "griezmann",
        ],
        "min_items": 2, "max_items": 4,
    },
    {
        "key": "tennis",
        "label": "Tennis",
        "feeds": [
            "https://www.espn.com/espn/rss/tennis/news",
            "https://www.tennis.com/feed/",
        ],
        "keywords": [],  # dedicated tennis feeds — take everything
        "min_items": 1, "max_items": 3,
    },
    {
        "key": "jdm_cars",
        "label": "JDM & Cars",
        "feeds": [
            "https://www.motor1.com/rss/news/",
            "https://www.caranddriver.com/rss/all.xml/",
        ],
        "keywords": [
            "nissan gt-r", "nissan gtr", "nissan skyline", "jdm",
            "gt-r", "skyline",
        ],
        "min_items": 1, "max_items": 3,
    },
    {
        "key": "recipes",
        "label": "Quick Veg/Pescetarian Recipes",
        "feeds": [
            "https://www.budgetbytes.com/feed/",
            "https://minimalistbaker.com/feed/",
        ],
        "keywords": [
            "vegetarian", "pescetarian", "instant pot", "one pan",
            "one-pan", "one pot", "one-pot", "skillet", "sheet pan",
            "meatless", "vegan",
        ],
        "min_items": 1, "max_items": 3,
    },
    {
        "key": "fire",
        "label": "FI / Investing",
        "feeds": [
            "https://www.mrmoneymustache.com/feed/",
            "https://www.financialsamurai.com/feed/",
            "https://www.physicianonfire.com/feed/",
        ],
        "keywords": [],  # already FI-focused blogs — take everything, capped
        "min_items": 1, "max_items": 3,
    },
    {
        "key": "spotify_streaming",
        "label": "Streaming / Music Biz",
        "feeds": [
            "https://www.musicbusinessworldwide.com/feed/",
            "https://variety.com/v/music/feed/",
            "https://www.billboard.com/feed/",
        ],
        "keywords": [
            "spotify", "streaming", "subscri", "music industry",
            "apple music", "youtube music", "amazon music", "tidal",
        ],
        "min_items": 1, "max_items": 3,
    },
    {
        "key": "family_games",
        "label": "Family & Games",
        "feeds": [
            "https://www.polygon.com/rss/index.xml",
        ],
        "keywords": [
            "card game", "board game", "family game", "mobile game",
            "honor of kings", "party game",
        ],
        "min_items": 1, "max_items": 3,
    },
    {
        "key": "movies_tv",
        "label": "Movies & TV",
        "feeds": [
            "https://variety.com/v/film/feed/",
            "https://www.indiewire.com/feed/",
            "https://www.starwars.com/news/feed",
        ],
        "keywords": [
            "marvel", "star wars", "wes anderson", "christopher nolan",
            "streaming", "new series", "new season", "trailer",
            "all creatures great and small", "mobland",
        ],
        "min_items": 1, "max_items": 3,
    },
    {
        "key": "fatherhood",
        "label": "Fatherhood",
        "feeds": [
            "https://www.parents.com/feed",
        ],
        "keywords": [
            "dad", "father", "fatherhood", "parenting",
        ],
        "min_items": 1, "max_items": 2,
    },
    {
        "key": "date_night_activities",
        "label": "Date Night / Things To Do",
        "feeds": [
            "https://patch.com/new-jersey/montclair/rss",
            "https://gothamist.com/feed",
            "https://www.amny.com/feed/",
        ],
        "keywords": [
            "things to do", "date night", "weekend", "event",
            "restaurant", "day trip", "festival", "opening",
        ],
        "min_items": 1, "max_items": 2,
    },
    {
        # Intentionally small: this was crowding out hobby topics when it
        # took every TechCrunch/Verge/Ars Technica headline unfiltered.
        "key": "tech_ai",
        "label": "Tech & AI",
        "feeds": [
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml",
            "https://feeds.arstechnica.com/arstechnica/index",
        ],
        "keywords": [],  # general tech/AI news — take everything, but capped small
        "min_items": 1, "max_items": 2,
    },
]

# ---------------------------------------------------------------------------
# LOCAL TOPICS — a light touch of Montclair/Essex County + NYC metro news.
# Kept deliberately small (was previously the biggest single source of
# volume in the feed).
# ---------------------------------------------------------------------------
LOCAL_TOPICS = [
    {
        "key": "local_montclair",
        "label": "Montclair / Essex County NJ",
        "feeds": [
            "https://patch.com/new-jersey/montclair/rss",
        ],
        "keywords": [],
        "min_items": 1, "max_items": 2,
    },
    {
        "key": "local_nyc_metro",
        "label": "NYC Metro",
        "feeds": [
            "https://gothamist.com/feed",
            "https://www.amny.com/feed/",
            "https://www.nj.com/arc/outboundfeeds/rss/",
        ],
        "keywords": [],
        "min_items": 1, "max_items": 2,
    },
]

# ---------------------------------------------------------------------------
# DISCOVERY / "MAY INTEREST YOU" — a rotating pool. Each run, a random subset
# of these is chosen so the feed's "adjacent" coverage shifts day to day.
# Inferred from Ben's core list; safe to add/remove entries any time.
# ---------------------------------------------------------------------------
DISCOVERY_TOPICS = [
    {
        "key": "mma_general",
        "label": "MMA / UFC (general)",
        "feeds": ["https://www.mmafighting.com/rss/current"],
        "keywords": ["ufc", "mma"],
        "max_items": 2,
    },
    {
        "key": "motorsport",
        "label": "Motorsport",
        "feeds": ["https://www.motor1.com/rss/news/"],
        "keywords": ["formula 1", "f1", "drift", "drifting", "nascar", "motorsport"],
        "max_items": 2,
    },
    {
        "key": "world_football",
        "label": "World Football (beyond your clubs)",
        "feeds": ["http://feeds.bbci.co.uk/sport/football/rss.xml"],
        "keywords": ["world cup", "uefa", "international friendly", "transfer"],
        "max_items": 2,
    },
    {
        "key": "personal_finance_general",
        "label": "Personal Finance (broader)",
        "feeds": ["https://www.financialsamurai.com/feed/"],
        "keywords": ["real estate", "index fund", "retirement", "net worth"],
        "max_items": 2,
    },
    {
        "key": "podcasting",
        "label": "Podcasting Industry",
        "feeds": ["https://www.musicbusinessworldwide.com/feed/", "https://variety.com/v/music/feed/"],
        "keywords": ["podcast"],
        "max_items": 2,
    },
    {
        "key": "gadgets",
        "label": "Consumer Gadgets",
        "feeds": ["https://www.theverge.com/rss/index.xml"],
        "keywords": ["review", "hands-on", "gadget", "wearable", "smart home"],
        "max_items": 2,
    },
    {
        "key": "board_games",
        "label": "Board Games",
        "feeds": ["https://www.polygon.com/rss/index.xml"],
        "keywords": ["board game", "tabletop"],
        "max_items": 2,
    },
    {
        "key": "indie_film",
        "label": "Indie Film / Awards",
        "feeds": ["https://www.indiewire.com/feed/"],
        "keywords": [],
        "max_items": 2,
    },
    {
        "key": "nj_ny_culture",
        "label": "NJ/NY Food & Culture",
        "feeds": ["https://gothamist.com/feed"],
        "keywords": ["restaurant", "food", "museum", "art", "culture"],
        "max_items": 2,
    },
]

# How many discovery topics get pulled into any single day's digest.
DISCOVERY_TOPICS_PER_RUN = (2, 3)
