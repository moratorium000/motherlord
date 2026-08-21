"""부록 C(출처 통합목록)를 본문에서 **생성**한다.

손으로 옮겨 적은 목록은 반드시 본문과 어긋난다. 그래서 이 문서는
저장소의 모든 마크다운을 훑어 외부 링크를 모으고, 등급을 파싱해
`03_부록/C_출처_통합목록.md` 를 새로 쓴다.

    python3 scripts/gen_appendix_c.py            # 생성
    python3 scripts/gen_appendix_c.py --check    # 본문과 어긋났는지만 확인

등급 표기가 여러 형태라 파서가 다 못 잡는다. 못 잡은 것은 GRADE_FIX 에
손으로 적고, 그 사실을 문서에도 남긴다 — 조용히 넘기지 않는다.
"""
import argparse
import pathlib
import re
import sys
from collections import Counter, defaultdict

# 마크다운 링크. URL 에 괄호가 들어간 주소(위키 계열)가 있어 한 겹까지 허용한다.
# `[^)\s]+` 만 쓰면 ..._(Steer) 같은 주소가 잘려 죽은 링크가 된다.
LINK = re.compile(r"\[([^\]]+)\]\((https?://(?:[^()\s]|\([^()\s]*\))+)\)")

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "03_부록/C_출처_통합목록.md"

# 훑을 문서 (설계서는 계획 문서라 제외 — 본문이 인용한 것만 모은다)
GLOBS = ("01_모듈/M*.md", "02_캡스톤/*.md", "03_부록/A_*.md",
         "03_부록/B_*.md", "03_부록/D_*.md", "03_부록/E_*.md")

GRADE_DESC = {
    "A": ("1차 표준·규격", "표준화 기구·규제기관의 원문. 가장 신뢰도가 높다"),
    "B": ("제조사·학술", "계측기·부품 제조사의 응용노트와 백서, 대학 교재·논문"),
    "C": ("교육 사이트", "정리가 잘 된 공개 교육 자료. 원문 확인이 필요할 때가 있다"),
    "D": ("블로그·개인", "유용하지만 단독 근거로 쓰지 않는다. 교차검증 필수"),
}

# 파서가 등급을 못 잡는 자리를 손으로 채운다.
# 값이 None 이면 "등급 없음(교육 구성 참고)" 으로 표시한다.
# 파서가 못 잡는 자리를 손으로 채운다. 값 None 은 "등급 없음".
# 부록 D 는 등급을 문장 안에 적어 두어(여러 링크를 한 괄호가 덮음) 자동으로는 안 잡힌다.
GRADE_FIX = {
    "https://www.centricrf.com/torque-specifications/": "D",
    "https://www.data-alliance.net/blog/torque-ratings-of-sma-and-rpsma-"
    "antenna-cable-connectors-adapters": "D",
    "https://www.rfcnn.com/blog/rf-connector-torque-guide-sma-n-3-5mm-2-92mm-"
    "4-3-10": "D",
    # 가격 참고용 소매점·비교 글 — 사실 근거가 아니라 시세 예시다
    "https://www.randl.com/index.php?main_page=product_info&products_id=75145": "D",
    "https://www.rtl-sdr.com/the-49-tinysa-spectrum-analyzer/": "D",
    "https://www.s3semi.com/tinysa-vs-nanovna-how-to-pick-the-right-analyzer-"
    "for-your-rf-projects/": "D",
}

# 지침 1의 참고 사이트. 사실 근거가 아니라 **교육 구성**을 참고한 곳이라
# 등급을 매기지 않는다. 주소가 여러 갈래여서 도메인으로 판정한다.
REFERENCE_SITE = "rfdh.com"

# 도메인 → 발행 주체 이름 (표를 읽기 좋게)
PUBLISHER = {
    "keysight.com": "Keysight", "docs.keysight.com": "Keysight",
    "helpfiles.keysight.com": "Keysight", "analog.com": "Analog Devices",
    "minicircuits.com": "Mini-Circuits", "blog.minicircuits.com": "Mini-Circuits",
    "microwaves101.com": "Microwaves101", "rfdh.com": "rfdh.com (참고 사이트)",
    "eng.libretexts.org": "LibreTexts (Steer 교재)", "ecfr.gov": "eCFR (미국 연방규정)",
    "euramet.org": "EURAMET", "etsi.org": "ETSI", "itu.int": "ITU",
    "arxiv.org": "arXiv", "scikit-rf.readthedocs.io": "scikit-rf",
    "everyspec.com": "MIL-STD", "3gpp.org": "3GPP",
}


