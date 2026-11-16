"""Sound design + score for the Throne Roofing reel (48 kHz stereo).

Usage: python3 make_audio.py <vo.wav> <out_mix.wav>
Everything except the voiceover is synthesised here: score (100 BPM, D minor),
drone rotor hum, wind, torch roar, whooshes, risers, impacts.
"""
import sys, subprocess, os
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly

SR = 48000
T_END = 46.6
N = int(SR * T_END)
rng = np.random.default_rng(3)
BEAT = 0.6
GRID0 = 13.0                       # a downbeat lands exactly on the timelapse drop

def bus():
    return np.zeros((N, 2), np.float32)

def lp(x, f, o=2):
    return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x, axis=0)

def hp(x, f, o=2):
    return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x, axis=0)

def bp(x, f1, f2, o=2):
    return sosfilt(butter(o, [f1, f2], 'band', fs=SR, output='sos'), x, axis=0)

def add(b, sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N:
        return
    if sig.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l, sig * r], 1) * 1.414
    n = min(len(sig), N - i)
    b[i:i + n] += sig[:n] * gain

def env(n, a, d_total, rel):
    e = np.ones(n, np.float32)
    na, nr = int(a * SR), int(rel * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e

def tt(dur):
    return np.arange(int(dur * SR)) / SR

def midi(m):
    return 440 * 2 ** ((m - 69) / 12)

def reverb(x, decay=1.8, mix=0.25, seed=5):
    """cheap stereo convolution reverb with an exponentially decaying noise IR"""
    r = np.random.default_rng(seed)
    n = int(decay * SR)
    t = np.arange(n) / SR
    ir = r.normal(0, 1, (n, 2)) * np.exp(-6.9 * t / decay)[:, None]
    ir = lp(ir, 6000)
    ir /= np.sqrt((ir ** 2).sum(0))
    from scipy.signal import fftconvolve
    wet = np.stack([fftconvolve(x[:, c], ir[:, c])[:len(x)] for c in range(2)], 1)
    return x * (1 - mix) + wet * mix * 3

# ------------------------------------------------------------------ score
CHORDS = [(50, [62, 65, 69]), (46, [62, 65, 70]), (41, [60, 65, 69]), (48, [60, 64, 67])]   # Dm Bb F C

def chord_at(t):
    return CHORDS[int(np.floor((t - GRID0) / 4.8)) % 4]

def pad():
    b = bus()
    seg = 4.8
    t0 = GRID0 - 3 * seg
    k = 0
    while t0 < T_END:
        root, notes = chord_at(t0 + 0.01)
        dur = seg + 0.8
        t = tt(dur)
        sig = np.zeros((len(t), 2))
        for m in notes + [notes[0] - 12]:
            for dt, pan in ((-0.09, -0.6), (0.0, 0.0), (0.11, 0.6)):
                f = midi(m) * 2 ** (dt / 12)
                ph = (f * t + rng.random()) % 1.0
                saw = 2 * ph - 1
                l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
                sig[:, 0] += saw * l; sig[:, 1] += saw * r
        cutoff = 900 if t0 < GRID0 else 1500
        sig = lp(sig, cutoff, 2)
        e = env(len(t), 1.2, dur, 1.2)
        # slow swell
        e *= 0.75 + 0.25 * np.sin(np.pi * t / dur)
        add(b, sig * e[:, None] * 0.05, max(t0, 0) if t0 >= 0 else 0)
        t0 += seg
    return b

def piano_note(m, dur=1.6, vel=1.0):
    t = tt(dur)
    f = midi(m)
    s = (np.sin(2 * np.pi * f * t) + 0.45 * np.sin(4 * np.pi * f * t) * np.exp(-t * 3)
         + 0.2 * np.sin(6 * np.pi * f * t) * np.exp(-t * 5) + 0.08 * np.sin(2 * np.pi * f * 4.01 * t) * np.exp(-t * 8))
    e = np.exp(-t * 2.2) * np.minimum(1, t / 0.004)
    return (s * e * vel).astype(np.float32)

def piano():
    b = bus()
    t = 0.4
    pattern = [0, 2, 1, 2, 0, 2, 1, 2]
    i = 0
    while t < T_END - 1:
        root, notes = chord_at(t + 0.01)
        if t < 9.6 or (27.4 <= t < 39.4) or t >= 39.4:
            if t < 39.4 or i % 2 == 0:
                m = notes[pattern[i % 8]] + 12
                vel = 0.55 if t < 13 else 0.35
                add(b, piano_note(m, 1.6, vel), t, 0.16, pan=0.25 * np.sin(i))
        t += BEAT if t < 13 else BEAT / 2
        i += 1
    return reverb(b, 2.4, 0.35)

def kick():
    t = tt(0.5)
    f = 45 + 95 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 7) + 0.3 * np.random.default_rng(1).normal(0, 1, len(t)) * np.exp(-t * 120)
    return np.tanh(s * 1.6).astype(np.float32)

