"""Procedural top-down drone view of a commercial flat roof being re-roofed.

Builds a large canvas (parking lot, trees, parapets, rooftop units) and renders
any moment of a 3-day tear-off -> base sheet -> torch-on cap sheet job, with
moving sun shadows, cloud shadows, crew and torch glow.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CW, CH = 1800, 3200
RX0, RX1, RY0, RY1 = 170, 1630, 700, 2900          # roof field (inside parapet)
ROLL = 74                                           # roll width in px (~1 m)
NROLLS = (RY1 - RY0) // ROLL + 1
rng = np.random.default_rng(7)


def noise(h, w, scale, seed, octaves=4):
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        sh, sw = max(2, int(h / scale) + 2), max(2, int(w / scale) + 2)
        a = r.random((sh, sw)).astype(np.float32)
        im = Image.fromarray((a * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        out += amp * (np.asarray(im, np.float32) / 255 - 0.5)
        tot += amp
        amp *= 0.5
        scale /= 2.2
    return out / tot


def fine(h, w, seed, s=1.0):
    return np.random.default_rng(seed).normal(0, s, (h, w)).astype(np.float32)


def tint(base, field):
    return np.clip(np.array(base, np.float32)[None, None, :] * field[..., None], 0, 255)


# ---------------------------------------------------------------- materials
def build_layers():
    h, w = RY1 - RY0, RX1 - RX0
    lap = np.arange(h) % ROLL

    # OLD weathered modified-bitumen / gravel roof
    f = 1 + 0.10 * noise(h, w, 400, 1) + 0.05 * noise(h, w, 60, 2) + 0.06 * fine(h, w, 3)
    old = tint((132, 128, 121), f)
    pond = np.clip((noise(h, w, 260, 4) - 0.12) * 6, 0, 1)
    pond = np.asarray(Image.fromarray((pond * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32) / 255
    old *= (1 - 0.38 * pond)[..., None]
    old[(lap < 2)] *= 0.86
    # irregular tar patches / repairs (semi-transparent, soft)
    im = Image.fromarray(old.astype(np.uint8))
    pm = Image.new('L', (w, h), 0); d = ImageDraw.Draw(pm)
    r = np.random.default_rng(11)
    for _ in range(14):
        cx, cy = r.integers(60, w - 60), r.integers(60, h - 60)
        R = r.uniform(25, 70); n = 9
        pts = [(cx + R * r.uniform(.6, 1.3) * np.cos(a), cy + R * r.uniform(.5, 1.2) * np.sin(a)) for a in np.linspace(0, 6.28, n, endpoint=False)]
        d.polygon(pts, fill=int(r.integers(110, 190)))
    pm = np.asarray(pm.filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
    old = old * (1 - 0.55 * pm[..., None]) + 40 * 0.55 * pm[..., None]
    # hairline cracks around the worst ponding area (the zoom target)
    cm = Image.new('L', (w, h), 0); d = ImageDraw.Draw(cm)
    for _ in range(26):
        x, y = 810 + r.normal(0, 80), 800 + r.normal(0, 80)
        pts = [(x, y)]
        for _ in range(5):
            x += r.normal(0, 10); y += r.normal(0, 10); pts.append((x, y))
        d.line(pts, fill=150, width=1)
    cm = np.asarray(cm.filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
    old = old * (1 - 0.45 * cm[..., None])
    old = old.astype(np.uint8)
    old = old.astype(np.float32) * (1 + 0.05 * fine(h, w, 12))[..., None]

    # DECK: exposed insulation boards after tear-off
    f = 1 + 0.07 * noise(h, w, 200, 21) + 0.07 * fine(h, w, 22)
    deck = tint((152, 131, 101), f)
    bw, bh = 120, 240
    r = np.random.default_rng(23)
    for by in range(0, h, bw):
        off = 0 if (by // bw) % 2 == 0 else bh // 2
        for bx in range(-off, w, bh):
            deck[by:by + bw, max(bx, 0):bx + bh] *= r.uniform(0.9, 1.08)
    deck[(np.arange(h) % bw) < 2] *= 0.6
    xx = np.arange(w)[None, :]
    for by in range(0, h, bw):
        off = 0 if (by // bw) % 2 == 0 else bh // 2
        cols = ((xx + off) % bh) < 2
        deck[by:by + bw][np.broadcast_to(cols, (min(bw, h - by), w))] *= 0.6
    dirt = np.clip((noise(h, w, 120, 24) - 0.1) * 4, 0, 1)
    deck *= (1 - 0.25 * dirt)[..., None]

    # BASE: black SBS base sheet
    f = 1 + 0.06 * noise(h, w, 300, 31) + 0.07 * fine(h, w, 32)
    base = tint((40, 40, 43), f)
    base[(lap >= 2) & (lap < 6)] = base[(lap >= 2) & (lap < 6)] * 1.6 + 8   # torch bleed line
    r = np.random.default_rng(33)
    for k in range(NROLLS):
        y0 = k * ROLL
        for x in range(int(r.integers(200, 600)), w, 980):
            base[y0:y0 + ROLL, x:x + 3] = base[y0:y0 + ROLL, x:x + 3] * 1.5 + 6

    # CAP: light grey granulated torch-on cap sheet
    f = 1 + 0.03 * noise(h, w, 300, 41) + 0.11 * fine(h, w, 42)
    cap = tint((178, 184, 188), f)
    r = np.random.default_rng(43)
    for k in range(NROLLS):
        cap[k * ROLL:(k + 1) * ROLL] *= r.uniform(0.965, 1.03)
        y0 = k * ROLL
        for x in range(int(r.integers(100, 900)), w, 1000):
            cap[y0:y0 + ROLL, x:x + 4] *= 0.86
    cap[(lap < 5)] *= 0.84
    cap[(lap >= 5) & (lap < 7)] *= 1.06

    # parapet inner shadow baked into every layer (sun upper-left)
    sh = np.ones((h, w), np.float32)
    t = np.clip(np.arange(h) / 34, 0, 1)[:, None]
    l = np.clip(np.arange(w) / 34, 0, 1)[None, :]
    sh *= (0.62 + 0.38 * t) * (0.7 + 0.3 * l)
    out = []
    for L in (old, deck, base, cap):
        out.append(np.clip(L * sh[..., None], 0, 255).astype(np.uint8))
    return out


# ---------------------------------------------------------------- surroundings
def car(d, x, y, horiz, col, r):
    w, h = (92, 44) if horiz else (44, 92)
    d.rounded_rectangle([x, y, x + w, y + h], 12, fill=col)
    dark = (35, 40, 48)
    if horiz:
        d.rounded_rectangle([x + 22, y + 5, x + 36, y + h - 5], 4, fill=dark)
        d.rounded_rectangle([x + 66, y + 6, x + 76, y + h - 6], 3, fill=dark)
        hl = tuple(min(255, c + 35) for c in col)
        d.rounded_rectangle([x + 38, y + 8, x + 64, y + h - 8], 5, fill=hl)
    else:
        d.rounded_rectangle([x + 5, y + 22, x + w - 5, y + 36], 4, fill=dark)
        d.rounded_rectangle([x + 6, y + 66, x + w - 6, y + 76], 3, fill=dark)
        hl = tuple(min(255, c + 35) for c in col)
        d.rounded_rectangle([x + 8, y + 38, x + w - 8, y + 64], 5, fill=hl)


CAR_COLS = [(230, 232, 235), (25, 27, 30), (120, 124, 130), (150, 30, 30), (40, 60, 110),
            (200, 200, 205), (90, 95, 100), (240, 240, 240), (60, 64, 70)]


def build_ground():
    g = np.zeros((CH, CW, 3), np.float32)
    f = 1 + 0.08 * noise(CH, CW, 300, 51) + 0.07 * fine(CH, CW, 52)
    g[:] = tint((74, 76, 80), f)                                  # asphalt
    # grass strip on right and trees
    gx0 = 1680
    gf = 1 + 0.12 * noise(CH, CW - gx0, 120, 53) + 0.1 * fine(CH, CW - gx0, 54)
    g[:, gx0:] = tint((96, 108, 62), gf)
    # adjacent low roof on the left
    lf = 1 + 0.06 * noise(CH, 130, 90, 55) + 0.1 * fine(CH, 130, 56)
    g[640:, :130] = tint((150, 146, 138), lf[640:])
    im = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # sidewalk + curb
    d.rectangle([0, 560, CW, 640], fill=(168, 166, 160))
    # parking lines
    for x in range(40, 1640, 120):
        d.rectangle([x, 240, x + 5, 470], fill=(214, 182, 64))
    d.rectangle([40, 470, 1640, 474], fill=(214, 182, 64))
    # hatch zone
    for k in range(9):
        d.line([(1300 + k * 22, 250), (1300 + k * 22 + 60, 460)], fill=(210, 178, 60), width=6)
    # walkway to the building
    d.rectangle([700, 0, 760, 560], fill=(190, 190, 186))
    return im


def tree_layer():
    lay = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    sh = Image.new('L', (CW, CH), 0)
    d, ds = ImageDraw.Draw(lay), ImageDraw.Draw(sh)
    r = np.random.default_rng(61)
    cols = [(214, 120, 30), (232, 160, 40), (196, 86, 26), (226, 186, 70), (120, 130, 50)]
    for y in range(80, CH, 230):
        x = 1745 + r.normal(0, 25)
        R = r.uniform(70, 115)
        ds.ellipse([x - R + 26, y - R + 30, x + R + 26, y + R + 30], fill=150)
        base = cols[r.integers(0, len(cols))]
        for _ in range(60):
            a, rr = r.uniform(0, 6.28), R * np.sqrt(r.uniform(0, 1))
            cx, cy = x + rr * np.cos(a), y + rr * np.sin(a)
            s = r.uniform(14, 30)
            k = 0.75 + 0.45 * (1 - (cy - y + R) / (2 * R)) + r.normal(0, .06)
            c = tuple(int(np.clip(v * k, 0, 255)) for v in base) + (255,)
            d.ellipse([cx - s, cy - s, cx + s, cy + s], fill=c)
    return lay, sh


# ---------------------------------------------------------------- rooftop units
UNITS = []
def _units():
    r = np.random.default_rng(71)
    hv = [(330, 900, 150, 110), (1180, 960, 120, 160), (560, 1320, 170, 120),
          (1320, 1660, 150, 110), (420, 2060, 120, 160), (1000, 2280, 170, 120),
          (760, 1840, 140, 100)]
    for x, y, w, h in hv:
        UNITS.append(('hvac', x, y, w, h))
    for x, y in [(860, 1080), (300, 1600), (1240, 2060), (640, 2560), (1420, 2600)]:
        UNITS.append(('sky', x, y, 74, 74))
    for _ in range(16):
        UNITS.append(('vent', int(r.integers(RX0 + 60, RX1 - 60)), int(r.integers(RY0 + 60, RY1 - 60)), 22, 22))
_units()
GASLINE = [(RX0 + 30, 1250), (720, 1250), (720, 1700), (1500, 1700), (1500, 2400)]


def unit_layer():
    lay = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    sh = Image.new('L', (CW, CH), 0)
    d, ds = ImageDraw.Draw(lay), ImageDraw.Draw(sh)
    for kind, x, y, w, h in UNITS:
        if kind == 'hvac':
            ds.rectangle([x, y, x + w + 0, y + h], fill=200)
            d.rectangle([x, y, x + w, y + h], fill=(206, 207, 203, 255))
            d.rectangle([x, y, x + w, y + 6], fill=(232, 232, 228, 255))
            d.rectangle([x, y + h - 5, x + w, y + h], fill=(160, 160, 156, 255))
            n = 2 if w > h else 1
            for i in range(n):
                cx = x + w * (i + 1) / (n + 1); cy = y + h * 0.55
                R = min(w, h) * 0.26
                d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(60, 62, 66, 255))
                for k in range(0, 360, 30):
                    a = np.radians(k)
                    d.line([(cx, cy), (cx + R * np.cos(a), cy + R * np.sin(a))], fill=(120, 122, 126, 255), width=2)
                d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(30, 30, 30, 255))
        elif kind == 'sky':
            ds.rectangle([x, y, x + w, y + h], fill=150)
            d.rectangle([x, y, x + w, y + h], fill=(150, 150, 148, 255))
            d.rectangle([x + 8, y + 8, x + w - 8, y + h - 8], fill=(150, 176, 190, 255))
            d.polygon([(x + 8, y + 8), (x + w - 8, y + 8), (x + 8, y + h - 8)], fill=(185, 205, 215, 255))
        else:
            ds.ellipse([x - 3, y - 3, x + w + 3, y + h + 3], fill=170)
            d.ellipse([x, y, x + w, y + h], fill=(190, 192, 195, 255))
            d.ellipse([x + 6, y + 6, x + w - 6, y + h - 6], fill=(110, 112, 115, 255))
    d.line(GASLINE, fill=(222, 196, 88, 255), width=6)
    ds.line(GASLINE, fill=120, width=6)
    for (x0, y0), (x1, y1) in zip(GASLINE, GASLINE[1:]):
        n = int(np.hypot(x1 - x0, y1 - y0) // 140)
        for k in range(n + 1):
            px, py = x0 + (x1 - x0) * k / max(n, 1), y0 + (y1 - y0) * k / max(n, 1)
            d.rectangle([px - 7, py - 7, px + 7, py + 7], fill=(150, 40, 30, 255))
    return lay, sh


# ---------------------------------------------------------------- scene state
class Roof:
    def __init__(self):
        self.layers = build_layers()
        self.ground = np.asarray(build_ground(), np.uint8).copy()
        tl, tsh = tree_layer()
        ul, ush = unit_layer()
        tl = tl.filter(ImageFilter.GaussianBlur(1.6))
        self.tree_rgba = np.asarray(tl, np.float32) / 255
        self.tree_rgba[..., :3] *= (1 + 0.18 * fine(CH, CW, 99))[..., None]
        self.tree_rgba = np.clip(self.tree_rgba, 0, 1)
        ul = ul.filter(ImageFilter.GaussianBlur(0.9))
        self.unit_rgba = np.asarray(ul, np.float32) / 255
        g = 1 + 0.06 * noise(CH, CW, 40, 98) + 0.05 * fine(CH, CW, 97)
        self.unit_rgba[..., :3] = np.clip(self.unit_rgba[..., :3] * g[..., None], 0, 1)
        self.tree_sh = np.asarray(tsh.filter(ImageFilter.GaussianBlur(10)), np.float32) / 255
        self.unit_sh = np.asarray(ush.filter(ImageFilter.GaussianBlur(4)), np.float32) / 255
        cl = np.clip((noise(1600, 900, 300, 81, 3) + 0.05) * 3, 0, 1)
        self.cloud = np.asarray(Image.fromarray((cl * 255).astype(np.uint8)).resize((CW * 2, CH), Image.BICUBIC), np.float32) / 255
        # precompute a smaller set of parapet / building edge drawing
        self.parapet = self._parapet()

    def _parapet(self):
        lay = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        P = 16
        c = (204, 202, 196, 255)
        d.rectangle([RX0 - P, RY0 - P, RX1 + P, RY0], fill=c)
        d.rectangle([RX0 - P, RY0 - P, RX0, RY1 + P], fill=c)
        d.rectangle([RX1, RY0 - P, RX1 + P, RY1 + P], fill=c)
        d.rectangle([RX0 - P, RY1, RX1 + P, RY1 + P], fill=c)
        d.rectangle([RX0 - P, RY0 - P, RX1 + P, RY0 - P + 3], fill=(235, 234, 230, 255))
        # adjacent old roof section beyond the bottom parapet
        return np.asarray(lay, np.float32) / 255

    def frame(self, fronts, sun=(0.0, 1.0), cloud_t=0.0, workers=(), flames=(), extras=(), exposure=1.0, dump=0.0):
        """fronts: (tear, base, cap) in rolls (float); sun: (dx,dy) shadow dir unit*len"""
        img = self.ground.astype(np.float32)
        roof = self.layers[0].copy()
        w = RX1 - RX0
        for li, fr in ((1, fronts[0]), (2, fronts[1]), (3, fronts[2])):
            full = int(np.floor(fr))
            yend = min(full * ROLL, roof.shape[0])
            if yend > 0:
                roof[:yend] = self.layers[li][:yend]
            part = fr - full
            if part > 0 and full * ROLL < roof.shape[0]:
                y0, y1 = full * ROLL, min((full + 1) * ROLL, roof.shape[0])
                # alternate laying direction each roll
                xe = int(part * w)
                if full % 2 == 0:
                    roof[y0:y1, :xe] = self.layers[li][y0:y1, :xe]
                else:
                    roof[y0:y1, w - xe:] = self.layers[li][y0:y1, w - xe:]
        img[RY0:RY1, RX0:RX1] = roof
        # bottom adjacent old section
        img[RY1 + 16:, RX0:RX1] = self.layers[0][:CH - RY1 - 16] * 0.97

        # dumpster with debris that fills as tear-off proceeds
        im = Image.fromarray(img.astype(np.uint8)); d = ImageDraw.Draw(im)
        d.rectangle([180, 300, 470, 470], fill=(40, 70, 52))
        d.rectangle([194, 314, 456, 456], fill=(55, 52, 48))
        r = np.random.default_rng(91)
        for _ in range(int(160 * dump)):
            x, y = r.integers(196, 440), r.integers(316, 440)
            s = r.integers(6, 22)
            c = int(r.integers(70, 160))
            d.rectangle([x, y, x + s, y + s // 2 + 2], fill=(c, c - 8, c - 18))
        # parked cars (vary per day via extras seed)
        seed = extras[0] if extras else 0
        r = np.random.default_rng(1000 + seed)
        for x in range(520, 1640, 120):
            if r.random() < 0.72:
                car(d, x + 38, r.integers(290, 330), False, CAR_COLS[r.integers(0, len(CAR_COLS))], r)
        for x in range(100, 1600, 140):
            if r.random() < 0.5:
                car(d, x, 120 + r.integers(-6, 6), True, CAR_COLS[r.integers(0, len(CAR_COLS))], r)
        # material pallets & propane on roof
        for (px, py, kind) in (extras[1] if len(extras) > 1 else []):
            if kind == 'rolls':
                d.rectangle([px, py, px + 90, py + 90], fill=(150, 120, 80))
                for i in range(3):
                    for j in range(3):
                        cx, cy = px + 15 + 30 * i, py + 15 + 30 * j
                        d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=(30, 30, 32))
                        d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(170, 150, 110))
            elif kind == 'capr':
                d.rectangle([px, py, px + 90, py + 90], fill=(150, 120, 80))
                for i in range(3):
                    d.rectangle([px + 4, py + 6 + 28 * i, px + 86, py + 28 + 28 * i], fill=(190, 194, 196))
            elif kind == 'tank':
                d.ellipse([px, py, px + 30, py + 30], fill=(236, 236, 236))
                d.ellipse([px + 10, py + 10, px + 20, py + 20], fill=(150, 150, 150))
            elif kind == 'debris':
                for k in range(14):
                    x, y = px + r.integers(-40, 40), py + r.integers(-30, 30)
                    c = int(r.integers(60, 130))
                    d.rectangle([x, y, x + r.integers(10, 30), y + r.integers(6, 16)], fill=(c, c - 6, c - 12))
        img = np.asarray(im, np.float32)

        # composite units, parapet, trees
        for rgba in (self.parapet, self.unit_rgba):
            a = rgba[..., 3:4]
            img = img * (1 - a) + rgba[..., :3] * 255 * a

        # shadows (sun-dependent) -> multiplier
        dx, dy = int(sun[0] * 26), int(sun[1] * 26)
        m = np.ones((CH, CW), np.float32)
        sh = np.roll(np.roll(self.unit_sh, dy, 0), dx, 1)
        m *= 1 - 0.55 * sh * (1 - self.unit_rgba[..., 3])
        tsh = np.roll(np.roll(self.tree_sh, dy * 2, 0), dx * 2, 1)
        m *= 1 - 0.5 * tsh
        # parapet exterior shadow
        cl = self.cloud[:, int(cloud_t) % CW: int(cloud_t) % CW + CW]
        if cl.shape[1] < CW:
            cl = np.concatenate([cl, self.cloud[:, :CW - cl.shape[1]]], 1)
        m *= 1 - 0.28 * cl
        img *= m[..., None]

        a = self.tree_rgba[..., 3:4]
        img = img * (1 - a) + self.tree_rgba[..., :3] * 255 * a

        # crew
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
        for (x, y, vest, hat, ang) in workers:
            sx, sy = x + dx * 0.6, y + dy * 0.6
            d.ellipse([sx - 17, sy - 11, sx + 17, sy + 11], fill=(28, 28, 28))
            ca, sa = np.cos(ang), np.sin(ang)
            pts = [(x + ca * u - sa * v, y + sa * u + ca * v) for u, v in ((-18, -8), (18, -8), (18, 8), (-18, 8))]
            d.polygon(pts, fill=vest)
            d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=hat)
        img = np.asarray(im.filter(ImageFilter.GaussianBlur(0.9)), np.float32)
        # torch flames: additive warm glow
        for (x, y, s) in flames:
            x0, x1, y0, y1 = int(x - 40), int(x + 40), int(y - 40), int(y + 40)
            if x0 < 0 or y0 < 0 or x1 > CW or y1 > CH:
                continue
            yy, xx = np.mgrid[y0:y1, x0:x1]
            g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * (9 * s) ** 2))
            img[y0:y1, x0:x1] += g[..., None] * np.array([255, 150, 40]) * 0.9 * s
        return np.clip(img * exposure, 0, 255).astype(np.uint8)
