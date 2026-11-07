# News to structured signals: GCC construction risk pipeline

```
pip install -r requirements.txt && python -m spacy download en_core_web_sm
bash run_pipeline.sh            # rebuilds every output from the raw seed
streamlit run app/dashboard.py  # dashboard
python tests/test_collect_rss.py
# full step-by-step checks: TESTING.md
```

| Step | Script | Output |
|---|---|---|
| RSS collection (needs internet) | `src/collect_rss.py` | `data/raw/rss_articles.csv` |
| Raw seed (15 articles) | `src/build_raw_dataset.py` | `data/raw/articles_raw.csv` |
| Cleaning | `src/preprocess.py` | `data/processed/articles_clean.csv` (adds `clean_title`) |
| Entities (spaCy + clean-up) | `src/entities.py` | `data/processed/articles_entities.csv` |
| Rule classifier v2 | `src/classify_risk.py` | `data/processed/risk_events.csv` |
| ML baseline, gold + challenge evaluation | `src/train_model.py` | `outputs/evaluation/metrics.csv` etc., `models/*.joblib` |
| Label review workbook (run once) | `src/make_review_workbook.py` | `data/labels/label_review.xlsx` |
| Merge reviewed labels | `src/apply_review.py` | `data/labels/*_reviewed.csv` (adds `label_status`) |
| Real-world held-out evaluation | `src/evaluate_realworld.py` | `outputs/evaluation/realworld_*.csv` |
| Demonstration table | `src/build_final.py` | `data/processed/risk_events_final.csv` |
| Dashboard | `app/dashboard.py` | Streamlit app |

## Data and how it was collected

| File | Rows | Collection | Role |
|---|---|---|---|
| `data/raw/articles_raw.csv` | 15 | Manual: real articles, stored as paraphrased summaries with URLs | Demonstration dataset (dashboard) and training / error analysis (gold set) |
| `data/labels/realworld_test.csv` | 108 | Manual, 18 Oct 2026: every construction item on two publisher listing pages (93) plus 15 risk headlines from targeted web searches | Evaluation dataset: independent held-out test; 70 have no risk event. Draft labels; 95 are headline only |
| `data/labels/challenge_set.csv` | 20 | Hand-written synthetic cases | Supplementary stress test only |

`src/collect_rss.py` automates collection. It is tested offline on `tests/sample_feed.xml`
but could not be run against live feeds from the environment it was written in, so
the 108-article test set was collected manually and `data/labels/build_realworld_test.py`
records exactly how. Run the collector on a normal connection to grow the pool.

## Two datasets, kept separate

- **Demonstration dataset**: the 15 seed articles. They go through the whole pipeline
  (cleaning, entities, rules, ML) into `risk_events_final.csv`, which the dashboard's
  default view shows.
- **Evaluation dataset**: the 108 real headlines. They are only used to score the
  classifiers (`outputs/evaluation/realworld_*.csv`) and have their own dashboard view
  (sidebar: *Evaluation dataset*). They never appear in the demonstration charts.

## Label status of the evaluation dataset

`data/labels/labelling_guidelines.md` defines the unit of analysis (one article,
headline + teaser/summary, one primary label or No Risk Event).

All labels, the 108 real-world ones and the 15 seed ("gold") ones, were drafted with
Claude and are **not gold-standard annotations** until a person reviews them. 95 of the 108 have no teaser, so their labels (and the classifiers'
predictions) rest on the headline alone; results are reported separately for the 13 with
a teaser. `data/labels/link_check.csv` records an automated check that each link opens
and matches its headline, with a one-line summary of the page and any doubt about the
draft label; it is a prompt for the human review, not a second annotator.

To review: open `data/labels/label_review.xlsx` (sheets *Real-world 108* and *Seed 15*),
set Decision (Accept / Correct / Exclude) in the yellow columns for each row, save, then
run `bash run_pipeline.sh`. `apply_review.py` writes `realworld_reviewed.csv` and
`gold_labels_reviewed.csv` with `label_status` (verified / corrected / excluded / draft);
every later step reads the reviewed files, and the evaluation adds a "human-reviewed
labels" subset. Rows left blank stay `draft`. The draft files are never overwritten.

`src/rules_v1.py` is the Phase 1 classifier, kept unchanged as the evaluation baseline.
Paths come from `src/config.py` and are relative to this folder.
