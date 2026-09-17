from typing import Dict, Any, List
from datetime import datetime, date

def evaluate_expenditure_velocity(
    transactions: List[Dict[str, Any]],
    allocated_amount: float,
    physical_progress: float = 0.0
) -> Dict[str, Any]:
    """
    Detects abnormal expenditure velocity (speed of fund consumption).
    Flags sudden rapid outflows or large payments before physical milestones are achieved.
    """
    if not transactions or allocated_amount <= 0:
        return {"score": 0, "flagged": False, "signal": None}

    total_spent = sum(t.get("amount", 0.0) for t in transactions)
    burn_rate = total_spent / allocated_amount if allocated_amount > 0 else 0

    score = 0
    signal = None

    # Check: High burn rate with low progress
    if burn_rate >= 0.70 and physical_progress < 35.0:
        score = 80
        signal = {
            "type": "EXPENDITURE_VELOCITY",
            "title": "Abnormal Expenditure Velocity",
            "severity": "CRITICAL",
            "scoreImpact": 20,
            "description": f"Fund utilization has reached {burn_rate*100:.1f}% while physical execution is only {physical_progress:.1f}%. Rapid capital outflow without corresponding ground progress."
        }
    elif burn_rate >= 0.50 and physical_progress < 20.0:
        score = 60
        signal = {
            "type": "EXPENDITURE_VELOCITY",
            "title": "Elevated Spending Velocity",
            "severity": "HIGH",
            "scoreImpact": 15,
            "description": f"Expended {burn_rate*100:.1f}% of allocated funds with only {physical_progress:.1f}% physical progress recorded."
        }

    return {
        "score": score,
        "burn_rate": round(burn_rate, 3),
        "total_spent": total_spent,
        "flagged": signal is not None,
        "signal": signal
    }
