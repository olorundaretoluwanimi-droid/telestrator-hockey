"""Contact sheet of the source video with source-time labels.
  python tools/sheet.py <out.jpg> <start_s> <dur_s> <fps> [width=384] [cols=6]
  python tools/sheet.py <out.jpg> --frames 61.2,61.5,62.0 [width] [cols]   (exact source times)
"""
import subprocess, sys, os, tempfile, glob
from PIL import Image, ImageDraw, ImageFont
SRC = os.path.join(os.path.dirname(__file__), '..', 'raw', 'umb_psu_video.mp4')
a = sys.argv[1:]; out = a[0]
font = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 15)
tmp = tempfile.mkdtemp()
if a[1] == '--frames':
    ts = [float(x) for x in a[2].split(',')]; rest = a[3:]
else:
    s, d, fps = float(a[1]), float(a[2]), float(a[3]); rest = a[4:]
    n = int(d * fps); ts = [round(s + i / fps, 3) for i in range(n)]
w = int(rest[0]) if rest else 384; cols = int(rest[1]) if len(rest) > 1 else 6
ims = []
for i, t in enumerate(ts):
    p = os.path.join(tmp, f'{i:04d}.png')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.3f}', '-i', SRC, '-frames:v', '1', '-vf', f'scale={w}:-1', p], check=True)
    im = Image.open(p).convert('RGB'); dr = ImageDraw.Draw(im)
    dr.rectangle([0, 0, 92, 18], fill='black'); dr.text((3, 1), f'{t:.2f}', fill='yellow', font=font); ims.append(im)
h = ims[0].height; rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, rows * h))
for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out, quality=85); print(out, len(ims), 'frames')
