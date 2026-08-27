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

# ── 두 권 ────────────────────────────────────────────────────────────────
# 기본 과정만으로도 A4 567쪽·책등 29 mm 라 심화를 얹으면 한 권으로는 무선제본
# 한계를 넘는다. 그래서 1권(기본)·2권(심화)으로 나눈다. 아래 표가 두 권의
# 차이를 전부 담고 있고, 나머지 계산은 권과 무관하게 같은 식을 쓴다.
VOLUMES = {
    1: dict(
        pdf="RF_시스템_엔지니어링_교재_1권_기본.pdf",
        body_out="본문_인쇄용_1권.pdf",
        cover_out="표지_전개도_1권.pdf",
        version="1권 · v1.4 · 2026-08",
        vol_tag="1권 · 기본 과정",
        sub1="전기전자 초심자에서 실무자까지",
        sub2="커리큘럼과 교육자료",
        contents="본문 18개 모듈 · 캡스톤 · 부록 A–E",
        spine_sub="M00–M17 · 캡스톤 · 부록",
        blurb=[
            '"잘 터지게 해 주세요" 라는 말을 받아',
            '"LNA 는 잡음지수 1.5 dB 이하" 라는 숫자로 바꾸고,',
            "그 숫자가 맞는지 장비로 재서 판정하는 일 — 그것이",
            "RF 시스템 엔지니어의 일입니다. 이 책은 데시벨부터",
            "시작해 거기까지 갑니다.",
        ],
        toc=[
            ("Part 0", "RF 시스템 엔지니어링이란"),
            ("Part I", "데시벨 · 전송선로 · S-파라미터"),
            ("Part II", "RF 실험실 입문 · 첫 측정"),
            ("Part III", "수동소자 · 필터 · 증폭기 · 주파수 변환"),
            ("Part IV", "안테나 · 트랜시버 · 예산 설계 · 변조"),
            ("Part V", "교정과 불확도 · 정밀 측정 · 검증과 튜닝 · 보드 설계"),
            ("Part VI", "캡스톤 — 2.4 GHz 송수신 트랜시버"),
            ("부록", "축약어 · 공식 치트시트 · 출처 · 장비 · 수학 보충"),
        ],
        promises=[
            "① 축약어는 처음 나올 때 원어와 우리말을 함께 적는다",
            "② 개념마다 주인이 되는 모듈이 하나씩 있다",
            "③ 모든 수치는 계산으로 확인했고 스크립트로 재현된다",
            "④ 모든 사실에 출처와 신뢰 등급을 붙였다",
        ],
        numbers=[
            ("77 dB", "26 MHz 클럭을 대역 밖으로 못 옮길 때 필요한 격리"),
            ("34.6배", "커패시터 한 종을 빼면 전원망 반공진이 넘는 배수"),
            ("2.50 GHz", "100 × 75 mm 실드 캔이 공진하는 주파수"),
            ("52 %", "확장불확도만큼 가드밴드를 두면 버리는 양품 비율"),
        ],
        srcdirs=("01_모듈", "02_캡스톤", "03_부록"),
    ),
    2: dict(
        pdf="RF_시스템_엔지니어링_교재_2권_심화.pdf",
        body_out="본문_인쇄용_2권.pdf",
        cover_out="표지_전개도_2권.pdf",
        version="2권 · v1.0 · 2026-08",
        vol_tag="2권 · 심화 과정",
        sub1="벤치 엔지니어",
        sub2="받은 보드를 양산으로 넘기기까지",
        contents="본문 12개 모듈 · 심화 캡스톤 · 부록 A",
        spine_sub="B01–B12 · 심화 캡스톤",
        blurb=[
            "1권이 \"이 값을 어떻게 재는가\" 였다면",
            "2권은 \"이 값을 믿어도 되는가\" 입니다.",
            "완성된 보드를 받아 살려내고, 재고, 판정하고,",
            "고쳐서 양산으로 넘기는 일 — 벤치 엔지니어의",
            "일을 절차와 계산으로 옮겼습니다.",
        ],
        toc=[
            ("Part A", "벤치 방법론 · 시간 영역 · 픽스처 · 대신호"),
            ("", "잡음 파라미터 · 위상잡음 (B01–B06)"),
            ("Part B", "EMC 디버그 · 전원·열 · OTA · 디센스 (B07–B10)"),
            ("Part C", "측정 시스템 분석 · 양산 이관 (B11–B12)"),
            ("Part D", "심화 캡스톤 — 받은 보드를 양산으로"),
            ("부록", "축약어 (나머지 부록은 1권)"),
        ],
        promises=[
            "① 모든 모듈에 T0(장비 없이) 대체 실습을 함께 둔다",
            "② 그 대체로 무엇을 못 얻는지도 함께 적는다",
            "③ 수치는 자체 검산이 붙은 스크립트로 재현된다",
            "④ 검산이 실패한 자리를 지우지 않고 본문으로 실었다",
        ],
        numbers=[
            ("9.6 dB", "교차상관 위상잡음이 좋은 쪽으로만 틀리는 양"),
            ("347배", "빈 벌크 커패시터가 만드는 돌입 첨두 / 정상 전류"),
            ("0.000 dB", "스프레드 스펙트럼을 켜도 그대로인 대역 총전력"),
            ("72 %", "수율 96 % 라인에서 떨어진 것 중 멀쩡했던 몫"),
        ],
        srcdirs=("05_심화",),
    ),
}

