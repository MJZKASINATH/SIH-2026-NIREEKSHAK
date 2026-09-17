from typing import Dict, Any, List

def format_explanation_report(risk_result: Dict[str, Any], project_title: str) -> Dict[str, Any]:
    """
    Transforms raw risk results into executive-ready explainable reports for auditors and administrators.
    Never outputs 'AI declared fraud' - produces clear, defensible evidence points.
    """
    score = risk_result.get("overall_score", 0)
    level = risk_result.get("risk_level", "LOW")
    signals = risk_result.get("signals", [])

    bullets = []
    for s in signals:
        bullets.append({
            "points": s.get("scoreImpact", 0),
            "signal_type": s.get("type"),
            "title": s.get("title"),
            "severity": s.get("severity"),
            "reason": s.get("description")
        })

    recommended_action = "Routine Monitoring"
    if level == "RED_FLAG":
        recommended_action = "Escalate to Vigilance / Schedule Urgent On-Site Physical Inspection"
    elif level == "HIGH":
        recommended_action = "Request Administrative Clarification & Audit Financial Vouchers"
    elif level == "MEDIUM":
        recommended_action = "Flag for Next Milestone Review"

    return {
        "project_title": project_title,
        "score_display": f"{score}/100 — {level.replace('_', ' ')}",
        "primary_statement": (
            "Project requires investigation because multiple independent risk signals were detected."
            if level == "RED_FLAG"
            else "Project parameters monitored within acceptable risk bands."
        ),
        "evidence_points": bullets,
        "recommended_action": recommended_action,
        "is_fraud_declared": False, # Explicit guardrail
        "final_decision_holder": "Authorized Human Personnel"
    }
