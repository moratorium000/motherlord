"""M17 손그림 SVG — 스택업, 선로 치수, 리턴 패스, 비아 펜싱, 배치 구획, 실드 캔.

주의: SVG 의 <text> 는 보는 사람의 글꼴로 그려지므로 한글을 넣지 않는다.
설명은 본문 캡션과 표가 맡는다. (<title> 은 화면에 안 그려지므로 예외)
"""
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets/M17"

C0 = 299_792_458.0

INK = "#1A1A1A"
BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
RED = "#C0392B"
YELLOW = "#E69F00"
GREY = "#7F7F7F"
LIGHT = "#F0F0F0"
COPPER = "#B87333"
DIEL = "#DCE9F5"
CORE = "#C7DCEF"

HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        'viewBox="0 0 {w} {h}" font-family="Helvetica,Arial,sans-serif">'
        '<title>{title}</title><rect width="{w}" height="{h}" fill="white"/>')


def esc(s):
    """SVG 는 XML 이라 <, &, > 를 그대로 쓰면 파일이 통째로 안 열린다."""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                  .replace(">", "&gt;"))


def txt(x, y, s, size=11, fill=INK, anchor="middle", weight="normal",
        mono=False):
    fam = ' font-family="Courier,monospace"' if mono else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}"{fam}>'
            f'{esc(s)}</text>')


def defs():
    return ('<defs>' + "".join(
        f'<marker id="a{n}" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
        for n, c in (("k", INK), ("r", RED), ("b", BLUE), ("g", GREEN),
                     ("o", ORANGE), ("y", YELLOW)))
            + '</defs>')


def rect(x, y, w, h, color=INK, fill="white", rx=3, sw=1.5, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{color}" stroke-width="{sw}"{d}/>')


def wire(x1, y1, x2, y2, color=INK, w=1.8, mark="k", dash=None):
    m = f' marker-end="url(#a{mark})"' if mark else ""
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{w}"{d}{m}/>')


def path(d, color=INK, w=1.8, fill="none", mark=None, dash=None):
    m = f' marker-end="url(#a{mark})"' if mark else ""
    ds = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<path d="{d}" fill="{fill}" stroke="{color}" '
            f'stroke-width="{w}"{ds}{m}/>')


def dim(x1, y, x2, label, color=GREY, above=True, size=10):
    """치수선. 양쪽 화살표와 치수 글자."""
    dy = -6 if above else 14
    return "".join([
        f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" '
        f'stroke-width="1.1" marker-start="url(#ak)" marker-end="url(#ak)"/>',
        txt((x1 + x2) / 2, y + dy, label, size, color),
    ])


def circle(cx, cy, r, color=INK, fill="white", sw=1.4):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" '
            f'stroke="{color}" stroke-width="{sw}"/>')


def save(name, body):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.svg").write_text(body + "</svg>")
    return name


