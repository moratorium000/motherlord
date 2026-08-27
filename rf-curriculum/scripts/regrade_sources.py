#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""심화 모듈의 출처 등급을 **출처마다** 다시 매긴다.

10단계 정합성 검토에서 나온 문제다. 기본 모듈(M00–M17)은 출처 표의 등급
칸에 `B, D, B` 처럼 **링크 순서대로** 적어 두었는데, 심화 모듈(B01–B12)은
행 하나에 글자 하나만 적었다. 그래서 한 행이 표준 원문과 제조사 응용노트를
함께 인용하면 부록 C 가 **둘 다 같은 등급**으로 싣게 된다.

실제로 그 일이 벌어져 같은 문서가 어떤 곳에서는 A, 어떤 곳에서는 B 로
실렸다(부록 C 의 "A/B" 항목 14건). 등급은 그 문서가 **무엇을 뒷받침하느냐**가
아니라 **어떤 종류의 문서냐**로 정해지므로, 한 문서에 두 등급이 붙으면
어느 쪽이든 틀린 것이다.

이 스크립트는 부록 C 의 등급 정의(§등급의 뜻)를 도메인 표로 옮겨,
심화 모듈의 등급 칸을 링크 개수만큼의 목록으로 바꾼다.

    python3 scripts/regrade_sources.py --check   # 바꿀 것만 보여 준다
    python3 scripts/regrade_sources.py           # 실제로 고친다

여러 번 돌려도 안전하다(이미 맞으면 안 건드린다).
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
TARGETS = sorted((ROOT / "05_심화").glob("B*.md"))

LINK = re.compile(r"\[([^\]]+)\]\((https?://(?:[^()\s]|\([^()\s]*\))+)\)")

# ── 등급 정의 (부록 C 와 같은 뜻) ────────────────────────────────────────
#   A 1차 표준·규격 — 표준화 기구·규제기관·국가측정표준기관의 원문
#   B 제조사·학술   — 계측기·부품 제조사의 응용노트와 백서, 학술지·대학 자료,
#                     업계 전문지
#   C 교육 사이트   — 정리가 잘 된 공개 교육 자료
#   D 블로그·개인   — 단독 근거로 쓰지 않는다
#
# 등급은 **문서의 종류**로 정한다. 그 문서가 어떤 주장을 뒷받침하는지와는
# 무관하다 — 그래야 같은 문서가 두 등급으로 실리는 일이 없다.
DOMAIN_GRADE: dict[str, str] = {}


def _put(grade: str, *domains: str) -> None:
    for d in domains:
        DOMAIN_GRADE[d] = grade


_put("A",
     # 규격 제정·인증 기관
     "ctiacertification.org", "api.ctia.org", "ieeexplore.ieee.org",
     "standards.iteh.ai", "ncsli.org",
     # 국가측정표준기관·국립연구소
     "nist.gov", "tf.nist.gov", "tf.boulder.nist.gov", "osti.gov",
     # IEEE 370 원문 사본 (호스트는 제3자이지만 내용은 표준 원문)
     "elecenghub.com")

_put("B",
     # 계측기·부품 제조사
     "keysight.com", "docs.keysight.com", "helpfiles.keysight.com",
     "assets.testequity.com", "rohde-schwarz.com", "scdn.rohde-schwarz.com",
     "cdn.rohde-schwarz.com.cn", "teledynelecroy.com",
     "cdn.teledynelecroy.com", "siglentna.com", "download.ni.com",
     "minicircuits.com", "analog.com", "markimicrowave.com", "maurymw.com",
     "focus-microwaves.com", "shop.richardsonrfpd.com", "rfmw.com",
     "www3.advantest.com", "mathworks.com", "resources.pcb.cadence.com",
     "scikit-rf.readthedocs.io", "elitetest.com", "toyotechus.com",
     "allpcb.com", "lbagroup.com", "wrc-nc.org",
     # 학술 — 논문·대학 자료
     "arxiv.org", "doi.org", "sciencedirect.com", "researchgate.net",
     "ojs.wiserpub.com", "radioeng.cz", "av.it.pt", "homepages.uc.edu",
     "web.ece.ucsb.edu", "csmantech.org", "learnemc.com",
     "cran.r-project.org", "blogs.sas.com",
     # 특허 원문 — 1차 문서이지만 표준·규격은 아니다
     "image-ppubs.uspto.gov", "patents.google.com",
     # 업계 전문지
     "microwavejournal.com", "mwrf.com", "signalintegrityjournal.com",
     "edn.com", "electronicdesign.com", "incompliancemag.com",
     "interferencetechnology.com", "highfrequencyelectronics.com",
     "qualitymag.com", "analyse-it.com", "simco.com")

