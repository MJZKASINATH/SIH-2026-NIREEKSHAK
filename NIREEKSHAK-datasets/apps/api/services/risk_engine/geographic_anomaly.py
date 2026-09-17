from typing import Dict, Any, List, Optional
import math

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    if None in (lat1, lon1, lat2, lon2):
        return 0.0
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0)**2
    return R * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

def evaluate_geographic_anomaly(
    expected_lat: Optional[float],
    expected_lng: Optional[float],
    submitted_lat: Optional[float],
    submitted_lng: Optional[float],
    exif_lat: Optional[float] = None,
    exif_lng: Optional[float] = None,
    checkpoints: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Evaluates geospatial consistency:
    1. Distance between submitted field photo and registered project coordinates.
    2. Discrepancy between device-captured GPS and EXIF image metadata.
    3. Checkpoint verification ratio.
    """
    score = 0
    signals = []

    # 1. Project-level boundary check
    distance_to_project = 0.0
    if expected_lat and expected_lng and submitted_lat and submitted_lng:
        distance_to_project = haversine(expected_lat, expected_lng, submitted_lat, submitted_lng)
        # If photo is submitted > 1000m (1km) from registered project site
        if distance_to_project > 1000.0:
            score = max(score, min(100, int(30 + (distance_to_project / 1000.0) * 10)))
            signals.append({
                "type": "GEOSPATIAL_ANOMALY",
                "title": "Geofence Boundary Violation",
                "severity": "CRITICAL" if distance_to_project > 5000.0 else "HIGH",
                "scoreImpact": 20,
                "description": f"Field evidence was uploaded {distance_to_project/1000.0:.1f} km away from registered project coordinates ({expected_lat:.4f}, {expected_lng:.4f}). Severe location mismatch."
            })

    # 2. Metadata tamper check: device GPS vs EXIF GPS
    exif_discrepancy = 0.0
    if submitted_lat and submitted_lng and exif_lat and exif_lng:
        exif_discrepancy = haversine(submitted_lat, submitted_lng, exif_lat, exif_lng)
        if exif_discrepancy > 500.0:
            score = max(score, 75)
            signals.append({
                "type": "METADATA_SUSPICIOUS",
                "title": "EXIF vs Device GPS Discrepancy",
                "severity": "HIGH",
                "scoreImpact": 15,
                "description": f"Image EXIF GPS ({exif_lat:.4f}, {exif_lng:.4f}) differs by {exif_discrepancy:.0f}m from device upload GPS. Possible image tampering or remote re-upload."
            })

    # 3. Checkpoints status check
    failed_checkpoints = 0
    total_checkpoints = 0
    if checkpoints:
        total_checkpoints = len(checkpoints)
        for cp in checkpoints:
            if cp.get("verification_status") == "MISMATCH":
                failed_checkpoints += 1
        if failed_checkpoints > 0:
            score = max(score, int(failed_checkpoints / total_checkpoints * 80))
            signals.append({
                "type": "CHECKPOINT_FAILURE",
                "title": f"{failed_checkpoints}/{total_checkpoints} Checkpoints Mismatched",
                "severity": "HIGH",
                "scoreImpact": 12,
                "description": f"{failed_checkpoints} field verification checkpoints failed geofence radius tests."
            })

    primary_signal = signals[0] if signals else None
    return {
        "score": score,
        "distance_to_project_meters": round(distance_to_project, 1),
        "exif_discrepancy_meters": round(exif_discrepancy, 1),
        "flagged": primary_signal is not None,
        "signal": primary_signal,
        "all_signals": signals
    }
