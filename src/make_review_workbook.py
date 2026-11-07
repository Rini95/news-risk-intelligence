"""
Builds data/labels/label_review.xlsx, the workbook for the human label review.

Every label in the project was drafted with Claude: the 108 real-world headlines
(realworld_test.csv) and the 15 seed articles (gold_labels.csv). None of them is a
gold-standard annotation until a person has read the source and accepted or
corrected it. The workbook has one sheet per set, with the source link, the draft
label and yellow cells for the reviewer's decision. After review, run
apply_review.py (run_pipeline.sh does this) to merge the decisions.

Refuses to overwrite a workbook that already contains decisions unless --force.
"""
import argparse

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from classify_risk import LEVELS, RISK_CATEGORY_MAP
from config import GOLD_DRAFT_CSV, LINK_CHECK_CSV, RAW_CSV, REALWORLD_DRAFT_CSV, REVIEW_XLSX

SEVERITIES = list(LEVELS) + ["None"]
FONT = "Arial"
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
HEAD_FILL = PatternFill("solid", fgColor="1F3864")
THIN = Side(style="thin", color="BFBFBF")
INPUTS = [("Decision", 11), ("Your event type", 20), ("Your severity", 11), ("Your comment", 30)]

# Per sheet: (header, source column, width); reviewer input columns are appended.
REALWORLD_SHEET = "Real-world 108"
REALWORLD_COLUMNS = [
    ("case_id", "case_id", 8),
    ("Link", "url", 8),
    ("Headline", "title", 48),
    ("Publisher teaser", "teaser", 36),
    ("Lead (Claude summary of page)", "lead_summary", 40),
    ("Link check", "link_check", 14),
    ("Publisher", "publisher", 18),
    ("Date", "publication_date", 10),
    ("Page date (link check)", "page_date", 11),
    ("Text used", "text_used", 12),
    ("Draft event type", "gold_event_type", 20),
    ("Draft severity", "gold_severity", 10),
    ("Draft note", "draft_note", 30),
    ("Claude concern from page", "label_concern", 30),
]
SEED_SHEET = "Seed 15"
SEED_COLUMNS = [
    ("article_id", "article_id", 9),
    ("Link", "url", 8),
    ("Headline", "title", 40),
    ("Stored summary (what the pipeline reads)", "article_text", 60),
    ("Publisher", "publisher", 16),
    ("Date", "publication_date", 11),
    ("Draft event type", "gold_event_type", 20),
    ("Draft severity", "gold_severity", 10),
    ("Draft rationale", "rationale", 40),
]
SHEETS = {REALWORLD_SHEET: (REALWORLD_COLUMNS, ["Accept", "Correct", "Exclude"]),
          SEED_SHEET: (SEED_COLUMNS, ["Accept", "Correct"])}


def load_realworld():
    df = pd.read_csv(REALWORLD_DRAFT_CSV, keep_default_na=False)
    df["text_used"] = df["teaser"].map(lambda t: "headline + teaser" if t else "headline only")
    df["draft_note"] = [("AMBIGUOUS. " if a == "yes" else "") + n for a, n in zip(df["ambiguous"], df["note"])]
    for col in ["lead_summary", "label_concern", "link_check", "page_date"]:
        df[col] = ""
    if LINK_CHECK_CSV.exists():
        lc = pd.read_csv(LINK_CHECK_CSV, keep_default_na=False).set_index("case_id")
        for col in ["lead_summary", "label_concern", "page_date"]:
            df[col] = df["case_id"].map(lc[col]).fillna("")
        df["link_check"] = df["case_id"].map(
            lambda c: f"{lc.at[c, 'link_status']}, headline {lc.at[c, 'headline_matches']}" if c in lc.index else "")
    return df


def load_seed():
    raw = pd.read_csv(RAW_CSV, keep_default_na=False)
    gold = pd.read_csv(GOLD_DRAFT_CSV, keep_default_na=False)
    return raw.merge(gold, on="article_id")


def has_decisions(path):
    if not path.exists():
        return False
    wb = load_workbook(path)
    for name in SHEETS:
        if name in wb.sheetnames:
            ws = wb[name]
            col = [c.value for c in ws[1]].index("Decision") + 1
            if any(ws.cell(r, col).value for r in range(2, ws.max_row + 1)):
                return True
    return False


def style_header(ws, row, widths):
    for i, w in enumerate(widths, 1):
        cell = ws.cell(row, i)
        cell.font = Font(name=FONT, bold=True, color="FFFFFF")
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[get_column_letter(i)].width = w


