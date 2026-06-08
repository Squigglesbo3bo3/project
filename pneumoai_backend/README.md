# PneumoAI — Backend Setup

## Folder structure

```
pneumoai_backend/
├── app.py
├── diagnosis.py               ← copy your Diagnosis.py here, rename it
├── intents.json               ← copy from NLP project
├── Final_Pneumonia_Model_EN.keras  ← copy your model here
├── requirements.txt
└── README.md
```

---

## Setup steps

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Copy your files into the folder
| File | Source |
|------|--------|
| `Final_Pneumonia_Model_EN.keras` | Your CV model |
| `intents.json` | Your NLP project |
| `diagnosis.py` | Your `Diagnosis.py` (just rename it) |

### 3. Run the server
```bash
python app.py
```
Server starts at: **http://localhost:5000**

---

## API Endpoints

### `POST /api/analyze`
Analyzes a chest X-ray image.

**Request:** `multipart/form-data`
| Field | Type | Description |
|-------|------|-------------|
| `file` | image | Chest X-ray (JPEG / PNG) |

**Response:**
```json
{
  "prediction":     "PNEUMONIA",
  "probability":    0.87,
  "normal_prob":    0.13,
  "pneumonia_prob": 0.87
}
```

---

### `POST /api/chat`
Gets a chatbot response.

**Request:** `application/json`
```json
{ "message": "What are the symptoms of pneumonia?" }
```

**Response:**
```json
{ "response": "Common symptoms include fever, cough, and shortness of breath." }
```

---

### `POST /api/diagnose`
Combines symptoms + X-ray result into a risk level.

**Request:** `application/json`
```json
{
  "symptoms": ["chest pain", "fever", "cough"],
  "cv_result": {
    "prediction":  "PNEUMONIA",
    "probability": 0.87
  }
}
```
> Both `symptoms` and `cv_result` are optional.

**Response:**
```json
{
  "risk_level":  "High",
  "score":       7,
  "confidence":  "High — symptoms + X-ray both available",
  "reasons": [
    "High-risk symptom detected: 'chest pain'",
    "Symptom detected: 'fever'",
    "X-ray Strongly Suggest pneumonia (87% confidence)"
  ]
}
```

---

## Connecting the Frontend

In your `app.js`, replace the `TODO` block inside `runAnalysis()` with:

```javascript
async function runAnalysis() {
  document.getElementById('analyzeBtn').style.display = 'none';
  document.getElementById('upZone').style.display = 'none';
  document.getElementById('loading').classList.add('show');

  const formData = new FormData();
  formData.append('file', document.getElementById('fi').files[0]);

  try {
    const res  = await fetch('http://localhost:5000/api/analyze', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();

    document.getElementById('loading').classList.remove('show');

    const score = Math.round(data.pneumonia_prob * 100);
    showResults(score, null, null);

  } catch (err) {
    console.error('Analysis error:', err);
    document.getElementById('loading').classList.remove('show');
    alert('Could not connect to the server. Make sure the backend is running.');
  }
}
```

And replace `sendChat()` with:

```javascript
async function sendChat() {
  const input = document.getElementById('chatInp');
  const msg   = input.value.trim();
  if (!msg) return;
  addMsg(msg, 'user');
  input.value = '';

  try {
    const res  = await fetch('http://localhost:5000/api/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ message: msg })
    });
    const data = await res.json();
    addMsg(data.response, 'bot');
  } catch (err) {
    addMsg("Sorry, I couldn't reach the server right now.", 'bot');
  }
}
```
