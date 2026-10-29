#!/usr/bin/env python3
"""Procedural audio generator for QuanTroIdle.

Standard library only. Writes 16-bit PCM mono WAV files into
<project>/assets/audio/. Deterministic (fixed random seed).

Run:  python tools/gen_audio.py
"""
import math
import random
import struct
import wave
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "audio"
TWO_PI = 2.0 * math.pi


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def db_to_lin(db):
    return 10.0 ** (db / 20.0)


def midi_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def normalize(buf, peak_db):
    peak = max(abs(x) for x in buf) or 1.0
    g = db_to_lin(peak_db) / peak
    return [x * g for x in buf]


def edge_fade(buf, sr, fade_in_s=0.003, fade_out_s=0.01):
    n = len(buf)
    fi = max(1, int(fade_in_s * sr))
    fo = max(1, int(fade_out_s * sr))
    for i in range(min(fi, n)):
        buf[i] *= 0.5 - 0.5 * math.cos(math.pi * i / fi)
    for i in range(min(fo, n)):
        buf[n - 1 - i] *= 0.5 - 0.5 * math.cos(math.pi * i / fo)
    return buf


def write_wav(name, buf, sr):
    path = OUT_DIR / name
    frames = bytearray()
    for x in buf:
        v = int(round(max(-1.0, min(1.0, x)) * 32767))
        frames += struct.pack("<h", v)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(bytes(frames))
    return path


def mix_into(buf, start, samples, gain=1.0, limit=None):
    """Add samples into buf at start. If limit is given, the event is forced
    to fade out completely before index `limit` (used for loop safety)."""
    end_cap = len(buf) if limit is None else limit
    avail = end_cap - start
    if avail <= 0:
        return
    n = len(samples)
    if n > avail:
        samples = samples[:avail]
        n = avail
        fl = min(n, 1500)
        for i in range(fl):
            k = n - 1 - i
            samples[k] *= 0.5 - 0.5 * math.cos(math.pi * i / fl)
    for i in range(n):
        buf[start + i] += samples[i] * gain


def onepole_lp(x, coeff):
    y, out = 0.0, []
    for v in x:
        y += coeff * (v - y)
        out.append(y)
    return out


# --------------------------------------------------------------------------
# Instruments (music, 22050 Hz)
# --------------------------------------------------------------------------
def pluck(freq, dur, sr, bright=1.0):
    """Plucked-zither / marimba-ish tone: additive harmonics whose upper
    partials decay faster. Soft 6 ms attack."""
    n = int((dur + 0.6) * sr)
    att = int(0.006 * sr)
    partials = [(1, 1.0, 3.2), (2, 0.42 * bright, 5.5), (3, 0.20 * bright, 8.0),
                (4, 0.16 * bright, 11.0), (5, 0.06 * bright, 14.0), (6, 0.04 * bright, 18.0)]
    partials = [p for p in partials if freq * p[0] < sr * 0.45]
    out = [0.0] * n
    note_off = int(dur * sr)
    for h, amp, decay in partials:
        w = TWO_PI * freq * h / sr
        ph = random.random() * 0.2
        for i in range(n):
            out[i] += amp * math.sin(w * i + ph) * math.exp(-decay * i / sr)
    for i in range(n):
        if i < att:
            out[i] *= i / att
        if i > note_off:  # damp after note length
            out[i] *= math.exp(-14.0 * (i - note_off) / sr)
    return out


def bass_note(freq, dur, sr):
    n = int((dur + 0.15) * sr)
    att = int(0.008 * sr)
    w = TWO_PI * freq / sr
    out = []
    off = int(dur * sr)
    for i in range(n):
        t = i / sr
        s = math.sin(w * i) + 0.25 * math.sin(2 * w * i) + 0.08 * math.sin(3 * w * i)
        env = math.exp(-2.2 * t)
        if i < att:
            env *= i / att
        if i > off:
            env *= math.exp(-30.0 * (i - off) / sr)
        out.append(s * env)
    return out


def pad_chord(freqs, dur, sr):
    n = int((dur + 0.35) * sr)
    att = int(0.18 * sr)
    rel_start = int(dur * sr)
    rel = n - rel_start
    out = [0.0] * n
    for f in freqs:
        for det in (-0.12, 0.12):  # gentle chorus via detune (Hz)
            w = TWO_PI * (f + det) / sr
            w2 = 2 * w
            for i in range(n):
                out[i] += math.sin(w * i) + 0.15 * math.sin(w2 * i)
    for i in range(n):
        if i < att:
            env = 0.5 - 0.5 * math.cos(math.pi * i / att)
        elif i >= rel_start:
            env = 0.5 + 0.5 * math.cos(math.pi * (i - rel_start) / rel)
        else:
            env = 1.0
        # slow tremolo for warmth
        out[i] *= env * (0.9 + 0.1 * math.sin(TWO_PI * 0.5 * i / sr))
    return out


def kick(sr):
    n = int(0.28 * sr)
    att = int(0.004 * sr)
    out, ph = [], 0.0
    for i in range(n):
        t = i / sr
        f = 48 + 90 * math.exp(-t * 35)
        ph += TWO_PI * f / sr
        env = math.exp(-t * 14)
        if i < att:
            env *= i / att
        out.append(math.sin(ph) * env)
    return out


def shaker(sr, length=0.06, decay=60.0):
    n = int(length * sr)
    prev, out = 0.0, []
    att = int(0.004 * sr)
    for i in range(n):
        r = random.uniform(-1, 1)
        hp = r - prev  # crude high-pass
        prev = r
        env = math.exp(-decay * i / sr)
        if i < att:
            env *= i / att
        out.append(hp * env)
    return onepole_lp(out, 0.55)


def snap(sr):
    """Soft rim/clap-like tick: band-limited noise + short body tone."""
    n = int(0.12 * sr)
    att = int(0.003 * sr)
    noise = shaker(sr, 0.12, 30.0)
    out = []
    for i in range(n):
        t = i / sr
        env = math.exp(-t * 40)
        if i < att:
            env *= i / att
        out.append(0.6 * noise[i] + 0.4 * math.sin(TWO_PI * 330 * t) * env)
    return out


