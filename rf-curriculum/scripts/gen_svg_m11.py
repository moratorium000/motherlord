#!/usr/bin/env python3
"""
M11 (트랜시버 아키텍처) 손그림 SVG 도해 생성기
==============================================

규약: SVG 안에 한글을 넣지 않는다. 한글 설명은 마크다운 캡션에 쓴다.

    python3 scripts/gen_svg_m11.py
"""

from pathlib import Path

INK = "#1a1a1a"
ACCENT = "#c0392b"
BLUE = "#0072B2"
GREEN = "#009E73"
AMBER = "#E69F00"
PINK = "#CC79A7"
PANEL = "#F4F7FA"
BG = "#ffffff"
FONT = "font-family='DejaVu Sans, Helvetica, Arial, sans-serif'"

OUT = Path(__file__).resolve().parent.parent / "assets"


def doc(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" role="img" aria-label="{title}">\n'
            f'  <title>{title}</title>\n'
            f'  <rect width="{w}" height="{h}" fill="{BG}"/>\n{body}\n</svg>\n')


def L(x1, y1, x2, y2, s=INK, w=2, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{s}" '
            f'stroke-width="{w}" stroke-linecap="round"{d}/>')


def R(x, y, w, h, fill="none", s=INK, sw=2, rx=0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{s}" stroke-width="{sw}"{d}/>')


def C(cx, cy, r, fill="none", s=INK, sw=2):
    return (f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" '
            f'stroke="{s}" stroke-width="{sw}"/>')


def P(d, s=INK, sw=2, fill="none", dash=None, marker=None):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    mk = f' marker-end="url(#{marker})"' if marker else ""
    return (f'  <path d="{d}" fill="{fill}" stroke="{s}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round"{da}{mk}/>')


def T(x, y, s, size=11, anchor="middle", fill=INK, weight="normal"):
    return (f'  <text x="{x}" y="{y}" {FONT} font-size="{size}" '
            f'text-anchor="{anchor}" fill="{fill}" font-weight="{weight}">'
            f'{s}</text>')


def defs():
    out = ['  <defs>']
    for name, col in (("ar", ACCENT), ("ab", BLUE), ("ag", GREEN),
                      ("ak", INK), ("ap", PINK)):
        out.append(
            f'    <marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{col}"/></marker>')
    out.append('  </defs>')
    return "\n".join(out)


# ── 블록 부품들 ─────────────────────────────────────────────────
def ant(x, y):
    """안테나 기호. (x, y) 는 급전점."""
    return [L(x, y, x, y - 22),
            L(x, y - 22, x - 13, y - 36), L(x, y - 22, x + 13, y - 36)]


def blk(x, y, w, h, label, sub=None, fill=PANEL, col=INK):
    out = [R(x, y, w, h, fill=fill, s=col, sw=1.8, rx=5)]
    if sub:
        out += [T(x + w / 2, y + h / 2 - 2, label, 9.6, weight="bold"),
                T(x + w / 2, y + h / 2 + 12, sub, 8.4, fill="#666")]
    else:
        out += [T(x + w / 2, y + h / 2 + 4, label, 9.6, weight="bold")]
    return out


def mix(cx, cy, r=15):
    d = r * 0.62
    return [C(cx, cy, r), L(cx - d, cy - d, cx + d, cy + d),
            L(cx - d, cy + d, cx + d, cy - d)]


def lo(cx, cy, label="LO", side="below"):
    out = [C(cx, cy, 14),
           P(f"M {cx-7} {cy} q 3.5 -6 7 0 q 3.5 6 7 0", sw=1.5)]
    # side 가 숫자면 그만큼 아래에 라벨을 둔다 (두 믹서 사이에 놓일 때).
    dy = 30 if side == "below" else float(side)
    out += [T(cx, cy + dy, label, 9.4, fill=AMBER, weight="bold")]
    return out


def adc(x, y, w=54, h=42, label="ADC"):
    return [P(f"M {x} {y} L {x+w-14} {y} L {x+w} {y+h/2} L {x+w-14} {y+h} "
              f"L {x} {y+h} Z", fill="#EFF6EF", s=GREEN, sw=1.8),
            T(x + w / 2 - 4, y + h / 2 + 4, label, 9.6, fill=GREEN,
              weight="bold")]


# ═══════════════════════════════ M11-1: 수신 아키텍처 4종
def architectures():
    W, H = 1160, 830
    b = [defs(), T(W / 2, 30, "Four receiver architectures, same drawing style",
                   14, weight="bold")]

    rows = [
        ("(a) Dual-conversion superheterodyne", 74),
        ("(b) Zero-IF (direct conversion)", 288),
        ("(c) Low-IF", 486),
        ("(d) Direct RF sampling", 660),
    ]
    for name, y in rows:
        b += [T(46, y, name, 12, anchor="start", weight="bold")]

    # ── (a) 이중변환 슈퍼헤테로다인 ───────────────────────────
    y = rows[0][1] + 66
    x = 60
    b += ant(x, y) + [L(x, y, x + 22, y)]
    b += blk(x + 22, y - 21, 60, 42, "RF", "BPF")
    b += [L(x + 82, y, x + 104, y)]
    b += blk(x + 104, y - 21, 52, 42, "LNA")
    b += [L(x + 156, y, x + 178, y)]
    b += blk(x + 178, y - 21, 66, 42, "image", "filter")
    b += [L(x + 244, y, x + 268, y)]
    b += mix(x + 285, y) + lo(x + 285, y + 62, "LO1  (tunes)")
    b += [L(x + 285, y + 15, x + 285, y + 48, s=AMBER)]
    b += [L(x + 300, y, x + 324, y)]
    b += blk(x + 324, y - 21, 66, 42, "IF1", "SAW")
    b += [L(x + 390, y, x + 412, y)]
    b += blk(x + 412, y - 21, 52, 42, "IF amp")
    b += [L(x + 464, y, x + 488, y)]
    b += mix(x + 505, y) + lo(x + 505, y + 62, "LO2  (fixed)")
    b += [L(x + 505, y + 15, x + 505, y + 48, s=AMBER)]
    b += [L(x + 520, y, x + 544, y)]
    b += blk(x + 544, y - 21, 66, 42, "IF2", "channel")
    b += [L(x + 610, y, x + 634, y)]
    b += adc(x + 634, y - 21)
    b += [L(x + 692, y, x + 716, y), T(x + 722, y + 4, "DSP", 9.6,
                                       anchor="start", weight="bold")]
    b += [T(838, y - 44, "+ best selectivity and dynamic range", 9.4,
            anchor="start", fill=GREEN),
          T(838, y - 28, "+ no DC-offset problem", 9.4, anchor="start",
            fill=GREEN),
          T(838, y - 8, "- image filters at every stage", 9.4, anchor="start",
            fill=ACCENT),
          T(838, y + 8, "- most parts, biggest, most expensive", 9.4,
            anchor="start", fill=ACCENT),
          T(838, y + 28, "- spur planning is hard (M09)", 9.4, anchor="start",
            fill=ACCENT)]

    # ── (b) Zero-IF ────────────────────────────────────────
    y = rows[1][1] + 60
    x = 60
    b += ant(x, y) + [L(x, y, x + 22, y)]
    b += blk(x + 22, y - 21, 60, 42, "RF", "BPF")
    b += [L(x + 82, y, x + 104, y)]
    b += blk(x + 104, y - 21, 52, 42, "LNA")
    b += [L(x + 156, y, x + 186, y)]
    b += [L(x + 186, y - 40, x + 186, y + 40)]
    for dy, tag in ((-40, "I"), (40, "Q")):
        b += [L(x + 186, y + dy, x + 214, y + dy)]
        b += mix(x + 231, y + dy)
        b += [L(x + 246, y + dy, x + 272, y + dy)]
        b += blk(x + 272, y + dy - 19, 66, 38, "LPF", None)
        b += [L(x + 338, y + dy, x + 362, y + dy)]
        b += adc(x + 362, y + dy - 19, 50, 38)
        b += [L(x + 412, y + dy, x + 440, y + dy)]
        b += [T(x + 200, y + dy + (-8 if dy < 0 else 18), tag, 9.6,
                fill=GREEN, weight="bold")]
    b += lo(x + 231, y, "LO = RF, split 0 / 90 deg", side=76)
    b += [L(x + 231, y - 25, x + 231, y - 14, s=AMBER),
          L(x + 231, y + 14, x + 231, y + 25, s=AMBER)]
    b += [L(x + 440, y - 40, x + 440, y + 40),
          L(x + 440, y, x + 466, y),
          T(x + 472, y + 4, "DSP", 9.6, anchor="start", weight="bold")]
    b += [T(560, y - 52, "+ fewest parts, easiest to integrate", 9.4,
            anchor="start", fill=GREEN),
          T(560, y - 36, "+ no image filter, no IF SAW", 9.4, anchor="start",
            fill=GREEN),
          T(560, y - 16, "- DC offset from LO self-mixing", 9.4,
            anchor="start", fill=ACCENT),
          T(560, y, "- 1/f noise sits right on the signal", 9.4,
            anchor="start", fill=ACCENT),
          T(560, y + 16, "- second-order distortion (IP2) lands at DC", 9.4,
            anchor="start", fill=ACCENT),
          T(560, y + 32, "- I/Q imbalance folds the channel onto itself",
            9.4, anchor="start", fill=ACCENT),
          T(560, y + 52, "the dominant choice in modern integrated radios",
            9.4, anchor="start", fill=BLUE, weight="bold")]

    # ── (c) Low-IF ─────────────────────────────────────────
    y = rows[2][1] + 56
    x = 60
    b += ant(x, y) + [L(x, y, x + 22, y)]
    b += blk(x + 22, y - 21, 60, 42, "RF", "BPF")
    b += [L(x + 82, y, x + 104, y)]
    b += blk(x + 104, y - 21, 52, 42, "LNA")
    b += [L(x + 156, y, x + 186, y)]
    b += [L(x + 186, y - 34, x + 186, y + 34)]
    for dy in (-34, 34):
        b += [L(x + 186, y + dy, x + 214, y + dy)]
        b += mix(x + 231, y + dy)
        b += [L(x + 246, y + dy, x + 272, y + dy)]
        b += blk(x + 272, y + dy - 17, 66, 34, "BPF", None)
        b += [L(x + 338, y + dy, x + 362, y + dy)]
        b += adc(x + 362, y + dy - 17, 50, 34)
        b += [L(x + 412, y + dy, x + 436, y + dy)]
    b += lo(x + 231, y, "LO = RF - lowIF", side=70)
    b += [L(x + 231, y - 25, x + 231, y - 14, s=AMBER),
          L(x + 231, y + 14, x + 231, y + 25, s=AMBER)]
    b += blk(x + 436, y - 30, 84, 60, "digital", "IQ correct", fill="#EFF6EF",
             col=GREEN)
    b += [L(x + 520, y, x + 544, y),
          T(x + 550, y + 4, "DSP", 9.6, anchor="start", weight="bold")]
    b += [T(640, y - 44, "+ moves the signal off DC and off 1/f noise", 9.4,
            anchor="start", fill=GREEN),
          T(640, y - 28, "+ still no IF SAW filter", 9.4, anchor="start",
            fill=GREEN),
          T(640, y - 8, "- the adjacent channel becomes the image", 9.4,
            anchor="start", fill=ACCENT),
          T(640, y + 8, "- needs I/Q imbalance calibration (25-60 dB)", 9.4,
            anchor="start", fill=ACCENT),
          T(640, y + 28, "used by Bluetooth, many IoT radios", 9.4,
            anchor="start", fill=BLUE, weight="bold")]

    # ── (d) 직접 RF 샘플링 ──────────────────────────────────
    y = rows[3][1] + 56
    x = 60
    b += ant(x, y) + [L(x, y, x + 22, y)]
    b += blk(x + 22, y - 21, 70, 42, "RF", "BPF (must!)")
    b += [L(x + 92, y, x + 114, y)]
    b += blk(x + 114, y - 21, 52, 42, "LNA")
    b += [L(x + 166, y, x + 190, y)]
    b += adc(x + 190, y - 24, 76, 48, "RF ADC")
    b += [L(x + 266, y, x + 294, y)]
    b += blk(x + 294, y - 24, 96, 48, "digital", "down-convert",
             fill="#EFF6EF", col=GREEN)
    b += [L(x + 390, y, x + 414, y)]
    b += blk(x + 414, y - 24, 84, 48, "decimate", "+ filter", fill="#EFF6EF",
             col=GREEN)
    b += [L(x + 498, y, x + 522, y),
          T(x + 528, y + 4, "DSP", 9.6, anchor="start", weight="bold")]
    b += [T(620, y - 44, "+ no analogue mixer, no I/Q imbalance at all", 9.4,
            anchor="start", fill=GREEN),
          T(620, y - 28, "+ one radio covers many bands in software", 9.4,
            anchor="start", fill=GREEN),
          T(620, y - 8, "- the ADC must swallow the whole band", 9.4,
            anchor="start", fill=ACCENT),
          T(620, y + 8, "- high power, and clock jitter now limits SNR",
            9.4, anchor="start", fill=ACCENT),
          T(620, y + 28, "- an out-of-band signal aliases straight in", 9.4,
            anchor="start", fill=ACCENT)]

    b += [T(W / 2, H - 16,
            "Every architecture keeps the same jobs - filter, amplify, shift, "
            "digitise. Only WHERE each job happens changes.",
            11, fill=ACCENT, weight="bold")]

    (OUT / "M11").mkdir(parents=True, exist_ok=True)
    (OUT / "M11" / "architectures.svg").write_text(
        doc(W, H, "\n".join(b),
            "수신 아키텍처 4종 비교 — 슈퍼헤테로다인, Zero-IF, Low-IF, 직접 RF 샘플링"),
        encoding="utf-8")


# ═══════════════════════════════ M11-4: Zero-IF 고유 문제
def zeroif_problems():
    W, H = 1080, 356
    b = [defs(), T(W / 2, 30,
                   "Two problems that only Zero-IF has", 14, weight="bold")]

    # ① LO 자체 혼합 -> DC 오프셋
    x0, y = 56, 168
    b += [T(x0, 92, "(1) LO self-mixing becomes a DC offset", 11.5,
            anchor="start", weight="bold")]
    b += ant(x0 + 24, y) + [L(x0 + 24, y, x0 + 60, y)]
    b += blk(x0 + 60, y - 20, 48, 40, "LNA")
    b += [L(x0 + 108, y, x0 + 138, y)]
    b += mix(x0 + 155, y)
    b += lo(x0 + 155, y + 66, "LO")
    b += [L(x0 + 155, y + 15, x0 + 155, y + 52, s=AMBER)]
    b += [L(x0 + 170, y, x0 + 200, y)]
    b += blk(x0 + 200, y - 20, 54, 40, "LPF")
    b += [L(x0 + 254, y, x0 + 280, y)]
    b += adc(x0 + 280, y - 20, 48, 40)

    # LO 누설 경로 (나가는 것과 되돌아오는 것)
    b += [P(f"M {x0+143} {y-16} C {x0+118} {y-46} {x0+58} {y-48} "
            f"{x0+26} {y-30}", s=ACCENT, sw=1.8, dash="5 4", marker="ar")]
    b += [C(x0 + 88, y - 47, 9, fill="white", s=ACCENT, sw=1.4),
          T(x0 + 88, y - 43, "1", 9, fill=ACCENT, weight="bold")]
    b += [P(f"M {x0+22} {y-40} C {x0+62} {y-76} {x0+150} {y-70} "
            f"{x0+166} {y-20}", s=ACCENT, sw=1.8, dash="5 4", marker="ar")]
    b += [C(x0 + 96, y - 68, 9, fill="white", s=ACCENT, sw=1.4),
          T(x0 + 96, y - 64, "2", 9, fill=ACCENT, weight="bold")]

    b += [T(x0 + 346, y - 34, "1  the LO leaks out to the antenna", 9.4,
            anchor="start", fill=ACCENT),
          T(x0 + 346, y - 16, "2  it reflects off nearby objects", 9.4,
            anchor="start", fill=ACCENT),
          T(x0 + 346, y + 2, "    and comes back into the mixer", 9.4,
            anchor="start", fill=ACCENT)]
    b += [T(x0 + 160, y + 106,
            "LO x LO = a constant -> a DC step at the ADC input", 9.6,
            anchor="middle", fill=ACCENT, weight="bold")]
    b += [T(x0 + 160, y + 124,
            "and it MOVES when the surroundings move", 9.4, anchor="middle",
            fill="#555")]

    # ② IP2 -> 포락선이 DC 로
    x0 = 604
    b += [T(x0, 92, "(2) Second-order distortion lands at DC", 11.5,
            anchor="start", weight="bold")]
    b += [L(x0 + 20, y + 40, x0 + 200, y + 40, s=INK, w=1.4)]
    b += [L(x0 + 20, y + 40, x0 + 20, y - 44, s=INK, w=1.4)]
    b += [L(x0 + 96, y + 40, x0 + 96, y - 30, s=INK, w=3.4),
          T(x0 + 96, y - 38, "strong interferer", 9.2, fill=INK)]
    b += [T(x0 + 110, y + 56, "RF spectrum", 9.2, anchor="middle",
            fill="#666")]

    b += [P(f"M {x0+210} {y} L {x0+250} {y}", s=ACCENT, sw=2, marker="ar"),
          T(x0 + 230, y - 10, "IP2", 9.4, fill=ACCENT, weight="bold")]

    b += [L(x0 + 264, y + 40, x0 + 430, y + 40, s=INK, w=1.4)]
    b += [L(x0 + 264, y + 40, x0 + 264, y - 44, s=INK, w=1.4)]
    b += [L(x0 + 266, y + 40, x0 + 266, y - 24, s=ACCENT, w=4.0)]
    b += [T(x0 + 300, y - 32, "its envelope appears at 0 Hz", 9.2,
            fill=ACCENT, anchor="start")]
    b += [T(x0 + 348, y + 56, "baseband spectrum", 9.2, anchor="middle",
            fill="#666")]
    b += [T(x0 + 200, y + 108,
            "in a superheterodyne this lands at 0 Hz too - but 0 Hz is not "
            "the signal there.", 9.6, anchor="middle", fill="#555")]
    b += [T(x0 + 200, y + 126,
            "In Zero-IF, 0 Hz IS the signal. Hence the high IP2 requirement.",
            9.6, anchor="middle", fill=ACCENT, weight="bold")]

    b += [T(W / 2, H - 14,
            "Both are fixed in practice by DC servo loops, AC coupling, and "
            "IP2 calibration - never by filtering alone.",
            10.5, fill=BLUE, weight="bold")]

    (OUT / "M11").mkdir(parents=True, exist_ok=True)
    (OUT / "M11" / "zeroif_problems.svg").write_text(
        doc(W, H, "\n".join(b),
            "Zero-IF 수신기에만 있는 두 가지 문제 — LO 자체 혼합에 의한 DC 오프셋과 IP2"),
        encoding="utf-8")


if __name__ == "__main__":
    architectures()
    zeroif_problems()
    print("M11 SVG 도해 2종 생성 완료")
