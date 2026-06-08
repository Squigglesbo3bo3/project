"""
PneumoAI — Flask Backend
"""

import os
import re
import json
import random
import numpy as np

from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import tensorflow as tf

from diagnosis import diagnose

# ── App setup
app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Load X-ray model 
MODEL_PATH  = os.path.join(BASE_DIR, "Final_Pneumonia_Model_EN.keras")
xray_model  = tf.keras.models.load_model(MODEL_PATH)
IMG_SIZE    = (224, 224)
CLASS_NAMES = ["NORMAL", "PNEUMONIA"]
print("✅ X-ray model loaded.")

# ── Load chatbot intents 
INTENTS_PATH = os.path.join(BASE_DIR, "intents.json")
with open(INTENTS_PATH, "r", encoding="utf-8") as f:
    intents_data = json.load(f)

intent_responses = {}
intent_patterns  = {}
for intent in intents_data["intents"]:
    tag = intent["tag"]
    intent_responses[tag] = intent["responses"]
    intent_patterns[tag]  = intent["patterns"]

print("✅ Chatbot intents loaded.")

# ── Helpers 
def preprocess_image(file_storage):
    img = Image.open(file_storage.stream).convert("RGB")
    img = img.resize(IMG_SIZE)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)

def _tokenize(text):
    return set(re.findall(r"[a-zA-Z']+", text.lower()))

def get_chatbot_response(user_message):
    user_input = user_message.lower().strip()

    # Step 1: Regex exact match
    for tag, patterns in intent_patterns.items():
        for pattern in patterns:
            regex_pattern = r'\b' + re.escape(pattern.lower()) + r'\b'
            if re.search(regex_pattern, user_input):
                return " ".join(intent_responses[tag])

    # Step 2: Token overlap fallback
    user_tokens = _tokenize(user_input)
    best_tag, best_score = None, 0
    for tag, patterns in intent_patterns.items():
        for pattern in patterns:
            score = len(user_tokens & _tokenize(pattern))
            if score > best_score:
                best_score, best_tag = score, tag

    if best_score >= 2 and best_tag:
        return " ".join(intent_responses[best_tag])

    return ("I'm not sure how to respond to that. "
            "You can ask me about pneumonia symptoms, treatment, prevention, or emergency signs.")

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "PneumoAI backend is running ✅"})

def generate_report_and_recs(predicted_class, pneumonia_prob):
    """
    Generates a dynamic medical report and recommendations
    based on the model's prediction and confidence level.
    """
    prob_pct = round(pneumonia_prob * 100, 1)

    if predicted_class == "PNEUMONIA":
        if pneumonia_prob >= 0.85:
            severity = "high"
            report = (
                f"The AI model has detected strong indicators of pneumonia with {prob_pct}% confidence. "
                "Significant consolidation and bilateral infiltrates are present in the lung fields. "
                "Air bronchograms are visible, consistent with bacterial pneumonia. "
                "Immediate medical attention is strongly advised."
            )
            recs = [
                "Seek emergency or urgent medical care immediately.",
                "Do not self-medicate — a physician must prescribe the correct antibiotics.",
                "Monitor oxygen saturation levels closely; go to ER if below 94%.",
                "Rest in bed, stay well-hydrated, and use a cool-mist humidifier.",
                "Follow up with a chest X-ray in 2–4 weeks to confirm recovery.",
            ]
        elif pneumonia_prob >= 0.60:
            severity = "medium"
            report = (
                f"The AI model has detected probable pneumonia with {prob_pct}% confidence. "
                "Patchy infiltrates are visible in one or more lung regions. "
                "Clinical correlation with symptoms and physical examination is recommended "
                "to confirm the diagnosis and determine severity."
            )
            recs = [
                "Schedule an appointment with a physician or pulmonologist as soon as possible.",
                "Do not self-medicate — antibiotic therapy must be prescribed by a doctor.",
                "Rest, stay well-hydrated, and monitor your temperature and breathing.",
                "Follow up with a chest X-ray in 4–6 weeks to confirm resolution.",
                "Go to the emergency room if you experience severe shortness of breath or bluish lips.",
            ]
        else:
            severity = "low"
            report = (
                f"The AI model has detected possible early-stage pneumonia with {prob_pct}% confidence. "
                "Subtle changes in lung opacity may be present, but findings are not conclusive. "
                "A clinical examination by a physician is recommended for accurate diagnosis."
            )
            recs = [
                "Consult a physician for a full clinical evaluation.",
                "Monitor your symptoms over the next 24–48 hours.",
                "Rest and stay hydrated.",
                "Return for a repeat X-ray if symptoms worsen.",
                "Avoid contact with vulnerable individuals (elderly, children) until cleared.",
            ]
    else:
        severity = "normal"
        report = (
            f"The AI model found no significant indicators of pneumonia ({prob_pct}% pneumonia probability). "
            "Both lung fields appear clear with no visible consolidation or infiltrates. "
            "The cardiac silhouette is within normal limits. No pleural effusion detected. "
            "Results should still be reviewed by a qualified physician."
        )
        recs = [
            "Results appear normal — continue monitoring if symptoms persist.",
            "Consult a physician if you still experience breathing difficulties or fever.",
            "Maintain good hygiene and consider pneumococcal and flu vaccinations.",
            "Avoid smoking and maintain a healthy immune system.",
            "Return for a follow-up X-ray if symptoms do not improve within 1 week.",
        ]

    return report, recs, severity


@app.route("/api/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400
    try:
        img_array       = preprocess_image(file)
        preds           = xray_model.predict(img_array)[0]
        normal_prob     = float(preds[0])
        pneumonia_prob  = float(preds[1])
        predicted_class = CLASS_NAMES[int(np.argmax(preds))]
        confidence      = float(np.max(preds))

        report, recs, severity = generate_report_and_recs(predicted_class, pneumonia_prob)

        return jsonify({
            "prediction":     predicted_class,
            "probability":    round(confidence, 4),
            "normal_prob":    round(normal_prob, 4),
            "pneumonia_prob": round(pneumonia_prob, 4),
            "report":         report,
            "recommendations": recs,
            "severity":       severity,
        })
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return jsonify({"error": "Send JSON with a 'message' field."}), 400
    user_message = str(data["message"]).strip()
    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400
    response = get_chatbot_response(user_message)
    return jsonify({"response": response})

@app.route("/api/diagnose", methods=["POST"])
def diagnose_route():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Send a JSON body."}), 400
    symptoms  = data.get("symptoms", [])
    cv_result = data.get("cv_result", None)
    if cv_result:
        cv_result = {
            "prediction":  cv_result.get("prediction", "").lower(),
            "probability": float(cv_result.get("probability", 0)),
        }
    result = diagnose(symptoms, cv_result)
    return jsonify(result)

# ── Run 
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