def write_instructions(wb, n_real, n_seed):
    ws = wb.active
    ws.title = "Instructions"
    lines = [
        ("How to review the labels", True),
        ("", False),
        (f"All labels here were drafted with Claude: {n_real} real-world headlines and {n_seed} seed articles.", False),
        ("They are not gold-standard annotations until you have checked each one against its source.", False),
        ("Only edit the yellow columns: Decision, Your event type, Your severity, Your comment.", True),
        ("", False),
        ("For each row: open the Link, read the article, then set Decision.", False),
        ("  Accept   the draft event type and severity are right. Leave Your event type / Your severity empty.", False),
        ("  Correct  fill Your event type and Your severity (severity None for No Risk Event).", False),
        ("  Exclude  (real-world sheet only) broken link, off-topic, not GCC, outside the 2025+ window,", False),
        ("           or a duplicate. The row leaves the evaluation.", False),
        ("Rows left without a decision stay as drafts and are reported as such.", False),
        ("", False),
        ("Label rules are in labelling_guidelines.md: one label per article, the primary event, or No Risk Event", False),
        ("when the article reports nothing adverse or notable for a project or company.", False),
        ("Text used shows what the classifiers saw. 95 real-world rows are headline only: label what the headline", False),
        ("says, as the classifier would, and note in Your comment when the full article tells a different story.", False),
        ("Lead and Claude concern are Claude's reading of each page, a prompt for your check, not a second annotator.", False),
        ("Rows with a Claude concern are worth doing first (filter that column for non-blanks).", False),
        ("", False),
        ("When done: save this file in place and run  bash run_pipeline.sh", True),
        ("", False),
        ("Example of a corrected row (not part of the data):", True),
    ]
    for i, (text, bold) in enumerate(lines, 1):
        ws.cell(i, 1, text).font = Font(name=FONT, bold=bold, size=12 if i == 1 else 10)
    r = len(lines) + 1
    headers = [h for h, _, _ in REALWORLD_COLUMNS] + [h for h, _ in INPUTS]
    widths = [w for _, _, w in REALWORLD_COLUMNS] + [w for _, w in INPUTS]
    example = ["R999", "open", "Contractor walks off Riyadh tower site over unpaid invoices", "", "", "ok, headline yes",
               "Example Daily", "2026-09", "2026-09-14", "headline only", "No Risk Event", "None", "", "",
               "Correct", "Payment Risk", "High", "Unpaid invoices stopped work"]
    for i, h in enumerate(headers, 1):
        ws.cell(r, i, h)
        cell = ws.cell(r + 1, i, example[i - 1])
        cell.font = Font(name=FONT, size=10)
        if i > len(REALWORLD_COLUMNS):
            cell.fill = INPUT_FILL
    style_header(ws, r, widths)
    ws.column_dimensions["A"].width = 12


def write_sheet(wb, name, df):
    columns, decisions = SHEETS[name]
    ws = wb.create_sheet(name)
    headers = [h for h, _, _ in columns] + [h for h, _ in INPUTS]
    for i, h in enumerate(headers, 1):
        ws.cell(1, i, h)
    style_header(ws, 1, [w for _, _, w in columns] + [w for _, w in INPUTS])
    for r, rec in enumerate(df.to_dict("records"), 2):
        for i in range(1, len(headers) + 1):
            cell = ws.cell(r, i)
            cell.font = Font(name=FONT, size=10)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = Border(bottom=THIN)
            if i > len(columns):
                cell.fill = INPUT_FILL
                continue
            src = columns[i - 1][1]
            if src == "url":
                cell.value = "open"
                cell.hyperlink = rec["url"]
                cell.font = Font(name=FONT, size=10, color="0563C1", underline="single")
            else:
                cell.value = rec[src]
    ws.freeze_panes = "D2"
    last = len(df) + 1
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{last}"
    lists = wb["Lists"]
    for header, values in [("Decision", decisions), ("Your event type", list(RISK_CATEGORY_MAP)),
                           ("Your severity", SEVERITIES)]:
        # One list column per (sheet, field) so each sheet can offer its own decisions.
        col = lists.max_column + 1 if lists.max_row > 1 or lists["A1"].value else 1
        for j, v in enumerate(values, 1):
            lists.cell(j, col, v).font = Font(name=FONT, size=10)
        letter = get_column_letter(col)
        target = get_column_letter(headers.index(header) + 1)
        dv = DataValidation(type="list", formula1=f"=Lists!${letter}$1:${letter}${len(values)}", allow_blank=True)
        dv.add(f"{target}2:{target}{last}")
        ws.add_data_validation(dv)


def main():
    parser = argparse.ArgumentParser(description="Build the label review workbook.")
    parser.add_argument("--force", action="store_true", help="overwrite a workbook that already has decisions")
    args = parser.parse_args()
    if has_decisions(REVIEW_XLSX) and not args.force:
        raise SystemExit(f"{REVIEW_XLSX.name} already has review decisions; not overwriting (use --force).")
    real, seed = load_realworld(), load_seed()
    wb = Workbook()
    write_instructions(wb, len(real), len(seed))
    wb.create_sheet("Lists").sheet_state = "hidden"
    write_sheet(wb, REALWORLD_SHEET, real)
    write_sheet(wb, SEED_SHEET, seed)
    wb.move_sheet("Lists", offset=2)
    wb.active = 0
    wb.save(REVIEW_XLSX)
    print(f"{len(real)} real-world + {len(seed)} seed rows -> {REVIEW_XLSX.name} "
          f"(link check {'merged' if LINK_CHECK_CSV.exists() else 'not found'})")


if __name__ == "__main__":
    main()
