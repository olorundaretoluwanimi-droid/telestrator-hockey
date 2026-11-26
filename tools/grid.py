"""Read coordinates off the source: one source frame (1280×720), a region enlarged, with a labelled pixel grid in SOURCE coordinates.
  python tools/grid.py <out.jpg> <t_s> [x0 y0 x1 y1] [step=20] [scale=2]
"""
import subprocess, sys, os, tempfile
from PIL import Image, ImageDraw, ImageFont
SRC = os.path.join(os.path.dirname(__file__), '..', 'raw', 'umb_psu_video.mp4')
a = sys.argv[1:]; out, t = a[0], float(a[1])
x0, y0, x1, y1 = (int(v) for v in a[2:6]) if len(a) >= 6 else (0, 0, 1280, 720)
step = int(a[6]) if len(a) > 6 else 20; sc = float(a[7]) if len(a) > 7 else 2
p = os.path.join(tempfile.mkdtemp(), 'f.png')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.4f}', '-i', SRC, '-frames:v', '1', p], check=True)
im = Image.open(p).convert('RGB').crop((x0, y0, x1, y1))
im = im.resize((int((x1 - x0) * sc), int((y1 - y0) * sc)), Image.LANCZOS)
d = ImageDraw.Draw(im, 'RGBA'); f = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 12)
for x in range((x0 // step + 1) * step, x1, step):
    X = (x - x0) * sc; major = x % (step * 5) == 0
    d.line([(X, 0), (X, im.height)], fill=(255, 0, 255, 150 if major else 60), width=1)
    if major: d.text((X + 2, 2), str(x), fill=(255, 255, 0), font=f)
for y in range((y0 // step + 1) * step, y1, step):
    Y = (y - y0) * sc; major = y % (step * 5) == 0
    d.line([(0, Y), (im.width, Y)], fill=(255, 0, 255, 150 if major else 60), width=1)
    if major: d.text((2, Y + 2), str(y), fill=(255, 255, 0), font=f)
d.rectangle([0, im.height - 18, 110, im.height], fill=(0, 0, 0, 200)); d.text((3, im.height - 16), f't={t:.3f}', fill='yellow', font=f)
im.save(out, quality=88); print(out, im.size)
