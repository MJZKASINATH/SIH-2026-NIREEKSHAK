from typing import Dict, Any, Optional
from datetime import date, datetime

def evaluate_timeline_anomaly(
    start_date: Optional[date],
    completion_date: Optional[date],
    expected_completion_date: Optional[date],
    physical_progress: float = 0.0,
    current_status: str = "IN_PROGRESS"
) -> Dict[str, Any]:
    """
    Detects project delays, stalled works, and missing statutory progress milestones.
    """
    score = 0
    signal = None
    today = date.today()

    if expected_completion_date and today > expected_completion_date and physical_progress < 95.0:
        overdue_days = (today - expected_completion_date).days
        if overdue_days > 180:
            score = 75
            signal = {
                "type": "TIMELINE_VIOLATION",
                "title": "Severe Project Overdue Delay",
                "severity": "HIGH",
                "scoreImpact": 15,
                "description": f"Project is {overdue_days} days past scheduled completion date with only {physical_progress:.1f}% work completed. Work appears stalled."
            }
        elif overdue_days > 60:
            score = 40
            signal = {
                "type": "TIMELINE_VIOLATION",
                "title": "Moderate Milestone Delay",
                "severity": "MEDIUM",
                "scoreImpact": 10,
                "description": f"Project has breached completion deadline by {overdue_days} days. Progress is lagging at {physical_progress:.1f}%."
            }
    elif current_status == "STALLED":
        score = 65
        signal = {
            "type": "TIMELINE_VIOLATION",
            "title": "Project Execution Stalled",
            "severity": "HIGH",
            "scoreImpact": 12,
            "description": "Field reporting indicates zero progress over consecutive reporting periods."
        }

    return {
        "score": score,
        "flagged": signal is not None,
        "signal": signal
    }
