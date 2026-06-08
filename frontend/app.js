/* ═══════════════════════════════════════════
   PNEUMOAI — JAVASCRIPT
   sections: config · navigation · chatbot · analysis
═══════════════════════════════════════════ */

/* ══════════════════════════════════════════
   CONFIGURATION
══════════════════════════════════════════ */
var API_BASE = 'http://localhost:5000';

/* ══════════════════════════════════════════
   NAVIGATION
══════════════════════════════════════════ */
function goPage(name, btn) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(name).classList.add('active');
  document.querySelectorAll('.nl, .nav-pill').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  window.scrollTo(0, 0);
}

function goTo(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/* ══════════════════════════════════════════
   VOICE — Speech to Text + Text to Speech
══════════════════════════════════════════ */

var recognition = null;
var isListening = false;

// ── Setup Speech Recognition (mic input) ────────────────────────────────────
function setupVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return null;

  const r = new SpeechRecognition();
  r.lang = 'en-US';
  r.continuous = false;
  r.interimResults = false;

  r.onresult = function(event) {
    const transcript = event.results[0][0].transcript;
    document.getElementById('chatInp').value = transcript;
    stopListening();
    // Auto-send after voice input
    sendChat();
  };

  r.onerror = function() {
    stopListening();
    addMsg("Sorry, I couldn't hear you. Please try again or type your question.", 'bot');
  };

  r.onend = function() {
    stopListening();
  };

  return r;
}

function startListening() {
  if (!recognition) recognition = setupVoiceInput();
  if (!recognition) {
    alert("Voice input is not supported in this browser. Please use Chrome.");
    return;
  }
  isListening = true;
  document.getElementById('micBtn').classList.add('listening');
  document.getElementById('chatInp').placeholder = 'Listening...';
  recognition.start();
}

function stopListening() {
  isListening = false;
  const btn = document.getElementById('micBtn');
  if (btn) btn.classList.remove('listening');
  const inp = document.getElementById('chatInp');
  if (inp) inp.placeholder = 'Type or speak your question...';
  if (recognition) {
    try { recognition.stop(); } catch(e) {}
  }
}

function toggleVoice() {
  if (isListening) {
    stopListening();
  } else {
    startListening();
  }
}

// ── Text to Speech (bot response read aloud) 
function speak(text) {
  if (!window.speechSynthesis) return;
  // Cancel any ongoing speech first
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'en-US';
  utterance.rate = 0.95;
  utterance.pitch = 1;

  // Pick a clear voice if available
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v =>
    v.lang === 'en-US' && (v.name.includes('Female') || v.name.includes('Samantha') || v.name.includes('Google'))
  );
  if (preferred) utterance.voice = preferred;

  window.speechSynthesis.speak(utterance);
}

