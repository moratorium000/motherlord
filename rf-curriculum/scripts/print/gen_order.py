#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""인쇄·제본 발주서를 **계산해서** 쓴다.

발주서는 인쇄소가 그대로 믿고 찍는 문서다. 쪽수·책등·전개도 크기가 하나라도
어긋나면 표지가 잘못 재단된다. 그런데 이 숫자들은 원고가 한 쪽만 늘어도
바뀐다 — 손으로 적어 두면 반드시 낡는다.

그래서 `spec.py` 의 계산값과 실제 PDF 에서 읽은 값으로 문서를 만든다.
`make_body.py` 의 검산이 이 문서의 숫자를 다시 대조하므로, 둘이 어긋나면
빌드가 멈춘다.

    python3 scripts/print/gen_order.py

출력: 04_인쇄/인쇄_발주서.md (두 권을 한 문서에)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spec  # noqa: E402

ROOT = spec.ROOT
OUT = ROOT / "04_인쇄" / "인쇄_발주서.md"


def trimbox_mm(pdf: Path) -> tuple[float, float]:
    from pypdf import PdfReader
    box = PdfReader(str(pdf)).pages[0]["/TrimBox"]
    return ((float(box[2]) - float(box[0])) / spec.MM,
            (float(box[3]) - float(box[1])) / spec.MM)


def pdf_pages(pdf: Path) -> int:
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
    for ln in out.stdout.splitlines():
        if ln.startswith("Pages:"):
            return int(ln.split()[1])
    raise SystemExit(f"쪽수를 읽지 못했습니다: {pdf}")


def mb(p: Path) -> str:
    return f"{p.stat().st_size / 1024 / 1024:.1f} MB"


def volume_block(vol: int) -> tuple[str, dict]:
    cp = spec.use(vol)
    info = spec.report()
    body = ROOT / "04_인쇄" / cp["body_out"]
    cover = ROOT / "04_인쇄" / cp["cover_out"]
    pages = pdf_pages(body)
    tw, th = trimbox_mm(cover)
    n_fig, n_src = spec.count_figures_and_sources(vol)
    s = info["spine"]

    lines = [
        f"## {vol}권 — {cp['sub1']}",
        "",
        f"**{cp['contents']}** · 그림 {n_fig}개 · 출처 {n_src}개",
        "",
        "| 항목 | 사양 |",
        "|---|---|",
        f"| **총 쪽수** | **{pages}쪽** ({pages // 4}대수 · 4의 배수) |",
        f"| **책등 두께** | **{s:.1f} mm** |",
        f"| 표지 재단 크기 | {tw:.1f} × {th:.0f} mm |",
        f"| 본문 파일 | `{cp['body_out']}` ({mb(body)}) |",
        f"| 표지 파일 | `{cp['cover_out']}` ({mb(cover)}) |",
        "",
        "### 책등 계산",
        "",
        "| 항목 | 계산 | 두께 |",
        "|---|---|---|",
        (f"| 본문 | {pages // 2}장 × {spec.BODY_PAPER.thickness_mm:.3f} mm | "
         f"{pages / 2 * spec.BODY_PAPER.thickness_mm:.2f} mm |"),
        (f"| 면지 | {spec.END_SHEETS}장 × "
         f"{spec.END_PAPER.thickness_mm:.3f} mm | "
         f"{spec.END_SHEETS * spec.END_PAPER.thickness_mm:.2f} mm |"),
        (f"| 표지 | 2장 × {spec.COVER_PAPER.thickness_mm:.3f} mm | "
         f"{2 * spec.COVER_PAPER.thickness_mm:.2f} mm |"),
        f"| | **합계** | **{s:.2f} mm → {s:.1f} mm** |",
        "",
    ]
    return "\n".join(lines), dict(pages=pages, spine=s, tw=tw, th=th)


