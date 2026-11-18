"""2.5D drone-style camera moves from a single photo + AI depth map (Depth Anything V2)."""
import numpy as np, cv2, sys, os, math, subprocess
IMG = '/tmp/claude-0/-home-user-usman/17155274-85b6-5c26-9ac5-e4d3e2acc502/images'
HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30

def ease(t): return t * t * (3 - 2 * t)

# per photo: duration, view center (fraction of image), view height fraction,
# keyframes (start, end) for: zoom, dolly a, shift x/y (in output px, scaled by depth), roll (deg)
MOVES = {
    1: dict(dur=3.6, c=(0.58, 0.55), vh=1.0, zoom=(1.05, 1.18), a=(0.0, 0.55), sx=(70, -70), sy=(30, -10), roll=(2.5, -1.0)),
    3: dict(dur=3.6, c=(0.55, 0.55), vh=1.0, zoom=(1.06, 1.16), a=(0.0, 0.45), sx=(-40, 40), sy=(60, -40), roll=(-1.5, 1.0)),
    5: dict(dur=3.6, c=(0.5, 0.5), vh=1.0, zoom=(1.08, 1.30), a=(0.0, 0.35), sx=(0, 0), sy=(0, 0), roll=(-6, 4)),
    4: dict(dur=3.6, c=(0.5, 0.5), vh=1.0, zoom=(1.08, 1.14), a=(0.05, 0.40), sx=(80, -60), sy=(-20, 20), roll=(1.5, -1.5)),
    2: dict(dur=3.6, c=(0.5, 0.5), vh=1.0, zoom=(1.22, 1.06), a=(0.45, 0.0), sx=(-50, 50), sy=(-30, 20), roll=(-2, 1)),
}

def render(k, out):
    m = MOVES[k]
    img = cv2.imread(f'{IMG}/{k}.webp').astype(np.float32)
    d = np.load(f'{HERE}/d{k}.npy')
    d = cv2.bilateralFilter(d, 9, 0.1, 9)
    d = cv2.GaussianBlur(d, (0, 0), 2.0)
    ih, iw = d.shape
    s0 = (ih * m['vh']) / H                     # source px per output px
    if W * s0 > iw: s0 = iw / W                  # landscape: fit width-limited window
    c0 = np.array([iw * m['c'][0], ih * m['c'][1]])
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    qx, qy = xx - W / 2, yy - H / 2
    n = int(m['dur'] * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    L = lambda key, t: m[key][0] + (m[key][1] - m[key][0]) * t
    for i in range(n):
        t = ease(i / (n - 1))
        z, a, sx, sy, rl = L('zoom', t), L('a', t), L('sx', t), L('sy', t), math.radians(L('roll', t))
        # micro handheld drone wobble
        wob = i / FPS
        sx += 3 * math.sin(wob * 5.1) ; sy += 3 * math.sin(wob * 4.3 + 1)
        cr, sr = math.cos(rl), math.sin(rl)
        rx, ry = cr * qx - sr * qy, sr * qx + cr * qy
        dd = np.zeros_like(xx)
        for _ in range(3):   # fixed-point: depth at the source location
            f = 1.0 / (z * (1 + a * dd))
            mx = (c0[0] + s0 * (rx * f - sx * dd)).astype(np.float32)
            my = (c0[1] + s0 * (ry * f - sy * dd)).astype(np.float32)
            dd = cv2.remap(d, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        fr = cv2.remap(img, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        p.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
    print('rendered', k, n, 'frames')

if __name__ == '__main__':
    for k in map(int, sys.argv[2:]):
        render(k, f'{sys.argv[1]}/p{k}.mp4')
