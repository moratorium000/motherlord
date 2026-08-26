#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""축약어 병기 검사 (커리큘럼 지침 2).

지침: "축약어는 뒤에 반드시 무슨 의미인지 병기할 것."

교재가 실제로 쓰는 방식은 세 겹이다.
  ① 본문 첫 등장에서 `잡음지수(Noise Figure, NF)` 처럼 풀어 쓴다
  ② 모듈 끝의 `## MXX.A 이 모듈의 축약어` 표에 모은다
  ③ 부록 A 마스터 목록에 모든 축약어를 모은다

이 스크립트는 ②와 ③을 기계적으로 검사한다. ①은 문장 형태가 다양해서
기계 판정이 어렵지만, 모듈 어딘가에 영문 풀이가 있는지는 확인한다.

  F1. 모듈이 쓴 축약어가 그 모듈의 축약어 표에 없다
  F2. 모듈이 쓴 축약어가 모듈 안 어디에서도 풀어 쓰이지 않았다
  F3. 모듈 축약어 표에 올렸는데 본문에서 쓰지 않는다 (죽은 항목)
  G1. 본문 축약어가 부록 A 에 없다
  G2. 부록 A 에 있는데 아무 문서도 쓰지 않는다

실행: python3 scripts/check_abbr.py
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DOCS: dict[str, Path] = {}
for sub in ("01_모듈", "02_캡스톤", "03_부록", "05_심화"):
    for p in sorted((ROOT / sub).glob("*.md")):
        DOCS[str(p.relative_to(ROOT))] = p
for p in sorted(ROOT.glob("00_*.md")):
    DOCS[str(p.relative_to(ROOT))] = p
DOCS["README.md"] = ROOT / "README.md"

TEXT = {k: p.read_text(encoding="utf-8") for k, p in DOCS.items()}

# 축약어가 아닌 대문자 토큰. 단위·원소기호·파일형식·영어 낱말·수식 기호.
STOP = set("""
A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
AND OR NOT THE OF IN ON AT TO IS IT IF FOR NO YES ALL ANY ONE TWO
HTTP HTTPS PDF CSV PNG SVG JPG URL API CLI GUI ID OS PC MAC WIN
OK NG PASS FAIL MIN MAX TYP AVG NOM ABS REF SET GET RUN
CU AU AG SN PB NI SI GE GA AS AL FE ZN TI CR MO
HZ KHZ MHZ GHZ DB DBM DBC DBI DBD DBW MW KW NW PW UW
V MA UA NA PA2 OHM K C0
TX RX2 UP DOWN LOW HIGH ON2 OFF
ISO IEC IEEE ITU FCC CE UL RTCA MIL EN JIS KS
NOTE TIP WARN INFO TODO FIXME
SCPI2 VISA2
AB AC AN APX BD BSD CAP DD DE DOCX FORMAT FR GB JC MSG OUT RIGHT SR
STEP SY TP TR VG WRONG XX ASCII OJT OCW
HUBER SUHNER TDK MIT KRISS AWR CST ADV
""".split())

ABBR = re.compile(r"(?<![A-Za-z0-9])([A-Z][A-Z0-9]{1,7})(?![A-Za-z0-9])")

# 축약어가 아니라 "이름표"인 토큰. 문서 번호(M12, L03, Q7), 소자 기호(S21,
# C1, R2, U3), 로마 숫자, 밴드 번호(B7) 따위.
NAMEISH = re.compile(
    r"^(?:M\d\d|L\d\d|P\d|Q\d+|S\d\d|B\d+|[A-Z]\d+|"
    r"I{1,3}|IV|VI{0,3}|IX|XI{0,3}|CUR|AN\d+|SNAA\d+|WP\d+)$")


def strip_code(t: str) -> str:
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"`[^`]*`", " ", t)
    t = re.sub(r"\$\$.*?\$\$", " ", t, flags=re.S)      # 수식 블록
    t = re.sub(r"\$[^$\n]*\$", " ", t)                  # 인라인 수식
    t = re.sub(r"\[[^\]]*\]\([^)]*\)", " ", t)          # 링크는 글자까지 통째로
    t = re.sub(r"^\|[^\n]*https?://[^\n]*$", " ", t, flags=re.M)  # 출처 표의 줄
    return t


def strip_sources(t: str) -> str:
    """출처·참고문헌 절을 뺀다. 문헌 제목 속 대문자는 축약어가 아니다."""
    return re.sub(r"^##+ [^\n]*(출처|참고 문헌|더 읽을)[^\n]*$.*?(?=^## |\Z)",
                  " ", t, flags=re.M | re.S)


