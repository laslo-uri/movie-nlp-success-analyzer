# Movie NLP Success Analyzer

**Academic Project — SIAP (Systems for Research and Data Analysis)**

*University of Novi Sad, Faculty of Technical Sciences*

*Laslo Uri (E2 163/2023) · Denis Dautovic (E2 166/2023) · Nikola Jankovic (E2 130/2025)*

---

## Overview

Predicting movie commercial success and Oscar nomination probability by combining **NLP analysis of subtitle texts** with financial and genre metadata. The system uses TF-IDF, sentiment analysis, and lexical diversity features extracted from subtitles alongside TMDB financial data, fed into Random Forest and XGBoost classifiers.

## Objectives

| Goal | Approach |
|------|----------|
| **Commercial success prediction** | Binary classification based on ROI ≥ 2.0 |
| **Award nomination prediction** | Predict Oscar nomination probability from genre + title features |
| **Feature importance analysis** | Identify which subtitle characteristics most influence success |
| **NLP + metadata fusion** | Combine textual features with financial and categorical data |

## Data Sources

- **TMDB API** — movie metadata: title, year, genres, budget, revenue (76 yearly CSV files, 1950–2025)
- **OpenSubtitles API** — subtitle texts for NLP feature extraction (~7,400 subtitle files collected)
- **Academy Awards Database** — historical Oscar nomination and win data

## ML Pipeline

```
TMDB metadata ─┐
                ├─▶ Preprocessing ─▶ Feature Engineering ─▶ Modeling ─▶ Evaluation
Subtitle texts ─┘       │                    │                  │            │
                    Clean text          TF-IDF vectors     Random Forest   F1-score
                    Handle nulls        Sentiment scores   XGBoost         AUC-ROC
                    Log-transform $     Lexical diversity  SMOTE balance   Cross-val
                                        Genre encoding
```

## Tech Stack

| Category | Libraries |
|----------|-----------|
| Data processing | Pandas, NumPy |
| Machine learning | Scikit-learn, XGBoost, Imbalanced-learn |
| NLP | SpaCy, NLTK, Gensim |
| Visualization | Matplotlib, Seaborn, Plotly |
| APIs | Requests, python-dotenv |

## Project Structure

```
movie-nlp-success-analyzer/
├── project/                          ← Main codebase & data
│   ├── data/
│   │   ├── raw/
│   │   │   ├── tmdb_metadata/        76 yearly CSVs (movies_1950–2025.csv)
│   │   │   ├── subtitles/            ~7,400 subtitle .txt files by TMDB ID
│   │   │   ├── awards/               Award ceremony data
│   │   │   └── oscars/               Oscar nomination data
│   │   ├── processed/                Cleaned & merged datasets
│   │   │   ├── final_movie_list.csv  Main dataset with labels
│   │   │   ├── tmdb_enriched.csv     Enriched TMDB data
│   │   │   ├── tmdb_combined.csv     All yearly TMDB CSVs merged
│   │   │   ├── awards_master_partial.csv
│   │   │   ├── awards_minor_categories.csv
│   │   │   └── ...
│   │   └── external/                 Third-party data
│   ├── reports/
│   │   └── figures/                  Generated visualizations
│   ├── project_setup.py              Scaffold script (initial setup)
│   └── requirements.txt              Python dependencies
│
├── project_proposal/                 ← Proposal documents (EN + SR)
│   ├── Analysis of the impact of movie titles and genres on success and awards.md
│   └── Analiza uticaja filmskih titlova i žanrova na uspeh i priznanja.md
│
├── research_papers/                  ← Literature review summaries
│   ├── Detecting Emotional Scenes - Semantic Analysis on Subtitles.md
│   ├── Screenplay Quality Assessment - Can We Predict Nominations.md
│   └── Success in Books - Big Data Approach to Bestsellers.md
│
├── README.md                         ← You are here
└── .gitignore
```

## Getting Started

```bash
# 1. Clone and enter
git clone https://github.com/<your-username>/movie-nlp-success-analyzer.git
cd movie-nlp-success-analyzer

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate    # macOS/Linux

# 3. Install dependencies
pip install -r project/requirements.txt

# 4. Set up API keys
cp project/.env.example project/.env
# Edit .env with your TMDB and OpenSubtitles credentials

# 5. Download SpaCy model
python -m spacy download en_core_web_sm
```

## Project Status

- [x] Literature review and project proposal
- [x] TMDB metadata collection (76 yearly files, 1950–2025)
- [x] Subtitle download pipeline (~7,400 movies)
- [x] Data cleaning and enrichment
- [x] Exploratory data analysis and visualizations
- [ ] NLP feature extraction (TF-IDF, sentiment, lexical diversity)
- [ ] Model training and evaluation
- [ ] Final report

## Documents

### Proposal
- [English](project_proposal/Analysis%20of%20the%20impact%20of%20movie%20titles%20and%20genres%20on%20success%20and%20awards.md) · [PDF](project_proposal/Analysis%20of%20the%20impact%20of%20movie%20titles%20and%20genres%20on%20success%20and%20awards.pdf)
- [Serbian](project_proposal/Analiza%20uticaja%20filmskih%20titlova%20i%20%C5%BEanrova%20na%20uspeh%20i%20priznanja.md) · [PDF](project_proposal/Analiza%20uticaja%20filmskih%20titlova%20i%20%C5%BEanrova%20na%20uspeh%20i%20priznanja.pdf)

### Literature Reviews
- [Emotional Scene Detection via Subtitle Analysis](research_papers/Detecting%20Emotional%20Scenes%20-%20Semantic%20Analysis%20on%20Subtitles.md)
- [Screenplay Quality Assessment for Oscar Prediction](research_papers/Screenplay%20Quality%20Assessment%20-%20Can%20We%20Predict%20Nominations.md)
- [Big Data Approach to Bestseller Prediction](research_papers/Success%20in%20Books%20-%20Big%20Data%20Approach%20to%20Bestsellers.md)

## License

Academic project — University of Novi Sad, Faculty of Technical Sciences. For educational and research purposes only.
