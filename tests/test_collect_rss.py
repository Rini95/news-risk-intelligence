"""Offline test of the RSS collector: python tests/test_collect_rss.py"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import collect_rss  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    collect_rss.RSS_CSV = Path(tmp) / "rss_articles.csv"
    feed = (ROOT / "tests" / "sample_feed.xml").as_uri()
    stats, total = collect_rss.collect([feed])
    assert stats == {"fetched": 5, "irrelevant": 1, "out_of_window": 1, "duplicate": 1, "added": 2,
                     "failed_feeds": 0}, stats
    rows = collect_rss.load_existing()[0]
    assert rows[0]["title"] == "Neom terminates $5bn Trojena dams contract with Webuild"
    assert rows[0]["publisher"] == "MEED" and rows[0]["teaser"] == "Neom terminates $5bn Trojena dams contract"
    # A second run adds nothing: everything is already stored.
    assert collect_rss.collect([feed])[0]["added"] == 0
print("collect_rss: all checks passed")