VOL = 1
_V = VOLUMES[VOL]
BODY_PDF = ROOT / _V["pdf"]


def use(vol: int) -> dict:
    """작업할 권을 고른다. 이 함수를 부른 뒤 spec 의 값을 읽어야 한다."""
    global VOL, _V, BODY_PDF, VERSION
    if vol not in VOLUMES:
        raise SystemExit(f"권 번호는 {sorted(VOLUMES)} 중 하나여야 합니다.")
    VOL, _V = vol, VOLUMES[vol]
    BODY_PDF = ROOT / _V["pdf"]
    VERSION = _V["version"]
    return _V


def copy() -> dict:
    """현재 권의 표지 문안."""
    return _V


def count_figures_and_sources(vol: int | None = None) -> tuple[int, int]:
    """표지에 적을 그림 수와 출처 수를 **세어서** 얻는다.

    손으로 적어 두면 반드시 낡는다 — 실제로 앞표지에 "그림 139개 · 출처
    166개" 가 굳어 있었고, 그 사이 그림은 172개가 되어 있었다.
    """
    import re
    v = VOLUMES[vol or VOL]
    figs, urls = 0, set()
    link = re.compile(r"\]\((https?://[^)\s]+)")
    for d in v["srcdirs"]:
        for f in sorted((ROOT / d).glob("*.md")):
            # 부록 C 는 출처를 **모아 놓은** 문서라 세면 두 번 센다.
            if f.name.startswith("C_출처"):
                continue
            txt = f.read_text(encoding="utf-8")
            figs += len(re.findall(r"^!\[", txt, re.M))
            figs += len(re.findall(r"^```mermaid$", txt, re.M))
            urls.update(link.findall(txt))
    return figs, len(urls)

MM = 72.0 / 25.4          # 1 mm 를 PDF 단위(pt)로

# ── 판형 ────────────────────────────────────────────────────────────────
TRIM_W_MM = 210.0         # A4 세로
TRIM_H_MM = 297.0
BLEED_MM = 3.0            # 도련. 국내 인쇄소 표준
SAFE_MM = 5.0             # 재단 안전선 (글자는 이 안쪽에)

# ── 제본 ────────────────────────────────────────────────────────────────
BINDING = "무선제본(퍼펙트 바인딩)"
VERSION = _V["version"]
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


def page_count(pdf: Path | None = None) -> int:
    """실제 PDF 에서 쪽수를 읽는다. 손으로 적으면 반드시 어긋난다.

    기본값을 인자에 박아 두면 함수를 정의할 때의 1권 경로가 굳어, use(2) 를
    불러도 1권 쪽수를 읽는다. 실제로 그렇게 두 권이 같은 값으로 나왔다.
    """
    pdf = pdf or BODY_PDF
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
    print(f"제본 규격 — {_V['vol_tag']}")
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
    # 무선제본은 등이 너무 얇으면 풀이 물릴 자리가 없고, 너무 두꺼우면
    # 펼침이 나빠 등이 갈라진다. 국내 인쇄소가 흔히 받는 범위는 대략
    # 5~40 mm 다. 한 권일 때 하한을 20 mm 로 두었던 것은 그 책이 두꺼워서
    # 였을 뿐, 규격이 아니었다 — 2권(14.3 mm)에서 걸려 바로잡았다.
    chk(5 <= s <= 40,
        f"책등 {s:.1f} mm 가 무선제본 가능 범위(5~40 mm) 안")
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
    # 인자 없이 돌리면 두 권을 모두 계산한다.
    args = [a for a in sys.argv[1:] if a.isdigit()]
    for _v in ([int(a) for a in args] or sorted(VOLUMES)):
        use(_v)
        print(f"\n########## {_V['vol_tag']} ##########")
        report()
