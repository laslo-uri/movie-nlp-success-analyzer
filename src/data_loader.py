"""
Data loading and preprocessing utilities for the Movie NLP Success Analyzer.

This module provides functions for:
- Loading CSV datasets
- Merging datasets with different sources
- Parsing and encoding categorical features
- Creating feature matrices for modeling
"""

import pandas as pd
import numpy as np
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def load_main_dataset(data_dir: Path) -> pd.DataFrame:
    """
    Load the main movie dataset.

    Args:
        data_dir: Path to the processed data directory

    Returns:
        DataFrame with movie data
    """
    df = pd.read_csv(data_dir / 'final_movie_list.csv')
    print(f"Loaded main dataset: {len(df):,} movies")

    # Parse genres
    df['genres_list'] = df['genres'].apply(safe_literal_eval)

    # Compute derived features
    df['roi'] = np.where(df['budget'] > 0, df['revenue'] / df['budget'], np.nan)

    return df


def load_nlp_features(data_dir: Path) -> pd.DataFrame:
    """
    Load NLP features extracted from subtitles.

    Args:
        data_dir: Path to the processed data directory

    Returns:
        DataFrame with NLP features per movie
    """
    nlp_df = pd.read_csv(data_dir / 'nlp_features.csv')
    print(f"Loaded NLP features: {len(nlp_df):,} movies with subtitles")
    return nlp_df


def merge_datasets(main_df: pd.DataFrame, nlp_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge main dataset with NLP features.

    Args:
        main_df: Main movie dataset
        nlp_df: NLP features dataset

    Returns:
        Merged DataFrame
    """
    merged_df = main_df.merge(nlp_df, on='id', how='left')
    print(f"Merged dataset: {len(merged_df):,} movies")
    print(f"Movies with NLP features: {merged_df['word_count'].notna().sum():,}")
    return merged_df


def safe_literal_eval(x) -> list:
    """
    Safely evaluate string representation of list.

    Args:
        x: String or value to evaluate

    Returns:
        List if successful, empty list otherwise
    """
    try:
        return ast.literal_eval(x) if isinstance(x, str) else []
    except:
        return []


def get_unique_genres(df: pd.DataFrame) -> List[str]:
    """
    Extract unique genres from dataset.

    Args:
        df: DataFrame with genres_list column

    Returns:
        Sorted list of unique genres
    """
    all_genres = [genre for genres_list in df['genres_list'] for genre in genres_list]
    unique_genres = sorted(list(set(all_genres)))
    print(f"Found {len(unique_genres)} unique genres: {', '.join(unique_genres)}")
    return unique_genres


def create_genre_dummies(df: pd.DataFrame, unique_genres: List[str]) -> pd.DataFrame:
    """
    Create dummy variables for genres.

    Args:
        df: DataFrame with genres_list column
        unique_genres: List of unique genres

    Returns:
        DataFrame with genre dummy columns added
    """
    for genre in unique_genres:
        df[f'genre_{genre.lower()}'] = df['genres_list'].apply(lambda x: genre in x)

    genre_cols = [f'genre_{genre.lower()}' for genre in unique_genres]
    print(f"Created {len(genre_cols)} genre dummy columns")
    return df


def create_feature_sets(df: pd.DataFrame, unique_genres: List[str]) -> Dict[str, List[str]]:
    """
    Define feature sets for modeling.

    Args:
        df: DataFrame with all features
        unique_genres: List of unique genres

    Returns:
        Dictionary of feature set names to column lists
    """
    # Basic features (always available)
    basic_features = ['budget', 'revenue', 'runtime', 'vote_count']

    # Genre features
    genre_features = [f'genre_{genre.lower()}' for genre in unique_genres]

    # NLP features (only for movies with subtitles)
    nlp_features = [
        'word_count', 'sentence_count', 'avg_sentence_length', 'char_count',
        'type_token_ratio', 'hapax_legomena_ratio', 'unique_words',
        'sentiment_compound', 'sentiment_pos', 'sentiment_neg', 'sentiment_neu'
    ]

    # Log-transformed versions
    log_features = ['basic_log', 'basic_genre_log', 'basic_genre_nlp_log']
    feature_sets = {
        'basic': basic_features,
        'basic_genre': basic_features + genre_features,
        'basic_genre_nlp': basic_features + genre_features + nlp_features,
        'basic_log': ['budget_log', 'revenue_log', 'runtime', 'vote_count_log'],
        'basic_genre_log': ['budget_log', 'revenue_log', 'runtime', 'vote_count_log'] + genre_features,
        'basic_genre_nlp_log': ['budget_log', 'revenue_log', 'runtime', 'vote_count_log'] + genre_features + nlp_features
    }

    # Add log-transformed features to dataframe
    df = df.copy()
    df['budget_log'] = np.log10(df['budget'].replace(0, np.nan))
    df['revenue_log'] = np.log10(df['revenue'].replace(0, np.nan))
    df['vote_count_log'] = np.log10(df['vote_count'].replace(0, np.nan) + 1)

    print("Feature sets defined:")
    for name, features in feature_sets.items():
        available = sum(1 for f in features if f in df.columns and df[f].notna().any())
        print(f"  {name}: {len(features)} features ({available} available)")

    return feature_sets, df


def get_modeling_subset(df: pd.DataFrame, feature_set: List[str],
                       target: str) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Create modeling subset with required features and target.

    Args:
        df: Full DataFrame
        feature_set: List of feature column names
        target: Target column name

    Returns:
        Tuple of (features DataFrame, target Series)
    """
    # Define modeling criteria
    modeling_criteria = (
        (df['budget'] > 0) &
        (df['revenue'] > 0) &
        (df['runtime'] > 0)
    )

    # Filter to movies meeting criteria
    modeling_df = df[modeling_criteria].copy()

    # Get available features and target
    available_features = [f for f in feature_set if f in modeling_df.columns]
    modeling_subset = modeling_df[available_features + [target]].dropna()

    X = modeling_subset[available_features]
    y = modeling_subset[target]

    print(f"Modeling subset for {target}:")
    print(f"  Samples: {len(modeling_subset):,} ({len(modeling_subset)/len(df)*100:.1f}%)")
    print(f"  Features: {len(available_features)}")
    print(f"  Class distribution: {y.value_counts().to_dict()}")
    print(f"  Class ratio: {y.mean():.3f}")

    return X, y


def load_and_prepare_data(data_dir: Path) -> Tuple[pd.DataFrame, List[str], Dict[str, List[str]]]:
    """
    Complete data loading and preparation pipeline.

    Args:
        data_dir: Path to processed data directory

    Returns:
        Tuple of (prepared DataFrame, unique genres, feature sets)
    """
    # Load datasets
    main_df = load_main_dataset(data_dir)
    nlp_df = load_nlp_features(data_dir)
    merged_df = merge_datasets(main_df, nlp_df)

    # Process genres
    unique_genres = get_unique_genres(merged_df)
    merged_df = create_genre_dummies(merged_df, unique_genres)

    # Create feature sets
    feature_sets, prepared_df = create_feature_sets(merged_df, unique_genres)

    return prepared_df, unique_genres, feature_sets