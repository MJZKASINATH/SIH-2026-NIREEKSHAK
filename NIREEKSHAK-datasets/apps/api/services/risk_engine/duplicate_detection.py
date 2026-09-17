from typing import Dict, Any, List, Optional
import math

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns distance in meters between two lat/lon coordinates."""
    if not (lat1 and lon1 and lat2 and lon2):
        return 999999.0
    R = 6371000.0 # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def evaluate_duplicate_detection(
    description: str,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    peer_projects: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Checks semantic similarity and geographic proximity against registered works.
    Flags identical or near-identical works proposed at the same physical location.
    """
    if not description or not peer_projects:
        return {"score": 0, "flagged": False, "signal": None, "matches": []}

    matches = []
    desc_lower = description.lower()

    for p in peer_projects:
        p_desc = p.get("description", "").lower()
        if not p_desc or p.get("id") == p.get("current_id"):
            continue

        # Text overlap heuristic
        words_curr = set(desc_lower.split())
        words_peer = set(p_desc.split())
        if not words_curr or not words_peer:
            continue

        jaccard = len(words_curr & words_peer) / len(words_curr | words_peer)
        
        # Spatial distance check if coordinates exist
        dist = 999999.0
        if lat and lng and p.get("latitude") and p.get("longitude"):
            dist = calculate_haversine_distance(lat, lng, p["latitude"], p["longitude"])

        if jaccard >= 0.70 or (jaccard >= 0.45 and dist <= 300.0):
            matches.append({
                "project_id": p.get("id"),
                "description": p.get("description"),
                "similarity_score": round(jaccard, 2),
                "distance_meters": round(dist, 1) if dist < 900000 else None
            })

    score = 0
    signal = None
    if matches:
        top_match = max(matches, key=lambda x: x["similarity_score"])
        score = int(top_match["similarity_score"] * 100)
        dist_str = f" located {top_match['distance_meters']:.0f}m away" if top_match.get("distance_meters") else ""
        signal = {
            "type": "DUPLICATE_WORK",
            "title": "High Work Similarity Detected",
            "severity": "CRITICAL" if score >= 80 else "HIGH",
            "scoreImpact": 18,
            "description": f"Strong semantic similarity ({int(top_match['similarity_score']*100)}%) with existing project [{top_match['project_id']}]{dist_str}. Potential duplicate sanction."
        }

    return {
        "score": score,
        "matches": matches,
        "flagged": signal is not None,
        "signal": signal
    }
