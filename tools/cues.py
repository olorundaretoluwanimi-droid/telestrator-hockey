#!/usr/bin/env python3
"""Subtitle cues → audio/cues.json (same rule as cueSpan() in index.html: line start → end + 0.45 s, or 0.08 s before the next line)."""
import json, os
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tl = json.load(open(f'{D}/timeline.json', encoding='utf-8')); vd = json.load(open(f'{D}/audio/vo/dur.json')); vo = tl['vo']; out = []
for i, v in enumerate(vo):
    t1 = v['t'] + vd.get(v['id'], 2.5) + .45
    if i + 1 < len(vo): t1 = min(t1, vo[i + 1]['t'] - .08)
    out.append({'t0': v['t'], 't1': round(t1, 3), 'text': v['text']})
json.dump(out, open(f'{D}/audio/cues.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print(len(out), 'cues')