def clap():
    t = tt(0.35)
    n = np.random.default_rng(2).normal(0, 1, len(t))
    e = np.exp(-t * 18) + 0.6 * np.exp(-((t - 0.012) % 0.011) * 300) * (t < 0.035)
    return bp(n * e, 900, 3500).astype(np.float32)

def hat(open_=False):
    t = tt(0.25 if open_ else 0.06)
    n = np.random.default_rng(4).normal(0, 1, len(t))
    return hp(n * np.exp(-t * (14 if open_ else 70)), 7000).astype(np.float32)

def drums():
    b, sc = bus(), np.ones(N, np.float32)
    k, c, h, ho = kick(), clap(), hat(), hat(True)
    t = GRID0
    beat = 0
    while t < 39.4 - 0.01:
        on = (t < 17.8 and beat % 2 == 0) or t >= 17.8
        if on:
            add(b, k, t, 0.55)
            i = int(t * SR); n = int(0.25 * SR)
            sc[i:i + n] = np.minimum(sc[i:i + n], 1 - 0.6 * np.exp(-np.arange(n) / SR * 14))
        if t >= 22.6 and beat % 2 == 1:
            add(b, c, t, 0.32)
        if t >= 17.8:
            add(b, h, t + BEAT / 2, 0.10, pan=0.3)
        if t >= 27.4:
            add(b, h, t + BEAT / 4, 0.05, pan=-0.3)
            add(b, h, t + 3 * BEAT / 4, 0.05, pan=-0.3)
        if t >= 33.4 and beat % 4 == 3:
            add(b, ho, t + BEAT / 2, 0.08)
        t += BEAT
        beat += 1
    # small fill into the reveal
    for j in range(4):
        add(b, c, 33.4 - BEAT + j * BEAT / 4, 0.18 + 0.05 * j)
    return reverb(b, 1.0, 0.12), sc

def bass():
    b = bus()
    t = GRID0
    while t < 39.4:
        root, _ = chord_at(t + 0.01)
        d = BEAT / 2
        tt_ = tt(d)
        f = midi(root - 12)
        s = np.sin(2 * np.pi * f * tt_) + 0.25 * np.sin(4 * np.pi * f * tt_)
        e = np.minimum(1, tt_ / 0.01) * np.exp(-tt_ * 3)
        add(b, (s * e).astype(np.float32), t, 0.22 if t >= 17.8 else 0.12)
        t += d
    # long sub under end card
    tt_ = tt(6.5)
    add(b, (np.sin(2 * np.pi * midi(38) * tt_) * np.exp(-tt_ * 0.6)).astype(np.float32), 39.4, 0.25)
    return lp(b, 400)

# ------------------------------------------------------------------ fx
def impact(size=1.0, dur=3.0):
    t = tt(dur)
    f = 32 + 60 * np.exp(-t * 10)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    n = rng.normal(0, 1, len(t))
    crack = lp(n * np.exp(-t * 9), 2500)
    s = np.tanh((boom * 1.2 + crack * 0.6) * 1.4) * size
    st = np.stack([s, s], 1)
    return reverb(st.astype(np.float32), 2.8, 0.35, seed=9)

