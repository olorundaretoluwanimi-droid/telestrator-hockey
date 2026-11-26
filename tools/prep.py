#!/usr/bin/env python3
"""Clips → graded 1920×1080 JPEG frames assets/<id>/0001.jpg … (60 fps). Frame n of clip <id> shows source second a + (n−1)/60.
  python3 tools/prep.py [<film a> <film b>]   — only the clips the film range [a, b) uses (each render job preps its own part)
Grade (STYLE.md §7): hqdn3d → lanczos 1.5× to 1920 → unsharp → eq (slightly flatter colour, a touch of contrast)."""
import json, os, subprocess, sys
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TL = json.load(open(f'{D}/timeline.json'))
VF = 'hqdn3d=1.2:1.2:2.5:2.5,scale=1920:1080:flags=lanczos,unsharp=5:5:0.55,eq=saturation=0.9:contrast=1.04:gamma=0.97'
if len(sys.argv) > 2 and sys.argv[1] == '--times':   # local check: only the frames (and next neighbour) at these source seconds
    for src in [float(x) for x in sys.argv[2].split(',')]:
        for cid, (a, b) in TL['clips'].items():
            if a - .02 <= src <= b + .02:
                for n in {max(1, round((src - a) * 60) + 1), round((src - a) * 60) + 2}:
                    od = f'{D}/assets/{cid}'; os.makedirs(od, exist_ok=True); out = f'{od}/{n:04d}.jpg'
                    if not os.path.exists(out): subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{(n - 1) / 60:.4f}', '-i', f'{D}/raw/clips/{cid}.mp4', '-frames:v', '1', '-vf', VF, '-q:v', '3', out], check=True)
                break
    sys.exit(0)
A, B = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) > 2 else (0, 1e9)
need = set()
for s in TL['seg']:
    if s['t1'] <= A - 1 or s['t0'] >= B + 1 or s['s0'] is None: continue
    for src in [s['s0'], s['s1'], s.get('r0'), s.get('r1')]:
        if src is None: continue
        for cid, (a, b) in TL['clips'].items():
            if a - .02 <= src <= b + .02: need.add(cid)
    if s['kind'] in ('board',) and s['id'] == 'record': need.add('c1')
for cid in sorted(need, key=lambda c: int(c[1:])):
    od = f'{D}/assets/{cid}'
    if os.path.isdir(od) and len(os.listdir(od)) > 10: print(cid, 'exists'); continue
    os.makedirs(od, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{D}/raw/clips/{cid}.mp4', '-vf', VF, '-q:v', '3', f'{od}/%04d.jpg'], check=True)
    print(cid, len(os.listdir(od)), 'frames')
