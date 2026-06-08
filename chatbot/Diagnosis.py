"""
diagnosis.py  —  v2
--------------------
Combines NLP symptoms + CV X-ray result → Risk level (Low / Medium / High)

Improvements :
  1. Symptom normalization  — maps similar phrases to standard symptoms
  2. Dynamic X-ray scoring  — weight changes based on symptom count
  3. Confidence score       — how sure we are about the result
  4. Edge case handling     — works even with no symptoms or no X-ray
"""


SYMPTOM_ALIASES = {
    # Breathing
    "short breath"          : "shortness of breath",
    "shortness of breath"   : "shortness of breath",
    "breathing problem"     : "shortness of breath",
    "cant breathe"          : "difficulty breathing",
    "can't breathe"         : "difficulty breathing",
    "hard to breathe"       : "difficulty breathing",
    "difficulty breathing"  : "difficulty breathing",
    "breathing difficulty"  : "difficulty breathing",

    # Chest
    "chest pain"            : "chest pain",
    "chest ache"            : "chest pain",
    "chest tightness"       : "chest pain",
    "tight chest"           : "chest pain",

    # Fever
    "high fever"            : "high fever",
    "fever"                 : "fever",
    "high temperature"      : "high fever",
    "temperature"           : "fever",

    # Cough
    "cough"                 : "cough",
    "coughing"              : "cough",
    "dry cough"             : "cough",
    "wet cough"             : "cough",
    "coughing blood"        : "coughing blood",

    # Other
    "confusion"             : "confusion",
    "confused"              : "confusion",
    "bluish lips"           : "bluish lips",
    "blue lips"             : "bluish lips",
    "fatigue"               : "fatigue",
    "tired"                 : "fatigue",
    "chills"                : "chills",
    "sweating"              : "sweating",
    "loss of appetite"      : "loss of appetite",
    "no appetite"           : "loss of appetite",
    "rapid breathing"       : "rapid breathing",
    "fast breathing"        : "rapid breathing",
    "wheezing"              : "wheezing",
}


HIGH_RISK_SYMPTOMS = {
    "difficulty breathing",
    "shortness of breath",
    "chest pain",
    "confusion",
    "high fever",
    "bluish lips",
    "coughing blood",
}

MEDIUM_RISK_SYMPTOMS = {
    "cough",
    "fever",
    "fatigue",
    "chills",
    "sweating",
    "loss of appetite",
    "rapid breathing",
    "wheezing",
}


#normalize symptoms
def normalize_symptoms(symptoms: list) -> list:
    """
    Converts raw symptom phrases → standard symptom names.
    e.g. "breathing problem" → "shortness of breath"
    """
    normalized = []
    for s in symptoms:
        s_lower = s.lower().strip()
        standard = SYMPTOM_ALIASES.get(s_lower, s_lower)  # fallback: keep as-is
        normalized.append(standard)
    return normalized


#  dynamic X-ray score 
def xray_score(prediction: str, probability: float, symptom_count: int) -> tuple:
    """
    Returns (score, reason).
    X-ray weight increases when more symptoms are present.
    """
    if prediction != "pneumonia":
        return 0, "X-ray appears normal — no pneumonia detected"

    
    if probability >= 0.8:
        base = 3
        label = "Strongly Suggest"
    elif probability >= 0.5:
        base = 2
        label = "suggests possible"
    else:
        base = 1
        label = "shows weak signal of"

    # Boost: if 3+ symptoms, X-ray carries more weight
    boost = 1 if symptom_count >= 3 else 0
    total = base + boost

    reason = (
        f"X-ray {label} pneumonia ({probability:.0%} confidence)"
        + (" — boosted: multiple symptoms present" if boost else "")
    )
    return total, reason