# ══════════════════════════════════ 1. 스택업 단면
def stackup():
    w, h = 1180, 640
    s = [HEAD.format(w=w, h=h, title="스택업 단면 - 4층과 하이브리드 6층"), defs()]
    s.append(txt(w / 2, 30, "Stack-up: where the 50 ohm reference plane sits",
                 16, weight="bold"))

    def layers(x0, y0, bw, stack, title, sub):
        """주석은 스택 오른쪽에 붙는다. 다른 요소와 겹치지 않게 폭을 재 둘 것."""
        out = [txt(x0 + bw / 2, y0 - 26, title, 13, weight="bold"),
               txt(x0 + bw / 2, y0 - 9, sub, 10, GREY)]
        y = y0
        for kind, thick, name, note in stack:
            fill = COPPER if kind == "cu" else (CORE if kind == "core" else DIEL)
            out.append(rect(x0, y, bw, thick, INK, fill, rx=0, sw=1.2))
            out.append(txt(x0 + 10, y + thick / 2 + 4, name, 10.5,
                           "white" if kind == "cu" else INK, anchor="start",
                           weight="bold" if kind == "cu" else "normal"))
            if note:
                out.append(wire(x0 + bw + 4, y + thick / 2, x0 + bw + 16,
                                y + thick / 2, GREY, 1.0, mark=None))
                out.append(txt(x0 + bw + 20, y + thick / 2 + 4, note, 9.5,
                               GREY, anchor="start"))
            y += thick
        return out, y

    # 4층 표준 — 주석은 x0+bw+20 부터, 오른쪽 스택 시작(640) 전에 끝나야 한다
    st4 = [("cu", 22, "L1  signal / RF", "50 ohm microstrip"),
           ("pp", 34, "prepreg  0.20 mm", "this gap sets the width"),
           ("cu", 22, "L2  GROUND (solid)", "reference - never split"),
           ("core", 78, "core  1.00 mm", "thick filler"),
           ("cu", 22, "L3  power", ""),
           ("pp", 34, "prepreg  0.20 mm", ""),
           ("cu", 22, "L4  ground / signal", "")]
    body, yend = layers(60, 100, 260, st4, "4-layer, general purpose",
                        "all FR-4, RF on L1")
    s += body
    s.append(dim(60, yend + 28, 320, "board 1.60 mm", GREY, above=False))
    s.append(txt(190, yend + 66, "cheap. the RF layer pays FR-4 loss.",
                 10.5, RED))

    # 하이브리드 6층
    st6 = [("cu", 20, "L1  RF  (Rogers)", "low loss where it matters"),
           ("pp", 26, "RO4350B  0.508 mm", "Dk 3.66   Df 0.0037"),
           ("cu", 20, "L2  GROUND (solid)", "the RF reference plane"),
           ("core", 34, "FR-4 core", "cheap filler - no RF below here"),
           ("cu", 18, "L3  digital", ""),
           ("pp", 24, "FR-4 prepreg", ""),
           ("cu", 18, "L4  power", ""),
           ("core", 34, "FR-4 core", ""),
           ("cu", 18, "L5  ground", ""),
           ("pp", 24, "FR-4 prepreg", ""),
           ("cu", 18, "L6  digital / mech", "")]
    body, yend2 = layers(640, 100, 250, st6, "hybrid 6-layer",
                         "Rogers on top only")
    s += body
    s.append(dim(640, yend2 + 28, 890, "board ~1.6 mm", GREY, above=False))
    s.append(txt(765, yend2 + 66, "RF gets low loss, the rest stays cheap",
                 10.5, GREEN))

    # 아래 규칙 띠
    s.append(rect(60, 470, 1060, 140, BLUE, "#F5F9FD", rx=8, sw=1.8))
    s.append(txt(590, 496, "the two rules that decide a stack-up", 12.5, BLUE,
                 weight="bold"))
    for i, ln in enumerate([
            "1   the layer directly under an RF trace must be a SOLID ground "
            "plane. Not power, not a split plane, not a gap.",
            "2   the L1-L2 dielectric thickness sets the 50 ohm width. "
            "Thin dielectric -> narrow trace -> tighter coupling -> less "
            "radiation and less crosstalk.",
            "",
            "so the usual move is: thin prepreg between L1 and L2, and a "
            "thick core underneath to make up the board thickness."]):
        s.append(txt(84, 522 + i * 22, ln, 10.5,
                     GREY if i == 3 else INK, anchor="start"))
    return save("stackup", "".join(s))


