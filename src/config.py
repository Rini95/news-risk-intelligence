"""Project paths, resolved relative to the repo so the pipeline runs from any checkout."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

RAW_CSV = DATA / "raw" / "articles_raw.csv"
CLEAN_CSV = DATA / "processed" / "articles_clean.csv"
ENTITIES_CSV = DATA / "processed" / "articles_entities.csv"
RISK_EVENTS_CSV = DATA / "processed" / "risk_events.csv"
FINAL_CSV = DATA / "processed" / "risk_events_final.csv"
# Seed-set labels: Claude's drafts, replaced by the reviewed copy once apply_review.py has run.
GOLD_DRAFT_CSV = DATA / "labels" / "gold_labels.csv"
GOLD_REVIEWED_CSV = DATA / "labels" / "gold_labels_reviewed.csv"
GOLD_CSV = GOLD_REVIEWED_CSV if GOLD_REVIEWED_CSV.exists() else GOLD_DRAFT_CSV

MODELS = ROOT / "models"
EVAL_DIR = ROOT / "outputs" / "evaluation"

# Articles older than this are flagged as out of the study window (e.g. article 14, 2018).
STUDY_WINDOW_START = "2025-01-01"

# Real-world evaluation set: Claude's draft labels, the review workbook (both sets), and the merged result.
REALWORLD_DRAFT_CSV = DATA / "labels" / "realworld_test.csv"
LINK_CHECK_CSV = DATA / "labels" / "link_check.csv"
REVIEW_XLSX = DATA / "labels" / "label_review.xlsx"
REALWORLD_REVIEWED_CSV = DATA / "labels" / "realworld_reviewed.csv"

# Output folders are not shipped with the code; create them so a fresh checkout runs.
for _d in (DATA / "processed", MODELS, EVAL_DIR):
    _d.mkdir(parents=True, exist_ok=True)
