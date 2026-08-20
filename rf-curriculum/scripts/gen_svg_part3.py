#!/usr/bin/env python3
"""
Part III 전반부 (M06, M07) 손그림 SVG 도해 생성기
=================================================

규약: SVG 안에 한글을 넣지 않는다. 한글 설명은 마크다운 캡션에 쓴다.

    python3 scripts/gen_svg_part3.py
"""

from pathlib import Path

INK = "#1a1a1a"
ACCENT = "#c0392b"
BLUE = "#0072B2"
GREEN = "#009E73"
AMBER = "#E69F00"
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
    for name, col in (("ar", ACCENT), ("ab", BLUE), ("ag", GREEN)):
        out.append(
            f'    <marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{col}"/></marker>')
    out.append('  </defs>')
    return "\n".join(out)


# 기본 소자 조각 (좌표를 받아 그리는 작은 부품들)
def res(x, y, w=34, h=16):
    return [R(x, y - h / 2, w, h)]


def cap(x, y, gap=10, h=20):
    return [L(x, y - h / 2, x, y + h / 2),
            L(x + gap, y - h / 2, x + gap, y + h / 2)]


def ind(x, y, n=4, r=8):
    d = f"M {x} {y}"
    for _ in range(n):
        d += f" a {r} {r} 0 0 1 {2*r} 0"
    return [P(d)]


def shunt_cap_over(xa, xb, y, top, label="Cp"):
    """노드 xa 와 xb 사이에 위쪽 가지로 병렬 커패시터를 건다."""
    xm = (xa + xb) / 2
    return [L(xa, y, xa, top), L(xa, top, xm - 9, top),
            L(xm - 9, top - 11, xm - 9, top + 11),
            L(xm + 3, top - 11, xm + 3, top + 11),
            L(xm + 3, top, xb, top), L(xb, top, xb, y),
            T(xm - 3, top - 18, label, 9.5, fill=ACCENT)]


# ────────────────────────────────────── M06: 실제 소자의 등가회로
def real_components():
    W, H = 880, 316
    b = [defs(), T(W / 2, 28, "Ideal vs real passive components", 13,
                   weight="bold")]

    y = 120

    # 커패시터
    x0 = 60
    b += [T(x0 + 130, 62, "Capacitor", 12, weight="bold")]
    b += [L(x0, y, x0 + 46, y)] + cap(x0 + 46, y) + [L(x0 + 56, y, x0 + 100, y)]
    b += [T(x0 + 51, y + 32, "ideal", 10, fill="#666")]
    yy = y + 96   # 기생 C 가지가 "ideal" 라벨과 닿지 않도록 여유
    b += [L(x0, yy, x0 + 26, yy)] + res(x0 + 26, yy) + \
         [L(x0 + 60, yy, x0 + 76, yy)] + ind(x0 + 76, yy, 3, 7) + \
         [L(x0 + 118, yy, x0 + 140, yy)] + cap(x0 + 140, yy) + \
         [L(x0 + 150, yy, x0 + 200, yy)]
    b += [T(x0 + 43, yy - 18, "ESR", 9.5, fill=ACCENT),
          T(x0 + 97, yy - 18, "ESL", 9.5, fill=ACCENT),
          T(x0 + 145, yy - 18, "C", 9.5),
          T(x0 + 100, yy + 30, "real (series model)", 10, fill="#666")]

    # 인덕터
    x1 = 330
    b += [T(x1 + 130, 62, "Inductor", 12, weight="bold")]
    b += [L(x1, y, x1 + 40, y)] + ind(x1 + 40, y, 4, 8) + \
         [L(x1 + 104, y, x1 + 150, y)]
    b += [T(x1 + 72, y + 32, "ideal", 10, fill="#666")]
    na, nb = x1 + 20, x1 + 180
    b += [L(x1, yy, na, yy)] + res(na, yy) + \
         [L(na + 34, yy, na + 50, yy)] + ind(na + 50, yy, 4, 8) + \
         [L(na + 114, yy, nb, yy), L(nb, yy, x1 + 210, yy)]
    b += shunt_cap_over(na, nb, yy, yy - 42)
    b += [T(na + 17, yy - 16, "Rs", 9.5, fill=ACCENT),
          T(na + 82, yy - 16, "L", 9.5),
          T((na + nb) / 2, yy + 30, "real (parallel Cp)", 10, fill="#666")]

    # 저항
    x2 = 620
    b += [T(x2 + 110, 62, "Resistor", 12, weight="bold")]
    b += [L(x2, y, x2 + 40, y)] + res(x2 + 40, y) + [L(x2 + 74, y, x2 + 180, y)]
    b += [T(x2 + 57, y + 32, "ideal", 10, fill="#666")]
    ra, rb = x2 + 20, x2 + 160
    b += [L(x2, yy, ra, yy)] + res(ra, yy) + \
         [L(ra + 34, yy, ra + 48, yy)] + ind(ra + 48, yy, 3, 7) + \
         [L(ra + 90, yy, rb, yy), L(rb, yy, x2 + 195, yy)]
    b += shunt_cap_over(ra, rb, yy, yy - 42)
    b += [T(ra + 17, yy - 16, "R", 9.5),
          T(ra + 69, yy - 16, "Ls", 9.5, fill=ACCENT),
          T((ra + rb) / 2, yy + 30, "real", 10, fill="#666")]

    b += [T(W / 2, H - 14, "Red labels are the PARASITICS - they are what "
            "decide the useful frequency range.", 10.5, fill=ACCENT,
            weight="bold")]

    (OUT / "M06").mkdir(parents=True, exist_ok=True)
    (OUT / "M06" / "real_components.svg").write_text(
        doc(W, H, "\n".join(b), "이상적 소자와 실제 소자의 등가회로 비교"),
        encoding="utf-8")


