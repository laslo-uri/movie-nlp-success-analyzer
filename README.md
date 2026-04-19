# Movie NLP Success Analyzer

**SIAP — University of Novi Sad, Faculty of Technical Sciences**  
*Laslo Uri · Denis Dautović · Nikola Janković*

Predicting **commercial success** (ROI ≥ 2.0) and **award nominations** for movies using NLP analysis of subtitles combined with TMDB metadata. The project features a fully automated data pipeline and a two-phase modeling approach — from baseline classifiers to hyperparameter-tuned models and ensemble methods.

---

## Results

| Task | Best Model | F1 (opt) | AUC |
|------|-----------|:--------:|:---:|
| Commercial Success | Random Forest (tuned) | **0.664** | 0.631 |
| Award Prediction | Logistic Regression (tuned) | **0.549** | **0.857** |

**Phase 1 baselines →** Commercial: LR F1=0.607, AUC=0.659 · Award: LR F1(opt)=0.508, AUC=0.797  
**Phase 2 improvements →** Hyperparameter tuning, SVM (linear/RBF), class balancing (SMOTE/ADASYN), soft/hard voting & stacking ensembles

---

## Dataset

| | |
|---|---|
| **Total films** | 12,950 (1950–2024) |
| **Modeling subset** | 5,791 (budget, revenue, runtime > 0 + subtitle available) |
| **Commercial positive rate** | ~49% |
| **Award positive rate** | ~16% |

**Sources:** TMDB API (metadata & financials), Subslikescript.com (subtitle text via web scraping), Wikipedia API (award history)

---

## Project Structure

```
movie-nlp-success-analyzer/
├── data_pipeline/          # Automated data collection & processing
│   ├── fetch_tmdb.py           # TMDB API metadata fetcher
│   ├── fetch_awards.py         # Wikipedia award scraper
│   ├── scrape_transcripts.py   # Subtitle web scraper
│   ├── enrich_tmdb_data.py     # Data enrichment
│   ├── merge_and_filter.py     # Dataset merging & filtering
│   ├── extend_database.py      # Database expansion utility
│   ├── audit_files.py          # File quality auditing
│   ├── check_balance.py        # Class balance analysis
│   └── specifications/         # Pipeline specification docs
├── src/                    # Shared library modules
│   ├── data_loader.py          # Data loading & preprocessing
│   ├── nlp_features.py         # NLP feature extraction (TF-IDF, VADER, lexical)
│   ├── models.py               # Model definitions, training & evaluation
│   └── eda_plots.py            # Visualization utilities
├── phase_01/               # KT1 — EDA, NLP features, baselines
│   ├── 01_eda.ipynb            # Exploratory data analysis
│   ├── 02_nlp_features.ipynb   # NLP feature engineering
│   ├── 03_baseline_models.ipynb # Baseline model training & evaluation
│   ├── figures/                # Generated plots
│   └── README.md               # Phase 1 detailed report
├── phase_02/               # KT2 — Tuning, SVM, ensembles, error analysis
│   ├── 04_model_improvements.ipynb  # Hyperparameter tuning & SVM
│   ├── 05_error_analysis_extended.ipynb # Detailed error analysis
│   ├── 06_conclusions_and_report_tables.ipynb # Final results & tables
│   └── figures/                # Generated plots
├── project_proposal/       # Initial project proposal (EN/SR)
├── requirements.txt
└── .env.example
```

**Not in repo** (gitignored): `data/`, `reports/`, `final_report/`, `research_papers/`, `models/`, `.venv/`

---

## Methods

### NLP Feature Pipeline
- Text cleaning (timestamps, HTML, brackets)
- Basic text statistics (word count, sentence count)
- Lexical diversity metrics
- Sentiment analysis (VADER compound, positive, negative, neutral)
- TF-IDF (5,000 terms) → TruncatedSVD (100 components)

### Models
- **Logistic Regression** — `class_weight='balanced'`
- **Random Forest** — 100 trees, balanced class weights
- **XGBoost** — gradient boosted trees with `scale_pos_weight`
- **SVM** — linear and RBF kernels (Phase 2)
- **Ensembles** — soft/hard voting, stacking with LR meta-classifier (Phase 2)

### Evaluation
- Stratified 70/15/15 split (train/validation/test)
- Metrics: F1, F1@optimal threshold, AUC, MCC, balanced accuracy
- Progressive feature set evaluation (9 cumulative feature sets)
- `RandomizedSearchCV` with `n_iter=25`, 5-fold stratified CV

---

## Quick Start

```bash
git clone <repo-url>
cd movie-nlp-success-analyzer
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run Phase 1 notebooks:
```bash
cd phase_01 && jupyter notebook
```

Run Phase 2 notebooks:
```bash
cd phase_02 && jupyter notebook
```

> Notebooks expect data in `data/processed/` — run the data pipeline scripts first to generate it.

---

## Links

- [Phase 1 Report](phase_01/README.md) · [Data Pipeline Specs](data_pipeline/specifications/)
- [Project Proposal](project_proposal/)

---

Academic use only — University of Novi Sad, Faculty of Technical Sciences, 2026.
