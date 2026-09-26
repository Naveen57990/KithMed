#!/usr/bin/env python3
"""
Assemble raw recording and narration audio into final 1080p MP4 demo video.
"""

import os
import subprocess

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    raw_video = os.path.join(DEMO_DIR, "raw_recording.webm")
    audio = os.path.join(DEMO_DIR, "kithmed_full_narration.mp3")
    output_mp4 = os.path.join(DEMO_DIR, "kithmed_demo.mp4")

    if not os.path.exists(raw_video):
        print(f"Error: {raw_video} not found.")
        return
    if not os.path.exists(audio):
        print(f"Error: {audio} not found.")
        return

    cmd = [
        "ffmpeg", "-y",
        "-i", raw_video,
        "-i", audio,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_mp4
    ]
    print(f"Executing: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"SUCCESS: Final demo video generated at {output_mp4}")

if __name__ == "__main__":
    main()