# ══════════════════════════════════ 2. 마이크로스트립 / GCPW 치수
def traces():
    w, h = 1040, 560
    s = [HEAD.format(w=w, h=h, title="마이크로스트립과 GCPW 치수"), defs()]
    s.append(txt(w / 2, 30, "Microstrip vs grounded coplanar waveguide (GCPW)",
                 16, weight="bold"))

    # ── 마이크로스트립
    x0, y0 = 70, 90
    s.append(txt(x0 + 180, y0 - 12, "microstrip", 13, weight="bold"))
    s.append(rect(x0, y0 + 40, 360, 60, INK, DIEL, rx=0, sw=1.2))
    s.append(rect(x0, y0 + 100, 360, 14, INK, COPPER, rx=0, sw=1.2))
    s.append(rect(x0 + 150, y0 + 26, 60, 14, INK, COPPER, rx=0, sw=1.2))
    s.append(txt(x0 + 180, y0 + 20, "W", 11, ORANGE, weight="bold"))
    s.append(dim(x0 + 150, y0 + 12, x0 + 210, "", ORANGE))
    s.append(txt(x0 + 400, y0 + 70, "h", 11, BLUE, weight="bold", anchor="start"))
    s.append(f'<line x1="{x0+380}" y1="{y0+40}" x2="{x0+380}" y2="{y0+100}" '
             f'stroke="{BLUE}" stroke-width="1.1" marker-start="url(#ab)" '
             f'marker-end="url(#ab)"/>')
    s.append(txt(x0 + 180, y0 + 111, "GROUND", 10, "white", weight="bold"))
    # 전기력선
    for dx, sweep in ((-1, 0), (1, 1)):
        s.append(path(f"M {x0+180+dx*24} {y0+30} "
                      f"Q {x0+180+dx*110} {y0+42} {x0+180+dx*105} {y0+100}",
                      GREEN, 1.2, dash="4 3"))
    s.append(txt(x0 + 180, y0 + 200,
                 "some field goes through air -> Dk_eff is below Dk", 10,
                 GREEN))
    s.append(txt(x0 + 180, y0 + 152,
                 "RO4350B  h = 0.508 mm  ->  W = 1.12 mm", 11, INK,
                 weight="bold"))
    s.append(txt(x0 + 180, y0 + 170, "easy to build, easy to probe", 10, GREY))

    # ── GCPW
    # 그리는 순서가 중요하다: 유전체 -> 비아 -> 구리 -> 글자.
    # 비아를 구리 위에 그리면 GND 글자가 비아에 잘려 "G D" 처럼 보인다.
    x1 = 600
    s.append(txt(x1 + 180, y0 - 12, "GCPW  (grounded coplanar waveguide)", 13,
                 weight="bold"))
    s.append(rect(x1, y0 + 40, 360, 60, INK, DIEL, rx=0, sw=1.2))
    for vx in (x1 + 62, x1 + 92, x1 + 122, x1 + 238, x1 + 268, x1 + 298):
        s.append(f'<rect x="{vx-4}" y="{y0+26}" width="8" height="88" '
                 f'fill="{COPPER}" stroke="{INK}" stroke-width="0.9"/>')
    s.append(rect(x1, y0 + 100, 360, 14, INK, COPPER, rx=0, sw=1.2))
    s.append(rect(x1 + 40, y0 + 26, 100, 14, INK, COPPER, rx=0, sw=1.2))
    s.append(rect(x1 + 220, y0 + 26, 100, 14, INK, COPPER, rx=0, sw=1.2))
    s.append(rect(x1 + 168, y0 + 26, 24, 14, INK, COPPER, rx=0, sw=1.2))
    # 치수와 이름은 구리 바깥에
    s.append(txt(x1 + 90, y0 + 18, "GND pour", 10, GREY))
    s.append(txt(x1 + 270, y0 + 18, "GND pour", 10, GREY))
    s.append(txt(x1 + 180, y0 + 66, "W", 11, ORANGE, weight="bold"))
    s.append(dim(x1 + 168, y0 + 52, x1 + 192, "", ORANGE))
    s.append(txt(x1 + 154, y0 + 66, "G", 11, RED, weight="bold"))
    s.append(txt(x1 + 206, y0 + 66, "G", 11, RED, weight="bold"))
    s.append(dim(x1 + 140, y0 + 52, x1 + 168, "", RED))
    s.append(dim(x1 + 192, y0 + 52, x1 + 220, "", RED))
    s.append(txt(x1 + 180, y0 + 111, "GROUND", 10, "white", weight="bold"))
    s.append(txt(x1 + 180, y0 + 134, "stitching vias tie the pours to the "
                 "plane below", 9.5, GREY))
    # 전기력선: 트레이스에서 옆 접지로 짧게
    s.append(path(f"M {x1+166} {y0+30} Q {x1+152} {y0+16} {x1+140} {y0+30}",
                  GREEN, 1.6))
    s.append(path(f"M {x1+194} {y0+30} Q {x1+208} {y0+16} {x1+220} {y0+30}",
                  GREEN, 1.6))
    s.append(txt(x1 + 180, y0 + 200, "field is trapped in the gap - "
                 "that is why GCPW isolates better", 10, GREEN))
    s.append(txt(x1 + 180, y0 + 152,
                 "50 ohm comes from W and G together", 11, INK, weight="bold"))
    s.append(txt(x1 + 180, y0 + 170,
                 "no stitching vias -> it is not GCPW, it is a slot", 10, RED))

    # ── 언제 무엇을
    s.append(rect(70, 320, 900, 130, INK, LIGHT, rx=8, sw=1.6))
    s.append(txt(520, 344, "which one", 12, weight="bold"))
    rows = [("microstrip",
             "below ~6 GHz, plenty of room, components sit on the line",
             "fewer vias, forgiving to build"),
            ("GCPW",
             "above ~6 GHz, dense layout, next to a noisy block, IC fan-out",
             "needs the side ground AND the stitching vias to work")]
    for i, (a, b, c) in enumerate(rows):
        y = 370 + i * 38
        s.append(txt(96, y, a, 11.5, BLUE, anchor="start", weight="bold"))
        s.append(txt(210, y, b, 10.5, INK, anchor="start"))
        s.append(txt(210, y + 15, c, 10, GREY, anchor="start"))

    s.append(txt(520, 470,
                 "the gap G matters as much as the width W - change one and "
                 "the impedance moves", 11, RED, weight="bold"))
    s.append(txt(520, 496,
                 "never copy a GCPW dimension without its gap and its via pitch",
                 10.5, GREY))
    return save("traces", "".join(s))


