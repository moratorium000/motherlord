#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""읽기용 PDF 를 제본용 본문 PDF 로 바꾼다.

화면으로 읽을 때는 좌우 여백이 같아도 되지만, 묶어 놓으면 안쪽이 책등에
말려 들어가 글자가 골짜기에 빠진다. 560쪽짜리 무선제본이면 더 그렇다.
그래서 **홀수 쪽은 오른쪽으로, 짝수 쪽은 왼쪽으로** 내용을 밀어 안쪽 여백을
늘린다. 판면 크기는 A4 그대로 두므로 재단 규격은 바뀌지 않는다.

  홀수 쪽 = 오른쪽 면(recto) → 책등이 왼쪽 → 내용을 오른쪽으로
  짝수 쪽 = 왼쪽 면(verso)  → 책등이 오른쪽 → 내용을 왼쪽으로

그리고 맨 뒤에 판권지를 붙이고 대수(4의 배수)에 맞춰 백면을 채운다.

출력: 04_인쇄/본문_인쇄용.pdf
실행: python3 scripts/print/make_body.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.lib.colors import CMYKColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spec  # noqa: E402

ROOT = spec.ROOT
# 권마다 다르다. main() 에서 spec.use() 뒤에 정한다.
SRC = spec.BODY_PDF
OUT = ROOT / "04_인쇄" / "본문_인쇄용.pdf"
MM = spec.MM

PAGE_W = spec.TRIM_W_MM * MM
PAGE_H = spec.TRIM_H_MM * MM
GUTTER = spec.GUTTER_MM * MM

INK = CMYKColor(0, 0, 0, 1)
SOFT = CMYKColor(0, 0, 0, 0.55)