# --------------------------------------------------------------------------
# Music loop
# --------------------------------------------------------------------------
def make_music():
    sr = 22050
    spb = 12000                    # samples per beat -> 110.25 BPM exactly
    spe = spb // 2                 # samples per eighth
    bars = 16
    total = bars * 4 * spb         # exact number of bars (768000 samples)
    limit = total - int(0.02 * sr)  # every event fully silent before loop end
    buf = [0.0] * total
    random.seed(20261028)

    # Chords: C, Am, F, G (pentatonic friendly voicings)
    chords = [
        (48, [60, 64, 67]),  # C
        (45, [57, 60, 64]),  # Am
        (41, [57, 60, 65]),  # F
        (43, [55, 59, 62]),  # G
    ]

    # Melody in C major pentatonic: (midi or None, length in eighths)
    C5, D5, E5, G5, A5, C6, D6, E6 = 72, 74, 76, 79, 81, 84, 86, 88
    R = None
    phrase_a = [
        [(E5, 2), (G5, 1), (A5, 1), (G5, 2), (E5, 2)],
        [(C6, 1), (A5, 1), (G5, 2), (E5, 2), (D5, 2)],
        [(C5, 2), (D5, 1), (E5, 1), (G5, 2), (A5, 1), (G5, 1)],
        [(E5, 2), (D5, 2), (D5, 1), (E5, 1), (R, 2)],
    ]
    phrase_b = [
        [(G5, 1), (A5, 1), (C6, 2), (A5, 1), (G5, 1), (E5, 2)],
        [(A5, 2), (G5, 1), (E5, 1), (D5, 2), (C5, 2)],
        [(D5, 1), (E5, 1), (G5, 1), (A5, 1), (C6, 2), (A5, 2)],
        [(G5, 2), (E5, 1), (D5, 1), (C5, 2), (R, 2)],
    ]
    phrase_c = [  # higher variation for second half
        [(C6, 1), (D6, 1), (E6, 2), (D6, 1), (C6, 1), (A5, 2)],
        [(C6, 2), (A5, 1), (G5, 1), (E5, 2), (G5, 2)],
        [(A5, 1), (C6, 1), (A5, 1), (G5, 1), (E5, 2), (D5, 2)],
        [(E5, 2), (G5, 1), (E5, 1), (D5, 2), (R, 2)],
    ]
    phrase_d = [
        [(G5, 1), (A5, 1), (C6, 2), (A5, 1), (G5, 1), (E5, 2)],
        [(A5, 2), (G5, 1), (E5, 1), (D5, 2), (C5, 2)],
        [(D5, 1), (E5, 1), (G5, 1), (A5, 1), (C6, 1), (A5, 1), (G5, 2)],
        [(E5, 1), (D5, 1), (C5, 2), (R, 4)],  # short final notes -> clean loop
    ]
    melody = phrase_a + phrase_b + phrase_c + phrase_d

    cache = {}

    def get_pluck(m, eighths):
        key = (m, eighths)
        if key not in cache:
            cache[key] = pluck(midi_hz(m), eighths * spe / sr * 0.95, sr)
        return cache[key]

    # Lead
    for bar, notes in enumerate(melody):
        pos = bar * 4 * spb
        for m, ln in notes:
            if m is not None:
                vel = 0.9 + 0.1 * random.random()
                mix_into(buf, pos, get_pluck(m, ln), 0.30 * vel, limit)
            pos += ln * spe

    # Sparkle echo of lead an octave up, quieter, in bars 9-12
    for bar in range(8, 12):
        pos = bar * 4 * spb
        for m, ln in melody[bar]:
            if m is not None and ln >= 2:
                mix_into(buf, pos + spe, pluck(midi_hz(m + 12), 0.15, sr, 0.5), 0.06, limit)
            pos += ln * spe

    # Bass + pads
    bass_cache = {}
    pad_cache = {}
    for bar in range(bars):
        root, triad = chords[bar % 4]
        start = bar * 4 * spb
        # bass pattern: root (beat1, q.), fifth (beat 2.5), root (beat 3), octave (beat 4)
        pattern = [(0, root, 3), (3, root + 7, 1), (4, root, 2), (6, root + 12, 1), (7, root + 7, 1)]
        for e, m, ln in pattern:
            k = (m, ln)
            if k not in bass_cache:
                bass_cache[k] = bass_note(midi_hz(m), ln * spe / sr * 0.9, sr)
            mix_into(buf, start + e * spe, bass_cache[k], 0.30, limit)
        k = tuple(triad)
        if k not in pad_cache:
            pad_cache[k] = pad_chord([midi_hz(x) for x in triad], 4 * spb / sr - 0.3, sr)
        mix_into(buf, start, pad_cache[k], 0.035, limit)

    # Percussion
    kk = kick(sr)
    sn = snap(sr)
    shakers = [shaker(sr) for _ in range(6)]
    for bar in range(bars):
        start = bar * 4 * spb
        for beat in range(4):
            b = start + beat * spb
            if beat in (0, 2):
                mix_into(buf, b, kk, 0.40, limit)
            if beat in (1, 3) and bar % 2 == 1 or beat == 3:
                mix_into(buf, b, sn, 0.07, limit)
        for e in range(8):
            g = 0.10 if e % 2 else 0.05
            mix_into(buf, start + e * spe, shakers[(bar * 8 + e) % 6], g, limit)

    # Gentle overall low-pass to take the edge off
    buf = onepole_lp(buf, 0.6)
    buf = normalize(buf, -6.0)
    # tiny boundary fades (signal is already silent here; safety only)
    edge_fade(buf, sr, 0.002, 0.005)
    return buf, sr


# --------------------------------------------------------------------------
# SFX (44100 Hz)
# --------------------------------------------------------------------------
SR = 44100


def tone(buf, start_s, freq, dur, amp, decay, harmonics=((1, 1.0),), att_s=0.004, vib=0.0):
    s0 = int(start_s * SR)
    n = int(dur * SR)
    att = max(1, int(att_s * SR))
    for i in range(n):
        idx = s0 + i
        if idx >= len(buf):
            break
        t = i / SR
        f = freq * (1 + vib * math.sin(TWO_PI * 5.5 * t) * min(1.0, t * 4))
        env = math.exp(-decay * t)
        if i < att:
            env *= i / att
        v = 0.0
        for h, a in harmonics:
            v += a * math.sin(TWO_PI * f * h * t)
        buf[idx] += amp * env * v


def sfx_coin():
    buf = [0.0] * int(0.25 * SR)
    bell = ((1, 1.0), (2, 0.3), (3, 0.12), (4.2, 0.05))
    tone(buf, 0.0, 987.77, 0.08, 0.6, 30, bell)      # B5
    tone(buf, 0.065, 1318.51, 0.185, 0.8, 14, bell)  # E6
    return edge_fade(normalize(buf, -3.0), SR, 0.002, 0.02)


