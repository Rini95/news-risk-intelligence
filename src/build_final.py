"""Export the dashboard-facing risk_events_final table (one row per article/event)."""
import pandas as pd

from config import EVAL_DIR, FINAL_CSV, RISK_EVENTS_CSV, STUDY_WINDOW_START

if __name__ == "__main__":
    df = pd.read_csv(RISK_EVENTS_CSV, parse_dates=["publication_date"])
    ml = pd.read_csv(EVAL_DIR / "gold_predictions.csv")[
        ["article_id", "ml_risk_category", "ml_risk_category_prob", "ml_severity", "ml_severity_prob"]]
    df = df.merge(ml, on="article_id", how="left")

    out = pd.DataFrame({
        "event_id": range(1, len(df) + 1),
        "article_id": df["article_id"],
        "title": df["title"],
        "company_name": df["organizations"].fillna(""),
        "location": df["locations"].fillna(""),
        "project": df["projects"].fillna(""),
        "event_type": df["event_type"],
        "risk_category": df["risk_category"],
        "severity": df["severity"],
        "confidence_score": df["confidence_score"],
        "ml_risk_category": df["ml_risk_category"],
        "ml_risk_category_prob": df["ml_risk_category_prob"],
        "ml_severity": df["ml_severity"],
        "ml_severity_prob": df["ml_severity_prob"],
        "publication_date": df["publication_date"].dt.strftime("%Y-%m-%d"),  # ISO, not locale-formatted
        "in_study_window": df["publication_date"] >= pd.Timestamp(STUDY_WINDOW_START),
        "source": df["publisher"],
        "source_url": df["url"],
        "supporting_text": df["article_text"],
    })
    # Agreement is recorded but not yet used for review routing: with 15 training
    # articles the model disagrees with the rules on most rows, so the flag would
    # mark everything. Switch needs_review to include disagreement once the
    # labelled set is large enough for the model to be trusted.
    out["rule_ml_severity_agree"] = out["ml_severity"] == out["severity"]
    out["needs_review"] = (out["confidence_score"] < 0.5) | ~out["in_study_window"]
    out.to_csv(FINAL_CSV, index=False)
    print(out[["event_id", "event_type", "risk_category", "severity", "confidence_score", "needs_review"]].to_string())
