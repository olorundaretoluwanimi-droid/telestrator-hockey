#!/usr/bin/env python3
"""raw/umb_psu_video.mp4 → raw/clips/<id>.mp4, exactly the source ranges in timeline.json "clips" (1280×720, 60 fps, CRF 14).
Small files that go into the repo; prep.py turns them into frames on the render machine."""
import json, os, subprocess
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TL = json.load(open(f'{D}/timeline.json')); os.makedirs(f'{D}/raw/clips', exist_ok=True)
for cid, (a, b) in TL['clips'].items():
    out = f'{D}/raw/clips/{cid}.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a:.3f}', '-i', f'{D}/raw/umb_psu_video.mp4', '-t', f'{b - a:.3f}', '-an',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-r', '60', '-pix_fmt', 'yuv420p', out], check=True)
    print(cid, a, b, os.path.getsize(out) // 1024, 'KB')
