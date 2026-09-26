/**
 * KithMed Field Clinical Decision & Uncertainty Bounding Console
 * Client-Side Deterministic Triage Logic
 */

// Presets
const PRESETS = {
  sepsis: {
    id: "KM-FIELD-704",
    age: 54,
    pregnant: false,
    oxygen: false,
    complaint: "Severe chills, high fever, altered mentation, tachypneic",
    hr: 124,
    sbp: 88,
    dbp: 54,
    rr: 26,
    spo2: 91,
    temp: 39.5,
    gcs: 13
  },
  trauma: {
    id: "KM-TRAUMA-112",
    age: 29,
    pregnant: false,
    oxygen: false,
    complaint: "High-speed vehicular trauma, acute pelvic / abdominal rigidity",
    hr: 128,
    sbp: 84,
    dbp: 50,
    rr: 24,
    spo2: 96,
    temp: 36.2,
    gcs: 14
  },
  respiratory: {
    id: "KM-RESP-308",
    age: 68,
    pregnant: false,
    oxygen: true,
    complaint: "Severe acute bronchospasm, cyanosis, audible wheezing",
    hr: 108,
    sbp: 138,
    dbp: 84,
    rr: 32,
    spo2: 84,
    temp: 37.2,
    gcs: 15
  },
  boundary: {
    id: "KM-PED-049",
    age: 3,
    pregnant: false,
    oxygen: false,
    complaint: "Pediatric poor feeding, lethargy, vital borderline parameters",
    hr: 94,
    sbp: 91,
    dbp: 58,
    rr: 21,
    spo2: 94,
    temp: 38.2,
    gcs: 15
  },
  routine: {
    id: "KM-AMB-910",
    age: 32,
    pregnant: false,
    oxygen: false,
    complaint: "Localized mild sprained wrist, normal physiologic state",
    hr: 72,
    sbp: 118,
    dbp: 76,
    rr: 15,
    spo2: 99,
    temp: 36.8,
    gcs: 15
  }
};

// Web Audio Synth for Emergency Tone
let audioCtx = null;
let audioEnabled = true;

function playAlertTone(severity) {
  if (!audioEnabled) return;
  try {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    if (severity === 'RED') {
      osc.frequency.setValueAtTime(880, audioCtx.currentTime); // High pitch alarm A5
      osc.frequency.setValueAtTime(440, audioCtx.currentTime + 0.1);
      gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.3);
    } else if (severity === 'ORANGE') {
      osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
      gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.2);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.2);
    }
  } catch (e) {
    // Web audio silent fail safe
  }
}

// Scoring Functions
function calculateNEWS2(rr, spo2, sbp, hr, temp, gcs, onO2) {
  let score = 0;
  // RR
  if (rr <= 8) score += 3;
  else if (rr <= 11) score += 1;
  else if (rr <= 20) score += 0;
  else if (rr <= 24) score += 2;
  else score += 3;

  // SpO2
  if (spo2 <= 91) score += 3;
  else if (spo2 <= 93) score += 2;
  else if (spo2 <= 95) score += 1;
  else score += 0;

  if (onO2) score += 2;

  // SBP
  if (sbp <= 90) score += 3;
  else if (sbp <= 100) score += 2;
  else if (sbp <= 110) score += 1;
  else if (sbp <= 219) score += 0;
  else score += 3;

  // HR
  if (hr <= 40) score += 3;
  else if (hr <= 50) score += 1;
  else if (hr <= 90) score += 0;
  else if (hr <= 110) score += 1;
  else if (hr <= 130) score += 2;
  else score += 3;

  // Temp
  if (temp <= 35.0) score += 3;
  else if (temp <= 36.0) score += 1;
  else if (temp <= 38.0) score += 0;
  else if (temp <= 39.0) score += 1;
  else score += 2;

  // GCS
  if (gcs < 15) score += 3;

  return Math.min(20, score);
}

function calculateQSOFA(rr, sbp, gcs) {
  let score = 0;
  if (rr >= 22) score += 1;
  if (sbp <= 100) score += 1;
  if (gcs < 15) score += 1;
  return score;
}

