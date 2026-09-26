"""
KithMed Comprehensive Deterministic Test Suite
Validates clinical calculations: NEWS2, qSOFA, Shock Index, Conformal Uncertainty, and Triage Tiers.
"""

import unittest
from .triage_models import VitalSigns, PatientRecord, TriageSeverity, ProtocolCategory
from .scoring_engine import ClinicalScoringEngine

class TestKithMedEngine(unittest.TestCase):

    def test_healthy_baseline_patient(self):
        vitals = VitalSigns(
            heart_rate_bpm=72,
            systolic_bp_mmhg=120,
            diastolic_bp_mmhg=80,
            respiratory_rate_bpm=16,
            spo2_percent=98,
            temperature_celsius=36.8,
            glasgow_coma_scale=15
        )
        patient = PatientRecord(
            patient_id="KM-001",
            age_years=32,
            is_pregnant=False,
            chief_complaint="Mild sprained ankle",
            vitals=vitals,
            reported_symptoms=["local swelling", "pain on weight bearing"]
        )
        result = ClinicalScoringEngine.evaluate_patient(patient)
        self.assertEqual(result.news2_score, 0)
        self.assertEqual(result.qsofa_score, 0)
        self.assertAlmostEqual(result.shock_index, 0.60, places=2)
        self.assertEqual(result.severity, TriageSeverity.GREEN)
        self.assertFalse(result.physician_escalation_required)

    def test_septic_shock_patient(self):
        vitals = VitalSigns(
            heart_rate_bpm=128,
            systolic_bp_mmhg=86,
            diastolic_bp_mmhg=52,
            respiratory_rate_bpm=26,
            spo2_percent=91,
            temperature_celsius=39.4,
            glasgow_coma_scale=13
        )
        patient = PatientRecord(
            patient_id="KM-002",
            age_years=58,
            is_pregnant=False,
            chief_complaint="High fever and severe confusion",
            vitals=vitals,
            reported_symptoms=["fever", "chills", "lethargy", "dysuria"]
        )
        result = ClinicalScoringEngine.evaluate_patient(patient)
        self.assertGreaterEqual(result.news2_score, 10)
        self.assertEqual(result.qsofa_score, 3) # SBP <= 100, RR >= 22, GCS < 15
        self.assertGreaterEqual(result.shock_index, 1.4)
        self.assertEqual(result.severity, TriageSeverity.RED)
        self.assertEqual(result.primary_protocol, ProtocolCategory.SEPSIS_INFECTION)
        self.assertTrue(result.physician_escalation_required)
        self.assertTrue(any("Sepsis-3" in act for act in result.actionable_interventions))

    def test_acute_respiratory_hypoxia(self):
        vitals = VitalSigns(
            heart_rate_bpm=102,
            systolic_bp_mmhg=135,
            diastolic_bp_mmhg=85,
            respiratory_rate_bpm=28,
            spo2_percent=86,
            temperature_celsius=37.1,
            glasgow_coma_scale=15
        )
        patient = PatientRecord(
            patient_id="KM-003",
            age_years=45,
            is_pregnant=False,
            chief_complaint="Acute severe shortness of breath",
            vitals=vitals,
            reported_symptoms=["dyspnea", "wheezing", "chest tightness"]
        )
        result = ClinicalScoringEngine.evaluate_patient(patient)
        self.assertGreaterEqual(result.news2_score, 6)
        self.assertEqual(result.severity, TriageSeverity.RED)
        self.assertEqual(result.primary_protocol, ProtocolCategory.RESPIRATORY)
        self.assertTrue(any("non-rebreather" in act for act in result.actionable_interventions))

    def test_hemorrhagic_occult_shock(self):
        vitals = VitalSigns(
            heart_rate_bpm=118,
            systolic_bp_mmhg=96,
            diastolic_bp_mmhg=64,
            respiratory_rate_bpm=22,
            spo2_percent=97,
            temperature_celsius=36.4,
            glasgow_coma_scale=15
        )
        patient = PatientRecord(
            patient_id="KM-004",
            age_years=28,
            is_pregnant=False,
            chief_complaint="Post-motorcycle fall with flank pain",
            vitals=vitals,
            reported_symptoms=["bleeding", "dizziness", "abdominal tenderness"]
        )
        result = ClinicalScoringEngine.evaluate_patient(patient)
        self.assertGreaterEqual(result.shock_index, 1.2)
        self.assertEqual(result.primary_protocol, ProtocolCategory.TRAUMA_HEMORRHAGE)
        self.assertTrue(result.physician_escalation_required)

    def test_conformal_uncertainty_elevation_on_boundary_states(self):
        # Patient sitting right on multiple critical threshold boundaries (e.g. SBP=91, SpO2=94, RR=21)
        vitals = VitalSigns(
            heart_rate_bpm=88,
            systolic_bp_mmhg=91,
            diastolic_bp_mmhg=60,
            respiratory_rate_bpm=21,
            spo2_percent=94,
            temperature_celsius=37.8,
            glasgow_coma_scale=15
        )
        patient = PatientRecord(
            patient_id="KM-005",
            age_years=2, # Pediatric vulnerable adjustment
            is_pregnant=False,
            chief_complaint="Fretful, reduced oral intake",
            vitals=vitals,
            reported_symptoms=["lethargy"]
        )
        result = ClinicalScoringEngine.evaluate_patient(patient)
        self.assertGreaterEqual(result.uncertainty_score, 0.35)
        self.assertTrue(result.physician_escalation_required)
        self.assertTrue(any("Conformal Epistemic Uncertainty" in finding for finding in result.key_findings))

    def test_pediatric_maternal_routing(self):
        vitals = VitalSigns(
            heart_rate_bpm=90,
            systolic_bp_mmhg=110,
            diastolic_bp_mmhg=70,
            respiratory_rate_bpm=18,
            spo2_percent=99,
            temperature_celsius=37.0,
            glasgow_coma_scale=15
        )
        patient = PatientRecord(
            patient_id="KM-006",
            age_years=24,
            is_pregnant=True,
            chief_complaint="Routine prenatal check, mild lower back ache",
            vitals=vitals,
            reported_symptoms=[]
        )
        result = ClinicalScoringEngine.evaluate_patient(patient)
        self.assertEqual(result.primary_protocol, ProtocolCategory.MATERNAL_PEDIATRIC)

    def test_oxygen_supplementation_impact(self):
        vitals = VitalSigns(
            heart_rate_bpm=80,
            systolic_bp_mmhg=120,
            diastolic_bp_mmhg=80,
            respiratory_rate_bpm=16,
            spo2_percent=96,
            temperature_celsius=37.0,
            glasgow_coma_scale=15
        )
        patient = PatientRecord(
            patient_id="KM-007",
            age_years=50,
            is_pregnant=False,
            chief_complaint="COPD exacerbation follow-up",
            vitals=vitals,
            reported_symptoms=[]
        )
        # On room air: score 0
        score_air = ClinicalScoringEngine.calculate_news2(vitals, on_oxygen=False)
        self.assertEqual(score_air, 0)
        # On supplemental O2: score 2
        score_o2 = ClinicalScoringEngine.calculate_news2(vitals, on_oxygen=True)
        self.assertEqual(score_o2, 2)

    def test_neurological_coma_triage(self):
        vitals = VitalSigns(
            heart_rate_bpm=58,
            systolic_bp_mmhg=165,
            diastolic_bp_mmhg=95,
            respiratory_rate_bpm=10,
            spo2_percent=95,
            temperature_celsius=36.6,
            glasgow_coma_scale=6 # Severe coma
        )
        patient = PatientRecord(
            patient_id="KM-008",
            age_years=62,
            is_pregnant=False,
            chief_complaint="Unresponsive following sudden collapse",
            vitals=vitals,
            reported_symptoms=["syncope", "unresponsive"]
        )
        result = ClinicalScoringEngine.evaluate_patient(patient)
        self.assertEqual(result.severity, TriageSeverity.RED)
        self.assertEqual(result.primary_protocol, ProtocolCategory.NEUROLOGICAL)
        self.assertTrue(result.physician_escalation_required)


if __name__ == "__main__":
    unittest.main()
