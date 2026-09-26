"""
KithMed Core Domain Models
Zero-Connectivity Humanitarian Triage & Uncertainty-Bounded Clinical Decision Engine.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import time

class TriageSeverity(Enum):
    GREEN = "ROUTINE"       # Non-urgent, outpatient care
    YELLOW = "URGENT"       # Significant illness, stable vitals
    ORANGE = "EMERGENT"     # High risk of rapid deterioration
    RED = "CRITICAL"        # Immediate life threat / resuscitation

class ProtocolCategory(Enum):
    RESPIRATORY = "Respiratory & Hypoxia"
    SEPSIS_INFECTION = "Sepsis & Severe Infection"
    TRAUMA_HEMORRHAGE = "Trauma & Hemorrhagic Shock"
    MATERNAL_PEDIATRIC = "Maternal & Pediatric Acute"
    NEUROLOGICAL = "Neurological & Altered Mental State"

@dataclass
class VitalSigns:
    heart_rate_bpm: int             # Normal: 60-100
    systolic_bp_mmhg: int           # Normal: 90-120
    diastolic_bp_mmhg: int          # Normal: 60-80
    respiratory_rate_bpm: int       # Normal: 12-20
    spo2_percent: int               # Normal: 95-100%
    temperature_celsius: float      # Normal: 36.5 - 37.5
    glasgow_coma_scale: int = 15    # Normal: 15 (Range 3-15)
    capillary_refill_seconds: float = 1.5

@dataclass
class PatientRecord:
    patient_id: str
    age_years: float
    is_pregnant: bool
    chief_complaint: str
    vitals: VitalSigns
    reported_symptoms: List[str] = field(default_factory=list)
    recorded_at: float = field(default_factory=time.time)

@dataclass
class ClinicalScoringResult:
    qsofa_score: int                # Quick Sepsis-related Organ Failure (0-3)
    news2_score: int                # National Early Warning Score 2 (0-20)
    shock_index: float              # HR / SBP (Normal < 0.7, > 0.9 = occult shock)
    severity: TriageSeverity
    primary_protocol: ProtocolCategory
    key_findings: List[str]
    actionable_interventions: List[str]
    uncertainty_score: float        # 0.0 (high confidence) to 1.0 (ambiguous)
    physician_escalation_required: bool
