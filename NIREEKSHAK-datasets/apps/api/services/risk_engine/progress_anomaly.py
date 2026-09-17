from typing import Dict, Any

def evaluate_progress_anomaly(
    physical_progress: float,
    financial_progress: float
) -> Dict[str, Any]:
    """
    Detects severe divergence between reported physical progress and financial expenditure.
    Example: Physical progress = 30%, Financial progress = 78%.
    """
    discrepancy = financial_progress - physical_progress
    score = 0
    signal = None

    if discrepancy >= 40.0:
        score = min(100, int(45 + (discrepancy - 40.0) * 1.5))
        signal = {
            "type": "PROGRESS_MISMATCH",
            "title": "Severe Physical vs Financial Discrepancy",
            "severity": "CRITICAL",
            "scoreImpact": 22,
            "description": f"Financial expenditure ({financial_progress:.1f}%) substantially exceeds physical completion ({physical_progress:.1f}%) with a +{discrepancy:.1f}% divergence gap."
        }
    elif discrepancy >= 25.0:
        score = int(25 + (discrepancy - 25.0) * 1.2)
        signal = {
            "type": "PROGRESS_MISMATCH",
            "title": "Progress vs Expenditure Mismatch",
            "severity": "HIGH",
            "scoreImpact": 15,
            "description": f"Financial progress ({financial_progress:.1f}%) is noticeably higher than reported physical progress ({physical_progress:.1f}%)."
        }
    elif discrepancy >= 15.0:
        score = 15
        signal = {
            "type": "PROGRESS_MISMATCH",
            "title": "Moderate Progress Divergence",
            "severity": "MEDIUM",
            "scoreImpact": 8,
            "description": f"Minor divergence of {discrepancy:.1f}% between physical progress and financial drawdowns."
        }

    return {
        "score": score,
        "discrepancy": round(discrepancy, 1),
        "physical_progress": physical_progress,
        "financial_progress": financial_progress,
        "flagged": signal is not None,
        "signal": signal
    }
