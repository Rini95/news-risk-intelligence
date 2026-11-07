"""
Merges the reviewer's decisions from data/labels/label_review.xlsx into
- data/labels/realworld_reviewed.csv (used by evaluate_realworld.py), and
- data/labels/gold_labels_reviewed.csv (used everywhere via config.GOLD_CSV).

Each row gets a label_status:
- verified   the reviewer accepted the draft label;
- corrected  the reviewer replaced it (Your event type / Your severity);
- excluded   the reviewer dropped the row (real-world sheet only);
- draft      no decision yet; the label is still Claude's draft.

Stops with a list of problems instead of writing a half-valid file.
"""
from datetime import date

import pandas as pd

from classify_risk import LEVELS, NO_EVENT, RISK_CATEGORY_MAP
from config import (GOLD_DRAFT_CSV, GOLD_REVIEWED_CSV, REALWORLD_DRAFT_CSV, REALWORLD_REVIEWED_CSV,
                    REVIEW_XLSX)
from make_review_workbook import REALWORLD_SHEET, SEED_SHEET, SHEETS

REVIEWER = "Rini"
LABEL_COLS = ["gold_event_type", "gold_risk_category", "gold_severity"]


def apply(draft, key, sheet, note_col, problems):
    review = pd.read_excel(REVIEW_XLSX, sheet_name=sheet, dtype=str).fillna("")
    review = review.set_index(key)[["Decision", "Your event type", "Your severity", "Your comment"]]
    review = review.apply(lambda col: col.str.strip())
    allowed = SHEETS[sheet][1]
    statuses = []
    for i, row in draft.iterrows():
        rid = str(row[key])
        r = review.loc[rid] if rid in review.index else None
        decision = r["Decision"].capitalize() if r is not None else ""
        status = {"Accept": "verified", "Correct": "corrected", "Exclude": "excluded", "": "draft"}.get(decision)
        if status is None or (decision and decision not in allowed):
            problems.append(f"{sheet} {rid}: Decision must be one of {', '.join(allowed)} (got '{decision}')")
            status = "draft"
        if status == "corrected":
            event, sev = r["Your event type"], r["Your severity"]
            if event == NO_EVENT:
                sev = sev or "None"
            if event not in RISK_CATEGORY_MAP:
                problems.append(f"{sheet} {rid}: Correct needs a valid 'Your event type' (got '{event}')")
            elif event == NO_EVENT and sev != "None":
                problems.append(f"{sheet} {rid}: No Risk Event must have severity None")
            elif event != NO_EVENT and sev not in LEVELS:
                problems.append(f"{sheet} {rid}: Correct needs 'Your severity' of {', '.join(LEVELS)}")
            else:
                draft.loc[i, LABEL_COLS] = [event, RISK_CATEGORY_MAP[event], sev]
        if r is not None and r["Your comment"]:
            draft.loc[i, note_col] = (row[note_col] + " | " if row[note_col] else "") + f"{REVIEWER}: {r['Your comment']}"
        statuses.append(status)
    draft["label_status"] = statuses
    draft["annotator"] = [f"{REVIEWER} (reviewed {date.today().isoformat()})" if s != "draft"
                          else "claude-draft (needs Rini's review)" for s in statuses]
    return draft


def main():
    problems = []
    real = apply(pd.read_csv(REALWORLD_DRAFT_CSV, keep_default_na=False), "case_id", REALWORLD_SHEET, "note", problems)
    seed = apply(pd.read_csv(GOLD_DRAFT_CSV, keep_default_na=False), "article_id", SEED_SHEET, "rationale", problems)
    if problems:
        raise SystemExit("Review not applied:\n  " + "\n  ".join(problems))
    real.to_csv(REALWORLD_REVIEWED_CSV, index=False)
    seed.to_csv(GOLD_REVIEWED_CSV, index=False)
    for name, df in [("real-world", real), ("seed", seed)]:
        print(f"{name}: {df['label_status'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
