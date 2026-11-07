"""
RSS collector: pulls GCC construction headlines from RSS feeds into data/raw/rss_articles.csv.

Each run fetches every feed in FEEDS, keeps items that mention a GCC location and a
construction term, drops items outside the study window, de-duplicates against what
is already stored (by URL and by normalised headline), and appends the rest.
Only the headline, the feed's own short description (HTML stripped, truncated),
the link, publisher and date are stored, never the full article text.

Usage:
    python collect_rss.py                       # all feeds in FEEDS
    python collect_rss.py --feed URL [--feed URL ...]
    python collect_rss.py --feed file:///path/to/sample.xml   # offline test

Status: written and tested against a saved sample feed (tests/sample_feed.xml).
It could not be run against live feeds from the environment it was built in
(outbound access to news sites was blocked), so the feed URLs below must be
checked on a normal internet connection before relying on them.
"""
import argparse
import csv
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from config import DATA, STUDY_WINDOW_START

RSS_CSV = DATA / "raw" / "rss_articles.csv"
COLUMNS = ["title", "teaser", "publisher", "url", "publication_date", "collected_date", "feed"]

# Google News search feeds work for any query; publisher feeds are listed where known.
GNEWS = "https://news.google.com/rss/search?hl=en-US&gl=US&ceid=US:en&q="
FEEDS = [
    GNEWS + "Saudi+construction+project",
    GNEWS + "UAE+construction+contract",
    GNEWS + "Qatar+OR+Kuwait+OR+Oman+OR+Bahrain+construction+project",
    GNEWS + "NEOM+OR+Qiddiya+OR+%22Red+Sea+Global%22+OR+Diriyah",
    GNEWS + "GCC+contractor+delay+OR+terminated+OR+payment",
    "https://www.constructionweekonline.com/feed",
    "https://www.zawya.com/sitemaps/en/rss",
]

GCC_TERMS = ["saudi", "riyadh", "jeddah", "makkah", "neom", "qiddiya", "diriyah", "uae", "dubai", "abu dhabi",
             "sharjah", "qatar", "doha", "kuwait", "oman", "muscat", "bahrain", "gcc", "gulf", "red sea", "trojena"]
CONSTRUCTION_TERMS = ["construct", "contract", "project", "infrastructure", "developer", "tower", "metro", "rail",
                      "epc", "tender", "real estate", "giga", "building", "airport", "stadium", "housing"]
TEASER_CHARS = 300


def normalise_title(title: str) -> str:
    # Google News appends " - Publisher"; strip it so the same story from two feeds matches.
    title = re.sub(r"\s+-\s+[^-]+$", "", title)
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html.unescape(text or ""))
    return re.sub(r"\s+", " ", text).strip()


def is_relevant(title: str, teaser: str) -> bool:
    text = f"{title} {teaser}".lower()
    return any(t in text for t in GCC_TERMS) and any(t in text for t in CONSTRUCTION_TERMS)


def parse_date(value: str):
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc)
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            return None


def fetch_items(feed_url: str):
    req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0 (capstone research collector)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        root = ET.fromstring(resp.read())
    atom = "{http://www.w3.org/2005/Atom}"
    for item in root.iter("item"):  # RSS 2.0
        source = item.find("source")
        yield {
            "title": strip_html(item.findtext("title")),
            "teaser": strip_html(item.findtext("description"))[:TEASER_CHARS],
            "url": (item.findtext("link") or "").strip(),
            "publisher": source.text.strip() if source is not None and source.text else "",
            "date": parse_date(item.findtext("pubDate")),
        }
    for entry in root.iter(f"{atom}entry"):  # Atom
        link = entry.find(f"{atom}link")
        yield {
            "title": strip_html(entry.findtext(f"{atom}title")),
            "teaser": strip_html(entry.findtext(f"{atom}summary"))[:TEASER_CHARS],
            "url": link.get("href", "") if link is not None else "",
            "publisher": "",
            "date": parse_date(entry.findtext(f"{atom}updated") or entry.findtext(f"{atom}published")),
        }


def load_existing():
    if not RSS_CSV.exists():
        return [], set(), set()
    with open(RSS_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows, {r["url"] for r in rows}, {normalise_title(r["title"]) for r in rows}


def collect(feeds):
    rows, seen_urls, seen_titles = load_existing()
    window_start = datetime.fromisoformat(STUDY_WINDOW_START).replace(tzinfo=timezone.utc)
    today = datetime.now(timezone.utc).date().isoformat()
    stats = {"fetched": 0, "irrelevant": 0, "out_of_window": 0, "duplicate": 0, "added": 0, "failed_feeds": 0}
    for feed in feeds:
        try:
            items = list(fetch_items(feed))
        except Exception as exc:  # one bad feed must not stop the run
            stats["failed_feeds"] += 1
            print(f"  ! {feed}: {exc}")
            continue
        for it in items:
            stats["fetched"] += 1
            key = normalise_title(it["title"])
            if not it["title"] or not is_relevant(it["title"], it["teaser"]):
                stats["irrelevant"] += 1
            elif it["date"] is not None and it["date"] < window_start:
                stats["out_of_window"] += 1
            elif it["url"] in seen_urls or key in seen_titles:
                stats["duplicate"] += 1
            else:
                seen_urls.add(it["url"])
                seen_titles.add(key)
                publisher = it["publisher"]
                title = it["title"]
                m = re.search(r"\s+-\s+([^-]+)$", title)
                # Google News appends " - Publisher" to every headline.
                if m and ("news.google." in feed or m.group(1).strip() == publisher):
                    publisher, title = publisher or m.group(1).strip(), title[: m.start()]
                rows.append({"title": title, "teaser": it["teaser"], "publisher": publisher, "url": it["url"],
                             "publication_date": it["date"].date().isoformat() if it["date"] else "",
                             "collected_date": today, "feed": feed})
                stats["added"] += 1
    RSS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(RSS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return stats, len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--feed", action="append", help="feed URL (repeatable); defaults to FEEDS")
    args = parser.parse_args()
    stats, total = collect(args.feed or FEEDS)
    print(f"{stats} -> {total} articles in {RSS_CSV.name}")
