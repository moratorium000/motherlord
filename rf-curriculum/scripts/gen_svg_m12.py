#!/usr/bin/env python3
"""
M12 (시스템 예산 설계) 손그림 SVG 도해 생성기
=============================================

규약: SVG 안에 한글을 넣지 않는다. 한글 설명은 마크다운 캡션에 쓴다.

    python3 scripts/gen_svg_m12.py
"""

from pathlib import Path

INK = "#1a1a1a"
ACCENT = "#c0392b"
BLUE = "#0072B2"
GREEN = "#009E73"
AMBER = "#E69F00"
PANEL = "#F4F7FA"
HEAD = "#E7EEF5"
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


def P(d, s=INK, sw=2, fill="none", dash=None, marker=None):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    mk = f' marker-end="url(#{marker})"' if marker else ""
    return (f'  <path d="{d}" fill="{fill}" stroke="{s}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round"{da}{mk}/>')


def T(x, y, s, size=11, anchor="middle", fill=INK, weight="normal",
      family=None):
    fam = family or FONT
    return (f'  <text x="{x}" y="{y}" {fam} font-size="{size}" '
            f'text-anchor="{anchor}" fill="{fill}" font-weight="{weight}">'
            f'{s}</text>')


MONO = "font-family='DejaVu Sans Mono, Consolas, monospace'"


def defs():
    out = ['  <defs>']
    for name, col in (("ar", ACCENT), ("ab", BLUE), ("ag", GREEN),
                      ("aa", AMBER)):
        out.append(
            f'    <marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{col}"/></marker>')
    out.append('  </defs>')
    return "\n".join(out)


# ═══════════════════════════ M12-1: 캐스케이드 예산표 양식
COLS = [("stage", 150), ("gain", 66), ("NF", 60), ("IIP3", 66),
        ("cum gain", 76), ("cum NF", 70), ("cum IIP3", 76)]

# 이 값들은 손으로 적지 말고 gen_fig_m12.py 의 계산 결과와 반드시 일치시킬 것.
# (초판에서 손으로 적었다가 누적 NF·IIP3 네 칸이 실제 계산과 어긋났다.)
ROWS = [
    ("cable + switch", "-0.5", "0.5", "(100)", "-0.5", "0.50", "(100)"),
    ("RF band filter", "-1.0", "1.0", "(100)", "-1.5", "1.50", "97.23"),
    ("LNA", "+22.0", "0.8", "+15.0", "+20.5", "2.30", "16.50"),
    ("band filter", "-2.5", "2.5", "(100)", "+18.0", "2.32", "16.50"),
    ("mixer", "-7.0", "7.0", "+18.0", "+11.0", "2.48", "-0.10"),
    ("IF filter", "-3.0", "3.0", "(100)", "+8.0", "2.67", "-0.10"),
    ("IF amplifier", "+25.0", "4.0", "+10.0", "+33.0", "3.20", "-2.18"),
]


def budget_table():
    W, H = 840, 604
    b = [defs(), T(W / 2, 32, "The cascade budget sheet - what each column is "
                              "for", 14, weight="bold")]

    x0, y0 = 56, 96
    rh = 30
    xs, x = [], x0
    for _, w in COLS:
        xs.append(x)
        x += w
    tw = x - x0

    # 머리글
    b += [R(x0, y0, tw, rh, fill=HEAD, s=INK, sw=1.6)]
    for (name, w), xx in zip(COLS, xs):
        b += [T(xx + w / 2, y0 + 20, name, 10.4, weight="bold")]
        if xx > x0:
            b += [L(xx, y0, xx, y0 + rh + len(ROWS) * rh, s="#C9D4DE", w=1)]

    # 본문
    for i, row in enumerate(ROWS):
        yy = y0 + rh + i * rh
        if i % 2:
            b += [R(x0, yy, tw, rh, fill="#FAFCFE", s="none", sw=0)]
        for (name, w), xx, val in zip(COLS, xs, row):
            anch = "start" if name == "stage" else "end"
            px = xx + 10 if name == "stage" else xx + w - 10
            col = INK
            if name.startswith("cum"):
                col = BLUE
            if val.startswith("("):
                col = "#9AA7B4"
            b += [T(px, yy + 20, val, 10.0, anchor=anch, fill=col,
                    weight="bold" if name.startswith("cum") else "normal",
                    family=None if name == "stage" else MONO)]
        b += [L(x0, yy, x0 + tw, yy, s="#DDE5EC", w=1)]
    b += [R(x0, y0, tw, rh * (len(ROWS) + 1), fill="none", s=INK, sw=1.6)]

    # 마지막 줄 강조
    yl = y0 + rh * len(ROWS)
    b += [R(xs[4], yl, tw - (xs[4] - x0), rh, fill="none", s=ACCENT, sw=2.2)]

    # 마지막 줄을 가리키는 화살표
    cx = xs[4] + (tw - (xs[4] - x0)) / 2
    b += [P(f"M {cx} {yl + rh + 6} L {cx} {yl + rh + 26}", s=ACCENT, sw=1.8,
            marker="ar")]
    b += [T(cx, yl + rh + 42, "the last row IS the system spec", 10.6,
            fill=ACCENT, weight="bold")]

    # 열의 성격 주석
    ny = yl + rh + 70
    b += [T(x0, ny, "input columns", 10.4, anchor="start", fill=INK,
            weight="bold"),
          T(x0 + 118, ny, "measured, or taken from the datasheet - "
                          "one row per part", 9.8, anchor="start",
            fill="#555")]
    b += [T(x0, ny + 18, "cumulative columns", 10.4, anchor="start", fill=BLUE,
            weight="bold"),
          T(x0 + 148, ny + 18, "computed by the three formulas below", 9.8,
            anchor="start", fill="#555")]

    fy = ny + 40
    b += [R(x0, fy, tw, 132, fill=PANEL, s="#C9D4DE", sw=1.4, rx=6)]
    b += [T(x0 + 16, fy + 24, "All three run on LINEAR ratios, not dB. "
                              "Convert first, convert back at the end.",
            9.8, anchor="start", fill=ACCENT, weight="bold")]
    forms = [
        ("cumulative gain", "G = G1 x G2 x ...", INK),
        ("cumulative noise factor",
         "F = F1 + (F2-1)/G1 + (F3-1)/(G1 G2) + ...", GREEN),
        ("cumulative IIP3",
         "1/IIP3 = 1/IIP3_1 + G1/IIP3_2 + (G1 G2)/IIP3_3 + ...", ACCENT),
    ]
    for i, (head, body, col) in enumerate(forms):
        yy = fy + 52 + i * 28
        b += [T(x0 + 16, yy, head, 9.8, anchor="start", fill=col,
                weight="bold"),
              T(x0 + 176, yy, body, 9.8, anchor="start", fill=INK,
                family=MONO)]

    b += [T(x0, H - 18,
            "(100) means the part is passive, so its IIP3 is effectively "
            "infinite - it never limits linearity.", 9.6, anchor="start",
            fill="#777")]

    (OUT / "M12").mkdir(parents=True, exist_ok=True)
    (OUT / "M12" / "budget_table.svg").write_text(
        doc(W, H, "\n".join(b), "캐스케이드 예산표 양식과 세 가지 누적 공식"),
        encoding="utf-8")


if __name__ == "__main__":
    budget_table()
    print("M12 SVG 도해 1종 생성 완료")
