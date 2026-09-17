from typing import Dict, Any, List, Optional
from .cost_anomaly import evaluate_cost_anomaly
from .expenditure_velocity import evaluate_expenditure_velocity
from .cost_overrun import evaluate_cost_overrun
from .progress_anomaly import evaluate_progress_anomaly
from .tender_anomaly import evaluate_tender_anomaly
from .duplicate_detection import evaluate_duplicate_detection
from .geographic_anomaly import evaluate_geographic_anomaly
from .timeline_anomaly import evaluate_timeline_anomaly
from .contractor_risk import evaluate_contractor_risk

def calculate_fused_risk(
    # Cost & Tender inputs
    cost: float = 0.0,
    peer_median: float = 2500000.0,
    peer_iqr_low: float = 1500000.0,
    peer_iqr_high: float = 3500000.0,
    estimated_amount: float = 0.0,
    awarded_amount: float = 0.0,
    actual_expenditure: float = 0.0,
    # Progress & Velocity inputs
    physical_progress: float = 0.0,
    financial_progress: float = 0.0,
    transactions: Optional[List[Dict[str, Any]]] = None,
    # Similarity inputs
    description: str = "",
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    peer_projects: Optional[List[Dict[str, Any]]] = None,
    # Geo inputs
    expected_lat: Optional[float] = None,
    expected_lng: Optional[float] = None,
    submitted_lat: Optional[float] = None,
    submitted_lng: Optional[float] = None,
    exif_lat: Optional[float] = None,
    exif_lng: Optional[float] = None,
    checkpoints: Optional[List[Dict[str, Any]]] = None,
    # Timeline inputs
    start_date: Optional[Any] = None,
    completion_date: Optional[Any] = None,
    expected_completion_date: Optional[Any] = None,
    current_status: str = "IN_PROGRESS",
    # Contractor inputs
    contractor_suspicious_count: int = 0,
    contractor_red_flags: int = 0,
    contractor_delayed_count: int = 0,
    contractor_total_projects: int = 0,
    contractor_name: str = "Unknown"
) -> Dict[str, Any]:
    """
    Combines all 9 anomaly detectors into an explainable, transparent 0-100 risk score.
    Returns: overall score, classification (LOW, MEDIUM, HIGH, RED_FLAG), signals list,
    point contributions, and detailed breakdown.
    """
    signals = []
    points_breakdown = {}

    # 1. Cost Anomaly Check
    cost_res = evaluate_cost_anomaly(
        cost=cost or awarded_amount or actual_expenditure,
        peer_median=peer_median,
        peer_iqr_low=peer_iqr_low,
        peer_iqr_high=peer_iqr_high
    )
    if cost_res["flagged"]:
        signals.append(cost_res["signal"])
        points_breakdown["costDeviationScore"] = cost_res["signal"]["scoreImpact"]
    else:
        points_breakdown["costDeviationScore"] = 0

    # 2. Progress vs Expenditure Mismatch Check
    progress_res = evaluate_progress_anomaly(
        physical_progress=physical_progress,
        financial_progress=financial_progress
    )
    if progress_res["flagged"]:
        signals.append(progress_res["signal"])
        points_breakdown["progressMismatchScore"] = progress_res["signal"]["scoreImpact"]
    else:
        points_breakdown["progressMismatchScore"] = 0

    # 3. Expenditure Velocity Check
    velocity_res = evaluate_expenditure_velocity(
        transactions=transactions or [],
        allocated_amount=awarded_amount or estimated_amount or cost,
        physical_progress=physical_progress
    )
    if velocity_res["flagged"]:
        signals.append(velocity_res["signal"])
        points_breakdown["velocityScore"] = velocity_res["signal"]["scoreImpact"]
    else:
        points_breakdown["velocityScore"] = 0

    # 4. Cost Overrun Check
    overrun_res = evaluate_cost_overrun(
        actual_expenditure=actual_expenditure,
        awarded_amount=awarded_amount,
        estimated_cost=estimated_amount or cost
    )
    if overrun_res["flagged"]:
        signals.append(overrun_res["signal"])
        points_breakdown["overrunScore"] = overrun_res["signal"]["scoreImpact"]
    else:
        points_breakdown["overrunScore"] = 0

    # 5. Tender Anomaly Check
    tender_res = evaluate_tender_anomaly(
        estimated_amount=estimated_amount,
        tender_amount=cost or awarded_amount,
        awarded_amount=awarded_amount
    )
    if tender_res["flagged"]:
        signals.append(tender_res["signal"])
        points_breakdown["tenderScore"] = tender_res["signal"]["scoreImpact"]
    else:
        points_breakdown["tenderScore"] = 0

    # 6. Duplicate / Semantic Overlap Check
    dup_res = evaluate_duplicate_detection(
        description=description,
        lat=lat or expected_lat,
        lng=lng or expected_lng,
        peer_projects=peer_projects
    )
    if dup_res["flagged"]:
        signals.append(dup_res["signal"])
        points_breakdown["duplicateOverlapScore"] = dup_res["signal"]["scoreImpact"]
    else:
        points_breakdown["duplicateOverlapScore"] = 0

    # 7. Geographic / Geofence Check
    geo_res = evaluate_geographic_anomaly(
        expected_lat=expected_lat,
        expected_lng=expected_lng,
        submitted_lat=submitted_lat,
        submitted_lng=submitted_lng,
        exif_lat=exif_lat,
        exif_lng=exif_lng,
        checkpoints=checkpoints
    )
    if geo_res["flagged"]:
        signals.append(geo_res["signal"])
        points_breakdown["geospatialScore"] = geo_res["signal"]["scoreImpact"]
    else:
        points_breakdown["geospatialScore"] = 0

    # 8. Timeline Anomaly Check
    time_res = evaluate_timeline_anomaly(
        start_date=start_date,
        completion_date=completion_date,
        expected_completion_date=expected_completion_date,
        physical_progress=physical_progress,
        current_status=current_status
    )
    if time_res["flagged"]:
        signals.append(time_res["signal"])
        points_breakdown["timelineLatencyScore"] = time_res["signal"]["scoreImpact"]
    else:
        points_breakdown["timelineLatencyScore"] = 0

    # 9. Contractor Entity Risk Check
    contractor_res = evaluate_contractor_risk(
        suspicious_projects=contractor_suspicious_count,
        red_flagged_projects=contractor_red_flags,
        delayed_projects=contractor_delayed_count,
        total_projects=contractor_total_projects,
        contractor_name=contractor_name
    )
    if contractor_res["flagged"]:
        signals.append(contractor_res["signal"])
        points_breakdown["agencyConcentrationScore"] = contractor_res["signal"]["scoreImpact"]
    else:
        points_breakdown["agencyConcentrationScore"] = 0

    # Aggregate base points
    total_impact = sum(s["scoreImpact"] for s in signals)
    
    # Scale and bound to 0-100
    if len(signals) >= 3:
        # Multi-signal compounding factor
        final_score = min(100, int(total_impact * 1.15))
    else:
        final_score = min(100, total_impact)

    # Classification thresholds
    # 0–29: LOW, 30–59: MEDIUM, 60–79: HIGH, 80–100: RED_FLAG
    if final_score >= 80:
        risk_level = "RED_FLAG"
    elif final_score >= 60:
        risk_level = "HIGH"
    elif final_score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Human-readable summary
    if risk_level == "RED_FLAG":
        summary_text = f"Project requires urgent investigation. Detected {len(signals)} independent risk signals with compound score {final_score}/100."
    elif risk_level == "HIGH":
        summary_text = f"High risk project ({final_score}/100). Surface indicators suggest anomalous expenditure or execution divergence requiring administrative review."
    elif risk_level == "MEDIUM":
        summary_text = f"Moderate risk ({final_score}/100). Minor timeline, cost, or progress variances detected; continuous monitoring advised."
    else:
        summary_text = f"Low risk ({final_score}/100). Parameters within standard MPLADS benchmarks."

    return {
        "overall_score": final_score,
        "risk_level": risk_level,
        "confidence_score": 0.91 if len(signals) >= 2 else 0.85,
        "signals": signals,
        "breakdown": points_breakdown,
        "summary_text": summary_text,
        "requires_investigation": risk_level == "RED_FLAG"
    }
