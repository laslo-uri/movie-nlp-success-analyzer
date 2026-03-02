# Movie NLP Success Analyzer

**SIAP — University of Novi Sad, Faculty of Technical Sciences**  
*Laslo Uri · Denis Dautovic · Nikola Jankovic*

Predict **commercial success** (ROI ≥ 2.0) and **Oscar nomination** using NLP on subtitles plus TMDB metadata. Pipeline: TF-IDF, sentiment (VADER/TextBlob), lexical diversity → Logistic Regression, Random Forest, XGBoost.

| Target            | Positive rate |
|-------------------|:------------:|
| `is_commercial`   | ~49%         |
| `is_award_winner` | ~16%         |

**Data:** TMDB API (metadata), OpenSubtitles (~7.4k subtitles), Academy Awards.

**Results (Phase 1, set `7_+runtime`):** Commercial — LR F1 0.607, AUC 0.659. Award — LR F1(opt) 0.508, AUC 0.797. Details: [phase_01/README.md](phase_01/README.md) and `phase_01/03_baseline_models.ipynb`.

---

## Structure

- **`data_pipeline/`** — Fetch TMDB, awards, subtitles; merge & filter. Specs in `data_pipeline/specifications/`.
- **`src/`** — `data_loader`, `nlp_features`, `models`, `eda_plots`.
- **`phase_01/`** — EDA, NLP features, baseline models (notebooks 01–03), report, figures, KT1 specs & guides in `specifications/` and `guides/`.

Not in repo: `.venv/`, `data/raw/`, `data/processed/`, `helpers/`, `phase_02/`.

---

## Quick start

```bash
git clone <repo-url>
cd movie-nlp-success-analyzer
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd phase_01 && jupyter notebook
```

Notebooks expect data in `data/processed/` (see data pipeline to generate).

---

## Links

- [Phase 1 report](phase_01/README.md) · [Phase 1 spec & guides](phase_01/specifications/) · [Data pipeline spec](data_pipeline/specifications/)
- [Project proposal](project_proposal/) · [Literature](research_papers/)

Academic use only — University of Novi Sad, FTN.
