#!/usr/bin/env python3
"""
Part I (M02, M03) 손그림 SVG 도해 생성기
========================================

데이터 플롯이 아니라 '설명 그림'이다. Matplotlib으로는 어색한 회로도·단면도를
직접 SVG로 그린다.

규약(설계서 §8.3, 2단계 확정 사항):
  * SVG 안에 한글을 넣지 않는다 → 보는 사람 PC에 한글 폰트가 없으면 깨진다.
    한글 설명은 마크다운 캡션과 그림 옆 표에 쓴다.
    다만 접근성용 <title> 에는 한글을 넣는다(화면에 그려지지 않음).
  * 배경 흰색 명시, 선 색 #1a1a1a 통일.

    python3 scripts/gen_svg_part1.py
"""

from pathlib import Path

INK = "#1a1a1a"
ACCENT = "#c0392b"
BLUE = "#0072B2"
GREEN = "#009E73"
COPPER = "#D9A066"
DIEL = "#CFE3F0"
BG = "#ffffff"
FONT = "font-family='DejaVu Sans, Helvetica, Arial, sans-serif'"

OUT = Path(__file__).resolve().parent.parent / "assets"


def doc(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" role="img" aria-label="{title}">\n'
            f'  <title>{title}</title>\n'
            f'  <rect width="{w}" height="{h}" fill="{BG}"/>\n'
            f'{body}\n</svg>\n')


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


def P(d, s=INK, sw=2, fill="none", dash=None):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'  <path d="{d}" fill="{fill}" stroke="{s}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round"{da}/>')


def T(x, y, s, size=11, anchor="middle", fill=INK, weight="normal",
      style="normal"):
    return (f'  <text x="{x}" y="{y}" {FONT} font-size="{size}" '
            f'text-anchor="{anchor}" fill="{fill}" font-weight="{weight}" '
            f'font-style="{style}">{s}</text>')


def arrow_defs():
    return ('  <defs>\n'
            f'    <marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">\n'
            f'      <path d="M 0 0 L 10 5 L 0 10 z" fill="{ACCENT}"/>\n'
            '    </marker>\n'
            f'    <marker id="ab" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">\n'
            f'      <path d="M 0 0 L 10 5 L 0 10 z" fill="{BLUE}"/>\n'
            '    </marker>\n'
            '  </defs>')


# ───────────────────────────────────────────── M02: 전송선 등가회로
def tline_equivalent():
    """분포정수 등가회로. 셀 2개면 '반복된다'는 뜻이 충분히 전달된다."""
    W, H = 760, 300
    y_top, y_bot = 96, 216
    b = [arrow_defs(),
         T(W / 2, 28, "Distributed model of a transmission line", 13,
           weight="bold"),
         T(W / 2, 48, "one cell = one short section of length dz  "
                      "(the pattern repeats)", 10, fill="#666")]

    cell_w = 250
    x_start = 60
    b += [L(20, y_top, x_start, y_top), L(20, y_bot, x_start, y_bot)]

    for k in range(2):
        x = x_start + k * cell_w
        # 직렬 R
        b += [R(x, y_top - 12, 46, 24), T(x + 23, y_top - 22, "R dz", 10)]
        # 직렬 L (코일 4개)
        d = f"M {x+62} {y_top}"
        for _ in range(4):
            d += " a 9 9 0 0 1 18 0"
        b += [L(x + 46, y_top, x + 62, y_top), P(d),
              T(x + 98, y_top - 22, "L dz", 10),
              L(x + 134, y_top, x + 158, y_top)]
        # 병렬 G (좌)
        gx = x + 158
        b += [L(gx, y_top, gx, y_top + 36), R(gx - 13, y_top + 36, 26, 44),
              L(gx, y_top + 80, gx, y_bot),
              T(gx - 22, y_top + 62, "G dz", 10, anchor="end")]
        # 병렬 C (우) — G 와 충분히 떨어뜨려 라벨이 겹치지 않게 한다
        cx = x + 216
        b += [L(gx, y_top, cx, y_top),
              L(cx, y_top, cx, y_top + 48),
              L(cx - 16, y_top + 48, cx + 16, y_top + 48),
              L(cx - 16, y_top + 62, cx + 16, y_top + 62),
              L(cx, y_top + 62, cx, y_bot),
              T(cx + 24, y_top + 60, "C dz", 10, anchor="start")]
        # 아래 도체(귀환 경로)를 끊김 없이 잇는다
        b += [L(gx, y_bot, cx, y_bot)]
        b += [L(x, y_bot, gx, y_bot)]
        if k == 0:
            b += [L(cx, y_top, x + cell_w, y_top),
                  L(cx, y_bot, x + cell_w, y_bot)]

    x_end = x_start + cell_w + 216
    b += [L(x_end, y_top, W - 30, y_top), L(x_end, y_bot, W - 30, y_bot),
          L(W - 30, y_top, W - 30, y_bot, INK, 2, "5 4"),
          T(W - 36, y_top - 14, "to the load", 9, anchor="middle",
            fill="#666")]

    # dz 구간 표시 (한 셀의 폭)
    yb = y_bot + 34
    b += [L(x_start, yb, x_start + cell_w, yb, ACCENT, 1.5),
          L(x_start, yb - 6, x_start, yb + 6, ACCENT, 1.5),
          L(x_start + cell_w, yb - 6, x_start + cell_w, yb + 6, ACCENT, 1.5),
          T(x_start + cell_w / 2, yb - 10, "one cell = dz", 10, fill=ACCENT,
            weight="bold")]

    b += [T(W / 2, H - 30, "Z0 = sqrt( (R + jwL) / (G + jwC) )", 13,
            weight="bold", fill=BLUE),
          T(W / 2, H - 10, "lossless line  (R = 0, G = 0):   Z0 = sqrt( L / C )", 11, fill=BLUE)]
    (OUT / "M02").mkdir(parents=True, exist_ok=True)
    (OUT / "M02" / "tline_equivalent.svg").write_text(
        doc(W, H, "\n".join(b),
            "전송선로의 분포정수 등가회로: 직렬 R·L 과 병렬 G·C 가 반복된다"),
        encoding="utf-8")


