"""Throne Roofing - story-style drone reel (1080x1920, 30fps).

Usage: python3 make_video.py <photos_dir> <out.mp4> [--preview t1,t2,...]
"""
import sys, os, subprocess, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import roofsim as R

W, H, FPS = 1080, 1920, 30
PH = sys.argv[1]
OUT = sys.argv[2]
FONT = '/usr/share/fonts/opentype/inter/'
RED = (186, 31, 39)

def font(name, size):
    return ImageFont.truetype(FONT + name, size)

def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)

def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3

def lerp(a, b, t):
    return a + (b - a) * t

def photo(i):
    names = sorted(f for f in os.listdir(PH) if f.lower().endswith(('jpg', 'jpeg')))
    return Image.open(os.path.join(PH, names[i])).convert('RGB')

def wobble(t, amp=1.0, seed=0):
    """low-frequency drone hover drift"""
    return (amp * (math.sin(t * 1.3 + seed) * 0.6 + math.sin(t * 2.9 + seed * 2) * 0.3 + math.sin(t * 6.1 + seed) * 0.1),
            amp * (math.cos(t * 1.1 + seed) * 0.6 + math.sin(t * 3.3 + seed * 3) * 0.3 + math.cos(t * 7.0 + seed) * 0.1))

def view(src, cx, cy, scale, ang=0.0):
    """Render a WxH view of src centred on (cx,cy); scale = src px per output px."""
    a = math.radians(ang)
    ca, sa = math.cos(a) * scale, math.sin(a) * scale
    # output (u,v) -> src: x = ca*(u-W/2) - sa*(v-H/2) + cx
    coeffs = (ca, -sa, cx - ca * W / 2 + sa * H / 2,
              sa, ca, cy - sa * W / 2 - ca * H / 2)
    return src.transform((W, H), Image.AFFINE, coeffs, resample=Image.BILINEAR)

# ------------------------------------------------------------------ grading
_x = np.arange(256) / 255.0
_curve = np.clip(_x + 0.10 * np.sin(2 * np.pi * _x) * -0.5 + 0.0, 0, 1)     # gentle S
_curve = 0.025 + 0.965 * (_x - 0.12 * np.sin(2 * np.pi * _x) / (2 * np.pi) * 2.2)
_curve = np.clip(_curve, 0, 1)
LUT_R = np.clip(255 * (_curve ** 0.97) * 1.015, 0, 255).astype(np.uint8)
LUT_G = np.clip(255 * _curve, 0, 255).astype(np.uint8)
LUT_B = np.clip(255 * (_curve ** 1.03) * 0.99 + 6 * (1 - _x), 0, 255).astype(np.uint8)
yy, xx = np.mgrid[0:H, 0:W]
_d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
VIG = (1 - 0.30 * np.clip(_d - 0.45, 0, 1) ** 1.6).astype(np.float32)[..., None]
GRAIN = [np.random.default_rng(k).normal(0, 3.2, (H, W, 1)).astype(np.float32) for k in range(6)]

def grade(img, fi, sat=1.08):
    a = np.asarray(img, np.uint8)
    a = np.stack([LUT_R[a[..., 0]], LUT_G[a[..., 1]], LUT_B[a[..., 2]]], -1).astype(np.float32)
    lum = a.mean(-1, keepdims=True)
    a = lum + (a - lum) * sat
    a = a * VIG + GRAIN[fi % 6]
    return np.clip(a, 0, 255).astype(np.uint8)

# ------------------------------------------------------------------ text
def text_layer():
    return Image.new('RGBA', (W, H), (0, 0, 0, 0))

def draw_text(lay, txt, y, size, alpha=1.0, dy=0, fnt='Inter-ExtraBold.otf', fill=(255, 255, 255), track=0, x=None, shadow=True):
    if alpha <= 0:
        return
    f = font(fnt, size)
    # width with tracking
    widths = [f.getlength(c) + track for c in txt]
    tw = sum(widths) - track
    x0 = (W - tw) / 2 if x is None else x
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    d = ImageDraw.Draw(lay)
    cx = x0
    for c, wdt in zip(txt, widths):
        if shadow:
            ds.text((cx + 2, y + dy + 4), c, font=f, fill=(0, 0, 0, int(170 * alpha)))
        cx += wdt
    if shadow:
        sh = sh.filter(ImageFilter.GaussianBlur(7))
        lay.alpha_composite(sh)
    cx = x0
    for c, wdt in zip(txt, widths):
        d.text((cx, y + dy), c, font=f, fill=fill + (int(255 * alpha),))
        cx += wdt
    return tw

