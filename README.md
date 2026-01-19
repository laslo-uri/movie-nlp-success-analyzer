# Movie Success Predictor

**Academic Project - Systems for Research and Data Analysis (SIAP)**

*University of Novi Sad, Faculty of Technical Sciences*

*Students: Laslo Uri (E2 163/2023), Denis Dautović (E2 166/2023), Nikola Janković (E2 130/2025)*

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


## Research Context

This project builds upon existing literature in screenplay analysis and cultural product success prediction:
- Emotional scene detection using subtitle analysis
- Screenplay quality assessment for Oscar prediction
- Big data approaches to bestseller prediction

## Project Structure

```
movie-nlp-success-analyzer/
├── project_proposal/
│   ├── Analiza uticaja filmskih titlova i žanrova na uspeh i priznanja.md
│   ├── Analiza uticaja filmskih titlova i žanrova na uspeh i priznanja.pdf
│   ├── Analysis of the impact of movie titles and genres on success and awards.md
│   └── Analysis of the impact of movie titles and genres on success and awards.pdf
├── research_papers/
│   ├── Detecting Emotional Scenes - Semantic Analysis on Subtitles.md
│   ├── Detecting Emotional Scenes - Semantic Analysis on Subtitles.pdf
│   ├── Screenplay Quality Assessment - Can We Predict Nominations.md
│   ├── Screenplay Quality Assessment - Can We Predict Nominations.pdf
│   ├── Success in Books - Big Data Approach to Bestsellers.md
│   └── Success in Books - Big Data Approach to Bestsellers.pdf
├── README.md
├── 
└── .gitignore
```

## Key Documents

### Project Proposal
- **[English Version](project_proposal/Analysis%20of%20the%20impact%20of%20movie%20titles%20and%20genres%20on%20success%20and%20awards.md)**: Complete project proposal in English
- **[Serbian Version](project_proposal/Analiza%20uticaja%20filmskih%20titlova%20i%20%C5%BEanrova%20na%20uspeh%20i%20priznanja.md)**: Original project proposal in Serbian
- **[English PDF](project_proposal/Analysis%20of%20the%20impact%20of%20movie%20titles%20and%20genres%20on%20success%20and%20awards.pdf)**: English proposal in PDF format
- **[Serbian PDF](project_proposal/Analiza%20uticaja%20filmskih%20titlova%20i%20%C5%BEanrova%20na%20uspeh%20i%20priznanja.pdf)**: Serbian proposal in PDF format

### Research Literature Reviews
- **[Emotional Scene Detection](research_papers/Detecting%20Emotional%20Scenes%20-%20Semantic%20Analysis%20on%20Subtitles.md)**: Analysis of subtitle-based emotion detection ([PDF](research_papers/Detecting%20Emotional%20Scenes%20-%20Semantic%20Analysis%20on%20Subtitles.pdf))
- **[Screenplay Quality Assessment](research_papers/Screenplay%20Quality%20Assessment%20-%20Can%20We%20Predict%20Nominations.md)**: Oscar nomination prediction from screenplays ([PDF](research_papers/Screenplay%20Quality%20Assessment%20-%20Can%20We%20Predict%20Nominations.pdf))
- **[Book Sales Prediction](research_papers/Success%20in%20Books%20-%20Big%20Data%20Approach%20to%20Bestsellers.md)**: Big data approach to predicting book success ([PDF](research_papers/Success%20in%20Books%20-%20Big%20Data%20Approach%20to%20Bestsellers.pdf))

## Academic Requirements

- **Course**: SIAP - Systems for Research and Data Analysis
- **Institution**: University of Novi Sad, Faculty of Technical Sciences
- **Academic Year**: 2025/2026
- **Deliverables**: Complete ML pipeline, comprehensive analysis, and research report

## Getting Started

1. Clone the repository
2. Review the project proposal documents in `project_proposal/`
3. Examine the literature reviews in `research_papers/`
4. Set up Python environment with required dependencies
5. Obtain API keys for TMDB and OpenSubtitles
6. Implement data collection, preprocessing, and modeling pipelines

## Project Status

- **Current Phase**: Literature review and project planning
- **Next Milestones**:
  - Data collection and preprocessing pipeline
  - Feature engineering and baseline model development
  - Model optimization and comparative analysis
  - Final evaluation and research report

## Contributing

This is an academic project developed by students at University of Novi Sad. For academic collaboration or questions, please contact the project team members.

## License

This project is developed as part of an academic course at University of Novi Sad, Faculty of Technical Sciences. All rights reserved to the project authors and the university. Intended for educational and research purposes only.

---

*Contact: Faculty of Technical Sciences, University of Novi Sad*
