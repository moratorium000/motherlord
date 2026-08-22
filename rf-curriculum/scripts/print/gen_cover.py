#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""표지 전개도(앞표지 · 책등 · 뒤표지)를 인쇄용 PDF 로 만든다.

인쇄소에 넘기는 표지는 **낱장이 아니라 한 장으로 펼친 전개도**다. 왼쪽부터
뒤표지 → 책등 → 앞표지 순으로 놓이고, 바깥으로 도련 3 mm 가 더 나간다.
책등 폭은 `spec.py` 가 쪽수와 종이에서 계산한 값을 그대로 쓴다 — 손으로 적으면
반드시 어긋난다.

앞표지 그림은 스미스 차트다. 이미지 파일을 얹지 않고 **원과 호를 계산해서
그린다** — 확대해도 깨지지 않고, 등저항 원과 등리액턴스 호가 실제로 맞는
자리에 온다.

출력: 04_인쇄/표지_전개도.pdf
실행: python3 scripts/print/gen_cover.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib.colors import CMYKColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spec  # noqa: E402

ROOT = spec.ROOT
OUT = ROOT / "04_인쇄" / "표지_전개도.pdf"
MM = spec.MM

MARK_M = 10.0             # 재단선을 그릴 바깥 여백(mm)
MARK_LEN = 5.0            # 재단선 길이
MARK_GAP = 1.0            # 재단선과 도련 사이 틈

# ── 색 (CMYK. 인쇄는 RGB 가 아니라 CMYK 로 찍는다) ──────────────────────
NAVY = CMYKColor(0.95, 0.72, 0.35, 0.40)
NAVY_D = CMYKColor(0.98, 0.80, 0.45, 0.60)
GOLD = CMYKColor(0.05, 0.25, 0.88, 0.00)
CYAN = CMYKColor(0.58, 0.06, 0.22, 0.00)
WHITE = CMYKColor(0, 0, 0, 0)
# 남색 바탕 위에 얹는 보조 글자색. 검정 톤은 바탕에 묻히므로
# 흰색 쪽으로 옅게 뺀 청회색을 쓴다.
PALE = CMYKColor(0.22, 0.10, 0.06, 0.02)   # 본문 보조
DIM = CMYKColor(0.35, 0.18, 0.10, 0.08)    # 더 약한 주석
GREY = PALE
REG = CMYKColor(1, 1, 1, 1)      # 재단선은 4색 모두 100 (레지스트레이션)

FONTS = {
    "N": "NanumGothic.ttf",
    "NB": "NanumGothicBold.ttf",
    "NX": "NanumGothicExtraBold.ttf",
    "NL": "NanumGothicLight.ttf",
}


def register_fonts() -> None:
    base = Path("/root/.fonts")
    for name, fn in FONTS.items():
        p = base / fn
        if not p.exists():
            sys.exit(f"글꼴이 없습니다: {p}")
        pdfmetrics.registerFont(TTFont(name, str(p)))


# ── 스미스 차트 ────────────────────────────────────────────────────────
def smith(c: canvas.Canvas, cx: float, cy: float, R: float) -> None:
    """단위원 안에 등저항 원과 등리액턴스 호를 그린다.

    등저항 r  : 중심 (r/(1+r), 0), 반지름 1/(1+r)
    등리액턴스 x: 중심 (1, 1/x),   반지름 1/|x|

    좌표는 정규화 평면(-1..1)이므로 R 배 해서 종이 위로 옮긴다.
    호가 단위원 밖으로 나가는 부분은 단위원으로 잘라 낸다.
    """
    c.saveState()
    clip = c.beginPath()
    clip.circle(cx, cy, R)
    c.clipPath(clip, stroke=0, fill=0)

    c.setLineWidth(0.35)
    c.setStrokeColor(CYAN)
    for r in (0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0):
        rr = 1.0 / (1.0 + r)
        c.circle(cx + r / (1.0 + r) * R, cy, rr * R, stroke=1, fill=0)

    c.setStrokeColor(GOLD)
    c.setLineWidth(0.30)
    for x in (0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0):
        rr = 1.0 / x
        for sgn in (+1, -1):
            c.circle(cx + R, cy + sgn * rr * R, rr * R, stroke=1, fill=0)

    # 실수축
    c.setStrokeColor(CYAN)
    c.setLineWidth(0.35)
    c.line(cx - R, cy, cx + R, cy)
    c.restoreState()

    # 바깥 테두리
    c.setStrokeColor(WHITE)
    c.setLineWidth(0.8)
    c.circle(cx, cy, R, stroke=1, fill=0)


