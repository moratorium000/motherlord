#!/usr/bin/env python3
"""
M13 (디지털 변조와 신호 품질) 손그림 SVG 도해 생성기
====================================================

규약: SVG 안에 한글을 넣지 않는다. 한글 설명은 마크다운 캡션에 쓴다.

    python3 scripts/gen_svg_m13.py
"""

import math
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
                      ("ak", INK), ("aa", AMBER)):
        out.append(
            f'    <marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{col}"/></marker>')
    out.append('  </defs>')
    return "\n".join(out)


# ═══════════════════════════════ M13-2: EVM 벡터의 정의
def evm_vector():
    W, H = 940, 470
    b = [defs(), T(W / 2, 32, "What the error vector actually is", 14,
                   weight="bold")]

    ox, oy = 300, 300           # 원점
    sc = 1.0
    b += [P(f"M {ox-40} {oy} L {ox+230} {oy}", s="#999", sw=1.4,
            marker="ak"),
          T(ox + 244, oy + 4, "I", 12, anchor="start", weight="bold"),
          P(f"M {ox} {oy+40} L {ox} {oy-230}", s="#999", sw=1.4,
            marker="ak"),
          T(ox - 4, oy - 244, "Q", 12, anchor="middle", weight="bold")]
    for g in range(1, 5):
        b += [L(ox + g * 46, oy - 4, ox + g * 46, oy + 4, s="#BBB", w=1),
              L(ox - 4, oy - g * 46, ox + 4, oy - g * 46, s="#BBB", w=1)]

    # 오차를 눈에 보이게 하려고 실제보다 훨씬 크게 그린다.
    rx_, ry = ox + 150, oy - 150          # 이상적인 기준 심볼
    mx, my = ox + 208, oy - 96            # 실제로 측정된 심볼
    b += [P(f"M {ox} {oy} L {rx_} {ry}", s=BLUE, sw=2.6, marker="ab")]
    b += [C(rx_, ry, 5.5, fill=BLUE, s=BLUE)]
    b += [T(rx_ - 60, ry - 26, "ideal symbol", 10.5, anchor="middle",
            fill=BLUE, weight="bold"),
          T(rx_ - 60, ry - 12, "(reference)", 9.6, anchor="middle",
            fill=BLUE)]
    b += [L(rx_ - 34, ry - 20, rx_ - 8, ry - 6, s=BLUE, w=1.1)]

    b += [P(f"M {ox} {oy} L {mx} {my}", s=INK, sw=2.6, marker="ak")]
    b += [C(mx, my, 5.5, fill=INK, s=INK)]
    b += [T(mx + 6, my + 36, "measured symbol", 10.5, anchor="middle",
            fill=INK, weight="bold")]
    b += [L(mx + 2, my + 24, mx, my + 10, s=INK, w=1.1)]

    b += [P(f"M {rx_} {ry} L {mx} {my}", s=ACCENT, sw=3.2, marker="ar")]
    b += [T(rx_ + 86, ry - 22, "error vector", 11.5, anchor="middle",
            fill=ACCENT, weight="bold")]
    b += [L(rx_ + 70, ry - 14, rx_ + 34, ry + 16, s=ACCENT, w=1.1)]

    # 성분 분해 (진폭 오차 / 위상 오차)
    b += [L(mx, my, mx, ry, s=ACCENT, w=1.3, dash="4 3"),
          L(rx_, ry, mx, ry, s=ACCENT, w=1.3, dash="4 3")]
    b += [T((rx_ + mx) / 2, ry - 8, "magnitude error", 9.4, fill=ACCENT),
          T(mx + 10, (ry + my) / 2 + 4, "phase error", 9.4, anchor="start",
            fill=ACCENT)]
    b += [T(ox + 100, oy + 34,
            "(the error is drawn much larger than it really is)", 9.2,
            anchor="middle", fill="#888")]

    # 정의 상자
    bx, by = 600, 96
    b += [R(bx, by, 300, 250, fill=PANEL, s="#C9D4DE", sw=1.4, rx=8)]
    lines = [
        ("EVM of one symbol", INK, 11, True),
        ("|error vector| / |reference|", INK, 10.4, False),
        ("", INK, 6, False),
        ("EVM (RMS) over many symbols", INK, 11, True),
        ("sqrt( mean |err|^2 / mean |ref|^2 )", INK, 10.4, False),
        ("", INK, 6, False),
        ("in dB", GREEN, 11, True),
        ("EVM[dB] = 20 log10( EVM )", GREEN, 10.4, False),
        ("", INK, 6, False),
        ("and therefore", ACCENT, 11, True),
        ("SNR[dB] = - EVM[dB]", ACCENT, 11.6, True),
    ]
    yy = by + 30
    for txt, col, sz, bold in lines:
        if txt:
            b += [T(bx + 18, yy, txt, sz, anchor="start", fill=col,
                    weight="bold" if bold else "normal")]
        yy += sz + 8

    b += [T(bx + 150, by + 268,
            "the reference is what SHOULD have been sent", 9.6, fill="#666")]

    b += [T(W / 2, H - 42,
            "Beware: some instruments normalise by the AVERAGE power, "
            "others by the PEAK.", 10.6, fill=ACCENT, weight="bold")]
    b += [T(W / 2, H - 22,
            "For 64-QAM the peak-normalised number is about 3.7 dB smaller. "
            "Always check which one a datasheet quotes.", 10, fill="#555")]

    (OUT / "M13").mkdir(parents=True, exist_ok=True)
    (OUT / "M13" / "evm_vector.svg").write_text(
        doc(W, H, "\n".join(b), "오차 벡터(EVM)의 정의와 성분 분해"),
        encoding="utf-8")


if __name__ == "__main__":
    evm_vector()
    print("M13 SVG 도해 1종 생성 완료")
