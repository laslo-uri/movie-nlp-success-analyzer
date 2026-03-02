"""
Model training and evaluation pipeline for the Movie NLP Success Analyzer.

Provides reusable functions for training, tuning, and evaluating classifiers,
so notebooks remain concise and narrative-focused.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import (
    train_test_split, StratifiedKFold, cross_val_score,
    RandomizedSearchCV
)
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, StackingClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    f1_score, roc_auc_score, precision_score, recall_score,
    balanced_accuracy_score,
    confusion_matrix, ConfusionMatrixDisplay, roc_curve
)
from imblearn.over_sampling import SMOTE, ADASYN
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional

RANDOM_SEED = 42


def prepare_modeling_data(df, target, feature_cols):
    """Filter to valid rows and split into X, y."""
    criteria = (df['budget'] > 0) & (df['revenue'] > 0) & (df['runtime'] > 0)
    subset = df[criteria][feature_cols + [target]].dropna()
    return subset[feature_cols], subset[target]


def create_splits(X, y, test_size=0.3, val_ratio=0.5):
    """Create stratified train/validation/test splits (70/15/15)."""
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=RANDOM_SEED)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=val_ratio, stratify=y_temp, random_state=RANDOM_SEED)
    print(f"Split: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}, "
          f"pos_rate={y_train.mean():.3f}")
    return {
        'X_train': X_train, 'y_train': y_train,
        'X_val': X_val, 'y_val': y_val,
        'X_test': X_test, 'y_test': y_test,
        'features': list(X.columns)
    }


def get_baseline_models():
    """Return baseline model configs (no hyperparameter grids)."""
    return {
        'Logistic Regression': LogisticRegression(
            class_weight='balanced', max_iter=2000, random_state=RANDOM_SEED),
        'Random Forest': RandomForestClassifier(
            n_estimators=100, class_weight='balanced', random_state=RANDOM_SEED),
        'XGBoost': xgb.XGBClassifier(
            n_estimators=100, eval_metric='logloss', random_state=RANDOM_SEED),
    }


def get_advanced_models_with_grids():
    """Return models with hyperparameter search spaces."""
    return {
        'LogReg': {
            'model': LogisticRegression(random_state=RANDOM_SEED, max_iter=2000),
            'params': {'C': [0.01, 0.1, 1, 10], 'penalty': ['l1', 'l2'], 'solver': ['liblinear']}
        },
        'RF': {
            'model': RandomForestClassifier(random_state=RANDOM_SEED),
            'params': {
                'n_estimators': [100, 200, 300], 'max_depth': [10, 20, 30, None],
                'min_samples_split': [2, 5, 10], 'min_samples_leaf': [1, 2, 4],
            }
        },
        'XGB': {
            'model': xgb.XGBClassifier(random_state=RANDOM_SEED, eval_metric='logloss'),
            'params': {
                'n_estimators': [100, 200, 300], 'max_depth': [3, 5, 7, 10],
                'learning_rate': [0.01, 0.05, 0.1, 0.2],
                'subsample': [0.7, 0.8, 0.9, 1.0], 'colsample_bytree': [0.7, 0.8, 0.9, 1.0],
            }
        },
        'SVM_linear': {
            'model': SVC(kernel='linear', probability=True, random_state=RANDOM_SEED),
            'params': {'C': [0.01, 0.1, 1, 10]}
        },
        'SVM_rbf': {
            'model': SVC(kernel='rbf', probability=True, random_state=RANDOM_SEED),
            'params': {'C': [0.1, 1, 10], 'gamma': ['scale', 'auto', 0.01, 0.1]}
        },
    }


def train_baseline(split, models=None, use_smote=False):
    """
    Train baseline models on a split. Returns dict of results.
    Uses original (pre-SMOTE) class ratio for XGBoost scale_pos_weight so test F1 benefits.
    Stores test_f1_opt (F1 at threshold chosen on validation) for imbalance-aware reporting.
    """
    if models is None:
        models = get_baseline_models()

    X_train, y_train = split['X_train'].copy(), split['y_train'].copy()
    # Original class ratio for XGB (before any resampling) — keeps loss aware of imbalance on test
    orig_pos = (split['y_train'] == 1).sum()
    orig_neg = (split['y_train'] == 0).sum()
    xgb_scale = orig_neg / max(orig_pos, 1)

    if use_smote:
        sm = SMOTE(random_state=RANDOM_SEED)
        X_train, y_train = sm.fit_resample(X_train, y_train)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(split['X_val'])
    X_test_s = scaler.transform(split['X_test'])

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    results = {}

    for name, model in models.items():
        if isinstance(model, xgb.XGBClassifier):
            model.set_params(scale_pos_weight=xgb_scale)

        model.fit(X_train_s, y_train)
        cv_scores = cross_val_score(model, X_train_s, y_train, cv=cv, scoring='f1')

        y_val_pred = model.predict(X_val_s)
        y_val_proba = model.predict_proba(X_val_s)[:, 1]
        y_test_pred = model.predict(X_test_s)
        y_test_proba = model.predict_proba(X_test_s)[:, 1]

        best_t, test_f1_opt = f1_at_optimal_threshold(split, model, scaler)

        results[name] = {
            'model': model, 'scaler': scaler,
            'cv_f1_mean': cv_scores.mean(), 'cv_f1_std': cv_scores.std(),
            'val_f1': f1_score(split['y_val'], y_val_pred),
            'val_auc': roc_auc_score(split['y_val'], y_val_proba),
            'test_f1': f1_score(split['y_test'], y_test_pred),
            'test_f1_opt': test_f1_opt,
            'best_threshold': best_t,
            'test_auc': roc_auc_score(split['y_test'], y_test_proba),
            'test_bal_acc': balanced_accuracy_score(split['y_test'], y_test_pred),
            'test_precision': precision_score(split['y_test'], y_test_pred),
            'test_recall': recall_score(split['y_test'], y_test_pred),
            'y_test': split['y_test'], 'y_test_pred': y_test_pred,
            'y_test_proba': y_test_proba, 'features': split['features'],
        }
        if hasattr(model, 'feature_importances_'):
            results[name]['feature_importance'] = model.feature_importances_
        elif hasattr(model, 'coef_'):
            results[name]['feature_importance'] = np.abs(model.coef_[0])

        print(f"  {name:25s} CV F1: {cv_scores.mean():.3f} ± {cv_scores.std():.3f} | "
              f"Test F1: {results[name]['test_f1']:.3f} (opt: {test_f1_opt:.3f}) | AUC: {results[name]['test_auc']:.3f}")

    return results


def f1_at_optimal_threshold(split, model, scaler):
    """Find threshold that maximizes F1 on validation; return (best_threshold, test_f1_at_that_threshold)."""
    X_val_s = scaler.transform(split['X_val'])
    X_test_s = scaler.transform(split['X_test'])
    p_val = model.predict_proba(X_val_s)[:, 1]
    p_test = model.predict_proba(X_test_s)[:, 1]
    best_t, best_f1 = 0.5, 0.0
    for t in np.linspace(0.05, 0.95, 91):
        f1 = f1_score(split['y_val'], (p_val >= t).astype(int), zero_division=0)
        if f1 > best_f1:
            best_f1, best_t = f1, t
    test_f1_opt = f1_score(split['y_test'], (p_test >= best_t).astype(int), zero_division=0)
    return best_t, test_f1_opt


def train_with_tuning(split, balancing='class_weight', n_iter=20):
    """
    Train all models with RandomizedSearchCV hyperparameter tuning.
    balancing: 'class_weight', 'smote', or 'adasyn'
    """
    X_train, y_train = split['X_train'].copy(), split['y_train'].copy()

    if balancing == 'smote':
        X_train, y_train = SMOTE(random_state=RANDOM_SEED).fit_resample(X_train, y_train)
    elif balancing == 'adasyn':
        X_train, y_train = ADASYN(random_state=RANDOM_SEED).fit_resample(X_train, y_train)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(split['X_val'])
    X_test_s = scaler.transform(split['X_test'])

    models_grids = get_advanced_models_with_grids()

    if balancing == 'class_weight':
        models_grids['LogReg']['model'].set_params(class_weight='balanced')
        models_grids['RF']['model'].set_params(class_weight='balanced')
        xgb_scale = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
        models_grids['XGB']['model'].set_params(scale_pos_weight=xgb_scale)
        models_grids['SVM_linear']['model'].set_params(class_weight='balanced')
        models_grids['SVM_rbf']['model'].set_params(class_weight='balanced')

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    results = {}

    for name, cfg in models_grids.items():
        print(f"  Training {name}...")
        search = RandomizedSearchCV(
            cfg['model'], cfg['params'],
            n_iter=min(n_iter, np.prod([len(v) for v in cfg['params'].values()])),
            cv=cv, scoring='f1', random_state=RANDOM_SEED, n_jobs=-1
        )
        search.fit(X_train_s, y_train)
        model = search.best_estimator_

        cv_scores = cross_val_score(model, X_train_s, y_train, cv=cv, scoring='f1')
        y_test_pred = model.predict(X_test_s)
        y_test_proba = model.predict_proba(X_test_s)[:, 1]
        best_t, test_f1_opt = f1_at_optimal_threshold(split, model, scaler)

        results[name] = {
            'model': model, 'scaler': scaler, 'best_params': search.best_params_,
            'cv_f1_mean': cv_scores.mean(), 'cv_f1_std': cv_scores.std(),
            'val_f1': f1_score(split['y_val'], model.predict(X_val_s)),
            'val_auc': roc_auc_score(split['y_val'], model.predict_proba(X_val_s)[:, 1]),
            'test_f1': f1_score(split['y_test'], y_test_pred),
            'test_f1_opt': test_f1_opt,
            'best_threshold': best_t,
            'test_auc': roc_auc_score(split['y_test'], y_test_proba),
            'test_bal_acc': balanced_accuracy_score(split['y_test'], y_test_pred),
            'test_precision': precision_score(split['y_test'], y_test_pred),
            'test_recall': recall_score(split['y_test'], y_test_pred),
            'y_test': split['y_test'], 'y_test_pred': y_test_pred,
            'y_test_proba': y_test_proba, 'features': split['features'],
        }
        if hasattr(model, 'feature_importances_'):
            results[name]['feature_importance'] = model.feature_importances_
        elif hasattr(model, 'coef_'):
            results[name]['feature_importance'] = np.abs(model.coef_[0])

        print(f"    CV F1: {cv_scores.mean():.3f} ± {cv_scores.std():.3f} | "
              f"Test F1: {results[name]['test_f1']:.3f} | AUC: {results[name]['test_auc']:.3f}")

    return results


def build_ensembles(split):
    """Build Voting and Stacking ensembles. Returns dict of results."""
    X_train, y_train = split['X_train'], split['y_train']
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(split['X_test'])

    xgb_scale = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)

    base = [
        ('lr', LogisticRegression(C=1, class_weight='balanced', max_iter=2000, random_state=RANDOM_SEED)),
        ('rf', RandomForestClassifier(n_estimators=200, max_depth=20, class_weight='balanced', random_state=RANDOM_SEED)),
        ('xgb', xgb.XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.1,
                                    scale_pos_weight=xgb_scale, eval_metric='logloss', random_state=RANDOM_SEED)),
        ('svm', SVC(C=1, kernel='rbf', class_weight='balanced', probability=True, random_state=RANDOM_SEED)),
    ]

    results = {}
    y_test = split['y_test']

    for ens_name, ens_model in [
        ('Soft Voting', VotingClassifier(estimators=base, voting='soft')),
        ('Hard Voting', VotingClassifier(estimators=base, voting='hard')),
        ('Stacking (LR)', StackingClassifier(
            estimators=base,
            final_estimator=LogisticRegression(class_weight='balanced', max_iter=2000, random_state=RANDOM_SEED),
            cv=cv, passthrough=False)),
    ]:
        print(f"  Training {ens_name}...")
        ens_model.fit(X_train_s, y_train)
        y_pred = ens_model.predict(X_test_s)
        has_proba = hasattr(ens_model, 'predict_proba')
        y_proba = ens_model.predict_proba(X_test_s)[:, 1] if has_proba else None

        results[ens_name] = {
            'test_f1': f1_score(y_test, y_pred),
            'test_auc': roc_auc_score(y_test, y_proba) if y_proba is not None else None,
            'test_precision': precision_score(y_test, y_pred),
            'test_recall': recall_score(y_test, y_pred),
            'y_test': y_test, 'y_test_pred': y_pred, 'y_test_proba': y_proba,
        }
        auc_str = f"{results[ens_name]['test_auc']:.3f}" if results[ens_name]['test_auc'] else "N/A"
        print(f"    Test F1: {results[ens_name]['test_f1']:.3f} | AUC: {auc_str}")

    return results


def results_table(results):
    """Create a comparison DataFrame from results dict. Handles None (e.g. AUC for Hard Voting)."""
    def fmt(v, f=".3f"):
        return f"{v:{f}}" if v is not None else "N/A"
    rows = []
    for name, r in results.items():
        row = {'Model': name, 'Test F1': fmt(r['test_f1']), 'Test AUC': fmt(r.get('test_auc')),
               'Bal. Acc.': fmt(r.get('test_bal_acc')),
               'Precision': fmt(r['test_precision']), 'Recall': fmt(r['test_recall'])}
        if r.get('test_f1_opt') is not None:
            row['F1 (opt)'] = fmt(r['test_f1_opt'])
        if 'cv_f1_mean' in r and r['cv_f1_mean'] is not None:
            row['CV F1'] = f"{r['cv_f1_mean']:.3f} ± {r['cv_f1_std']:.3f}"
        rows.append(row)
    return pd.DataFrame(rows)


# --- Plotting Helpers ---

def plot_confusion_matrices(results, task_name, feat_label, save_path=None):
    """Plot confusion matrices for all models in a results dict."""
    n = len(results)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 5))
    if n == 1:
        axes = [axes]
    fig.suptitle(f'{task_name} — Confusion Matrices ({feat_label})', fontsize=16, fontweight='bold')
    cmap = 'Blues' if 'Commercial' in task_name else 'Oranges'
    for i, (name, r) in enumerate(results.items()):
        cm = confusion_matrix(r['y_test'], r['y_test_pred'])
        ConfusionMatrixDisplay(cm, display_labels=['Neg', 'Pos']).plot(ax=axes[i], cmap=cmap, colorbar=False)
        axes[i].set_title(f"{name}\nF1={r['test_f1']:.3f}")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_roc_curves(results, task_name, save_path=None):
    """Plot ROC curves for all models in a results dict."""
    plt.figure(figsize=(10, 8))
    for name, r in results.items():
        if r.get('y_test_proba') is not None:
            fpr, tpr, _ = roc_curve(r['y_test'], r['y_test_proba'])
            plt.plot(fpr, tpr, label=f"{name} (AUC={r['test_auc']:.3f})", linewidth=2)
    plt.plot([0, 1], [0, 1], 'k--', alpha=0.5, label='Random')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(f'{task_name} — ROC Curves', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_feature_importance(results, feat_cols, task_name, models=('RF', 'XGB'), save_path=None):
    """Plot feature importance for tree-based models."""
    fig, axes = plt.subplots(1, len(models), figsize=(9 * len(models), 8))
    if len(models) == 1:
        axes = [axes]
    fig.suptitle(f'{task_name} — Feature Importance', fontsize=16, fontweight='bold')
    for ax_i, mname in enumerate(models):
        if mname in results and 'feature_importance' in results[mname]:
            imp = results[mname]['feature_importance']
            n_top = min(15, len(imp))
            top_idx = np.argsort(imp)[-n_top:]
            axes[ax_i].barh(range(n_top), imp[top_idx])
            axes[ax_i].set_yticks(range(n_top))
            axes[ax_i].set_yticklabels([feat_cols[i] for i in top_idx])
            axes[ax_i].set_title(f'{mname} — Top {n_top}')
            axes[ax_i].grid(axis='x', alpha=0.3)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