# ───────────────────────────────────────────── M02: 전송선 단면도
def cross_sections():
    b = [T(440, 26, "Transmission line cross sections", 13, weight="bold")]

    # 1) 동축
    ox, oy = 108, 150
    b += [C(ox, oy, 52, DIEL), C(ox, oy, 52, "none", INK, 2.5),
          C(ox, oy, 12, COPPER, INK, 2),
          T(ox, oy + 5, "S", 11, weight="bold"),
          T(ox, 56, "Coaxial", 12, weight="bold"),
          T(ox, oy + 78, "shield fully surrounds signal", 9, fill="#666"),
          T(ox, oy + 91, "no radiation", 9, fill="#666")]
    b += [L(ox, oy, ox + 52, oy, ACCENT, 1.4, "4 3"),
          T(ox + 30, oy - 8, "D/d", 9, fill=ACCENT)]

    # 2) 마이크로스트립
    mx, my = 320, 160
    b += [T(mx + 60, 56, "Microstrip", 12, weight="bold"),
          R(mx, my - 40, 120, 40, DIEL, INK, 1.6),
          R(mx, my, 120, 10, COPPER, INK, 1.6),
          R(mx + 44, my - 52, 32, 12, COPPER, INK, 1.6),
          T(mx + 60, my + 30, "ground plane below only", 9, fill="#666"),
          T(mx + 60, my + 43, "fields partly in air", 9, fill="#666"),
          T(mx + 60, my - 60, "W", 10),
          L(mx + 128, my - 40, mx + 128, my, ACCENT, 1.3),
          T(mx + 140, my - 16, "h", 10, fill=ACCENT)]
    b += [P(f"M {mx+52} {my-40} q 10 -22 -22 -22", "#9ab", 1.2, dash="3 2"),
          P(f"M {mx+68} {my-40} q -10 -22 22 -22", "#9ab", 1.2, dash="3 2")]

    # 3) 스트립라인
    sx, sy = 520, 160
    b += [T(sx + 60, 56, "Stripline", 12, weight="bold"),
          R(sx, sy - 78, 120, 88, DIEL, INK, 1.6),
          R(sx, sy, 120, 10, COPPER, INK, 1.6),
          R(sx, sy - 88, 120, 10, COPPER, INK, 1.6),
          R(sx + 44, sy - 40, 32, 10, COPPER, INK, 1.6),
          T(sx + 60, sy + 30, "buried between two grounds", 9, fill="#666"),
          T(sx + 60, sy + 43, "no radiation, but no probing", 9, fill="#666")]

    # 4) GCPW
    gx, gy = 700, 160
    b += [T(gx + 60, 56, "Grounded CPW", 12, weight="bold"),
          R(gx, gy - 40, 120, 40, DIEL, INK, 1.6),
          R(gx, gy, 120, 10, COPPER, INK, 1.6),
          R(gx + 50, gy - 52, 20, 12, COPPER, INK, 1.6),
          R(gx - 2, gy - 52, 38, 12, COPPER, INK, 1.6),
          R(gx + 84, gy - 52, 38, 12, COPPER, INK, 1.6),
          T(gx + 60, gy + 30, "ground beside AND below", 9, fill="#666"),
          T(gx + 60, gy + 43, "better isolation at mmWave", 9, fill="#666")]
    for vx in (gx + 14, gx + 26, gx + 96, gx + 108):
        b += [R(vx - 3, gy - 40, 6, 40, COPPER, INK, 1.0)]

    b += [T(440, 258, "S = signal conductor,   brown = copper,   "
            "blue = dielectric substrate", 10, fill="#666")]
    (OUT / "M02" / "cross_sections.svg").write_text(
        doc(880, 272, "\n".join(b),
            "전송선로 단면 비교: 동축, 마이크로스트립, 스트립라인, 접지형 코플래너 도파관"),
        encoding="utf-8")


