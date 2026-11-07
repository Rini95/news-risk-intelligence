#!/usr/bin/env bash
# Rebuilds every output. Two separate datasets:
#   demonstration  15 seed articles -> data/processed/risk_events_final.csv (what the dashboard's demo view shows)
#   evaluation     108 real headlines -> outputs/evaluation/realworld_*.csv (scores only)
# Optional first step, needs internet access: python3 collect_rss.py  (appends to data/raw/rss_articles.csv)
set -euo pipefail
cd "$(dirname "$0")/src"
python3 build_raw_dataset.py
# Merge Rini's label review (rows without a decision stay "draft"); later steps read the reviewed labels.
if [ -f ../data/labels/label_review.xlsx ]; then python3 apply_review.py; fi
python3 preprocess.py
python3 entities.py
python3 classify_risk.py
python3 train_model.py
python3 evaluate_realworld.py
python3 build_final.py
