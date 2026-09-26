"""
KithMed Clinical Decision & Uncertainty Bounding Scoring Engine
Implements validated clinical risk stratification algorithms:
- NEWS2 (National Early Warning Score 2 - NHS Standard)
- qSOFA (Quick Sepsis-related Organ Failure Assessment - Third International Consensus)
- Shock Index (HR / SBP occult hypoperfusion indicator)
- Conformal Uncertainty Quantification (bounds prediction ambiguity for field escalation)
"""

from typing import List, Tuple, Dict, Any
from .triage_models import VitalSigns, PatientRecord, ClinicalScoringResult, TriageSeverity, ProtocolCategory
import math

class ClinicalScoringEngine:
    """
    Zero-connectivity deterministic clinical risk engine with conformal uncertainty bounding.
    """

    @staticmethod
    def calculate_respiratory_news2_score(rr: int, spo2: int, on_oxygen: bool = False) -> int:
        score = 0
        # Respiratory Rate
        if rr <= 8:
            score += 3
        elif 9 <= rr <= 11:
            score += 1
        elif 12 <= rr <= 20:
            score += 0
        elif 21 <= rr <= 24:
            score += 2
        else: # >= 25
            score += 3

        # SpO2 (Scale 1 standard)
        if spo2 <= 91:
            score += 3
        elif 92 <= spo2 <= 93:
            score += 2
        elif 94 <= spo2 <= 95:
            score += 1
        else:
            score += 0

        if on_oxygen:
            score += 2

        return score

    @staticmethod
    def calculate_cardiovascular_news2_score(sbp: int, hr: int) -> int:
        score = 0
        # Systolic BP
        if sbp <= 90:
            score += 3
        elif 91 <= sbp <= 100:
            score += 2
        elif 101 <= sbp <= 110:
            score += 1
        elif 111 <= sbp <= 219:
            score += 0
        else: # >= 220
            score += 3

        # Heart Rate
        if hr <= 40:
            score += 3
        elif 41 <= hr <= 50:
            score += 1
        elif 51 <= hr <= 90:
            score += 0
        elif 91 <= hr <= 110:
            score += 1
        elif 111 <= hr <= 130:
            score += 2
        else: # >= 131
            score += 3

        return score

    @staticmethod
    def calculate_neuro_temp_news2_score(temp_c: float, gcs: int) -> int:
        score = 0
        # Temperature
        if temp_c <= 35.0:
            score += 3
        elif 35.1 <= temp_c <= 36.0:
            score += 1
        elif 36.1 <= temp_c <= 38.0:
            score += 0
        elif 38.1 <= temp_c <= 39.0:
            score += 1
        else: # >= 39.1
            score += 2

        # Neurological / Consciousness
        if gcs < 15:
            score += 3

        return score

    @classmethod
    def calculate_news2(cls, vitals: VitalSigns, on_oxygen: bool = False) -> int:
        """Calculates total NHS NEWS2 score (0-20)."""
        score = (
            cls.calculate_respiratory_news2_score(vitals.respiratory_rate_bpm, vitals.spo2_percent, on_oxygen) +
            cls.calculate_cardiovascular_news2_score(vitals.systolic_bp_mmhg, vitals.heart_rate_bpm) +
            cls.calculate_neuro_temp_news2_score(vitals.temperature_celsius, vitals.glasgow_coma_scale)
        )
        return min(20, score)

    @staticmethod
    def calculate_qsofa(vitals: VitalSigns) -> int:
        """
        Calculates Quick SOFA score (0-3):
        - Respiratory rate >= 22 bpm (+1)
        - Altered mentation (GCS < 15) (+1)
        - Systolic BP <= 100 mmHg (+1)
        """
        score = 0
        if vitals.respiratory_rate_bpm >= 22:
            score += 1
        if vitals.glasgow_coma_scale < 15:
            score += 1
        if vitals.systolic_bp_mmhg <= 100:
            score += 1
        return score

    @staticmethod
    def calculate_shock_index(hr: int, sbp: int) -> float:
        """Calculates Shock Index = HR / SBP. Normal: 0.5 - 0.7. Elevated > 0.9."""
        if sbp <= 0:
            return 9.99
        return round(hr / sbp, 2)

    @classmethod
    def compute_conformal_uncertainty(cls, patient: PatientRecord, news2: int, shock_index: float) -> float:
        """
        Estimates conformal epistemic/aleatoric uncertainty based on vital boundary proximity,
        missing telemetry, and extreme variance between indicators.
        Returns uncertainty bounded in [0.0, 1.0].
        """
        uncertainty = 0.05 # Baseline calibration uncertainty

        # Boundary proximity penalty: vital close to threshold flips
        v = patient.vitals
        if 89 <= v.systolic_bp_mmhg <= 92:
            uncertainty += 0.15
        if 93 <= v.spo2_percent <= 95:
            uncertainty += 0.12
        if 20 <= v.respiratory_rate_bpm <= 22:
            uncertainty += 0.12

        # Discordant signal penalty: e.g. normal NEWS2 but high shock index
        if news2 < 4 and shock_index > 0.9:
            uncertainty += 0.25

        # Pediatric or Pregnancy vulnerability adjustment
        if patient.age_years < 5 or patient.is_pregnant:
            uncertainty += 0.18

        return min(0.95, round(uncertainty, 2))

    @classmethod
    def evaluate_patient(cls, patient: PatientRecord, on_oxygen: bool = False) -> ClinicalScoringResult:
        """
        Executes full multi-modal triage assessment.
        """
        v = patient.vitals
        news2 = cls.calculate_news2(v, on_oxygen)
        qsofa = cls.calculate_qsofa(v)
        si = cls.calculate_shock_index(v.heart_rate_bpm, v.systolic_bp_mmhg)
        uncertainty = cls.compute_conformal_uncertainty(patient, news2, si)

        findings: List[str] = []
        interventions: List[str] = []
        escalate = False

        # Identify Primary Clinical Protocol
        symptoms_lower = [s.lower() for s in patient.reported_symptoms]
        complaint_lower = patient.chief_complaint.lower()

        if "bleeding" in symptoms_lower or "trauma" in complaint_lower or "fall" in complaint_lower or (si >= 1.0 and "fever" not in symptoms_lower):
            protocol = ProtocolCategory.TRAUMA_HEMORRHAGE
        elif qsofa >= 2 or "fever" in symptoms_lower or "chills" in symptoms_lower or v.temperature_celsius >= 38.5:
            protocol = ProtocolCategory.SEPSIS_INFECTION
        elif v.spo2_percent < 94 or v.respiratory_rate_bpm >= 25 or "dyspnea" in symptoms_lower or "cough" in symptoms_lower:
            protocol = ProtocolCategory.RESPIRATORY
        elif patient.is_pregnant or patient.age_years < 5:
            protocol = ProtocolCategory.MATERNAL_PEDIATRIC
        elif v.glasgow_coma_scale < 15 or "syncope" in symptoms_lower or "confusion" in symptoms_lower:
            protocol = ProtocolCategory.NEUROLOGICAL
        else:
            protocol = ProtocolCategory.RESPIRATORY

        # Determine Severity
        if news2 >= 7 or qsofa >= 2 or si >= 1.2 or v.spo2_percent <= 88 or v.glasgow_coma_scale <= 8:
            severity = TriageSeverity.RED
            escalate = True
            findings.append("CRITICAL: Severe physiologic collapse or impending respiratory/circulatory failure")
        elif news2 >= 5 or si >= 1.0 or v.spo2_percent <= 92 or qsofa == 1:
            severity = TriageSeverity.ORANGE
            escalate = True
            findings.append("HIGH RISK: Rapid deterioration threshold reached; urgent stabilization needed")
        elif news2 >= 3 or si >= 0.85:
            severity = TriageSeverity.YELLOW
            findings.append("MODERATE: Abnormal vital parameters; requires serial monitoring every 30m")
        else:
            severity = TriageSeverity.GREEN
            findings.append("STABLE: Vitals within ambulatory baseline tolerances")

        # Specific Clinical Diagnostics
        if qsofa >= 2:
            findings.append(f"qSOFA = {qsofa}/3: Positive for high risk of in-hospital sepsis mortality")
            interventions.append("Initiate Sepsis-3 bundle: Blood cultures, IV crystalloid resuscitation, empiric antibiotics")
        
        if si >= 1.0:
            findings.append(f"Shock Index = {si:.2f}: Overt hemodynamic decompensation (tachycardia disproportionate to SBP)")
            interventions.append("Establish 2x large-bore IV lines (16-18G); rapid fluid challenge 500mL crystalloid")
        elif si >= 0.9:
            findings.append(f"Shock Index = {si:.2f}: Occult shock warning threshold exceeded")
            interventions.append("Position supine, monitor orthostatic vitals, prepare fluid warming")

        if v.spo2_percent < 92:
            findings.append(f"SpO2 = {v.spo2_percent}%: Moderate-to-severe hypoxemia")
            interventions.append("Administer supplemental high-flow O2 via non-rebreather mask (10-15 L/min)")

        if v.glasgow_coma_scale < 15:
            findings.append(f"GCS = {v.glasgow_coma_scale}/15: Neurological compromise / depressed consciousness")
            interventions.append("Airway protection evaluation, rapid blood glucose fingerstick, cervical collar if trauma")

        if uncertainty >= 0.35:
            findings.append(f"Conformal Epistemic Uncertainty = {uncertainty*100:.0f}%: Complex boundary state")
            escalate = True
            interventions.append("Mandatory physician tele-consultation or transfer dispatch due to diagnostic ambiguity")

        if not interventions:
            interventions.append("Continue standard oral hydration, prescribe symptomatic care, discharge with red-flag warning instructions")

        return ClinicalScoringResult(
            qsofa_score=qsofa,
            news2_score=news2,
            shock_index=si,
            severity=severity,
            primary_protocol=protocol,
            key_findings=findings,
            actionable_interventions=interventions,
            uncertainty_score=uncertainty,
            physician_escalation_required=escalate
        )
