"""M15 손그림 SVG — 측정 셋업도 두 종.

주의: SVG 의 <text> 는 보는 사람의 글꼴로 그려지므로 한글을 넣지 않는다.
설명은 본문 캡션이 맡는다. (<title> 은 화면에 안 그려지므로 예외)

셋업도의 목적은 "이렇게 연결하라" 가 아니라 **"이 부품이 왜 거기 있는가"** 다.
그래서 부품마다 이유를 함께 적는다.
"""
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets/M15"

INK = "#1A1A1A"
BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
RED = "#C0392B"
GREY = "#7F7F7F"
LIGHT = "#EFEFEF"

HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        'viewBox="0 0 {w} {h}" font-family="Helvetica,Arial,sans-serif">'
        '<title>{title}</title><rect width="{w}" height="{h}" fill="white"/>')


def txt(x, y, s, size=11.5, fill=INK, anchor="middle", weight="normal"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def defs():
    return ('<defs>' + "".join(
        f'<marker id="a{n}" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
        for n, c in (("k", INK), ("r", RED), ("g", GREEN), ("b", BLUE)))
            + '</defs>')


def wire(x1, y1, x2, y2, color=INK, w=2.0, mark="k"):
    m = f' marker-end="url(#a{mark})"' if mark else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{w}"{m}/>')


def blk(x, y, w, h, label, sub="", color=INK, fill="white"):
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" '
         f'stroke="{color}" stroke-width="2"/>')
    if sub:
        s += txt(x + w / 2, y + h / 2 - 2, label, 12.5, color, weight="bold")
        s += txt(x + w / 2, y + h / 2 + 15, sub, 10, GREY)
    else:
        s += txt(x + w / 2, y + h / 2 + 5, label, 12.5, color, weight="bold")
    return s


def why(x, y, lines, color=RED, anchor="middle"):
    """부품 밑에 '왜 여기 있는가' 를 적는다."""
    out = ""
    for i, ln in enumerate(lines):
        out += txt(x, y + i * 14, ln, 9.8, color, anchor=anchor)
    return out


# ══════════════════════════════════ 1. Y 계수법 셋업
def yfactor_setup():
    w, h = 1000, 520
    s = [HEAD.format(w=w, h=h, title="Y 계수법 잡음지수 측정 셋업"), defs()]
    s.append(txt(w / 2, 34, "Y-factor noise figure measurement", 16,
                 weight="bold"))

    y0 = 130
    s.append(blk(60, y0 - 34, 150, 68, "NOISE SOURCE", "ENR 15.2 dB", GREEN))
    s.append(wire(210, y0, 300, y0))
    s.append(blk(300, y0 - 34, 150, 68, "DUT", "the amplifier", BLUE))
    s.append(wire(450, y0, 560, y0))
    s.append(blk(560, y0 - 34, 190, 68, "NF ANALYSER", "or SA + preamp", INK))
    s.append(wire(750, y0, 840, y0, mark=None))
    s.append(blk(840, y0 - 22, 110, 44, "READ Y", "", INK, LIGHT))

    s.append(why(135, y0 + 62, [
        "the ENR figure on this",
        "sticker is the root of",
        "the whole measurement",
        "-> keep it calibrated"], GREEN))
    s.append(why(375, y0 + 62, [
        "must be well matched.",
        "the source impedance",
        "changes between hot",
        "and cold states"], BLUE))
    s.append(why(655, y0 + 62, [
        "its own noise figure is",
        "measured first, then",
        "subtracted (second-stage)"], INK))

    # 28 V 펄스 표시
    s.append(f'<path d="M 100,{y0 - 58} l 0,-16 l 22,0 l 0,16 l 22,0 l 0,-16 '
             f'l 22,0" stroke="{GREEN}" stroke-width="2" fill="none"/>')
    s.append(txt(175, y0 - 62, "28 V on / off", 10, GREEN, anchor="start"))

    # 2단계 절차
    y1 = 330
    s.append(f'<line x1="40" y1="{y1 - 34}" x2="960" y2="{y1 - 34}" '
             f'stroke="{GREY}" stroke-width="1" stroke-dasharray="5 4"/>')
    s.append(txt(60, y1 - 8, "STEP 1   calibrate : noise source straight into "
                 "the analyser, no DUT", 12.5, RED, anchor="start",
                 weight="bold"))
    s.append(txt(60, y1 + 12, "         -> gives the analyser's own noise "
                 "figure and gain", 11, GREY, anchor="start"))
    s.append(txt(60, y1 + 46, "STEP 2   measure : put the DUT back in",
                 12.5, RED, anchor="start", weight="bold"))
    s.append(txt(60, y1 + 66, "         -> the analyser subtracts step 1 and "
                 "reports the DUT alone", 11, GREY, anchor="start"))

    s.append(txt(60, y1 + 108, "F = ENR / (Y - 1)          "
                 "Y = (noise out, source hot) / (noise out, source cold)",
                 13, INK, anchor="start", weight="bold"))
    s.append(txt(60, y1 + 134, "a large Y is a comfortable measurement.  "
                 "Y below about 1 dB means the two readings are nearly the "
                 "same and noise takes over.", 11, RED, anchor="start"))
    s.append("</svg>")
    (OUT / "yfactor_setup.svg").write_text("\n".join(s))


