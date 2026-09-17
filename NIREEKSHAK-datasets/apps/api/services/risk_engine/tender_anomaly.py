from typing import Dict, Any

def evaluate_tender_anomaly(
    estimated_amount: float,
    tender_amount: float,
    awarded_amount: float
) -> Dict[str, Any]:
    """
    Evaluates tender anomalies such as abnormal tender deviations (severe underbidding or massive inflation).
    """
    if estimated_amount <= 0 or awarded_amount <= 0:
        return {"score": 0, "flagged": False, "signal": None}

    deviation_percent = ((awarded_amount - estimated_amount) / estimated_amount) * 100.0
    score = 0
    signal = None

    # Significant inflation (+25% over estimate)
    if deviation_percent >= 25.0:
        score = min(100, int(30 + (deviation_percent - 25.0) * 2))
        signal = {
            "type": "TENDER_ANOMALY",
            "title": "Inflated Tender Award",
            "severity": "HIGH",
            "scoreImpact": 16,
            "description": f"Awarded amount (₹{awarded_amount:,.0f}) exceeds official engineering estimate (₹{estimated_amount:,.0f}) by +{deviation_percent:.1f}%."
        }
    # Severe underbidding (-30% below estimate: risk of abandoning project or sub-standard execution)
    elif deviation_percent <= -30.0:
        score = min(100, int(30 + abs(deviation_percent + 30.0) * 1.5))
        signal = {
            "type": "TENDER_ANOMALY",
            "title": "Aggressive Underbidding Detected",
            "severity": "MEDIUM",
            "scoreImpact": 12,
            "description": f"Awarded contract is {abs(deviation_percent):.1f}% below estimate. Highly aggressive bid poses execution abandonment or cost escalation risk."
        }

    return {
        "score": score,
        "deviation_percent": round(deviation_percent, 2),
        "flagged": signal is not None,
        "signal": signal
    }
