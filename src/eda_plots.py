"""
EDA plotting functions for the Movie NLP Success Analyzer (Phase 01).

All plot functions take a DataFrame and a figures directory path;
they save PNGs and optionally display. Used by 01_eda.ipynb to keep
the notebook concise while most code lives in Python modules.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy.stats import pointbiserialr
from typing import Optional, Set


def _ensure_temporal(df: pd.DataFrame) -> pd.DataFrame:
    """Add release_year and decade if missing (in-place on copy)."""
    out = df.copy()
    if 'release_year' not in out.columns:
        out['release_year'] = pd.to_datetime(out['release_date'], errors='coerce').dt.year
    if 'decade' not in out.columns:
        out['decade'] = (out['release_year'] // 10) * 10
    return out


def plot_target_distributions(df: pd.DataFrame, figures_dir: Path) -> None:
    """Bar plots for is_commercial, is_award_winner, is_popular."""
    targets = ['is_commercial', 'is_award_winner', 'is_popular']
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, target in zip(axes, targets):
        counts = df[target].value_counts()
        bars = ax.bar(counts.index.astype(str), counts.values, color=['#e74c3c', '#2ecc71'])
        ax.set_title(target, fontsize=14, fontweight='bold')
        ax.set_xlabel('Value')
        ax.set_ylabel('Count')
        for bar, count in zip(bars, counts.values):
            pct = count / len(df) * 100
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                    f'{count:,}\n({pct:.1f}%)', ha='center', va='bottom', fontsize=10)
    plt.suptitle('Target Variable Distributions', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(figures_dir / '01_eda_01_target_distributions.png', dpi=150, bbox_inches='tight')
    plt.show()


def plot_financial_distributions(df: pd.DataFrame, figures_dir: Path) -> pd.DataFrame:
    """Histograms for budget, revenue, ROI (log where appropriate). Returns df_financial for reuse."""
    df_financial = df[(df['budget'] > 0) & (df['revenue'] > 0)].copy()
    print(f"Movies with budget > 0 AND revenue > 0: {len(df_financial):,} ({len(df_financial)/len(df)*100:.1f}%)")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    axes[0].hist(np.log10(df_financial['budget']), bins=50, color='steelblue', edgecolor='white')
    axes[0].set_title('Budget Distribution (log₁₀)', fontweight='bold')
    axes[0].set_xlabel('log₁₀(Budget USD)')
    axes[0].set_ylabel('Count')
    axes[1].hist(np.log10(df_financial['revenue']), bins=50, color='coral', edgecolor='white')
    axes[1].set_title('Revenue Distribution (log₁₀)', fontweight='bold')
    axes[1].set_xlabel('log₁₀(Revenue USD)')
    roi_clipped = df_financial['roi'].clip(upper=df_financial['roi'].quantile(0.99))
    axes[2].hist(roi_clipped, bins=50, color='seagreen', edgecolor='white')
    axes[2].set_title('ROI Distribution (clipped at 99th pctl)', fontweight='bold')
    axes[2].set_xlabel('ROI (Revenue / Budget)')
    plt.tight_layout()
    plt.savefig(figures_dir / '01_eda_02_financial_distributions.png', dpi=150, bbox_inches='tight')
    plt.show()
    return df_financial


def plot_budget_vs_revenue(df_financial: pd.DataFrame, figures_dir: Path) -> None:
    """Scatter budget vs revenue colored by commercial success with ROI=2 line."""
    fig, ax = plt.subplots(figsize=(10, 8))
    scatter = ax.scatter(
        np.log10(df_financial['budget']),
        np.log10(df_financial['revenue']),
        c=df_financial['is_commercial'].astype(int),
        cmap='RdYlGn', alpha=0.4, s=15
    )
    budget_range = np.linspace(df_financial['budget'].min(), df_financial['budget'].max(), 100)
    ax.plot(np.log10(budget_range), np.log10(2 * budget_range),
            'k--', linewidth=2, label='ROI = 2.0 (commercial threshold)')
    ax.set_xlabel('log₁₀(Budget)', fontsize=13)
    ax.set_ylabel('log₁₀(Revenue)', fontsize=13)
    ax.set_title('Budget vs Revenue (colored by commercial success)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    plt.colorbar(scatter, label='Commercial Success')
    plt.tight_layout()
    plt.savefig(figures_dir / '01_eda_03_budget_vs_revenue.png', dpi=150, bbox_inches='tight')
    plt.show()


def plot_financial_boxplots(df_financial: pd.DataFrame, figures_dir: Path) -> None:
    """Boxplots of budget and revenue by commercial success."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, col, title in zip(axes, ['budget', 'revenue'], ['Budget', 'Revenue']):
        data_success = df_financial.loc[df_financial['is_commercial'] == True, col]
        data_fail = df_financial.loc[df_financial['is_commercial'] == False, col]
        ax.boxplot([np.log10(data_fail), np.log10(data_success)],
                   labels=['Not Commercial', 'Commercial'],
                   patch_artist=True,
                   boxprops=dict(facecolor='lightblue'))
        ax.set_title(f'{title} by Commercial Success (log₁₀)', fontweight='bold')
        ax.set_ylabel(f'log₁₀({title} USD)')
    plt.tight_layout()
    plt.savefig(figures_dir / '01_eda_04_financial_boxplots.png', dpi=150, bbox_inches='tight')
    plt.show()


