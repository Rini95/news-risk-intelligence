"""
Evaluation on independent real news (data/labels/realworld_test.csv).

The 108 headlines were collected after the v2 rules were frozen and were never
used to change a rule. Unlike the 15 training articles, most of them contain no
risk event, so this is where event *detection* (RQ1) and its false positives can
be measured, not only classification of articles already known to be events.

Labels: until Rini has reviewed them (make_review_workbook.py -> apply_review.py),
all 108 labels are Claude's drafts, so every score here is agreement with draft
labels, not with gold-standard annotations. 95 of the 108 items are headline only
(no teaser), so results are also reported separately for the 13 with a teaser.

Unit of analysis: one news article, represented by its headline plus the
publisher's teaser where the source shows one. One label per article: the
primary event type, or "No Risk Event".

Systems compared:
- rules v1 (Phase 1), with its "Other" output read as "No Risk Event";
- rules v2 (frozen);
- ML trained on the 15 gold articles only (it has never seen a negative example,
  so it cannot output "No Risk Event");
- ML trained with negatives: 5-fold stratified cross-validation over the real
  set, each fold trained on the 15 gold articles plus the other four folds.
"""
import warnings

import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold

import rules_v1
from classify_risk import NO_EVENT, RISK_CATEGORY_MAP, classify
from config import EVAL_DIR, GOLD_CSV, REALWORLD_DRAFT_CSV, REALWORLD_REVIEWED_CSV, RISK_EVENTS_CSV
from preprocess import clean_text
from train_model import make_model, model_text

TARGETS = ["event_type", "risk_category", "severity"]


def load_realworld():
    if REALWORLD_REVIEWED_CSV.exists():
        df = pd.read_csv(REALWORLD_REVIEWED_CSV, keep_default_na=False)
    else:
        df = pd.read_csv(REALWORLD_DRAFT_CSV, keep_default_na=False)
        df["label_status"] = "draft"
    df = df[df["label_status"] != "excluded"].reset_index(drop=True)
    df["has_teaser"] = df["teaser"] != ""
    df = df.rename(columns={f"gold_{t}": t for t in TARGETS})
    df["clean_title"] = df["title"].apply(clean_text)
    df["clean_text"] = df["teaser"].apply(clean_text)
    df["text"] = [model_text(t, b) for t, b in zip(df["clean_title"], df["clean_text"])]
    df["is_event"] = df["event_type"] != NO_EVENT
    return df


def load_gold_training():
    events = pd.read_csv(RISK_EVENTS_CSV)
    gold = pd.read_csv(GOLD_CSV).rename(columns={f"gold_{t}": t for t in TARGETS})
    df = events[["clean_title", "clean_text", "article_id"]].merge(gold, on="article_id")
    df["text"] = [model_text(t, b) for t, b in zip(df["clean_title"], df["clean_text"])]
    return df


def rules_v1_predict(title, body):
    # v1 never looked at the headline; with headline-only items it gets the headline as its body.
    text = f"{title} {body}".strip()
    event = rules_v1.detect_event(text)
    if event == "Other":
        return {"event_type": NO_EVENT, "risk_category": "None", "severity": "None"}
    return {"event_type": event, "risk_category": rules_v1.RISK_CATEGORY_MAP[event],
            "severity": rules_v1.assign_severity(text)}


def detection_scores(y_true, y_pred):
    p, r, f, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)
    negatives = (~y_true).sum()
    fp = int((y_pred & ~y_true).sum())
    return {"n": len(y_true), "events": int(y_true.sum()), "predicted_events": int(y_pred.sum()),
            "precision": p, "recall": r, "f1": f, "false_positives": fp,
            "false_positive_rate": fp / negatives if negatives else float("nan")}


def class_scores(y_true, y_pred):
    p, r, f, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    return {"n": len(y_true), "accuracy": accuracy_score(y_true, y_pred), "macro_precision": p,
            "macro_recall": r, "macro_f1": f}


