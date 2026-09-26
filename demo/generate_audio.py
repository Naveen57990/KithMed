#!/usr/bin/env python3
"""
Generate high-fidelity voiceover narration for KithMed demo video.
Uses edge-tts with en-US-AndrewNeural voice.
"""

import asyncio
import os
import edge_tts

VOICE = "en-US-AndrewNeural"
RATE = "-2%"
PITCH = "+0Hz"

SCENES = [
    {
        "id": "scene1_intro",
        "text": "In humanitarian crisis zones and remote rural clinics, front-line health workers must make critical triage decisions in seconds without internet connectivity. Meet KithMed: a zero-connectivity clinical decision engine that brings uncertainty-bounded machine intelligence directly to the edge."
    },
    {
        "id": "scene2_sepsis",
        "text": "KithMed combines validated clinical risk models including NHS NEWS2, Sepsis-3 quick SOFA, and the Shock Index. Here, evaluating a septic shock patient with high fever and tachypnea, KithMed instantly flags a critical RED status, triggers sepsis bundles, and alerts the operator."
    },
    {
        "id": "scene3_trauma",
        "text": "When switching to acute trauma, KithMed continuously evaluates occult hypoperfusion. Even before systolic blood pressure collapses, a Shock Index above 1.1 alerts the field medic to impending hemorrhagic decompensation and recommends rapid large-bore IV access."
    },
    {
        "id": "scene4_uncertainty",
        "text": "Crucially, KithMed introduces conformal uncertainty bounding. When vital telemetry lies right on fragile decision boundaries or in vulnerable pediatric patients, KithMed refuses to guess and mandates immediate physician tele-consultation."
    },
    {
        "id": "scene5_pass_closing",
        "text": "Frontline workers can generate cryptographic offline triage passes for patient transfer and run bulk field assessments via the tactical terminal CLI. KithMed is open source, private, and engineered to save lives everywhere."
    }
]

async def generate_scene_audio():
    output_dir = os.path.dirname(__file__)
    for idx, scene in enumerate(SCENES):
        mp3_path = os.path.join(output_dir, f"{scene['id']}.mp3")
        print(f"Generating audio for Scene {idx+1}: {scene['id']}...")
        communicate = edge_tts.Communicate(scene['text'], VOICE, rate=RATE, pitch=PITCH)
        await communicate.save(mp3_path)
        print(f"Saved: {mp3_path}")

if __name__ == "__main__":
    asyncio.run(generate_scene_audio())