def pill(lay, txt, y, alpha, dy=0, size=34):
    if alpha <= 0:
        return
    f = font('Inter-Bold.otf', size)
    tw = f.getlength(txt) + 3 * len(txt)
    pw, phh = tw + 48, size + 26
    x0 = (W - pw) / 2
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([x0, y + dy, x0 + pw, y + dy + phh], phh // 2, fill=RED + (int(235 * alpha),))
    cx = x0 + 24
    for c in txt:
        d.text((cx, y + dy + 10), c, font=f, fill=(255, 255, 255, int(255 * alpha)))
        cx += f.getlength(c) + 3

def caption(lay, lines, t, t0, t1, y=1260, size=78, kicker=None):
    """animated caption: slide-up + fade in/out between t0..t1"""
    if t < t0 - 0.01 or t > t1:
        return
    a = ease((t - t0) / 0.35) * (1 - ease((t - (t1 - 0.3)) / 0.3))
    dy = (1 - ease_out((t - t0) / 0.45)) * 40
    yy = y
    if kicker:
        pill(lay, kicker, yy - 90, a, dy)
    for i, ln in enumerate(lines):
        draw_text(lay, ln, yy + i * (size + 14), size, a, dy * (1 + 0.3 * i), track=1)

def hud(lay, t, alpha):
    if alpha <= 0:
        return
    d = ImageDraw.Draw(lay)
    c = (255, 255, 255, int(150 * alpha))
    m, L = 70, 60
    for (x, y, sx, sy) in ((m, 260, 1, 1), (W - m, 260, -1, 1), (m, H - 420, 1, -1), (W - m, H - 420, -1, -1)):
        d.line([(x, y), (x + sx * L, y)], fill=c, width=3)
        d.line([(x, y), (x, y + sy * L)], fill=c, width=3)
    f = font('Inter-SemiBold.otf', 28)
    if int(t * 2) % 2 == 0:
        d.ellipse([m + 4, 200, m + 24, 220], fill=(230, 40, 40, int(220 * alpha)))
    d.text((m + 36, 194), 'REC  4K 30', font=f, fill=c)
    alt = 118 - 40 * min(t / 9, 1)
    d.text((W - m - 230, 194), f'H {alt:5.1f} m', font=f, fill=c)
    # centre crosshair
    d.line([(W / 2 - 18, H / 2), (W / 2 + 18, H / 2)], fill=(255, 255, 255, int(80 * alpha)), width=2)
    d.line([(W / 2, H / 2 - 18), (W / 2, H / 2 + 18)], fill=(255, 255, 255, int(80 * alpha)), width=2)

# ------------------------------------------------------------------ shots
class PhotoShot:
    def __init__(self, idx, t0, t1, start, end, seed=0, sat=1.08):
        """start/end: (fx, fy, zoom, ang); fx/fy in 0..1 of the photo, zoom 1 = cover-fit"""
        self.img = photo(idx)
        self.t0, self.t1, self.start, self.end, self.seed, self.sat = t0, t1, start, end, seed, sat
        iw, ih = self.img.size
        self.cover = min(iw / W, ih / H)            # src px per out px when cover-fitting

    def render(self, t):
        u = ease((t - self.t0) / (self.t1 - self.t0)) * 0.6 + ((t - self.t0) / (self.t1 - self.t0)) * 0.4
        fx, fy, z, ang = [lerp(a, b, u) for a, b in zip(self.start, self.end)]
        iw, ih = self.img.size
        s = self.cover / z
        wx, wy = wobble(t, 2.5, self.seed)
        cx = fx * iw + wx * s
        cy = fy * ih + wy * s
        # keep inside image
        hw, hh = W * s / 2 * 1.02, H * s / 2 * 1.02
        cx = min(max(cx, hw), iw - hw) if iw > 2 * hw else iw / 2
        cy = min(max(cy, hh), ih - hh) if ih > 2 * hh else ih / 2
        return view(self.img, cx, cy, s, ang + 0.25 * math.sin(t * 0.9 + self.seed))


class RoofShot:
    def __init__(self, roof):
        self.roof = roof

    def static(self, t, t0, t1):
        """establishing descent over the old roof, ends close on the damage"""
        u = ease((t - t0) / (t1 - t0))
        fr = self.roof.frame((0, 0, 0), sun=(0.5, 0.8), cloud_t=900 + t * 40, extras=(0, []), dump=0.0)
        src = Image.fromarray(fr)
        wx, wy = wobble(t, 3.0, 4)
        cx = lerp(900, 985, u) + wx
        cy = lerp(1650, 1520, u) + wy
        scale = lerp(1.62, 0.62, u)
        ang = lerp(-14, -3, u)
        return view(src, cx, cy, scale, ang)

    def timelapse(self, t, t0, t1):
        n = R.NROLLS
        p = (t - t0) / (t1 - t0)
        day = min(int(p * 3), 2)
        pd = p * 3 - day
        # fronts in rolls, piecewise per day
        keys = [(0, 0.0, 0.0, 0.0), (1, 0.72, 0.32, 0.0), (2, 1.0, 1.0, 0.25), (3, 1.0, 1.0, 1.0)]
        a, b = keys[day], keys[day + 1]
        tear = lerp(a[1], b[1], pd) * n
        base = lerp(a[2], b[2], pd) * n
        cap = lerp(a[3], b[3], pd) * n
        # sun sweeps each day (morning -> evening)
        ang = lerp(-0.9, 0.9, pd)
        sun = (math.sin(ang) * 1.1, 0.75 + 0.2 * math.cos(ang))
        # night dip between days
        dip = min(pd / 0.05, (1 - pd) / 0.05, 1.0)
        exposure = 0.55 + 0.45 * dip if day < 3 else 1
        rng = np.random.default_rng(int(t * FPS))
        workers, flames, extras = [], [], []
        vests = [(244, 120, 24), (206, 232, 40), (244, 120, 24), (206, 232, 40)]
        hats = [(250, 250, 250), (240, 150, 20), (250, 250, 250), (230, 40, 40)]
        def front_pos(fr, k):
            full = int(fr); part = fr - full
            y = R.RY0 + full * R.ROLL + R.ROLL / 2
            w = R.RX1 - R.RX0
            x = R.RX0 + (part * w if full % 2 == 0 else w - part * w)
            return x, y, full
        if 0 < tear < n and dip > 0.3:
            x, y, full = front_pos(tear, 0)
            for k in range(3):
                workers.append((x + rng.normal(0, 90) - 60 * k, y + rng.normal(0, 20) + 50, vests[k], hats[k], rng.uniform(0, 3)))
            extras.append((min(max(x, R.RX0 + 80), R.RX1 - 120), y + 120, 'debris'))
        if 0 < base < n and dip > 0.3:
            x, y, full = front_pos(base, 1)
            for k in range(2):
                wx_, wy_ = x + rng.normal(0, 25) + (-40 if full % 2 == 0 else 40) * k, y + rng.normal(0, 10) - 10
                workers.append((wx_, wy_, vests[k + 1], hats[k + 2], 1.57 + rng.normal(0, .3)))
                flames.append((wx_ + (30 if full % 2 == 0 else -30), wy_ + 22, rng.uniform(0.7, 1.15)))
            extras.append((R.RX0 + 40, R.RY0 + max(full - 2, 0) * R.ROLL, 'rolls'))
            extras.append((R.RX0 + 140, R.RY0 + max(full - 2, 0) * R.ROLL + 30, 'tank'))
        if 0 < cap < n and dip > 0.3:
            x, y, full = front_pos(cap, 2)
            for k in range(2):
                wx_, wy_ = x + rng.normal(0, 25) + (-40 if full % 2 == 0 else 40) * k, y + rng.normal(0, 10) - 10
                workers.append((wx_, wy_, vests[k], hats[k], 1.57 + rng.normal(0, .3)))
                flames.append((wx_ + (30 if full % 2 == 0 else -30), wy_ + 22, rng.uniform(0.7, 1.15)))
            extras.append((R.RX1 - 140, R.RY0 + max(full - 2, 0) * R.ROLL, 'capr'))
        # a couple of people walking around / carrying material
        if dip > 0.3:
            for k in range(2):
                workers.append((rng.uniform(R.RX0 + 100, R.RX1 - 100), R.RY0 + rng.uniform(0.05, 0.9) * (R.RY1 - R.RY0) * min(1, (tear + 2) / n), vests[k], hats[k], rng.uniform(0, 3)))
        dump = min(1.0, tear / n * 1.2)
        fr = self.roof.frame((tear, base, cap), sun=sun, cloud_t=(t - t0) * 260, workers=workers, flames=flames,
                             extras=(day, extras), exposure=exposure * (1 + rng.normal(0, 0.012)), dump=dump)
        src = Image.fromarray(fr)
        u = (t - t0) / (t1 - t0)
        wx, wy = wobble(t, 1.2, 7)
        return view(src, 900 + wx, lerp(1760, 1800, u) + wy, lerp(1.40, 1.30, u), 0)


def whip(a, b, k, axis=0, direction=1):
    """whip-pan from frame a to frame b (k: 0..1) with directional motion blur"""
    size = H if axis == 0 else W
    comb = np.concatenate([a, b], axis)
    off = int(ease(k) * size)
    fr = comb[off:off + H] if axis == 0 else comb[:, off:off + W]
    sp = math.sin(math.pi * k)
    n = int(2 + sp * 10)
    step = int(4 + sp * 12)
    acc = np.zeros(fr.shape, np.float32)
    for i in range(n):
        acc += np.roll(fr, i * step, axis)
    return (acc / n).astype(np.uint8)


# ------------------------------------------------------------------ timeline
roof = R.Roof()
RS = RoofShot(roof)
logo = Image.open(os.path.join(PH, 'TR-LOGO-copy-2-01-scaled.png')).convert('RGBA')
la = np.asarray(logo, np.float32)
lum = la[..., :3].mean(-1)
is_red = (la[..., 0] > 120) & (la[..., 1] < 90)
alpha = np.clip((255 - lum) / 200, 0, 1)
alpha[is_red] = 1
alpha *= la[..., 3] / 255
rgb = np.where(is_red[..., None], la[..., :3], 255)
logo_w = Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), 'RGBA')
logo_w = logo_w.resize((760, int(760 * logo_w.height / logo_w.width)), Image.LANCZOS)

