/** 
 * @param {string} name  - page id
 * @param {HTMLElement|null} btn - the nav button that was clicked
 */
function goPage(name, btn) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(name).classList.add('active');
  document.querySelectorAll('.nl, .nav-pill').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  window.scrollTo(0, 0);
}

/**
 
 * @param {string} id
 */
function goTo(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}



const botReplies = {
  symptoms:
    'Pneumonia symptoms include high fever, chills, a productive cough (often with yellow or green mucus), shortness of breath, sharp chest pain, and fatigue. Symptoms typically worsen over 48–72 hours.',

  treatment:
    'Bacterial pneumonia is treated with antibiotics. Viral pneumonia may require antivirals or supportive care. Rest, fluids, and monitoring oxygen levels are also important. Hospitalization may be needed for severe cases.',

  prevention:
    'Key prevention steps: get vaccinated (pneumococcal and flu vaccines), wash hands regularly, avoid smoking, and maintain a healthy immune system through diet and sleep.',

  emergency:
    'Seek emergency care immediately if you notice: severe difficulty breathing, bluish lips or fingernails, confusion or disorientation, very low oxygen saturation, or a high fever that does not respond to medication.',

  xray:
    'On a chest X-ray, pneumonia shows as white or hazy patches called infiltrates or consolidations. Our AI is trained on thousands of scans to detect these patterns and estimate infection probability.',

  default:
    "That's a great question. Pneumonia is a serious but treatable infection when caught early. I'd recommend uploading a chest X-ray for a more specific assessment, or consulting a physician for a full diagnosis."
};

/**
 * Match user message to a reply category.
 * @param {string} msg
 * @returns {string}
 */
function getReply(msg) {
  const m = msg.toLowerCase();
  if (m.match(/symptom|sign|fever|cough|breath|chest pain/))      return botReplies.symptoms;
  if (m.match(/treat|medic|antibiotic|cure|recover/))             return botReplies.treatment;
  if (m.match(/prevent|vaccin|avoid|protect/))                    return botReplies.prevention;
  if (m.match(/emergency|urgent|severe|danger|serious|er |e\.r/)) return botReplies.emergency;
  if (m.match(/xray|x-ray|x ray|scan|image|upload|analys/))       return botReplies.xray;
  return botReplies.default;
}

/**
 
 * @param {string} text
 * @param {'bot'|'user'} cls
 */
function addMsg(text, cls) {
  const container = document.getElementById('chatMsgs');
  const div = document.createElement('div');
  div.className = `msg ${cls}`;
  div.textContent = text;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

/**
 
 * @param {string} text
 */
function sendQ(text) {
  addMsg(text, 'user');
  setTimeout(() => addMsg(getReply(text), 'bot'), 650);
}


function sendChat() {
  const input = document.getElementById('chatInp');
  const msg = input.value.trim();
  if (!msg) return;
  addMsg(msg, 'user');
  input.value = '';
  setTimeout(() => addMsg(getReply(msg), 'bot'), 650);
}


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

  
  setTimeout(() => {
    document.getElementById('loading').classList.remove('show');
    showResults(87, null, null); // pass real data from backend here
  }, 2600);
}

/**
 * Render the results section.
 * @param {number}   score            - 0–100 confidence from model
 * @param {string|null} report        - medical report text (null = use placeholder)
 * @param {string[]|null} recs        - recommendations array (null = use placeholder)
 */
function showResults(score, report, recs) {
  const results = document.getElementById('results');
  results.classList.add('show');

  // ── Severity label & icon colour ────────────────────────────────────
  const icon  = document.getElementById('resIcon');
  const title = document.getElementById('resTitle');
  const sub   = document.getElementById('resSub');

  if (score >= 60) {
    icon.style.background = 'var(--r50)';
    icon.innerHTML = `
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
        <path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
              stroke="#B02E2E" stroke-width="1.5" stroke-linecap="round"/>
      </svg>`;
    title.textContent = 'Pneumonia Detected';
    sub.textContent   = 'AI has identified pneumonia indicators in this scan';
  } else {
    icon.style.background = 'var(--g50)';
    icon.innerHTML = `
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
        <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              stroke="#0D7A50" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>`;
    title.textContent = 'No Pneumonia Detected';
    sub.textContent   = 'AI found no significant indicators of pneumonia';
  }

  
  const bar = document.getElementById('scoreBar');
  const val = document.getElementById('scoreVal');
  val.textContent  = score + '%';
  val.style.color  = score >= 60 ? 'var(--r600)' : 'var(--g600)';
  bar.style.background = score >= 60 ? '#E04444' : 'var(--g400)';
  setTimeout(() => { bar.style.width = score + '%'; }, 120);

  
  document.getElementById('repText').textContent = report ||
    'The AI model has detected bilateral infiltrates predominantly in the right lower lobe, ' +
    'consistent with bacterial pneumonia. Consolidation is visible with air bronchograms present. ' +
    'The left lung appears within normal limits. Cardiac silhouette is normal. No pleural effusion detected.';

  
  const defaultRecs = [
    'See a physician or pulmonologist as soon as possible for clinical evaluation.',
    'Do not self-medicate — antibiotic therapy should be prescribed by a doctor.',
    'Rest, stay well-hydrated, and monitor your oxygen saturation regularly.',
    'Follow up with a chest X-ray in 4–6 weeks to confirm resolution.',
    'Go to the emergency room immediately if you experience severe breathing difficulty, bluish lips, or confusion.'
  ];

  const list = document.getElementById('recList');
  list.innerHTML = '';
  (recs || defaultRecs).forEach((text, i) => {
    list.innerHTML +=
      `<div class="rec-row">
         <div class="rec-num">${i + 1}</div>
         <span>${text}</span>
       </div>`;
  });

 
  document.getElementById('clinicsBlock').style.display = score >= 60 ? 'block' : 'none';
}

/**
 google maps
 * @param {'hospital'|'pulmonologist'} type
 */
function openMaps(type) {
  const query = type === 'hospital'
    ? 'hospitals+near+me'
    : 'pulmonology+clinic+near+me';

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      pos => {
        const { latitude: lat, longitude: lng } = pos.coords;
        window.open(
          `https://www.google.com/maps/search/${query}/@${lat},${lng},14z`,
          '_blank'
        );
      },
      () => {
       
        window.open(`https://www.google.com/maps/search/${query}`, '_blank');
      }
    );
  } else {
    window.open(`https://www.google.com/maps/search/${query}`, '_blank');
  }
}


function resetAnalysis() {
  document.getElementById('results').classList.remove('show');
  document.getElementById('upZone').style.display  = '';
  document.getElementById('upZone').classList.remove('has-file');
  document.getElementById('analyzeBtn').style.display = '';
  document.getElementById('analyzeBtn').disabled = true;
  document.getElementById('upTitle').textContent = 'Drop your X-ray here, or click to browse';
  document.getElementById('upSub').textContent   = 'Supports JPEG, PNG, DICOM formats';
  document.getElementById('fi').value            = '';
  document.getElementById('scoreBar').style.width = '0%';
  document.getElementById('clinicsBlock').style.display = 'none';
}
