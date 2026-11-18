"""Continue the satellite lock into a 3D orbit + tilt dive, ending with the camera looking south-west over
the hospital roof (the same direction as the site photos, toward the grain bins)."""
import math, os, sys, subprocess, numpy as np, cv2
sys.argv = [sys.argv[0], os.path.join(os.path.dirname(__file__), 'frames_unused')]
import importlib.util
spec = importlib.util.spec_from_file_location('sz', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'satzoom_lib.py'))
sz = importlib.util.module_from_spec(spec); spec.loader.exec_module(sz)
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, DUR = 1080, 1920, 30, 1.7
L = 19
sz.R = 2300
m, tx, ty = sz.mosaic(L)
mos = cv2.cvtColor(np.array(m), cv2.COLOR_RGB2BGR)
fy = (H / 2) / math.tan(math.radians(30))
D0 = 0.5606 * fy            # matches the last satzoom frame (Z=19.25 rendered at 720 then upscaled 1.5x)
D1 = 0.38 * fy
FB = '/usr/share/fonts/opentype/inter/Inter-Black.otf'; FX = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
FM = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
f_big = ImageFont.truetype(FB, 66); f_mid = ImageFont.truetype(FX, 39); f_mono = ImageFont.truetype(FM, 30)
RED = (225, 25, 35)

def ease(t): return t * t * t * (t * (6 * t - 15) + 10)

K = np.array([[fy, 0, W / 2], [0, fy, H / 2], [0, 0, 1]])
n = int(DUR * FPS)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tiltdive.mp4')
p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-vf', 'noise=alls=4:allf=t', '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
yy = np.linspace(0, 1, H)[:, None, None]
for i in range(n):
    t = ease(i / (n - 1))
    az = math.radians(-135 * t)
    th = math.radians(54 * t)
    D = D0 + (D1 - D0) * t
    dx, dy = math.sin(az), -math.cos(az)
    T = np.array([tx + 25 * t * dx, ty + 25 * t * dy, 0.0])
    f = np.array([dx * math.sin(th), dy * math.sin(th), -math.cos(th)])
    C = T - D * f
    r = np.array([-dy, dx, 0.0])
    u = np.array([-dx * math.cos(th), -dy * math.cos(th), -math.sin(th)])
    M = np.stack([np.array([r[0], u[0], f[0]]), np.array([r[1], u[1], f[1]]),
                  -np.array([r @ C, u @ C, f @ C])], axis=1)
    Hm = K @ M
    fr = cv2.warpPerspective(mos, Hm, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
    # atmospheric haze toward the top as the camera tilts up
    haze = np.clip((0.5 - yy) / 0.5, 0, 1) ** 1.3 * (math.sin(th) ** 1.2) * 0.97
    fr = fr * (1 - haze) + np.array([225, 205, 185], np.float32) * haze
    fr = cv2.convertScaleAbs(fr, alpha=1.08, beta=-6)
    # HUD fades out during the dive
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).convert('RGBA')
    hud = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(hud)
    a = int(255 * max(0, 1 - (i / (n - 1)) / 0.55))
    if a > 0:
        d.rectangle((0, 0, W, 96), fill=(0, 0, 0, int(a * 0.67)))
        d.text((36, 27), 'SAT-LINK', font=f_mid, fill=(255, 255, 255, a))
        d.text((264, 33), 'LIVE', font=f_mono, fill=RED + (a,))
        d.rectangle((0, H - 315, W, H), fill=(0, 0, 0, int(a * 0.59)))
        d.rectangle((36, H - 279, 45, H - 60), fill=RED + (a,))
        d.text((66, H - 285), '49.1818° N   105.9526° W', font=f_mono, fill=(255, 255, 255, a))
        d.text((66, H - 237), 'ROCKGLEN, SASKATCHEWAN', font=f_big, fill=(255, 255, 255, a))
        d.text((66, H - 147), 'TARGET LOCKED', font=f_mid, fill=RED + (a,))
        d.text((66, H - 93), 'HOSPITAL SITE  •  26,500+ SQ FT', font=f_mono, fill=(255, 255, 255, a))
    d.text((W - 18, 111), 'Imagery © Esri, Maxar, Earthstar Geographics', font=ImageFont.truetype(FM, 18), fill=(255, 255, 255, 150), anchor='ra')
    im = Image.alpha_composite(im, hud).convert('RGB')
    p.stdin.write(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR).tobytes())
p.stdin.close(); p.wait(); print('tiltdive', n)