# ══════════════════════════════════ 3. 리턴 패스
PLANE_TINT = "#EBCBA9"      # 구리를 옅게. 진한 구리색 위에서는 글자가 안 읽힌다.


def returnpath():
    """위에서 내려다본 그림으로 그린다.

    단면으로 그리면 '되돌아오는 전류가 옆으로 우회한다'는 핵심이 안 보인다.
    루프가 커지는 것은 보드 평면 안에서 벌어지는 일이다.
    """
    w, h = 1060, 580
    s = [HEAD.format(w=w, h=h, title="리턴 패스 - 정상과 단절"), defs()]
    s.append(txt(w / 2, 30, "The return current, seen from above", 16,
                 weight="bold"))
    s.append(txt(w / 2, 52, "every signal current comes back. the only "
                 "question is by which route.", 11, GREY))

    bw, bh = 430, 276
    y0 = 82

    def frame(x0, title, good):
        col = GREEN if good else RED
        return [rect(x0, y0, bw, bh, col, "#FAFCFA" if good else "#FDF6F5",
                     rx=8, sw=2.2),
                txt(x0 + bw / 2, y0 - 10, title, 13, col, weight="bold"),
                rect(x0 + 24, y0 + 34, bw - 48, 168, COPPER, PLANE_TINT,
                     rx=2, sw=1.6)]

    # ── 정상: 연속 접지면
    x0 = 50
    s += frame(x0, "solid ground plane", True)
    s.append(txt(x0 + bw / 2, y0 + 52, "GROUND PLANE  (layer 2, seen through "
                 "the board)", 9.5, GREY))
    ytr = y0 + 112
    s.append(wire(x0 + 44, ytr, x0 + bw - 44, ytr, BLUE, 4.0, mark="b"))
    s.append(path(f"M {x0+bw-44} {ytr+9} L {x0+44} {ytr+9}", ORANGE, 3.0,
                  mark="o", dash="7 4"))
    s.append(txt(x0 + bw / 2, ytr - 12, "signal, layer 1", 10.5, BLUE,
                 weight="bold"))
    s.append(txt(x0 + bw / 2, ytr + 28, "return, layer 2, right underneath",
                 10.5, ORANGE, weight="bold"))
    s.append(txt(x0 + bw / 2, ytr + 76,
                 "no loop area worth speaking of", 10.5, INK, weight="bold"))
    s.append(txt(x0 + bw / 2, y0 + 228,
                 "the two currents lie on top of each other, 0.2 mm apart.",
                 10, INK))
    s.append(txt(x0 + bw / 2, y0 + 248,
                 "the loop they enclose is a thin ribbon - it barely radiates.",
                 10, GREEN, weight="bold"))

    # ── 단절: 슬롯이 가로지른다
    x1 = 580
    s += frame(x1, "the plane is split", False)
    s.append(txt(x1 + 40, y0 + 52, "GROUND PLANE with a SLOT", 9.5, GREY,
                 anchor="start"))
    ytr = y0 + 112
    # 우회가 감싸는 면적을 먼저 칠한다 (선 아래로 가게)
    s.append(f'<rect x="{x1+100}" y="{ytr}" width="230" height="56" '
             f'fill="{RED}" opacity="0.17"/>')
    # 슬롯: 접지면을 위에서 잘라 내려오다 중간에서 끝난다
    s.append(f'<rect x="{x1+206}" y="{y0+34}" width="16" height="130" '
             f'fill="white" stroke="{RED}" stroke-width="1.8" '
             f'stroke-dasharray="5 4"/>')
    s.append(txt(x1 + 214, y0 + 26, "slot", 10, RED, weight="bold"))
    s.append(wire(x1 + 44, ytr, x1 + bw - 44, ytr, BLUE, 4.0, mark="b"))
    s.append(path(f"M {x1+bw-44} {ytr+9} L {x1+330} {ytr+9} "
                  f"L {x1+330} {ytr+52} L {x1+100} {ytr+52} "
                  f"L {x1+100} {ytr+9} L {x1+44} {ytr+9}",
                  ORANGE, 3.0, mark="o", dash="7 4"))
    s.append(txt(x1 + bw / 2, ytr - 12, "signal crosses the slot", 10.5, BLUE,
                 weight="bold"))
    s.append(txt(x1 + 152, ytr + 34, "loop area", 10, RED, weight="bold"))
    s.append(txt(x1 + bw / 2, ytr + 78, "the return goes round the slot end",
                 10.5, ORANGE, weight="bold"))
    s.append(txt(x1 + bw / 2, y0 + 228,
                 "the loop now encloses real area.", 10, INK))
    s.append(txt(x1 + bw / 2, y0 + 248,
                 "that area is an antenna - it radiates out, and it picks up.",
                 10, RED, weight="bold"))

    # ── 결론
    s.append(rect(50, 396, 960, 138, INK, LIGHT, rx=8, sw=1.6))
    s.append(txt(530, 422, "the rule that saves the most boards", 12.5,
                 weight="bold"))
    for i, ln in enumerate([
            "1   every RF trace needs an UNBROKEN reference plane directly "
            "beneath it, along its whole length.",
            "2   do not split the ground plane. A split is a slot, and a slot "
            "the signal has to jump is a slot antenna.",
            "3   when a signal changes layer, put a GROUND via right next to "
            "the signal via - the return needs a way through too.",
            "4   the same applies to a plane broken by a row of connector "
            "holes, or by a wide gap between two pours."]):
        s.append(txt(74, 448 + i * 22, ln, 10.5, INK, anchor="start"))
    return save("returnpath", "".join(s))


