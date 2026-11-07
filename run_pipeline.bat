@echo off
REM Windows version of run_pipeline.sh: rebuilds every output.
REM   demonstration  15 seed articles -> data\processed\risk_events_final.csv
REM   evaluation     108 real headlines -> outputs\evaluation\realworld_*.csv
cd /d "%~dp0src" || exit /b 1
python build_raw_dataset.py || exit /b 1
REM Merge the label review (rows without a decision stay "draft").
if exist ..\data\labels\label_review.xlsx (python apply_review.py || exit /b 1)
python preprocess.py || exit /b 1
python entities.py || exit /b 1
python classify_risk.py || exit /b 1
python train_model.py || exit /b 1
python evaluate_realworld.py || exit /b 1
python build_final.py || exit /b 1
cd /d "%~dp0"
echo Pipeline finished.
