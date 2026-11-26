#!/usr/bin/env python3
"""Mix for THE SLOT — "Bookends": broadcast sound (commentary + crowd) + voice-over (Stephen Courson via AI33) + sampled score + foley → out/mix.wav (48 kHz stereo).
Music rule (STYLE.md §8): while the picture plays, the band plays; on a freeze the drums stop — one stab + timpani + thump + shutter, then hi-hat only.
Live play carries the broadcast commentary at full level (it calls the goals); freezes and slow motion get a low-passed crowd murmur of the same moment.
Run with the library's Python: $LIB/.venv/Scripts/python.exe tools/mix.py"""
import sys, os, json
import numpy as np, soundfile as sf, soxr
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.environ.get('LIB') or 'C:/Users/HP/lemo-opuscar'; sys.path.insert(0, LIB)
from core.audio import sampler as S
from core.audio.sfx import SR, add, lp, hp, bp, noise, env_exp, t_, thump, whoosh, step, pop, norm, limit

TL = json.load(open(f'{D}/timeline.json', encoding='utf-8')); DUR = TL['dur']; N = int(DUR * SR)
seg = {s['id']: s for s in TL['seg']}
S.seed(11)
def stereo(n=N): return np.zeros((n, 2), np.float32)
def fade(x, fi=.03, fo=.06):
    n = len(x); a = min(int(fi * SR), n // 2); b = min(int(fo * SR), n // 2)
    if a: x[:a] *= np.linspace(0, 1, a)[:, None]
    if b: x[-b:] *= np.linspace(1, 0, b)[:, None]
    return x
def put(buf, x, at, g=1.0):
    s = int(at * SR); e = min(len(buf), s + len(x));
    if e > s: buf[s:e] += x[:e - s] * g

# ---------- broadcast sound ----------
o, osr = sf.read(f'{D}/audio/orig.wav', dtype='float32')
if osr != SR: o = soxr.resample(o, osr, SR)
o = o / (np.sqrt((o ** 2).mean()) + 1e-9) * 10 ** (-22 / 20)          # whole programme to about −22 dBFS RMS
def osl(a, b): return o[int(a * SR):int(b * SR)].copy()
def murmur(a, b, out_len):
    """low-passed crowd + commentary murmur of the source moment a–b, stretched/looped to out_len seconds (speech becomes unintelligible)"""
    x = osl(a - .5, max(b, a + 1.5) + .5); x = np.stack([lp(lp(x[:, c], 500), 500) for c in range(2)], 1).astype(np.float32)
    n = int(out_len * SR); y = np.zeros((n, 2), np.float32); p = 0
    while p < n: L = min(len(x), n - p); y[p:p + L] += fade(x[:L].copy(), .2, .2); p += max(1, L - int(.2 * SR))
    return y
orig = stereo()
for sid, s in seg.items():
    k = s['kind']; d = s['t1'] - s['t0']
    if k in ('live', 'rep'):                                  # 1×: the broadcast sound itself
        put(orig, fade(osl(s['s0'], s['s1'] + .05), .03, .12), s['t0'], 1.0)
    elif k in ('fz', 'slow', 'split', 'splitfz'):
        put(orig, murmur(s['s0'], s['s1'], d), s['t0'], .55)
    elif k == 'rew':                                          # the live sound reversed and squeezed into 0.6 s
        rv = osl(276.6, 284.7)[::-1]; rv = soxr.resample(rv, SR * 8.1 / .6, SR)[:int(.6 * SR)]; put(orig, fade(rv, .02, .05), s['t0'], .35)
    elif k == 'map':
        put(orig, murmur(280.0, 283.0, d), s['t0'], .3)
# end: the commentator's sign-off runs over the slate (L-cut) — "Beacons eight, Panthers five, and that is execution."
put(orig, fade(osl(283.55, 288.9), .05, .4), seg['end']['t0'] + .15, 1.0)
put(orig, murmur(296.5, 300.5, seg['card']['t1'] - seg['end']['t0'] - 5.3), seg['end']['t0'] + 5.3, .3)

# ---------- voice-over ----------
vo = stereo(); vdur = json.load(open(f'{D}/audio/vo/dur.json'))
for v in TL['vo']:
    x, vsr = sf.read(f'{D}/audio/vo/{v["id"]}.wav', dtype='float32')
    if x.ndim > 1: x = x.mean(1)
    if vsr != SR: x = soxr.resample(x, vsr, SR)
    x = hp(x, 90).astype(np.float32); x = x / (np.sqrt((x[np.abs(x) > 1e-3] ** 2).mean()) + 1e-9) * 10 ** (-17 / 20)
    add(vo, x, v['t'], 1.0, 0)
vmask = np.zeros(N, np.float32)
for v in TL['vo']: a, b = int(v['t'] * SR), int((v['t'] + vdur[v['id']]) * SR); vmask[a:b] = 1
k = int(.12 * SR); vmask = np.convolve(vmask, np.ones(k) / k, 'same'); duck = (1 - .55 * vmask)[:, None]

# ---------- score: sampled band, A minor, 124 BPM ----------
B = 60 / 124; ev = []
BASS = ['A1', 'A1', 'C2', 'D2', 'A1', 'A1', 'E2', 'D2']
def groove(a, b, g=1.0, half=False, hat=True):
    t = a; i = 0
    while t < b - 1e-6:
        beat = i % 4
        if hat: ev.append((t, 'drum_kit', 'hi_hat_closed', None, .42 * g, .3)); ev.append((t + B / 2, 'drum_kit', 'hi_hat_closed', None, .28 * g, .3))
        if half:
            if beat == 0: ev.append((t, 'drum_kit', 'kick_drum_left', None, .8 * g, 0))
            if beat == 2: ev.append((t, 'drum_kit', 'snare_1', None, .55 * g, -.05))
            if beat in (0, 2): ev.append((t, 'electric_bass', BASS[(i // 2) % 8], B * 1.8, .7 * g, 0))
        else:
            if beat in (0, 2) or (beat == 3 and i % 8 == 7): ev.append((t, 'drum_kit', 'kick_drum_left', None, .9 * g, 0))
            if beat in (1, 3): ev.append((t, 'drum_kit', 'snare_1', None, .72 * g, -.05))
            ev.append((t, 'electric_bass', BASS[i % 8], B * .8, .72 * g, 0))
            if beat == 1: ev.append((t + B / 2, 'electric_bass', BASS[(i + 1) % 8], B * .4, .55 * g, 0))
        t += B; i += 1
def stab(t, g=1.0, big=False):
    for p in ['A4', 'C5', 'E5'] + (['A5'] if big else []): ev.append((t, 'trumpet_stac', p, .3, .85 * g, .15))
    for p in ['A2', 'E3']: ev.append((t, 'trombone_stac', p, .35, .85 * g, -.15))
    ev.append((t, 'timpani', 'A2', 1.2, .9 * g, 0))
    if big: ev.append((t, 'drum_kit', 'crash_left', None, .8 * g, -.3))
def hats(a, b, g=.24):
    t = a
    while t < b - .05: ev.append((t, 'drum_kit', 'hi_hat_closed', None, g, .3)); t += B / 2

ST = seg['sting']['t0']; stab(ST + .44, 1.0, big=True); ev.append((ST, 'drum_kit', 'tom_1', None, .5, .2)); ev.append((ST + .2, 'drum_kit', 'tom_2', None, .6, -.2))
for k_ in range(6): ev.append((ST + 1.1 + k_ * .1, 'drum_kit', 'snare_2', None, .25 + .08 * k_, 0))
R0 = seg['record']['t0']; groove(R0, seg['record']['t1'], .95)
for i in range(13): ev.append((R0 + .9 + i * .12, 'glockenspiel', ['A6', 'E6'][i % 2], .3, .32, .25))
for sid, s in seg.items():
    if s['kind'] in ('live',): groove(s['t0'], s['t1'], .38)
    if s['kind'] in ('slow', 'split', 'rep'): groove(s['t0'], s['t1'], .6, half=True)
    if s['kind'] in ('fz', 'splitfz'):
        stab(s['t0'], .55); hats(s['t0'] + B, s['t1'], .22 if sid != 'dfz3' else .0)   # dfz3: near-silence before the shot
for G in TL['goals']: stab(G['t'], .8, big=True); ev.append((G['t'] + .05, 'glockenspiel', 'A6', .5, .45, .2))
# the turn: near-silence into it, then a slow build with a timpani hit on each Plymouth State goal
T0 = seg['turn']['t0']; groove(T0 + 1.0, seg['turn']['t1'], .55, half=True)
for d_ in [1.5, 2.7, 3.5]: ev.append((T0 + d_, 'timpani', 'E2', 1.0, .8, 0)); ev.append((T0 + d_, 'trombone_stac', 'E2', .5, .7, -.1))
ev.append((T0 + 4.3, 'drum_kit', 'crash_left', None, .55, -.3))
for p in ['A2', 'E3']: ev.append((T0 + .1, 'cellos', p, 3.2, .4, 0))
# map: stab → timpani roll under the flatten → stab when the board settles → glock as rows land → half-time
M0 = seg['map']['t0']; stab(M0, .55)
for i in range(16): ev.append((M0 + .55 + i * .065, 'timpani', 'A2', .3, .22 + .04 * i, 0))
stab(M0 + 1.6, .7)
for tt, p in [(M0 + 2.0, 'C6'), (M0 + 2.35, 'E6'), (M0 + 2.7, 'A6')]: ev.append((tt, 'glockenspiel', p, .6, .5, .2))
groove(M0 + 3.2, seg['map']['t1'], .5, half=True)
D0 = seg['data']['t0']; groove(D0, seg['data']['t1'], .58)
for i, p in enumerate(['A5', 'C6', 'E6', 'A6']): ev.append((D0 + .5 + i * .3, 'glockenspiel', p, .5, .42, .2))
E0 = seg['end']['t0']; stab(E0, 1.0, big=True)
for p in ['A2', 'E3', 'C4']: ev.append((E0 + .05, 'horn', p, 4.2, .5, 0))
ev.append((E0 + .05, 'cellos', 'A1', 4.3, .45, 0))
C0 = seg['card']['t0']; ev.append((C0, 'timpani', 'A2', 1.6, .55, 0)); CL = seg['card']['t1'] - C0
for p in ['A2', 'E3', 'A3']: ev.append((C0 + .05, 'horn', p, CL - .3, .4, 0))
ev.append((C0 + .05, 'cellos', 'A1', CL - .2, .4, 0)); ev.append((C0 + .2, 'glockenspiel', 'A6', .8, .4, .2)); ev.append((C0 + .45, 'glockenspiel', 'E6', 1.0, .34, .25))
music = S.render(ev, dur=DUR + 3)[:N].astype(np.float32)
music = S.room(music, size=.35, mix=.12)[:N]
music = music / (np.sqrt((music ** 2).mean()) + 1e-9) * 10 ** (-27 / 20)
gap = np.ones(N, np.float32)                                  # near-silence: the half second before the turn board
a, b = int((T0 - .55) * SR), int((T0 + .9) * SR); gap[a:b] = np.concatenate([np.linspace(1, .05, int(.15 * SR)), np.full(b - a - int(.15 * SR), .05)])
mf = np.ones(N, np.float32); a = int((DUR - 1.2) * SR); mf[a:] = np.linspace(1, 0, N - a) ** 1.5
music *= (gap * mf)[:, None]; orig *= gap[:, None]

# ---------- foley ----------
fx = stereo()
def squeak(d, v=1.0, seed=0):
    rng = np.random.default_rng(seed); n = int(d * SR); tt = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 2200, 5200)
    am = .55 + .45 * np.sin(2 * np.pi * (24 + 8 * rng.random()) * tt + rng.random() * 6) * (1 + .3 * np.sin(2 * np.pi * 3.1 * tt))
    e = np.minimum(1, tt / .02) * np.minimum(1, (d - tt) / .04)
    return (norm(x * am * e) * v).astype(np.float32)
def shutter(v=1.0):
    d = .09; x = hp(noise(d), 1500) * (env_exp(d, .004) + .6 * np.roll(env_exp(d, .006), int(.035 * SR)))
    return (norm(x) * v).astype(np.float32)
i = 0
for sid, s in seg.items():
    if s['kind'] in ('fz', 'splitfz', 'map'):
        add(fx, thump(1, 52), s['t0'], .7); add(fx, shutter(1), s['t0'], .45)
        for d_ in (.12, .45, .8): add(fx, squeak(.32, .45, i), s['t0'] + d_, .5, (i % 3 - 1) * .2); i += 1   # marker lines
        for d_ in (.2, .5): add(fx, pop(1), s['t0'] + d_, .18, .1)                                        # rings
        add(fx, step(1), s['t0'] + 1.05, .25)                                                              # the label lands
for sid in ['sting', 'record', 'g2live', 'turn', 'g9live', 'g10live', 'g12', 'dlive', 'map', 'data', 'end', 'card']: add(fx, whoosh(.34, 1), seg[sid]['t0'] - .17, .35)
add(fx, whoosh(.9, 1), M0 + .55, .3)
for d_ in (2.6, 2.9): add(fx, squeak(.35, .4, 90 + int(d_ * 10)), R0 + d_, .5)
add(fx, squeak(.36, .7, 77), ST + .12, .55)   # the sting's marker slash                             # bracket circles on the record card
add(fx, squeak(.5, .45, 99), T0 + 4.3, .5); add(fx, squeak(.5, .45, 98), D0 + 2.0, .5)
w = (bp(noise(.6), 300, 2200) * np.sin(np.pi * t_(.6) / .6)).astype(np.float32); add(fx, norm(w), seg['drew']['t0'], .25)
for sid in ['dslow2', 'dfz3', 'dgo']:                                                                        # stopwatch ticks while the arena clock is shown
    s = seg[sid]; t = s['t0']
    while t < s['t1']:
        src = s['s0'] + (s['s1'] - s['s0']) * (t - s['t0']) / (s['t1'] - s['t0'])
        if src < 281.5: add(fx, step(.6), t, .16, .3)
        t += .2

# ---------- bus ----------
mix = orig * duck * 1.0 + vo * 1.0 + music * duck * 1.0 + fx * .5
tail = np.ones(N, np.float32); a = int((DUR - .45) * SR); tail[a:] = np.linspace(1, 0, N - a) ** 2; mix *= tail[:, None]
for c in range(2): mix[:, c] = limit(mix[:, c], .5)
os.makedirs(f'{D}/out', exist_ok=True); sf.write(f'{D}/out/mix.wav', mix, SR, subtype='PCM_24')
print('mix', mix.shape, 'peak', float(np.abs(mix).max()))
print(S.credits(sorted({e[1] for e in ev})))