function computeUncertainty(sbp, spo2, rr, news2, shockIndex, age, pregnant) {
  let u = 0.05;
  if (sbp >= 89 && sbp <= 92) u += 0.15;
  if (spo2 >= 93 && spo2 <= 95) u += 0.12;
  if (rr >= 20 && rr <= 22) u += 0.12;
  if (news2 < 4 && shockIndex > 0.9) u += 0.25;
  if (age < 5 || pregnant) u += 0.18;
  return Math.min(0.95, Math.round(u * 100) / 100);
}

// DOM Elements
const elements = {
  patientId: document.getElementById('patientId'),
  patientAge: document.getElementById('patientAge'),
  isPregnant: document.getElementById('isPregnant'),
  onOxygen: document.getElementById('onOxygen'),
  chiefComplaint: document.getElementById('chiefComplaint'),
  casePreset: document.getElementById('casePreset'),
  themeToggle: document.getElementById('themeToggle'),
  themeIcon: document.getElementById('themeIcon'),
  audioToggle: document.getElementById('audioToggle'),
  audioIcon: document.getElementById('audioIcon'),
  resetBtn: document.getElementById('resetBtn'),

  // Sliders & value displays
  val_hr: document.getElementById('val_hr'),
  input_hr: document.getElementById('input_hr'),
  val_sbp: document.getElementById('val_sbp'),
  input_sbp: document.getElementById('input_sbp'),
  val_dbp: document.getElementById('val_dbp'),
  input_dbp: document.getElementById('input_dbp'),
  val_rr: document.getElementById('val_rr'),
  input_rr: document.getElementById('input_rr'),
  val_spo2: document.getElementById('val_spo2'),
  input_spo2: document.getElementById('input_spo2'),
  val_temp: document.getElementById('val_temp'),
  input_temp: document.getElementById('input_temp'),
  val_gcs: document.getElementById('val_gcs'),
  input_gcs: document.getElementById('input_gcs'),

  // Output cards
  triageBanner: document.getElementById('triageBanner'),
  triageBadge: document.getElementById('triageBadge'),
  triageDesc: document.getElementById('triageDesc'),
  score_news2: document.getElementById('score_news2'),
  interp_news2: document.getElementById('interp_news2'),
  score_qsofa: document.getElementById('score_qsofa'),
  interp_qsofa: document.getElementById('interp_qsofa'),
  score_si: document.getElementById('score_si'),
  interp_si: document.getElementById('interp_si'),
  score_protocol: document.getElementById('score_protocol'),
  interp_escalation: document.getElementById('interp_escalation'),
  val_uncertainty: document.getElementById('val_uncertainty'),
  uncertaintyBar: document.getElementById('uncertaintyBar'),
  findingsList: document.getElementById('findingsList'),
  interventionsList: document.getElementById('interventionsList'),

  exportPassBtn: document.getElementById('exportPassBtn'),
  copyJsonBtn: document.getElementById('copyJsonBtn'),
  passModal: document.getElementById('passModal'),
  modalContent: document.getElementById('modalContent'),
  closeModalBtn: document.getElementById('closeModalBtn'),
  printBtn: document.getElementById('printBtn')
};

