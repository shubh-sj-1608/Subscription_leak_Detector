import numpy as np
import pandas as pd


def analyze_cluster(group):
    dates = sorted(group["date"])
    amounts = group["amount"].values

    if len(dates) < 2:
        gap_mean = None
        gap_std = None
    else:
        gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
        gap_mean = np.mean(gaps)
        gap_std = np.std(gaps)

    return pd.Series({
        "transaction_count": len(group),
        "gap_mean_days": gap_mean,
        "gap_std_days": gap_std,
        "amount_mean": np.mean(amounts),
        "amount_std": np.std(amounts),
        "first_seen": min(dates),
        "last_seen": max(dates),
    })


def is_recurring(row):
    if row["transaction_count"] < 3:
        return False
    if row["gap_std_days"] is None or row["gap_std_days"] > 5:
        return False
    plausible_cycle = any(abs(row["gap_mean_days"] - target) <= 5 for target in [7, 30, 365])
    if not plausible_cycle:
        return False
    return True


def detect_recurring_clusters(df):
    """Takes a DataFrame with 'cluster_id', 'date', 'amount' columns. Returns per-cluster stats."""
    cluster_stats = df.groupby("cluster_id").apply(analyze_cluster, include_groups=False).reset_index()
    cluster_stats["is_recurring_predicted"] = cluster_stats.apply(is_recurring, axis=1)
    return cluster_stats