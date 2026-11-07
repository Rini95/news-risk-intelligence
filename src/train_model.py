"""
Supervised baseline (TF-IDF + Logistic Regression) and evaluation against the rules.

What is evaluated, and how honestly:
- gold set (15 real articles, hand-labelled): ML scored with leave-one-out CV, so every
  prediction is for an article the model never saw. The v2 rules were revised after
  error analysis on these same articles, so their gold-set score is optimistic.
- challenge set (20 short synthetic cases written after the v2 rules were frozen):
  neither the rules nor the model saw them, so this is the fairer held-out comparison.
  They are hand-written test cases, not real news, and are never used for training.
- robustness: v2 rules re-run on degraded gold text (no headline, headline only,
  random word dropout).

With 15 training examples (several classes have one example) the numbers show the
evaluation framework working, not model quality. They become meaningful once the
planned 500-1,000 labelled articles exist; the same script then runs unchanged.
"""
import random
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC

import rules_v1
from classify_risk import classify
from config import EVAL_DIR, GOLD_CSV, MODELS, RISK_EVENTS_CSV
from preprocess import clean_text

TARGETS = ["event_type", "risk_category", "severity"]
SEVERITY_ORDER = ["Low", "Medium", "High"]


def make_model(kind="logreg"):
    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1, stop_words="english")
    clf = {
        "logreg": LogisticRegression(C=10, class_weight="balanced", max_iter=2000),
        "linear_svm": LinearSVC(C=1, class_weight="balanced"),
        "naive_bayes": ComplementNB(alpha=0.5),
    }[kind]
    return make_pipeline(vec, clf)


def scores(y_true, y_pred):
    p, r, f, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    return {"accuracy": accuracy_score(y_true, y_pred), "macro_precision": p, "macro_recall": r, "macro_f1": f}


def rules_v1_predict(body):
    event = rules_v1.detect_event(body)
    return {"event_type": event, "risk_category": rules_v1.RISK_CATEGORY_MAP[event],
            "severity": rules_v1.assign_severity(body)}


def model_text(title, body):
    return f"{title} {title} {body}"  # headline repeated, mirroring the rules' title weight


def load_gold():
    events = pd.read_csv(RISK_EVENTS_CSV)
    gold = pd.read_csv(GOLD_CSV).rename(columns={f"gold_{t}": t for t in TARGETS})
    df = events[["article_id", "clean_title", "clean_text"]].merge(gold, on="article_id")
    df["text"] = [model_text(t, b) for t, b in zip(df["clean_title"], df["clean_text"])]
    return df


def load_challenge():
    df = pd.read_csv(GOLD_CSV.parent / "challenge_set.csv").rename(columns={f"gold_{t}": t for t in TARGETS})
    df["clean_title"] = df["title"].apply(clean_text)
    df["clean_text"] = df["text"].apply(clean_text)
    df["text"] = [model_text(t, b) for t, b in zip(df["clean_title"], df["clean_text"])]
    return df


def degrade(text, drop, rng):
    words = text.split()
    return " ".join(w for w in words if rng.random() > drop)