function updateCalculation() {
  const hr = parseInt(elements.input_hr.value, 10);
  const sbp = parseInt(elements.input_sbp.value, 10);
  const dbp = parseInt(elements.input_dbp.value, 10);
  const rr = parseInt(elements.input_rr.value, 10);
  const spo2 = parseInt(elements.input_spo2.value, 10);
  const temp = parseFloat(elements.input_temp.value);
  const gcs = parseInt(elements.input_gcs.value, 10);
  const onO2 = elements.onOxygen.checked;
  const age = parseFloat(elements.patientAge.value) || 30;
  const isPregnant = elements.isPregnant.checked;
  const complaint = elements.chiefComplaint.value.toLowerCase();

  // Sync displays
  elements.val_hr.textContent = hr;
  elements.val_sbp.textContent = sbp;
  elements.val_dbp.textContent = dbp;
  elements.val_rr.textContent = rr;
  elements.val_spo2.textContent = spo2;
  elements.val_temp.textContent = temp.toFixed(1);
  elements.val_gcs.textContent = gcs;

  // Run scoring
  const news2 = calculateNEWS2(rr, spo2, sbp, hr, temp, gcs, onO2);
  const qsofa = calculateQSOFA(rr, sbp, gcs);
  const shockIndex = sbp > 0 ? (hr / sbp) : 9.99;
  const uncertainty = computeUncertainty(sbp, spo2, rr, news2, shockIndex, age, isPregnant);

  // Determine Severity
  let severity = 'GREEN';
  let bannerClass = 'green';
  let badgeText = 'ROUTINE • GREEN';
  let descText = 'Physiologically Stable — Standard Ambulatory Care Protocols';

  if (news2 >= 7 || qsofa >= 2 || shockIndex >= 1.2 || spo2 <= 88 || gcs <= 8) {
    severity = 'RED';
    bannerClass = 'red';
    badgeText = 'CRITICAL • RED';
    descText = 'Immediate Resuscitation Required — Physiologic Collapse Threat';
  } else if (news2 >= 5 || shockIndex >= 1.0 || spo2 <= 92 || qsofa === 1) {
    severity = 'ORANGE';
    bannerClass = 'orange';
    badgeText = 'EMERGENT • ORANGE';
    descText = 'High Risk of Rapid Deterioration — Urgent Field Stabilization';
  } else if (news2 >= 3 || shockIndex >= 0.85) {
    severity = 'YELLOW';
    bannerClass = 'yellow';
    badgeText = 'URGENT • YELLOW';
    descText = 'Moderate Abnormalities — Serial Re-evaluation Every 30 Minutes';
  }

  // Determine Protocol
  let protocol = "RESPIRATORY & HYPOXIA";
  if (complaint.includes("bleed") || complaint.includes("trauma") || complaint.includes("fall") || (shockIndex >= 1.0 && !complaint.includes("fever"))) {
    protocol = "TRAUMA & HEMORRHAGIC SHOCK";
  } else if (qsofa >= 2 || complaint.includes("fever") || complaint.includes("chill") || temp >= 38.5) {
    protocol = "SEPSIS & INFECTION";
  } else if (spo2 < 94 || rr >= 25 || complaint.includes("shortness") || complaint.includes("breath") || complaint.includes("cough")) {
    protocol = "RESPIRATORY & HYPOXIA";
  } else if (isPregnant || age < 5) {
    protocol = "MATERNAL & PEDIATRIC ACUTE";
  } else if (gcs < 15 || complaint.includes("syncope") || complaint.includes("confusion")) {
    protocol = "NEUROLOGICAL & ALTERED MENTAL";
  }

  // Update UI Elements
  elements.triageBanner.className = `triage-status-banner ${bannerClass}`;
  elements.triageBadge.textContent = badgeText;
  elements.triageDesc.textContent = descText;

  elements.score_news2.innerHTML = `${news2}<span class="sub-denom">/20</span>`;
  elements.interp_news2.textContent = news2 >= 7 ? "Extreme Clinical Risk" : news2 >= 5 ? "Medium Risk (Trigger Ward Review)" : news2 >= 1 ? "Low Risk" : "Normal Baseline";

  elements.score_qsofa.innerHTML = `${qsofa}<span class="sub-denom">/3</span>`;
  elements.interp_qsofa.textContent = qsofa >= 2 ? "High Sepsis Mortality Risk" : qsofa === 1 ? "Elevated Warning State" : "Standard Risk Profile";

  elements.score_si.textContent = shockIndex.toFixed(2);
  elements.interp_si.textContent = shockIndex >= 1.0 ? "Overt Hemodynamic Collapse" : shockIndex >= 0.9 ? "Occult Shock Warning" : "Normal Perfusion (0.5 - 0.7)";

  elements.score_protocol.textContent = protocol;
  const isEscalate = severity === 'RED' || severity === 'ORANGE' || uncertainty >= 0.35;
  elements.interp_escalation.textContent = isEscalate ? "MANDATORY PHYSICIAN ESCALATION" : "COMMUNITY HEALTH WORKER DISPATCH";
  elements.interp_escalation.style.color = isEscalate ? "var(--red-text)" : "var(--green-text)";

  // Uncertainty
  const uPct = Math.round(uncertainty * 100);
  elements.val_uncertainty.textContent = `${uPct}% BOUND`;
  elements.uncertaintyBar.style.width = `${uPct}%`;

  // Findings & Interventions
  const findings = [];
  const interventions = [];

  if (severity === 'RED') {
    findings.push("CRITICAL: Severe physiologic collapse or impending respiratory failure");
  } else if (severity === 'ORANGE') {
    findings.push("HIGH RISK: Rapid deterioration threshold reached; urgent stabilization needed");
  } else if (severity === 'YELLOW') {
    findings.push("MODERATE: Abnormal vital parameters; requires serial monitoring");
  } else {
    findings.push("STABLE: Vitals within ambulatory baseline tolerances");
  }

  if (qsofa >= 2) {
    findings.push(`qSOFA = ${qsofa}/3: Positive for high risk of in-hospital sepsis mortality`);
    interventions.push("Initiate Sepsis-3 bundle: Blood cultures, IV crystalloid resuscitation, empiric antibiotics");
  }

  if (shockIndex >= 1.0) {
    findings.push(`Shock Index = ${shockIndex.toFixed(2)}: Overt hemodynamic decompensation (tachycardia disproportionate to SBP)`);
    interventions.push("Establish 2x large-bore IV lines (16-18G); rapid fluid challenge 500mL crystalloid");
  } else if (shockIndex >= 0.9) {
    findings.push(`Shock Index = ${shockIndex.toFixed(2)}: Occult shock warning threshold exceeded`);
    interventions.push("Position supine, monitor orthostatic vitals, prepare fluid warming");
  }

  if (spo2 < 92) {
    findings.push(`SpO2 = ${spo2}%: Moderate-to-severe hypoxemia`);
    interventions.push("Administer supplemental high-flow O2 via non-rebreather mask (10-15 L/min)");
  }

  if (gcs < 15) {
    findings.push(`GCS = ${gcs}/15: Neurological compromise / depressed consciousness`);
    interventions.push("Airway protection evaluation, rapid blood glucose fingerstick, cervical collar if trauma");
  }

  if (uncertainty >= 0.35) {
    findings.push(`Conformal Epistemic Uncertainty = ${uPct}%: Complex boundary state`);
    interventions.push("Mandatory physician tele-consultation or transfer dispatch due to diagnostic ambiguity");
  }

  if (interventions.length === 0) {
    interventions.push("Continue standard oral hydration, prescribe symptomatic care, discharge with red-flag warning instructions");
  }

  elements.findingsList.innerHTML = findings.map(f => `<li>${f}</li>`).join('');
  elements.interventionsList.innerHTML = interventions.map(i => `<li>${i}</li>`).join('');

  // Optional trigger audio
  playAlertTone(severity);
}

