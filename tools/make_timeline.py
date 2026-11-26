#!/usr/bin/env python3
"""Builds timeline.json: segments (film time t0–t1, source seconds s0→s1 or a frozen source second), the clips prep.sh cuts,
goal flips (score strip), and the voice cues. Page, mix, cues and render all read timeline.json.
Source = UMass Boston Athletics highlights (1280×720, 60 fps). Times in source seconds of raw/umb_psu_video.mp4."""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
vdur = json.load(open(f'{D}/audio/vo/dur.json'))
lines = {l['id']: l for l in json.load(open(f'{D}/audio/lines.json', encoding='utf-8'))}

CLIPS = {  # id: (a, b) source seconds, extracted at 60 fps → assets/<id>/0001.jpg …
    'c1': (0.5, 13.6), 'c2': (43.9, 50.0), 'c3': (79.9, 83.5), 'c4': (124.5, 128.3), 'c5': (168.0, 172.8),
    'c6': (196.7, 201.7), 'c7': (222.9, 225.2), 'c8': (237.9, 243.7), 'c9': (275.8, 284.8), 'c10': (297.4, 300.6), 'c11': (304.5, 305.7)}

SEG = []; t = 0.0
def add(id, d, kind, s0=None, s1=None, **kw):
    global t
    SEG.append(dict(id=id, t0=round(t, 3), t1=round(t + d, 3), kind=kind, s0=s0, s1=s1 if s1 is not None else s0, **kw)); t += d
# kind: board | live | fz (freeze) | slow | rew | rep (replay play) | split | splitfz | map | end | card
add('sting', 2.0, 'board')
add('record', 8.0, 'board', 0.6)
add('g1live', 9.4, 'live', 0.6, 10.0, clock='g1')
add('g1fz', 2.4, 'fz', 10.0, clock='g1')
add('g1go', 3.4, 'live', 10.0, 13.4, clock='g1')
add('g2live', 3.4, 'live', 44.0, 47.4)
add('g2fz', 2.2, 'fz', 47.4)
add('g2go', 2.4, 'live', 47.4, 49.8)
add('g3', 3.4, 'live', 80.0, 83.4)
add('g4', 3.6, 'live', 124.6, 128.2)
add('turn', 10.0, 'board')
add('g9live', 2.2, 'live', 168.1, 170.3)
add('g9fz', 2.2, 'fz', 170.3)
add('g9go', 2.4, 'live', 170.3, 172.7)
add('g10live', 4.8, 'live', 196.8, 201.6)
add('g10rep', 2.0, 'rep', 223.0, 225.0)
add('g10rfz', 2.0, 'fz', 225.0, rep=True)
add('g12', 5.6, 'live', 238.0, 243.6, pp=True)
add('dlive', 8.8, 'live', 275.9, 284.7, pp=True, clock='g13')
add('drew', 0.6, 'rew', 284.7, 276.6, pp=True, clock='g13')
add('dfz1', 2.6, 'fz', 276.6, pp=True, clock='g13')
add('dslow1', 3.6, 'slow', 276.6, 279.6, pp=True, clock='g13')
add('dfz2', 2.8, 'fz', 279.6, pp=True, clock='g13', watch=True)
add('dslow2', 1.2, 'slow', 279.6, 279.9, pp=True, clock='g13', watch=True)
add('dfz3', 2.4, 'fz', 279.9, pp=True, clock='g13', watch=True)
add('dgo', 3.4, 'slow', 279.9, 281.9, pp=True, clock='g13', watch=True)
add('dsplit', 2.2, 'split', 279.3, 280.3, r0=304.6, r1=305.6, pp=True)
add('dsplitfz', 2.4, 'splitfz', 280.3, r0=305.6, pp=True)
add('map', 10.0, 'map', 280.7)
add('data', 8.0, 'board')
add('end', 4.4, 'end', 297.5, 300.5)
add('card', 6.0, 'card', 300.5, 300.6)
DUR = round(t, 3)
S = {s['id']: s for s in SEG}

def film_t(sid, src):
    """film time at which segment sid shows source second src (linear segments)"""
    s = S[sid]; return s['t0'] + (src - s['s0']) / (s['s1'] - s['s0']) * (s['t1'] - s['t0'])

# goal flips: (n UMB goals after, PSU goals, segment, source second the puck is in, official time label, team)
GOALS = [
    dict(umb=1, psu=0, t=film_t('g1go', 10.45), from_=S['g1live']['t0'], lab='0:10 1ST'),
    dict(umb=2, psu=0, t=film_t('g2go', 48.4), from_=S['g2live']['t0'], lab='8:07 1ST'),
    dict(umb=3, psu=1, t=film_t('g3', 81.7), from_=S['g3']['t0'], lab='13:22 1ST'),
    dict(umb=4, psu=1, t=film_t('g4', 126.9), from_=S['g4']['t0'], lab='16:33 1ST'),
    dict(umb=5, psu=4, t=film_t('g9go', 171.7), from_=S['g9live']['t0'], lab='7:51 2ND'),
    dict(umb=6, psu=4, t=film_t('g10live', 199.3), from_=S['g10live']['t0'], lab='13:32 2ND'),
    dict(umb=7, psu=5, t=film_t('g12', 242.7), from_=S['g12']['t0'], lab='18:24 2ND'),
    dict(umb=8, psu=5, t=film_t('dlive', 280.2), from_=S['dlive']['t0'], lab='19:52.3 2ND'),
]
# before each flip the PSU score is psu (goals 3–4 come after PSU's 8:51 goal; goal 9 after the 4–4 tie; goal 12 after the 17:35 SH goal)

VO = [  # (id, film time)
    ('v01', S['record']['t0'] + .6), ('v02', S['g1live']['t0'] + .6), ('v03', S['g1fz']['t0'] + .15), ('v04', GOALS[0]['t'] + 1.0),
    ('v05', S['g2fz']['t0'] + .1), ('v06', S['g3']['t0'] + .4), ('v07', S['turn']['t0'] + 1.0), ('v08', S['g9fz']['t0'] + .1),
    ('v09', GOALS[5]['t'] + .3), ('v11', S['dlive']['t0'] + .3), ('v12', S['dfz1']['t0'] + .1),
    ('v13', S['dfz2']['t0'] + .1), ('v15', S['dfz3']['t0'] + .3), ('v16', S['dsplit']['t0'] + .5), ('v17', S['map']['t0'] + 1.8),
    ('v18', S['data']['t0'] + .6), ('v19', S['end']['t0'] + 3.9)]
vo = [dict(id=i, t=round(tt, 3), text=lines[i]['sub']) for i, tt in VO]
for a, b in zip(vo, vo[1:]):
    if a['t'] + vdur[a['id']] > b['t'] - .1: print(f"!! {a['id']} ({a['t']:.2f}+{vdur[a['id']]:.2f}) overlaps {b['id']} at {b['t']:.2f}")
for g in GOALS: g['t'] = round(g['t'], 3); g['from'] = round(g.pop('from_'), 3)
json.dump(dict(dur=DUR, fps=30, src_fps=60, clips=CLIPS, seg=SEG, goals=GOALS, vo=vo), open(f'{D}/timeline.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('dur', DUR)
for s in SEG: print(f"{s['id']:9s} {s['t0']:7.2f}–{s['t1']:7.2f}  {s['kind']:7s} {s['s0']}→{s['s1']}")
for v in vo: print(v['id'], v['t'], '→', round(v['t'] + vdur[v['id']], 2), v['text'])