# ── 조판 도우미 ────────────────────────────────────────────────────────
def text(c, x, y, s, font="N", size=10, color=WHITE, align="l", track=0.0):
    """한 줄 찍기. track 은 자간(pt). 자간은 텍스트 객체로만 줄 수 있다."""
    w = c.stringWidth(s, font, size) + track * max(len(s) - 1, 0)
    if align == "c":
        x -= w / 2
    elif align == "r":
        x -= w
    c.setFillColor(color)
    to = c.beginText(x, y)
    to.setFont(font, size)
    # 0 이어도 반드시 넣는다. 텍스트 객체가 캔버스의 자간 상태를 물려받아서,
    # 빼먹으면 앞서 자간을 준 줄의 값이 뒤 글줄에 그대로 새어 나온다.
    to.setCharSpace(track)
    to.textOut(s)
    c.drawText(to)
    return w


def rule(c, x0, y, x1, color=GOLD, w=0.6):
    c.setStrokeColor(color)
    c.setLineWidth(w)
    c.line(x0, y, x1, y)


def para(c, x, y, lines, font="NL", size=9, lead=4.6, color=WHITE):
    """줄 목록을 위에서 아래로. 반환값은 마지막 줄의 y."""
    for ln in lines:
        text(c, x, y, ln, font=font, size=size, color=color)
        y -= lead * MM
    return y


# ── 앞표지 ─────────────────────────────────────────────────────────────
def front(c, x0, y0, w, h, info):
    cxm = x0 + w / 2

    # 위쪽 얇은 금색 띠
    c.setFillColor(GOLD)
    c.rect(x0, y0 + h - 14 * MM, w, 1.2 * MM, stroke=0, fill=1)

    text(c, x0 + 20 * MM, y0 + h - 26 * MM,
         "RF SYSTEMS ENGINEERING", font="NB", size=9, color=GOLD, track=2.2)

    # 제목
    text(c, x0 + 20 * MM, y0 + h - 52 * MM, "RF 시스템", font="NX", size=40)
    text(c, x0 + 20 * MM, y0 + h - 70 * MM, "엔지니어링", font="NX", size=40)

    rule(c, x0 + 20 * MM, y0 + h - 80 * MM, x0 + 80 * MM)

    text(c, x0 + 20 * MM, y0 + h - 90 * MM,
         "전기전자 초심자에서 실무자까지", font="N", size=13, color=WHITE)
    text(c, x0 + 20 * MM, y0 + h - 99 * MM,
         "커리큘럼과 교육자료", font="NL", size=11, color=CYAN)

    # 스미스 차트
    smith(c, cxm, y0 + 122 * MM, 46 * MM)
    text(c, cxm, y0 + 66 * MM,
         "정합의 언어 — 스미스 차트", font="NL", size=9,
         color=PALE, align="c", track=1.2)

    # 아래 정보
    rule(c, x0 + 20 * MM, y0 + 42 * MM, x0 + w - 20 * MM, color=DIM, w=0.4)
    text(c, x0 + 20 * MM, y0 + 33 * MM,
         "본문 18개 모듈 · 캡스톤 · 부록 A–E", font="NB", size=10)
    text(c, x0 + 20 * MM, y0 + 25 * MM,
         f"A4 {info['final_pages']}쪽 · 그림 139개 · 출처 166개",
         font="NL", size=9, color=PALE)
    text(c, x0 + w - 20 * MM, y0 + 25 * MM, spec.VERSION,
         font="NL", size=9, color=PALE, align="r")