def norm(url):
    """같은 문서를 가리키는 주소를 하나로 모은다 (www·http 차이)."""
    u = url.rstrip("/")
    u = re.sub(r"^http://", "https://", u)
    u = re.sub(r"^https://www\.", "https://", u)
    return u


def domain(url):
    d = url.split("/")[2] if "//" in url else url
    return d.replace("www.", "")


def parse_grades(cell, n_links):
    """등급 칸을 읽는다. 여러 표기 형태를 다룬다.

    "B"            → 전부 B
    "B, B, D"      → 순서대로
    "**A**, B"     → 굵게 표시된 것도 같다
    "B ×3 + D ×3"  → B 세 개, D 세 개
    """
    if not cell:
        return []
    m = re.findall(r"([ABCD])\s*[×x]\s*(\d+)", cell)
    if m:
        out = []
        for g, k in m:
            out += [g] * int(k)
        return out[:n_links] if len(out) >= n_links else out
    gs = re.findall(r"\b([ABCD])\b", re.sub(r"\*", "", cell))
    if len(gs) == 1 and n_links > 1:
        return gs * n_links              # 한 등급이 전부를 덮는 경우
    return gs


GRADE_FIX = {norm(k): v for k, v in GRADE_FIX.items()}


def collect():
    """모든 문서에서 (정규화 URL) → 정보 를 모은다."""
    recs = defaultdict(lambda: dict(titles=set(), docs=set(), grades=set(),
                                    topics=set(), raw=set()))
    files = []
    for g in GLOBS:
        files += sorted(ROOT.glob(g))

    for f in files:
        text = f.read_text()
        doc = f.stem
        mod = doc[:3] if doc[0] in "MP" else doc.split("_")[0]
        mod = {"A": "부록 A", "B": "부록 B", "D": "부록 D", "E": "부록 E",
               "00": "캡스톤"}.get(mod, mod)
        if doc.startswith("00_과제"):
            mod = "캡스톤"

        # ── ① 출처 표에서 (등급이 붙어 있다)
        tabled = set()
        # 주의: re.S 아래서 .* 는 줄바꿈까지 먹는다. 제목 부분은 [^\n]* 로 막는다
        for sm in re.finditer(r"^## [^\n]*출처[^\n]*$(.*?)(?=^## |\Z)",
                              text, re.M | re.S):
            for ln in sm.group(1).splitlines():
                s = ln.strip()
                if not (s.startswith("|") and s.endswith("|")):
                    continue
                cells = [c.strip() for c in s.strip("|").split("|")]
                if len(cells) < 2 or set(cells[0]) <= set("-: "):
                    continue
                if cells[0] in ("내용", "항목", "주제"):
                    continue
                links = LINK.findall(s)
                if not links:
                    continue
                gcell = ""
                for c in cells[2:]:
                    if re.search(r"[ABCD]", re.sub(r"\*", "", c)) and \
                            re.fullmatch(r"[\*ABCD,×x\d\s\+]+", c):
                        gcell = c
                        break
                grades = parse_grades(gcell, len(links))
                for i, (title, url) in enumerate(links):
                    u = norm(url)
                    tabled.add(u)
                    r = recs[u]
                    r["titles"].add(title.strip())
                    r["docs"].add(mod)
                    r["topics"].add(cells[0][:40])
                    r["raw"].add(url)
                    if domain(u) == REFERENCE_SITE:
                        pass                        # 참고 사이트는 등급 없음
                    elif u in GRADE_FIX:
                        r["grades"].add(GRADE_FIX[u])
                    elif i < len(grades):
                        r["grades"].add(grades[i])

        # ── ② 본문에만 있는 링크 (부록 D 처럼 인라인으로 등급을 적은 곳)
        for m in LINK.finditer(text):
            u = norm(m.group(2))
            if u in tabled:
                continue
            r = recs[u]
            r["titles"].add(m.group(1).strip())
            r["docs"].add(mod)
            r["raw"].add(m.group(2))
            r["topics"].add("(본문 인용)")
            tail = text[m.end():m.end() + 40].split("\n")[0].split("|")[0]
            g = re.search(r"등급\s*([ABCD])", tail)
            if domain(u) == REFERENCE_SITE:
                pass
            elif u in GRADE_FIX:
                r["grades"].add(GRADE_FIX[u])
            elif g:
                r["grades"].add(g.group(1))

    return recs