T_END = 46.6
SHOTS = [
    # (t0, t1, kind, obj)
    (0.0, 4.0, 'photo', PhotoShot(7, 0.0, 4.2, (0.5, 0.22, 1.25, 0), (0.5, 0.62, 1.08, 0), seed=1)),
    (4.0, 9.6, 'roof_static', None),
    (9.6, 11.3, 'photo', PhotoShot(3, 9.4, 11.5, (0.55, 0.55, 1.05, 0), (0.45, 0.62, 1.22, 0), seed=2)),
    (11.3, 13.0, 'photo', PhotoShot(2, 11.1, 13.2, (0.5, 0.45, 1.25, -2), (0.5, 0.58, 1.08, 1), seed=3)),
    (13.0, 27.4, 'timelapse', None),
    (27.4, 28.6, 'photo', PhotoShot(4, 27.4, 28.6, (0.5, 0.5, 1.05, 0), (0.5, 0.5, 1.2, 2), seed=4)),
    (28.6, 29.8, 'photo', PhotoShot(21, 28.6, 29.8, (0.45, 0.5, 1.25, 0), (0.5, 0.45, 1.08, 0), seed=5)),
    (29.8, 31.0, 'photo', PhotoShot(13, 29.8, 31.0, (0.5, 0.6, 1.08, 0), (0.5, 0.55, 1.22, -1), seed=6)),
    (31.0, 32.2, 'photo', PhotoShot(26, 31.0, 32.2, (0.25, 0.5, 1.0, 0), (0.75, 0.5, 1.0, 0), seed=7)),
    (32.2, 33.4, 'photo', PhotoShot(16, 32.2, 33.4, (0.5, 0.6, 1.2, 0), (0.5, 0.5, 1.05, 0), seed=8)),
    (33.4, 35.2, 'photo', PhotoShot(29, 33.4, 35.2, (0.5, 0.45, 1.25, 0), (0.5, 0.55, 1.04, 0), seed=9)),
    (35.2, 36.4, 'photo', PhotoShot(17, 35.2, 36.4, (0.5, 0.6, 1.05, 0), (0.5, 0.5, 1.18, 0), seed=10)),
    (36.4, 37.6, 'photo', PhotoShot(19, 36.4, 37.6, (0.5, 0.45, 1.18, 0), (0.5, 0.55, 1.04, 0), seed=11)),
    (37.6, 39.4, 'photo', PhotoShot(20, 37.6, 39.4, (0.5, 0.6, 1.04, 0), (0.5, 0.42, 1.2, 0), seed=12)),
    (39.4, T_END, 'end', PhotoShot(32, 39.4, T_END, (0.3, 0.5, 1.0, 0), (0.7, 0.5, 1.0, 0), seed=13)),
]