# ══════════════════════════════════ 2. 2-tone IP3 셋업
def twotone_setup():
    w, h = 1060, 560
    s = [HEAD.format(w=w, h=h, title="2-tone IP3 측정 셋업"), defs()]
    s.append(txt(w / 2, 34, "Two-tone IP3 setup - every part is there for a reason",
                 16, weight="bold"))

    ya, yb = 110, 210
    for i, (yy, name, f) in enumerate(((ya, "SIGNAL GEN 1", "f1"),
                                       (yb, "SIGNAL GEN 2", "f2"))):
        s.append(blk(40, yy - 26, 130, 52, name, "", INK))
        s.append(wire(170, yy, 220, yy))
        s.append(blk(220, yy - 24, 90, 48, "AMP", "", ORANGE))
        s.append(wire(310, yy, 356, yy))
        s.append(blk(356, yy - 24, 90, 48, "LPF", "", GREEN))
        s.append(wire(446, yy, 492, yy))
        s.append(blk(492, yy - 24, 78, 48, "6 dB", "pad", BLUE))
        s.append(wire(570, yy, 620, yy))
        s.append(txt(105, yy - 36, f, 11, GREY))

    # 합성기
    s.append(blk(620, ya - 26, 110, 152, "COMBINER", "", INK))
    s.append(txt(675, yb + 6, "", 11))
    s.append(wire(730, 160, 790, 160))
    s.append(blk(790, 136, 110, 48, "DUT", "", BLUE))
    s.append(wire(900, 160, 950, 160, mark=None))
    s.append(blk(950, 136, 90, 48, "ATT", "", RED))

    s.append(txt(995, 210, "-> SA", 12, INK, weight="bold"))

    # 왜 그 부품이 있는가
    y2 = 300
    rows = [
        (ORANGE, "AMP",
         "raises the level so the pads and combiner can be afforded"),
        (GREEN, "LPF",
         "generator harmonics as low as -60 dBc still spoil an IM3 reading"),
        (BLUE, "6 dB PAD",
         "the two big reasons a two-tone test goes wrong are generator "
         "interaction and mismatch"),
        (INK, "COMBINER",
         "a tee is not a combiner - it creates mismatch and lets the "
         "generators pull each other"),
        (RED, "ATT before SA",
         "so the analyser is not the thing making the IM3 you are reading"),
    ]
    s.append(txt(50, y2 - 16, "why each part is there", 13, INK,
                 anchor="start", weight="bold"))
    for i, (col, name, note) in enumerate(rows):
        yy = y2 + 12 + i * 30
        s.append(f'<rect x="50" y="{yy - 12}" width="14" height="14" rx="2" '
                 f'fill="{col}"/>')
        s.append(txt(74, yy, name, 11.5, col, anchor="start", weight="bold"))
        s.append(txt(210, yy, note, 11, GREY, anchor="start"))

    s.append(txt(50, y2 + 178,
                 "amp + 6 dB pads + combiner give roughly 70 dB of isolation "
                 "between the two generators.", 11.5, RED, anchor="start",
                 weight="bold"))
    s.append(txt(50, y2 + 200,
                 "check first with the DUT replaced by a through: whatever IM3 "
                 "you still see is the test set's own.", 11.5, RED,
                 anchor="start"))
    s.append("</svg>")
    (OUT / "twotone_setup.svg").write_text("\n".join(s))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    yfactor_setup()
    twotone_setup()
    for f in sorted(OUT.glob("*.svg")):
        print(f"  {f.name}  {f.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
