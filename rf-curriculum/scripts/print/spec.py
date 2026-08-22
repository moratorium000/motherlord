#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""제본 규격을 한 곳에서 계산한다.

인쇄소에 넘길 때 가장 자주 틀리는 숫자가 **책등 두께**다. 표지 전개도의 폭이
곧 책등 두께에 달려 있고, 이것이 틀리면 앞표지 그림이 책등으로 말려 들어가거나
뒤표지가 앞으로 넘어온다. 그래서 쪽수와 종이 사양에서 계산으로 뽑고, 그 값을
표지 생성기와 발주서가 같이 쓴다.

책등 두께 = 본문 두께 + 면지 두께 + 표지 두께 × 2

종이 한 장의 두께는 `평량(g/m²) × 부피(bulk) / 1000` mm 로 어림한다. 부피는
지종마다 다르고 제지사마다도 조금씩 다르므로, **발주 전에 인쇄소에 확인받아야
하는 값**이다. 아래 값은 국내에서 흔히 쓰는 어림치다.

실행: python3 scripts/print/spec.py
"""

from __future__ import annotations

import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BODY_PDF = ROOT / "RF_시스템_엔지니어링_교재.pdf"

MM = 72.0 / 25.4          # 1 mm 를 PDF 단위(pt)로

# ── 판형 ────────────────────────────────────────────────────────────────
TRIM_W_MM = 210.0         # A4 세로
TRIM_H_MM = 297.0
BLEED_MM = 3.0            # 도련. 국내 인쇄소 표준
SAFE_MM = 5.0             # 재단 안전선 (글자는 이 안쪽에)

# ── 제본 ────────────────────────────────────────────────────────────────
BINDING = "무선제본(퍼펙트 바인딩)"
VERSION = "v1.3 · 2026-08"
GUTTER_MM = 5.0           # 안쪽으로 더 주는 여백. 두꺼운 책일수록 크게


@dataclass(frozen=True)
class Paper:
    name: str
    gsm: float            # 평량 g/m²
    bulk: float           # 부피 cm³/g

    @property
    def thickness_mm(self) -> float:
        return self.gsm * self.bulk / 1000.0


# 부피는 흔히 쓰는 어림치. 인쇄소 확인 필요.
BODY_PAPER = Paper("미색모조 80 g/m²", 80, 1.25)
END_PAPER = Paper("색지 120 g/m²", 120, 1.20)
COVER_PAPER = Paper("아트지 250 g/m²", 250, 0.80)

END_SHEETS = 2            # 앞뒤 면지 각 1장


def page_count(pdf: Path = BODY_PDF) -> int:
    """실제 PDF 에서 쪽수를 읽는다. 손으로 적으면 반드시 어긋난다."""
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
    for line in out.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split()[1])
    raise SystemExit(f"쪽수를 읽지 못했습니다: {pdf}")


def pad_to_signature(n: int, multiple: int = 4) -> int:
    """대수(signature) 단위로 맞춘 쪽수. 무선제본은 4의 배수가 안전하다."""
    return math.ceil(n / multiple) * multiple


def spine_mm(pages: int) -> float:
    """책등 두께(mm). 쪽수는 '면' 이므로 종이 장수는 그 절반이다."""
    sheets = pages / 2
    return (sheets * BODY_PAPER.thickness_mm
            + END_SHEETS * END_PAPER.thickness_mm
            + 2 * COVER_PAPER.thickness_mm)


def cover_spread_mm(pages: int) -> tuple[float, float]:
    """표지 전개도 크기(도련 포함). 뒤표지 + 책등 + 앞표지."""
    w = TRIM_W_MM * 2 + spine_mm(pages) + BLEED_MM * 2
    h = TRIM_H_MM + BLEED_MM * 2
    return w, h


def report() -> dict:
    raw = page_count()
    # 판권지 1쪽을 뒤에 붙이고 대수에 맞춘다
    final = pad_to_signature(raw + 1)
    s = spine_mm(final)
    cw, ch = cover_spread_mm(final)

    print("=" * 66)
    print("제본 규격")
    print("=" * 66)
    print(f"  판형          A4 {TRIM_W_MM:.0f} × {TRIM_H_MM:.0f} mm 세로")
    print(f"  제본          {BINDING}")
    print(f"  본문 쪽수     {raw} 쪽 → 판권지·백면 더해 {final} 쪽 "
          f"({final // 4}대수)")
    print(f"  본문 종이     {BODY_PAPER.name} "
          f"(장당 {BODY_PAPER.thickness_mm:.3f} mm)")
    print(f"  면지          {END_PAPER.name} × {END_SHEETS} 장")
    print(f"  표지 종이     {COVER_PAPER.name}")
    print("-" * 66)
    print(f"  본문 두께     {final / 2:.0f} 장 × {BODY_PAPER.thickness_mm:.3f}"
          f" = {final / 2 * BODY_PAPER.thickness_mm:.2f} mm")
    print(f"  면지 두께     {END_SHEETS} 장 × {END_PAPER.thickness_mm:.3f}"
          f" = {END_SHEETS * END_PAPER.thickness_mm:.2f} mm")
    print(f"  표지 두께     2 장 × {COVER_PAPER.thickness_mm:.3f}"
          f" = {2 * COVER_PAPER.thickness_mm:.2f} mm")
    print(f"  ── 책등       {s:.1f} mm")
    print("-" * 66)
    print(f"  표지 전개도   {cw:.0f} × {ch:.0f} mm (도련 {BLEED_MM:.0f} mm 포함)")
    print(f"                뒤표지 {TRIM_W_MM:.0f} + 책등 {s:.1f} "
          f"+ 앞표지 {TRIM_W_MM:.0f}")
    print(f"  본문 인쇄용   {TRIM_W_MM:.0f} × {TRIM_H_MM:.0f} mm, "
          f"도련 없음, 접지 여백 {GUTTER_MM:.0f} mm")

    # ── 자체 검산 ────────────────────────────────────────────────────
    print("-" * 66)
    checks = []

    def chk(ok, msg):
        checks.append(ok)
        print(f"  [{'OK ' if ok else '실패'}] {msg}")

    chk(final % 4 == 0, f"최종 쪽수 {final} 이 4의 배수")
    chk(final >= raw + 1, "판권지 자리가 확보됨")
    chk(abs(cw - (TRIM_W_MM * 2 + s + 2 * BLEED_MM)) < 1e-9,
        "전개도 폭 = 앞뒤표지 + 책등 + 도련")
    chk(20 <= s <= 40,
        f"책등 {s:.1f} mm 가 무선제본 가능 범위(20~40 mm) 안")
    # 손으로 한 번 더: 278장 × 0.1 = 27.8
    hand = final / 2 * 0.100 + 2 * 0.144 + 2 * 0.200
    chk(abs(hand - s) < 0.05,
        f"책등을 독립 계산으로 재확인 ({hand:.2f} vs {s:.2f} mm)")
    chk(TRIM_W_MM - 2 * SAFE_MM > 0 and BLEED_MM < SAFE_MM,
        "도련보다 안전선이 안쪽에 있음")

    if not all(checks):
        sys.exit("규격 검산 실패")
    print(f"\n  검산 {len(checks)}항목 전부 통과")

    return dict(raw_pages=raw, final_pages=final, spine=s,
                cover_w=cw, cover_h=ch)


if __name__ == "__main__":
    report()
