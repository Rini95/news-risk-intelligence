"""
GCC construction risk signals dashboard.

Two datasets, chosen in the sidebar and never mixed:
- Demonstration: the 15 seed articles in risk_events_final.csv, run through the full
  pipeline (entities, rules, ML). Their labels are also Claude drafts until reviewed.
- Evaluation: 108 real headlines (outputs/evaluation/realworld_predictions.csv),
  used only to score the classifiers. Their labels are Claude's drafts until Rini
  has reviewed them, and 95 of them are headline only.

Run from the project root:  streamlit run app/dashboard.py
"""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from config import EVAL_DIR, FINAL_CSV, GOLD_CSV  # noqa: E402

SEVERITY_ORDER = ["High", "Medium", "Low"]
# Status colours for the ordinal severity scale; always shown with a text label.
SEVERITY_COLORS = {"High": "#d03b3b", "Medium": "#ec835a", "Low": "#fab219"}
# Categorical slots in fixed order, so a category keeps its colour under any filter.
RISK_ORDER = ["Operational", "Financial", "Market", "Regulatory"]
RISK_COLORS = {"Operational": "#2a78d6", "Financial": "#eb6834", "Market": "#1baf7a", "Regulatory": "#eda100"}
CHART_LAYOUT = dict(margin=dict(l=10, r=10, t=40, b=10), legend_title_text="", font=dict(size=13))

st.set_page_config(page_title="GCC Construction Risk Signals", layout="wide")


@st.cache_data
def load_events():
    df = pd.read_csv(FINAL_CSV, parse_dates=["publication_date"])
    for col in ["company_name", "location", "project"]:
        df[col] = df[col].fillna("")
    return df


@st.cache_data
def load_realworld():
    return {
        "pred": pd.read_csv(EVAL_DIR / "realworld_predictions.csv", keep_default_na=False,
                            converters={"has_teaser": lambda v: v == "True"}),
        "detection": pd.read_csv(EVAL_DIR / "realworld_detection.csv"),
        "classification": pd.read_csv(EVAL_DIR / "realworld_classification.csv"),
    }


@st.cache_data
def load_eval():
    return {
        "metrics": pd.read_csv(EVAL_DIR / "metrics.csv"),
        "robustness": pd.read_csv(EVAL_DIR / "robustness_rules_v2.csv"),
        "challenge": pd.read_csv(EVAL_DIR / "challenge_predictions.csv"),
    }