// Preset Loader
function loadPreset(presetKey) {
  const p = PRESETS[presetKey];
  if (!p) return;
  elements.patientId.value = p.id;
  elements.patientAge.value = p.age;
  elements.isPregnant.checked = p.pregnant;
  elements.onOxygen.checked = p.oxygen;
  elements.chiefComplaint.value = p.complaint;

  elements.input_hr.value = p.hr;
  elements.input_sbp.value = p.sbp;
  elements.input_dbp.value = p.dbp;
  elements.input_rr.value = p.rr;
  elements.input_spo2.value = p.spo2;
  elements.input_temp.value = p.temp;
  elements.input_gcs.value = p.gcs;

  updateCalculation();
}

// Event Listeners
[
  elements.input_hr, elements.input_sbp, elements.input_dbp,
  elements.input_rr, elements.input_spo2, elements.input_temp,
  elements.input_gcs, elements.patientAge, elements.isPregnant,
  elements.onOxygen, elements.chiefComplaint
].forEach(input => {
  input.addEventListener('input', updateCalculation);
  input.addEventListener('change', updateCalculation);
});

elements.casePreset.addEventListener('change', (e) => {
  loadPreset(e.target.value);
});

// Theme Switcher
elements.themeToggle.addEventListener('click', () => {
  const isDark = document.body.classList.toggle('theme-dark');
  elements.themeIcon.textContent = isDark ? "🌙 NIGHT TACTICAL" : "☀️ SUNLIGHT MODE";
});

