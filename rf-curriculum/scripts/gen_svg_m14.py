"""M14 손그림 SVG — 신호 흐름 그래프, 오차 모델, 교정 표준, 기준면.

주의: SVG 의 <text> 는 **보는 사람의 글꼴**로 그려진다. 한글을 넣으면 한글
글꼴이 없는 환경에서 네모로 깨지므로, 이 파일의 <text> 에는 ASCII 만 쓴다.
한글 설명은 본문 캡션이 맡는다. (<title> 은 화면에 안 그려지므로 예외)
"""
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets/M14"

INK = "#1A1A1A"
BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
RED = "#C0392B"
GREY = "#7F7F7F"
LIGHT = "#EDEDED"

HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" '
        'width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        'font-family="Helvetica,Arial,sans-serif">'
        '<title>{title}</title>'
        '<rect width="{w}" height="{h}" fill="white"/>')


def txt(x, y, s, size=12, fill=INK, anchor="middle", weight="normal",
        style="normal"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" '
            f'font-style="{style}">{s}</text>')


def arrow_defs():
    return ('<defs>'
            + "".join(
                f'<marker id="a{n}" viewBox="0 0 10 10" refX="9" refY="5" '
                f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
                for n, c in (("k", INK), ("b", BLUE), ("o", ORANGE),
                             ("g", GREEN), ("r", RED)))
            + '</defs>')


