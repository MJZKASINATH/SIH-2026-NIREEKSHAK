from typing import Dict, Any, Optional
import math

def evaluate_cost_anomaly(
    cost: float,
    peer_median: float = 2500000.0,
    peer_iqr_low: float = 1500000.0,
    peer_iqr_high: float = 3500000.0,
    category: str = "General"
) -> Dict[str, Any]:
    """
    Evaluates cost deviation against peer projects in the same category/constituency.
    Returns anomaly score (0-100), signal details, and human-readable explanation.
    """
    if cost <= 0:
        return {"score": 0, "flagged": False, "signal": None}

    # If peer statistics not provided, use standard tier
    if peer_median <= 0:
        peer_median = 2500000.0
    if peer_iqr_high <= peer_median:
        peer_iqr_high = peer_median * 1.4
    if peer_iqr_low <= 0:
        peer_iqr_low = peer_median * 0.7

    iqr = peer_iqr_high - peer_iqr_low
    upper_whisker = peer_iqr_high + 1.5 * iqr
    extreme_whisker = peer_iqr_high + 3.0 * iqr

    ratio = cost / peer_median
    score = 0
    signal = None

    if cost > extreme_whisker or ratio >= 2.0:
        score = min(100, int(35 + (ratio - 2.0) * 20))
        signal = {
            "type": "COST_ANOMALY",
            "title": "Severe Cost Outlier Detected",
            "severity": "CRITICAL",
            "scoreImpact": 24,
            "description": f"Cost (₹{cost:,.0f}) is {ratio:.2f}× higher than category median (₹{peer_median:,.0f}), significantly exceeding IQR statistical bounds."
        }
    elif cost > upper_whisker or ratio >= 1.4:
        score = int(20 + (ratio - 1.4) * 25)
        signal = {
            "type": "COST_ANOMALY",
            "title": "Elevated Project Cost",
            "severity": "HIGH",
            "scoreImpact": 16,
            "description": f"Project cost is {ratio:.2f}× higher than comparable peer projects in {category}."
        }
    elif ratio > 1.2:
        score = 10
        signal = {
            "type": "COST_ANOMALY",
            "title": "Moderate Cost Deviation",
            "severity": "MEDIUM",
            "scoreImpact": 8,
            "description": f"Cost is {ratio:.2f}× peer median, slightly above normal variance."
        }

    return {
        "score": score,
        "ratio": round(ratio, 2),
        "flagged": signal is not None,
        "signal": signal,
        "peer_median": peer_median,
        "upper_whisker": upper_whisker
    }
