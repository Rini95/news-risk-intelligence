"""Phase 1 rule-based classifier, kept unchanged as the evaluation baseline."""
import pandas as pd

# NOTE (error analysis, Step 10): keyword-priority order matters for rule-based
# classification. E.g. article 2 ("NEOM cancels tunnel contract...") mentions
# both "terminated" and "had been awarded" (referring to the earlier award) -
# checking Contract Cancellation before Contract Award fixes that specific
# case, but this brittleness is exactly why the guide recommends moving to a
# trained ML classifier (Step 7) once labelled data exists, rather than
# relying on keyword order indefinitely.
EVENT_KEYWORDS = {
    "Contract Cancellation": ["cancel", "terminat", "breakdown in"],
    "Project Suspension": ["suspend", "paused", "on hold", "reassess"],
    "Project Delay": ["delay", "postponed", "behind schedule", "extension", "downscaled", "downscale"],
    "Contract Award": ["awarded", "signed contract", "won contract", "secured a", "wins"],
    "Cost Overrun": ["cost overrun", "ballooned", "budget balloon", "cost escalation"],
    "Financial Result": ["net profit", "revenue", "earnings"],
    "Regulatory Change": ["regulator", "permit", "compliance", "zoning", "enforcement"],
    "Supply Chain Disruption": ["supply chain", "supply-chain", "shipping", "lead time", "shortage"],
    "Workforce Change": ["workforce", "headcount", "relocat", "labour", "labor"],
}

RISK_CATEGORY_MAP = {
    "Project Delay": "Operational",
    "Project Suspension": "Operational",
    "Contract Award": "Market",
    "Contract Cancellation": "Operational",
    "Cost Overrun": "Financial",
    "Financial Result": "Financial",
    "Regulatory Change": "Regulatory",
    "Supply Chain Disruption": "Operational",
    "Workforce Change": "Operational",
    "Other": "Market",
}

SEVERITY_TERMS = {
    "High": ["bankruptcy", "major loss", "cancel", "terminat", "default", "suspend", "ballooned", "breakdown"],
    "Medium": ["delay", "decline", "shortage", "investigation", "dispute", "escalation", "downscale"],
    "Low": ["minor", "temporary", "small decline", "awarded", "wins", "profit", "growth"],
}


def detect_event(text: str) -> str:
    text = text.lower()
    for event_type, keywords in EVENT_KEYWORDS.items():
        if any(k in text for k in keywords):
            return event_type
    return "Other"


def assign_severity(text: str) -> str:
    text = text.lower()
    for severity, keywords in SEVERITY_TERMS.items():
        if any(k in text for k in keywords):
            return severity
    return "Low"


