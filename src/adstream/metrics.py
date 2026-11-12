def compute_ctr(clicks: int, impressions: int) -> float:
    if clicks < 0 or impressions < 0:
        raise ValueError("Clicks cannot be negative")
    return clicks / impressions if impressions > 0 else 0.0