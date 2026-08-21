#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""그림 번호를 읽는 순서대로 다시 매긴다.

M00~M10 은 집필 중에 그림이 빠지거나 자리를 옮기면서 번호가 문서 순서와
어긋났다. 예를 들어 M02 는 캡션이 1,3,4,6,2,7 순으로 나오고 5번은 아예
없다. 교재에서 그림 6이 그림 2보다 먼저 나오면 읽는 사람이 앞뒤를 헷갈린다.

이 스크립트는
  1. 모듈 본문에서 캡션을 등장 순서대로 모아 옛 번호 → 새 번호 표를 만들고
  2. 본문·다른 문서·그림 생성 스크립트의 `그림 MXX-N` 을 한꺼번에 바꾼다.

동시 치환이라 1↔2 같은 맞바꿈에서도 값이 겹치지 않는다. 치환은 자리표시자를
거쳐 두 번에 나눠 한다.

실행 뒤에는 반드시 해당 그림 생성 스크립트를 다시 돌려야 한다. 번호가
그림 안 제목에도 들어가 있기 때문이다.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 번호를 바꿀 대상 문서. _build 는 빌드 산출물이라 제외한다.
TARGETS: list[Path] = []
for sub in ("01_모듈", "02_캡스톤", "03_부록"):
    TARGETS += sorted((ROOT / sub).glob("*.md"))
TARGETS += sorted(ROOT.glob("00_*.md"))
TARGETS.append(ROOT / "README.md")
TARGETS += sorted((ROOT / "scripts").glob("gen_*.py"))


def caption_order(code: str, text: str) -> list[int]:
    return [int(m.group(1))
            for m in re.finditer(rf"^\*그림 {code}-(\d+)\.", text, re.M)]


def main() -> int:
    plans: dict[str, dict[int, int]] = {}

    for p in sorted((ROOT / "01_모듈").glob("M*.md")):
        code = re.match(r"(M\d\d)", p.name).group(1)
        old = caption_order(code, p.read_text(encoding="utf-8"))
        if not old:
            continue
        if old == list(range(1, len(old) + 1)):
            continue
        mapping = {o: i + 1 for i, o in enumerate(old)}
        if len(set(old)) != len(old):
            print(f"[중단] {code}: 캡션 번호가 중복된다 → {old}")
            return 1
        plans[code] = mapping
        moved = {o: n for o, n in mapping.items() if o != n}
        print(f"{code}: {old} → 1..{len(old)}  (바뀌는 번호 {len(moved)}개)")

    if not plans:
        print("바꿀 것 없음")
        return 0

    changed = 0
    for path in TARGETS:
        text = original = path.read_text(encoding="utf-8")
        for code, mapping in plans.items():
            # 1단계: 옛 번호 → 자리표시자 (\x00 은 문서에 나올 리 없다)
            def to_ph(m: re.Match) -> str:
                n = int(m.group(1))
                return f"그림 \x00{code}-{mapping.get(n, n)}\x00"
            text = re.sub(rf"그림 {code}-(\d+)(?![\d])", to_ph, text)
        # 2단계: 자리표시자 → 실제 번호
        text = text.replace("\x00", "")
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed += 1
            print("   고침:", path.relative_to(ROOT))

    print(f"\n{changed}개 파일 수정. 그림 생성 스크립트를 다시 돌릴 것.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