def sfx_click():
    n = int(0.08 * SR)
    buf, ph = [], 0.0
    random.seed(7)
    att = int(0.002 * SR)
    for i in range(n):
        t = i / SR
        f = 700 + 900 * math.exp(-t * 80)
        ph += TWO_PI * f / SR
        env = math.exp(-t * 70)
        if i < att:
            env *= i / att
        noise = random.uniform(-1, 1) * math.exp(-t * 400) * 0.2
        buf.append((math.sin(ph) + noise) * env)
    buf = onepole_lp(buf, 0.5)
    return edge_fade(normalize(buf, -3.0), SR, 0.001, 0.01)


def sfx_purchase():
    buf = [0.0] * int(0.45 * SR)
    random.seed(11)
    bell = ((1, 1.0), (2, 0.35), (3, 0.15), (5, 0.05))
    notes = [1046.5, 1318.5, 1568.0, 2093.0]  # C6 E6 G6 C7
    for k, f in enumerate(notes):
        st = k * 0.055
        tone(buf, st, f, 0.45 - st, 0.5 if k < 3 else 0.6, 9 if k == 3 else 16, bell)
    # "cha" shimmer: filtered noise burst at start
    prev = 0.0
    for i in range(int(0.12 * SR)):
        t = i / SR
        r = random.uniform(-1, 1)
        hp = r - prev
        prev = r
        env = math.exp(-t * 35) * min(1.0, i / (0.003 * SR))
        buf[i] += 0.18 * hp * env
    # sparkle on the final note
    tone(buf, 0.2, 4186.0, 0.2, 0.08, 20)
    return edge_fade(normalize(buf, -3.0), SR, 0.002, 0.03)


def sfx_levelup():
    buf = [0.0] * int(1.4 * SR)
    brass = ((1, 1.0), (2, 0.5), (3, 0.3), (4, 0.15), (5, 0.08))
    seq = [(0.00, 783.99), (0.10, 1046.5), (0.20, 1318.5), (0.30, 1568.0)]  # G5 C6 E6 G6
    for st, f in seq:
        tone(buf, st, f, 0.16, 0.35, 12, brass, att_s=0.008)
    # held major chord C6-E6-G6-C7 with vibrato
    for f, a in ((1046.5, 0.3), (1318.5, 0.25), (1568.0, 0.25), (2093.0, 0.3)):
        tone(buf, 0.42, f, 0.98, a, 3.2, brass, att_s=0.012, vib=0.004)
    # sparkles
    random.seed(3)
    for k in range(8):
        st = 0.45 + k * 0.1
        f = random.choice([2637.0, 3136.0, 3520.0, 4186.0])
        tone(buf, st, f, 0.15, 0.06, 25)
    return edge_fade(normalize(buf, -3.0), SR, 0.002, 0.12)


def sfx_whoosh():
    n = int(0.3 * SR)
    random.seed(5)
    buf = []
    low = band = 0.0
    q = 0.6
    for i in range(n):
        x = i / n
        fc = 300 + 2700 * math.sin(math.pi * x * 0.5) ** 2  # sweep up
        f = 2 * math.sin(math.pi * fc / SR)
        r = random.uniform(-1, 1)
        low += f * band
        high = r - low - q * band
        band += f * high
        env = math.sin(math.pi * x) ** 1.5
        buf.append(band * env)
    return edge_fade(normalize(buf, -3.0), SR, 0.005, 0.02)


def sfx_pop():
    n = int(0.12 * SR)
    buf, ph = [], 0.0
    att = int(0.002 * SR)
    for i in range(n):
        t = i / SR
        f = 380 + 900 * (1 - math.exp(-t * 60))
        ph += TWO_PI * f / SR
        env = math.exp(-t * 45)
        if i < att:
            env *= i / att
        buf.append((math.sin(ph) + 0.2 * math.sin(2 * ph)) * env)
    return edge_fade(normalize(buf, -3.0), SR, 0.001, 0.015)


# ==========================================================================
# Extra content (v2): regional music loops + gacha / cooking SFX.
# These never touch the original outputs above.
# ==========================================================================

# ---- extra instruments (music, 22050 Hz) ---------------------------------
def tranh(freq, dur, sr, bend=0.0, bright=1.0):
    """Đàn tranh-like plucked zither: bright additive string with an optional
    slide into the note (bend < 0 = slide up from below) and gentle late
    vibrato ("rung"). Damped after the note length."""
    n = int((dur + 0.7) * sr)
    att = max(1, int(0.003 * sr))
    off = int(dur * sr)
    parts = [(1, 1.0, 2.0), (2, 0.6, 3.5), (3, 0.38, 5.0), (4, 0.22, 7.0),
             (5, 0.14, 9.5), (6, 0.09, 12.0), (7, 0.05, 15.0)]
    parts = [(h, a * (bright if h > 1 else 1.0), d) for h, a, d in parts
             if freq * h < sr * 0.45]
    k = TWO_PI * freq / sr
    base, ph = [], 0.0
    for i in range(n):
        t = i / sr
        r = (1.0 + bend * math.exp(-t * 16.0)
             + 0.004 * math.sin(TWO_PI * 5.0 * t) * min(1.0, max(0.0, t - 0.15) * 3.0))
        ph += k * r
        base.append(ph)
    out = [0.0] * n
    for h, a, d in parts:
        for i in range(n):
            out[i] += a * math.sin(h * base[i]) * math.exp(-d * i / sr)
    for i in range(n):
        if i < att:
            out[i] *= i / att
        if i > off:
            out[i] *= math.exp(-9.0 * (i - off) / sr)
    return out


def flute(freq, dur, sr, rng):
    """Soft sine flute (sáo-like): slow attack, delayed vibrato, a little breath."""
    n = int((dur + 0.25) * sr)
    att = max(1, int(0.09 * sr))
    off = int(dur * sr)
    rel = max(1, n - off)
    k = TWO_PI * freq / sr
    ph, lp, out = 0.0, 0.0, []
    for i in range(n):
        t = i / sr
        ph += k * (1.0 + 0.006 * math.sin(TWO_PI * 5.2 * t) * min(1.0, max(0.0, t - 0.15) * 2.5))
        s = math.sin(ph) + 0.18 * math.sin(2 * ph) + 0.05 * math.sin(3 * ph)
        lp += 0.08 * (rng.uniform(-1, 1) - lp)
        s += 0.35 * lp
        if i < att:
            env = 0.5 - 0.5 * math.cos(math.pi * i / att)
        else:
            env = 0.85 + 0.15 * math.exp(-t * 2.0)
        if i >= off:
            env *= 0.5 + 0.5 * math.cos(math.pi * (i - off) / rel)
        out.append(s * env)
    return out