def whoosh(dur=0.7, f0=300, f1=4000, rev=False):
    t = tt(dur)
    n = rng.normal(0, 1, (len(t), 2))
    out = np.zeros_like(n)
    blocks = 40
    L = len(t) // blocks
    for i in range(blocks):
        u = i / blocks
        fc = f0 * (f1 / f0) ** (u if not rev else 1 - u)
        seg = bp(n[max(0, i * L - 2000): (i + 1) * L], max(60, fc * 0.6), min(20000, fc * 1.6))
        out[i * L:(i + 1) * L] = seg[-L:]
    e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return (out * e[:, None]).astype(np.float32)

def riser(dur):
    t = tt(dur)
    n = rng.normal(0, 1, (len(t), 2))
    s = hp(n, 2500) * ((t / dur) ** 2.5)[:, None]
    tone = np.sin(2 * np.pi * np.cumsum(200 * 2 ** (3 * t / dur)) / SR) * (t / dur) ** 3 * 0.3
    return lp(s * 0.6 + tone[:, None], 9000).astype(np.float32)

def drone_hum(dur, base=205):
    t = tt(dur)
    f = base * (1 + 0.012 * np.sin(2 * np.pi * 0.37 * t) + 0.006 * rng.normal(0, 1, len(t)).cumsum() / np.sqrt(len(t)))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum(a * np.sin(k * ph) for k, a in ((1, 1), (2, .55), (3, .35), (4, .22), (6, .1), (8, .06)))
    # four rotors slightly detuned
    for d in (1.013, 0.991, 1.021):
        ph2 = 2 * np.pi * np.cumsum(f * d) / SR
        s += 0.6 * (np.sin(ph2) + 0.4 * np.sin(2 * ph2))
    air = lp(hp(rng.normal(0, 1, len(t)), 300), 3000) * 0.9
    s = s / 4 + air * 0.5
    st = np.stack([s, np.roll(s, 40)], 1)
    return lp(st, 4500).astype(np.float32)

def wind(dur):
    t = tt(dur)
    n = rng.normal(0, 1, (len(t), 2))
    s = lp(n, 500) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * t[:, None] + np.array([0, 1.3])[None, :]))
    return s.astype(np.float32)

def torch(dur):
    t = tt(dur)
    n = rng.normal(0, 1, (len(t), 2))
    roar = lp(n, 700, 3)
    turb = 1 + 0.35 * lp(rng.normal(0, 1, len(t)), 12)[:, None] * 6
    hiss = hp(n, 3000) * 0.08
    crack = (rng.random((len(t), 1)) > 0.9996) * rng.normal(0, 1, (len(t), 1)) * 3
    s = roar * turb * 2.2 + hiss + lp(crack, 4000)
    e = np.minimum(1, t / 0.15) * np.minimum(1, (dur - t) / 0.3)
    return (s * e[:, None]).astype(np.float32)

def scrape(dur):
    t = tt(dur)
    n = rng.normal(0, 1, (len(t), 2))
    am = (np.sin(2 * np.pi * 1.7 * t) > 0.3).astype(float)
    am = lp(am, 30)
    return (bp(n, 600, 2400) * am[:, None]).astype(np.float32)

def click():
    t = tt(0.05)
    return (np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 150)).astype(np.float32)

def shimmer(dur=3.0):
    t = tt(dur)
    s = sum(np.sin(2 * np.pi * midi(m) * t) * np.exp(-t * 1.2) for m in (74, 81, 86, 93))
    return reverb(np.stack([s, s], 1).astype(np.float32) * 0.25, 3.0, 0.5)

# ------------------------------------------------------------------ voice
def load_vo(path):
    tmp = path + '.48k.wav'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', path, '-ac', '1', '-ar', str(SR),
                    '-af', 'highpass=f=85,lowpass=f=12500,equalizer=f=180:t=q:w=1:g=2,equalizer=f=3200:t=q:w=1.2:g=2.5,'
                           'acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=3', tmp], check=True)
    import wave
    w = wave.open(tmp)
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return a

