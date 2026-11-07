"""
Rule-based event / risk / severity classifier (v2).

Error analysis of the Phase 1 rules (v1, kept in rules_v1.py) found three
structural problems rather than just missing keywords:

1. Only the article body was classified, never the headline. Article 1's body
   says "paused" and only its title says "suspended", so severity fell through
   to the default Low.
2. First-match-wins over a fixed keyword order. Article 7 (Hormuz shipping)
   matched "terminat" in "termination disputes" before reaching the supply-chain
   keywords; article 8 (permit enforcement) matched "delay" before
   "regulator"/"permit". Order cannot fix both at once.
3. Severity came from free-floating words, independent of the event, with Low
   as the fall-through, so any article with no listed word became Low.

v2 instead scores every event type (title hits count double), picks the highest
score with the priority order only breaking ties, uses patterns that exclude
known false triggers ("termination disputes", "delayed payment"), and derives
severity from the event type, adjusted by intensifiers and mitigators.
confidence_score is the winning share of all keyword evidence, a heuristic
rather than a calibrated probability.

An article with no keyword evidence is "No Risk Event" (risk category and
severity "None") rather than being forced into a category, so the pipeline can
reject irrelevant news and false positives can be measured. (This replaced the
v1 "Other" label, which was mapped to Market risk.)
"""
import re

import pandas as pd

from config import ENTITIES_CSV, RISK_EVENTS_CSV

TITLE_WEIGHT = 2

# Dict order is the tie-break priority.
EVENT_PATTERNS = {
    "Contract Cancellation": [r"\bcancel", r"\bterminat\w*(?! disputes)(?! claims)", r"\bbreakdown in\b", r"\bscrapped\b"],
    "Project Suspension": [r"\bsuspen", r"\bpaus", r"\bon hold\b", r"\breassess", r"\bre-?scop", r"\brecalibrat",
                           r"\bscal\w* ?-?back", r"\bhalt"],
    "Cost Overrun": [r"\bcost overrun", r"\bballoon", r"\bover budget\b", r"\bcost escalation\b", r"\bbudget blow"],
    "Regulatory Change": [r"\bregulat", r"\bpermit", r"\bcomplian", r"\bzoning\b", r"\benforcement\b", r"\blegislat",
                          r"\bnew law\b", r"\bdecree\b"],
    "Supply Chain Disruption": [r"\bsupply.?chain", r"\bshipping\b", r"\blead times?\b", r"\bshortage", r"\bdisrupt",
                                r"\bimported materials\b", r"\bmanufacturing base\b", r"\blogistic"],
    "Project Delay": [r"\bdelay(?!ed payment)(?!s? in payment)", r"\bpostpon", r"\bbehind schedule\b",
                      r"\bfell \w+ behind\b", r"\bextension of time\b", r"\bunrealistic\b", r"\bmissed (the )?deadline"],
    "Workforce Change": [r"\bworkforce\b", r"\bheadcount\b", r"\brelocat", r"\blayoffs?\b", r"\bjob cuts\b",
                         r"\bstaff\b", r"\bemployees\b"],
    "Payment Risk": [r"\blate payment", r"\bpayment (risk|cycles?|stretch|delays?)\b", r"\bcash.?flow\b",
                     r"\bdelayed payment", r"\bunpaid\b", r"\bindexation\b"],
    "Contract Award": [r"\bawarded\b", r"\bwins?\b", r"\bwon\b", r"\bsecured an?\b", r"\bsigned an? .{0,30}contract",
                       r"\bcontract.award"],
    "Financial Result": [r"\bnet profit\b", r"\brevenue\b", r"\bearnings\b", r"\bquarterly results\b"],
    "Market Trend": [r"\byear on year\b", r"\bquarter on quarter\b", r"\bmarket report\b", r"\bprojected to\b",
                     r"\boutlook\b", r"\bawards (jump|climb|rose|fell|totall)", r"\bforecast"],
}

RISK_CATEGORY_MAP = {
    "Project Delay": "Operational",
    "Project Suspension": "Operational",
    "Contract Cancellation": "Operational",
    "Supply Chain Disruption": "Operational",
    "Workforce Change": "Operational",
    "Cost Overrun": "Financial",
    "Payment Risk": "Financial",
    "Financial Result": "Financial",
    "Regulatory Change": "Regulatory",
    "Contract Award": "Market",
    "Market Trend": "Market",
    "No Risk Event": "None",
}

BASE_SEVERITY = {
    "Contract Cancellation": "High",
    "Project Suspension": "High",
    "Cost Overrun": "High",
    "Project Delay": "Medium",
    "Supply Chain Disruption": "Medium",
    "Regulatory Change": "Medium",
    "Workforce Change": "Medium",
    "Payment Risk": "Medium",
    "Contract Award": "Low",
    "Financial Result": "Low",
    "Market Trend": "Low",
}

# Push severity one level up or down from the event's base level.
INTENSIFIERS = [r"\bparalys", r"\bbankrupt", r"\binsolven", r"\bdefault", r"\bcollapse", r"\bconflict\b",
                r"\bmajor loss", r"\bwrite.?down"]
MITIGATORS = [r"\bby (one|two|three|a few) (days|weeks)\b", r"\bminor\b", r"\btemporar", r"\bcommonly\b",
              r"\bstandard practice\b", r"\bceremonial\b"]

LEVELS = ["Low", "Medium", "High"]
NO_EVENT = "No Risk Event"


def _hits(patterns, text):
    return sum(len(re.findall(p, text)) for p in patterns)


def event_scores(title: str, body: str) -> dict:
    return {
        event: TITLE_WEIGHT * _hits(patterns, title) + _hits(patterns, body)
        for event, patterns in EVENT_PATTERNS.items()
    }


def detect_event(title: str, body: str):
    """Return (event_type, confidence) where confidence is the winner's share of keyword evidence."""
    scores = event_scores(title.lower(), body.lower())
    total = sum(scores.values())
    if total == 0:
        return NO_EVENT, 0.0
    best = max(scores, key=scores.get)  # max() keeps the first key on ties, i.e. priority order
    return best, round(scores[best] / total, 2)


def assign_severity(event_type: str, title: str, body: str) -> str:
    if event_type == NO_EVENT:
        return "None"
    text = f"{title} {body}".lower()
    level = LEVELS.index(BASE_SEVERITY[event_type])
    if _hits(INTENSIFIERS, text):
        level += 1
    if _hits(MITIGATORS, text):
        level -= 1
    return LEVELS[max(0, min(level, 2))]


def classify(title: str, body: str) -> dict:
    title, body = str(title), str(body)
    event_type, confidence = detect_event(title, body)
    return {
        "event_type": event_type,
        "risk_category": RISK_CATEGORY_MAP[event_type],
        "severity": assign_severity(event_type, title, body),
        "confidence_score": confidence,
    }


if __name__ == "__main__":
    df = pd.read_csv(ENTITIES_CSV)

    out = pd.DataFrame([classify(t, b) for t, b in zip(df["clean_title"], df["clean_text"])], index=df.index)
    df = pd.concat([df, out], axis=1)

    df.to_csv(RISK_EVENTS_CSV, index=False)
    print(df[["article_id", "title", "event_type", "risk_category", "severity", "confidence_score"]].to_string())
    print("\nRisk category distribution:")
    print(df["risk_category"].value_counts())
    print("\nSeverity distribution:")
    print(df["severity"].value_counts())