def ml_with_negatives(real, gold, target):
    """Out-of-fold predictions on the real set from models trained on gold + the other folds."""
    preds = pd.Series(index=real.index, dtype=object)
    # Stratify on detection so every fold has events and non-events.
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    for train_idx, test_idx in folds.split(real, real["is_event"]):
        train = pd.concat([gold[["text", target]], real.iloc[train_idx][["text", target]]])
        model = make_model("logreg").fit(train["text"], train[target])
        preds.iloc[test_idx] = model.predict(real.iloc[test_idx]["text"])
    return preds


def main():
    warnings.filterwarnings("ignore")
    real, gold = load_realworld(), load_gold_training()

    systems = {
        "rules v1 (Phase 1)": pd.DataFrame([rules_v1_predict(t, b) for t, b in zip(real["clean_title"], real["clean_text"])],
                                           index=real.index),
        "rules v2 (frozen)": pd.DataFrame([classify(t, b) for t, b in zip(real["clean_title"], real["clean_text"])],
                                          index=real.index),
    }
    gold_only = {t: make_model("logreg").fit(gold["text"], gold[t]).predict(real["text"]) for t in TARGETS}
    systems["ML, 15 gold articles only"] = pd.DataFrame(gold_only, index=real.index)
    ml = pd.DataFrame({t: ml_with_negatives(real, gold, t) for t in TARGETS}, index=real.index)
    # Keep the three outputs consistent: no event means no category and no severity.
    ml.loc[ml["event_type"] == NO_EVENT, ["risk_category", "severity"]] = "None"
    systems["ML + negatives (5-fold CV)"] = ml

    candidates = {
        "all": real.index,
        "natural listing": real.index[real["sampling"] == "natural_listing"],
        "unambiguous only": real.index[real["ambiguous"] != "yes"],
        "headline + teaser": real.index[real["has_teaser"]],
        "headline only": real.index[~real["has_teaser"]],
        "human-reviewed labels": real.index[real["label_status"].isin(["verified", "corrected"])],
    }
    subsets = {f"{k} ({len(v)})": v for k, v in candidates.items() if len(v)}
    all_name = next(iter(subsets))

    det_rows, cls_rows = [], []
    for name, pred in systems.items():
        is_event = pred["event_type"] != NO_EVENT
        for sub, idx in subsets.items():
            det_rows.append({"system": name, "subset": sub, **detection_scores(real.loc[idx, "is_event"], is_event.loc[idx])})
        for target in TARGETS:
            cls_rows.append({"system": name, "target": target, "subset": all_name,
                             **class_scores(real[target], pred[target])})
            ev = real.index[real["is_event"]]
            cls_rows.append({"system": name, "target": target, "subset": f"true events only ({len(ev)})",
                             **class_scores(real.loc[ev, target], pred.loc[ev, target])})
        for target in TARGETS:
            real[f"{name}|{target}"] = pred[target]

    det = pd.DataFrame(det_rows).round(3)
    cls = pd.DataFrame(cls_rows).round(3)
    det.to_csv(EVAL_DIR / "realworld_detection.csv", index=False)
    cls.to_csv(EVAL_DIR / "realworld_classification.csv", index=False)

    v2 = systems["rules v2 (frozen)"]["event_type"]
    labels = sorted(set(real["event_type"]) | set(v2))
    pd.DataFrame(confusion_matrix(real["event_type"], v2, labels=labels),
                 index=[f"true {l}" for l in labels], columns=[f"pred {l}" for l in labels]) \
        .to_csv(EVAL_DIR / "realworld_confusion_rules_v2.csv")
    keep = ["case_id", "title", "teaser", "publisher", "url", "publication_date", "sampling", "ambiguous",
            "has_teaser", "label_status", "event_type", "risk_category", "severity"]
    out = real[keep + [c for c in real.columns if "|" in c]]
    out.to_csv(EVAL_DIR / "realworld_predictions.csv", index=False)

    status = real["label_status"].value_counts().rename_axis("label_status").reset_index(name="n")
    status.to_csv(EVAL_DIR / "realworld_label_status.csv", index=False)
    print(f"labels: {dict(zip(status.label_status, status.n))}; with teaser {int(real.has_teaser.sum())}/{len(real)}")

    with pd.option_context("display.width", 220, "display.max_columns", 20):
        print(det.to_string(index=False))
        print(cls.to_string(index=False))


if __name__ == "__main__":
    main()
