# Movie Success Predictor

**Academic Project - Systems for Research and Data Analysis (SIAP)**

*University of Novi Sad, Faculty of Technical Sciences*

*Students: Laslo Uri (E2 163/2023), Denis Dautović (E2 166/2023), Nikola Janković (E2130/2025)*

## Project Overview

A comprehensive machine learning system that analyzes movie titles, subtitles, and genres to predict commercial success and award nominations. Using Natural Language Processing (NLP) techniques on subtitle data combined with financial and genre information, the system classifies movies as successful/unsuccessful and predicts Oscar nomination probability.

## Objectives

- **Binary Classification**: Predict movie commercial success based on ROI (Return on Investment) metrics
- **Award Prediction**: Predict probability of Oscar nominations using genre and title characteristics
- **Feature Analysis**: Identify which subtitle characteristics (sentiment, lexical diversity, genre) most influence movie success
- **NLP Integration**: Combine textual analysis with financial and categorical data for robust predictions

## Methodology

### Data Sources
- **TMDB API**: Movie metadata (title, year, genres, budget, box office revenue)
- **OpenSubtitles API**: Movie subtitle texts for NLP analysis
- **Academy Awards Database**: Historical Oscar nomination data

### Feature Engineering
- **Genre Classification**: Binary encoding of movie genres (action, drama, comedy, horror, etc.)
- **NLP Features**: TF-IDF vectors, sentiment analysis, lexical diversity metrics from subtitles
- **Financial Features**: Log-transformed budget and ROI calculations

### Machine Learning Pipeline
1. **Data Collection**: Aggregate movie data from multiple APIs
2. **Preprocessing**: Clean subtitles, extract features, handle missing data
3. **Modeling**: Random Forest and XGBoost classifiers with SMOTE for class imbalance
4. **Evaluation**: Stratified cross-validation with F1-score and AUC-ROC metrics

## Technologies Used

- **Programming Language**: Python 3.10+
- **Data Processing**: Pandas, NumPy
- **Machine Learning**: Scikit-learn, XGBoost, Imbalanced-learn
- **NLP**: SpaCy, NLTK, Gensim
- **Visualization**: Matplotlib, Seaborn, Plotly
- **Development Environment**: Jupyter Notebook

## Dataset

- **Scope**: 5,000+ movies (2000-2024) with complete financial and subtitle data
- **Target Variables**:
  - Commercial Success: Binary classification (ROI ≥ 2.0)
  - Oscar Nomination: Binary classification (nominated/not nominated)
- **Class Imbalance**: Expected higher proportion of unsuccessful/non-nominated movies

## Expected Outcomes

- Accurate prediction models for movie success and award nominations
- Insights into how subtitle content and genre influence box office performance
- Comparative analysis of different ML algorithms for textual data
- Practical tool for film industry decision-making

## Project Structure

```
movie-success-predictor/
├── data/
│   ├── raw/                 # Raw API data
│   └── processed/           # Cleaned datasets
├── notebooks/
│   ├── 01_data_collection.ipynb
│   ├── 02_eda_analysis.ipynb
│   ├── 03_feature_engineering.ipynb
│   └── 04_modeling.ipynb
├── src/
│   ├── data_processing.py
│   ├── feature_extraction.py
│   ├── modeling.py
│   └── utils.py
├── models/                  # Trained models
├── reports/                 # Analysis reports
├── requirements.txt
└── README.md
```

## Research Context

This project builds upon existing literature in screenplay analysis and cultural product success prediction:
- Emotional scene detection using subtitle analysis
- Screenplay quality assessment for Oscar prediction
- Big data approaches to bestseller prediction

## Academic Requirements

- **Course**: SIAP - Systems for Research and Data Analysis
- **Institution**: University of Novi Sad, Faculty of Technical Sciences
- **Academic Year**: 2024/2025
- **Deliverables**: Complete ML pipeline, comprehensive analysis, and research report

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Obtain API keys for TMDB and OpenSubtitles
4. Run data collection notebook
5. Execute feature engineering and modeling pipelines

## License

This project is developed as part of an academic course and is intended for educational purposes.

---

*For questions or collaboration inquiries, please contact the project team members.*
