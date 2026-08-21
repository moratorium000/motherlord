"""캡스톤 손그림 SVG — 트랜시버 블록도, 산출물 지도.

주의: SVG 의 <text> 는 보는 사람의 글꼴로 그려지므로 한글을 넣지 않는다.
설명은 본문 캡션과 표가 맡는다. (<title> 은 화면에 안 그려지므로 예외)
"""
import pathlib
import xml.etree.ElementTree as ET

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets/Capstone"

INK = "#1A1A1A"
BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
RED = "#C0392B"
YELLOW = "#E69F00"
GREY = "#7F7F7F"
LIGHT = "#F0F0F0"

HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        'viewBox="0 0 {w} {h}" font-family="Helvetica,Arial,sans-serif">'
        '<title>{title}</title><rect width="{w}" height="{h}" fill="white"/>')


def esc(s):
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
                     ("o", ORANGE))) + '</defs>')


def rect(x, y, w, h, color=INK, fill="white", rx=4, sw=1.6, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{color}" stroke-width="{sw}"{d}/>')


def wire(x1, y1, x2, y2, color=INK, w=2.0, mark="k", dash=None):
    m = f' marker-end="url(#a{mark})"' if mark else ""
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{w}"{d}{m}/>')


def path(d, color=INK, w=2.0, fill="none", mark=None, dash=None):
    m = f' marker-end="url(#a{mark})"' if mark else ""
    ds = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<path d="{d}" fill="{fill}" stroke="{color}" '
            f'stroke-width="{w}"{ds}{m}/>')


def save(name, body):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{name}.svg"
    p.write_text(body + "</svg>")
    ET.parse(p)                      # XML 로 열리는지 바로 확인한다
    print(f"  {p.relative_to(OUT.parent.parent)}  "
          f"({p.stat().st_size / 1024:.1f} KB)  XML OK")
    return name


# ══════════════════════════════════ 1. 트랜시버 블록도
def transceiver():
    w, h = 1180, 620
    s = [HEAD.format(w=w, h=h, title="2.4 GHz 송수신 겸용 트랜시버 블록도"),
         defs()]
    s.append(txt(w / 2, 30, "2.4 GHz half-duplex transceiver - what you are "
                 "building", 16, weight="bold"))
    s.append(txt(w / 2, 52, "the numbers under each block are what YOUR budget "
                 "must fill in", 10.5, GREY))

    bw, bh = 96, 46

    def blk(x, y, name, sub, col=INK, fill="white"):
        return [rect(x, y, bw, bh, col, fill),
                txt(x + bw / 2, y + 20, name, 11, col, weight="bold"),
                txt(x + bw / 2, y + 36, sub, 9, GREY)]

    # ── 안테나와 T/R 스위치
    ax, ay = 60, 285
    s.append(path(f"M {ax+18} {ay} L {ax+18} {ay-26} M {ax+2} {ay-26} "
                  f"L {ax+34} {ay-26} M {ax+6} {ay-34} L {ax+30} {ay-34}",
                  INK, 2.2))
    s.append(txt(ax + 18, ay + 18, "ANT", 10.5, INK, weight="bold"))
    s.append(txt(ax + 18, ay + 32, "2 dBi", 9, GREY))
    s += blk(ax + 60, ay - 23, "T/R SW", "IL 1.0 dB", INK, "#F7F7F7")
    s.append(wire(ax + 36, ay, ax + 60, ay))

    # ── 수신 경로 (위)
    ry = 150
    rx0 = ax + 60 + bw + 34
    s.append(rect(rx0 - 18, ry - 40, 830, 118, BLUE, "#F5F9FD", rx=8, sw=1.8))
    s.append(txt(rx0 + 396, ry - 22, "RECEIVE", 12, BLUE, weight="bold"))
    rxb = [("BPF", "IL 1.5 dB"), ("LNA", "G 22 / NF 0.9"),
           ("BPF", "IL 1.5 dB"), ("MIXER", "G 8 / NF 10"),
           ("LPF", "IL 1.0 dB"), ("VGA", "G 30 / NF 15"),
           ("ADC", "-> baseband")]
    x = rx0
    for i, (n, sub) in enumerate(rxb):
        col = ORANGE if n in ("LNA", "VGA") else INK
        s += blk(x, ry, n, sub, col, "white" if col == INK else "#FDF3EC")
        if i:
            s.append(wire(x - 34, ry + bh / 2, x, ry + bh / 2, BLUE, 2.0, "b"))
        x += bw + 34
    s.append(path(f"M {ax+60+bw} {ay-8} L {rx0-26} {ay-8} L {rx0-26} {ry+bh/2} "
                  f"L {rx0} {ry+bh/2}", BLUE, 2.2, mark="b"))
    s.append(txt(rx0 + 200, ry + 96,
                 "AGC switches the LNA in and out - that is how NF and IIP3",
                 10, ORANGE, weight="bold"))
    s.append(txt(rx0 + 200, ry + 112, "are met in different modes", 10,
                 ORANGE, weight="bold"))

    # ── 송신 경로 (아래)
    ty = 420
    s.append(rect(rx0 - 18, ty - 40, 830, 118, GREEN, "#EFF7F3", rx=8, sw=1.8))
    s.append(txt(rx0 + 396, ty - 22, "TRANSMIT", 12, GREEN, weight="bold"))
    txb = [("HPF", "IL 1.5 dB"), ("PA", "P1dB +32"),
           ("DRIVER", "G 20 dB"), ("MOD", "I/Q up-conv"),
           ("LPF", "reconstruct"), ("DAC", "<- baseband"), ("", "")]
    x = rx0
    for i, (n, sub) in enumerate(txb):
        if not n:
            break
        col = ORANGE if n == "PA" else INK
        s += blk(x, ty, n, sub, col, "white" if col == INK else "#FDF3EC")
        if i:
            s.append(wire(x, ty + bh / 2, x - 34, ty + bh / 2, GREEN, 2.0, "g"))
        x += bw + 34
    s.append(path(f"M {rx0} {ty+bh/2} L {rx0-8} {ty+bh/2} L {rx0-8} {ay+8} "
                  f"L {ax+60+bw} {ay+8}", GREEN, 2.2, mark="g"))
    s.append(txt(rx0 + 396, ty + 96,
                 "PAPR 10 dB means the peak sits 10 dB above the average - "
                 "that is what sets the PA", 10, GREEN, weight="bold"))

    # ── 공용 합성기
    sx, sy = rx0 + 3 * (bw + 34) - 8, 290
    s += blk(sx, sy - 5, "PLL / VCO", "shared LO", YELLOW, "#FDF6E8")
    s.append(path(f"M {sx+bw/2} {sy-5} L {sx+bw/2} {ry+bh}", YELLOW, 1.8,
                  dash="5 4", mark="y" if False else None))
    s.append(path(f"M {sx+bw/2} {sy+bh-5} L {sx+bw/2} {ty}", YELLOW, 1.8,
                  dash="5 4"))
    s.append(txt(sx + bw / 2, sy + 62, "one reference for both", 9, GREY))
    s.append(rect(sx - 130, sy + 76, 356, 34, RED, "#FDF6F5", rx=6, sw=1.5))
    s.append(txt(sx + 48, sy + 97,
                 "40 MHz ref x 61 = 2440 MHz - inside the band. "
                 "You cannot plan it away.", 10, RED, weight="bold"))

    # ── 전원
    s.append(rect(60, 520, 1060, 74, INK, LIGHT, rx=8, sw=1.6))
    s.append(txt(590, 542, "POWER  -  its own budget, and its own noise",
                 11.5, weight="bold"))
    s.append(txt(84, 562,
                 "Z_target = dV / dI    ·    the switching regulator is the "
                 "loudest thing on the board    ·    RF rail separated by "
                 "ferrite or its own LDO", 10, INK, anchor="start"))
    s.append(txt(84, 580,
                 "every block above draws current; the sum has to fit the "
                 "power budget, and the PA dominates it", 10, GREY,
                 anchor="start"))
    return save("transceiver", "".join(s))


