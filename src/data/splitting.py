"""Domain-disjoint splitting: URLs from the same registrable_domain stay together."""
import hashlib
import numpy as np
import pandas as pd


def domain_disjoint_split(df, dev_ratio=0.15, test_ratio=0.15, seed=42):
    """Split a manifest DataFrame into TRAIN/DEV/LOCKED_TEST by registrable_domain.

    Returns dict with keys TRAIN, DEV, LOCKED_TEST, each a DataFrame.
    Domains are grouped; a domain never appears in two splits.
    """
    rng = np.random.default_rng(seed)
    domains = df["registrable_domain"].fillna("").astype(str).unique()
    # stable shuffle
    order = np.array(sorted(domains))
    rng.shuffle(order)
    n = len(order)
    n_test = int(n * test_ratio)
    n_dev = int(n * dev_ratio)
    test_domains = set(order[:n_test])
    dev_domains = set(order[n_test:n_test + n_dev])
    train_domains = set(order[n_test + n_dev:])

    def pick(doms):
        return df[df["registrable_domain"].isin(doms)].copy()

    return {
        "TRAIN": pick(train_domains),
        "DEV": pick(dev_domains),
        "LOCKED_TEST": pick(test_domains),
    }


def save_splits(splits, out_dir):
    import os
    os.makedirs(out_dir, exist_ok=True)
    for name, d in splits.items():
        d.to_csv(os.path.join(out_dir, f"{name}.csv"), index=False)
    return {name: len(d) for name, d in splits.items()}
