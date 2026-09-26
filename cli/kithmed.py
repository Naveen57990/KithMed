#!/usr/bin/env python3
"""
KithMed Tactical Field CLI
Zero-Connectivity Triage Assessment & Rapid Clinical Decision Support
"""

import sys
import os
import argparse
import json
import time

# Support relative and module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.triage_models import VitalSigns, PatientRecord, TriageSeverity, ProtocolCategory
from engine.scoring_engine import ClinicalScoringEngine

# ANSI Colors
RED = "\033[1;31m"
ORANGE = "\033[1;33m"
YELLOW = "\033[0;33m"
GREEN = "\033[1;32m"
CYAN = "\033[1;36m"
WHITE = "\033[1;37m"
GRAY = "\033[0;90m"
RESET = "\033[0m"
BOLD = "\033[1m"

def get_severity_badge(severity: TriageSeverity) -> str:
    if severity == TriageSeverity.RED:
        return f"{RED}[ CRITICAL - RED ]{RESET}"
    elif severity == TriageSeverity.ORANGE:
        return f"{ORANGE}[ EMERGENT - ORANGE ]{RESET}"
    elif severity == TriageSeverity.YELLOW:
        return f"{YELLOW}[ URGENT - YELLOW ]{RESET}"
    else:
        return f"{GREEN}[ ROUTINE - GREEN ]{RESET}"

def print_triage_card(patient: PatientRecord, result):
    badge = get_severity_badge(result.severity)
    print(f"\n{CYAN}{'='*64}{RESET}")
    print(f"{BOLD}KITHMED CLINICAL TRIAGE REPORT{RESET} | ID: {WHITE}{patient.patient_id}{RESET} | Status: {badge}")
    print(f"{CYAN}{'='*64}{RESET}")
    
    print(f"{BOLD}Demographics:{RESET} Age {patient.age_years:.0f} | Pregnant: {'YES' if patient.is_pregnant else 'NO'}")
    print(f"{BOLD}Chief Complaint:{RESET} {patient.chief_complaint}")
    print(f"{BOLD}Symptoms:{RESET} {', '.join(patient.reported_symptoms) if patient.reported_symptoms else 'None reported'}")
    
    v = patient.vitals
    print(f"\n{GRAY}--- VITAL TELEMETRY ---{RESET}")
    print(f"HR: {v.heart_rate_bpm} bpm | SBP/DBP: {v.systolic_bp_mmhg}/{v.diastolic_bp_mmhg} mmHg | RR: {v.respiratory_rate_bpm} bpm")
    print(f"SpO2: {v.spo2_percent}% | Temp: {v.temperature_celsius:.1f}°C | GCS: {v.glasgow_coma_scale}/15")
    
    print(f"\n{GRAY}--- CLINICAL RISK STRATIFICATION ---{RESET}")
    print(f"Protocol: {WHITE}{result.primary_protocol.value}{RESET}")
    print(f"NEWS2 Score: {BOLD}{result.news2_score}/20{RESET} | qSOFA Score: {BOLD}{result.qsofa_score}/3{RESET} | Shock Index: {BOLD}{result.shock_index:.2f}{RESET}")
    print(f"Conformal Epistemic Uncertainty: {BOLD}{result.uncertainty_score*100:.0f}%{RESET} | Physician Escalation: {'MANDATORY' if result.physician_escalation_required else 'STANDARD'}")

    print(f"\n{GRAY}--- KEY CLINICAL FINDINGS ---{RESET}")
    for item in result.key_findings:
        print(f"  • {item}")

    print(f"\n{GRAY}--- RECOMMENDED INTERVENTIONS ---{RESET}")
    for item in result.actionable_interventions:
        print(f"  ➜ {WHITE}{item}{RESET}")
    print(f"{CYAN}{'='*64}{RESET}\n")

def demo_batch():
    sample_patients = [
        PatientRecord(
            patient_id="KM-ALPHA",
            age_years=54,
            is_pregnant=False,
            chief_complaint="Severe chills, high fever, altered mentation",
            vitals=VitalSigns(124, 88, 54, 26, 91, 39.5, 13),
            reported_symptoms=["fever", "chills", "lethargy"]
        ),
        PatientRecord(
            patient_id="KM-BRAVO",
            age_years=29,
            is_pregnant=False,
            chief_complaint="Motorcycle fall, abdominal pain",
            vitals=VitalSigns(114, 98, 62, 22, 97, 36.6, 15),
            reported_symptoms=["bleeding", "dizziness"]
        ),
        PatientRecord(
            patient_id="KM-CHARLIE",
            age_years=3,
            is_pregnant=False,
            chief_complaint="Pediatric cough with poor oral intake",
            vitals=VitalSigns(92, 92, 60, 21, 94, 38.0, 15),
            reported_symptoms=["cough", "lethargy"]
        ),
        PatientRecord(
            patient_id="KM-DELTA",
            age_years=34,
            is_pregnant=False,
            chief_complaint="Mild ankle sprain",
            vitals=VitalSigns(70, 118, 76, 15, 99, 36.7, 15),
            reported_symptoms=["ankle swelling"]
        )
    ]

    print(f"{BOLD}{CYAN}Running KithMed Zero-Connectivity Batch Field Triage Benchmark (4 Cases)...{RESET}")
    for p in sample_patients:
        res = ClinicalScoringEngine.evaluate_patient(p)
        print_triage_card(p, res)

def main():
    parser = argparse.ArgumentParser(description="KithMed Field Triage & Clinical Decision CLI")
    parser.add_argument("--demo", action="store_true", help="Run multi-case field triage demo benchmark")
    parser.add_argument("--hr", type=int, default=75, help="Heart rate (bpm)")
    parser.add_argument("--sbp", type=int, default=120, help="Systolic blood pressure (mmHg)")
    parser.add_argument("--dbp", type=int, default=80, help="Diastolic blood pressure (mmHg)")
    parser.add_argument("--rr", type=int, default=16, help="Respiratory rate (bpm)")
    parser.add_argument("--spo2", type=int, default=98, help="Oxygen saturation percentage (0-100)")
    parser.add_argument("--temp", type=float, default=37.0, help="Temperature in Celsius")
    parser.add_argument("--gcs", type=int, default=15, help="Glasgow Coma Scale (3-15)")
    parser.add_argument("--age", type=float, default=30.0, help="Patient age in years")
    parser.add_argument("--pregnant", action="store_true", help="Patient is pregnant")
    parser.add_argument("--complaint", type=str, default="Routine triage evaluation", help="Chief complaint")
    parser.add_argument("--symptoms", type=str, default="", help="Comma separated symptoms")

    args = parser.parse_args()

    if args.demo:
        demo_batch()
        return

    symptoms = [s.strip() for s in args.symptoms.split(",") if s.strip()]
    vitals = VitalSigns(
        heart_rate_bpm=args.hr,
        systolic_bp_mmhg=args.sbp,
        diastolic_bp_mmhg=args.dbp,
        respiratory_rate_bpm=args.rr,
        spo2_percent=args.spo2,
        temperature_celsius=args.temp,
        glasgow_coma_scale=args.gcs
    )
    patient = PatientRecord(
        patient_id="KM-FIELD-1",
        age_years=args.age,
        is_pregnant=args.pregnant,
        chief_complaint=args.complaint,
        vitals=vitals,
        reported_symptoms=symptoms
    )
    result = ClinicalScoringEngine.evaluate_patient(patient)
    print_triage_card(patient, result)

if __name__ == "__main__":
    main()