# VO phrase windows in the generated file (from silence detection) -> placement on the timeline
VO_SEGS = [((0.45, 2.25), 0.8), ((3.10, 5.95), 4.6), ((6.95, 8.70), 7.9), ((9.55, 12.36), 10.0),
           ((12.85, 13.78), 13.4), ((14.28, 15.45), 18.2), ((15.93, 17.06), 23.0), ((17.62, 18.92), 28.4),
           ((19.45, 20.90), 40.7)]

def main(vo_path, out):
    music, fx, vo = bus(), bus(), bus()
    music += pad()
    music += piano()
    d, sc = drums()
    music += d
    music += bass()
    music *= sc[:, None] ** 0.5

    # risers / impacts / whooshes
    add(fx, riser(2.4), 13.0 - 2.4, 0.11)
    add(fx, riser(1.8), 27.4 - 1.8, 0.08)
    add(fx, riser(2.2), 33.4 - 2.2, 0.13)
    add(fx, impact(0.6), 13.0, 0.5)
    add(fx, impact(0.8), 27.4, 0.5)
    add(fx, impact(1.0), 33.4, 0.7)
    add(fx, impact(1.0, 4.5), 39.4, 0.7)
    add(fx, shimmer(), 40.6, 0.5)
    for tc in (4.0, 9.6, 13.0):
        add(fx, whoosh(0.8, 250, 5000), tc - 0.45, 0.35)
    for tc in (11.3, 28.6, 29.8, 31.0, 32.2, 35.2, 36.4, 37.6):
        add(fx, whoosh(0.35, 800, 6000), tc - 0.2, 0.12)
    for t0, *_ in [(33.4,), (35.2,), (36.4,), (37.6,)]:
        for j in range(6):
            add(fx, click(), t0 + j * 0.1, 0.05)

    # ambience beds
    hum = drone_hum(13.2)
    e = np.ones(len(hum)); e[:int(1.5 * SR)] = np.linspace(0, 1, int(1.5 * SR))
    e[int(9.3 * SR):] *= np.linspace(1, 0.35, len(e) - int(9.3 * SR))
    add(fx, hum * e[:, None], 0.0, 0.10)
    add(fx, drone_hum(14.4, 198) * 0.5, 13.0, 0.05)
    w = wind(13.4)
    add(fx, w, 0.0, 0.10)
    add(fx, wind(6.0), 33.4, 0.06)
    add(fx, torch(1.9), 11.2, 0.20)
    add(fx, torch(1.3), 27.3, 0.18)
    add(fx, torch(9.6) * 0.5, 17.8, 0.06)
    add(fx, scrape(4.6), 13.1, 0.035)

    # voice
    a = load_vo(vo_path)
    vo_env = np.zeros(N, np.float32)
    for (s0, s1), tpos in VO_SEGS:
        seg = a[int(s0 * SR):int(s1 * SR)].copy()
        f = int(0.02 * SR)
        seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
        add(vo, seg, tpos, 1.0)
        i = int(tpos * SR)
        vo_env[max(0, i - int(0.15 * SR)): i + len(seg) + int(0.25 * SR)] = 1
    vo = reverb(vo, 0.9, 0.06, seed=11)
    # smooth ducking envelope (-7 dB under voice)
    k = int(0.12 * SR)
    sm = np.convolve(vo_env, np.ones(k) / k, 'same')
    duck = 1 - 0.55 * sm
    music *= duck[:, None]
    fx *= (1 - 0.3 * sm)[:, None]

    mix = music * 0.9 + fx + vo * 1.25
    # fades
    fo = int(0.8 * SR)
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    mix /= np.max(np.abs(mix)) + 1e-9
    mix *= 0.89
    raw = out + '.raw.wav'
    import wave
    with wave.open(raw, 'wb') as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
        wv.writeframes((mix * 32767).astype(np.int16).tobytes())
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af',
                    'loudnorm=I=-14:TP=-1.0:LRA=9,alimiter=limit=0.85:level=disabled', '-ar', str(SR), out], check=True)
    os.remove(raw)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