# ══════════════════════════════════ 4. 비아 펜싱
def viafence():
    w, h = 1040, 590
    s = [HEAD.format(w=w, h=h, title="비아 펜싱과 스티칭 - 간격 규칙"), defs()]
    s.append(txt(w / 2, 30, "Via fencing: how close is close enough?", 16,
                 weight="bold"))

    # 평면도
    x0, y0, bw, bh = 60, 70, 560, 250
    s.append(rect(x0, y0, bw, bh, INK, "#F7F7F7", rx=6, sw=1.6))
    s.append(txt(x0 + bw / 2, y0 - 10, "top view", 12, GREY))
    # RF 선로
    s.append(rect(x0 + 40, y0 + 118, bw - 80, 14, INK, COPPER, rx=0, sw=1.2))
    s.append(txt(x0 + bw / 2, y0 + 112, "RF trace", 10.5, ORANGE,
                 weight="bold"))
    # 위쪽 촘촘한 펜스
    for i in range(11):
        s.append(circle(x0 + 60 + i * 44, y0 + 74, 7, INK, COPPER))
    s.append(dim(x0 + 60, y0 + 52, x0 + 104, "s", GREEN))
    s.append(txt(x0 + bw / 2, y0 + 36,
                 "good: s = lambda/20 or less", 11, GREEN, weight="bold"))
    # 아래쪽 성긴 펜스
    for i in range(4):
        s.append(circle(x0 + 70 + i * 140, y0 + 178, 7, INK, COPPER))
    s.append(dim(x0 + 70, y0 + 200, x0 + 210, "s", RED, above=True))
    s.append(txt(x0 + bw / 2, y0 + 232,
                 "bad: the gap is a slot - energy leaks through it", 11, RED,
                 weight="bold"))
    # 누설 표시
    # 누설은 비아 사이 빈 곳에서 새어 나간다
    s.append(path(f"M {x0+420} {y0+178} L {x0+420} {y0+206}",
                  RED, 1.8, dash="4 3", mark="r"))
    s.append(txt(x0 + 432, y0 + 200, "leaks out here", 9.5, RED,
                 weight="bold", anchor="start"))

    # 단면도
    x1, y1 = 660, 70
    s.append(rect(x1, y1, 320, 250, INK, "#F7F7F7", rx=6, sw=1.6))
    s.append(txt(x1 + 160, y1 - 10, "side view", 12, GREY))
    s.append(rect(x1 + 30, y1 + 60, 260, 90, INK, DIEL, rx=0, sw=1.2))
    s.append(rect(x1 + 30, y1 + 46, 260, 14, INK, COPPER, rx=0, sw=1.2))
    s.append(rect(x1 + 30, y1 + 150, 260, 14, INK, COPPER, rx=0, sw=1.2))
    s.append(txt(x1 + 160, y1 + 40, "top ground pour", 10, GREY))
    s.append(txt(x1 + 160, y1 + 176, "ground plane", 10, GREY))
    for vx in range(x1 + 60, x1 + 280, 44):
        s.append(f'<rect x="{vx-4}" y="{y1+46}" width="8" height="118" '
                 f'fill="{COPPER}" stroke="{INK}" stroke-width="1"/>')
    s.append(txt(x1 + 160, y1 + 210,
                 "the vias make the two coppers", 10.5, INK))
    s.append(txt(x1 + 160, y1 + 226,
                 "ONE ground, not two", 10.5, GREEN, weight="bold"))

    # 계산
    s.append(rect(60, 350, 920, 190, BLUE, "#F5F9FD", rx=8, sw=1.8))
    s.append(txt(520, 376, "working out the spacing", 12.5, BLUE,
                 weight="bold"))
    s.append(txt(88, 400, "lambda_g = c / (f * sqrt(Dk_eff))", 11, INK,
                 anchor="start", mono=True))
    s.append(txt(430, 400, "s = lambda_g / 20", 11, GREEN, anchor="start",
                 mono=True, weight="bold"))
    hdr = ["material", "Dk_eff", "2.45 GHz: lambda_g", "s (= /20)",
           "5.8 GHz: lambda_g", "s (= /20)"]
    cols = [96, 250, 370, 560, 680, 880]
    for c, hh in zip(cols, hdr):
        s.append(txt(c, 428, hh, 10.5, GREY, anchor="start", weight="bold"))
    rows = [("FR-4", "3.27", "67.7 mm", "3.38 mm", "28.6 mm", "1.43 mm"),
            ("RO4350B", "2.85", "72.4 mm", "3.62 mm", "30.6 mm", "1.53 mm"),
            ("PTFE", "1.87", "89.4 mm", "4.47 mm", "37.8 mm", "1.89 mm")]
    for i, r in enumerate(rows):
        for c, v in zip(cols, r):
            s.append(txt(c, 450 + i * 21, v, 10.5, INK, anchor="start",
                         mono=(c != 96)))
    s.append(txt(88, 524,
                 "higher Dk -> shorter wavelength -> vias must be CLOSER. "
                 "Above 3 GHz many designers use lambda/40.",
                 10.5, RED, anchor="start"))
    return save("viafence", "".join(s))