STATS = [(33.4, 35.2, 90, '+', 'COMMERCIAL PROJECTS'), (35.2, 36.4, 100, '', 'RESIDENTIAL PROJECTS'),
         (36.4, 37.6, 30, '', 'SKILLED CREW MEMBERS'), (37.6, 39.4, 300, '', 'HAPPY CUSTOMERS')]

def base_frame(t):
    for t0, t1, kind, obj in SHOTS:
        if t0 <= t < t1:
            if kind == 'photo' or kind == 'end':
                im = obj.render(t)
                if kind == 'end':
                    im = im.filter(ImageFilter.GaussianBlur(10))
                    a = np.asarray(im, np.float32) * 0.38
                    return a.astype(np.uint8)
                return np.asarray(im)
            if kind == 'roof_static':
                return np.asarray(RS.static(t, t0, t1))
            if kind == 'timelapse':
                return np.asarray(RS.timelapse(t, t0, t1))
    return np.zeros((H, W, 3), np.uint8)

WHIPS = [(4.0, 0, 1), (9.6, 1, 1), (13.0, 0, 1)]   # (cut time, axis, dir)
WHIP_LEN = 0.30

def overlays(t):
    lay = text_layer()
    # drone HUD on the establishing shots
    if t < 9.6:
        hud(lay, t, ease(t / 0.6) * (1 - ease((t - 9.2) / 0.4)))
    caption(lay, ['EVERY ROOF', 'TELLS A STORY'], t, 0.7, 3.8, y=1180, size=92)
    caption(lay, ['Years of Calgary', 'hail, wind & snow'], t, 4.7, 7.6, y=1240, size=72, kicker='THE PROBLEM')
    caption(lay, ['Until it couldn\'t', 'take any more.'], t, 7.9, 9.5, y=1240, size=72)
    caption(lay, ['So our crew', 'went to work.'], t, 9.8, 12.9, y=1240, size=80, kicker='THRONE ROOFING CREW')
    caption(lay, ['TEAR-OFF'], t, 13.25, 17.7, y=1380, size=96, kicker='DAY 1')
    caption(lay, ['BASE SHEET'], t, 18.05, 22.5, y=1380, size=96, kicker='DAY 2')
    caption(lay, ['TORCH-ON CAP'], t, 22.85, 27.3, y=1380, size=96, kicker='DAY 3')
    caption(lay, ['SEALED TIGHT.'], t, 27.5, 30.9, y=1300, size=96)
    caption(lay, ['Every seam. Every vent.', 'Every flashing.'], t, 31.0, 33.35, y=1300, size=64)
    for t0, t1, n, suf, label in STATS:
        if t0 <= t < t1:
            c = int(round(n * ease_out((t - t0) / 0.6)))
            a = ease((t - t0) / 0.2) * (1 - ease((t - (t1 - 0.15)) / 0.15))
            draw_text(lay, f'{c}{suf}', 1130, 210, a, fnt='Inter-ExtraBold.otf', track=-4)
            draw_text(lay, label, 1370, 46, a, fnt='Inter-Bold.otf', track=6)
    if 33.4 <= t < 39.4:
        pill(lay, 'BUILT TO LAST', 1040, ease((t - 33.5) / 0.3) * (1 - ease((t - 39.2) / 0.2)))
    # end card
    if t >= 39.4:
        k = (t - 39.4)
        a = ease(k / 0.5)
        s = lerp(0.86, 1.0, ease_out(k / 0.9))
        lw = logo_w.resize((int(logo_w.width * s), int(logo_w.height * s)), Image.LANCZOS)
        la_ = lw.copy(); la_.putalpha(lw.getchannel('A').point(lambda v: int(v * a)))
        lay.alpha_composite(la_, (int((W - lw.width) / 2), int(560 - (lw.height - logo_w.height) / 2)))
        caption(lay, ['BUILT TO RULE.'], t, 40.6, T_END + 1, y=1130, size=92)
        a2 = ease((k - 1.6) / 0.5)
        draw_text(lay, 'Torch-On SBS  ·  TPO  ·  Metal  ·  Shingle', 1280, 38, a2, fnt='Inter-Medium.otf')
        draw_text(lay, 'Calgary  ·  Edmonton  ·  Saskatchewan', 1336, 38, a2, fnt='Inter-Medium.otf', fill=(220, 220, 220))
        a3 = ease((k - 2.4) / 0.5)
        pill(lay, 'GET A FREE QUOTE', 1450, a3, size=40)
        draw_text(lay, '(587) 701-1400', 1560, 64, a3, fnt='Inter-ExtraBold.otf')
        draw_text(lay, 'throneroofing.ca', 1650, 40, a3, fnt='Inter-Medium.otf', fill=(230, 230, 230))
        draw_text(lay, 'Licensed  ·  Insured  ·  WCB Compliant', 1720, 30, a3 * 0.8, fnt='Inter-Medium.otf', fill=(200, 200, 200))
    return lay

