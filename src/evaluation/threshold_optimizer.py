"""Threshold optimization on DEV only."""
import numpy as np
import pandas as pd


def optimize_thresholds(y_true, scores, target_recall=0.85):
    y_true = np.asarray(y_true).astype(int)
    scores = np.asarray(scores).astype(float)
    thresholds = np.unique(scores)
    # also include a fine grid
    grid = np.linspace(scores.min(), scores.max(), 2001)
    candidates = np.unique(np.concatenate([thresholds, grid]))
    rows = []
    for t in candidates:
        pred = (scores >= t).astype(int)
        tp = int(((pred == 1) & (y_true == 1)).sum())
        fp = int(((pred == 1) & (y_true == 0)).sum())
        tn = int(((pred == 0) & (y_true == 0)).sum())
        fn = int(((pred == 0) & (y_true == 1)).sum())
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rows.append({"threshold": float(t), "recall": recall, "fpr": fpr,
                     "precision": precision, "tp": tp, "fp": fp, "tn": tn, "fn": fn})
    df = pd.DataFrame(rows)
    feasible = df[df["recall"] >= target_recall]
    if len(feasible) > 0:
        best = feasible.loc[feasible["fpr"].idxmin()]
    else:
        best = df.loc[df["recall"].idxmax()]
    return df, best


def bootstrap_threshold_stability(y_true, scores, target_recall=0.85, n_boot=200, seed=42):
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true); scores = np.asarray(scores)
    n = len(y_true)
    thr_list = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        _, best = optimize_thresholds(y_true[idx], scores[idx], target_recall)
        thr_list.append(best["threshold"])
    thr_list = np.array(thr_list)
    return {"mean": float(thr_list.mean()), "std": float(thr_list.std()),
            "q025": float(np.quantile(thr_list, 0.025)),
            "q975": float(np.quantile(thr_list, 0.975))}