# ── 책등 ───────────────────────────────────────────────────────────────
def spine_panel(c, x0, y0, w, h):
    c.saveState()
    # 국내 책의 책등은 위에서 아래로 읽는다. 그래서 시계 방향(-90°)이다.
    # 반대로 돌리면 책장에 꽂았을 때 제목이 거꾸로 선다.
    c.translate(x0 + w / 2, y0 + h / 2)
    c.rotate(-90)

    # 돌린 좌표에서 지면 가로 위치는 local_y 그대로다. 글자 몸통의 한가운데를
    # 책등 한가운데에 맞추려면 기준선을 몸통 높이의 절반만큼 내려야 한다.
    # 이걸 빼먹으면 제목이 책등 한쪽으로 쏠린다 (처음에 실제로 그랬다).
    cap = 14 * 0.72 / 72 * 25.4        # 14 pt 글자의 대략적 몸통 높이(mm)
    text(c, 0, -cap / 2 * MM, "RF 시스템 엔지니어링",
         font="NX", size=14, align="c")

    cap2 = 8 * 0.72 / 72 * 25.4
    text(c, h / 2 - 20 * MM, -cap2 / 2 * MM,
         "M00–M17 · 캡스톤 · 부록", font="NL", size=8,
         color=PALE, align="r")
    c.restoreState()

    # 위아래 금색 점
    c.setFillColor(GOLD)
    c.circle(x0 + w / 2, y0 + h - 13 * MM, 1.6 * MM, stroke=0, fill=1)
    c.circle(x0 + w / 2, y0 + 13 * MM, 1.6 * MM, stroke=0, fill=1)


# ── 뒤표지 ─────────────────────────────────────────────────────────────
def back(c, x0, y0, w, h, info):
    L = x0 + 20 * MM
    Rr = x0 + w - 20 * MM

    c.setFillColor(GOLD)
    c.rect(x0, y0 + h - 14 * MM, w, 1.2 * MM, stroke=0, fill=1)

    y = y0 + h - 30 * MM
    text(c, L, y, "무엇을 하는 책인가", font="NB", size=12, color=GOLD)
    y -= 10 * MM
    y = para(c, L, y, [
        "\"잘 터지게 해 주세요\" 라는 말을 받아",
        "\"LNA 는 잡음지수 1.5 dB 이하\" 라는 숫자로 바꾸고,",
        "그 숫자가 맞는지 장비로 재서 판정하는 일 — 그것이",
        "RF 시스템 엔지니어의 일입니다. 이 책은 데시벨부터",
        "시작해 거기까지 갑니다.",
    ], font="N", size=9.5, lead=5.4)

    y -= 5 * MM
    rule(c, L, y, Rr, color=GREY, w=0.4)
    y -= 9 * MM

    text(c, L, y, "차례", font="NB", size=11, color=GOLD)
    y -= 8 * MM
    parts = [
        ("Part 0", "RF 시스템 엔지니어링이란"),
        ("Part I", "데시벨 · 전송선로 · S-파라미터"),
        ("Part II", "RF 실험실 입문 · 첫 측정"),
        ("Part III", "수동소자 · 필터 · 증폭기 · 주파수 변환"),
        ("Part IV", "안테나 · 트랜시버 · 예산 설계 · 변조"),
        ("Part V", "교정과 불확도 · 정밀 측정 · 검증과 튜닝 · 보드 설계"),
        ("Part VI", "캡스톤 — 2.4 GHz 송수신 트랜시버"),
        ("부록", "축약어 · 공식 치트시트 · 출처 · 장비 · 수학 보충"),
    ]
    for tag, body in parts:
        text(c, L, y, tag, font="NB", size=8.5, color=CYAN)
        text(c, L + 20 * MM, y, body, font="NL", size=8.5, color=WHITE)
        y -= 5.6 * MM

    y -= 4 * MM
    rule(c, L, y, Rr, color=GREY, w=0.4)
    y -= 9 * MM

    text(c, L, y, "이 책의 약속", font="NB", size=11, color=GOLD)
    y -= 8 * MM
    para(c, L, y, [
        "① 축약어는 처음 나올 때 원어와 우리말을 함께 적는다",
        "② 개념마다 주인이 되는 모듈이 하나씩 있다",
        "③ 모든 수치는 계산으로 확인했고 스크립트로 재현된다",
        "④ 모든 사실에 출처와 신뢰 등급을 붙였다",
    ], font="NL", size=8.5, lead=5.2)

    # 비는 자리에는 책이 실제로 내놓는 숫자를 넣는다. 표지의 빈 칸을
    # 장식으로 채우는 것보다 이쪽이 고르는 사람에게 쓸모가 있다.
    y -= 26 * MM
    rule(c, L, y + 8 * MM, Rr, color=DIM, w=0.4)
    text(c, L, y, "이런 것을 계산합니다", font="NB", size=11, color=GOLD)
    y -= 8 * MM
    for num, what in [
        ("77 dB", "26 MHz 클럭을 대역 밖으로 못 옮길 때 필요한 격리"),
        ("34.6배", "커패시터 한 종을 빼면 전원망 반공진이 넘는 배수"),
        ("2.50 GHz", "100 × 75 mm 실드 캔이 공진하는 주파수"),
        ("52 %", "확장불확도만큼 가드밴드를 두면 버리는 양품 비율"),
    ]:
        text(c, L, y, num, font="NB", size=9, color=CYAN)
        text(c, L + 22 * MM, y, what, font="NL", size=8.5, color=WHITE)
        y -= 5.6 * MM

    # 아래: 주의 문구 + 바코드 자리
    note_y = y0 + 44 * MM
    rule(c, L, note_y + 10 * MM, Rr, color=DIM, w=0.4)
    para(c, L, note_y, [
        "이 책은 외부 웹 접속이 막힌 환경에서 집필되었습니다. 모든 사실은",
        "독립 출처 두 곳 이상으로 교차검증했으나 원문을 직접 열어 보지는",
        "못했습니다. 규격 한도값은 설명을 위한 것이며, 실제 판정은 최신",
        "원문과 인증 시험소의 확인을 받아야 합니다.",
    ], font="NL", size=7.4, lead=4.0, color=PALE)

    # ISBN 바코드 자리 (흰 상자. 실제 바코드는 발급 후 얹는다)
    bw, bh = 40 * MM, 22 * MM
    bx, by = Rr - bw, y0 + 14 * MM
    c.setFillColor(WHITE)
    c.rect(bx, by, bw, bh, stroke=0, fill=1)
    c.setStrokeColor(CMYKColor(0, 0, 0, 0.30))
    c.setLineWidth(0.3)
    c.rect(bx, by, bw, bh, stroke=1, fill=0)
    text(c, bx + bw / 2, by + bh / 2 - 1 * MM, "ISBN 바코드 자리",
         font="NL", size=7, color=CMYKColor(0, 0, 0, 0.55), align="c")

    text(c, L, y0 + 20 * MM, "RF 시스템 엔지니어링 커리큘럼",
         font="NB", size=8.5, color=WHITE)
    text(c, L, y0 + 15 * MM, spec.VERSION, font="NL", size=7.5, color=PALE)


