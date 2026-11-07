import json
import re

import pandas as pd
import spacy

from config import CLEAN_CSV, ENTITIES_CSV

nlp = spacy.load("en_core_web_sm")

# en_core_web_sm tags programmes, events and regional blocs as ORG/GPE. These are
# not companies, so they are moved out of the organisations list (error analysis
# of the Phase 1 output: "Vision 2030" and "GCC" appeared as company names,
# "Expo 2030" as a location).
NOT_ORGS = {"vision 2030", "expo 2030", "world cup 2034", "gcc", "gcc mep", "uae", "saudi", "iran"}
NOT_LOCS = {"expo 2030", "world cup 2034", "vision 2030"}
ORG_TO_LOC = {"gcc", "uae"}
# Nationality adjectives ("Saudi construction projects") locate an article as well as a GPE does.
NORP_TO_LOC = {"saudi": "Saudi Arabia", "emirati": "UAE", "qatari": "Qatar", "omani": "Oman", "kuwaiti": "Kuwait"}
# Places spaCy misses in these articles because they are project names, not GPEs.
# Developer entities that spaCy sometimes tags as a place (NEOM is both a region and a company).
KNOWN_ORGS = {"neom": "NEOM", "public investment fund": "Public Investment Fund"}
PROJECT_NAMES = ["NEOM", "The Line", "New Murabba", "Mukaab", "Qiddiya", "Trojena", "Expo 2030 Riyadh"]


def normalise(name: str) -> str:
    name = re.sub(r"['’]s$", "", name.strip())   # "Kamco Invest's" -> "Kamco Invest"
    name = re.sub(r"^the\s+", "", name, flags=re.I)  # "the Strait of Hormuz" -> "Strait of Hormuz"
    return name.strip()


def extract_entities(text: str) -> dict:
    doc = nlp(text)
    orgs, locs = [], []
    for ent in doc.ents:
        name = normalise(ent.text)
        key = name.lower()
        if re.match(r"^(aed|sar|usd|\$)\s?[\d.,]+", key):
            continue  # currency amounts mis-tagged as ORG, e.g. "AED230 million"
        if key in KNOWN_ORGS:
            orgs.append(KNOWN_ORGS[key])
        elif ent.label_ == "ORG":
            if key in ORG_TO_LOC:
                locs.append(name)
            elif key not in NOT_ORGS:
                orgs.append(name)
        elif ent.label_ == "NORP" and key in NORP_TO_LOC:
            locs.append(NORP_TO_LOC[key])
        elif ent.label_ in {"GPE", "LOC"} and key not in NOT_LOCS:
            locs.append(name)
    projects = [p for p in PROJECT_NAMES if p.lower() in text.lower()]
    return {
        "organizations": list(dict.fromkeys(orgs)),
        "locations": list(dict.fromkeys(locs)),
        "projects": projects,
        "dates": list(dict.fromkeys(ent.text for ent in doc.ents if ent.label_ == "DATE")),
        "money": list(dict.fromkeys(ent.text for ent in doc.ents if ent.label_ == "MONEY")),
    }


if __name__ == "__main__":
    df = pd.read_csv(CLEAN_CSV)

    # Run entity extraction on the original-case text (spaCy NER works better
    # on true-cased text than on the lowercased clean_text column).
    df["entities"] = df["article_text"].apply(extract_entities)
    df["organizations"] = df["entities"].apply(lambda d: "; ".join(d["organizations"]))
    df["locations"] = df["entities"].apply(lambda d: "; ".join(d["locations"]))
    df["projects"] = df["entities"].apply(lambda d: "; ".join(d["projects"]))
    df["money_mentions"] = df["entities"].apply(lambda d: "; ".join(d["money"]))
    df["entities_json"] = df["entities"].apply(json.dumps)
    df = df.drop(columns=["entities"])

    df.to_csv(ENTITIES_CSV, index=False)
    print(df[["article_id", "organizations", "locations", "projects", "money_mentions"]].to_string())