/* ══════════════════════════════════════════
   CHATBOT
══════════════════════════════════════════ */
function addMsg(text, cls) {
  const container = document.getElementById('chatMsgs');
  const div = document.createElement('div');
  div.className = 'msg ' + cls;
  div.textContent = text;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function addTyping() {
  const container = document.getElementById('chatMsgs');
  const div = document.createElement('div');
  div.className = 'msg bot';
  div.id = 'typingIndicator';
  div.textContent = '...';
  div.style.opacity = '0.5';
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function sendToBackend(msg) {
  const typing = addTyping();

  fetch(API_BASE + '/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: msg })
  })
    .then(res => res.json())
    .then(data => {
      typing.remove();
      const response = data.response || "I'm sorry, I couldn't process that.";
      addMsg(response, 'bot');
      speak(response);
    })
    .catch(() => {
      typing.remove();
      addMsg("Sorry, I couldn't reach the server. Please make sure the backend is running.", 'bot');
    });
}

function sendQ(text) {
  addMsg(text, 'user');
  sendToBackend(text);
}

function sendChat() {
  const input = document.getElementById('chatInp');
  const msg = input.value.trim();
  if (!msg) return;
  addMsg(msg, 'user');
  input.value = '';
  sendToBackend(msg);
}

/* 
   ANALYSIS PAGE
 */
function handleFile(input) {
  if (!input.files || !input.files[0]) return;
  const file = input.files[0];
  document.getElementById('upTitle').textContent = file.name;
  document.getElementById('upSub').textContent =
    (file.size / 1024).toFixed(1) + ' KB · Ready to analyze';
  document.getElementById('upZone').classList.add('has-file');
  document.getElementById('analyzeBtn').disabled = false;
}

function runAnalysis() {
  document.getElementById('analyzeBtn').style.display = 'none';
  document.getElementById('upZone').style.display = 'none';
  document.getElementById('loading').classList.add('show');

  const formData = new FormData();
  formData.append('file', document.getElementById('fi').files[0]);

  fetch(API_BASE + '/api/analyze', {
    method: 'POST',
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      document.getElementById('loading').classList.remove('show');
      if (data.error) {
        alert('Analysis error: ' + data.error);
        resetAnalysis();
        return;
      }
      const score = Math.round(data.pneumonia_prob * 100);
      showResults(score, data.report, data.recommendations);
    })
    .catch(() => {
      document.getElementById('loading').classList.remove('show');
      alert('Could not connect to the server.\nMake sure the Flask backend is running on ' + API_BASE);
      resetAnalysis();
    });
}

function showResults(score, report, recs) {
  document.getElementById('results').classList.add('show');

  const icon  = document.getElementById('resIcon');
  const title = document.getElementById('resTitle');
  const sub   = document.getElementById('resSub');

  if (score >= 60) {
    icon.style.background = 'var(--r50)';
    icon.innerHTML = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
            stroke="#B02E2E" stroke-width="1.5" stroke-linecap="round"/></svg>`;
    title.textContent = 'Pneumonia Detected';
    sub.textContent   = 'AI has identified pneumonia indicators in this scan';
  } else {
    icon.style.background = 'var(--g50)';
    icon.innerHTML = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            stroke="#0D7A50" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
    title.textContent = 'No Pneumonia Detected';
    sub.textContent   = 'AI found no significant indicators of pneumonia';
  }

  const bar = document.getElementById('scoreBar');
  const val = document.getElementById('scoreVal');
  val.textContent      = score + '%';
  val.style.color      = score >= 60 ? 'var(--r600)' : 'var(--g600)';
  bar.style.background = score >= 60 ? '#E04444' : 'var(--g400)';
  setTimeout(() => { bar.style.width = score + '%'; }, 120);

  document.getElementById('repText').textContent = report ||
    'Report not available. Please try again.';

  const list = document.getElementById('recList');
  list.innerHTML = '';
  (recs || []).forEach((text, i) => {
    list.innerHTML += `<div class="rec-row"><div class="rec-num">${i + 1}</div><span>${text}</span></div>`;
  });

  document.getElementById('clinicsBlock').style.display = score >= 60 ? 'block' : 'none';
}

function openMaps(type) {
  const query = type === 'hospital' ? 'hospitals+near+me' : 'pulmonology+clinic+near+me';
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      pos => window.open(`https://www.google.com/maps/search/${query}/@${pos.coords.latitude},${pos.coords.longitude},14z`, '_blank'),
      ()  => window.open(`https://www.google.com/maps/search/${query}`, '_blank')
    );
  } else {
    window.open(`https://www.google.com/maps/search/${query}`, '_blank');
  }
}

function resetAnalysis() {
  document.getElementById('results').classList.remove('show');
  document.getElementById('upZone').style.display = '';
  document.getElementById('upZone').classList.remove('has-file');
  document.getElementById('analyzeBtn').style.display = '';
  document.getElementById('analyzeBtn').disabled = true;
  document.getElementById('upTitle').textContent = 'Drop your X-ray here, or click to browse';
  document.getElementById('upSub').textContent   = 'Supports JPEG, PNG, DICOM formats';
  document.getElementById('fi').value            = '';
  document.getElementById('scoreBar').style.width = '0%';
  document.getElementById('clinicsBlock').style.display = 'none';
}
