#!/usr/bin/env python3
"""
Part II (M04, M05) 손그림 SVG 도해 생성기
=========================================

규약: SVG 안에 한글을 넣지 않는다 (보는 사람 PC의 폰트에 의존하므로).
      한글 설명은 마크다운 캡션과 본문 표에 쓴다.

    python3 scripts/gen_svg_part2.py
"""

from pathlib import Path

INK = "#1a1a1a"
ACCENT = "#c0392b"
BLUE = "#0072B2"
GREEN = "#009E73"
AMBER = "#E69F00"
COPPER = "#D9A066"
PANEL = "#F4F7FA"
SCREEN = "#0E1A24"
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


def T(x, y, s, size=11, anchor="middle", fill=INK, weight="normal",
      family=None):
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


# ────────────────────────────────────── M04: 커넥터 계열 호환성
def connector_family():
    W, H = 880, 432
    b = [defs(), T(W / 2, 28, "RF connector families and mating compatibility",
                   13, weight="bold")]

    fams = [
        ("SMA", 4.2, "18 GHz", COPPER, 112),
        ("3.5 mm", 3.5, "26.5 GHz", BLUE, 268),
        ("2.92 mm", 2.92, "40 GHz", GREEN, 412),
        ("2.4 mm", 2.4, "50 GHz", AMBER, 606),
        ("1.85 mm", 1.85, "67 GHz", "#CC79A7", 748),
    ]
    cy = 130
    for name, dia, fmax, col, cx in fams:
        rr = dia * 9
        b += [C(cx, cy, rr + 9, "none", INK, 2.2),
              C(cx, cy, rr, "#EAF2F8", col, 2.0),
              C(cx, cy, 4.5, col, INK, 1.4),
              T(cx, cy - rr - 20, name, 12, weight="bold"),
              T(cx, cy + rr + 24, f"up to {fmax}", 9.5, fill="#666"),
              T(cx, cy + rr + 38, f"outer dia {dia} mm", 9, fill="#999")]

    # 결합 가능한 두 무리 (Group A / Group B). 무리 사이는 결합 금지.
    y = 236
    b += [P(f"M 112 {y} L 412 {y}", GREEN, 2.4, dash="7 4"),
          P(f"M 606 {y} L 748 {y}", GREEN, 2.4, dash="7 4")]
    for cx in (112, 268, 412, 606, 748):
        b += [C(cx, y, 5, GREEN, GREEN, 1)]
    b += [T(262, y + 22, "GROUP A - mate with each other (with care)", 10,
            weight="bold", fill=GREEN),
          T(677, y + 22, "GROUP B - mate with each other", 10,
            weight="bold", fill=GREEN)]

    bx = 509
    b += [T(bx, y - 30, "DO NOT MATE", 10.5, weight="bold", fill=ACCENT),
          P(f"M {bx-26} {y-16} L {bx+26} {y+16}", ACCENT, 3.0),
          P(f"M {bx-26} {y+16} L {bx+26} {y-16}", ACCENT, 3.0)]

    y2 = 316
    b += [R(30, y2 - 20, W - 60, 92, "#FDF0EE", ACCENT, 2, rx=6)]
    b += [T(46, y2, "KEY RULES:", 11, anchor="start", weight="bold",
            fill=ACCENT)]
    b += [T(46, y2 + 20, "1. Group A and Group B are DELIBERATELY "
            "incompatible. The threads almost catch - forcing them "
            "destroys both.", 10, anchor="start", fill=INK)]
    b += [T(46, y2 + 39, "2. Within a group, the cheaper part limits "
            "performance and the precision part is the one that gets "
            "damaged.", 10, anchor="start", fill=INK)]
    b += [T(46, y2 + 58, "3. N-type, BNC, TNC, SMP are separate families. "
            "Torque differs by body material - see Appendix D.", 10,
            anchor="start", fill=INK)]

    (OUT / "M04").mkdir(parents=True, exist_ok=True)
    (OUT / "M04" / "connector_family.svg").write_text(
        doc(W, H, "\n".join(b),
            "RF 커넥터 계열과 결합 호환성: SMA, 3.5 mm, 2.92 mm, 2.4 mm"),
        encoding="utf-8")