def epiano(freqs, dur, sr):
    """Rhodes-ish FM electric piano chord."""
    n = int((dur + 0.3) * sr)
    att = max(1, int(0.003 * sr))
    off = int(dur * sr)
    out = [0.0] * n
    for f in freqs:
        wc = TWO_PI * f / sr
        tine = f * 7 < sr * 0.45
        for i in range(n):
            t = i / sr
            idx = 0.15 + 1.6 * math.exp(-t * 7.0)
            s = math.sin(wc * i + idx * math.sin(wc * i)) * math.exp(-t * 1.8)
            if tine:
                s += 0.12 * math.sin(7 * wc * i) * math.exp(-t * 25.0)
            out[i] += s
    for i in range(n):
        if i < att:
            out[i] *= i / att
        if i > off:
            out[i] *= math.exp(-18.0 * (i - off) / sr)
    return out


def musicbox(freq, sr, length=2.0):
    """Music-box / small bell: inharmonic tine partials."""
    n = int(length * sr)
    att = max(1, int(0.002 * sr))
    parts = [(1.0, 1.0, 2.2), (2.0, 0.18, 4.0), (2.756, 0.30, 5.5),
             (5.404, 0.12, 9.0), (8.933, 0.05, 14.0)]
    parts = [p for p in parts if freq * p[0] < sr * 0.45]
    out = [0.0] * n
    for h, a, d in parts:
        w = TWO_PI * freq * h / sr
        for i in range(n):
            out[i] += a * math.sin(w * i) * math.exp(-d * i / sr)
    fo = int(0.1 * sr)
    for i in range(n):
        if i < att:
            out[i] *= i / att
        if i >= n - fo:
            out[i] *= (n - i) / fo
    return out


def hihat(sr, rng, length=0.045, decay=110.0):
    n = int(length * sr)
    att = max(1, int(0.001 * sr))
    p1 = p2 = 0.0
    out = []
    for i in range(n):
        r = rng.uniform(-1, 1)
        d1 = r - p1
        p1 = r
        d2 = d1 - p2  # second difference -> bright
        p2 = d1
        env = math.exp(-decay * i / sr)
        if i < att:
            env *= i / att
        out.append(0.5 * d2 * env)
    fo = min(n, int(0.004 * sr))
    for i in range(fo):
        out[n - 1 - i] *= i / fo
    return out


def woodblock(sr, rng, freq=1000.0, length=0.08):
    """Mõ-like wooden tick."""
    n = int(length * sr)
    att = max(1, int(0.001 * sr))
    out = []
    for i in range(n):
        t = i / sr
        s = (math.sin(TWO_PI * freq * t) * math.exp(-t * 55)
             + 0.3 * math.sin(TWO_PI * freq * 2.3 * t) * math.exp(-t * 90)
             + 0.3 * rng.uniform(-1, 1) * math.exp(-t * 500))
        if i < att:
            s *= i / att
        out.append(s)
    fo = min(n, int(0.005 * sr))
    for i in range(fo):
        out[n - 1 - i] *= i / fo
    return out


def gong(freq, sr, rng, length=3.5):
    n = int(length * sr)
    att = max(1, int(0.006 * sr))
    parts = [(1.0, 1.0, 0.9), (1.48, 0.55, 1.3), (2.0, 0.35, 1.7),
             (2.62, 0.30, 2.2), (3.2, 0.18, 2.8), (4.15, 0.10, 3.6)]
    out = [0.0] * n
    for h, a, d in parts:
        w = TWO_PI * freq * h / sr
        shimmer = 0.2 if h == 2.0 else 0.0
        for i in range(n):
            t = i / sr
            out[i] += (a * math.sin(w * i * (1 + 0.004 * math.exp(-t * 3)))
                       * math.exp(-d * t) * (1 - shimmer + shimmer * math.sin(TWO_PI * 3.1 * t)))
    lp = 0.0
    for i in range(int(0.08 * sr)):
        lp += 0.2 * (rng.uniform(-1, 1) - lp)
        out[i] += 0.6 * lp * math.exp(-i / sr * 30)
    fo = int(0.3 * sr)
    for i in range(n):
        if i < att:
            out[i] *= i / att
        if i >= n - fo:
            out[i] *= 0.5 - 0.5 * math.cos(math.pi * (n - i) / fo)
    return out


def tom(sr, f0=95.0, length=0.35):
    n = int(length * sr)
    att = max(1, int(0.003 * sr))
    ph, out = 0.0, []
    for i in range(n):
        t = i / sr
        ph += TWO_PI * f0 * (1 + 0.6 * math.exp(-t * 25)) / sr
        env = math.exp(-t * 9)
        if i < att:
            env *= i / att
        out.append(math.sin(ph) * env)
    fo = int(0.02 * sr)
    for i in range(fo):
        out[n - 1 - i] *= i / fo
    return out


# ---- composition helpers --------------------------------------------------
def compose(seed, scale, center, chord_pcs, rhythms, form, end_rhythm, tonic_pc):
    """Deterministic pentatonic melody. `form` is a string of 4-bar phrase
    letters: an uppercase letter seen before repeats that phrase, a lowercase
    letter repeats its uppercase phrase with a new 4th bar. The final bar uses
    `end_rhythm` (which ends with a rest) and lands on the tonic.
    Rhythm items are (eighths, is_rest). Returns list of bars of (midi|None, eighths)."""
    rng = random.Random(seed)
    top = len(scale) - 1
    state = {"idx": center}

    def snap_to(idx, ok):
        for d in (0, -1, 1, -2, 2, -3, 3, -4, 4):
            j = idx + d
            if 0 <= j <= top and ok(scale[j] % 12):
                return j
        return idx

    def make_bar(bar_no, rh, final):
        pcs = chord_pcs[bar_no % len(chord_pcs)]
        last_k = max(k for k, (_, r) in enumerate(rh) if not r)
        notes = []
        for k, (ln, rest) in enumerate(rh):
            if rest:
                notes.append((None, ln))
                continue
            idx = state["idx"]
            step = rng.choice((-2, -1, -1, 0, 1, 1, 2))
            if idx > center + 3:
                step = -abs(step) or -1
            elif idx < center - 3:
                step = abs(step) or 1
            idx = max(0, min(top, idx + step))
            if final and k == last_k:
                idx = snap_to(center, lambda pc: pc == tonic_pc)
            elif k == 0 or k == last_k:
                idx = snap_to(idx, lambda pc: pc in pcs)
            state["idx"] = idx
            notes.append((scale[idx], ln))
        return notes

    phrases, melody = {}, []
    for p, letter in enumerate(form):
        base = letter.upper()
        bars = []
        for b in range(4):
            bar_no = p * 4 + b
            final = (p == len(form) - 1 and b == 3)
            if not final and base in phrases and (letter.isupper() or b < 3):
                bars.append(phrases[base][b])
                continue
            rh = end_rhythm if final else rng.choice(rhythms)
            bars.append(make_bar(bar_no, rh, final))
        if letter.isupper() and letter not in phrases:
            phrases[letter] = bars
        melody += bars
    return melody