# ────────────────────────────────────── M06: 직렬 공진 vs 병렬 공진
def resonance():
    W, H = 780, 340
    b = [defs(), T(W / 2, 28, "Series vs parallel resonance", 13,
                   weight="bold")]

    # 직렬
    x0, y = 90, 120
    b += [T(x0 + 130, 62, "SERIES resonance", 12, weight="bold", fill=BLUE)]
    b += [L(x0, y, x0 + 26, y)] + res(x0 + 26, y) + \
         [L(x0 + 60, y, x0 + 76, y)] + ind(x0 + 76, y, 3, 7) + \
         [L(x0 + 118, y, x0 + 140, y)] + cap(x0 + 140, y) + \
         [L(x0 + 150, y, x0 + 200, y)]
    b += [T(x0 + 43, y - 18, "R", 9.5), T(x0 + 97, y - 18, "L", 9.5),
          T(x0 + 145, y - 18, "C", 9.5)]
    b += [R(x0 - 10, y + 34, 220, 96, "#EAF2F8", BLUE, 1.6, rx=5)]
    b += [T(x0 + 100, y + 56, "at f0:  Z = R  (minimum)", 11, weight="bold",
            fill=BLUE),
          T(x0 + 100, y + 76, "looks like a SHORT", 10, fill="#444"),
          T(x0 + 100, y + 96, "use: notch to ground,", 10, fill="#444"),
          T(x0 + 100, y + 112, "decoupling, series trap", 10, fill="#444")]

    # 병렬
    x1 = 430
    b += [T(x1 + 120, 58, "PARALLEL resonance", 12, weight="bold", fill=GREEN)]
    b += [L(x1, y, x1 + 40, y), L(x1 + 200, y, x1 + 240, y)]
    b += [L(x1 + 40, y, x1 + 40, y - 34), L(x1 + 40, y, x1 + 40, y + 34),
          L(x1 + 200, y, x1 + 200, y - 34), L(x1 + 200, y, x1 + 200, y + 34)]
    b += [L(x1 + 40, y - 34, x1 + 78, y - 34)] + ind(x1 + 78, y - 34, 3, 7) + \
         [L(x1 + 120, y - 34, x1 + 200, y - 34)]
    b += [L(x1 + 40, y + 34, x1 + 110, y + 34)] + cap(x1 + 110, y + 34, 0, 0) + \
         [L(x1 + 106, y + 26, x1 + 106, y + 42),
          L(x1 + 118, y + 26, x1 + 118, y + 42),
          L(x1 + 118, y + 34, x1 + 200, y + 34)]
    b += [T(x1 + 99, y - 46, "L", 9.5), T(x1 + 112, y + 62, "C", 9.5)]
    b += [R(x1 - 6, y + 76, 250, 96, "#EAF6F1", GREEN, 1.6, rx=5)]
    b += [T(x1 + 119, y + 98, "at f0:  Z = maximum", 11, weight="bold",
            fill=GREEN),
          T(x1 + 119, y + 118, "looks like an OPEN", 10, fill="#444"),
          T(x1 + 119, y + 138, "use: tank circuit, bias choke,", 10,
            fill="#444"),
          T(x1 + 119, y + 154, "oscillator resonator", 10, fill="#444")]

    b += [T(W / 2, H - 10, "f0 = 1 / (2 pi sqrt(L C))   for both.   "
            "Q = f0 / BW.", 11.5, weight="bold")]

    (OUT / "M06" / "resonance.svg").write_text(
        doc(W, H, "\n".join(b), "직렬 공진과 병렬 공진의 회로와 성질 비교"),
        encoding="utf-8")