# ══════════════════════════════════ 2. 산출물 지도
def deliverables():
    w, h = 1120, 640
    s = [HEAD.format(w=w, h=h, title="캡스톤 산출물 11종과 의존 관계"), defs()]
    s.append(txt(w / 2, 30, "Eleven deliverables - and what each one feeds",
                 16, weight="bold"))
    s.append(txt(w / 2, 52, "an arrow means: you cannot write the next one "
                 "without the previous", 10.5, GREY))

    phases = [
        ("P1  system design", BLUE, "#F5F9FD", 82, [
            ("1", "requirements analysis", "conflicts found and negotiated"),
            ("2", "RX cascade budget", "NF - IIP3 - gain, per AGC mode"),
            ("3", "TX cascade budget", "output - backoff - EVM"),
            ("4", "frequency plan + spur table", "isolation budget, not zero")]),
        ("P2  implementation", ORANGE, "#FDF3EC", 240, [
            ("5", "part selection rationale", "datasheet -> our spec"),
            ("6", "schematic + board files", "stack-up, impedance, layout")]),
        ("P3  verification", GREEN, "#EFF7F3", 356, [
            ("7", "test plan", "conditions - equipment - guard band"),
            ("8", "measurement report", "value +/- uncertainty")]),
        ("P4  tune - judge - report", RED, "#FDF6F5", 472, [
            ("9", "tuning log", "one change at a time"),
            ("10", "conformity statement", "decision rule stated"),
            ("11", "design review pack", "what you would do differently")]),
    ]

    boxw, boxh, gap = 236, 62, 22
    for title, col, fill, y, items in phases:
        n = len(items)
        band_h = boxh + 46
        s.append(rect(60, y, w - 120, band_h, col, fill, rx=8, sw=1.8))
        s.append(txt(78, y + 20, title, 12, col, weight="bold", anchor="start"))
        x = 84
        for num, name, sub in items:
            s.append(rect(x, y + 28, boxw, boxh, col, "white", rx=5, sw=1.4))
            s.append(f'<circle cx="{x+18}" cy="{y+46}" r="12" fill="{col}"/>')
            s.append(txt(x + 18, y + 50, num, 10.5, "white", weight="bold"))
            s.append(txt(x + 38, y + 44, name, 10.5, INK, anchor="start",
                         weight="bold"))
            s.append(txt(x + 38, y + 60, sub, 9, GREY, anchor="start"))
            x += boxw + gap
        if y != 472:
            s.append(path(f"M {w/2} {y+band_h} L {w/2} {y+band_h+16}",
                          GREY, 2.0, mark="k"))

    s.append(rect(60, 566, w - 120, 58, INK, LIGHT, rx=8, sw=1.6))
    s.append(txt(w / 2, 588, "the rule that decides the grade", 11.5,
                 weight="bold"))
    s.append(txt(w / 2, 610,
                 "every number in every deliverable must be traceable to a "
                 "datasheet, a measurement, or a calculation you can show",
                 10.5, RED, weight="bold"))
    return save("deliverables", "".join(s))


if __name__ == "__main__":
    for fn in (transceiver, deliverables):
        fn()