# confidence calculation 
def calculate_confidence(score: int, symptom_count: int, has_xray: bool) -> str:
    """
    Returns a confidence label based on how much data we have.
    """
    if not has_xray and symptom_count == 0:
        return "Very Low — no data provided"
    if not has_xray:
        return "Low — based on symptoms only, no X-ray"
    if symptom_count == 0:
        return "Medium — based on X-ray only, no symptoms reported"
    if symptom_count >= 3 and has_xray:
        return "High — symptoms + X-ray both available"
    return "Medium — limited data"



def diagnose(symptoms: list, cv_result: dict = None) -> dict:
   
 
    if not symptoms and not cv_result:
        return {
            "risk_level" : "Unknown",
            "score"      : 0,
            "confidence" : "Very Low — no data provided",
            "reasons"    : ["No symptoms or X-ray data was provided."],
        }

    score   = 0
    reasons = []

    
    normalized = normalize_symptoms(symptoms) if symptoms else []

   
    for symptom in normalized:
        if symptom in HIGH_RISK_SYMPTOMS:
            score += 2
            reasons.append(f"High-risk symptom detected: '{symptom}'")
        elif symptom in MEDIUM_RISK_SYMPTOMS:
            score += 1
            reasons.append(f"Symptom detected: '{symptom}'")

   
    has_xray = bool(cv_result)

    if has_xray:
        prediction  = cv_result.get("prediction", "").lower()
        probability = float(cv_result.get("probability", 0))
        xray_pts, xray_reason = xray_score(prediction, probability, len(normalized))
        score += xray_pts
        reasons.append(xray_reason)
    else:
        reasons.append("No X-ray provided — diagnosis based on symptoms only")

    if not normalized:
        reasons.append("No symptoms reported — result relies entirely on X-ray")

    
    if score >= 5:
        risk_level = "High"
    elif score >= 3:
        risk_level = "Medium"
    elif score > 0:
        risk_level = "Low"
    else:
        risk_level = "Unknown"

    
    confidence = calculate_confidence(score, len(normalized), has_xray)

    return {
        "risk_level" : risk_level,
        "score"      : score,
        "confidence" : confidence,
        "reasons"    : reasons,
    }


# ── Tests 
if __name__ == "__main__":

    tests = [
        {
            "label"    : "Test 1 — High risk (raw phrases, strong X-ray)",
            "symptoms" : ["chest pain", "hard to breathe", "fever"],
            "cv"       : {"prediction": "pneumonia", "probability": 0.82},
        },
        {
            "label"    : "Test 2 — Medium risk",
            "symptoms" : ["cough", "tired"],
            "cv"       : {"prediction": "pneumonia", "probability": 0.65},
        },
        {
            "label"    : "Test 3 — Low risk (normal X-ray)",
            "symptoms" : ["cough"],
            "cv"       : {"prediction": "normal", "probability": 0.1},
        },
        {
            "label"    : "Test 4 — No X-ray provided",
            "symptoms" : ["chest tightness", "fast breathing", "high temperature"],
            "cv"       : None,
        },
        {
            "label"    : "Test 5 — No symptoms, only X-ray",
            "symptoms" : [],
            "cv"       : {"prediction": "pneumonia", "probability": 0.75},
        },
        {
            "label"    : "Test 6 — No data at all",
            "symptoms" : [],
            "cv"       : None,
        },
        {
            "label"    : "Test 7 — Boost: 3+ symptoms + strong X-ray",
            "symptoms" : ["breathing problem", "chest ache", "high temperature", "coughing"],
            "cv"       : {"prediction": "pneumonia", "probability": 0.85},
        },
    ]

    for t in tests:
        print(f"\n{'─'*55}")
        print(f"{t['label']}")
        result = diagnose(t["symptoms"], t["cv"])
        print(f"  Risk       : {result['risk_level']}")
        print(f"  Score      : {result['score']}")
        print(f"  Confidence : {result['confidence']}")
        print(f"  Reasons:")
        for r in result["reasons"]:
            print(f"    • {r}")