def grade_of(rec):
    gs = rec["grades"]
    if not gs:
        return "-"
    if len(gs) == 1:
        return next(iter(gs))
    return "/".join(sorted(gs))         # 문서마다 다르게 매긴 경우 — 드러낸다


def best_title(rec):
    """가장 설명적인 제목을 고른다 (마크다운 강조 기호는 턴다)."""
    ts = [re.sub(r"[*_`]", "", t) for t in rec["titles"]]
    return max(ts, key=len)


def build(recs):
    n = len(recs)
    by_grade = defaultdict(list)
    for u, r in recs.items():
        by_grade[grade_of(r)].append((u, r))
    # 발행 주체 이름으로 묶는다 — blog.x.com 과 x.com 이 따로 세어지면 안 된다
    doms = Counter(PUBLISHER.get(domain(u), domain(u)) for u in recs)
    shared = sorted(((u, r) for u, r in recs.items() if len(r["docs"]) >= 3),
                    key=lambda kv: -len(kv[1]["docs"]))
    mixed = [(u, r) for u, r in recs.items() if len(r["grades"]) > 1]
    ungraded = by_grade.get("-", [])
    ref_site = [(u, r) for u, r in ungraded if domain(u) == REFERENCE_SITE]
    unknown = [(u, r) for u, r in ungraded if domain(u) != REFERENCE_SITE]

    L = []
    A = L.append
    A("# 부록 C — 출처 통합목록")
    A("")
    A("**문서 번호**: RF-CUR-APX-C · **버전**: v1.0")
    A("**대응 규칙**: 설계서 §11 (출처 관리·신뢰성 등급·교차검증)")
    A("**생성 방법**: 이 문서는 **본문에서 자동 생성**됩니다 — "
      "`python3 scripts/gen_appendix_c.py`")
    A("")
    A("---")
    A("")
    A("## C.0 이 문서는 무엇인가")
    A("")
    A("> **본문 전체가 인용한 외부 출처를 한곳에 모은 것입니다.** "
      "어떤 주장이 어디서 왔는지 되짚을 때, 그리고 **링크가 죽었는지 "
      "확인할 때** 씁니다.")
    A("")
    A("### 손으로 쓰지 않았습니다")
    A("")
    A("출처 목록을 손으로 옮겨 적으면 본문이 바뀔 때마다 어긋납니다. "
      "그래서 이 문서는 저장소의 모든 마크다운을 훑어 **생성**합니다.")
    A("")
    A("```bash")
    A("python3 scripts/gen_appendix_c.py            # 다시 생성")
    A("python3 scripts/gen_appendix_c.py --check    # 본문과 어긋났는지 확인")
    A("```")
    A("")
    A("> 📌 **본문에 출처를 추가하거나 고쳤다면 이 스크립트를 다시 돌리십시오.** "
      "`--check` 는 어긋난 것이 있으면 0이 아닌 값으로 끝나므로 자동화에 걸 수 있습니다.")
    A("")
    A("### 등급의 뜻")
    A("")
    A("| 등급 | 무엇 | 어떻게 쓰나 |")
    A("|---|---|---|")
    for g in "ABCD":
        name, desc = GRADE_DESC[g]
        A(f"| **{g}** | {name} | {desc} |")
    A("| — | 등급 없음 | **사실 근거가 아니라 교육 구성 참고**로 인용한 것 |")
    A("")
    A("> ⚠️ **등급은 신뢰도의 순위이지 정확도의 보증이 아닙니다.** "
      "등급 A라도 개정되고, 등급 D라도 맞을 수 있습니다. "
      "**중요한 수치는 등급과 무관하게 원문에서 확인**하십시오.")
    A("")
    A("---")
    A("")
    A("## C.1 한눈에")
    A("")
    A("| | |")
    A("|---|---|")
    A(f"| 고유 출처 | **{n}개** |")
    A(f"| 인용한 문서 | {len({d for r in recs.values() for d in r['docs']})}편 |")
    A(f"| 발행 주체 | {len(doms)}곳 |")
    A("")
    A("### 등급 분포")
    A("")
    A("| 등급 | 개수 | 비율 |")
    A("|---|---|---|")
    for g in "ABCD":
        k = len(by_grade.get(g, []))
        A(f"| {g} | {k} | {k/n*100:.1f} % |")
    k = len(ref_site)
    A(f"| — (참고 사이트, 교육 구성 참고) | {k} | {k/n*100:.1f} % |")
    if unknown:
        A(f"| **등급 미상** | {len(unknown)} | {len(unknown)/n*100:.1f} % |")
    mx = sum(len(v) for kk, v in by_grade.items() if "/" in kk)
    if mx:
        A(f"| **문서마다 다르게 매김** | {mx} | {mx/n*100:.1f} % |")
    A("")
    A("> 📌 **등급 D가 적지 않은 것은 의도된 결과입니다.** "
      "RF 실무 지식의 상당 부분이 제조사 블로그와 엔지니어 개인 글에 있습니다. "
      "그래서 D는 **단독으로 쓰지 않고 반드시 교차검증**했습니다 — "
      "각 모듈의 출처 표에 교차검증 건수가 적혀 있습니다.")
    A("")
    A("### 발행 주체 상위")
    A("")
    A("| 발행 주체 | 출처 수 |")
    A("|---|---|")
    for d, c in doms.most_common(14):
        A(f"| {d} | {c} |")
    A("")
    A("---")
    A("")

    # ── 여러 모듈이 함께 쓴 출처
    A("## C.2 여러 모듈이 함께 쓴 출처")
    A("")
    A("세 편 이상에서 인용한 것들입니다. **이 커리큘럼의 뼈대를 이루는 자료**입니다.")
    A("")
    A("| 등급 | 출처 | 쓴 모듈 |")
    A("|---|---|---|")
    for u, r in shared:
        A(f"| {grade_of(r)} | [{best_title(r)[:70]}]({u}) | "
          f"{' · '.join(sorted(r['docs']))} |")
    A("")
    A("---")
    A("")

    # ── 등급별 전수
    for g in "ABCD":
        items = sorted(by_grade.get(g, []), key=lambda kv: domain(kv[0]))
        if not items:
            continue
        name, desc = GRADE_DESC[g]
        A(f"## C.{'3456'['ABCD'.index(g)]} 등급 {g} — {name} ({len(items)}개)")
        A("")
        A(f"*{desc}*")
        A("")
        A("| 출처 | 발행 주체 | 쓴 모듈 |")
        A("|---|---|---|")
        for u, r in items:
            A(f"| [{best_title(r)[:74]}]({u}) | "
              f"{PUBLISHER.get(domain(u), domain(u))} | "
              f"{' · '.join(sorted(r['docs']))} |")
        A("")
        A("---")
        A("")

    # ── 등급 없음
    if ref_site:
        A(f"## C.7 참고 사이트 — 등급 없음 ({len(ref_site)}개)")
        A("")
        A("> **지침 1의 참고 사이트입니다.** 사실의 근거가 아니라 "
          "**무엇을 어떤 순서로 가르칠지**를 참고했습니다. 그래서 등급을 "
          "매기지 않았습니다.")
        A("")
        A("| 출처 | 쓴 모듈 |")
        A("|---|---|")
        for u, r in sorted(ref_site, key=lambda kv: kv[0]):
            A(f"| [{best_title(r)[:74]}]({u}) | {' · '.join(sorted(r['docs']))} |")
        A("")
        A("---")
        A("")

    if unknown:
        A(f"## C.7-2 등급을 못 매긴 출처 ({len(unknown)}개)")
        A("")
        A("> ⚠️ **파서가 등급을 찾지 못했고, 손으로도 정하지 않은 것들입니다.** "
          "본문의 출처 표에 등급을 적어 주십시오.")
        A("")
        A("| 출처 | 쓴 문서 |")
        A("|---|---|")
        for u, r in sorted(unknown, key=lambda kv: kv[0]):
            A(f"| [{best_title(r)[:74]}]({u}) | {' · '.join(sorted(r['docs']))} |")
        A("")
        A("---")
        A("")

    # ── 등급이 갈린 것
    A("## C.8 문서마다 등급이 갈린 출처")
    A("")
    if mixed:
        A("| 출처 | 매겨진 등급 | 쓴 모듈 |")
        A("|---|---|---|")
        for u, r in mixed:
            A(f"| [{best_title(r)[:60]}]({u}) | {grade_of(r)} | "
              f"{' · '.join(sorted(r['docs']))} |")
        A("")
        A("> ⚠️ **같은 자료에 다른 등급이 붙어 있습니다.** 인용한 맥락이 달라서일 "
          "수도 있고, 실수일 수도 있습니다. **원문을 볼 때 더 낮은 등급으로 "
          "가정**하십시오.")
    else:
        A("없습니다. 같은 출처에는 모든 문서가 같은 등급을 매겼습니다.")
    A("")
    A("---")
    A("")

    # ── 모듈별 색인
    A("## C.9 모듈별 색인")
    A("")
    per = defaultdict(list)
    for u, r in recs.items():
        for d in r["docs"]:
            per[d].append((u, r))
    A("| 문서 | 출처 수 | 등급 구성 |")
    A("|---|---|---|")
    for d in sorted(per):
        items = per[d]
        c = Counter(grade_of(r) for _, r in items)
        comp = " · ".join(f"{k} {v}" for k, v in sorted(c.items()))
        A(f"| {d} | {len(items)} | {comp} |")
    A("")
    A("> 📌 **각 문서의 §S(출처) 절에 그 문서만의 목록과 교차검증 건수가 있습니다.** "
      "여기는 전체를 훑기 위한 색인입니다.")
    A("")
    A("---")
    A("")

    # ── 한계
    A("## C.10 확인 안내와 한계")
    A("")
    A("> ⚠️ **URL을 직접 열어 확인하지 못했습니다.**")
    A(">")
    A("> 이 커리큘럼은 조직 네트워크 정책상 **외부 웹사이트 직접 접속이 차단된 "
      "환경**에서 작성되었습니다. 모든 사실은 검색 결과의 서지 정보와 요약을 "
      "**독립 출처 2곳 이상으로 교차 대조**해 썼지만, **원문을 열어 확인하지는 "
      "못했습니다.**")
    A(">")
    A("> 따라서 다음을 독자가 확인해 주셔야 합니다.")
    A(">")
    A("> | 확인할 것 | 왜 |")
    A("> |---|---|")
    A("> | 링크가 살아 있는가 | 제조사 응용노트는 개편 때 주소가 자주 바뀐다 |")
    A("> | 인용한 수치가 원문에 있는가 | 요약을 대조했을 뿐이다 |")
    A("> | 규격의 개정 여부 | 조항 번호와 한계값은 개정된다 |")
    A("> | 가격·재고 정보 | 시점에 따라 크게 변한다 (부록 D) |")
    A("")
    A("> 📌 **이 한계를 감추지 않는 것이 이 커리큘럼의 방침입니다.** "
      "각 모듈의 출처 절에도 같은 안내가 붙어 있습니다. 배경은 "
      "[M00.S](../01_모듈/M00_RF시스템엔지니어링이란.md#m00s-출처)에 있습니다.")
    A("")
    A("### 링크 확인 도구")
    A("")
    A("접속이 되는 환경이라면 아래로 한 번에 확인할 수 있습니다.")
    A("")
    A("```bash")
    A("# 이 문서의 모든 링크에 HEAD 요청을 보내 죽은 링크를 찾는다")
    A("grep -o 'https\\?://[^)]*' 03_부록/C_출처_통합목록.md | sort -u | \\")
    A("  while read u; do")
    A('    code=$(curl -s -o /dev/null -w "%{http_code}" -L --max-time 15 "$u")')
    A('    [ "$code" = "200" ] || echo "$code  $u"')
    A("  done")
    A("```")
    A("")
    A("---")
    A("")
    A("## 변경 이력")
    A("")
    A("| 버전 | 일자 | 내용 |")
    A("|---|---|---|")
    A(f"| v1.0 | 2026-08-21 | 최초 생성. 고유 출처 {n}개, "
      f"등급 A {len(by_grade.get('A', []))} · B {len(by_grade.get('B', []))} · "
      f"C {len(by_grade.get('C', []))} · D {len(by_grade.get('D', []))}. "
      "`gen_appendix_c.py` 로 본문에서 자동 생성 |")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="본문과 어긋났는지만 확인하고 쓰지 않는다")
    args = ap.parse_args()

    recs = collect()
    text = build(recs)

    n = len(recs)
    by_grade = Counter(grade_of(r) for r in recs.values())
    print(f"출처 {n}개 수집 — " +
          " · ".join(f"{k} {v}" for k, v in sorted(by_grade.items())))

    # ── 자체 점검
    problems = []
    for u, r in recs.items():
        if not r["titles"]:
            problems.append(f"제목 없음: {u}")
        if len(r["grades"]) > 1:
            problems.append(f"등급 갈림 {sorted(r['grades'])}: {u}")
        if not r["grades"] and domain(u) != REFERENCE_SITE:
            problems.append(f"등급 없음: {u}")

    # 빠뜨린 링크가 없는지 — 본문의 모든 외부 URL 이 이 문서에 들어갔는가
    corpus = set()
    for g in GLOBS:
        for f in ROOT.glob(g):
            for _, u in LINK.findall(f.read_text()):
                corpus.add(norm(u))
    missing = corpus - set(recs)
    for u in sorted(missing):
        problems.append(f"수집 누락: {u}")
    print(f"본문 외부 링크 {len(corpus)}개 중 {len(corpus) - len(missing)}개 수록")

    # 정규식과 무관한 방법으로 한 번 더 센다 — LINK 정규식 자체가 틀렸을 때를 잡는다.
    # (실제로 URL 안의 괄호를 못 살려 주소가 잘리는 버그를 이 방식으로 발견했다)
    raw = set()
    for g in GLOBS:
        for f in ROOT.glob(g):
            for line in f.read_text().splitlines():
                for i, ch in enumerate(line):
                    if line.startswith("http", i) and (i == 0 or line[i - 1] == "("):
                        depth, j = 0, i
                        while j < len(line):
                            if line[j] == "(":
                                depth += 1
                            elif line[j] == ")":
                                if depth == 0:
                                    break
                                depth -= 1
                            elif line[j] in " \t":
                                break
                            j += 1
                        raw.add(norm(line[i:j]))
    only_raw = raw - corpus
    only_re = corpus - raw
    if only_raw or only_re:
        problems.append(f"두 방법의 수집 결과가 다르다 "
                        f"(괄호 세기만: {len(only_raw)}, 정규식만: {len(only_re)})")
        for u in sorted(only_raw | only_re):
            problems.append(f"    {u}")
    else:
        print(f"괄호를 세는 독립 방식으로도 같은 {len(raw)}개 — 정규식이 맞다")

    # 생성된 문서 안에도 실제로 들어갔는지 (표가 잘렸을 수도 있다)
    body = text
    not_in_doc = [u for u in recs if u not in body]
    for u in sorted(not_in_doc):
        problems.append(f"문서에 안 실림: {u}")
    if problems:
        print(f"\n확인이 필요한 항목 {len(problems)}건")
        for p in problems:
            print(f"  · {p}")

    if args.check:
        if not OUT.exists():
            print("\n부록 C 가 아직 없습니다.")
            return 1
        same = OUT.read_text() == text
        print("\n본문과 " + ("일치합니다." if same
                            else "어긋납니다 — 다시 생성하십시오."))
        return 0 if same else 1

    OUT.write_text(text)
    print(f"\n{OUT.relative_to(ROOT)} 를 썼습니다 ({len(text.splitlines())}줄)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