def plot_genre_frequency(df: pd.DataFrame, figures_dir: Path) -> pd.Series:
    """Bar chart of genre counts. Returns genre_counts for reuse."""
    all_genres = [g for genres in df['genres_list'] for g in genres]
    genre_counts = pd.Series(all_genres).value_counts()
    print(f"Unique genres: {len(genre_counts)}")
    fig, ax = plt.subplots(figsize=(14, 6))
    genre_counts.plot(kind='bar', ax=ax, color='steelblue', edgecolor='white')
    ax.set_title('Genre Frequency', fontsize=14, fontweight='bold')
    ax.set_xlabel('Genre')
    ax.set_ylabel('Number of Movies')
    ax.tick_params(axis='x', rotation=45)
    for i, (val, name) in enumerate(zip(genre_counts.values, genre_counts.index)):
        ax.text(i, val + 30, f'{val:,}', ha='center', va='bottom', fontsize=8)
    plt.tight_layout()
    plt.savefig(figures_dir / '01_eda_05_genre_frequency.png', dpi=150, bbox_inches='tight')
    plt.show()
    return genre_counts


def plot_genre_success_rates(df_financial: pd.DataFrame, unique_genres: list, figures_dir: Path) -> None:
    """Horizontal bar chart of commercial success rate by genre."""
    genre_success = []
    for genre in unique_genres:
        subset = df_financial[df_financial['genres_list'].apply(lambda x: genre in x)]
        if len(subset) > 0:
            genre_success.append({
                'genre': genre,
                'total': len(subset),
                'commercial_rate': subset['is_commercial'].mean()
            })
    genre_success_df = pd.DataFrame(genre_success).sort_values('commercial_rate', ascending=True)
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(genre_success_df['genre'], genre_success_df['commercial_rate'],
                   color='coral', edgecolor='white')
    ax.axvline(x=df_financial['is_commercial'].mean(), color='black',
               linestyle='--', linewidth=1.5, label='Overall average')
    ax.set_xlabel('Commercial Success Rate', fontsize=13)
    ax.set_title('Commercial Success Rate by Genre', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    for bar, rate in zip(bars, genre_success_df['commercial_rate']):
        ax.text(rate + 0.005, bar.get_y() + bar.get_height()/2,
                f'{rate:.1%}', va='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(figures_dir / '01_eda_06_genre_success_rates.png', dpi=150, bbox_inches='tight')
    plt.show()


def plot_genre_cooccurrence(df: pd.DataFrame, unique_genres: list, figures_dir: Path) -> None:
    """Heatmap of genre co-occurrence (diagonal zeroed)."""
    genre_matrix = pd.DataFrame(0, index=unique_genres, columns=unique_genres)
    for genres in df['genres_list']:
        for g1 in genres:
            for g2 in genres:
                if g1 in genre_matrix.index and g2 in genre_matrix.columns:
                    genre_matrix.loc[g1, g2] += 1
    for i in genre_matrix.index:
        if i in genre_matrix.columns:
            genre_matrix.loc[i, i] = 0
    fig, ax = plt.subplots(figsize=(14, 11))
    sns.heatmap(genre_matrix, annot=True, fmt='d', cmap='YlOrRd',
                linewidths=0.5, ax=ax, annot_kws={'size': 7})
    ax.set_title('Genre Co-occurrence Matrix', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(figures_dir / '01_eda_07_genre_cooccurrence.png', dpi=150, bbox_inches='tight')
    plt.show()


def plot_temporal_production(df: pd.DataFrame, figures_dir: Path) -> None:
    """Movies per year and per decade. Expects release_year and decade (added if missing)."""
    df = _ensure_temporal(df)
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    year_counts = df['release_year'].value_counts().sort_index()
    axes[0].plot(year_counts.index, year_counts.values, color='steelblue', linewidth=1.5)
    axes[0].fill_between(year_counts.index, year_counts.values, alpha=0.3, color='steelblue')
    axes[0].set_title('Movies Released per Year', fontweight='bold')
    axes[0].set_xlabel('Year')
    axes[0].set_ylabel('Number of Movies')
    decade_counts = df['decade'].value_counts().sort_index()
    axes[1].bar(decade_counts.index.astype(str), decade_counts.values,
                color='coral', edgecolor='white', width=0.7)
    axes[1].set_title('Movies per Decade', fontweight='bold')
    axes[1].set_xlabel('Decade')
    axes[1].set_ylabel('Number of Movies')
    axes[1].tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(figures_dir / '01_eda_08_temporal_production.png', dpi=150, bbox_inches='tight')
    plt.show()


def plot_temporal_financials(df: pd.DataFrame, figures_dir: Path) -> None:
    """Avg and median budget/revenue by decade."""
    df = _ensure_temporal(df)
    decade_financial = df[(df['budget'] > 0) & (df['revenue'] > 0)].groupby('decade').agg(
        avg_budget=('budget', 'mean'),
        avg_revenue=('revenue', 'mean'),
        median_budget=('budget', 'median'),
        median_revenue=('revenue', 'median')
    ).dropna()
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    axes[0].plot(decade_financial.index, decade_financial['avg_budget'] / 1e6, 'o-',
                 label='Avg Budget', color='steelblue', linewidth=2)
    axes[0].plot(decade_financial.index, decade_financial['avg_revenue'] / 1e6, 's-',
                 label='Avg Revenue', color='coral', linewidth=2)
    axes[0].set_title('Average Budget & Revenue by Decade', fontweight='bold')
    axes[0].set_xlabel('Decade')
    axes[0].set_ylabel('USD (Millions)')
    axes[0].legend()
    axes[1].plot(decade_financial.index, decade_financial['median_budget'] / 1e6, 'o-',
                 label='Median Budget', color='steelblue', linewidth=2)
    axes[1].plot(decade_financial.index, decade_financial['median_revenue'] / 1e6, 's-',
                 label='Median Revenue', color='coral', linewidth=2)
    axes[1].set_title('Median Budget & Revenue by Decade', fontweight='bold')
    axes[1].set_xlabel('Decade')
    axes[1].set_ylabel('USD (Millions)')
    axes[1].legend()
    plt.tight_layout()
    plt.savefig(figures_dir / '01_eda_09_temporal_financials.png', dpi=150, bbox_inches='tight')
    plt.show()


def plot_temporal_success_rates(df: pd.DataFrame, figures_dir: Path) -> pd.DataFrame:
    """Success rates by decade. Returns decade_rates for display in notebook."""
    df = _ensure_temporal(df)
    decade_rates = df.groupby('decade').agg(
        commercial_rate=('is_commercial', 'mean'),
        award_rate=('is_award_winner', 'mean'),
        popular_rate=('is_popular', 'mean'),
        count=('id', 'count')
    ).dropna()
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(decade_rates.index, decade_rates['commercial_rate'], 'o-',
            label='Commercial', linewidth=2, markersize=8)
    ax.plot(decade_rates.index, decade_rates['award_rate'], 's-',
            label='Award Winner', linewidth=2, markersize=8)
    ax.plot(decade_rates.index, decade_rates['popular_rate'], '^-',
            label='Popular', linewidth=2, markersize=8)
    ax.set_title('Success Rates by Decade', fontsize=14, fontweight='bold')
    ax.set_xlabel('Decade')
    ax.set_ylabel('Rate')
    ax.legend(fontsize=11)
    ax.set_ylim(0, 1)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(figures_dir / '01_eda_10_temporal_success_rates.png', dpi=150, bbox_inches='tight')
    plt.show()
    return decade_rates


def plot_runtime_votes_distributions(df: pd.DataFrame, figures_dir: Path) -> None:
    """Runtime and vote_count distributions."""
    df_runtime = df[df['runtime'] > 0]
    df_votes = df[df['vote_count'] > 0]
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    axes[0].hist(df_runtime['runtime'], bins=60, color='mediumpurple', edgecolor='white')
    axes[0].axvline(df_runtime['runtime'].median(), color='black', linestyle='--',
                    label=f'Median: {df_runtime["runtime"].median():.0f} min')
    axes[0].set_title('Runtime Distribution', fontweight='bold')
    axes[0].set_xlabel('Runtime (minutes)')
    axes[0].set_ylabel('Count')
    axes[0].set_xlim(0, 250)
    axes[0].legend()
    axes[1].hist(np.log10(df_votes['vote_count']), bins=50, color='goldenrod', edgecolor='white')
    axes[1].axvline(np.log10(df_votes['vote_count'].median()), color='black', linestyle='--',
                    label=f'Median: {df_votes["vote_count"].median():.0f}')
    axes[1].set_title('Vote Count Distribution (log₁₀)', fontweight='bold')
    axes[1].set_xlabel('log₁₀(Vote Count)')
    axes[1].set_ylabel('Count')
    axes[1].legend()
    plt.tight_layout()
    plt.savefig(figures_dir / '01_eda_11_runtime_votes_distributions.png', dpi=150, bbox_inches='tight')
    plt.show()


def plot_runtime_votes_by_success(df: pd.DataFrame, figures_dir: Path) -> None:
    """Runtime and vote_count by commercial success."""
    df_model = df[(df['budget'] > 0) & (df['revenue'] > 0) & (df['runtime'] > 0)].copy()
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for label, color in [(True, '#2ecc71'), (False, '#e74c3c')]:
        subset = df_model[df_model['is_commercial'] == label]
        axes[0].hist(subset['runtime'], bins=40, alpha=0.6, label=str(label),
                     color=color, edgecolor='white')
    axes[0].set_title('Runtime by Commercial Success', fontweight='bold')
    axes[0].set_xlabel('Runtime (minutes)')
    axes[0].set_ylabel('Count')
    axes[0].set_xlim(0, 250)
    axes[0].legend(title='is_commercial')
    for label, color in [(True, '#2ecc71'), (False, '#e74c3c')]:
        subset = df_model[df_model['is_commercial'] == label]
        axes[1].hist(np.log10(subset['vote_count'].clip(lower=1)), bins=40, alpha=0.6,
                    label=str(label), color=color, edgecolor='white')
    axes[1].set_title('Vote Count by Commercial Success (log₁₀)', fontweight='bold')
    axes[1].set_xlabel('log₁₀(Vote Count)')
    axes[1].set_ylabel('Count')
    axes[1].legend(title='is_commercial')
    plt.tight_layout()
    plt.savefig(figures_dir / '01_eda_12_runtime_votes_by_success.png', dpi=150, bbox_inches='tight')
    plt.show()


def plot_missing_data_heatmap(df: pd.DataFrame, figures_dir: Path) -> None:
    """Correlation of zero-value indicators (budget, revenue, runtime, vote_count)."""
    missing_matrix = df[['budget', 'revenue', 'runtime', 'vote_count']].copy()
    missing_matrix = (missing_matrix == 0).astype(int)
    missing_matrix.columns = ['budget=0', 'revenue=0', 'runtime=0', 'vote_count=0']
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(missing_matrix.corr(), annot=True, cmap='YlOrRd', fmt='.2f',
                linewidths=0.5, ax=ax, vmin=0, vmax=1)
    ax.set_title('Zero-Value Co-occurrence (budget, revenue, runtime, votes)', fontweight='bold')
    plt.tight_layout()
    plt.savefig(figures_dir / '01_eda_13_missing_data_heatmap.png', dpi=150, bbox_inches='tight')
    plt.show()


def plot_subtitle_coverage(df: pd.DataFrame, figures_dir: Path, subtitle_ids: Optional[Set[int]] = None) -> None:
    """Subtitle coverage by decade. Pass subtitle_ids to set has_subtitle from IDs; else df must have 'has_subtitle'."""
    out = _ensure_temporal(df.copy())
    if subtitle_ids is not None:
        out['has_subtitle'] = out['id'].isin(subtitle_ids)
    elif 'has_subtitle' not in out.columns:
        raise ValueError("df must have 'has_subtitle' or pass subtitle_ids")
    decade_subs = out.groupby('decade').agg(
        total=('id', 'count'),
        with_subtitle=('has_subtitle', 'sum')
    ).dropna()
    decade_subs['coverage'] = decade_subs['with_subtitle'] / decade_subs['total']
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(decade_subs))
    width = 0.35
    ax.bar(x - width/2, decade_subs['total'], width, label='Total Movies', color='steelblue')
    ax.bar(x + width/2, decade_subs['with_subtitle'], width, label='With Subtitle', color='coral')
    ax2 = ax.twinx()
    ax2.plot(x, decade_subs['coverage'], 'ko-', linewidth=2, markersize=8, label='Coverage Rate')
    ax2.set_ylabel('Coverage Rate', fontsize=12)
    ax2.set_ylim(0, 1)
    ax.set_xticks(x)
    ax.set_xticklabels(decade_subs.index.astype(int).astype(str), rotation=45)
    ax.set_xlabel('Decade')
    ax.set_ylabel('Number of Movies')
    ax.set_title('Subtitle Coverage by Decade', fontsize=14, fontweight='bold')
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    plt.tight_layout()
    plt.savefig(figures_dir / '01_eda_14_subtitle_coverage.png', dpi=150, bbox_inches='tight')
    plt.show()


def plot_feature_correlations(df_financial: pd.DataFrame, figures_dir: Path) -> None:
    """Numeric feature correlation heatmap (upper triangle)."""
    numeric_cols = ['budget', 'revenue', 'runtime', 'vote_count', 'roi']
    corr_df = df_financial[numeric_cols].corr()
    fig, ax = plt.subplots(figsize=(8, 6))
    mask = np.triu(np.ones_like(corr_df, dtype=bool), k=1)
    sns.heatmap(corr_df, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
                mask=mask, linewidths=0.5, ax=ax, vmin=-1, vmax=1)
    ax.set_title('Numeric Feature Correlations', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(figures_dir / '01_eda_15_feature_correlations.png', dpi=150, bbox_inches='tight')
    plt.show()


def plot_point_biserial_correlations(df_financial: pd.DataFrame, figures_dir: Path) -> None:
    """Point-biserial correlation of numeric features with is_commercial and is_award_winner."""
    features_for_corr = ['budget', 'revenue', 'runtime', 'vote_count']
    pb_results = []
    for target in ['is_commercial', 'is_award_winner']:
        for feat in features_for_corr:
            valid = df_financial[[feat, target]].dropna()
            r, p = pointbiserialr(valid[target].astype(int), valid[feat])
            pb_results.append({'target': target, 'feature': feat, 'r': r, 'p_value': p})
    pb_df = pd.DataFrame(pb_results)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, target in zip(axes, ['is_commercial', 'is_award_winner']):
        subset = pb_df[pb_df['target'] == target].sort_values('r')
        colors = ['#e74c3c' if r < 0 else '#2ecc71' for r in subset['r']]
        ax.barh(subset['feature'], subset['r'], color=colors)
        ax.set_title(f'Point-Biserial Correlations: {target}', fontweight='bold')
        ax.set_xlabel('Correlation (r)')
        ax.axvline(x=0, color='black', linewidth=0.8)
        for i, (feat, r) in enumerate(zip(subset['feature'], subset['r'])):
            ax.text(r + 0.01 * np.sign(r), i, f'{r:.3f}', va='center', fontsize=10)
    plt.tight_layout()
    plt.savefig(figures_dir / '01_eda_16_point_biserial_correlations.png', dpi=150, bbox_inches='tight')
    plt.show()