def play_line(buf, melody, spe, sr, make, gain, limit, rng, cache, transpose=0,
              bars_only=None, vel_var=0.1):
    for bar, notes in enumerate(melody):
        pos = bar * 8 * spe
        for m, ln in notes:
            if m is not None and (bars_only is None or bar in bars_only):
                key = (m + transpose, ln)
                if key not in cache:
                    cache[key] = make(midi_hz(m + transpose), ln * spe / sr * 0.95)
                mix_into(buf, int(round(pos)), cache[key],
                         gain * (1.0 - vel_var * rng.random()), limit)
            pos += ln * spe


def finish_music(buf, sr, lp_coeff):
    buf = onepole_lp(buf, lp_coeff)
    buf = normalize(buf, -6.0)
    edge_fade(buf, sr, 0.002, 0.005)
    return buf, sr


# ---- regional loops -------------------------------------------------------
def make_music_hoi_an():
    """Hội An: lantern-lit riverside evening. ~92 BPM, D minor pentatonic,
    đàn tranh lead with slides, soft flute counter-line, light mõ/shaker."""
    sr = 22050
    spb = 14380                      # 92.0 BPM
    spe = spb // 2
    bars = 12
    total = bars * 4 * spb           # 690240 samples = 31.30 s
    limit = total - int(0.02 * sr)
    buf = [0.0] * total
    random.seed(9201)
    rng = random.Random(9202)

    scale = [62, 65, 67, 69, 72, 74, 77, 79, 81, 84]          # D F G A C ...
    chords = [(38, [57, 62, 65]), (34, [58, 62, 65]), (41, [57, 60, 65]), (36, [55, 60, 64])]
    pcs = [{2, 5, 9}, {10, 2, 5}, {5, 9, 0}, {0, 4, 7}]        # Dm Bb F C
    rhythms = [
        [(2, 0), (1, 0), (1, 0), (2, 0), (2, 0)],
        [(3, 0), (1, 0), (4, 0)],
        [(2, 0), (2, 0), (2, 0), (2, 0)],
        [(1, 0), (1, 0), (2, 0), (4, 0)],
        [(4, 0), (2, 0), (2, 0)],
        [(2, 0), (2, 1), (1, 0), (1, 0), (2, 0)],
    ]
    end = [(2, 0), (2, 0), (4, 1)]
    melody = compose(5011, scale, 5, pcs, rhythms, "ABa", end, tonic_pc=2)

    lead_cache = {}
    play_line(buf, melody, spe, sr,
              lambda f, d: tranh(f, d, sr, bend=-0.03 if d > 0.5 else 0.0),
              0.32, limit, rng, lead_cache)

    # rolled tranh arpeggio at each phrase start
    for bar in (0, 4, 8):
        _, triad = chords[bar % 4]
        for j, m in enumerate(triad + [triad[0] + 12]):
            mix_into(buf, bar * 4 * spb + int(j * 0.045 * sr),
                     tranh(midi_hz(m + 12), 0.6, sr, bright=0.7), 0.12, limit)

    # flute counter-line: half notes on chord tones, bars 4..10
    prev = 69
    fl_cache = {}
    for bar in range(4, 11):
        _, triad = chords[bar % 4]
        for half in range(2):
            cands = [m for m in range(62, 77) if m % 12 in {x % 12 for x in triad}]
            m = min(cands, key=lambda x: (abs(x - prev), x))
            if half == 1 and m == prev:
                m = min([c for c in cands if c != prev], key=lambda x: abs(x - prev))
            prev = m
            if m not in fl_cache:
                fl_cache[m] = flute(midi_hz(m), 2 * spb / sr * 0.92, sr, rng)
            mix_into(buf, bar * 4 * spb + half * 2 * spb, fl_cache[m], 0.13, limit)

    # bass + pad
    for bar in range(bars):
        root, triad = chords[bar % 4]
        st = bar * 4 * spb
        mix_into(buf, st, bass_note(midi_hz(root), 3 * spe / sr, sr), 0.26, limit)
        mix_into(buf, st + 4 * spe, bass_note(midi_hz(root + 7), 3 * spe / sr, sr), 0.20, limit)
        mix_into(buf, st, pad_chord([midi_hz(x) for x in triad], 4 * spb / sr - 0.3, sr), 0.03, limit)

    # light percussion
    kk = kick(sr)
    wb = [woodblock(sr, rng, 900.0), woodblock(sr, rng, 1200.0)]
    sh = [shaker(sr) for _ in range(4)]
    for bar in range(bars):
        st = bar * 4 * spb
        mix_into(buf, st, kk, 0.22, limit)
        mix_into(buf, st + spb, wb[0], 0.07, limit)
        mix_into(buf, st + 3 * spb, wb[1], 0.06, limit)
        for e in (1, 3, 5, 7):
            mix_into(buf, st + e * spe, sh[(bar + e) % 4], 0.05, limit)
    return finish_music(buf, sr, 0.55)