def demo_view():
    df = load_events()

    gold = pd.read_csv(GOLD_CSV)
    n_rev = int(gold["label_status"].isin(["verified", "corrected"]).sum()) if "label_status" in gold else 0
    labels = ("labels reviewed by Rini" if n_rev == len(gold) else
              f"reference labels drafted with Claude ({n_rev} of {len(gold)} reviewed so far)")
    st.caption(f"**Demonstration dataset.** {len(df)} seed news articles run through the full pipeline "
               f"(cleaning, entities, rule classifier v2, ML baseline), with {labels}. "
               "Signals are diagnostic and meant for human review, not automated decisions. "
               "The larger real-world evaluation set is under *Evaluation dataset* in the sidebar.")

    # Filters, in one row above the charts.
    f1, f2, f3, f4 = st.columns([2, 2, 2, 1])
    risk_sel = f1.multiselect("Risk category", RISK_ORDER, default=[r for r in RISK_ORDER if r in set(df["risk_category"])])
    sev_sel = f2.multiselect("Severity", SEVERITY_ORDER, default=SEVERITY_ORDER)
    search = f3.text_input("Company, project or location contains")
    window_only = f4.checkbox("2025+ only", value=True, help="Hide articles outside the study window (article 14 is from 2018).")

    view = df[df["risk_category"].isin(risk_sel) & df["severity"].isin(sev_sel)]
    if window_only:
        view = view[view["in_study_window"]]
    if search:
        hay = (view["company_name"] + " " + view["project"] + " " + view["location"]).str.lower()
        view = view[hay.str.contains(search.lower(), regex=False)]

    tab_overview, tab_events, tab_eval = st.tabs(["Overview", "Events", "Model evaluation"])

    with tab_overview:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Events", len(view))
        k2.metric("High severity", int((view["severity"] == "High").sum()))
        k3.metric("Most common risk", view["risk_category"].mode()[0] if len(view) else "–")
        k4.metric("Flagged for review", int(view["needs_review"].sum()))

        if view.empty:
            st.info("No events match the filters.")
        else:
            c1, c2 = st.columns(2)
            counts = view.groupby(["risk_category", "severity"]).size().reset_index(name="events")
            fig = px.bar(counts, y="risk_category", x="events", color="severity", orientation="h",
                         category_orders={"risk_category": RISK_ORDER, "severity": SEVERITY_ORDER},
                         color_discrete_map=SEVERITY_COLORS, title="Events by risk category and severity",
                         labels={"risk_category": "", "events": "Events"})
            fig.update_traces(marker_line_width=2, marker_line_color="white",
                              hovertemplate="%{y} · %{fullData.name}: %{x} events<extra></extra>")
            fig.update_layout(**CHART_LAYOUT, bargap=0.45)
            c1.plotly_chart(fig, use_container_width=True)

            types = view["event_type"].value_counts().sort_values().reset_index()
            types.columns = ["event_type", "events"]
            fig = px.bar(types, y="event_type", x="events", orientation="h", title="Events by type",
                         labels={"event_type": "", "events": "Events"}, color_discrete_sequence=["#2a78d6"])
            fig.update_traces(hovertemplate="%{y}: %{x}<extra></extra>")
            fig.update_layout(**CHART_LAYOUT, bargap=0.45, showlegend=False, xaxis_dtick=1)
            c2.plotly_chart(fig, use_container_width=True)

            # Articles from the same day and category would sit on top of each other; spread
            # them vertically so every signal stays visible and hoverable.
            tl = view.copy()
            tl["row"] = tl["risk_category"].map({r: i for i, r in enumerate(RISK_ORDER)}).astype(float)
            dup = tl.groupby(["publication_date", "risk_category"]).cumcount()
            size = tl.groupby(["publication_date", "risk_category"])["event_id"].transform("count")
            tl["row"] += (dup - (size - 1) / 2) * 0.18
            fig = px.scatter(tl, x="publication_date", y="row", color="severity",
                             category_orders={"risk_category": RISK_ORDER, "severity": SEVERITY_ORDER},
                             color_discrete_map=SEVERITY_COLORS, hover_name="title",
                             hover_data={"event_type": True, "risk_category": True, "source": True,
                                         "publication_date": "|%d %b %Y", "row": False, "severity": True},
                             title="Risk signals over time", labels={"publication_date": "", "row": ""})
            fig.update_yaxes(tickvals=list(range(len(RISK_ORDER))), ticktext=RISK_ORDER, autorange="reversed",
                             range=[-0.5, len(RISK_ORDER) - 0.5])
            fig.update_traces(marker=dict(size=13, line=dict(width=2, color="white")))
            fig.update_layout(**CHART_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

    with tab_events:
        st.dataframe(
            view[["event_id", "publication_date", "title", "event_type", "risk_category", "severity",
                  "confidence_score", "company_name", "project", "location", "source", "needs_review"]],
            hide_index=True, use_container_width=True,
            column_config={"publication_date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                           "confidence_score": st.column_config.NumberColumn("Rule confidence", format="%.2f")},
        )
        if not view.empty:
            st.subheader("Inspect an event")
            pick = st.selectbox("Event", view["event_id"],
                                format_func=lambda i: f"{i}: {view.loc[view['event_id'] == i, 'title'].iloc[0]}")
            row = view[view["event_id"] == pick].iloc[0]
            a, b, c = st.columns(3)
            a.markdown(f"**Event type**  \n{row['event_type']}")
            b.markdown(f"**Risk / severity (rules)**  \n{row['risk_category']} · {row['severity']} "
                       f"(confidence {row['confidence_score']:.2f})")
            c.markdown(f"**ML baseline (out-of-fold)**  \n{row['ml_risk_category']} ({row['ml_risk_category_prob']:.2f}) · "
                       f"{row['ml_severity']} ({row['ml_severity_prob']:.2f})")
            st.markdown(f"**Entities**: {row['company_name'] or '–'} | **Project**: {row['project'] or '–'} | "
                        f"**Location**: {row['location'] or '–'}")
            st.info(row["supporting_text"])
            st.markdown(f"Source: [{row['source']}]({row['source_url']}) · {row['publication_date']:%d %b %Y}")

    with tab_eval:
        ev = load_eval()
        st.markdown(
            "**How to read this.** The *gold* set is the 15 articles above, with reference labels (drafted with Claude; see the label status in the caption). The v2 rules were "
            "revised after error analysis on those same articles, so their gold score is optimistic. The ML "
            "models are scored on gold with leave-one-out cross-validation. The *challenge* set is 20 short "
            "hand-written test cases (not real news) written after the rules were frozen, so it is the fairer "
            "held-out comparison. With 15 training articles, these numbers demonstrate the evaluation method "
            "rather than final model quality."
        )
        m = ev["metrics"]
        chal = m[m["dataset"] == "challenge"]
        fig = px.bar(chal, x="system", y="macro_f1", color="target", barmode="group",
                     category_orders={"target": ["event_type", "risk_category", "severity"]},
                     color_discrete_sequence=["#2a78d6", "#eb6834", "#1baf7a"],
                     title="Macro F1 on the held-out challenge set", labels={"system": "", "macro_f1": "Macro F1"})
        fig.update_traces(hovertemplate="%{x} · %{fullData.name}: %{y:.2f}<extra></extra>")
        fig.update_layout(**CHART_LAYOUT, yaxis_range=[0, 1], bargap=0.3, bargroupgap=0.1)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(m, hide_index=True, use_container_width=True)
        st.subheader("Robustness of the v2 rules (gold set accuracy)")
        st.dataframe(ev["robustness"], hide_index=True, use_container_width=True)
        st.subheader("Challenge set predictions")
        st.dataframe(ev["challenge"], hide_index=True, use_container_width=True)


SYSTEM_COLORS = ["#8c8c8c", "#2a78d6", "#eda100", "#1baf7a"]
STATUS_TEXT = {"draft": "Claude draft, not yet reviewed", "verified": "reviewed, draft accepted",
               "corrected": "reviewed, corrected"}


def evaluation_view():
    rw = load_realworld()
    pred, det = rw["pred"], rw["detection"]
    n = len(pred)
    reviewed = int(pred["label_status"].isin(["verified", "corrected"]).sum())
    headline_only = int((~pred["has_teaser"]).sum())
    st.caption(f"**Evaluation dataset.** {n} real GCC construction headlines collected after the rules were frozen, "
               "used only to score the classifiers. They are not shown in the demonstration charts.")
    if reviewed < n:
        st.warning(f"**Reference labels are not gold standard yet.** {n - reviewed} of {n} labels are Claude's "
                   f"drafts awaiting Rini's review (data/labels/label_review.xlsx), so the scores below measure "
                   f"agreement with draft labels. {headline_only} of {n} items are headline only, with no teaser.")
    else:
        st.success(f"All {n} labels have been reviewed. {headline_only} of {n} items are headline only.")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Headlines", n)
    k2.metric("Risk events (reference)", int((pred["event_type"] != "No Risk Event").sum()))
    k3.metric("Headline only", headline_only)
    k4.metric("Human-reviewed labels", reviewed)

    subsets = list(det["subset"].unique())
    subset = st.radio("Subset", subsets, horizontal=True)
    d = det[det["subset"] == subset].melt(id_vars="system", value_vars=["precision", "recall", "false_positive_rate"],
                                           var_name="measure", value_name="score")
    d["measure"] = d["measure"].map({"precision": "Precision", "recall": "Recall",
                                     "false_positive_rate": "False positive rate"})
    fig = px.bar(d, x="measure", y="score", color="system", barmode="group",
                 color_discrete_sequence=SYSTEM_COLORS, title=f"Risk event detection, {subset}",
                 labels={"measure": "", "score": "Score"})
    fig.update_traces(hovertemplate="%{fullData.name} · %{x}: %{y:.2f}<extra></extra>")
    fig.update_layout(**CHART_LAYOUT, yaxis_range=[0, 1], bargap=0.3, bargroupgap=0.1)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Detection treats every label other than No Risk Event as an event. "
               "ML + negatives is trained partly on these same draft labels (5-fold CV), so it is optimistic.")
    with st.expander("Detection and classification tables"):
        st.dataframe(det, hide_index=True, use_container_width=True)
        st.dataframe(rw["classification"], hide_index=True, use_container_width=True)

    st.subheader("Headlines and predictions")
    systems = [c.split("|")[0] for c in pred.columns if c.endswith("|event_type")]
    c1, c2, c3 = st.columns([2, 2, 1])
    system = c1.selectbox("Compare against", systems, index=systems.index("rules v2 (frozen)"))
    status = c2.multiselect("Label status", sorted(pred["label_status"].unique()),
                            default=sorted(pred["label_status"].unique()))
    wrong_only = c3.checkbox("Disagreements only")
    t = pred[pred["label_status"].isin(status)].copy()
    t["prediction"] = t[f"{system}|event_type"]
    t["text used"] = t["has_teaser"].map({True: "headline + teaser", False: "headline only"})
    if wrong_only:
        t = t[t["prediction"] != t["event_type"]]
    st.dataframe(
        t[["case_id", "title", "event_type", "severity", "prediction", "label_status", "text used",
           "publisher", "url"]],
        hide_index=True, use_container_width=True,
        column_config={"title": st.column_config.TextColumn("Headline", width="large"),
                       "event_type": "Reference event type", "severity": "Reference severity",
                       "prediction": f"{system}", "label_status": "Label status",
                       "url": st.column_config.LinkColumn("Source", display_text="open")},
    )
    st.caption("Label status: " + "; ".join(f"{k} = {v}" for k, v in STATUS_TEXT.items()) + ".")


st.title("GCC construction risk signals")
DATASETS = {"Demonstration dataset (15 seed articles)": demo_view,
            "Evaluation dataset (108 real headlines)": evaluation_view}
choice = st.sidebar.radio("Dataset", list(DATASETS),
                          help="The demonstration set runs through the full pipeline. "
                               "The evaluation set is only used to score the classifiers.")
st.sidebar.caption("The two datasets are kept separate: evaluation headlines never appear in the demonstration charts.")
DATASETS[choice]()