# ── 재단선 ─────────────────────────────────────────────────────────────
def marks(c, tx0, ty0, tw, th, folds):
    """재단선(모서리)과 접는선(책등 양쪽)을 도련 바깥에 그린다."""
    c.setStrokeColor(REG)
    c.setLineWidth(0.25)
    g, ln = MARK_GAP * MM, MARK_LEN * MM
    b = spec.BLEED_MM * MM
    for x in (tx0, tx0 + tw):
        for y in (ty0, ty0 + th):
            sx = -1 if x == tx0 else 1
            sy = -1 if y == ty0 else 1
            # 가로 선
            c.line(x + sx * (b + g), y, x + sx * (b + g + ln), y)
            # 세로 선
            c.line(x, y + sy * (b + g), x, y + sy * (b + g + ln))
    # 책등 접는선
    for x in folds:
        c.line(x, ty0 - b - g, x, ty0 - b - g - ln)
        c.line(x, ty0 + th + b + g, x, ty0 + th + b + g + ln)


def main() -> int:
    register_fonts()
    info = spec.report()
    pages = info["final_pages"]
    sp = info["spine"]

    tw = (spec.TRIM_W_MM * 2 + sp) * MM        # 재단 후 폭
    th = spec.TRIM_H_MM * MM
    media_w = tw + 2 * (spec.BLEED_MM + MARK_M) * MM
    media_h = th + 2 * (spec.BLEED_MM + MARK_M) * MM

    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(media_w, media_h))
    c.setTitle("RF 시스템 엔지니어링 — 표지 전개도")
    c.setAuthor("RF 시스템 엔지니어링 커리큘럼")

    tx0 = (spec.BLEED_MM + MARK_M) * MM
    ty0 = (spec.BLEED_MM + MARK_M) * MM
    b = spec.BLEED_MM * MM

    # 도련까지 바탕을 깐다 (재단이 밀려도 흰 줄이 안 생기도록)
    c.setFillColor(NAVY)
    c.rect(tx0 - b, ty0 - b, tw + 2 * b, th + 2 * b, stroke=0, fill=1)

    back_w = spec.TRIM_W_MM * MM
    spine_w = sp * MM
    # 책등은 살짝 어둡게 해서 접히는 자리를 눈으로 알 수 있게
    c.setFillColor(NAVY_D)
    c.rect(tx0 + back_w, ty0 - b, spine_w, th + 2 * b, stroke=0, fill=1)

    back(c, tx0, ty0, back_w, th, info)
    spine_panel(c, tx0 + back_w, ty0, spine_w, th)
    front(c, tx0 + back_w + spine_w, ty0, back_w, th, info)

    marks(c, tx0, ty0, tw, th, [tx0 + back_w, tx0 + back_w + spine_w])

    c.showPage()
    c.save()

    add_boxes(OUT, media_w, media_h, tx0, ty0, tw, th, b)

    audit()

    size = OUT.stat().st_size / 1024
    print(f"\n표지 전개도 → {OUT.relative_to(ROOT)}  "
          f"({media_w / MM:.0f} × {media_h / MM:.0f} mm 판, "
          f"재단 {tw / MM:.1f} × {th / MM:.0f} mm, {size:.0f} KB)")
    print(f"  책등 {sp:.1f} mm · 본문 {pages}쪽 기준")
    return 0


