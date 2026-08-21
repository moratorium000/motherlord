"""M16 손그림 SVG — 데이터시트 해부도, 스펙 매핑표 양식, 자동화 구성도.

주의: SVG 의 <text> 는 보는 사람의 글꼴로 그려지므로 한글을 넣지 않는다.
설명은 본문 캡션과 표가 맡는다. (<title> 은 화면에 안 그려지므로 예외)
"""
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets/M16"

INK = "#1A1A1A"
BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
RED = "#C0392B"
GREY = "#7F7F7F"
LIGHT = "#F0F0F0"
BAND = "#E8EDF5"

HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        'viewBox="0 0 {w} {h}" font-family="Helvetica,Arial,sans-serif">'
        '<title>{title}</title><rect width="{w}" height="{h}" fill="white"/>')


def esc(s):
    """SVG 는 XML 이라 <, &, > 를 그대로 쓰면 파일이 통째로 안 열린다.

    'NF <= 2.0 dB' 같은 문구 하나가 그림 전체를 깨뜨린 적이 있어 함수로 굳혔다.
    """
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
        for n, c in (("k", INK), ("r", RED), ("b", BLUE), ("g", GREEN)))
            + '</defs>')


def rect(x, y, w, h, color=INK, fill="white", rx=4, sw=1.6, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{color}" stroke-width="{sw}"{d}/>')


def wire(x1, y1, x2, y2, color=INK, w=1.8, mark="k", dash=None):
    m = f' marker-end="url(#a{mark})"' if mark else ""
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{w}"{d}{m}/>')


# ══════════════════════════════════ 1. 데이터시트 해부도
def datasheet():
    w, h = 1020, 570
    s = [HEAD.format(w=w, h=h, title="데이터시트 해부 - 어디를 봐야 하는가"), defs()]
    s.append(txt(w / 2, 32, "Reading a datasheet: the numbers are not the point",
                 16, weight="bold"))

    # 가짜 데이터시트 표
    x0, y0, tw = 60, 70, 560
    s.append(rect(x0, y0, tw, 250, INK, "white", rx=6, sw=2))
    s.append(txt(x0 + 16, y0 + 26, "LNA-2450  Electrical Specifications", 13,
                 anchor="start", weight="bold"))
    s.append(txt(x0 + 16, y0 + 46,
                 "Vdd = 5 V, Idq = 60 mA, Ta = 25 C, Z0 = 50 ohm", 10, GREY,
                 anchor="start"))
    s.append(f'<line x1="{x0+16}" y1="{y0+56}" x2="{x0+tw-16}" y2="{y0+56}" '
             f'stroke="{GREY}" stroke-width="1"/>')

    cols = [(x0 + 20, "Parameter"), (x0 + 210, "Min"), (x0 + 290, "Typ"),
            (x0 + 370, "Max"), (x0 + 450, "Unit")]
    for cx, name in cols:
        s.append(txt(cx, y0 + 78, name, 11, INK, anchor="start", weight="bold"))
    rows = [("Frequency", "2400", "-", "2500", "MHz", 104),
            ("Gain", "16.5", "18.0", "-", "dB", 128),
            ("Noise figure", "-", "1.3", "-", "dB", 152),
            ("OIP3", "28", "31", "-", "dBm", 176),
            ("P1dB", "-", "19", "-", "dBm", 200),
            ("Supply current", "-", "60", "75", "mA", 224)]
    for name, mn, tp, mx, un, dy in rows:
        yy = y0 + dy
        for cx, v in zip([c[0] for c in cols], [name, mn, tp, mx, un]):
            col = RED if (v == "-" and cx != x0 + 20) else INK
            s.append(txt(cx, yy, v, 11, col, anchor="start"))
    s.append(rect(x0 + 270, y0 + 138, 60, 20, RED, "none", rx=3, sw=2))
    s.append(rect(x0 + 202, y0 + 162, 60, 20, RED, "none", rx=3, sw=2))

    # 주석
    # 가리키는 줄(target)과 글자를 놓는 자리(label)를 따로 둔다.
    # 같은 높이에 두면 두 줄짜리 설명끼리 겹친다.
    notes = [
        (RED, y0 + 46, y0 + 40, "the CONDITIONS line is the real specification",
         "every number below is only true here"),
        (RED, y0 + 152, y0 + 110, "Typ only, no Max -> NOT guaranteed",
         "you may not design to this number"),
        (BLUE, y0 + 176, y0 + 180, "Min is guaranteed, Typ is not",
         "use Min for your budget"),
        (GREEN, y0 + 224, y0 + 250, "Max supply current sizes your regulator",
         "not the typical one"),
    ]
    nx = x0 + tw + 34
    for col, ty, ly, a, b in notes:
        mk = "b" if col == BLUE else ("g" if col == GREEN else "r")
        s.append(f'<path d="M {x0+tw+6},{ty} L {nx-16},{ly - 4}" '
                 f'stroke="{col}" stroke-width="1.4" fill="none" '
                 f'marker-end="url(#a{mk})"/>')
        s.append(txt(nx, ly - 6, a, 10.5, col, anchor="start", weight="bold"))
        s.append(txt(nx, ly + 9, b, 9.5, GREY, anchor="start"))

    # 아래: 꼭 확인할 것
    y1 = 360
    s.append(rect(60, y1, w - 120, 176, GREY, LIGHT, rx=8, sw=1.4))
    s.append(txt(80, y1 + 26, "before you believe any number, find these",
                 12.5, INK, anchor="start", weight="bold"))
    checks = [
        "1.  the test conditions  (voltage, current, temperature, impedance)",
        "2.  is it Min/Max (guaranteed) or Typ (not guaranteed)?",
        "3.  over what temperature range is it guaranteed?",
        "4.  the test circuit in the appendix - your board is not that board",
        "5.  which revision of the datasheet is this?",
    ]
    for i, c in enumerate(checks):
        s.append(txt(84, y1 + 54 + i * 24, c, 11, INK, anchor="start"))
    s.append("</svg>")
    (OUT / "datasheet.svg").write_text("\n".join(s))


# ══════════════════════════════════ 2. 스펙 매핑표 양식
def specmap():
    w, h = 1040, 430
    s = [HEAD.format(w=w, h=h, title="스펙 매핑표 양식"), defs()]
    s.append(txt(w / 2, 32, "Spec mapping sheet - our requirement vs the part",
                 16, weight="bold"))

    cols = [(50, 150, "OUR SPEC"), (200, 130, "value"),
            (330, 160, "DATASHEET"), (490, 120, "value"),
            (610, 110, "condition"), (720, 110, "margin"),
            (830, 160, "verdict / action")]
    y0 = 62
    s.append(rect(50, y0, 940, 34, INK, BAND, rx=4, sw=1.6))
    for x, cw, name in cols:
        s.append(txt(x + cw / 2, y0 + 22, name, 11, INK, weight="bold"))

    rows = [
        ("Noise figure", "<= 2.0 dB", "NF", "1.3 dB typ", "25 C", "0.7 dB",
         "TYP ONLY - ask vendor", RED),
        ("Gain", ">= 15 dB", "Gain", "16.5 dB min", "25 C", "1.5 dB",
         "OK", GREEN),
        ("OIP3", ">= 26 dBm", "OIP3", "28 dBm min", "60 mA", "2 dB",
         "OK if Idq kept", ORANGE),
        ("Current", "<= 80 mA", "Idd", "75 mA max", "5 V", "5 mA",
         "OK", GREEN),
        ("Temp range", "-20..+70 C", "-", "25 C only", "-", "?",
         "NOT COVERED - test it", RED),
    ]
    for i, (a, b, c, d, e, f, g, col) in enumerate(rows):
        yy = y0 + 34 + i * 34
        s.append(rect(50, yy, 940, 34, GREY, "white" if i % 2 else "#FAFAFA",
                      rx=0, sw=0.8))
        for (x, cw, _), v in zip(cols, (a, b, c, d, e, f, g)):
            s.append(txt(x + 8, yy + 22, v, 10.5,
                         col if v == g else INK, anchor="start",
                         weight="bold" if v == g else "normal"))

    s.append(txt(50, 330, "the two red rows are the whole point of this sheet",
                 12, RED, anchor="start", weight="bold"))
    s.append(txt(50, 352,
                 "a Typ-only number is not a promise, and a spec the datasheet "
                 "never covers is a test you have to run yourself.",
                 11, GREY, anchor="start"))
    s.append(txt(50, 386,
                 "margin = our spec - datasheet guaranteed value.  "
                 "If you cannot write a number here, the row is not finished.",
                 11, INK, anchor="start"))
    s.append("</svg>")
    (OUT / "specmap.svg").write_text("\n".join(s))


# ══════════════════════════════════ 3. 자동화 구성도
def automation():
    w, h = 1020, 560
    s = [HEAD.format(w=w, h=h, title="시험 자동화 구성도"), defs()]
    s.append(txt(w / 2, 32, "Test automation: what talks to what", 16,
                 weight="bold"))

    s.append(rect(60, 70, 240, 150, BLUE, "white", rx=6, sw=2))
    s.append(txt(180, 96, "PC  /  Python", 13, BLUE, weight="bold"))
    s.append(txt(180, 122, "pyvisa", 12, INK, mono=True))
    s.append(txt(180, 144, "your test script", 10.5, GREY))
    s.append(txt(180, 168, "sweep - measure - judge", 10, GREY))
    s.append(txt(180, 192, "write CSV / Touchstone", 10, GREY))

    s.append(wire(300, 145, 380, 145, INK, 2))
    s.append(rect(380, 118, 150, 54, INK, LIGHT, rx=5))
    s.append(txt(455, 142, "VISA layer", 12, INK, weight="bold"))
    s.append(txt(455, 160, "USB / LAN / GPIB", 9.5, GREY))

    ys = [70, 148, 226]
    names = [("VNA", "S-parameters"), ("SIGNAL GEN", "stimulus"),
             ("SPECTRUM AN.", "spurious, ACLR")]
    for (nm, sub), yy in zip(names, ys):
        s.append(wire(530, 145, 620, yy + 27, INK, 1.6))
        s.append(rect(620, yy, 190, 54, INK, "white", rx=5))
        s.append(txt(715, yy + 24, nm, 12, INK, weight="bold"))
        s.append(txt(715, yy + 42, sub, 9.5, GREY))

    s.append(rect(850, 118, 120, 118, GREEN, "white", rx=6, sw=2))
    s.append(txt(910, 146, "DUT", 14, GREEN, weight="bold"))
    s.append(txt(910, 168, "one board,", 9.5, GREY))
    s.append(txt(910, 184, "one serial", 9.5, GREY))
    s.append(txt(910, 200, "number", 9.5, GREY))
    for yy in ys:
        s.append(wire(810, yy + 27, 848, yy + 27, GREY, 1.4, None))

    # SCPI 예시
    y1 = 300
    s.append(rect(60, y1, 470, 210, GREY, "#FAFAFA", rx=6, sw=1.4))
    s.append(txt(80, y1 + 26, "the four calls you actually need", 12, INK,
                 anchor="start", weight="bold"))
    code = [
        'rm = pyvisa.ResourceManager()',
        'inst = rm.open_resource("TCPIP::192.168.0.10::INSTR")',
        'inst.timeout = 10000            # ms',
        'print(inst.query("*IDN?"))      # who are you',
        'inst.write("SENS:FREQ:STAR 2.4e9")',
        'data = inst.query("CALC:DATA? SDATA")',
    ]
    for i, c in enumerate(code):
        s.append(txt(80, y1 + 52 + i * 24, c, 10, INK, anchor="start",
                     mono=True))

    # 규칙
    s.append(rect(560, y1, 400, 210, RED, "white", rx=6, sw=1.6))
    s.append(txt(580, y1 + 26, "rules that save you later", 12, RED,
                 anchor="start", weight="bold"))
    rules = [
        "always ask *IDN? first and log the answer",
        "set a timeout - the default is too short",
        "*OPC? after a slow sweep, do not sleep()",
        "save raw data, never only the verdict",
        "put the settings into the file you save",
        "one file per DUT serial number",
    ]
    for i, r in enumerate(rules):
        s.append(txt(580, y1 + 52 + i * 24, "- " + r, 10.5, INK, anchor="start"))
    s.append("</svg>")
    (OUT / "automation.svg").write_text("\n".join(s))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    datasheet()
    specmap()
    automation()
    for f in sorted(OUT.glob("*.svg")):
        print(f"  {f.name}  {f.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
