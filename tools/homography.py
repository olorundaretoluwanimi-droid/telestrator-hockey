"""Rink homography for the goal frame: rink feet → source pixels (1280×720), least squares over the marked points.
Rink coordinates: u = feet out from the goal line toward centre ice, v = feet across (+ = camera-side boards), goal centre = (0, 0).
Rink (NCAA/NHL standard): posts v = ±3, end-zone dots u = 20, v = ±22, circle radius 15, blue line u = 64, boards v = ±42.5, goal line 11 ft from the end boards.
  python tools/homography.py check   → research/g/hcheck.jpg (predicted markings drawn on the frame)
  python tools/homography.py         → assets/rink.json
"""
import json, sys, os, subprocess, tempfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..')
FRAME_T = 280.7
PTS = [  # (u, v) feet → (x, y) source px, read on research/g/h1.jpg and c_m25.jpg
    ((0, 3), (384, 355)),     # near post (foot)
    ((0, -3), (462, 344)),    # far post (foot)
    ((20, -22), (872, 355)),  # far end-zone dot
    ((20, 22), (305, 473)),   # near end-zone dot
]
def fit(pts):
    A = []
    for (u, v), (x, y) in pts:
        A.append([u, v, 1, 0, 0, 0, -x * u, -x * v, -x]); A.append([0, 0, 0, u, v, 1, -y * u, -y * v, -y])
    _, _, Vt = np.linalg.svd(np.array(A, float)); H = Vt[-1].reshape(3, 3); return H / H[2, 2]
def ap(H, u, v):
    p = H @ [u, v, 1]; return p[0] / p[2], p[1] / p[2]
H = fit(PTS)
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        from PIL import Image, ImageDraw
        p = os.path.join(tempfile.mkdtemp(), 'f.png')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(FRAME_T), '-i', os.path.join(ROOT, 'raw', 'umb_psu_video.mp4'), '-frames:v', '1', p], check=True)
        im = Image.open(p).convert('RGB'); d = ImageDraw.Draw(im)
        import math
        def poly(pts, col, w=2): d.line([ap(H, u, v) for u, v in pts], fill=col, width=w)
        poly([(0, -42.5), (0, 42.5)], (255, 0, 0)); poly([(64, -42.5), (64, 42.5)], (0, 120, 255), 3)
        for s in (-1, 1):
            poly([(20 + 15 * math.cos(a / 40 * 2 * math.pi), s * 22 + 15 * math.sin(a / 40 * 2 * math.pi)) for a in range(41)], (255, 0, 255))
        poly([(6 * math.cos(a / 20 * math.pi - math.pi / 2), 6 * math.sin(a / 20 * math.pi - math.pi / 2)) for a in range(21)], (0, 255, 255))
        poly([(-11, -42.5), (-11, 42.5)], (255, 255, 0)); poly([(-11, 42.5), (70, 42.5)], (255, 255, 0)); poly([(-11, -42.5), (70, -42.5)], (255, 255, 0))
        for (u, v), (x, y) in PTS:
            px, py = ap(H, u, v); d.ellipse([x - 4, y - 4, x + 4, y + 4], outline=(0, 255, 0), width=2); print((u, v), 'resid', round(px - x, 1), round(py - y, 1))
        im.save(os.path.join(ROOT, 'research', 'g', 'hcheck.jpg'), quality=88); print('wrote research/g/hcheck.jpg')
    else:
        os.makedirs(os.path.join(ROOT, 'assets'), exist_ok=True)
        json.dump({'t': FRAME_T, 'H': H.tolist()}, open(os.path.join(ROOT, 'assets', 'rink.json'), 'w'), indent=1); print('assets/rink.json')
