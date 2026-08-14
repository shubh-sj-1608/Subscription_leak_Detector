import pandas as pd


def build_risk_features(row, df):
    cluster_txns = df[df["cluster_id"] == row["cluster_id"]].sort_values("date")
    days_since_last = (df["date"].max() - row["last_seen"]).days
    price_stability = row["amount_std"] / row["amount_mean"] if row["amount_mean"] > 0 else 0

    half = len(cluster_txns) // 2
    if half > 0:
        early_avg = cluster_txns["amount"].iloc[:half].mean()
        late_avg = cluster_txns["amount"].iloc[half:].mean()
        price_increase_pct = ((late_avg - early_avg) / early_avg * 100) if early_avg > 0 else 0
    else:
        price_increase_pct = 0

    return pd.Series({
        "days_since_last_charge": days_since_last,
        "price_stability": price_stability,
        "price_increase_pct": price_increase_pct,
    })


def calculate_risk_score(row):
    score = 0
    reasons = []

    if row["price_increase_pct"] > 10:
        score += 0.35
        reasons.append(f"price increased {row['price_increase_pct']:.0f}% over time")

    if row["price_stability"] < 0.05:
        score += 0.25
        reasons.append("price has never changed (classic 'set and forget' pattern)")

    if row["days_since_last_charge"] > 45:
        score += 0.20
        reasons.append("no recent charge detected")

    score += 0.20
    reasons.append("confirmed recurring pattern")

    score = min(score, 1.0)
    return pd.Series({"risk_score": round(score, 2), "risk_reasons": "; ".join(reasons)})


def score_recurring_clusters(cluster_stats, df):
    """Takes recurring cluster stats + full df, returns clusters with risk scores attached."""
    recurring = cluster_stats[cluster_stats["is_recurring_predicted"] == True].copy()
    risk_features = recurring.apply(lambda row: build_risk_features(row, df), axis=1)
    recurring = pd.concat([recurring, risk_features], axis=1)
    risk_results = recurring.apply(calculate_risk_score, axis=1)
    recurring = pd.concat([recurring, risk_results], axis=1)
    return recurring


def calculate_annual_cost(row):
    if row["gap_mean_days"] <= 10:
        charges_per_year = 52
    elif row["gap_mean_days"] <= 45:
        charges_per_year = 12
    else:
        charges_per_year = 1
    return row["amount_mean"] * charges_per_year

def adjust_score_with_feedback(base_score, merchant_name, user_feedback_lookup):
    """
    Adjusts a risk score based on past user feedback for this exact merchant.
    user_feedback_lookup: dict mapping merchant_name -> list of feedback_types e.g. ['confirmed', 'cancelled']
    """
    feedback_list = user_feedback_lookup.get(merchant_name, [])
    if not feedback_list:
        return base_score, "no prior feedback"

    confirmed_count = feedback_list.count('confirmed')
    cancelled_count = feedback_list.count('cancelled')

    if cancelled_count > confirmed_count:
        # User has said "cancel" before for this merchant - boost risk score
        adjusted = min(base_score + 0.15, 1.0)
        return adjusted, f"boosted (user marked 'cancel' {cancelled_count}x previously)"
    elif confirmed_count > cancelled_count:
        # User has confirmed they use it - lower risk score
        adjusted = max(base_score - 0.20, 0.0)
        return adjusted, f"lowered (user confirmed usage {confirmed_count}x previously)"

    return base_score, "mixed feedback, no adjustment"