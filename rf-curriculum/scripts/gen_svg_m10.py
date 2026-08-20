#!/usr/bin/env python3
"""
M10 (안테나와 전파) 손그림 SVG 도해 생성기
==========================================

규약: SVG 안에 한글을 넣지 않는다. 한글 설명은 마크다운 캡션에 쓴다.

    python3 scripts/gen_svg_m10.py
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


def source(cx, cy, r=13):
    return [C(cx, cy, r),
            P(f"M {cx-7} {cy} q 3.5 -6 7 0 q 3.5 6 7 0", sw=1.6)]


# ═══════════════════════════════ M10-1: 전류가 어떻게 전파가 되는가
def radiation():
    W, H = 1120, 470
    b = [defs(), T(W / 2, 30, "How a current on a wire becomes a radio wave",
                   14, weight="bold")]

    y0 = 90
    # (a) 평행 2선 — 전자기장이 선 사이에 갇혀 있다
    x0 = 60
    b += [T(x0, y0, "(a) Open two-wire line", 11.5, anchor="start",
            weight="bold")]
    yc = y0 + 96
    b += source(x0 + 16, yc)
    b += [L(x0 + 16, yc - 13, x0 + 16, yc - 46), L(x0 + 16, yc + 13,
                                                   x0 + 16, yc + 46)]
    b += [L(x0 + 16, yc - 46, x0 + 200, yc - 46),
          L(x0 + 16, yc + 46, x0 + 200, yc + 46)]
    for xx in range(x0 + 44, x0 + 200, 26):
        b += [P(f"M {xx} {yc-42} L {xx} {yc+42}", s=BLUE, sw=1.4,
                marker="ab")]
    b += [T(x0 + 118, yc + 74, "field is trapped between the wires", 9.6,
            fill=BLUE),
          T(x0 + 118, yc + 90, "almost nothing radiates", 9.6, fill="#666")]

    # (b) 끝을 벌리면
    x0 = 380
    b += [T(x0, y0, "(b) Bend the ends outward", 11.5, anchor="start",
            weight="bold")]
    b += source(x0 + 16, yc)
    b += [L(x0 + 16, yc - 13, x0 + 16, yc - 46), L(x0 + 16, yc + 13,
                                                   x0 + 16, yc + 46)]
    b += [L(x0 + 16, yc - 46, x0 + 120, yc - 46),
          L(x0 + 16, yc + 46, x0 + 120, yc + 46)]
    b += [L(x0 + 120, yc - 46, x0 + 196, yc - 82),
          L(x0 + 120, yc + 46, x0 + 196, yc + 82)]
    for xx in range(x0 + 44, x0 + 120, 26):
        b += [P(f"M {xx} {yc-42} L {xx} {yc+42}", s=BLUE, sw=1.4,
                marker="ab")]
    for r in (44, 68, 92):
        b += [P(f"M {x0+196+r*0.2} {yc-r*0.62} "
                f"A {r} {r} 0 0 1 {x0+196+r*0.2} {yc+r*0.62}",
                s=ACCENT, sw=1.5, dash="5 4")]
    b += [T(x0 + 118, yc + 106, "the field starts to escape", 9.6,
            fill=ACCENT)]

    # (c) 반파장 다이폴
    x0 = 736
    b += [T(x0, y0, "(c) Half-wave dipole", 11.5, anchor="start",
            weight="bold")]
    cx = x0 + 148
    b += source(cx, yc)
    b += [L(cx, yc - 13, cx, yc - 92, w=3), L(cx, yc + 13, cx, yc + 92, w=3)]
    # 전류 분포 (반주기 사인)
    d = f"M {cx} {yc-92}"
    for i in range(1, 41):
        t = i / 40.0
        yy = yc - 92 + t * 184
        import math
        xx = cx + 34 * math.sin(math.pi * t)
        d += f" L {xx:.1f} {yy:.1f}"
    b += [P(d, s=GREEN, sw=2.0, dash="6 4")]
    b += [T(cx + 44, yc + 122, "current distribution", 9.6, fill=GREEN)]
    for r in (46, 68, 90):
        b += [P(f"M {cx-r} {yc} A {r} {r} 0 0 0 {cx+r} {yc}", s=ACCENT,
                sw=1.5, dash="5 4"),
              P(f"M {cx-r} {yc} A {r} {r} 0 0 1 {cx+r} {yc}", s=ACCENT,
                sw=1.5, dash="5 4")]
    b += [L(cx - 116, yc - 92, cx - 100, yc - 92, s="#777", w=1.2),
          L(cx - 116, yc + 92, cx - 100, yc + 92, s="#777", w=1.2),
          P(f"M {cx-108} {yc-92} L {cx-108} {yc+92}", s="#777", sw=1.2,
            marker="ak"),
          T(cx - 114, yc + 4, "L / 2", 9.6, anchor="end", fill="#777")]

    b += [T(W / 2, H - 52,
            "Radiation happens when the current cannot return along a nearby "
            "opposite conductor.", 11, fill=ACCENT, weight="bold")]
    b += [T(W / 2, H - 32,
            "That is also why an unintended slot in a ground plane radiates - "
            "see M17.", 10, fill="#555")]
    b += [T(W / 2, H - 12,
            "L here means the wavelength, so the dipole is half a wavelength "
            "long.", 9.6, fill="#777")]

    (OUT / "M10").mkdir(parents=True, exist_ok=True)
    (OUT / "M10" / "radiation.svg").write_text(
        doc(W, H, "\n".join(b),
            "전류가 전파가 되는 과정 — 평행 2선에서 반파장 다이폴까지"),
        encoding="utf-8")


# ═══════════════════════════════ M10-7: OTA 측정 방식 세 가지
def ota_setup():
    W, H = 1060, 372
    b = [defs(), T(W / 2, 30, "Three ways to measure an antenna over the air",
                   14, weight="bold")]

    def chamber(x, y, w, h):
        out = [R(x, y, w, h, fill="#FBFBFC", s=INK, sw=2, rx=4)]
        step = 17
        for xx in range(x + 6, x + w - 6, step):
            out += [P(f"M {xx} {y+3} l 8 14 l 8 -14", s="#9AA7B4", sw=1.2)]
            out += [P(f"M {xx} {y+h-3} l 8 -14 l 8 14", s="#9AA7B4", sw=1.2)]
        for yy in range(y + 20, y + h - 20, step):
            out += [P(f"M {x+3} {yy} l 14 8 l -14 8", s="#9AA7B4", sw=1.2)]
            out += [P(f"M {x+w-3} {yy} l -14 8 l 14 8", s="#9AA7B4", sw=1.2)]
        return out

    def horn(x, y, flip=False):
        s = -1 if flip else 1
        return [P(f"M {x} {y} l {-18*s} -14 l 0 28 z", fill=INK, s=INK),
                L(x, y - 5, x + 22 * s, y - 20),
                L(x, y + 5, x + 22 * s, y + 20),
                L(x + 22 * s, y - 20, x + 22 * s, y + 20)]

    # ① 직접 원거리장
    x0, y0, w0, h0 = 40, 74, 300, 178
    b += [T(x0, y0 - 12, "(1) Direct far-field chamber", 11.5, anchor="start",
            weight="bold")]
    b += chamber(x0, y0, w0, h0)
    b += horn(x0 + 40, y0 + h0 / 2)
    b += [C(x0 + w0 - 46, y0 + h0 / 2, 13, fill=PANEL)]
    b += [T(x0 + w0 - 46, y0 + h0 / 2 + 30, "DUT", 9.6, weight="bold")]
    b += [P(f"M {x0+72} {y0+h0/2} L {x0+w0-64} {y0+h0/2}", s=ACCENT, sw=1.8,
            marker="ar")]
    b += [T(x0 + w0 / 2, y0 + h0 / 2 - 14, "R > 2D^2 / L", 10.5, fill=ACCENT,
            weight="bold")]
    b += [T(x0, y0 + h0 + 26, "simplest and most trusted,", 9.6,
            anchor="start", fill="#555"),
          T(x0, y0 + h0 + 42, "but the room must be long enough.", 9.6,
            anchor="start", fill="#555"),
          T(x0, y0 + h0 + 62, "1 m array at 28 GHz needs 187 m -", 9.6,
            anchor="start", fill=ACCENT),
          T(x0, y0 + h0 + 78, "no such room exists.", 9.6, anchor="start",
            fill=ACCENT)]

    # ② CATR
    x0 = 372
    b += [T(x0, y0 - 12, "(2) Compact range (CATR)", 11.5, anchor="start",
            weight="bold")]
    b += chamber(x0, y0, w0, h0)
    b += [P(f"M {x0+w0-40} {y0+22} A 150 150 0 0 0 {x0+w0-40} {y0+h0-22}",
            s=INK, sw=3)]
    b += horn(x0 + 62, y0 + h0 - 44, flip=True)
    b += [C(x0 + 82, y0 + 48, 13, fill=PANEL),
          T(x0 + 82, y0 + 26, "DUT", 9.6, weight="bold")]
    b += [P(f"M {x0+92} {y0+h0-52} L {x0+w0-56} {y0+h0/2-6}", s=AMBER,
            sw=1.6, marker="ak")]
    for dy in (-22, 0, 22):
        b += [P(f"M {x0+w0-58} {y0+h0/2+dy} L {x0+100} {y0+h0/2+dy}",
                s=ACCENT, sw=1.6, marker="ar")]
    b += [T(x0 + w0 / 2 + 8, y0 + h0 / 2 + 46, "plane wave", 10,
            fill=ACCENT, weight="bold")]
    b += [T(x0, y0 + h0 + 26, "a shaped reflector turns a spherical", 9.6,
            anchor="start", fill="#555"),
          T(x0, y0 + h0 + 42, "wave into a flat one in a few metres.", 9.6,
            anchor="start", fill="#555"),
          T(x0, y0 + h0 + 62, "expensive, and the quiet zone is", 9.6,
            anchor="start", fill=AMBER),
          T(x0, y0 + h0 + 78, "smaller than the chamber.", 9.6, anchor="start",
            fill=AMBER)]

    # ③ 근거리장 스캐닝
    x0 = 704
    b += [T(x0, y0 - 12, "(3) Near-field scanning", 11.5, anchor="start",
            weight="bold")]
    b += chamber(x0, y0, w0, h0)
    b += [C(x0 + 56, y0 + h0 / 2, 13, fill=PANEL),
          T(x0 + 56, y0 + h0 / 2 + 30, "DUT", 9.6, weight="bold")]
    b += [L(x0 + 168, y0 + 26, x0 + 168, y0 + h0 - 26, s=GREEN, w=2,
            dash="6 4")]
    for yy in range(y0 + 34, y0 + h0 - 26, 26):
        b += [R(x0 + 160, yy - 6, 16, 12, fill=GREEN, s=GREEN, sw=1)]
    b += [P(f"M {x0+196} {y0+34} L {x0+196} {y0+h0-34}", s=GREEN, sw=1.6,
            marker="ag"),
          T(x0 + 202, y0 + h0 - 34, "scan", 9.6, anchor="start",
            fill=GREEN)]
    b += [T(x0 + 252, y0 + h0 / 2 - 12, "FFT to", 10.5, fill=ACCENT,
            weight="bold"),
          T(x0 + 252, y0 + h0 / 2 + 6, "far field", 10.5, fill=ACCENT,
            weight="bold")]
    b += [T(x0, y0 + h0 + 26, "measure amplitude AND phase close in,", 9.6,
            anchor="start", fill="#555"),
          T(x0, y0 + h0 + 42, "then transform to the far field.", 9.6,
            anchor="start", fill="#555"),
          T(x0, y0 + h0 + 62, "smallest room, but slow and it needs", 9.6,
            anchor="start", fill=GREEN),
          T(x0, y0 + h0 + 78, "a phase-accurate receiver.", 9.6,
            anchor="start", fill=GREEN)]

    (OUT / "M10").mkdir(parents=True, exist_ok=True)
    (OUT / "M10" / "ota_setup.svg").write_text(
        doc(W, H, "\n".join(b),
            "공중 방사(OTA) 측정 방식 세 가지 — 직접 원거리장, 컴팩트 레인지, 근거리장 스캐닝"),
        encoding="utf-8")


if __name__ == "__main__":
    radiation()
    ota_setup()
    print("M10 SVG 도해 2종 생성 완료")