# ══════════════════════════════════ 5. 배치 구획
def floorplan():
    w, h = 1040, 620
    s = [HEAD.format(w=w, h=h, title="배치 구획 - RF / 디지털 / 전원 분리"), defs()]
    s.append(txt(w / 2, 30, "Floor plan: decide this before you route "
                 "a single trace", 16, weight="bold"))

    x0, y0, bw, bh = 60, 60, 700, 420
    s.append(rect(x0, y0, bw, bh, INK, "#FCFCFC", rx=8, sw=2.2))
    s.append(txt(x0 + 12, y0 + 18, "board outline", 10, GREY, anchor="start"))

    def zone(x, y, ww, hh, name, sub, col, fill):
        return [rect(x, y, ww, hh, col, fill, rx=6, sw=1.8),
                txt(x + ww / 2, y + 20, name, 11.5, col, weight="bold"),
                txt(x + ww / 2, y + 37, sub, 9.5, GREY)]

    # RF 구역
    s += zone(x0 + 20, y0 + 40, 300, 200, "RF FRONT END",
              "antenna - filter - LNA/PA - mixer", ORANGE, "#FDF3EC")
    for i, (nm, xx, yy) in enumerate([("ANT", 40, 100), ("FILT", 110, 100),
                                      ("LNA", 180, 100), ("MIX", 250, 100)]):
        s.append(rect(x0 + xx - 26, y0 + yy, 52, 30, INK, "white", rx=3))
        s.append(txt(x0 + xx, y0 + yy + 20, nm, 10, INK, weight="bold"))
        if i:
            s.append(wire(x0 + xx - 70 + 26, y0 + yy + 15, x0 + xx - 26,
                          y0 + yy + 15, ORANGE, 2.0, mark="o"))
    s.append(txt(x0 + 170, y0 + 168, "signal flows in ONE direction", 10,
                 ORANGE, weight="bold"))
    s.append(txt(x0 + 170, y0 + 186, "no folding back on itself", 9.5, GREY))
    s.append(txt(x0 + 170, y0 + 210, "keep this whole block on solid ground",
                 9.5, GREY))

    # 디지털
    s += zone(x0 + 360, y0 + 40, 310, 200, "DIGITAL",
              "MCU - clock - memory - USB", BLUE, "#EEF4FA")
    s.append(txt(x0 + 515, y0 + 120, "clock harmonics live here", 10, BLUE))
    s.append(txt(x0 + 515, y0 + 142, "they will find your RF band", 10, RED,
                 weight="bold"))
    s.append(txt(x0 + 515, y0 + 176, "route clocks AWAY from the boundary",
                 9.5, GREY))
    s.append(txt(x0 + 515, y0 + 194, "never over the RF ground", 9.5, GREY))

    # 전원
    s += zone(x0 + 20, y0 + 262, 650, 130, "POWER",
              "connector - protection - regulators - bulk caps", GREEN,
              "#EFF7F3")
    s.append(txt(x0 + 345, y0 + 322,
                 "feed each block on its own branch: "
                 "RF rail and digital rail never share a via", 10, INK))
    s.append(txt(x0 + 345, y0 + 344,
                 "ferrite bead or LDO between the noisy rail and the quiet one",
                 10, GREY))
    s.append(txt(x0 + 345, y0 + 368,
                 "star the returns at ONE point, or use one plane and never "
                 "cut it", 10, GREY))

    # 경계선
    s.append(path(f"M {x0+345} {y0+40} L {x0+345} {y0+240}", RED, 2.4,
                  dash="7 5"))
    s.append(txt(x0 + 345, y0 + 30, "the boundary", 10.5, RED, weight="bold"))

    # 오른쪽 규칙
    s.append(rect(790, 60, 190, 420, INK, LIGHT, rx=8, sw=1.6))
    s.append(txt(885, 84, "order of work", 12, weight="bold"))
    for i, ln in enumerate([
            "1  antenna position",
            "    (it decides the rest)", "",
            "2  RF chain, straight",
            "    line, shortest path", "",
            "3  the boundary between",
            "    RF and digital", "",
            "4  power entry and",
            "    regulators", "",
            "5  connectors and",
            "    mounting holes", "",
            "6  everything else",
            "", "",
            "moving a part later",
            "costs ten times more",
            "than placing it right"]):
        s.append(txt(806, 110 + i * 17.5, ln, 10,
                     RED if i >= 17 else INK, anchor="start",
                     weight="bold" if i >= 17 else "normal"))

    s.append(txt(w / 2, 520,
                 "the single most common failure: the RF block sits next to "
                 "the switching regulator", 11.5, RED, weight="bold"))
    s.append(txt(w / 2, 546,
                 "a buck converter at 2 MHz has harmonics that reach far past "
                 "1 GHz - give it distance and its own return", 10.5, GREY))
    s.append(txt(w / 2, 578,
                 "and keep a clear keep-out around the antenna: no copper, "
                 "no parts, no metal shell", 10.5, GREY))
    return save("floorplan", "".join(s))