def frame(fi):
    t = fi / FPS
    img = None
    for tc, axis, dr in WHIPS:
        if tc - WHIP_LEN / 2 <= t < tc + WHIP_LEN / 2:
            k = (t - (tc - WHIP_LEN / 2)) / WHIP_LEN
            a = base_frame(tc - WHIP_LEN / 2 - 0.001 + (t - (tc - WHIP_LEN / 2)) * 0.5)
            b = base_frame(tc + 0.001 + (t - (tc - WHIP_LEN / 2)) * 0.5)
            img = whip(a, b, k, axis, dr)
            break
    if img is None:
        img = base_frame(t)
    img = grade(img, fi)
    # impact punch-in at the drop and at the reveal
    for tp in (27.4, 33.4):
        if tp <= t < tp + 0.25:
            z = 1 + 0.06 * (1 - (t - tp) / 0.25)
            im = Image.fromarray(img)
            cw, ch = int(W / z), int(H / z)
            img = np.asarray(im.crop(((W - cw) // 2, (H - ch) // 2, (W + cw) // 2, (H + ch) // 2)).resize((W, H), Image.BILINEAR))
    # white flash at the reveal, dip at end card
    if 33.4 <= t < 33.75:
        f = 1 - (t - 33.4) / 0.35
        img = np.clip(img.astype(np.float32) + 255 * f ** 2, 0, 255).astype(np.uint8)
    if 39.2 <= t < 39.6:
        f = 1 - abs(t - 39.4) / 0.2
        img = (img.astype(np.float32) * (1 - 0.9 * f)).astype(np.uint8)
    # fade in / out
    if t < 0.4:
        img = (img * ease(t / 0.4)).astype(np.uint8)
    if t > T_END - 0.6:
        img = (img * ease((T_END - t) / 0.6)).astype(np.uint8)
    lay = overlays(t)
    out = Image.fromarray(img).convert('RGBA')
    out.alpha_composite(lay)
    return np.asarray(out.convert('RGB'))


if __name__ == '__main__':
    if len(sys.argv) > 3 and sys.argv[3] == '--preview':
        for ts in sys.argv[4].split(','):
            Image.fromarray(frame(int(float(ts) * FPS))).save(os.path.join(os.path.dirname(OUT), f'prev_{ts}.jpg'), quality=88)
        sys.exit()
    nf = int(T_END * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17',
                          '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    stop = int(sys.argv[4]) if len(sys.argv) > 4 else nf
    for fi in range(start, stop):
        p.stdin.write(frame(fi).tobytes())
        if fi % 60 == 0:
            print(f'frame {fi}/{nf}', flush=True)
    p.stdin.close(); p.wait()