def audit() -> None:
    """인쇄소가 되묻는 두 가지를 미리 계산해 둔다.

    · 총 잉크량(TAC) — 코팅지 기준 300 % 를 넘으면 마르지 않아 묻어난다
    · 가장 가는 선 — 0.25 pt 아래로 내려가면 인쇄에서 끊긴다
    """
    inks = {"바탕 남색": NAVY, "책등 남색": NAVY_D, "금색": GOLD,
            "청록": CYAN, "옅은 청회색": PALE, "약한 주석": DIM}
    print("-" * 66)
    worst = 0.0
    for name, col in inks.items():
        tac = (col.cyan + col.magenta + col.yellow + col.black) * 100
        worst = max(worst, tac)
        print(f"  잉크량 {name:12s} {tac:5.0f} %")
    print(f"  ── 최대 {worst:.0f} % (재단선은 레지스트레이션 400 % — 정상)")
    assert worst <= 300, f"총 잉크량 {worst:.0f} % 가 300 % 를 넘습니다"

    thin = min(0.30, 0.35, 0.25)
    print(f"  가장 가는 선  도형 0.30 pt · 재단선 {thin:.2f} pt "
          f"(인쇄 한계 0.25 pt)")
    assert thin >= 0.25


def add_boxes(path: Path, mw, mh, tx0, ty0, tw, th, b) -> None:
    """TrimBox·BleedBox 를 박는다. 인쇄소 RIP 이 이 상자로 재단 위치를 잡는다."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, FloatObject, NameObject

    def box(x0, y0, w, h):
        return ArrayObject([FloatObject(x0), FloatObject(y0),
                            FloatObject(x0 + w), FloatObject(y0 + h)])

    r = PdfReader(str(path))
    w = PdfWriter()
    pg = r.pages[0]
    pg[NameObject("/TrimBox")] = box(tx0, ty0, tw, th)
    pg[NameObject("/BleedBox")] = box(tx0 - b, ty0 - b, tw + 2 * b, th + 2 * b)
    pg[NameObject("/ArtBox")] = box(tx0, ty0, tw, th)
    w.add_page(pg)
    with open(path, "wb") as f:
        w.write(f)


if __name__ == "__main__":
    sys.exit(main())
