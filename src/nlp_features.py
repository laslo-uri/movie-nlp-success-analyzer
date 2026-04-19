"""
NLP feature extraction for movie subtitle analysis.

All text cleaning and feature extraction functions used by notebook 02.
The notebook imports these rather than redefining them inline.
"""

import re
import time
import sys
import numpy as np
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from pathlib import Path
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def clean_subtitle_text(text: str) -> str:
    """Clean subtitle text for feature extraction (strict mode)."""
    if not text or not isinstance(text, str):
        return ""
    text = re.sub(r'\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[[^\]]+\]', '', text)
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r"[^a-zA-Z\s.,!?'\"\-]", '', text)
    return text


def clean_subtitle_text_for_sentiment(text: str) -> str:
    """Clean text for sentiment analysis (keeps more punctuation)."""
    if not text or not isinstance(text, str):
        return ""
    text = re.sub(r'\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[[^\]]+\]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ---------------------------------------------------------------------------
# Basic text statistics
# ---------------------------------------------------------------------------

def extract_basic_text_stats(text: str) -> Dict[str, float]:
    """Word count, sentence count, avg sentence length, char count."""
    if not text or not isinstance(text, str):
        return {'word_count': 0, 'sentence_count': 0, 'avg_sentence_length': 0, 'char_count': 0}
    words = text.split()
    word_count = len(words)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    sentence_count = len(sentences)
    avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
    return {
        'word_count': word_count,
        'sentence_count': sentence_count,
        'avg_sentence_length': avg_sentence_length,
        'char_count': len(text),
    }


# ---------------------------------------------------------------------------
# Lexical diversity
# ---------------------------------------------------------------------------

def extract_lexical_diversity(text: str) -> Dict[str, float]:
    """Type-token ratio, hapax legomena ratio, unique word count."""
    if not text or not isinstance(text, str):
        return {'type_token_ratio': 0, 'hapax_legomena_ratio': 0, 'unique_words': 0}
    words = re.findall(r'\b\w+\b', text.lower())
    if len(words) == 0:
        return {'type_token_ratio': 0, 'hapax_legomena_ratio': 0, 'unique_words': 0}
    unique = set(words)
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    hapax = sum(1 for v in freq.values() if v == 1)
    return {
        'type_token_ratio': len(unique) / len(words),
        'hapax_legomena_ratio': hapax / len(words),
        'unique_words': len(unique),
    }


# ---------------------------------------------------------------------------
# Sentiment (VADER)
# ---------------------------------------------------------------------------

_vader_instance = None

def _get_vader():
    global _vader_instance
    if _vader_instance is not None:
        return _vader_instance
    try:
        _vader_instance = SentimentIntensityAnalyzer()
    except LookupError:
        nltk.download('vader_lexicon', quiet=True)
        _vader_instance = SentimentIntensityAnalyzer()
    return _vader_instance


def extract_sentiment_features(text: str) -> Dict[str, float]:
    """VADER compound/pos/neg/neu + emotional intensity."""
    if not text or not isinstance(text, str):
        return {
            'sentiment_compound': 0, 'sentiment_pos': 0,
            'sentiment_neg': 0, 'sentiment_neu': 0, 'emotional_intensity': 0.0,
        }
    sia = _get_vader()
    cleaned = clean_subtitle_text_for_sentiment(text)
    scores = sia.polarity_scores(cleaned)
    return {
        'sentiment_compound': scores['compound'],
        'sentiment_pos': scores['pos'],
        'sentiment_neg': scores['neg'],
        'sentiment_neu': scores['neu'],
        'emotional_intensity': scores['pos'] + scores['neg'],
    }


# ---------------------------------------------------------------------------
# Punctuation features (Kalyan & Kim: dialogue energy)
# ---------------------------------------------------------------------------

def extract_punctuation_features(text: str) -> Dict[str, float]:
    """Exclamation / question ratios per sentence."""
    if not text or not isinstance(text, str):
        return {'exclamation_ratio': 0.0, 'question_ratio': 0.0}
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    n = len(sentences)
    if n == 0:
        return {'exclamation_ratio': 0.0, 'question_ratio': 0.0}
    return {
        'exclamation_ratio': text.count('!') / n,
        'question_ratio': text.count('?') / n,
    }


# ---------------------------------------------------------------------------
# Sentiment variance (per-sentence compound std)
# ---------------------------------------------------------------------------

def extract_sentiment_variance(text: str) -> Dict[str, float]:
    """Std of per-sentence VADER compound (Chiu et al.)."""
    if not text or not isinstance(text, str):
        return {'sentiment_compound_std': 0.0}
    sia = _get_vader()
    cleaned = clean_subtitle_text_for_sentiment(text)
    sentences = [s.strip() for s in re.split(r'[.!?]+', cleaned) if len(s.strip()) > 2]
    if len(sentences) < 2:
        return {'sentiment_compound_std': 0.0}
    compounds = [sia.polarity_scores(s)['compound'] for s in sentences]
    return {'sentiment_compound_std': float(np.std(compounds))}


# ---------------------------------------------------------------------------
# Readability features
# ---------------------------------------------------------------------------

def extract_readability(text: str) -> Dict[str, float]:
    """Average word length and std of sentence lengths."""
    if not text or not isinstance(text, str):
        return {'avg_word_length': 0.0, 'sentence_length_std': 0.0}
    words = text.split()
    if len(words) == 0:
        return {'avg_word_length': 0.0, 'sentence_length_std': 0.0}
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    sent_lens = [len(s.split()) for s in sentences]
    return {
        'avg_word_length': float(np.mean([len(w) for w in words])),
        'sentence_length_std': float(np.std(sent_lens)) if len(sent_lens) > 1 else 0.0,
    }


def extract_textblob_features(text: str) -> Dict[str, float]:
    """TextBlob polarity and subjectivity (returns zeros if textblob unavailable)."""
    try:
        from textblob import TextBlob
    except ImportError:
        return {'textblob_polarity': 0.0, 'textblob_subjectivity': 0.0}
    if not text or not isinstance(text, str) or len(text.split()) < 5:
        return {'textblob_polarity': 0.0, 'textblob_subjectivity': 0.0}
    try:
        blob = TextBlob(text)
        return {
            'textblob_polarity': blob.sentiment.polarity,
            'textblob_subjectivity': blob.sentiment.subjectivity,
        }
    except Exception:
        return {'textblob_polarity': 0.0, 'textblob_subjectivity': 0.0}


# ---------------------------------------------------------------------------
# Batch processing: extract ALL features for a list of movie IDs
# ---------------------------------------------------------------------------

def _fmt_eta(seconds: float) -> str:
    """Format seconds into a human-readable ETA string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    if m < 60:
        return f"{m}m {s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}m"


def process_subtitle_batch(movie_ids: List[int], subtitle_dir: Path,
                           progress_every: int = 100) -> pd.DataFrame:
    """
    Process subtitle files and extract all NLP features in one pass.

    Returns a DataFrame with one row per successfully processed movie.
    """
    total = len(movie_ids)
    rows = []
    ok, err = 0, 0
    t_start = time.time()

    for i, mid in enumerate(movie_ids):
        try:
            path = subtitle_dir / f"{mid}.txt"
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                raw = f.read()
            cleaned = clean_subtitle_text(raw)
            row = {
                'id': mid,
                'raw_text_length': len(raw),
                'cleaned_text_length': len(cleaned),
                **extract_basic_text_stats(cleaned),
                **extract_lexical_diversity(cleaned),
                **extract_sentiment_features(raw),
                **extract_punctuation_features(cleaned),
                **extract_sentiment_variance(raw),
                **extract_readability(cleaned),
                **extract_textblob_features(cleaned),
            }
            rows.append(row)
            ok += 1
        except Exception as e:
            print(f"  Error on movie {mid}: {e}")
            err += 1

        done = i + 1
        if done % progress_every == 0 or done == total:
            elapsed = time.time() - t_start
            pct = done / total * 100
            rate = done / elapsed if elapsed > 0 else 0
            eta = (total - done) / rate if rate > 0 else 0
            print(f"  {done:,}/{total:,}  ({pct:5.1f}%)  "
                  f"{rate:.1f} files/s  "
                  f"ETA {_fmt_eta(eta)}")
            sys.stdout.flush()

    elapsed = time.time() - t_start
    print(f"Done: {ok:,} processed, {err:,} errors  "
          f"({_fmt_eta(elapsed)} total)")
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# TF-IDF
# ---------------------------------------------------------------------------

def create_tfidf_vectorizer(corpus: List[str],
                            max_features: int = 5000) -> Tuple[TfidfVectorizer, object]:
    """Fit a TF-IDF vectorizer. Returns (vectorizer, sparse matrix)."""
    vec = TfidfVectorizer(
        max_features=max_features, stop_words='english',
        min_df=5, max_df=0.8, ngram_range=(1, 2),
    )
    matrix = vec.fit_transform(corpus)
    sparsity = 1.0 - (matrix.nnz / (matrix.shape[0] * matrix.shape[1]))
    print(f"TF-IDF: {matrix.shape[0]:,} docs x {matrix.shape[1]:,} terms, "
          f"sparsity {sparsity:.1%}")
    return vec, matrix


def get_top_tfidf_terms(vec: TfidfVectorizer, matrix, top_n: int = 20):
    """Top terms by average TF-IDF score."""
    names = vec.get_feature_names_out()
    avg = np.array(matrix.mean(axis=0)).flatten()
    idx = np.argsort(avg)[-top_n:][::-1]
    return [(names[i], avg[i]) for i in idx]
