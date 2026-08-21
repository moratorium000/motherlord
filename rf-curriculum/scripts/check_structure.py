#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""17단계 · 전체 구조 정합성 검토.

교재 전체(모듈 18편 + 캡스톤 5편 + 부록 5편 + 설계서 + README)를 읽어
아래 항목을 기계적으로 검사한다. 사람 눈으로는 놓치는 종류의 오류만
잡는 것이 목적이다.

  A. 상호 참조 — `M12 §5` 형태의 참조가 실제 존재하는 절인가
  B. 링크 — 상대 경로 링크의 대상 파일이 실제로 있는가
  C. 그림 — 삽입한 이미지 파일이 실제로 있는가
  D. 소유 개념 — 두 모듈이 같은 개념을 소유한다고 주장하지 않는가
  E. 그림 번호 — 모듈 안에서 1부터 빠짐없이 이어지는가
  F/G. 축약어 — scripts/check_abbr.py 로 분리 (지침 2)
  H. 용어 표기 — 같은 뜻을 두 가지로 적지 않는가
  I. 분량 — 모듈이 선언한 시간이 설계서 계획과 맞는가

실행: python3 scripts/check_structure.py
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

problems: list[tuple[str, str]] = []   # (검사 항목, 설명)
notes: list[str] = []


def bad(kind: str, msg: str) -> None:
    problems.append((kind, msg))


# ---------------------------------------------------------------- 파일 수집

def collect() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for sub in ("01_모듈", "02_캡스톤", "03_부록"):
        for p in sorted((ROOT / sub).glob("*.md")):
            out[str(p.relative_to(ROOT))] = p
    for name in ("README.md",):
        out[name] = ROOT / name
    for p in sorted(ROOT.glob("00_*.md")):
        out[str(p.relative_to(ROOT))] = p
    return out


DOCS = collect()
TEXT = {k: p.read_text(encoding="utf-8") for k, p in DOCS.items()}

# 모듈 코드 → 상대 경로
MOD_FILE: dict[str, str] = {}
for key in DOCS:
    m = re.match(r"01_모듈/(M\d\d)_", key)
    if m:
        MOD_FILE[m.group(1)] = key

# 모듈 코드 → 존재하는 절 번호 집합 (## M12.5 ... 형태)
MOD_SECTIONS: dict[str, dict[int, str]] = {}
for code, key in MOD_FILE.items():
    secs: dict[int, str] = {}
    for m in re.finditer(rf"^##\s+{code}\.(\d+)\s+([^\n]*)$", TEXT[key], re.M):
        secs[int(m.group(1))] = m.group(2).strip()
    MOD_SECTIONS[code] = secs

# 캡스톤/부록도 절을 가진다
OTHER_SECTIONS: dict[str, dict[str, str]] = {}
for key, txt in TEXT.items():
    d: dict[str, str] = {}
    for m in re.finditer(r"^##+\s+([^\n]*)$", txt, re.M):
        d[m.group(1).strip()] = key
    OTHER_SECTIONS[key] = d


# ------------------------------------------------------- A. 상호 참조 검사

# `M12 §5`, `M12 §5.2`, `M08 §5` — 공백/비공백 모두 허용
REF = re.compile(r"(M\d\d)\s*§\s*(\d+)")

ref_count = 0
for key, txt in TEXT.items():
    for m in REF.finditer(txt):
        code, num = m.group(1), int(m.group(2))
        ref_count += 1
        if code not in MOD_FILE:
            bad("A", f"{key}: 존재하지 않는 모듈 {code} 를 참조")
            continue
        if num not in MOD_SECTIONS[code]:
            have = ",".join(str(n) for n in sorted(MOD_SECTIONS[code]))
            bad("A", f"{key}: {code} §{num} 없음 (있는 절: {have})")
notes.append(f"A. 모듈 절 참조 {ref_count}건 확인")


# ------------------------------------------------------------- B. 링크 검사

LINK = re.compile(r"\[([^\]]*)\]\((\.{1,2}/[^)\s]+)\)")
link_count = 0
for key, txt in TEXT.items():
    base = DOCS[key].parent
    for m in LINK.finditer(txt):
        target = m.group(2).split("#", 1)[0]
        if not target:
            continue
        link_count += 1
        if not (base / target).resolve().exists():
            bad("B", f"{key}: 링크 대상 없음 → {m.group(2)}")
notes.append(f"B. 상대 경로 링크 {link_count}건 확인")


# ------------------------------------------------------------- C. 그림 파일