def make_music_sai_gon():
    """Sài Gòn: lively modern city. 120 BPM, G major pentatonic, bouncy bass,
    FM e-piano offbeat chords, snappy hats, marimba-ish lead."""
    sr = 22050
    spb = 11025                      # 120 BPM exactly
    spe = spb / 2.0
    bars = 16
    total = bars * 4 * spb           # 705600 samples = 32.00 s
    limit = total - int(0.02 * sr)
    buf = [0.0] * total
    random.seed(1201)
    rng = random.Random(1202)

    scale = [67, 69, 71, 74, 76, 79, 81, 83, 86, 88]          # G A B D E ...
    chords = [
        (43, [59, 62, 66, 69]),   # Gmaj9-ish
        (40, [59, 62, 64, 67]),   # Em7
        (36, [60, 64, 67, 71]),   # Cmaj7
        (38, [57, 62, 66, 69]),   # D
    ]
    pcs = [{7, 11, 2}, {4, 7, 11}, {0, 4, 7}, {2, 6, 9}]
    rhythms = [
        [(1, 0), (1, 0), (1, 1), (1, 0), (2, 0), (1, 0), (1, 0)],
        [(2, 0), (1, 0), (1, 0), (1, 1), (1, 0), (2, 0)],
        [(1, 0), (2, 0), (1, 0), (2, 0), (2, 0)],
        [(3, 0), (1, 0), (1, 0), (1, 0), (2, 0)],
        [(1, 0)] * 8,
        [(1, 1), (1, 0), (1, 0), (1, 0), (2, 0), (2, 0)],
    ]
    end = [(1, 0), (1, 0), (2, 0), (4, 1)]
    melody = compose(7123, scale, 3, pcs, rhythms, "ABAb", end, tonic_pc=7)
    play_line(buf, melody, spe, sr, lambda f, d: pluck(f, d, sr, 1.3),
              0.26, limit, rng, {})

    ep_cache, bass_cache = {}, {}
    for bar in range(bars):
        root, voicing = chords[bar % 4]
        st = bar * 4 * spb
        # e-piano: syncopated stabs
        for e, ln in ((0, 2.0), (3, 1.0), (6, 1.5)):
            k = (bar % 4, ln)
            if k not in ep_cache:
                ep_cache[k] = epiano([midi_hz(x) for x in voicing], ln * spe / sr * 0.8, sr)
            mix_into(buf, st + int(e * spe), ep_cache[k], 0.07, limit)
        # bouncy staccato bass with octave jumps
        for e, m in ((0, root), (2, root + 12), (3, root), (4, root + 7),
                     (6, root + 12), (7, root + 7)):
            if m not in bass_cache:
                bass_cache[m] = bass_note(midi_hz(m), 0.6 * spe / sr, sr)
            mix_into(buf, st + int(e * spe), bass_cache[m], 0.32, limit)

    kk = kick(sr)
    sn = snap(sr)
    hats = [hihat(sr, rng) for _ in range(6)]
    ohat = hihat(sr, rng, 0.18, 18.0)
    s16 = spb / 4.0
    for bar in range(bars):
        st = bar * 4 * spb
        mix_into(buf, st, kk, 0.45, limit)
        mix_into(buf, st + 2 * spb, kk, 0.45, limit)
        if bar % 2 == 1:
            mix_into(buf, st + int(3 * spe), kk, 0.28, limit)
        mix_into(buf, st + spb, sn, 0.16, limit)
        mix_into(buf, st + 3 * spb, sn, 0.16, limit)
        for e in range(8):
            if e == 7 and bar % 2 == 0:
                mix_into(buf, st + int(e * spe), ohat, 0.05, limit)
                continue
            mix_into(buf, st + int(e * spe), hats[(bar * 8 + e) % 6], 0.09 if e % 2 else 0.05, limit)
        if bar % 4 == 3:   # 16th hat fill on beat 4
            for s in (13, 15):
                mix_into(buf, st + int(s * s16), hats[s % 6], 0.06, limit)
    return finish_music(buf, sr, 0.8)


def make_music_da_lat():
    """Đà Lạt: cool misty highlands. ~96 BPM, F major pentatonic, music-box
    lead with soft echo, warm pads, minimal percussion."""
    sr = 22050
    spb = 13782                      # 95.99 BPM
    spe = spb // 2
    bars = 12
    total = bars * 4 * spb           # 661536 samples = 30.00 s
    limit = total - int(0.02 * sr)
    buf = [0.0] * total
    random.seed(9601)
    rng = random.Random(9602)

    scale = [72, 74, 77, 79, 81, 84, 86, 89, 91, 93]          # C D F G A ...
    chords = [
        (41, [53, 57, 60, 64]),   # Fmaj7
        (38, [53, 57, 60, 62]),   # Dm7
        (34, [53, 57, 58, 62]),   # Bbmaj7
        (36, [55, 60, 62, 67]),   # Csus2
    ]
    pcs = [{5, 9, 0, 4}, {2, 5, 9, 0}, {10, 2, 5, 9}, {0, 2, 7}]
    rhythms = [
        [(2, 0), (2, 0), (4, 0)],
        [(4, 0), (2, 0), (2, 0)],
        [(2, 0), (2, 1), (2, 0), (2, 0)],
        [(3, 0), (1, 0), (4, 0)],
        [(2, 0), (2, 0), (2, 0), (2, 0)],
    ]
    end = [(2, 0), (2, 0), (4, 1)]
    melody = compose(4407, scale, 4, pcs, rhythms, "ABa", end, tonic_pc=5)

    mb_cache = {}

    def mb(f, d):
        return musicbox(f, sr, 2.0)

    play_line(buf, melody, spe, sr, mb, 0.24, limit, rng, mb_cache)
    # airy echoes (dotted quarter, then a quieter repeat)
    play_line(buf, [[(None, 3)] + bar for bar in melody], spe, sr, mb, 0.07, limit, rng, mb_cache)
    play_line(buf, [[(None, 6)] + bar for bar in melody], spe, sr, mb, 0.03, limit, rng, mb_cache)

    # soft high arpeggio sparkles in the middle section
    for bar in range(4, 11):
        _, voicing = chords[bar % 4]
        for j, e in enumerate((1, 3, 5, 7)):
            m = voicing[j % len(voicing)] + 24
            if (m, 0) not in mb_cache:
                mb_cache[(m, 0)] = musicbox(midi_hz(m), sr, 1.2)
            mix_into(buf, bar * 4 * spb + e * spe, mb_cache[(m, 0)], 0.045, limit)

    for bar in range(bars):
        root, voicing = chords[bar % 4]
        st = bar * 4 * spb
        mix_into(buf, st, pad_chord([midi_hz(x) for x in voicing], 4 * spb / sr - 0.3, sr), 0.045, limit)
        mix_into(buf, st, bass_note(midi_hz(root), 4 * spb / sr * 0.9, sr), 0.22, limit)

    kk = kick(sr)
    sh = [shaker(sr, 0.08, 45.0) for _ in range(4)]
    for bar in range(bars):
        st = bar * 4 * spb
        if bar % 2 == 0:
            mix_into(buf, st, kk, 0.18, limit)
        mix_into(buf, st + 3 * spe, sh[bar % 4], 0.05, limit)
        mix_into(buf, st + 7 * spe, sh[(bar + 1) % 4], 0.05, limit)
    return finish_music(buf, sr, 0.6)


