#!/usr/bin/env python3
"""
Measure scene durations and concatenate into a single audio file with exact scene timestamp metadata.
"""

import os
import json
import subprocess

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))

SCENES = [
    {"id": "scene1_intro", "text": "In humanitarian crisis zones and remote rural clinics, front-line health workers must make critical triage decisions in seconds without internet connectivity. Meet KithMed: a zero-connectivity clinical decision engine that brings uncertainty-bounded machine intelligence directly to the edge."},
    {"id": "scene2_sepsis", "text": "KithMed combines validated clinical risk models including NHS NEWS2, Sepsis-3 quick SOFA, and the Shock Index. Here, evaluating a septic shock patient with high fever and tachypnea, KithMed instantly flags a critical RED status, triggers sepsis bundles, and alerts the operator."},
    {"id": "scene3_trauma", "text": "When switching to acute trauma, KithMed continuously evaluates occult hypoperfusion. Even before systolic blood pressure collapses, a Shock Index above 1.1 alerts the field medic to impending hemorrhagic decompensation and recommends rapid large-bore IV access."},
    {"id": "scene4_uncertainty", "text": "Crucially, KithMed introduces conformal uncertainty bounding. When vital telemetry lies right on fragile decision boundaries or in vulnerable pediatric patients, KithMed refuses to guess and mandates immediate physician tele-consultation."},
    {"id": "scene5_pass_closing", "text": "Frontline workers can generate cryptographic offline triage passes for patient transfer and run bulk field assessments via the tactical terminal CLI. KithMed is open source, private, and engineered to save lives everywhere."}
]

def get_duration(file_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    out = subprocess.check_output(cmd).decode().strip()
    return float(out)

def main():
    concat_list = os.path.join(DEMO_DIR, "concat_list.txt")
    with open(concat_list, "w") as f:
        for s in SCENES:
            mp3_name = f"{s['id']}.mp3"
            f.write(f"file '{mp3_name}'\n")

    output_audio = os.path.join(DEMO_DIR, "kithmed_full_narration.mp3")
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", output_audio
    ]
    subprocess.run(cmd, check=True)

    current_time = 0.0
    timeline = []
    for s in SCENES:
        dur = get_duration(os.path.join(DEMO_DIR, f"{s['id']}.mp3"))
        start = current_time
        end = current_time + dur
        current_time = end
        timeline.append({
            "id": s["id"],
            "text": s["text"],
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(dur, 2)
        })

    print("Total Audio Duration:", current_time)
    print("Timeline:", json.dumps(timeline, indent=2))

    with open(os.path.join(DEMO_DIR, "timeline.json"), "w") as f:
        json.dump({"total_duration": current_time, "scenes": timeline}, f, indent=2)

if __name__ == "__main__":
    main()