def register_fonts() -> None:
    base = Path("/root/.fonts")
    for name, fn in (("N", "NanumGothic.ttf"), ("NB", "NanumGothicBold.ttf"),
                     ("NL", "NanumGothicLight.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(base / fn)))


# ─────────────────────────────────────────────────────────── 판권지
def colophon(path: Path, info: dict) -> None:
    c = canvas.Canvas(str(path), pagesize=(PAGE_W, PAGE_H))
    L = 30 * MM
    R = PAGE_W - 30 * MM
    y = PAGE_H - 60 * MM

    c.setFillColor(INK)
    c.setFont("NB", 15)
    c.drawString(L, y, "RF 시스템 엔지니어링")
    y -= 8 * MM
    c.setFont("NL", 10)
    c.drawString(L, y, "전기전자 초심자에서 실무자까지 — 커리큘럼과 교육자료")

    y -= 6 * MM
    c.setStrokeColor(INK)
    c.setLineWidth(0.8)
    c.line(L, y, R, y)
    y -= 12 * MM

    rows = [
        ("펴낸 날", f"{spec.VERSION.split('·')[1].strip()}"),
        ("판·쇄", "초판 1쇄"),
        ("지은이", "　"),
        ("펴낸곳", "　"),
        ("ISBN", "　"),
        ("", ""),
        ("분량", f"A4 {info['final_pages']}쪽 · 그림 139개 · 인용 출처 166개"),
        ("구성", "본문 18개 모듈 · 캡스톤 5편 · 부록 A–E · 커리큘럼 설계서"),
        ("원본", "https://github.com/moratorium000/motherlord"),
        ("", ""),
        ("만든 방법", "마크다운 원본 → pandoc → DOCX → LibreOffice → PDF."),
        ("", "그림은 Matplotlib · scikit-rf · Mermaid · 인라인 SVG 로"),
        ("", "전부 스크립트가 생성하며, 각 스크립트는 자체 검산 결과를"),
        ("", "함께 출력합니다. 저장소의 검사 스크립트를 돌리면 본문의"),
        ("", "숫자·상호 참조·축약어·출처가 서로 맞는지 확인됩니다."),
    ]
    c.setFont("N", 9)
    for k, v in rows:
        if k:
            c.setFillColor(SOFT)
            c.setFont("NB", 9)
            c.drawString(L, y, k)
        c.setFillColor(INK)
        c.setFont("N", 9)
        c.drawString(L + 26 * MM, y, v)
        y -= 5.6 * MM

    # 아래쪽 주의 문구
    y = 52 * MM
    c.setStrokeColor(SOFT)
    c.setLineWidth(0.4)
    c.line(L, y + 8 * MM, R, y + 8 * MM)
    c.setFillColor(SOFT)
    c.setFont("NL", 8)
    for ln in [
        "이 책은 외부 웹 접속이 막힌 환경에서 집필되었습니다. 모든 사실은 독립 출처",
        "두 곳 이상으로 교차검증했으나 원문을 직접 열어 보지는 못했습니다. 각 모듈",
        "끝의 출처 표에 원문 주소와 신뢰 등급을 적어 두었으니, 중요한 수치는 반드시",
        "원문에서 확인하십시오. 본문에 인용한 규격 한도값은 설명을 위한 것이며,",
        "규격은 개정되고 지역·제품 분류에 따라 달라지므로 실제 판정은 최신 원문과",
        "인증 시험소의 확인을 받아야 합니다.",
    ]:
        c.drawString(L, y, ln)
        y -= 4.6 * MM

    c.showPage()
    c.save()


def blank(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=(PAGE_W, PAGE_H))
    c.showPage()
    c.save()


# ─────────────────────────────────────────────────────────── 본체
def main() -> int:
    global SRC, OUT
    vol = int(next((a for a in sys.argv[1:] if a.isdigit()), "1"))
    cp = spec.use(vol)
    SRC, OUT = spec.BODY_PDF, ROOT / "04_인쇄" / cp["body_out"]
    if not SRC.exists():
        sys.exit(f"본문 PDF 가 없습니다: {SRC}")
    register_fonts()
    info = spec.report()

    tmp = Path(tempfile.mkdtemp())
    colophon(tmp / "colophon.pdf", info)
    blank(tmp / "blank.pdf")

    reader = PdfReader(str(SRC))
    n_src = len(reader.pages)
    writer = PdfWriter()

    shifted = {"recto": 0, "verso": 0}
    for i, page in enumerate(reader.pages):
        # PDF 1쪽이 책의 1쪽(오른쪽 면)이다.
        recto = (i % 2 == 0)
        dx = GUTTER if recto else -GUTTER
        page.add_transformation(Transformation().translate(tx=dx, ty=0))
        shifted["recto" if recto else "verso"] += 1
        writer.add_page(page)

    # 백면으로 채운 뒤 마지막 장에 판권지를 놓는다 (판권은 책의 맨 뒷면).
    n_final = info["final_pages"]
    blank_reader = PdfReader(str(tmp / "blank.pdf"))
    colo_reader = PdfReader(str(tmp / "colophon.pdf"))
    n_blank = n_final - n_src - 1
    if n_blank < 0:
        sys.exit("쪽수 계산이 어긋났습니다")
    for _ in range(n_blank):
        writer.add_page(blank_reader.pages[0])
    colo = colo_reader.pages[0]
    # 판권지는 짝수 쪽(왼쪽 면)에 놓이므로 왼쪽으로 민다
    colo.add_transformation(Transformation().translate(tx=-GUTTER, ty=0))
    writer.add_page(colo)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "wb") as f:
        writer.write(f)

    print()
    print(f"본문 인쇄용 → {OUT.relative_to(ROOT)}")
    print(f"  원본 {n_src}쪽 + 백면 {n_blank}쪽 + 판권지 1쪽 = "
          f"{len(writer.pages)}쪽")
    print(f"  접지 여백 {spec.GUTTER_MM:.0f} mm — "
          f"오른쪽 면 {shifted['recto']}쪽은 오른쪽으로, "
          f"왼쪽 면 {shifted['verso']}쪽은 왼쪽으로")
    verify(n_final)
    return 0


def verify(expect_pages: int) -> None:
    """정말로 밀렸는지 글자 좌표로 확인한다. 눈으로 보면 5 mm 는 안 보인다."""
    print("-" * 66)
    ok = []

    def chk(cond, msg):
        ok.append(cond)
        print(f"  [{'OK ' if cond else '실패'}] {msg}")

    out = subprocess.run(["pdfinfo", str(OUT)], capture_output=True, text=True)
    pages = size = None
    for line in out.stdout.splitlines():
        if line.startswith("Pages:"):
            pages = int(line.split()[1])
        if line.startswith("Page size:"):
            size = line
    chk(pages == expect_pages, f"쪽수 {pages} = 계산값 {expect_pages}")
    chk(pages % 4 == 0, "4의 배수 (대수 맞춤)")
    chk(size is not None and "595" in size and "841" in size,
        f"판면이 A4 그대로 ({size.split(':')[1].strip() if size else '?'})")

    # 같은 쪽의 글자 x 좌표를 원본과 견준다
    def first_x(pdf: Path, page: int) -> float:
        r = subprocess.run(["pdftotext", "-bbox", "-f", str(page),
                            "-l", str(page), str(pdf), "-"],
                           capture_output=True, text=True)
        for line in r.stdout.splitlines():
            if "<word " in line:
                return float(line.split('xMin="')[1].split('"')[0])
        return float("nan")

    mmpt = spec.GUTTER_MM * MM
    for page, want, label in ((5, +mmpt, "5쪽(오른쪽 면)"),
                              (6, -mmpt, "6쪽(왼쪽 면)")):
        d = first_x(OUT, page) - first_x(SRC, page)
        chk(abs(d - want) < 0.5,
            f"{label} 글자가 {d:+.1f} pt 이동 (기대 {want:+.1f} pt "
            f"= {want / MM:+.0f} mm)")

    # 발주서에 적은 숫자가 실제 파일과 맞는지도 본다. 발주서는 사람이
    # 읽고 인쇄소가 그대로 믿는 문서라, 여기가 어긋나면 잘못 찍힌다.
    order = ROOT / "04_인쇄" / "인쇄_발주서.md"
    if order.exists():
        txt = order.read_text(encoding="utf-8")
        for want, what in [
            (f"{expect_pages}쪽", "총 쪽수"),
            (f"{spec.spine_mm(expect_pages):.1f} mm", "책등 두께"),
            (f"{spec.GUTTER_MM:.0f} mm", "접지 여백"),
        ]:
            chk(want in txt, f"발주서의 {what} 표기 '{want}' 가 계산값과 같음")
        cov = ROOT / "04_인쇄" / spec.copy()["cover_out"]
        if cov.exists():
            from pypdf import PdfReader
            box = PdfReader(str(cov)).pages[0]["/TrimBox"]
            w = (float(box[2]) - float(box[0])) / MM
            chk(f"{w:.1f} mm" in txt or f"{w:.1f} ×" in txt,
                f"발주서의 표지 재단 폭 {w:.1f} mm 가 PDF 와 같음")

    if not all(ok):
        sys.exit("본문 검산 실패")
    print(f"\n  검산 {len(ok)}항목 전부 통과")


if __name__ == "__main__":
    sys.exit(main())