def make_music_hue():
    """Huế: royal / imperial elegance. 108 BPM, D major pentatonic, dignified
    plucked lead (with flute doubling in the middle), gong on the downbeat
    every 4 bars, soft drum."""
    sr = 22050
    spb = 12250                      # 108 BPM exactly
    spe = spb // 2
    bars = 16
    total = bars * 4 * spb           # 784000 samples = 35.56 s
    limit = total - int(0.02 * sr)
    buf = [0.0] * total
    random.seed(1001)
    rng = random.Random(1002)

    scale = [62, 64, 66, 69, 71, 74, 76, 78, 81, 83, 86]      # D E F# A B ...
    chords = [(38, [62, 66, 69]), (35, [59, 62, 66]), (43, [59, 62, 67]), (45, [61, 64, 69])]
    pcs = [{2, 6, 9}, {11, 2, 6}, {7, 11, 2}, {9, 1, 4}]        # D Bm G A
    rhythms = [
        [(3, 0), (1, 0), (2, 0), (2, 0)],
        [(4, 0), (2, 0), (2, 0)],
        [(2, 0), (2, 0), (3, 0), (1, 0)],
        [(2, 0), (1, 0), (1, 0), (4, 0)],
        [(6, 0), (2, 0)],
    ]
    end = [(2, 0), (2, 0), (4, 1)]
    melody = compose(3108, scale, 5, pcs, rhythms, "ABCa", end, tonic_pc=2)
    play_line(buf, melody, spe, sr, lambda f, d: pluck(f, d, sr, 0.9),
              0.28, limit, rng, {})
    play_line(buf, melody, spe, sr, lambda f, d: flute(f, d, sr, rng),
              0.10, limit, rng, {}, transpose=-12, bars_only=set(range(4, 12)), vel_var=0.0)

    for bar in range(bars):
        root, triad = chords[bar % 4]
        st = bar * 4 * spb
        mix_into(buf, st, pad_chord([midi_hz(x) for x in triad], 4 * spb / sr - 0.3, sr), 0.04, limit)
        mix_into(buf, st, bass_note(midi_hz(root), 4 * spe / sr * 0.9, sr), 0.28, limit)
        mix_into(buf, st + 4 * spe, bass_note(midi_hz(root + 7), 4 * spe / sr * 0.9, sr), 0.22, limit)

    g = gong(midi_hz(50), sr, rng)
    t_hi, t_lo = tom(sr, 110.0), tom(sr, 82.0)
    sh = [shaker(sr) for _ in range(4)]
    for bar in range(bars):
        st = bar * 4 * spb
        if bar % 4 == 0:
            mix_into(buf, st, g, 0.35, limit)
        mix_into(buf, st, t_lo, 0.35, limit)
        mix_into(buf, st + 2 * spb, t_hi, 0.22, limit)
        if bar % 4 == 3:
            mix_into(buf, st + 6 * spe, t_hi, 0.16, limit)
            mix_into(buf, st + 7 * spe, t_lo, 0.18, limit)
        for e in range(8):
            mix_into(buf, st + e * spe, sh[(bar + e) % 4], 0.03 if e % 2 else 0.015, limit)
    return finish_music(buf, sr, 0.6)


# ---- extra SFX (44100 Hz) -------------------------------------------------
def sfx_sizzle():
    rng = random.Random(41)
    n = int(0.8 * SR)
    crackle = [0.0] * n
    for _ in range(70):
        s = rng.randrange(n - 400)
        amp = rng.uniform(0.3, 1.0)
        ln = rng.randint(40, 200)
        prev = 0.0
        for i in range(ln):
            r = rng.uniform(-1, 1)
            crackle[s + i] += amp * (r - prev) * math.exp(-i / (ln * 0.3))
            prev = r
    buf = []
    prev = lp = 0.0
    fi, fo = int(0.12 * SR), int(0.3 * SR)
    for i in range(n):
        t = i / SR
        r = rng.uniform(-1, 1)
        hp = r - prev
        prev = r
        lp += 0.5 * (hp - lp)
        flutter = 0.7 + 0.3 * math.sin(TWO_PI * 7.3 * t) * math.sin(TWO_PI * 2.1 * t)
        if i < fi:
            env = 0.5 - 0.5 * math.cos(math.pi * i / fi)
        elif i >= n - fo:
            env = 0.5 - 0.5 * math.cos(math.pi * (n - 1 - i) / fo)
        else:
            env = 1.0
        buf.append(env * (0.35 * lp * flutter + 0.5 * crackle[i]))
    buf = onepole_lp(buf, 0.7)
    return edge_fade(normalize(buf, -6.0), SR, 0.002, 0.01)