def main() -> int:
    blocks, infos = [], {}
    for v in sorted(spec.VOLUMES):
        text, info = volume_block(v)
        blocks.append(text)
        infos[v] = info

    doc = f"""# 인쇄·제본 발주서

**품명**: RF 시스템 엔지니어링 — 전기전자 초심자에서 실무자까지 (전 2권)
**작성 기준**: `scripts/print/spec.py` 계산값 · 쪽수는 실제 PDF 에서 읽음

> 이 문서는 **손으로 쓴 것이 아니라 `scripts/print/gen_order.py` 가
> 만든 것**입니다. 원고가 한 쪽만 늘어도 쪽수와 책등이 바뀌므로, 원고를
> 고친 뒤에는 반드시 다시 돌려 주십시오. `make_body.py` 의 검산이 이
> 문서의 숫자를 다시 대조하므로 어긋나면 빌드가 멈춥니다.

---

## 0. 두 권으로 나눈 이유

한 권으로 묶으면 A4 {infos[1]['pages'] + infos[2]['pages']}쪽,
책등 {infos[1]['spine'] + infos[2]['spine']:.0f} mm 가 되어 무선제본이
버티지 못합니다. 나누는 자리는 독자가 갈리는 자리와 같습니다 —
**1권은 배우는 사람, 2권은 이미 보드를 받아 든 사람**입니다.

---

## 1. 두 권 공통 사양

| 항목 | 사양 |
|---|---|
| **판형** | A4 {spec.TRIM_W_MM:.0f} × {spec.TRIM_H_MM:.0f} mm 세로 |
| **제본** | {spec.BINDING}, 좌철 |
| **본문 인쇄** | 흑백 1도 양면 |
| **본문 용지** | {spec.BODY_PAPER.name} |
| **표지 인쇄** | 컬러 4도 단면 (표1·책등·표4) |
| **표지 용지** | {spec.COVER_PAPER.name} |
| **표지 후가공** | 무광 라미네이팅 |
| **면지** | {spec.END_PAPER.name} 앞뒤 각 1장 |
| **도련** | {spec.BLEED_MM:.0f} mm |
| **접지 여백(gutter)** | 안쪽 +{spec.GUTTER_MM:.0f} mm |
| **부수** | 1권 ____ 부 · 2권 ____ 부 |

두 권의 판형·용지·후가공은 같습니다. **다른 것은 쪽수와 책등뿐**입니다.

---

{blocks[0]}
---

{blocks[1]}
---

## 4. 넘기는 파일

| 파일 | 내용 |
|---|---|
| `본문_인쇄용_1권.pdf` | 1권 본문 {infos[1]['pages']}쪽. 접지 여백 반영, 판권지·백면 포함 |
| `표지_전개도_1권.pdf` | 1권 표4 + 책등 + 표1 한 장 |
| `본문_인쇄용_2권.pdf` | 2권 본문 {infos[2]['pages']}쪽. 같은 규칙 |
| `표지_전개도_2권.pdf` | 2권 표4 + 책등 + 표1 한 장 |

**PDF 1장 = 인쇄 1면**입니다. 터잡기(면부치기)는 하지 않았으므로 인쇄소에서
진행해 주십시오. 표지 PDF 에는 **TrimBox·BleedBox 가 박혀 있고**, 재단선과
책등 접는선도 도련 바깥에 그려 두었습니다.

---

## 5. 확인 부탁드립니다

**종이 부피(bulk)는 제지사·롯트마다 다릅니다.** 위 책등은 아래 어림치로
계산했습니다 — 귀사 기준으로 다시 계산해 주시고 값이 다르면 알려 주십시오.
표지 전개도를 그 값으로 다시 뽑아 보내겠습니다.

| 용지 | 평량 | 부피 | 장당 두께 |
|---|---|---|---|
| {spec.BODY_PAPER.name} | {spec.BODY_PAPER.gsm:.0f} g/m² | {spec.BODY_PAPER.bulk:.2f} | {spec.BODY_PAPER.thickness_mm:.3f} mm |
| {spec.END_PAPER.name} | {spec.END_PAPER.gsm:.0f} g/m² | {spec.END_PAPER.bulk:.2f} | {spec.END_PAPER.thickness_mm:.3f} mm |
| {spec.COVER_PAPER.name} | {spec.COVER_PAPER.gsm:.0f} g/m² | {spec.COVER_PAPER.bulk:.2f} | {spec.COVER_PAPER.thickness_mm:.3f} mm |

책등이 ±1 mm 어긋나면 표1의 제목이 책등으로 말려 들어가거나 표4가 앞으로
넘어옵니다. 표지 디자인은 책등 양옆으로 **20 mm 안쪽까지 글자가 없도록**
비워 두었으니, 그 범위 안의 오차는 표지가 흡수합니다.

---

## 6. 본문 판면

| 항목 | 값 |
|---|---|
| 위·아래 여백 | 20 mm |
| 좌우 여백 | 25 mm (접지 여백 반영 시 안쪽 30 mm / 바깥 20 mm) |
| 쪽번호 | 아래 가운데, 모든 쪽 |

접지 여백은 홀수 쪽(오른쪽 면)은 오른쪽으로, 짝수 쪽(왼쪽 면)은 왼쪽으로
글자를 {spec.GUTTER_MM:.0f} mm 씩 밀어 넣는 방식으로 반영했습니다. 무선제본은
안쪽이 말려 들어가므로 이 여백이 없으면 안쪽 글자가 읽히지 않습니다.
"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"발주서 → {OUT.relative_to(ROOT)}")
    for v, i in infos.items():
        print(f"  {v}권  {i['pages']}쪽 · 책등 {i['spine']:.1f} mm · "
              f"표지 재단 {i['tw']:.1f} × {i['th']:.0f} mm")
    return 0


if __name__ == "__main__":
    sys.exit(main())
