from typing import Dict, Any, Optional
import re

def normalize_entity_name(name: str) -> str:
    """Normalizes vendor / contractor strings to prevent duplicate entity records."""
    if not name:
        return "UNKNOWN"
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', name).strip().upper()
    # Normalize common business suffixes
    suffixes = ["PVT LTD", "LTD", "LIMITED", "CONSTRUCTIONS", "INFRA", "INFRASTRUCTURE", "ENTERPRISES", "BUILDERS", "CO"]
    for s in suffixes:
        cleaned = re.sub(rf'\b{s}\b', '', cleaned).strip()
    return " ".join(cleaned.split())

def evaluate_contractor_risk(
    suspicious_projects: int = 0,
    red_flagged_projects: int = 0,
    delayed_projects: int = 0,
    total_projects: int = 0,
    contractor_name: str = "Unknown"
) -> Dict[str, Any]:
    """
    Evaluates risk score of a contractor based on historical red flags and suspicious project involvement.
    """
    score = 0
    signal = None

    bad_history_count = suspicious_projects + red_flagged_projects

    if bad_history_count >= 3:
        score = 85
        signal = {
            "type": "AGENCY_RISK",
            "title": "High-Risk Contractor Entity Pattern",
            "severity": "CRITICAL",
            "scoreImpact": 20,
            "description": f"Contractor '{contractor_name}' is associated with {bad_history_count} previously flagged/suspicious MPLADS works across multiple constituencies."
        }
    elif bad_history_count >= 1:
        score = 50
        signal = {
            "type": "AGENCY_RISK",
            "title": "Contractor Prior Flag History",
            "severity": "HIGH",
            "scoreImpact": 14,
            "description": f"Contractor has {bad_history_count} previous project(s) under review or flagged for irregularities."
        }
    elif delayed_projects >= 2 and total_projects > 0 and (delayed_projects / total_projects) >= 0.4:
        score = 30
        signal = {
            "type": "AGENCY_RISK",
            "title": "Chronic Delivery Delays",
            "severity": "MEDIUM",
            "scoreImpact": 8,
            "description": f"Contractor exhibits severe delay frequency ({delayed_projects}/{total_projects} projects delayed)."
        }

    return {
        "score": score,
        "bad_history_count": bad_history_count,
        "flagged": signal is not None,
        "signal": signal
    }
