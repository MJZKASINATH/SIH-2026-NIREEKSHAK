from typing import Dict, Any

def evaluate_cost_overrun(
    actual_expenditure: float,
    awarded_amount: float,
    estimated_cost: float
) -> Dict[str, Any]:
    """
    Detects cost overruns where actual expenditures exceed the awarded contract ceiling.
    """
    ceiling = awarded_amount if awarded_amount > 0 else estimated_cost
    if ceiling <= 0:
        return {"score": 0, "flagged": False, "signal": None}

    overrun_ratio = actual_expenditure / ceiling
    score = 0
    signal = None

    if actual_expenditure > ceiling:
        excess = actual_expenditure - ceiling
        score = min(100, int(40 + (overrun_ratio - 1.0) * 100))
        signal = {
            "type": "COST_OVERRUN",
            "title": "Contract Budget Overrun",
            "severity": "CRITICAL" if overrun_ratio > 1.15 else "HIGH",
            "scoreImpact": 18,
            "description": f"Cumulative expenditure (₹{actual_expenditure:,.0f}) exceeds approved awarded contract ceiling (₹{ceiling:,.0f}) by ₹{excess:,.0f} ({((overrun_ratio-1)*100):.1f}% excess)."
        }
    elif overrun_ratio >= 0.98:
        score = 25
        signal = {
            "type": "COST_OVERRUN",
            "title": "Expenditure Approaching Ceiling",
            "severity": "MEDIUM",
            "scoreImpact": 8,
            "description": f"Cumulative expenditure has reached {overrun_ratio*100:.1f}% of the contract limit."
        }

    return {
        "score": score,
        "overrun_ratio": round(overrun_ratio, 3),
        "flagged": signal is not None,
        "signal": signal
    }