IMG = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
img_count = 0
for key, txt in TEXT.items():
    base = DOCS[key].parent
    for m in IMG.finditer(txt):
        src = m.group(2)
        if src.startswith("http"):
            continue
        img_count += 1
        if not (base / src).resolve().exists():
            bad("C", f"{key}: 그림 파일 없음 → {src}")
notes.append(f"C. 삽입 그림 {img_count}건 확인")


# --------------------------------------------------------- D. 소유 개념 중복

# 머리표의 "이 모듈이 소유하는 개념" 행에서 개념을 뽑는다.
OWNER_ROW = re.compile(r"^\|\s*\*\*이 모듈이 소유하는 개념\*\*\s*\|(.+)\|\s*$", re.M)

def norm_concept(s: str) -> str:
    s = re.sub(r"\*+", "", s)
    s = re.sub(r"\([^)]*\)", "", s)       # 괄호 안 영문 풀이 제거
    s = re.sub(r"[·,]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()

owners: dict[str, list[str]] = defaultdict(list)
for code, key in sorted(MOD_FILE.items()):
    m = OWNER_ROW.search(TEXT[key])
    if not m:
        bad("D", f"{key}: 머리표에 '이 모듈이 소유하는 개념' 행이 없음")
        continue
    for raw in m.group(1).split(","):
        c = norm_concept(raw)
        if len(c) < 3:
            continue
        owners[c].append(code)

dupes = {c: v for c, v in owners.items() if len(set(v)) > 1}
for c, v in sorted(dupes.items()):
    bad("D", f"개념 '{c}' 를 {', '.join(sorted(set(v)))} 가 함께 소유한다고 선언")
notes.append(f"D. 소유 개념 {len(owners)}종 확인 ({len(MOD_FILE)}개 모듈)")


# --------------------------------------------------------- E. 그림 번호 연속

FIGCAP = re.compile(r"^\*그림\s+(M\d\d|P\d|C)-(\d+)\.", re.M)
for code, key in sorted(MOD_FILE.items()):
    nums = [int(m.group(2)) for m in FIGCAP.finditer(TEXT[key])
            if m.group(1) == code]
    if not nums:
        continue
    want = list(range(1, len(nums) + 1))
    if nums != want:
        bad("E", f"{key}: 그림 번호가 {nums} — 1..{len(nums)} 이어야 함")
    # 본문에서 부르는 번호가 캡션 범위를 넘는지
    for m in re.finditer(rf"그림\s+{code}-(\d+)", TEXT[key]):
        n = int(m.group(1))
        if n > len(nums):
            bad("E", f"{key}: 본문이 그림 {code}-{n} 을 부르는데 캡션은 "
                     f"{len(nums)}개뿐")
notes.append("E. 모듈별 그림 번호 연속성 확인")


# ------------------------------------------------------- F/G. 축약어 병기

# 축약어 검사는 판정 규칙이 길어서 scripts/check_abbr.py 로 떼어 놨다.
# 여기서 얼기설기 다시 만들면 두 곳의 판정이 어긋난다.
notes.append("F/G. 축약어 병기는 scripts/check_abbr.py 가 맡는다")


# ----------------------------------------------------------- H. 용어 표기

VARIANTS = [
    ("스미스 차트", "스미스차트"),
    ("데이터 시트", "데이터시트"),
    ("잡음 지수", "잡음지수"),
    ("반사 계수", "반사계수"),
    ("정재파 비", "정재파비"),
    ("임피던스 정합", "임피던스 매칭"),
    ("네트워크 애널라이저", "네트워크 분석기"),
    ("스펙트럼 애널라이저", "스펙트럼 분석기"),
    ("디엠베딩", "디임베딩"),
    ("캐스케이드", "캐스케이딩"),
    ("주파수 응답", "주파수응답"),
]
def h_body(txt: str) -> str:
    """표기 검사용 본문. 세면 안 되는 두 가지를 뺀다.

    - 마크다운 링크: 파일 이름(M03_S파라미터와스미스차트.md)이 걸린다
    - rfdh.com 목차 인용: 참고 사이트의 표현을 그대로 옮긴 것이라
      우리 표기로 고치면 인용이 아니게 된다 (설계서 §6.2, 원칙 1)
    """
    txt = re.sub(r"\[[^\]]*\]\([^)]*\)", " ", txt)
    txt = re.sub(r"^### 원칙 1\. 참고 사이트[^\n]*$.*?(?=^#{2,3} )",
                 " ", txt, flags=re.M | re.S)
    txt = re.sub(r"^### 6\.2 rfdh\.com[^\n]*$.*?(?=^#{2,3} )",
                 " ", txt, flags=re.M | re.S)
    return txt


H_TEXT = {k: h_body(v) for k, v in TEXT.items()}

for a, b in VARIANTS:
    na = sum(t.count(a) for t in H_TEXT.values())
    nb = sum(t.count(b) for t in H_TEXT.values())
    if na and nb:
        bad("H", f"표기 혼용: '{a}' {na}회 · '{b}' {nb}회")
notes.append(f"H. 용어 표기 {len(VARIANTS)}쌍 확인")


# ------------------------------------------------------------- I. 분량 표기

DESIGN = TEXT["00_커리큘럼_설계서_v1.2.md"]

# 설계서에는 모듈별 시간표가 없고 트랙별 주당 시간만 있다(§8). 그래서
# 여기서는 모듈이 분량을 빠짐없이 밝히는지와 총합만 본다.
decl: dict[str, tuple[float, float]] = {}
for code, key in sorted(MOD_FILE.items()):
    m = re.search(r"\*\*분량\*\*:\s*이론\s*([\d.]+)\s*h\s*\+\s*실습\s*([\d.]+)\s*h",
                  TEXT[key])
    if not m:
        bad("I", f"{key}: 머리말에 '이론 N h + 실습 N h' 표기가 없음")
        continue
    decl[code] = (float(m.group(1)), float(m.group(2)))

th = sum(a for a, _ in decl.values())
pr = sum(b for _, b in decl.values())
notes.append(f"I. 모듈 {len(decl)}편 분량 표기 확인 · "
             f"이론 {th:.0f} h + 실습 {pr:.0f} h = {th + pr:.0f} h")


# --------------------------------------------------- J. 주차표와 분량 대조

# 설계서 §4.2 주차표의 "본문 분량" 열은 모듈 머리말의 선언값을 옮겨 적은
# 것이다. 한쪽만 고치면 어긋나므로 기계로 맞춰 둔다.
m = re.search(r"^### 4\.2 표준[^\n]*$(.*?)(?=^### )", DESIGN, re.M | re.S)
if not m:
    bad("J", "설계서 §4.2 주차표를 찾지 못함")
else:
    plan_h: dict[str, int] = {}
    alloc = 0
    for row in re.finditer(r"^\|\s*\*{0,2}([\d]+(?:[–-][\d]+)?)\*{0,2}\s*\|"
                           r"([^|]*)\|\s*([^|]*?)\s*\|\s*(\d+)\s*h\s*\|",
                           m.group(1), re.M):
        code = re.search(r"M\d\d", row.group(2))
        alloc += int(row.group(4))
        if code:
            hh = re.match(r"(\d+)\s*h", row.group(3).strip())
            if not hh:
                bad("J", f"{code.group(0)}: 주차표에 본문 분량이 없음")
                continue
            plan_h[code.group(0)] = int(hh.group(1))
    for code in sorted(set(plan_h) & set(decl)):
        real = int(sum(decl[code]))
        if plan_h[code] != real:
            bad("J", f"{code}: 주차표 {plan_h[code]} h vs 본문 {real} h")
    mod_alloc = alloc - sum(int(r.group(1)) for r in
                            re.finditer(r"Capstone[^|]*\|[^|]*\|\s*(\d+)\s*h",
                                        m.group(1)))
    gap = int(th + pr) - mod_alloc
    note = re.search(r"모듈에 배정한 것은 \*\*(\d+)주 × (\d+) h = (\d+) h\*\*",
                     DESIGN)
    if not note:
        bad("J", "§4.2 '주차와 분량의 셈' 주석을 찾지 못함")
    elif int(note.group(3)) != mod_alloc:
        bad("J", f"주석의 배정 시간 {note.group(3)} h vs 표 합계 {mod_alloc} h")
    short = re.search(r"\*\*(\d+) h가 모자랍니다", DESIGN)
    if short and int(short.group(1)) != gap:
        bad("J", f"주석의 부족분 {short.group(1)} h vs 실제 {gap} h")
    notes.append(f"J. 주차표 대 본문 분량 {len(plan_h)}건 대조 · "
                 f"모듈 배정 {mod_alloc} h, 부족 {gap} h")


# ------------------------------------------------------------------- 출력

print("=" * 68)
print("17단계 · 전체 구조 정합성 검토")
print("=" * 68)
for n in notes:
    print("  ", n)
print("-" * 68)
if not problems:
    print("문제 0건")
else:
    by_kind: dict[str, list[str]] = defaultdict(list)
    for k, msg in problems:
        by_kind[k].append(msg)
    for k in sorted(by_kind):
        print(f"\n[{k}] {len(by_kind[k])}건")
        for msg in by_kind[k]:
            print("   -", msg)
    print(f"\n총 {len(problems)}건")
sys.exit(1 if problems else 0)