_put("C",
     "allaboutcircuits.com", "rahsoft.com", "rfwireless-world.com",
     "rfessentials.com", "en.wikipedia.org", "community.element14.com",
     "calibrationos.com", "sigmadesk.app", "app.qualityengineer.ai",
     "redeweb.com", "hwe.design",
     # 측정 컨설팅 회사의 해설 글. M16 이 이미 C 로 매겨 두었다 —
     # 같은 문서에 두 등급이 붙지 않도록 그쪽에 맞춘다.
     "isobudgets.com")

# 참고 사이트(지침 1)는 등급을 매기지 않는다.
REFERENCE_SITE = "rfdh.com"


def host(url: str) -> str:
    return urlparse(url).netloc.replace("www.", "")


def grade_of(url: str) -> str | None:
    h = host(url)
    if h.endswith(REFERENCE_SITE):
        return None
    return DOMAIN_GRADE.get(h)


def is_grade_cell(cell: str) -> bool:
    """등급 칸인가. 링크가 없고 A~D 와 쉼표만으로 이뤄져야 한다."""
    if LINK.search(cell):
        return False
    c = cell.strip()
    return bool(c) and bool(re.search(r"[ABCD]", re.sub(r"\*", "", c))) \
        and bool(re.fullmatch(r"[\*ABCD,\s]+", c))


def main() -> int:
    check_only = "--check" in sys.argv
    unknown: Counter[str] = Counter()
    changes: list[tuple[str, int, str, str]] = []
    files_changed = 0

    for path in TARGETS:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        # 출처 절만 손댄다. 본문 표에도 A~D 가 나올 수 있다.
        spans = [(m.start(), m.end()) for m in
                 re.finditer(r"^## [^\n]*출처[^\n]*$.*?(?=^## |\Z)",
                             text, re.M | re.S)]
        if not spans:
            print(f"[건너뜀] {path.name}: 출처 절이 없다")
            continue

        out, pos, changed = [], 0, False
        for i, ln in enumerate(lines, 1):
            start = pos
            pos += len(ln)
            in_src = any(a <= start < b for a, b in spans)
            s = ln.strip()
            if not (in_src and s.startswith("|") and s.endswith("|")):
                out.append(ln)
                continue
            links = LINK.findall(s)
            if not links:
                out.append(ln)
                continue

            cells = s.strip("|").split("|")
            gi = next((k for k in range(1, len(cells))
                       if is_grade_cell(cells[k])), None)
            if gi is None:
                out.append(ln)
                continue

            want = []
            for _, url in links:
                g = grade_of(url)
                if g is None and not host(url).endswith(REFERENCE_SITE):
                    unknown[host(url)] += 1
                    g = "?"
                want.append(g or "—")
            new_cell = ", ".join(want)
            if cells[gi].strip() == new_cell:
                out.append(ln)
                continue

            changes.append((path.name, i, cells[gi].strip(), new_cell))
            cells[gi] = f" {new_cell} "
            out.append("|" + "|".join(cells) + "|\n")
            changed = True

        if changed and not check_only:
            path.write_text("".join(out), encoding="utf-8")
            files_changed += 1

    for name, ln, old, new in changes:
        print(f"  {name}:{ln}  {old!r} -> {new!r}")
    print(f"\n등급 칸 {len(changes)}곳" +
          (" (바꿀 것만 표시)" if check_only else f" 수정 · 파일 {files_changed}개"))

    if unknown:
        print("\n[분류표에 없는 도메인]")
        for d, n in unknown.most_common():
            print(f"  {n:3d}  {d}")
        print("  -> DOMAIN_GRADE 에 추가한 뒤 다시 돌리십시오")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