# ────────────────────────────────────── M04: 장비 보호 셋업
def protection_setup():
    W, H = 820, 300
    b = [defs(), T(W / 2, 28, "Protecting the instrument input", 13,
                   weight="bold")]

    # 나쁜 예
    yb = 88
    b += [T(24, yb - 20, "WRONG", 11.5, anchor="start", weight="bold",
            fill=ACCENT)]
    b += [R(64, yb - 22, 108, 46, PANEL, INK, 2, rx=4),
          T(118, yb + 6, "PA +33 dBm", 11, weight="bold")]
    b += [P(f"M 172 {yb} L 300 {yb}", ACCENT, 2.6, marker="ar")]
    b += [R(300, yb - 30, 128, 62, PANEL, INK, 2, rx=5),
          R(310, yb - 20, 84, 34, SCREEN, INK, 1.4, rx=2),
          T(352, yb + 26, "SPECTRUM ANALYZER", 7.5, fill="#666")]
    b += [T(470, yb - 6, "max safe +10 dBm", 10.5, anchor="start",
            fill=ACCENT, weight="bold"),
          T(470, yb + 12, "-> 23 dB over: front end destroyed", 10.5,
            anchor="start", fill=ACCENT)]

    # 좋은 예
    yg = 218
    b += [T(24, yg - 20, "RIGHT", 11.5, anchor="start", weight="bold",
            fill=GREEN)]
    b += [R(64, yg - 22, 108, 46, PANEL, INK, 2, rx=4),
          T(118, yg + 6, "PA +33 dBm", 11, weight="bold")]
    b += [P(f"M 172 {yg} L 206 {yg}", GREEN, 2.6, marker="ag")]
    b += [R(206, yg - 20, 62, 40, "#EAF6F1", GREEN, 2, rx=4),
          T(237, yg + 5, "-30 dB", 10.5, weight="bold", fill=GREEN),
          T(237, yg - 28, "attenuator", 9, fill="#666")]
    b += [P(f"M 268 {yg} L 300 {yg}", GREEN, 2.6, marker="ag")]
    b += [R(300, yg - 30, 128, 62, PANEL, INK, 2, rx=5),
          R(310, yg - 20, 84, 34, SCREEN, INK, 1.4, rx=2),
          T(352, yg + 26, "SPECTRUM ANALYZER", 7.5, fill="#666")]
    b += [T(470, yg - 6, "sees +3 dBm - safe", 10.5, anchor="start",
            fill=GREEN, weight="bold"),
          T(470, yg + 12, "add 30 dB back when reading the value", 10.5,
            anchor="start", fill="#444")]

    (OUT / "M04" / "protection_setup.svg").write_text(
        doc(W, H, "\n".join(b),
            "장비 입력 보호: 감쇠기를 넣어 최대 정격을 넘지 않게 한다"),
        encoding="utf-8")


# ────────────────────────────────────── M05: SA 화면 주석도
def sa_screen():
    W, H = 820, 470
    b = [defs(), T(W / 2, 26, "Spectrum analyzer screen - what to read first",
                   13, weight="bold")]

    gx, gy, gw, gh = 150, 60, 500, 300
    b += [R(gx, gy, gw, gh, SCREEN, INK, 2, rx=3)]
    for i in range(1, 10):
        b += [L(gx + gw * i / 10, gy, gx + gw * i / 10, gy + gh, "#2A3E4E", 1)]
    for i in range(1, 10):
        b += [L(gx, gy + gh * i / 10, gx + gw, gy + gh * i / 10, "#2A3E4E", 1)]

    # 트레이스: 잡음 바닥 + 반송파 + 하모닉
    pts = []
    import math
    for i in range(0, 501, 2):
        x = gx + i
        n = 250 + 8 * math.sin(i * 0.7) * math.cos(i * 0.21)
        for c, amp, wdt in ((120, 190, 7), (250, 120, 6), (380, 70, 6)):
            n -= amp * math.exp(-((i - c) / wdt) ** 2)
        pts.append(f"{x} {gy + max(6, min(gh - 4, n))}")
    b += [P("M " + " L ".join(pts), "#FFD24A", 1.8)]

    def call(x1, y1, x2, y2, text, col=ACCENT, anchor="start"):
        return [P(f"M {x1} {y1} L {x2} {y2}", col, 1.5, marker="ar"),
                T(x1, y1 - 6, text, 10, anchor=anchor, fill=col,
                  weight="bold")]

    b += call(24, 82, 146, 78, "1  Reference level")
    b += call(24, 150, 146, 175, "2  dB / division")
    b += call(24, 250, 146, 300, "3  Noise floor (DANL)")
    b += call(660, 96, 282, 118, "4  Marker readout", anchor="start")
    b += [T(660, 112, "1.000 GHz", 10, anchor="start", fill="#444"),
          T(660, 126, "-20.4 dBm", 10, anchor="start", fill="#444")]
    b += call(660, 240, 540, 300, "5  Harmonics", anchor="start")
    b += [T(660, 256, "2f0, 3f0 ...", 10, anchor="start", fill="#444")]

    # 하단 설정 바
    by = gy + gh + 16
    b += [R(gx, by, gw, 40, PANEL, INK, 1.6, rx=3)]
    cells = [("CENTER", "1.000 GHz"), ("SPAN", "500 MHz"),
             ("RBW", "100 kHz"), ("VBW", "30 kHz"), ("ATT", "10 dB")]
    for i, (k, v) in enumerate(cells):
        cx = gx + gw * (i + 0.5) / len(cells)
        b += [T(cx, by + 16, k, 9, fill="#666", weight="bold"),
              T(cx, by + 31, v, 10.5)]
        if i:
            b += [L(gx + gw * i / len(cells), by + 4,
                    gx + gw * i / len(cells), by + 36, "#BBB", 1)]

    b += [T(gx - 6, by + 26, "6  Settings bar", 10, anchor="end",
            fill=ACCENT, weight="bold")]
    b += [T(W / 2, H - 22, "Read in this order: 6 (settings) -> 1,2 (scale) "
            "-> 3 (floor) -> 4,5 (signals).", 10.5, fill="#444"),
          T(W / 2, H - 7, "Reading a trace without checking RBW and "
            "attenuation is the most common beginner mistake.", 10,
            fill=ACCENT)]

    (OUT / "M05").mkdir(parents=True, exist_ok=True)
    (OUT / "M05" / "sa_screen.svg").write_text(
        doc(W, H, "\n".join(b), "스펙트럼 분석기 화면 해부도"), encoding="utf-8")


