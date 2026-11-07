# How to test everything

Each step says what to run and what you should see. Run every command from the
`news-risk-intelligence` folder (unzip `capstone_files.zip` first).
These steps were checked on a fresh copy on 19 Oct 2026, with Python 3.13.

## 1. Set up (once)

You need Python 3.11 or newer (`python3 --version`). On Windows the command is `python`
(or `py`), not `python3`: use `python --version`, `python -m venv .venv` and so on.
If Windows says "Python was not found ... Microsoft Store", install Python from python.org
and tick "Add python.exe to PATH" in the installer.

```
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

**Check:** `python -c "import spacy; spacy.load('en_core_web_sm'); print('ok')"` prints `ok`.

## 2. Run the whole pipeline

```
bash run_pipeline.sh
```

On Windows (Command Prompt), run `run_pipeline.bat` instead; it does the same steps.

**Check:** it ends without an error, and these files now exist:

- `data/processed/risk_events_final.csv`: 15 rows (the demonstration dataset)
- `models/logreg_event_type.joblib`, `models/logreg_risk_category.joblib`, `models/logreg_severity.joblib`
- `outputs/evaluation/metrics.csv`, plus five `realworld_*.csv` and two `challenge_*.csv` files

Near the top of the output you should see `real-world: {'draft': 108}` and `seed: {'draft': 15}`,
meaning that no label has been reviewed yet.

## 3. Check the evaluation numbers

Open `outputs/evaluation/realworld_detection.csv` and look at the `all (108)` rows. Before any
label review, they should read:

| system | precision | recall | false positive rate |
|---|---|---|---|
| rules v1 (Phase 1) | 0.818 | 0.237 | 0.029 |
| rules v2 (frozen) | 0.750 | 0.237 | 0.043 |
| ML, 15 gold articles only | 0.352 | 1.000 | 1.000 |
| ML + negatives (5-fold CV) | 0.900 | 0.711 | 0.043 |

These are the numbers in the write-up. If yours match, the pipeline reproduces.
`realworld_label_status.csv` shows how many labels are draft or reviewed.

## 4. Test the RSS collector

Offline test (no internet needed):

```
python tests/test_collect_rss.py
```

**Check:** it prints `collect_rss: all checks passed`.

Live run (needs internet; the feeds were never reachable from where the code was built):

```
cd src && python collect_rss.py && cd ..
```

**Check:** it prints counts such as `{'fetched': ..., 'added': ...}` and writes
`data/raw/rss_articles.csv`. A line starting with `!` means that one feed failed. Note
which ones fail, because their URLs may need updating in `FEEDS`.

## 5. Review the labels

1. Open `data/labels/label_review.xlsx`. The *Instructions* sheet explains the process.
2. On *Real-world 108* and *Seed 15*, fill in the yellow columns: Decision (Accept / Correct /
   Exclude), and for Correct also Your event type and Your severity. Start with the rows that
   have text in *Claude concern from page* (R001, R010, R096, R102, R104).
3. Save the file and run `bash run_pipeline.sh` again (Windows: `run_pipeline.bat`).

**Check:** the output now shows your counts, for example `real-world: {'draft': 78, 'verified': 30}`.
`realworld_detection.csv` gains `human-reviewed labels (N)` rows, and
`data/labels/realworld_reviewed.csv` / `gold_labels_reviewed.csv` have a `label_status` column.
The draft files `realworld_test.csv` and `gold_labels.csv` are never changed.

If you type an invalid value, for example Correct with no event type, the run stops and lists
the rows to fix. Nothing is half-applied.

Do not run `src/make_review_workbook.py` again after you have started reviewing. It refuses
to overwrite your decisions unless you pass `--force`.

## 6. Check the dashboard (both modes)

```
streamlit run app/dashboard.py
```

It opens at http://localhost:8501. Use the **Dataset** switch in the sidebar.

**Demonstration dataset (15 seed articles)**

- The caption says how many of the 15 seed labels have been reviewed.
- Overview shows 14 events with "2025+ only" ticked, and 15 with it unticked (article 14 is from 2018).
- Events: pick an event in the inspector. It shows the rule result, the ML prediction, the
  entities and a working source link.
- Model evaluation shows the challenge-set chart and the metrics tables.

**Evaluation dataset (108 real headlines)**

- A yellow banner says how many labels are still drafts and that 95 are headline only.
  After a full review it turns green.
- The KPI row shows 108 headlines, 38 events, 95 headline only, and the number of human-reviewed labels.
- Switching the Subset changes the detection chart. The bars should match step 3.
- In the table, tick "Disagreements only" and change "Compare against". The rows should
  change, and each "open" link should go to the article.

## Quick re-check after any change

```
bash run_pipeline.sh && python tests/test_collect_rss.py
```

Then repeat step 3. If the `all (108)` numbers change and you did not review any labels,
something in the code changed the results.
