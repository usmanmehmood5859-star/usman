import math, io, os, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

LAT, LON = 49.18185, -105.9526004
OUT = sys.argv[1]  # frames dir
os.makedirs(OUT, exist_ok=True)
CACHE = os.path.join(os.path.dirname(OUT), 'tiles'); os.makedirs(CACHE, exist_ok=True)
W, H = 720, 1280          # internal render size, upscaled later
FPS, DUR = 30, 3.4
Z0, Z1 = 3.6, 19.25
MAXL = 19
FB = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
FX = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
FM = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'

def world(z):
    n = 2 ** z
    x = (LON + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(LAT)) + 1 / math.cos(math.radians(LAT))) / math.pi) / 2 * n
    return x * 256, y * 256

def tile(z, x, y):
    n = 2 ** z
    if y < 0 or y >= n: return Image.new('RGB', (256, 256), (5, 5, 8))
    x %= n
    p = f'{CACHE}/{z}_{x}_{y}.jpg'
    if not os.path.exists(p):
        u = f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
        for _ in range(3):
            try:
                d = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'reel/1.0'}), timeout=30).read()
                open(p, 'wb').write(d); break
            except Exception as e:
                err = e
    try: return Image.open(p).convert('RGB')
    except Exception: return Image.new('RGB', (256, 256), (5, 5, 8))

R = int(math.ceil(math.hypot(W, H) * 1.45 / 2)) + 256   # half-extent needed at a level
mosaics = {}
def mosaic(L):
    if L in mosaics: return mosaics[L]
    cx, cy = world(L)
    x0, y0 = int((cx - R) // 256), int((cy - R) // 256)
    x1, y1 = int((cx + R) // 256), int((cy + R) // 256)
    coords = [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]
    with ThreadPoolExecutor(8) as ex:
        ims = list(ex.map(lambda c: tile(L, *c), coords))
    m = Image.new('RGB', ((x1 - x0 + 1) * 256, (y1 - y0 + 1) * 256))
    for (x, y), im in zip(coords, ims):
        m.paste(im, ((x - x0) * 256, (y - y0) * 256))
    mosaics[L] = (m, cx - x0 * 256, cy - y0 * 256)
    print('level', L, len(coords), 'tiles', flush=True)
    return mosaics[L]

def ease(t):  # slow start, fast middle, soft landing
    return t * t * t * (t * (6 * t - 15) + 10)

f_big = ImageFont.truetype(FB, 44); f_mid = ImageFont.truetype(FX, 26); f_mono = ImageFont.truetype(FM, 20)
N = int(FPS * DUR)
for i in range(N):
    t = i / (N - 1)
    Z = Z0 + (Z1 - Z0) * ease(t)
    ang = 32 * (1 - ease(min(1, t * 1.15)))
    L = max(2, min(MAXL, round(Z)))
    m, cx, cy = mosaic(L)
    s = 2 ** (L - Z)        # level-L pixels per output pixel
    side = int(math.hypot(W, H) * s) + 4
    crop = m.crop((int(cx - side / 2), int(cy - side / 2), int(cx - side / 2) + side, int(cy - side / 2) + side))
    crop = crop.rotate(ang, resample=Image.BICUBIC)
    scale = 1 / s
    big = crop.resize((int(side * scale), int(side * scale)), Image.LANCZOS)
    bx, by = (big.width - W) // 2, (big.height - H) // 2
    fr = big.crop((bx, by, bx + W, by + H))
    # atmosphere: haze + desaturation when high up, motion blur during fast part
    alt = max(0, min(1, (12 - Z) / 8))
    fr = ImageEnhance.Contrast(fr).enhance(1.12)
    fr = ImageEnhance.Color(fr).enhance(1.05 - 0.35 * alt)
    speed = 6 * t * t * (1 - t) * (1 - t) * 16
    if speed > 0.4:
        fr = fr.filter(ImageFilter.GaussianBlur(min(2.2, speed * 0.6)))
    haze = Image.new('RGB', (W, H), (190, 205, 225))
    fr = Image.blend(fr, haze, 0.25 * alt)
    # HUD (black / white / red)
    d = ImageDraw.Draw(fr, 'RGBA')
    red = (225, 25, 35, 255)
    cxp, cyp = W // 2, H // 2
    lock = t > 0.82
    r = int(70 - 30 * max(0, min(1, (t - 0.82) / 0.1))) if lock else 70
    blink = (i // 4) % 2 == 0
    if lock or blink:
        for a, b in [((-1, -1), (1, 0)), ((-1, -1), (0, 1)), ((1, -1), (-1, 0)), ((1, -1), (0, 1)),
                     ((-1, 1), (1, 0)), ((-1, 1), (0, -1)), ((1, 1), (-1, 0)), ((1, 1), (0, -1))]:
            x0, y0 = cxp + a[0] * r, cyp + a[1] * r
            d.line((x0, y0, x0 + b[0] * r * 0.45, y0 + b[1] * r * 0.45), fill=red, width=4)
    d.line((cxp - 12, cyp, cxp + 12, cyp), fill=red, width=2); d.line((cxp, cyp - 12, cxp, cyp + 12), fill=red, width=2)
    # top bar
    d.rectangle((0, 0, W, 64), fill=(0, 0, 0, 170))
    d.text((24, 18), 'SAT-LINK', font=f_mid, fill=(255, 255, 255, 255))
    d.ellipse((150, 26, 162, 38), fill=red if blink else (90, 0, 0, 255))
    d.text((176, 22), 'LIVE', font=f_mono, fill=red)
    d.text((W - 24, 22), f'ALT {int(20000 * 2 ** (-(Z - 4))) + 120:>6} M', font=f_mono, fill=(255, 255, 255, 230), anchor='ra')
    # bottom coordinate block
    d.rectangle((0, H - 210, W, H), fill=(0, 0, 0, 150))
    d.rectangle((24, H - 186, 30, H - 40), fill=red)
    d.text((44, H - 190), '49.1818° N   105.9526° W', font=f_mono, fill=(255, 255, 255, 235))
    d.text((44, H - 158), 'ROCKGLEN, SASKATCHEWAN', font=f_big, fill=(255, 255, 255, 255))
    status = 'TARGET LOCKED' if lock else 'ACQUIRING TARGET...'
    d.text((44, H - 98), status, font=f_mid, fill=red if (lock or blink) else (255, 255, 255, 200))
    d.text((44, H - 62), 'HOSPITAL SITE  •  26,500+ SQ FT', font=f_mono, fill=(255, 255, 255, 210))
    d.text((W - 12, 74), 'Imagery © Esri, Maxar, Earthstar Geographics', font=ImageFont.truetype(FM, 12), fill=(255, 255, 255, 150), anchor='ra')
    fr.save(f'{OUT}/f{i:04d}.png')
print('done', N)
