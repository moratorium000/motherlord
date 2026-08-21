#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""모듈 끝의 `## MXX.A 이 모듈의 축약어` 표를 채운다.

부록 A §A.1 이 정한 규약은 이렇다.

    모듈은 각각 독립적으로 읽힐 수 있어야 하므로, 모듈이 바뀌면 다시
    완전 표기한다.

그런데 17단계 검토에서 `scripts/check_abbr.py` 로 훑어 보니, 본문에 쓰이지만
그 모듈 안 어디에서도 풀어 쓰지 않고 모듈 축약어 표에도 없는 항목이 100건
넘게 남아 있었다. 모듈을 건너뛰어 읽는 사람에게는 뜻을 찾을 곳이 없다는
뜻이다.

이 스크립트는 부록 A 마스터 목록을 사전으로 삼아 빠진 행을 각 모듈 표에
알파벳순으로 끼워 넣는다. 부록 A 에 없는 축약어는 넣지 않고 보고만 한다 —
사전에 없는 뜻을 지어내면 안 되기 때문이다.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPX = ROOT / "03_부록" / "A_축약어_마스터목록.md"


def load_glossary() -> dict[str, tuple[str, str]]:
    """부록 A §A.2 → {약어: (영문 원어, 한글)}."""
    text = APPX.read_text(encoding="utf-8")
    m = re.search(r"^## A\.2 [^\n]*$(.*?)(?=^## A\.3)", text, re.M | re.S)
    out: dict[str, tuple[str, str]] = {}
    for row in re.finditer(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|",
                           m.group(1), re.M):
        head, eng, kor = row.group(1), row.group(2), row.group(3)
        if head.startswith("-") or head == "약어":
            continue
        for tok in re.split(r"\s*[/·]\s*", head):
            tok = tok.strip().replace("_", "")
            if re.fullmatch(r"[A-Za-z][A-Za-z0-9\-]{0,12}", tok):
                out.setdefault(tok.upper(), (eng, kor))
                # FR-4 처럼 붙임표가 있는 항목은 앞 조각으로도 찾을 수 있게
                if "-" in tok:
                    out.setdefault(tok.split("-")[0].upper(), (eng, kor))
    return out


def missing_by_module() -> dict[str, list[str]]:
    """검사기를 그대로 돌려 F1·F2 목록을 받는다. 판정 규칙을 한 곳에 둔다."""
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_abbr.py")],
                       capture_output=True, text=True, cwd=ROOT)
    out: dict[str, list[str]] = defaultdict(list)
    for m in re.finditer(r"^   - (M\d\d): ([A-Z0-9][A-Z0-9\-]*) — ",
                         r.stdout, re.M):
        out[m.group(1)].append(m.group(2))
    return out


def main() -> int:
    gloss = load_glossary()
    print(f"부록 A 사전 {len(gloss)}종")

    todo = missing_by_module()
    if not todo:
        print("채울 것 없음")
        return 0

    unknown: list[str] = []
    total = 0

    for code, terms in sorted(todo.items()):
        path = next((ROOT / "01_모듈").glob(f"{code}_*.md"))
        text = path.read_text(encoding="utf-8")
        m = re.search(rf"^## {code}\.A [^\n]*$(.*?)(?=^## |\Z)",
                      text, re.M | re.S)
        if not m:
            print(f"[건너뜀] {code}: 축약어 표 절이 없음")
            continue

        added = 0
        for term in sorted(set(terms)):
            if term not in gloss:
                unknown.append(f"{code}: {term}")
                continue
            eng, kor = gloss[term]
            row = f"| {term} | {eng} | {kor} |"

            m = re.search(rf"^## {code}\.A [^\n]*$(.*?)(?=^## |\Z)",
                          text, re.M | re.S)
            block = m.group(1)
            rows = [(mm.start(), mm.group(0), mm.group(1).strip().upper())
                    for mm in re.finditer(r"^\|\s*\*{0,2}([^|*]+?)\*{0,2}\s*\|"
                                          r"[^\n]*$", block, re.M)
                    if not mm.group(1).startswith("-")
                    and mm.group(1).strip() not in ("약어", "축약어")]
            if not rows:
                print(f"[건너뜀] {code}: 표를 찾지 못함")
                break
            # 기존 표는 알파벳순이 아니라 배우는 순서로 짜여 있다.
            # 그 순서를 흩뜨리지 않도록 새 행은 표 끝에 붙인다.
            last = rows[-1]
            at = m.start(1) + last[0] + len(last[1]) + 1
            text = text[:at] + row + "\n" + text[at:]
            added += 1

        if added:
            path.write_text(text, encoding="utf-8")
            total += added
            print(f"  {code}: {added}행 추가")

    if unknown:
        print("\n부록 A 에 없어 넣지 못한 것:")
        for u in unknown:
            print("   -", u)

    print(f"\n총 {total}행 추가")
    return 0


if __name__ == "__main__":
    sys.exit(main())