# ══════════════════════════════════ 6. 실드 캔
def shieldcan():
    w, h = 1040, 500
    s = [HEAD.format(w=w, h=h, title="실드 캔 단면과 흡수체"), defs()]
    s.append(txt(w / 2, 30, "Shield cans: what they fix, and what they break",
                 16, weight="bold"))

    x0, y0 = 80, 90
    s.append(rect(x0, y0 + 140, 400, 16, INK, COPPER, rx=0, sw=1.2))
    s.append(txt(x0 + 200, y0 + 202, "PCB, ground plane under the can frame",
                 10, GREY))
    # 캔
    s.append(path(f"M {x0+40} {y0+140} L {x0+40} {y0+40} L {x0+360} {y0+40} "
                  f"L {x0+360} {y0+140}", GREY, 4.0))
    s.append(txt(x0 + 200, y0 + 8, "shield can (soldered frame + lid)", 11,
                 INK, weight="bold"))
    # 접지 납땜점
    for vx in range(x0 + 40, x0 + 380, 40):
        s.append(circle(vx, y0 + 142, 5, INK, GREEN))
    s.append(txt(x0 + 200, y0 + 182,
                 "solder to ground every < lambda/20, same rule as vias", 10,
                 GREEN, weight="bold"))
    # 안의 회로
    for i, nm in enumerate(["LNA", "MIX", "VCO"]):
        s.append(rect(x0 + 70 + i * 100, y0 + 92, 62, 34, INK, "white", rx=3))
        s.append(txt(x0 + 101 + i * 100, y0 + 114, nm, 10, INK, weight="bold"))
    # 공동 공진
    s.append(path(f"M {x0+60} {y0+70} Q {x0+200} {y0+56} {x0+340} {y0+70}",
                  RED, 2.0, dash="6 4"))
    s.append(txt(x0 + 345, y0 + 84, "cavity resonance", 10, RED,
                 weight="bold", anchor="end"))
    # 흡수체
    s.append(f'<rect x="{x0+60}" y="{y0+44}" width="280" height="12" '
             f'fill="{YELLOW}" stroke="{INK}" stroke-width="1"/>')
    s.append(txt(x0 + 200, y0 + 26, "absorber sheet on the lid inside", 10,
                 YELLOW, weight="bold"))

    # 계산 상자
    s.append(rect(540, 90, 430, 250, BLUE, "#F5F9FD", rx=8, sw=1.8))
    s.append(txt(755, 116, "the can itself resonates", 12.5, BLUE,
                 weight="bold"))
    s.append(txt(560, 142,
                 "f_res = (c / 2) * sqrt((m/a)^2 + (n/b)^2)", 11, INK,
                 anchor="start", mono=True))
    s.append(txt(560, 160, "lowest mode is m = n = 1;  a, b = inside "
                 "length and width", 10, GREY, anchor="start"))
    # 숫자는 손으로 적지 않고 여기서 계산한다. 처음에 손으로 적었다가
    # 세 줄 중 두 줄이 틀렸다.
    for i, (a_mm, b_mm) in enumerate([(30, 20), (60, 45), (100, 75)]):
        f1 = (C0 / 2) * ((1 / (a_mm / 1000)) ** 2
                         + (1 / (b_mm / 1000)) ** 2) ** 0.5
        hit = 2.40e9 <= f1 <= 2.50e9
        s.append(txt(575, 190 + i * 22, f"a = {a_mm} mm, b = {b_mm} mm", 10.5,
                     INK, anchor="start", mono=True))
        s.append(txt(800, 190 + i * 22, f"-> {f1/1e9:.2f} GHz", 10.5,
                     RED if hit else INK, anchor="start", mono=True))
    s.append(txt(560, 274,
                 "the 100 x 75 mm can resonates inside the 2.4 GHz band.",
                 10.5, RED, anchor="start", weight="bold"))
    s.append(txt(560, 292,
                 "fixes: make it smaller, split it with an internal wall,",
                 10.5, INK, anchor="start"))
    s.append(txt(560, 310,
                 "or put absorber on the lid. Measure before and after.",
                 10.5, INK, anchor="start"))

    # 아래 정리
    s.append(rect(80, 370, 890, 106, INK, LIGHT, rx=8, sw=1.6))
    s.append(txt(525, 394, "before you reach for a can", 12, weight="bold"))
    for i, ln in enumerate([
            "a can fixes RADIATED coupling. It does nothing for coupling "
            "through the power rail or through a shared ground.",
            "a can with too few ground contacts is worse than none - the "
            "gaps become slots.",
            "a can traps heat. Check the power amplifier temperature after "
            "you fit it."]):
        s.append(txt(104, 418 + i * 20, ln, 10.5,
                     RED if i == 1 else INK, anchor="start"))
    return save("shieldcan", "".join(s))


if __name__ == "__main__":
    import xml.etree.ElementTree as ET
    for fn in (stackup, traces, returnpath, viafence, floorplan, shieldcan):
        name = fn()
        p = OUT / f"{name}.svg"
        ET.parse(p)          # XML 로 열리는지 바로 확인한다
        print(f"  {p.relative_to(OUT.parent.parent)}  "
              f"({p.stat().st_size/1024:.1f} KB)  XML OK")