# ────────────────────────────────────── M07: 결합기·분배기·서큘레이터
def couplers():
    W, H = 880, 400
    b = [defs(), T(W / 2, 28, "Directional coupler, Wilkinson divider, "
                   "circulator", 13, weight="bold")]

    # 방향성 결합기
    b += [T(150, 62, "Directional coupler", 12, weight="bold")]
    b += [L(40, 100, 260, 100), L(40, 160, 260, 160)]
    b += [L(90, 100, 90, 160, INK, 1.4, "5 3"),
          L(210, 100, 210, 160, INK, 1.4, "5 3")]
    b += [T(44, 92, "1 IN", 9.5, anchor="start", fill=ACCENT, weight="bold"),
          T(256, 92, "2 OUT", 9.5, anchor="end", fill=ACCENT, weight="bold"),
          T(44, 178, "4 ISO", 9.5, anchor="start", fill=BLUE),
          T(256, 178, "3 CPL", 9.5, anchor="end", fill=BLUE)]
    b += [T(150, 210, "coupling  C = P1 / P3   (e.g. 20 dB)", 9.6, fill="#444"),
          T(150, 226, "directivity D = P3 / P4  (higher = better)", 9.6,
            fill="#444"),
          T(150, 242, "isolation  I = C + D", 9.6, fill="#444")]

    # 윌킨슨 분배기
    cx = 470
    b += [T(cx, 62, "Wilkinson divider", 12, weight="bold")]
    b += [L(cx - 120, 130, cx - 60, 130)]
    b += [P(f"M {cx-60} 130 L {cx-10} 100 L {cx+60} 100", INK, 2.4),
          P(f"M {cx-60} 130 L {cx-10} 160 L {cx+60} 160", INK, 2.4)]
    b += [T(cx - 26, 88, "quarter-wave, 70.7 ohm", 8.6, fill="#666"),
          T(cx - 26, 182, "quarter-wave, 70.7 ohm", 8.6, fill="#666")]
    b += [L(cx + 60, 100, cx + 60, 118), L(cx + 60, 142, cx + 60, 160)]
    b += [R(cx + 44, 118, 32, 24, "#FDF0EE", ACCENT, 2)]
    b += [T(cx + 60, 134, "100", 9, fill=ACCENT, weight="bold")]
    b += [L(cx + 76, 100, cx + 120, 100), L(cx + 76, 160, cx + 120, 160)]
    b += [T(cx - 118, 122, "IN", 9.5, anchor="start", fill=ACCENT,
            weight="bold"),
          T(cx + 118, 92, "OUT 1", 9.5, anchor="end"),
          T(cx + 118, 182, "OUT 2", 9.5, anchor="end")]
    b += [T(cx, 210, "-3 dB each, all ports matched,", 9.6, fill="#444"),
          T(cx, 226, "output ports ISOLATED by the 100 ohm resistor", 9.6,
            fill="#444"),
          T(cx, 242, "(without it, they would just be a T junction)", 9.6,
            fill=ACCENT)]

    # 서큘레이터
    sx = 760
    b += [T(sx, 62, "Circulator", 12, weight="bold")]
    b += [C(sx, 130, 44)]
    b += [P(f"M {sx-20} {130+14} A 24 24 0 1 1 {sx+20} {130+14}", INK, 2.0),
          P(f"M {sx+13} {130+8} L {sx+20} {130+16} L {sx+27} {130+5}", INK, 2.0)]
    b += [L(sx - 80, 130, sx - 44, 130), L(sx + 44, 130, sx + 80, 130),
          L(sx, 174, sx, 206)]
    b += [T(sx - 76, 122, "1", 10, anchor="start", weight="bold"),
          T(sx + 76, 122, "2", 10, anchor="end", weight="bold"),
          T(sx + 10, 202, "3", 10, anchor="start", weight="bold")]
    b += [T(sx, 226, "1 -> 2 -> 3 -> 1 only", 9.6, fill="#444"),
          T(sx, 242, "terminate port 3 = isolator", 9.6, fill="#444")]

    y2 = 296
    b += [R(30, y2 - 16, W - 60, 84, PANEL, INK, 1.8, rx=6)]
    b += [T(46, y2 + 4, "WHY THESE MATTER FOR MEASUREMENT:", 11,
            anchor="start", weight="bold")]
    b += [T(46, y2 + 24, "Coupler: watch a transmitter output without "
            "loading it. Directivity limits how well you can separate "
            "forward and reverse waves.", 10, anchor="start"),
          T(46, y2 + 42, "Divider: split one source into two paths that stay "
            "isolated from each other (two-tone test - see M15).", 10,
            anchor="start"),
          T(46, y2 + 60, "Circulator / isolator: protect a source from "
            "reflected power, or separate TX and RX on one antenna.", 10,
            anchor="start")]

    (OUT / "M07").mkdir(parents=True, exist_ok=True)
    (OUT / "M07" / "couplers.svg").write_text(
        doc(W, H, "\n".join(b),
            "방향성 결합기, 윌킨슨 전력 분배기, 서큘레이터의 구조와 파라미터"),
        encoding="utf-8")


if __name__ == "__main__":
    real_components()
    resonance()
    couplers()
    print("SVG 도해 3종 생성 완료")
