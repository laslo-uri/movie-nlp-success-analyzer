# Phase 1 Report — Movie NLP Success Analyzer

**SIAP · UNS FTN · Laslo Uri, Denis Dautovic, Nikola Jankovic · March 2026 · KT1**  
Spec: `specifications/` (Phase_01_KT1 EN/SR PDF).

**Data.** TMDB (76 CSVs), OpenSubtitles (~7.6k), Oscars + Golden Globes → `final_movie_list.csv` (12,950). Recomputed `is_commercial` (ROI ≥ 2.0), `is_popular` (vote_count ≥ 500). Subset: budget/revenue/runtime > 0 → 8,890; commercial ~44% pos., award ~12.8%, popular ~56%. No revenue in commercial features (leakage).

**Cleaning.** Missing: budget 29%, revenue 2%, runtime 0.2%. Logs: budget, revenue, vote_count. Genres → 19 dummies.

**EDA.** 1950–2024; ROI skewed; genre success: Adventure/Sci-Fi high, Documentary/History low; 58.8% subtitle coverage; top corr. vote_count, budget (commercial), runtime (award).

**NLP.** Clean timestamps/HTML/brackets; word/sentence + lexical diversity; VADER; TF-IDF 5k terms → 100 SVD. Out: `nlp_features.csv`, `tfidf_matrix.npz`.

**Models.** 70/15/15, StandardScaler, 5-fold CV. LR, RF (100), XGB. Sets: text_basic → +vader → text_full (100 SVD) → … → 7_+runtime (genre, budget_log, runtime).

| Task      | Best | F1    | F1(opt) | AUC   |
|-----------|------|:-----:|:-------:|:-----:|
| Commercial| LR   | 0.607 | 0.653   | 0.659 |
| Award     | LR   | 0.397 | **0.508** (CW) | **0.797** |

Award: class-weight beats SMOTE (SMOTE overfits). Importance: vote_count_log, budget_log, runtime (commercial); vote_count_log, runtime, revenue_log (award).

**Limitations.** No revenue for commercial; vote_count post-release; 59% subtitles; English only.

**Next (KT2).** SVM, hyperparameter tuning, class-weight default, ensembles. Targets: commercial F1(opt) 0.72+, award 0.60+. Guides: `../phase_02/`.
