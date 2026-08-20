#!/usr/bin/env python3
"""
M08 (증폭기) 손그림 SVG 도해 생성기
====================================

규약: SVG 안에 한글을 넣지 않는다 (보는 사람 PC의 폰트에 의존하므로).
      한글 설명은 마크다운 캡션과 본문 표에 쓴다.

    python3 scripts/gen_svg_m08.py
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
    for name, col in (("ar", ACCENT), ("ab", BLUE), ("ag", GREEN),
                      ("ak", INK)):
        out.append(
            f'    <marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{col}"/></marker>')
    out.append('  </defs>')
    return "\n".join(out)


def res(x, y, w=34, h=15):
    return [R(x, y - h / 2, w, h)]


def cap_h(x, y, gap=9, h=19):
    """가로 배선 위의 직렬 커패시터. 왼쪽 판이 x 에 온다."""
    return [L(x, y - h / 2, x, y + h / 2),
            L(x + gap, y - h / 2, x + gap, y + h / 2)]


def cap_v(x, y, gap=9, w=19):
    """세로 배선 위의 커패시터. 위쪽 판이 y 에 온다."""
    return [L(x - w / 2, y, x + w / 2, y),
            L(x - w / 2, y + gap, x + w / 2, y + gap)]


def ind_h(x, y, n=4, r=7):
    d = f"M {x} {y}"
    for _ in range(n):
        d += f" a {r} {r} 0 0 1 {2*r} 0"
    return [P(d)]


def gnd(x, y, w=18):
    return [L(x, y, x, y + 8),
            L(x - w / 2, y + 8, x + w / 2, y + 8),
            L(x - w / 2 + 5, y + 13, x + w / 2 - 5, y + 13),
            L(x - w / 2 + 9, y + 18, x + w / 2 - 9, y + 18)]


def fet(x, y, s=INK):
    """간단한 FET 기호. (x, y) 는 게이트 단자 끝점."""
    gx, bx = x + 26, x + 34            # 게이트 세로선, 채널 세로선
    return [L(x, y, gx, y),                              # 게이트 리드
            L(gx, y - 20, gx, y + 20),                   # 게이트 판
            L(bx, y - 22, bx, y + 22),                   # 채널
            L(bx, y - 18, bx + 30, y - 18),              # 드레인
            L(bx + 30, y - 18, bx + 30, y - 40),
            L(bx, y + 18, bx + 30, y + 18),              # 소스
            L(bx + 30, y + 18, bx + 30, y + 40)]


# ═══════════════════════════════════════ M08-1: 네 가지 이득의 정의
def gain_types():
    W, H = 900, 470
    b = [defs(), T(W / 2, 30, "Where each gain definition looks", 14,
                   weight="bold")]

    y = 122
    # 소스 - 입력 정합 - 2포트 - 출력 정합 - 부하
    b += [C(80, y, 20), L(80, y - 20, 80, y - 34), L(80, y + 20, 80, y + 34)]
    b += gnd(80, y + 34, 22)
    b += [T(80, y - 44, "Source", 11, weight="bold"),
          T(112, y + 6, "Zs", 11, anchor="start", fill=ACCENT)]
    b += [L(100, y, 150, y)]
    b += [R(150, y - 30, 96, 60, fill=PANEL, rx=6),
          T(198, y - 6, "Input", 11), T(198, y + 10, "match", 11)]
    b += [L(246, y, 296, y)]
    b += [R(296, y - 34, 108, 68, fill="#FFF6E8", rx=6),
          T(350, y - 8, "Two-port", 12, weight="bold"),
          T(350, y + 12, "(transistor)", 10, fill="#666")]
    b += [L(404, y, 454, y)]
    b += [R(454, y - 30, 96, 60, fill=PANEL, rx=6),
          T(502, y - 6, "Output", 11), T(502, y + 10, "match", 11)]
    b += [L(550, y, 600, y)]
    b += [R(600, y - 20, 16, 40, fill="none"),
          T(608, y - 32, "Load", 11, weight="bold"),
          T(624, y + 6, "ZL", 11, anchor="start", fill=ACCENT)]

    # 반사계수 화살표 네 개
    arrows = [(150, "Gs", BLUE, "ab", -1), (296, "Gin", GREEN, "ag", +1),
              (404, "Gout", GREEN, "ag", -1), (550, "GL", BLUE, "ab", +1)]
    for x, name, col, mk, direction in arrows:
        y0 = y - 52
        x1 = x + 26 * direction
        b += [P(f"M {x} {y0} L {x1} {y0}", s=col, sw=2, marker=mk),
              T((x + x1) / 2, y0 - 8, name, 10.5, fill=col, weight="bold")]
        b += [L(x, y - 46, x, y - 6, s=col, w=1.2, dash="3 3")]

    # 이득 정의 표
    ty = 214
    rows = [("Transducer  GT",
             "power delivered to load / power AVAILABLE from source",
             "both ends mismatched - the honest, real-world number", INK),
            ("Available  GA",
             "power available from network / power available from source",
             "depends on Gs only - used for NOISE and LNA design", GREEN),
            ("Operating (power)  GP",
             "power delivered to load / power INPUT to the network",
             "depends on GL only - used for PA / output design", ACCENT),
            ("Maximum available  MAG",
             "GT when both ends are conjugate-matched (needs K > 1)",
             "the ceiling - a single number in the datasheet", BLUE)]
    b += [R(52, ty - 26, W - 104, 26 + len(rows) * 46 + 8, fill="#FCFCFD",
            s="#DDD", sw=1.4, rx=8)]
    b += [T(66, ty - 8, "Name", 11, anchor="start", weight="bold"),
          T(250, ty - 8, "Definition", 11, anchor="start", weight="bold"),
          T(556, ty - 8, "When you use it", 11, anchor="start",
            weight="bold")]
    for i, (name, dfn, use, col) in enumerate(rows):
        yy = ty + 22 + i * 46
        b += [L(60, yy - 16, W - 60, yy - 16, s="#E6E6E6", w=1)]
        b += [T(66, yy + 4, name, 10.5, anchor="start", fill=col,
                weight="bold"),
              T(250, yy + 4, dfn, 9.6, anchor="start"),
              T(556, yy + 4, use, 9.6, anchor="start", fill="#555")]

    b += [T(W / 2, H - 32,
            "All four are equal only when BOTH ends are conjugate-matched.",
            10.5, fill=ACCENT, weight="bold"),
          T(W / 2, H - 12,
            "G in this figure means Gamma - the reflection coefficient "
            "looking in that direction.", 9.6, fill="#555")]

    (OUT / "M08").mkdir(parents=True, exist_ok=True)
    (OUT / "M08" / "gain_types.svg").write_text(
        doc(W, H, "\n".join(b),
            "증폭기의 네 가지 이득 정의와 각각이 무엇을 가정하는지"),
        encoding="utf-8")


def ind_v(x, y, n=3, r=7):
    """세로 배선 위의 인덕터. (x, y) 에서 아래로 n 개의 반원."""
    d = f"M {x} {y}"
    for _ in range(n):
        d += f" a {r} {r} 0 0 1 0 {2*r}"
    return [P(d)]


# ---------------------------------------- M08-9: 실제 LNA 회로도
def lna_schematic():
    W, H = 1000, 620
    b = [defs(), T(W / 2, 32, "A real single-stage LNA - what every part "
                              "is for", 14, weight="bold")]

    y = 310                       # 입력 신호 경로 높이
    yo = y - 40                   # 출력 신호 경로 높이 (드레인 쪽)
    vdd = 96                      # 전원 레일

    b += [L(56, vdd, W - 40, vdd, s=ACCENT, w=2),
          T(56, vdd - 12, "VDD", 11, anchor="start", fill=ACCENT,
            weight="bold")]

    # 입력 경로
    b += [C(64, y, 14), T(64, y - 26, "RF IN", 10.5, weight="bold")]
    b += [L(78, y, 104, y)] + cap_h(104, y) + [L(113, y, 152, y)]
    b += [T(108, y - 20, "Cblk", 9.5, fill=BLUE)]
    b += ind_h(152, y, 3, 7) + [L(194, y, 292, y)]
    b += [T(173, y - 20, "Lser", 9.5, fill=GREEN)]

    # 정합용 병렬 커패시터 (아래로)
    b += [L(226, y, 226, y + 40)] + cap_v(226, y + 40) + \
         [L(226, y + 49, 226, y + 66)] + gnd(226, y + 66)
    b += [T(240, y + 46, "Cshunt", 9.5, anchor="start", fill=GREEN)]

    # 게이트 바이어스 (위로)
    bias_y = 190
    b += [L(266, y, 266, bias_y), L(266, bias_y, 232, bias_y)]
    b += res(198, bias_y) + [L(184, bias_y, 198, bias_y)]
    b += [T(215, bias_y - 14, "Rgate", 9.5, fill=AMBER)]
    b += [C(160, bias_y, 14), T(160, bias_y - 26, "VG", 10.5, weight="bold")]
    b += [L(184, bias_y, 184, bias_y + 26)] + cap_v(184, bias_y + 26) + \
         [L(184, bias_y + 35, 184, bias_y + 50)] + gnd(184, bias_y + 50)
    b += [T(198, bias_y + 34, "Cbyp", 9.5, anchor="start", fill=AMBER)]
    b += [T(60, 442, "Rgate: bias enters through a resistor, so the bias "
                     "line barely loads the RF", 9.4, anchor="start",
            fill=AMBER)]

    # 트랜지스터
    gx, bx = 314, 328             # 게이트 판, 채널 (간격을 벌려야 구분된다)
    b += [L(292, y, gx, y), L(gx, y - 22, gx, y + 22),
          L(bx, y - 26, bx, y + 26)]
    b += [L(bx, y - 20, bx + 44, y - 20), L(bx + 44, y - 20, bx + 44, yo)]
    b += [L(bx, y + 20, bx + 44, y + 20), L(bx + 44, y + 20, bx + 44, y + 44)]
    b += [T(bx + 62, y + 6, "LNA device", 10.5, anchor="start",
            weight="bold")]

    # 소스 축퇴 인덕터
    sx = bx + 44
    b += ind_v(sx, y + 44, 3, 7) + [L(sx, y + 86, sx, y + 100)] + \
         gnd(sx, y + 100)
    b += [T(sx + 18, y + 66, "Ldeg (source degeneration)", 9.6,
            anchor="start", fill=ACCENT)]
    b += [T(sx + 18, y + 82, "adds a real part to Zin WITHOUT adding noise", 9.2,
            anchor="start", fill="#666")]

    # 드레인: RF 초크로 전원 공급
    dx = sx
    b += [L(dx, yo, dx, 190)]
    b += ind_v(dx, 148, 3, 7)
    b += [L(dx, 148, dx, vdd)]
    b += [T(dx + 16, 156, "Lchoke", 9.6, anchor="start", fill=AMBER),
          T(dx + 16, 172, "RF blocked, DC passes", 9.2, anchor="start",
            fill="#666")]

    # 출력 경로
    b += [L(dx, yo, 430, yo)] + ind_h(430, yo, 3, 7) + [L(472, yo, 520, yo)]
    b += [T(451, yo - 20, "Lout", 9.5, fill=GREEN)]
    b += cap_h(520, yo) + [L(529, yo, 592, yo)]
    b += [T(524, yo - 20, "Cblk", 9.5, fill=BLUE)]
    b += [L(560, yo, 560, yo + 40)] + cap_v(560, yo + 40) + \
         [L(560, yo + 49, 560, yo + 66)] + gnd(560, yo + 66)
    b += [T(574, yo + 46, "Cshunt", 9.5, anchor="start", fill=GREEN)]
    b += [C(606, yo, 14), T(606, yo - 26, "RF OUT", 10.5, weight="bold")]

    # 전원 디커플링
    for xx, lab in ((700, "100 pF"), (770, "10 nF"), (840, "10 uF")):
        b += [L(xx, vdd, xx, vdd + 30)] + cap_v(xx, vdd + 30) + \
             [L(xx, vdd + 39, xx, vdd + 54)] + gnd(xx, vdd + 54)
        b += [T(xx, vdd + 92, lab, 9.4, fill=BLUE)]
    b += [T(770, vdd + 116, "decoupling: smallest value nearest the pin, "
                            "and watch the anti-resonance (M06)", 9.4,
            fill="#555")]

    # 색 범례 (바이어스 부품이 회로 여기저기에 흩어져 있어
    #           x 위치로 구역을 나누면 오히려 거짓말이 된다)
    zy = 474
    legend = [(GREEN, "matching", "sets Gs and GL - the terminations the "
               "device wants, not 50 ohm"),
              (AMBER, "bias", "sets the DC operating point, and must look "
               "like an open circuit to RF"),
              (BLUE, "DC block / decoupling", "keeps DC out of the RF path "
               "and RF out of the supply")]
    b += [R(56, zy - 18, W - 112, 86, fill="#FCFCFD", s="#DDD", sw=1.4,
            rx=8)]
    for i, (col, head, sub) in enumerate(legend):
        yy = zy + 4 + i * 24
        b += [L(76, yy - 4, 106, yy - 4, s=col, w=4)]
        b += [T(118, yy, head, 10, anchor="start", fill=col, weight="bold"),
              T(268, yy, sub, 9.6, anchor="start", fill="#444")]

    b += [T(W / 2, H - 34,
            "The matching networks are NOT there to make 50 ohm - they are "
            "there to present the source and load the device wants.",
            10.5, fill=ACCENT, weight="bold")]
    b += [T(W / 2, H - 14, "G = Gamma (reflection coefficient).", 9.6,
            fill="#555")]

    (OUT / "M08").mkdir(parents=True, exist_ok=True)
    (OUT / "M08" / "lna_schematic.svg").write_text(
        doc(W, H, "\n".join(b),
            "단일 단 저잡음 증폭기의 실제 회로도와 각 부품의 역할"),
        encoding="utf-8")


if __name__ == "__main__":
    gain_types()
    lna_schematic()
    print("M08 SVG 도해 2종 생성 완료")