def main():
    # LOO folds that hold out a class's only example trigger sklearn warnings; expected here.
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)
    gold, chal = load_gold(), load_challenge()

    v1_gold = pd.DataFrame([rules_v1_predict(b) for b in gold["clean_text"]])
    v2_gold = pd.DataFrame([classify(t, b) for t, b in zip(gold["clean_title"], gold["clean_text"])])
    v1_chal = pd.DataFrame([rules_v1_predict(b) for b in chal["clean_text"]])
    v2_chal = pd.DataFrame([classify(t, b) for t, b in zip(chal["clean_title"], chal["clean_text"])])

    rows, preds = [], gold[["article_id"] + TARGETS].copy()
    loo = LeaveOneOut()
    for target in TARGETS:
        y, yc = gold[target], chal[target]
        # Majority baseline fit on all 15: under LOO a perfectly balanced target (severity is 5/5/5)
        # always predicts a wrong class, which would understate the baseline.
        majority = DummyClassifier(strategy="most_frequent").fit(gold["text"], y)
        rows.append({"dataset": "gold", "target": target, "system": "majority class",
                     **scores(y, majority.predict(gold["text"]))})
        rows.append({"dataset": "gold", "target": target, "system": "rules v1 (Phase 1)", **scores(y, v1_gold[target])})
        rows.append({"dataset": "gold", "target": target, "system": "rules v2 (tuned on gold)", **scores(y, v2_gold[target])})
        rows.append({"dataset": "challenge", "target": target, "system": "majority class",
                     **scores(yc, [y.mode()[0]] * len(yc))})
        rows.append({"dataset": "challenge", "target": target, "system": "rules v1 (Phase 1)", **scores(yc, v1_chal[target])})
        rows.append({"dataset": "challenge", "target": target, "system": "rules v2", **scores(yc, v2_chal[target])})

        for kind in ["logreg", "linear_svm", "naive_bayes"]:
            oof = cross_val_predict(make_model(kind), gold["text"], y, cv=loo)
            rows.append({"dataset": "gold (LOO)", "target": target, "system": f"ML {kind}", **scores(y, oof)})
            full = make_model(kind).fit(gold["text"], y)
            rows.append({"dataset": "challenge", "target": target, "system": f"ML {kind}",
                         **scores(yc, full.predict(chal["text"]))})
            if kind == "logreg":
                # Out-of-fold probabilities: the dashboard's ML confidence for each article
                # comes from a model that did not see that article.
                proba = cross_val_predict(make_model(kind), gold["text"], y, cv=loo, method="predict_proba")
                preds[f"ml_{target}"] = oof
                preds[f"ml_{target}_prob"] = proba.max(axis=1).round(2)
                joblib.dump(full, MODELS / f"logreg_{target}.joblib")
                chal[f"ml_{target}"] = full.predict(chal["text"])

    metrics = pd.DataFrame(rows).round(3)
    metrics.to_csv(EVAL_DIR / "metrics.csv", index=False)

    for target in TARGETS:
        preds[f"rules_v1_{target}"] = v1_gold[target]
        preds[f"rules_v2_{target}"] = v2_gold[target]
        chal[f"rules_v2_{target}"] = v2_chal[target]
        chal[f"rules_v1_{target}"] = v1_chal[target]
    preds.to_csv(EVAL_DIR / "gold_predictions.csv", index=False)
    chal.drop(columns=["text", "clean_title", "clean_text"]).to_csv(EVAL_DIR / "challenge_predictions.csv", index=False)

    cm = confusion_matrix(chal["severity"], chal["rules_v2_severity"], labels=SEVERITY_ORDER)
    pd.DataFrame(cm, index=[f"true {s}" for s in SEVERITY_ORDER], columns=[f"pred {s}" for s in SEVERITY_ORDER]) \
        .to_csv(EVAL_DIR / "challenge_severity_confusion_rules_v2.csv")

    # Robustness of the v2 rules to missing / noisy text on the gold set.
    robust = []
    for name, fn in [("full text", lambda t, b, r: (t, b)), ("body only (no headline)", lambda t, b, r: ("", b)),
                     ("headline only", lambda t, b, r: (t, ""))]:
        p = pd.DataFrame([classify(*fn(t, b, None)) for t, b in zip(gold["clean_title"], gold["clean_text"])])
        robust.append({"condition": name, **{f"{x}_accuracy": accuracy_score(gold[x], p[x]) for x in TARGETS}})
    for drop in [0.1, 0.2, 0.3]:
        accs = {x: [] for x in TARGETS}
        for seed in range(30):
            rng = random.Random(seed)
            p = pd.DataFrame([classify(degrade(t, drop, rng), degrade(b, drop, rng))
                              for t, b in zip(gold["clean_title"], gold["clean_text"])])
            for x in TARGETS:
                accs[x].append(accuracy_score(gold[x], p[x]))
        robust.append({"condition": f"{int(drop * 100)}% words dropped (mean of 30 runs)",
                       **{f"{x}_accuracy": np.mean(v) for x, v in accs.items()}})
    pd.DataFrame(robust).round(3).to_csv(EVAL_DIR / "robustness_rules_v2.csv", index=False)

    with pd.option_context("display.width", 200):
        print(metrics.to_string(index=False))
        print(pd.DataFrame(robust).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