# ────────────────────────────────────── M05: VNA 화면 주석도
def vna_screen():
    W, H = 820, 430
    import math
    b = [defs(), T(W / 2, 26, "VNA screen - the same data, four formats", 13,
                   weight="bold")]

    def panel(px, py, pw, ph, title, drawer):
        out = [R(px, py, pw, ph, SCREEN, INK, 2, rx=3),
               T(px + pw / 2, py - 8, title, 10.5, weight="bold")]
        for i in range(1, 6):
            out += [L(px + pw * i / 6, py, px + pw * i / 6, py + ph,
                      "#2A3E4E", 1),
                    L(px, py + ph * i / 6, px + pw, py + ph * i / 6,
                      "#2A3E4E", 1)]
        out += drawer(px, py, pw, ph)
        return out

    def s11_db(px, py, pw, ph):
        pts = []
        for i in range(0, 201):
            x = px + pw * i / 200
            d = -3 - 26 * math.exp(-((i - 100) / 22) ** 2)
            y = py + ph * (-d) / 40
            pts.append(f"{x} {min(py+ph-3, max(py+3, y))}")
        return [P("M " + " L ".join(pts), "#4FC3F7", 2.0)]

    def s21_db(px, py, pw, ph):
        pts = []
        for i in range(0, 201):
            x = px + pw * i / 200
            d = -60 + 58 * math.exp(-((i - 100) / 30) ** 2)
            y = py + ph * (-d) / 70
            pts.append(f"{x} {min(py+ph-3, max(py+3, y))}")
        return [P("M " + " L ".join(pts), "#FFD24A", 2.0)]

    def smith(px, py, pw, ph):
        cx, cy, rr = px + pw / 2, py + ph / 2, min(pw, ph) / 2 - 8
        out = [C(cx, cy, rr, "none", "#7FA8C0", 1.6),
               L(cx - rr, cy, cx + rr, cy, "#7FA8C0", 1.2)]
        for r in (0.3, 1.0, 3.0):
            cc, rad = r / (1 + r), 1 / (1 + r)
            out += [C(cx + rr * cc, cy, rr * rad, "none", "#3E5C70", 1.0)]
        # 공진 소자의 전형적인 S11 궤적: 주파수를 쓸면 고리를 그리며
        # 공진점에서 중심(정합)에 가장 가까워진다.
        pts = []
        for i in range(0, 201):
            x_ = (i - 100) / 26.0                  # 정규화 이조(detuning)
            g = complex(0.0, 0.0)
            g = (1j * x_ - 0.12) / (1j * x_ + 1.0)  # 단순 공진 모델
            pts.append(f"{cx + rr*g.real} {cy - rr*g.imag}")
        out += [P("M " + " L ".join(pts), "#4FC3F7", 2.0)]
        out += [C(cx, cy, 3.5, "#FF7043", "#FF7043", 1)]
        return out

    def swr(px, py, pw, ph):
        pts = []
        for i in range(0, 201):
            x = px + pw * i / 200
            v = 3.4 - 2.3 * math.exp(-((i - 100) / 24) ** 2)
            y = py + ph * (5 - v) / 4.2
            pts.append(f"{x} {min(py+ph-3, max(py+3, y))}")
        return [P("M " + " L ".join(pts), "#A5D6A7", 2.0)]

    b += panel(60, 66, 300, 130, "S11  log magnitude (dB)", s11_db)
    b += panel(456, 66, 300, 130, "S21  log magnitude (dB)", s21_db)
    b += panel(60, 240, 300, 130, "S11  Smith chart", smith)
    b += panel(456, 240, 300, 130, "S11  SWR", swr)

    notes = [
        (60, 210, "Dip = matched here. Depth = return loss."),
        (456, 210, "Flat top = passband. Skirt = selectivity."),
        (60, 384, "Where the trace sits tells you what to add."),
        (456, 384, "Same info as S11 dB, easier for a pass/fail limit."),
    ]
    for x, y, t in notes:
        b += [T(x, y, t, 9.5, anchor="start", fill="#444")]

    b += [T(W / 2, H - 8, "All four are the SAME measurement shown "
            "differently - change the FORMAT, not the measurement.", 10.5,
            fill=ACCENT, weight="bold")]

    (OUT / "M05" / "vna_screen.svg").write_text(
        doc(W, H, "\n".join(b), "VNA 화면 해부도: 같은 데이터의 네 가지 표시 형식"),
        encoding="utf-8")


if __name__ == "__main__":
    connector_family()
    protection_setup()
    sa_screen()
    vna_screen()
    print("SVG 도해 4종 생성 완료")