def used_in(t: str) -> set[str]:
    return {m.group(1) for m in ABBR.finditer(strip_code(strip_sources(t)))
            if m.group(1) not in STOP and not NAMEISH.match(m.group(1))}


def table_terms(t: str) -> set[str]:
    """`| **NF** | Noise Figure | 잡음지수 |` 형태의 첫 칸을 모은다."""
    out: set[str] = set()
    for m in re.finditer(r"^\|\s*\*{0,2}([A-Za-z][A-Za-z0-9_\-/·&\s]{0,60}?)"
                         r"\*{0,2}\s*\|[^|]*\|[^|]*\|", t, re.M):
        first = m.group(1).replace("_", "")
        toks = re.split(r"[/·\s]+", first)
        toks += [x for tk in toks for x in tk.split("-") if x]
        for tok in toks:
            tok = tok.strip().upper()
            if tok and re.fullmatch(r"[A-Z][A-Z0-9\-]{0,9}", tok):
                out.add(tok)
    return out


problems: list[tuple[str, str]] = []
notes_f3: list[str] = []


def bad(kind: str, msg: str) -> None:
    problems.append((kind, msg))


# ------------------------------------------------------------- 부록 A 목록
APPX_A = TEXT["03_부록/A_축약어_마스터목록.md"]
A_TERMS = table_terms(APPX_A)

# ------------------------------------------------------------ 모듈별 검사
MOD_FILE = {re.match(r"01_모듈/(M\d\d)_", k).group(1): k
            for k in DOCS if re.match(r"01_모듈/M\d\d_", k)}

all_used: dict[str, set[str]] = defaultdict(set)

for code, key in sorted(MOD_FILE.items()):
    txt = TEXT[key]
    # 모듈 축약어 표 구간
    m = re.search(rf"^## {code}\.A [^\n]*$(.*?)(?=^## |\Z)", txt, re.M | re.S)
    mod_table = table_terms(m.group(1)) if m else set()
    body = txt[:m.start()] if m else txt

    used = used_in(body)
    for t in used:
        all_used[t].add(key)

    for t in sorted(used):
        if t in mod_table:
            continue
        # 모듈 안 어딘가에서 영문으로 풀어 썼는가
        expanded = re.search(rf"\(\s*[A-Z][A-Za-z\- ]{{3,}}[^)]*\b{t}\b[^)]*\)",
                             body) or \
                   re.search(rf"\b{t}\s*\(\s*[A-Z][A-Za-z\- ]{{3,}}", body)
        if expanded:
            bad("F1", f"{code}: {t} — 본문에서 풀어 썼으나 모듈 축약어 표에 없음")
        else:
            bad("F2", f"{code}: {t} — 모듈 안에서 한 번도 풀어 쓰지 않음")

    for t in sorted(mod_table - used - {"MHZ", "GHZ"}):
        if t in STOP:
            continue
        notes_f3.append(f"{code}: {t}")

# --------------------------------------------------------- 다른 문서 사용
for key, txt in TEXT.items():
    if key.startswith("01_모듈/") or key.startswith("03_부록/A_") \
            or key.startswith("03_부록/C_"):
        continue
    for t in used_in(txt):
        all_used[t].add(key)

for t, where in sorted(all_used.items()):
    if t not in A_TERMS:
        bad("G1", f"{t} — {len(where)}개 문서에서 쓰는데 부록 A 에 없음 "
                  f"(예: {sorted(where)[0]})")

# G2 는 흠이 아니라 참고 사항이다. 부록 A 는 커리큘럼 밖(데이터시트·규격서)에서
# 만날 축약어까지 담는 조회용 사전이고, dB·dBm 처럼 단위로 걸러진 것도 섞인다.
notes_g2 = sorted(A_TERMS - set(all_used))

# ------------------------------------------------------------------- 출력
print("=" * 68)
print("축약어 병기 검사 (지침 2)")
print("=" * 68)
print(f"   본문 축약어 {len(all_used)}종 · 부록 A {len(A_TERMS)}종")
print(f"   (참고) 부록 A 에만 있고 본문에서 안 쓰는 항목 {len(notes_g2)}건")
print(f"   (참고) 모듈 축약어 표에는 있으나 본문에서 안 쓰는 항목 {len(notes_f3)}건 — 조회용 표이므로 흠은 아님)")
print("-" * 68)
if not problems:
    print("문제 0건")
else:
    by: dict[str, list[str]] = defaultdict(list)
    for k, msg in problems:
        by[k].append(msg)
    for k in sorted(by):
        print(f"\n[{k}] {len(by[k])}건")
        for msg in by[k]:
            print("   -", msg)
    print(f"\n총 {len(problems)}건")
sys.exit(1 if problems else 0)
