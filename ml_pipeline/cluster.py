from rapidfuzz import fuzz


def cluster_merchants(primary_tokens, threshold=88):
    """
    Groups similar primary tokens into clusters using fuzzy matching.
    Returns a dict mapping each unique token -> cluster_id
    """
    unique_tokens = primary_tokens.unique()
    clusters = {}
    cluster_reps = []

    for token in unique_tokens:
        matched = False
        for i, rep in enumerate(cluster_reps):
            score = fuzz.partial_ratio(token, rep)
            if score >= threshold:
                clusters[token] = i
                matched = True
                break
        if not matched:
            cluster_reps.append(token)
            clusters[token] = len(cluster_reps) - 1

    return clusters, cluster_reps


def apply_clustering(df, threshold=88):
    """Takes a cleaned DataFrame, adds a 'cluster_id' column."""
    df = df.copy()
    clusters, _ = cluster_merchants(df["primary_token"], threshold=threshold)
    df["cluster_id"] = df["primary_token"].map(clusters)
    return df