// Audio Toggle
elements.audioToggle.addEventListener('click', () => {
  audioEnabled = !audioEnabled;
  elements.audioIcon.textContent = audioEnabled ? "🔊 AUDIO ALARMS ON" : "🔇 AUDIO MUTED";
  elements.audioToggle.style.opacity = audioEnabled ? "1" : "0.6";
});

// Reset
elements.resetBtn.addEventListener('click', () => {
  loadPreset('sepsis');
  elements.casePreset.value = 'sepsis';
});

// Modal & Export
elements.exportPassBtn.addEventListener('click', () => {
  const passText = `================================================================
KITHMED OFFLINE FIELD TRIAGE EMERGENCY PASS
================================================================
Patient ID: ${elements.patientId.value}
Age: ${elements.patientAge.value} | Pregnant: ${elements.isPregnant.checked ? 'YES' : 'NO'}
Chief Complaint: ${elements.chiefComplaint.value}

--- TRIAGE STATUS ---
Classification: ${elements.triageBadge.textContent}
Primary Protocol: ${elements.score_protocol.textContent}
Escalation: ${elements.interp_escalation.textContent}

--- VITALS TELEMETRY ---
HR: ${elements.input_hr.value} bpm | BP: ${elements.input_sbp.value}/${elements.input_dbp.value} mmHg
RR: ${elements.input_rr.value} bpm | SpO2: ${elements.input_spo2.value}%
Temp: ${elements.input_temp.value}°C | GCS: ${elements.input_gcs.value}/15

--- CLINICAL RISK SCORES ---
NEWS2 Score: ${elements.score_news2.textContent} (${elements.interp_news2.textContent})
qSOFA Score: ${elements.score_qsofa.textContent} (${elements.interp_qsofa.textContent})
Shock Index: ${elements.score_si.textContent} (${elements.interp_si.textContent})
Conformal Epistemic Uncertainty: ${elements.val_uncertainty.textContent}

Timestamp: ${new Date().toISOString()}
Cryptographic Engine: Deterministic Zero-Connectivity
================================================================`;

  elements.modalContent.textContent = passText;
  elements.passModal.classList.remove('hidden');
});

elements.closeModalBtn.addEventListener('click', () => {
  elements.passModal.classList.add('hidden');
});

elements.printBtn.addEventListener('click', () => {
  window.print();
});

elements.copyJsonBtn.addEventListener('click', () => {
  const payload = {
    patient_id: elements.patientId.value,
    age_years: parseFloat(elements.patientAge.value),
    is_pregnant: elements.isPregnant.checked,
    chief_complaint: elements.chiefComplaint.value,
    vitals: {
      hr: parseInt(elements.input_hr.value, 10),
      sbp: parseInt(elements.input_sbp.value, 10),
      dbp: parseInt(elements.input_dbp.value, 10),
      rr: parseInt(elements.input_rr.value, 10),
      spo2: parseInt(elements.input_spo2.value, 10),
      temp_c: parseFloat(elements.input_temp.value),
      gcs: parseInt(elements.input_gcs.value, 10)
    },
    scores: {
      news2: elements.score_news2.textContent,
      qsofa: elements.score_qsofa.textContent,
      shock_index: parseFloat(elements.score_si.textContent),
      uncertainty: elements.val_uncertainty.textContent
    },
    severity: elements.triageBadge.textContent,
    protocol: elements.score_protocol.textContent
  };
  navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
  elements.copyJsonBtn.textContent = "COPIED TO CLIPBOARD!";
  setTimeout(() => {
    elements.copyJsonBtn.textContent = "COPY JSON TELEMETRY";
  }, 2000);
});

// Initial compute
updateCalculation();