# ───────────────────────────────────────────── M03: 2포트 진행파
def twoport_waves():
    b = [arrow_defs()]
    b += [T(330, 26, "Two-port network: incident and reflected waves", 13,
            weight="bold")]

    bx, by, bw, bh = 230, 80, 200, 110
    b += [R(bx, by, bw, bh, "#F4F7FA", INK, 2.5, rx=6),
          T(bx + bw / 2, by + 52, "DUT", 20, weight="bold"),
          T(bx + bw / 2, by + 76, "2-port", 11, fill="#666")]

    b += [L(60, by + 40, bx, by + 40), L(bx + bw, by + 40, 600, by + 40)]
    b += [T(60, by - 4, "Port 1", 12, anchor="start", weight="bold"),
          T(600, by - 4, "Port 2", 12, anchor="end", weight="bold")]

    # a1 (입사), b1 (반사)
    b += [P(f"M 80 {by+14} L 200 {by+14}", ACCENT, 2.4) +
          '', ]
    b[-1] = (f'  <path d="M 80 {by+14} L 200 {by+14}" fill="none" '
             f'stroke="{ACCENT}" stroke-width="2.4" marker-end="url(#ah)"/>')
    b += [T(140, by + 4, "a1  incident", 11, fill=ACCENT, weight="bold")]

    b += [(f'  <path d="M 200 {by+70} L 80 {by+70}" fill="none" '
           f'stroke="{BLUE}" stroke-width="2.4" marker-end="url(#ab)"/>')]
    b += [T(140, by + 88, "b1  reflected", 11, fill=BLUE, weight="bold")]

    b += [(f'  <path d="M 460 {by+70} L 580 {by+70}" fill="none" '
           f'stroke="{BLUE}" stroke-width="2.4" marker-end="url(#ab)"/>')]
    b += [T(520, by + 88, "b2  transmitted", 11, fill=BLUE, weight="bold")]

    b += [(f'  <path d="M 580 {by+14} L 460 {by+14}" fill="none" '
           f'stroke="{ACCENT}" stroke-width="2.4" marker-end="url(#ah)"/>')]
    b += [T(520, by + 4, "a2  incident", 11, fill=ACCENT, weight="bold")]

    b += [T(180, 240, "b1 = S11 a1 + S12 a2", 14, weight="bold", fill=INK),
          T(480, 240, "b2 = S21 a1 + S22 a2", 14, weight="bold", fill=INK)]
    b += [T(330, 262,
            "S11 = b1/a1  and  S21 = b2/a1   are measured with  a2 = 0 "
            "(port 2 terminated in Z0)", 10, fill="#666")]
    (OUT / "M03").mkdir(parents=True, exist_ok=True)
    (OUT / "M03" / "twoport_waves.svg").write_text(
        doc(660, 280, "\n".join(b),
            "2포트 회로망의 진행파 정의: 입사파 a와 반사파 b, 그리고 S-파라미터"),
        encoding="utf-8")


if __name__ == "__main__":
    tline_equivalent()
    cross_sections()
    twoport_waves()
    print("SVG 도해 3종 생성 완료")