def sfx_chest_open():
    rng = random.Random(77)
    n = int(0.9 * SR)
    buf = [0.0] * n
    # wooden creak: stick-slip pulses exciting woody resonances (0 - 0.38 s)
    t, creak_end = 0.02, 0.38
    while t < creak_end:
        x = (t - 0.02) / (creak_end - 0.02)
        rate = 55 + 110 * math.sin(math.pi * x) + rng.uniform(-12, 12)
        amp = math.sin(math.pi * x) ** 0.7 * rng.uniform(0.7, 1.0)
        s0 = int(t * SR)
        for i in range(int(0.012 * SR)):
            if s0 + i >= n:
                break
            tt = i / SR
            buf[s0 + i] += amp * (0.6 * math.sin(TWO_PI * 640 * tt) * math.exp(-tt * 260)
                                  + 0.4 * math.sin(TWO_PI * 1480 * tt) * math.exp(-tt * 420)
                                  + 0.25 * math.sin(TWO_PI * 260 * tt) * math.exp(-tt * 150))
        t += 1.0 / rate
    # lid thunk
    s0 = int(0.38 * SR)
    for i in range(int(0.15 * SR)):
        tt = i / SR
        buf[s0 + i] += 0.7 * (math.sin(TWO_PI * (110 + 60 * math.exp(-tt * 40)) * tt)
                              * math.exp(-tt * 22) * min(1.0, i / (0.002 * SR)))
    # magical sparkle burst
    bell = ((1, 1.0), (2, 0.25), (3, 0.08))
    tone(buf, 0.40, 1046.5, 0.5, 0.18, 6, bell, att_s=0.005)   # C6
    tone(buf, 0.42, 1318.5, 0.48, 0.16, 6, bell, att_s=0.005)  # E6
    tone(buf, 0.44, 1568.0, 0.46, 0.16, 6, bell, att_s=0.005)  # G6
    notes = [2093.0, 2349.3, 2637.0, 3136.0, 3520.0, 4186.0, 4698.6, 5274.0]
    for k in range(16):
        st = 0.40 + k * 0.022 + rng.uniform(0, 0.012)
        tone(buf, st, notes[min(len(notes) - 1, k // 2 + rng.randint(0, 1))],
             0.2, rng.uniform(0.05, 0.1), rng.uniform(18, 30), att_s=0.002)
    prev = 0.0
    s0 = int(0.40 * SR)
    for i in range(int(0.45 * SR)):
        r = rng.uniform(-1, 1)
        hp = r - prev
        prev = r
        tt = i / SR
        buf[s0 + i] += 0.08 * hp * math.exp(-tt * 9) * min(1.0, tt / 0.01)
    return edge_fade(normalize(buf, -3.0), SR, 0.002, 0.08)


def sfx_card_flip():
    rng = random.Random(23)
    n = int(0.25 * SR)
    buf = [0.0] * n
    low = band = 0.0
    q = 0.7
    wn = int(0.15 * SR)
    for i in range(wn):
        x = i / wn
        fc = 800 + 3200 * x * x
        f = 2 * math.sin(math.pi * fc / SR)
        r = rng.uniform(-1, 1)
        low += f * band
        high = r - low - q * band
        band += f * high
        buf[i] += 0.7 * band * math.sin(math.pi * x) ** 1.2
    s0 = int(0.145 * SR)
    att = max(1, int(0.0005 * SR))
    for i in range(n - s0):
        tt = i / SR
        v = (0.6 * rng.uniform(-1, 1) * math.exp(-tt * 400)
             + 0.5 * math.sin(TWO_PI * 2200 * tt) * math.exp(-tt * 120)
             + 0.5 * math.sin(TWO_PI * 300 * tt) * math.exp(-tt * 60))
        if i < att:
            v *= i / att
        buf[s0 + i] += v
    return edge_fade(normalize(buf, -3.0), SR, 0.003, 0.02)


def sfx_legendary():
    rng = random.Random(99)
    n = int(1.6 * SR)
    buf = [0.0] * n
    # rising noise swell
    prev = 0.0
    sw = int(0.42 * SR)
    for i in range(sw):
        r = rng.uniform(-1, 1)
        hp = r - prev
        prev = r
        x = i / sw
        buf[i] += 0.12 * hp * x ** 2 * (1 - 0.6 * max(0.0, x - 0.9) / 0.1)
    # warm low swell C3 + G3
    for f in (130.81, 196.0):
        for i in range(n):
            t = i / SR
            env = min(1.0, t / 0.4) * math.exp(-max(0.0, t - 0.4) * 2.5)
            buf[i] += 0.12 * env * math.sin(TWO_PI * f * t)
    bell = ((1, 1.0), (2, 0.35), (3, 0.15), (4.2, 0.06))
    brass = ((1, 1.0), (2, 0.5), (3, 0.3), (4, 0.15), (5, 0.08))
    arp = [523.25, 659.26, 783.99, 1046.5, 1318.5, 1568.0]   # C5 E5 G5 C6 E6 G6
    for k, f in enumerate(arp):
        tone(buf, k * 0.06, f, 0.3, 0.3, 10, bell, att_s=0.004)
    # triumphant held chord
    for f, a in ((523.25, 0.14), (659.26, 0.12), (783.99, 0.12)):
        tone(buf, 0.40, f, 1.2, a, 2.2, brass, att_s=0.015, vib=0.004)
    for f, a in ((1046.5, 0.28), (1318.5, 0.24), (1568.0, 0.24), (2093.0, 0.26), (2637.0, 0.12)):
        tone(buf, 0.40, f, 1.2, a, 2.6, bell, att_s=0.004, vib=0.003)
    # shimmering sparkles
    sp = [2637.0, 3136.0, 3520.0, 4186.0, 4698.6, 5274.0]
    for k in range(22):
        st = 0.42 + k * 0.045 + rng.uniform(0, 0.02)
        tone(buf, st, rng.choice(sp), 0.18, rng.uniform(0.04, 0.08) * (1 - k / 30), 22)
    return edge_fade(normalize(buf, -3.0), SR, 0.002, 0.25)


def sfx_spin_tick():
    rng = random.Random(5)
    n = int(0.05 * SR)
    att = max(1, int(0.0005 * SR))
    buf = []
    for i in range(n):
        t = i / SR
        v = (math.sin(TWO_PI * 1400 * t) * math.exp(-t * 140)
             + 0.4 * math.sin(TWO_PI * 2900 * t) * math.exp(-t * 250)
             + 0.35 * rng.uniform(-1, 1) * math.exp(-t * 600))
        if i < att:
            v *= i / att
        buf.append(v)
    buf = onepole_lp(buf, 0.6)
    return edge_fade(normalize(buf, -6.0), SR, 0.0005, 0.005)


ORIGINAL_FILES = ("music_loop.wav", "coin.wav", "click.wav", "purchase.wav",
                  "levelup.wav", "whoosh.wav", "pop.wav")
NEW_FILES = ("music_hoi_an.wav", "music_sai_gon.wav", "music_da_lat.wav", "music_hue.wav",
             "sizzle.wav", "chest_open.wav", "card_flip.wav", "legendary.wav", "spin_tick.wav")


# --------------------------------------------------------------------------
def verify(name):
    path = OUT_DIR / name
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        ch = w.getnchannels()
        sw = w.getsampwidth()
        data = w.readframes(n)
    vals = struct.unpack("<%dh" % n, data)
    peak = max(abs(v) for v in vals)
    peak_db = 20 * math.log10(peak / 32767) if peak else float("-inf")
    print("%-18s %6.3f s  %5d Hz  ch=%d  %d-bit  peak=%6d (%.2f dBFS)  first=%d last=%d  %d bytes"
          % (name, n / sr, sr, ch, sw * 8, peak, peak_db, vals[0], vals[-1], path.stat().st_size))


def main():
    """Default: write only the v2 files (originals are left untouched).
    Pass --all to also regenerate the original 7 files (same output as v1)."""
    import sys
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    regen_all = "--all" in sys.argv[1:]
    if regen_all:
        music, msr = make_music()
        write_wav("music_loop.wav", music, msr)
        write_wav("coin.wav", sfx_coin(), SR)
        write_wav("click.wav", sfx_click(), SR)
        write_wav("purchase.wav", sfx_purchase(), SR)
        write_wav("levelup.wav", sfx_levelup(), SR)
        write_wav("whoosh.wav", sfx_whoosh(), SR)
        write_wav("pop.wav", sfx_pop(), SR)
    for name, fn in (("music_hoi_an.wav", make_music_hoi_an),
                     ("music_sai_gon.wav", make_music_sai_gon),
                     ("music_da_lat.wav", make_music_da_lat),
                     ("music_hue.wav", make_music_hue)):
        buf, sr = fn()
        write_wav(name, buf, sr)
    write_wav("sizzle.wav", sfx_sizzle(), SR)
    write_wav("chest_open.wav", sfx_chest_open(), SR)
    write_wav("card_flip.wav", sfx_card_flip(), SR)
    write_wav("legendary.wav", sfx_legendary(), SR)
    write_wav("spin_tick.wav", sfx_spin_tick(), SR)
    print("Output:", OUT_DIR)
    for name in ORIGINAL_FILES + NEW_FILES:
        verify(name)


if __name__ == "__main__":
    main()
