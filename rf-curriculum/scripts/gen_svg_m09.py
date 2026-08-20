#!/usr/bin/env python3
"""
M09 (주파수 변환과 신호원) 손그림 SVG 도해 생성기
==================================================

규약: SVG 안에 한글을 넣지 않는다 (보는 사람 PC의 폰트에 의존하므로).
      한글 설명은 마크다운 캡션과 본문 표에 쓴다.

    python3 scripts/gen_svg_m09.py
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


def mixer_sym(cx, cy, r=17):
    """믹서 기호: 원 안에 곱셈 표시."""
    d = r * 0.62
    return [C(cx, cy, r),
            L(cx - d, cy - d, cx + d, cy + d),
            L(cx - d, cy + d, cx + d, cy - d)]


def diode(x, y, ang=0):
    """다이오드 기호. ang=0 이면 오른쪽으로 흐른다."""
    if ang == 0:
        return [P(f"M {x} {y-8} L {x+14} {y} L {x} {y+8} Z", fill=INK),
                L(x + 14, y - 8, x + 14, y + 8, w=2.4)]
    return [P(f"M {x-8} {y} L {x} {y+14} L {x+8} {y} Z", fill=INK),
            L(x - 8, y + 14, x + 8, y + 14, w=2.4)]


def transformer(x, y, h=54):
    """중심탭 변압기(발룬) 기호."""
    out = []
    for dx in (0, 22):
        d = f"M {x+dx} {y}"
        for _ in range(3):
            d += f" a 8 8 0 0 {1 if dx == 0 else 0} 0 {h/3:.1f}"
        out.append(P(d))
    out += [L(x + 9, y - 4, x + 9, y + h + 4, w=1.4),
            L(x + 13, y - 4, x + 13, y + h + 4, w=1.4)]
    return out


def diode_rot(cx, cy, ang):
    """(cx, cy) 를 중심으로 ang 도 방향을 향하는 다이오드."""
    return [f'  <g transform="translate({cx},{cy}) rotate({ang})">'
            f'<path d="M -10 -7 L 4 0 L -10 7 Z" fill="{INK}"/>'
            f'<line x1="4" y1="-7" x2="4" y2="7" stroke="{INK}" '
            f'stroke-width="2.4"/></g>']


def hop(x, y, r=7):
    """세로 배선이 가로 배선을 넘어갈 때 쓰는 반원 점프 (연결 아님을 뜻한다)."""
    return [P(f"M {x} {y-r} a {r} {r} 0 0 1 0 {2*r}", sw=2)]


def gnd(x, y, w=18):
    return [L(x, y, x, y + 8),
            L(x - w / 2, y + 8, x + w / 2, y + 8),
            L(x - w / 2 + 5, y + 13, x + w / 2 - 5, y + 13),
            L(x - w / 2 + 9, y + 18, x + w / 2 - 9, y + 18)]


# ══════════════════════════════════════ M09-7: 믹서 구조 비교
def mixer_types():
    W, H = 1100, 790
    b = [defs(), T(W / 2, 30, "Mixer topologies - what each one buys you",
                   14, weight="bold")]

    # ── (a) 단일 소자 ──────────────────────────────────────────
    x0, y0 = 56, 84
    b += [T(x0, y0, "(a) Single-ended", 12, anchor="start", weight="bold")]
    yy = y0 + 66
    b += [L(x0, yy, x0 + 54, yy),
          T(x0 + 2, yy - 24, "RF and LO", 9.4, anchor="start", fill=BLUE),
          T(x0 + 2, yy - 11, "share ONE port", 9.4, anchor="start", fill=BLUE)]
    b += diode(x0 + 54, yy) + [L(x0 + 68, yy, x0 + 132, yy)]
    b += [L(x0 + 100, yy, x0 + 100, yy + 24),
          L(x0 + 88, yy + 24, x0 + 112, yy + 24),
          L(x0 + 88, yy + 31, x0 + 112, yy + 31)]
    b += gnd(x0 + 100, yy + 31)
    b += [T(x0 + 138, yy + 4, "IF", 10.5, anchor="start", weight="bold")]
    for i, (txt, col) in enumerate((("one diode - cheapest", "#555"),
                                    ("no port isolation at all;", ACCENT),
                                    ("LO leaks straight to RF and IF", ACCENT),
                                    ("all spur orders present", ACCENT))):
        b += [T(x0, yy + 92 + i * 16, txt, 9.4, anchor="start", fill=col)]

    # ── (b) 단일 평형 ──────────────────────────────────────────
    x0 = 300
    b += [T(x0, y0, "(b) Single-balanced", 12, anchor="start", weight="bold")]
    yy = y0 + 40
    b += transformer(x0 + 44, yy)
    b += [L(x0, yy + 27, x0 + 44, yy + 27),
          T(x0 + 2, yy + 19, "LO", 9.6, anchor="start", fill=AMBER,
            weight="bold")]
    for dy in (0, 54):
        b += [L(x0 + 79, yy + dy, x0 + 104, yy + dy)]
        b += diode(x0 + 104, yy + dy)
        b += [L(x0 + 118, yy + dy, x0 + 152, yy + dy)]
    b += [L(x0 + 152, yy, x0 + 152, yy + 54),
          L(x0 + 152, yy + 27, x0 + 192, yy + 27)]
    b += [T(x0 + 198, yy + 31, "IF", 10.5, anchor="start", weight="bold")]
    b += [L(x0 + 66, yy + 27, x0 + 66, yy + 100)]
    b += [T(x0 + 66, yy + 116, "RF", 10.5, weight="bold", fill=BLUE),
          T(x0 + 74, yy + 88, "(centre tap)", 8.4, anchor="start",
            fill="#777")]
    for i, (txt, col) in enumerate((("a balun drives two diodes", "#555"),
                                    ("in opposite phase, so the LO", "#555"),
                                    ("cancels at the IF port.", GREEN),
                                    ("LO-to-IF isolation: good", GREEN),
                                    ("RF-to-IF isolation: still poor",
                                     ACCENT))):
        b += [T(x0, yy + 146 + i * 16, txt, 9.4, anchor="start", fill=col)]

    # ── (c) 이중 평형 (다이오드 링) ────────────────────────────
    # 링의 네 꼭짓점 중 마주보는 쌍 하나에 LO 발룬이, 나머지 쌍에 RF 발룬이
    # 걸린다. 이 회로는 평면에 교차 없이 그릴 수 없어 점프(hop) 하나가 남는다.
    x0 = 596
    b += [T(x0, y0, "(c) Double-balanced (diode ring)", 12, anchor="start",
            weight="bold")]
    cx, cy, rr = x0 + 200, y0 + 124, 46
    top, right, bot, left = ((cx, cy - rr), (cx + rr, cy), (cx, cy + rr),
                             (cx - rr, cy))
    for a, c2 in ((top, right), (right, bot), (bot, left), (left, top)):
        b += [L(a[0], a[1], c2[0], c2[1], w=2)]
    for (a, c2, ang) in ((top, right, 45), (right, bot, 135),
                         (bot, left, 225), (left, top, 315)):
        b += diode_rot((a[0] + c2[0]) / 2, (a[1] + c2[1]) / 2, ang)

    # LO 발룬 (왼쪽) — 왼쪽/오른쪽 꼭짓점 쌍에 걸린다
    b += transformer(x0 + 40, cy - 27)
    b += [L(x0, cy, x0 + 40, cy),
          T(x0 + 2, cy - 9, "LO", 9.6, anchor="start", fill=AMBER,
            weight="bold")]
    b += [L(x0 + 62, cy + 27, x0 + 62, cy + 48)] + gnd(x0 + 62, cy + 48)
    b += [L(x0 + 75, cy - 27, left[0] - 24, cy - 27),
          L(left[0] - 24, cy - 27, left[0] - 24, cy),
          L(left[0] - 24, cy, left[0], left[1])]
    b += [L(x0 + 75, cy + 27, x0 + 75, cy + rr + 46),
          L(x0 + 75, cy + rr + 46, right[0] + 26, cy + rr + 46),
          L(right[0] + 26, cy + rr + 46, right[0] + 26, cy + rr + 29),
          L(right[0] + 26, cy + rr + 15, right[0] + 26, cy),
          L(right[0] + 26, cy, right[0], right[1])]
    b += hop(right[0] + 26, cy + rr + 22)

    # RF 발룬 (오른쪽) — 위/아래 꼭짓점 쌍에 걸린다
    xr = cx + rr + 56
    b += transformer(xr, cy - 27)
    b += [L(xr, cy - 27, xr - 10, cy - 27),
          L(xr - 10, cy - 27, xr - 10, cy - rr - 26),
          L(xr - 10, cy - rr - 26, top[0], cy - rr - 26),
          L(top[0], cy - rr - 26, top[0], top[1])]
    b += [L(xr, cy + 27, xr - 10, cy + 27),
          L(xr - 10, cy + 27, xr - 10, cy + rr + 22),
          L(xr - 10, cy + rr + 22, bot[0], cy + rr + 22),
          L(bot[0], cy + rr + 22, bot[0], bot[1])]
    b += [L(xr + 35, cy, xr + 68, cy),
          T(xr + 74, cy + 4, "RF", 10.5, anchor="start", fill=BLUE,
            weight="bold")]
    b += [L(xr, cy, xr, cy + rr + 62),
          L(xr, cy + rr + 62, xr + 68, cy + rr + 62),
          T(xr + 74, cy + rr + 66, "IF", 10.5, anchor="start",
            weight="bold"),
          T(xr + 30, cy + rr + 78, "(centre tap)", 8.6, anchor="start",
            fill="#777")]

    for i, (txt, col) in enumerate((("two baluns + four diodes", "#555"),
                                    ("all three ports isolated", GREEN),
                                    ("even-order spurs suppressed", GREEN),
                                    ("needs the most LO drive power",
                                     ACCENT))):
        b += [T(x0, cy + 168 + i * 16, txt, 9.4, anchor="start", fill=col)]
    b += [T(x0, cy + 242, "the small arc is a wire hop: those two wires",
            8.8, anchor="start", fill="#777"),
          T(x0, cy + 256, "cross without touching", 8.8, anchor="start",
            fill="#777")]

    # ── (d) I/Q (이미지 제거) 믹서 ─────────────────────────────
    x0, y0 = 56, 466
    b += [T(x0, y0, "(d) Image-reject (I/Q) mixer", 12, anchor="start",
            weight="bold")]
    yy = y0 + 96
    b += [L(x0, yy, x0 + 34, yy),
          T(x0 + 2, yy - 10, "RF", 9.6, anchor="start", fill=BLUE,
            weight="bold")]
    b += [R(x0 + 34, yy - 40, 58, 80, fill=PANEL, rx=6),
          T(x0 + 63, yy - 5, "in-phase", 9.4), T(x0 + 63, yy + 9, "split", 9.4)]
    for dy, tag, ph in ((-40, "I", "0 deg"), (40, "Q", "90 deg")):
        b += [L(x0 + 92, yy + dy, x0 + 138, yy + dy)]
        b += mixer_sym(x0 + 155, yy + dy)
        b += [L(x0 + 172, yy + dy, x0 + 218, yy + dy)]
        # LO 는 배선을 끌지 않고 짧은 스터브 + 라벨로 표시한다.
        # (두 믹서 사이로 선을 끌면 신호 경로와 교차해 오히려 읽기 나쁘다)
        sy = dy - 30 if dy < 0 else dy + 30
        b += [L(x0 + 155, yy + dy + (-17 if dy < 0 else 17),
                x0 + 155, yy + sy + (9 if dy < 0 else -9), s=AMBER)]
        b += [T(x0 + 155, yy + sy + (4 if dy < 0 else 18),
                f"LO {ph}", 9.4, fill=AMBER, weight="bold")]
        b += [T(x0 + 115, yy + dy - 7 if dy < 0 else yy + dy + 16, tag, 10,
                fill=GREEN, weight="bold")]
    b += [R(x0 + 218, yy - 40, 58, 80, fill=PANEL, rx=6),
          T(x0 + 247, yy - 5, "90 deg", 9.4),
          T(x0 + 247, yy + 9, "combine", 9.4)]
    b += [L(x0 + 276, yy, x0 + 320, yy),
          T(x0 + 326, yy + 4, "IF", 10.5, anchor="start", weight="bold")]
    b += [T(x0 + 155, yy + 108, "the LO is split 0 / 90 deg and fed to the "
                                "two mixers", 9.2, fill="#777")]

    tx = x0 + 400
    for i, (txt, col, sz) in enumerate((
            ("the wanted signal adds in phase; the image cancels.", GREEN,
             10.2),
            ("typical rejection 20-35 dB, set by amplitude and phase balance.",
             "#555", 10.2),
            ("1 deg of phase error, or 0.2 dB of amplitude error,", "#555",
             9.8),
            ("already caps rejection at roughly 40 dB.", "#555", 9.8),
            ("so it does NOT replace the RF filter - it relaxes it.", ACCENT,
             10.2))):
        b += [T(tx, yy - 34 + i * 20, txt, sz, anchor="start", fill=col,
                weight="bold" if col in (GREEN, ACCENT) else "normal")]

    (OUT / "M09").mkdir(parents=True, exist_ok=True)
    (OUT / "M09" / "mixer_types.svg").write_text(
        doc(W, H, "\n".join(b),
            "믹서 구조 4종 — 단일소자, 단일평형, 이중평형, 이미지 제거 믹서"),
        encoding="utf-8")


if __name__ == "__main__":
    mixer_types()
    print("M09 SVG 도해 1종 생성 완료")