def line(x1, y1, x2, y2, color=INK, w=1.6, mark=None, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#a{mark})"' if mark else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{w}" fill="none"{d}{m}/>')


def box(x, y, w, h, color=INK, fill="white", rx=4, sw=1.8):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{color}" stroke-width="{sw}"/>')


def node(cx, cy, r=7, color=INK):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="white" stroke="{color}" stroke-width="2"/>'


# ══════════════════════════════════ 1. 신호 흐름 그래프 (1-포트 오차 모델)
def signal_flow():
    w, h = 1000, 430
    s = [HEAD.format(w=w, h=h, title="1포트 오차 모델의 신호 흐름 그래프"),
         arrow_defs()]
    s.append(txt(w / 2, 34, "One-port error model as a signal flow graph",
                 size=16, weight="bold"))

    xs = {"a0": 210, "b0": 210, "a1": 620, "b1": 620}
    ys = {"a0": 130, "b0": 290, "a1": 130, "b1": 290}
    for k in xs:
        s.append(node(xs[k], ys[k]))
        s.append(txt(xs[k], ys[k] + 4, k, size=11, weight="bold"))

    s.append(line(220, 130, 610, 130, BLUE, 2.0, "b"))
    s.append(txt(415, 118, "e10   incident reaches the DUT", size=12, fill=BLUE))
    s.append(line(610, 290, 220, 290, BLUE, 2.0, "b"))
    s.append(txt(415, 312, "e01   the return reaches the receiver", size=12,
                 fill=BLUE))

    # e00 : 방향성 (왼쪽 바깥)
    s.append(f'<path d="M 205,140 Q 150,210 205,280" stroke="{RED}" '
             f'stroke-width="2.4" fill="none" marker-end="url(#ar)"/>')
    s.append(txt(105, 196, "e00", size=15, fill=RED, weight="bold"))
    s.append(txt(105, 216, "DIRECTIVITY", size=10, fill=RED))
    s.append(txt(105, 234, "leaks straight across", size=9.5, fill=RED))
    s.append(txt(105, 248, "and never sees", size=9.5, fill=RED))
    s.append(txt(105, 262, "the DUT at all", size=9.5, fill=RED))

    # e11 : 소스 정합 (두 노드 사이 안쪽) — 설명은 그림 아래로 뺀다
    s.append(f'<path d="M 630,280 Q 690,210 630,140" stroke="{ORANGE}" '
             f'stroke-width="2.4" fill="none" marker-end="url(#ao)"/>')
    s.append(txt(706, 206, "e11", size=15, fill=ORANGE, weight="bold",
                 anchor="start"))

    # DUT
    s.append(line(630, 130, 800, 130, GREY, 1.4, dash="3 3"))
    s.append(line(630, 290, 800, 290, GREY, 1.4, dash="3 3"))
    s.append(f'<path d="M 800,130 Q 890,210 800,290" stroke="{GREEN}" '
             f'stroke-width="3" fill="none" marker-end="url(#ag)"/>')
    s.append(txt(905, 200, "GAMMA", size=14, fill=GREEN, weight="bold",
                 anchor="start"))
    s.append(txt(905, 220, "the DUT", size=10, fill=GREEN, anchor="start"))
    s.append(txt(905, 236, "what we want", size=10, fill=GREEN, anchor="start"))

    s.append(txt(w / 2, 358,
                 "e11  SOURCE MATCH : the analyser is not a perfect 50 ohm, "
                 "so whatever comes back is sent in again", size=11.5,
                 fill=ORANGE))
    s.append(txt(w / 2, 396,
                 "measured = e00 + (e10 e01) x GAMMA / (1 - e11 x GAMMA)",
                 size=13.5, weight="bold"))
    s.append("</svg>")
    (OUT / "signal_flow.svg").write_text("\n".join(s))


# ══════════════════════════════════ 2. 12항 오차 모델
def twelve_term():
    w, h = 980, 500
    s = [HEAD.format(w=w, h=h, title="2포트 12항 오차 모델"), arrow_defs()]
    s.append(txt(w / 2, 32, "The twelve error terms, drawn where they happen",
                 size=16, weight="bold"))

    for row, (name, col, y0) in enumerate(
            (("FORWARD   source drives port 1", BLUE, 58),
             ("REVERSE   source drives port 2", ORANGE, 268))):
        s.append(box(30, y0, 920, 190, col, "white", rx=8, sw=1.6))
        s.append(txt(52, y0 + 24, name, size=13, fill=col, anchor="start",
                     weight="bold"))
        yc = y0 + 96
        p1, p2 = (150, 830) if row == 0 else (830, 150)
        s.append(box(430, yc - 26, 130, 52, INK, LIGHT))
        s.append(txt(495, yc + 5, "DUT", size=15, weight="bold"))
        s.append(line(p1, yc, 426 if row == 0 else 564, yc, INK, 1.8, "k"))
        s.append(line(564 if row == 0 else 426, yc, p2, yc, INK, 1.8, "k"))
        s.append(txt(p1, yc - 42, "PORT 1" if row == 0 else "PORT 2",
                     size=11, weight="bold"))
        s.append(txt(p2, yc - 42, "PORT 2" if row == 0 else "PORT 1",
                     size=11, weight="bold"))

        drive, term = (p1, p2) if row == 0 else (p1, p2)
        # 구동 쪽: 방향성 · 소스 정합 · 반사 추적
        s.append(txt(drive, yc + 44, "directivity", size=10, fill=col))
        s.append(txt(drive, yc + 60, "source match", size=10, fill=col))
        s.append(txt(drive, yc + 76, "reflection tracking", size=10, fill=col))
        # 받는 쪽: 부하 정합 · 전송 추적
        s.append(txt(term, yc + 44, "load match", size=10, fill=col))
        s.append(txt(term, yc + 60, "transmission tracking", size=10, fill=col))
        # 누설: DUT 를 건너뛴다
        s.append(f'<path d="M {drive},{yc - 30} Q 495,{y0 + 34} {term},{yc - 30}" '
                 f'stroke="{RED}" stroke-width="1.6" fill="none" '
                 f'stroke-dasharray="5 3" marker-end="url(#ar)"/>')
        s.append(txt(495, y0 + 46, "isolation  (crosstalk that skips the DUT)",
                     size=10, fill=RED))

    s.append(txt(w / 2, 482,
                 "six terms per direction = twelve.  Isolation is often left "
                 "out when the crosstalk sits far below the DUT signal.",
                 size=11.5, fill=GREY))
    s.append("</svg>")
    (OUT / "twelve_term.svg").write_text("\n".join(s))


# ══════════════════════════════════ 3. 교정 표준의 물리적 모습
def standards():
    w, h = 940, 430
    s = [HEAD.format(w=w, h=h, title="SOLT 와 TRL 의 교정 표준"), arrow_defs()]
    s.append(txt(w / 2, 32, "What the standards physically are", size=16,
                 weight="bold"))

    def conn(x, y):
        """동축 커넥터 모양."""
        return (box(x, y - 16, 26, 32, INK, LIGHT, rx=3, sw=1.5)
                + line(x + 26, y, x + 46, y, INK, 2.2))

    # SOLT
    s.append(box(30, 60, 430, 340, BLUE, "white", rx=8, sw=1.6))
    s.append(txt(50, 86, "SOLT   coaxial, standards fully known", size=13,
                 fill=BLUE, anchor="start", weight="bold"))
    rows = [("SHORT", "GAMMA = -1", 130), ("OPEN", "GAMMA = +1", 200),
            ("LOAD", "GAMMA = 0", 270), ("THRU", "S21 = 1", 340)]
    for nm, val, y in rows:
        s.append(txt(70, y + 4, nm, size=12, anchor="start", weight="bold"))
        s.append(conn(150, y))
        if nm == "SHORT":
            s.append(line(196, y - 18, 196, y + 18, INK, 4))
        elif nm == "OPEN":
            s.append(line(196, y - 10, 196, y + 10, GREY, 1.4, dash="3 3"))
            s.append(txt(214, y + 4, "gap", size=9.5, fill=GREY, anchor="start"))
        elif nm == "LOAD":
            s.append(box(190, y - 16, 30, 32, INK, LIGHT, rx=2, sw=1.5))
            s.append(txt(205, y + 5, "50", size=10))
        else:
            s.append(line(196, y, 240, y, INK, 2.2))
            s.append(conn(266, y))
        s.append(txt(330, y + 4, val, size=11, fill=GREY, anchor="start"))
    s.append(txt(50, 386, "each one is defined in the cal-kit file",
                 size=10.5, fill=GREY, anchor="start"))

    # TRL
    s.append(box(480, 60, 430, 340, GREEN, "white", rx=8, sw=1.6))
    s.append(txt(500, 86, "TRL   on a board, standards only partly known",
                 size=13, fill=GREEN, anchor="start", weight="bold"))
    trl = [("THRU", 130, 120), ("REFLECT", 210, 40), ("LINE", 300, 220)]
    for nm, y, length in trl:
        s.append(txt(520, y + 4, nm, size=12, anchor="start", weight="bold"))
        s.append(box(610, y - 14, length, 28, INK, LIGHT, rx=2, sw=1.4))
        s.append(line(600, y, 610, y, INK, 2))
        if nm == "REFLECT":
            s.append(line(650, y - 16, 650, y + 16, RED, 3.5))
            s.append(txt(672, y + 4, "open or short - value need not be known",
                         size=9.5, fill=RED, anchor="start"))
        else:
            s.append(line(610 + length, y, 620 + length, y, INK, 2))
    s.append(txt(520, 344, "LINE must differ from THRU by 20 to 160 degrees",
                 size=10.5, fill=GREEN, anchor="start"))
    s.append(txt(520, 364, "-> one line covers only an 8:1 band",
                 size=10.5, fill=GREEN, anchor="start"))
    s.append(txt(520, 386, "impedance of the line becomes the reference",
                 size=10.5, fill=GREY, anchor="start"))
    s.append("</svg>")
    (OUT / "standards.svg").write_text("\n".join(s))


# ══════════════════════════════════ 4. 기준면 이동
def reference_plane():
    w, h = 1020, 430
    s = [HEAD.format(w=w, h=h, title="기준면 이동 - 포트 익스텐션과 디임베딩"),
         arrow_defs()]
    s.append(txt(w / 2, 32, "Where is the reference plane?", size=16,
                 weight="bold"))

    for i, (label, col, y0, note) in enumerate((
            ("after calibration", GREY, 110,
             "plane sits at the cal standards"),
            ("port extension", ORANGE, 220,
             "delay only - loss and mismatch stay"),
            ("de-embedding", GREEN, 330,
             "the whole fixture is removed"))):
        s.append(txt(40, y0 + 6, label, size=12.5, fill=col, anchor="start",
                     weight="bold"))
        s.append(line(200, y0, 300, y0, INK, 2.4))
        s.append(box(300, y0 - 20, 130, 40, INK, LIGHT, rx=3, sw=1.5))
        s.append(txt(365, y0 + 5, "FIXTURE", size=11))
        s.append(line(430, y0, 500, y0, INK, 2.4))
        s.append(box(500, y0 - 24, 110, 48, BLUE, "white", rx=4, sw=2))
        s.append(txt(555, y0 + 5, "DUT", size=13, weight="bold"))
        s.append(line(610, y0, 690, y0, INK, 2.4))

        plane_x = 300 if i == 0 else 500
        s.append(line(plane_x, y0 - 44, plane_x, y0 + 44, col, 2.6,
                      dash="6 4"))
        s.append(txt(plane_x, y0 - 52, "reference plane", size=10, fill=col,
                     weight="bold"))
        s.append(txt(700, y0 + 5, note, size=10, fill=GREY, anchor="start"))

    s.append(txt(40, 404,
                 "quick test: extend the port, then measure a SHORT at the DUT "
                 "plane.  If it is not 180 deg +/- 2, extension was not enough.",
                 size=11, fill=RED, anchor="start"))
    s.append("</svg>")
    (OUT / "reference_plane.svg").write_text("\n".join(s))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    signal_flow()
    twelve_term()
    standards()
    reference_plane()
    for f in sorted(OUT.glob("*.svg")):
        print(f"  {f.name}  {f.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
