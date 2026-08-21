"""RF 시스템 엔지니어링 커리큘럼 -> 한 권의 docx.

원본은 GitHub 에서 읽히도록 쓰였다. 워드로 옮기면서 손봐야 하는 것들은
prep.py 가, 수식과 표처럼 렌더러가 까다로운 것들은 이 파일이 맡는다.
"""
import pathlib
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import prep  # noqa: E402

ROOT, BUILD, HERE = prep.ROOT, prep.BUILD, prep.HERE
OUT_NAME = "RF_시스템_엔지니어링_교재.docx"


def find_pandoc():
    """pandoc 을 찾는다. 없으면 pypandoc 이 들고 온 바이너리를 쓴다."""
    found = subprocess.run(["which", "pandoc"], capture_output=True, text=True)
    if found.returncode == 0:
        return found.stdout.strip()
    try:
        import pypandoc
        return pypandoc.get_pandoc_path()
    except Exception:
        sys.exit("pandoc 이 없습니다.  pip install pypandoc_binary  후 다시 실행하십시오.")

TITLE = "RF 시스템 엔지니어링"
SUBTITLE = "전기전자 초심자에서 실무자까지 — 커리큘럼과 교육자료"
DATE = "2026년 8월 21일 · v1.2 (본문 M00–M17 전편 · 부록 A/D/E)"

PARTS = [
    ("Part 0 — 출발점", ["M00_RF시스템엔지니어링이란"]),
    ("Part I — RF의 공용어", ["M01_데시벨과전력", "M02_전송선로",
                          "M03_S파라미터와스미스차트"]),
    ("Part II — 손에 잡히는 RF", ["M04_RF실험실입문", "M05_첫측정"]),
    ("Part III — 부품과 블록", ["M06_수동소자와공진", "M07_필터와수동네트워크",
                          "M08_증폭기", "M09_주파수변환과신호원"]),
    ("Part IV — 시스템", ["M10_안테나와전파", "M11_트랜시버아키텍처",
                      "M12_시스템예산설계", "M13_변조와신호품질"]),
    ("Part V — 측정과 검증", ["M14_정밀측정1_교정과불확도",
                         "M15_정밀측정2_잡음선형성위상잡음",
                         "M16_DUT검증과튜닝과자동화",
                         "M17_보드설계와인증"]),
]
APPENDIX = ["A_축약어_마스터목록", "D_장비_소프트웨어_준비가이드", "E_수학_회로_보충"]

PAGEBREAK = prep.PAGEBREAK


EMU = 360000            # 1 cm
LAND_W, LAND_H = 24.7, 13.0


def enlarge_landscape(doc):
    """가로 구역에 들어간 그림을 가로 쪽 크기로 되돌린다.

    pandoc 은 참조 문서의 세로 쪽 폭(16 cm)을 넘는 그림을 무조건 줄여 버려서,
    가로 쪽에 앉혀도 16 cm 로 깎여 나온다. 구역 표시 사이에 있는 그림만
    찾아 원래 의도한 크기로 늘린다. 세로/가로 비율은 pandoc 이 지켜 놓았다.
    """
    # 구역 표시 문단에는 spacing/rPr 이 먼저 올 수 있으므로 sectPr 만 보고 찾는다
    marks = list(re.finditer(
        r"<w:p><w:pPr>(?:(?!<w:p>).)*?<w:sectPr>.*?</w:sectPr></w:pPr></w:p>",
        doc, re.S))
    assert marks, "구역 표시 문단을 하나도 못 찾았다"
    spans, n = [], 0
    for a, b in zip(marks, marks[1:]):
        if 'w:orient="landscape"' in b.group(0) and \
                'w:orient="landscape"' not in a.group(0):
            spans.append((a.end(), b.start()))

    def scale(seg):
        nonlocal n

        def one(m):
            nonlocal n
            cx, cy = int(m.group(2)), int(m.group(3))
            w_cm = min(LAND_W, LAND_H * cx / cy)
            n += 1
            return (f"{m.group(1)}cx=\"{round(w_cm * EMU)}\" "
                    f"cy=\"{round(w_cm * cy / cx * EMU)}\"")
        return re.sub(r'(<wp:extent |<a:ext )cx="(\d+)" cy="(\d+)"', one, seg)

    parts, last = [], 0
    for s, e in spans:
        parts.append(doc[last:s])
        parts.append(scale(doc[s:e]))
        last = e
    parts.append(doc[last:])
    # 확대가 조용히 빠지는 일이 없도록 확인한다 (wp:extent 와 a:ext 두 곳씩)
    assert n == 2 * len(spans), f"가로 구역 {len(spans)}개인데 그림은 {n // 2}개"
    print(f"  가로 쪽 그림 {len(spans)}개 확대")
    return "".join(parts)


def repack(src_dir, out_path):
    """디렉터리를 docx 로 다시 묶는다.

    zip(1) 은 이름의 대괄호를 와일드카드로 해석해 [Content_Types].xml 을
    말없이 빠뜨릴 수 있다. 그 파일이 빠지면 워드가 파일을 아예 못 연다.
    """
    import zipfile
    out_path = pathlib.Path(out_path)
    out_path.unlink(missing_ok=True)
    src_dir = pathlib.Path(src_dir)
    names = sorted(p for p in src_dir.rglob("*") if p.is_file())
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in names:
            z.write(p, p.relative_to(src_dir).as_posix())
    with zipfile.ZipFile(out_path) as z:
        assert "[Content_Types].xml" in z.namelist(), "Content_Types 누락"
        assert "word/document.xml" in z.namelist(), "document.xml 누락"
    return len(names)



# ────────────────────────────────────────────────── 수식
def fix_math(md):
    """LibreOffice·워드가 OMML 로 못 그리는 표기를 같은 뜻의 다른 표기로 바꾼다.

    렌더 시험으로 확인한 것들 (mt.md · mt2.md · mt3.md):
      · | … |            -> 물음표로 깨진다. \\left| … \\right| 는 정상
      · \\lvert \\rvert \\vert -> 전부 깨진다
      · \\mathrm{dBm}      -> 'd B m' 으로 벌어진다. \\text{dBm} 은 정상
      · \\underbrace{}_{}  -> 밑의 설명이 통째로 사라진다
      · \\boxed{}          -> 상자가 사라진다 (내용은 남는다)
    """
    def one(m):
        body, whole = m.group(2), m.group(0)
        # 상자는 어차피 안 그려지므로 벗기고, 안쪽 여백 기호도 턴다
        body = re.sub(r"\\boxed\{\s*(.*?)\s*\}\s*$", r"\1", body.strip(), flags=re.S)
        # \boxed 안쪽의 여백 기호(\; \, \!)와 홀로 남은 역슬래시를 턴다.
        # 하나만 지우면 "…\" 가 남아 pandoc 이 수식을 통째로 포기한다.
        for _ in range(4):
            body = re.sub(r"^\s*\\[;,! ]|\\[;,! ]\s*$|\\\s*$", "", body).strip()
        # 절댓값 막대
        body = body.replace(r"\lvert", r"\left|").replace(r"\rvert", r"\right|")
        body = re.sub(r"(?<!\\left)(?<!\\right)\|(.*?)(?<!\\left)(?<!\\right)\|",
                      r"\\left|\1\\right|", body)
        # 단위는 로만체로 붙여서. 다만 \mathrm{\mu V} 처럼 안에 명령이 든 것을
        # \text 로 바꾸면 pandoc 이 수식을 통째로 포기하므로 명령은 밖으로 뺀다.
        body = re.sub(r"\\mathrm\{\\([a-zA-Z]+)\s*([^}\\]*)\}",
                      lambda g: "\\" + g.group(1) + (r"\text{" + g.group(2).strip() + "}"
                                                  if g.group(2).strip() else ""),
                      body)
        body = re.sub(r"\\mathrm\{([^}\\]*)\}", r"\\text{\1}", body)
        # 가로 여백 명령은 렌더러가 삼킨다 -> 전각 공백으로 바꾼다
        body = re.sub(r"\\q?quad\s*\\text\{(.*?)\}\s*\\q?quad",
                      r"\\text{　\1　}", body)
        return whole[:m.start(2) - m.start(0)] + body + whole[m.end(2) - m.start(0):]

    md = re.sub(r"(\$\$)(.+?)(\$\$)", one, md, flags=re.S)
    md = re.sub(r"(?<!\$)(\$)([^$\n]+)(\$)(?!\$)", one, md)

    # underbrace 는 밑말이 사라지므로, 식에서 떼어 바로 아래 줄로 옮긴다
    def unbrace(m):
        body = m.group(1)
        labels = re.findall(r"\\underbrace\{.*?\}_\{\\text\{(.*?)\}\}", body)
        body = re.sub(r"\\underbrace\{(.*?)\}_\{\\text\{.*?\}\}", r"\1", body)
        out = f"$${body}$$"
        if labels:
            out += "\n\n*(각 항은 차례로 " + " · ".join(labels) + "입니다.)*"
        return out

    return re.sub(r"\$\$(.*?\\underbrace.*?)\$\$", unbrace, md, flags=re.S)


# ────────────────────────────────────────────────── 조립
def front_matter():
    return f"""# 일러두기

이 책은 **전기전자공학을 처음 시작하는 사람**이 RF(Radio Frequency, 무선주파수)
시스템 엔지니어링을 실무 수준까지 익히도록 짠 커리큘럼과 그 교육자료입니다.
저장소의 마크다운 원본을 한 권으로 묶은 것으로, **M00부터 M17까지
본문 열여덟 개 모듈 전편과 부록 세 편**을 담았습니다.

**읽는 법**

| 표시 | 뜻 |
|---|---|
| 📌 | 꼭 가져가야 할 핵심 |
| ⚠️ | 틀리기 쉬운 곳, 함정 |
| 💡 | 알아 두면 좋은 것 |
| 📖 | 용어·문서 안내 |
| **Lab** | 직접 해 보는 실습. Tier 0은 소프트웨어만, Tier 1은 저가 장비, Tier 2는 실무 장비로 합니다 |

**이 책의 약속**

1. **축약어는 처음 나올 때 반드시 원어와 우리말을 함께** 적습니다. 모르는 약어가
   나오면 부록 A의 마스터 목록에서 찾을 수 있습니다.
2. **개념마다 주인이 되는 모듈이 하나씩** 있습니다. 다른 모듈에서는 참조만 하고
   다시 정의하지 않습니다. 같은 말을 두 번 하지 않기 위한 장치입니다.
3. **모든 수치는 계산으로 확인**했습니다. 그림에 쓰인 값은 `scripts/` 아래의
   생성 스크립트를 실행하면 그대로 재현되며, 각 스크립트는 자체 검산 결과를
   함께 출력합니다.
4. **각 모듈은 세 번의 검토**를 거쳤습니다. 1차는 사실, 2차는 교육적 전달,
   3차는 구조 정합성입니다. 검토에서 무엇을 고쳤는지는 각 모듈 끝의
   **변경 이력**에 그대로 적어 두었습니다.

> ⚠️ **출처에 대하여.** 이 교재는 외부 웹 접속이 막힌 환경에서 집필되었습니다.
> 모든 사실은 독립된 출처 두 곳 이상으로 교차검증했으나 **원문을 직접 열어
> 보지는 못했습니다.** 각 모듈 끝의 출처 표에 원문 주소와 신뢰 등급을 함께
> 적어 두었으니, 중요한 수치는 반드시 원문에서 확인하시기 바랍니다.

> ⚠️ **규격 값에 대하여.** 본문에 인용한 규격 한도값은 **설명을 위한 것**입니다.
> 규격은 개정되고 지역·제품 분류에 따라 달라지므로, 실제 판정은 최신 원문과
> 인증 시험소의 확인을 받아야 합니다.

**아직 없는 것**

**본문은 M17 로 완결되었습니다.** 남은 것은 캡스톤 과제(2.4 GHz 송수신 겸용
트랜시버 모듈)와 부록 B(공식 치트시트)·C(출처 통합목록)입니다.
전체 설계는 이 책 끝의 **별첨 — 커리큘럼 설계서**에서 볼 수 있습니다.
"""


def assemble():
    chunks = [front_matter()]
    for part_title, mods in PARTS:
        chunks.append(f"# {part_title}")
        for i, stem in enumerate(mods):
            if i:
                chunks.append(PAGEBREAK)
            chunks.append(fix_math(prep.convert(ROOT / "01_모듈" / f"{stem}.md")))
    chunks.append("# 부록")
    for i, stem in enumerate(APPENDIX):
        if i:
            chunks.append(PAGEBREAK)
        chunks.append(fix_math(prep.convert(ROOT / "03_부록" / f"{stem}.md")))
    chunks.append("# 별첨 — 커리큘럼 설계서")
    chunks.append(
        "*이 책이 어떤 계획 아래 쓰였는지를 담은 설계 문서입니다. 모듈의 순서,\n"
        "개념의 소유권, 검토 규칙, 남은 집필 계획이 여기에 있습니다.*\n")
    chunks.append(fix_math(prep.convert(ROOT / "00_커리큘럼_설계서_v1.2.md",
                                        drop_title=True)))
    return "\n\n".join(chunks)


# ────────────────────────────────────────────────── 표 다듬기
def polish_tables(docx):
    """표가 쪽 경계에서 잘리지 않게 하고, 머리행을 각 쪽에 반복시킨다.

    pandoc 은 trPr 을 넣지 않아 규격 표가 두 쪽에 걸쳐 토막 난다.
    """
    work = BUILD / "_polish"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir()
    subprocess.run(["unzip", "-q", str(docx), "-d", str(work)], check=True)
    p = work / "word/document.xml"
    t = p.read_text()

    # pandoc 은 <m:nor/> 와 <m:sty/> 를 함께 내보내는데 OMML 스키마는 둘 중
    # 하나만 허용한다. 둘 다 "곧게 세워라" 라는 같은 뜻이라 뒤엣것을 뺀다.
    t = re.sub(r"(<m:nor\s*/>)\s*<m:sty[^/]*/>", r"\1", t)
    # 행렬 열 속성도 순서가 뒤집혀 나온다. count 가 mcJc 보다 앞이다.
    t = re.sub(r"<m:mcPr>(<m:mcJc[^/]*/>)\s*(<m:count[^/]*/>)</m:mcPr>",
               r"<m:mcPr>\2\1</m:mcPr>", t)

    rows = re.findall(r"<w:tbl>.*?</w:tbl>", t, re.S)
    out, cursor = [], 0
    for m in re.finditer(r"<w:tbl>.*?</w:tbl>", t, re.S):
        tbl = m.group(0)
        first = [True]

        def row(rm):
            props = "<w:cantSplit/>" + ("<w:tblHeader/>" if first[0] else "")
            first[0] = False
            body = rm.group(1)
            if body.startswith("<w:trPr>"):
                return "<w:tr>" + body.replace("<w:trPr>", "<w:trPr>" + props, 1) + "</w:tr>"
            return f"<w:tr><w:trPr>{props}</w:trPr>{body}</w:tr>"

        out.append(t[cursor:m.start()])
        out.append(re.sub(r"<w:tr>(.*?)</w:tr>", row, tbl, flags=re.S))
        cursor = m.end()
    out.append(t[cursor:])
    doc = enlarge_landscape("".join(out))

    # 표제지가 한 쪽을 온전히 쓰도록, 목차 블록 앞에서 쪽을 나눈다
    doc, n = re.subn(r"<w:sdt><w:sdtPr><w:docPartObj>",
                     '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
                     "<w:sdt><w:sdtPr><w:docPartObj>", doc, count=1)
    assert n == 1, "목차 블록을 못 찾아 표제지를 못 나눴다"
    p.write_text(doc)

    # pandoc 은 그림마다 Override 로 형식을 적는다. 규격상 맞지만 확장자
    # Default 도 함께 두는 편이 워드 구버전까지 안전하다.
    ct = work / "[Content_Types].xml"
    c = ct.read_text()
    if 'Extension="png"' not in c:
        c = c.replace("<Types ", "<Types ", 1).replace(
            "</Types>", '<Default Extension="png" ContentType="image/png"/></Types>')
        ct.write_text(c)

    repack(work, docx)
    return len(rows)


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    if not (BUILD / "img_meta.json").exists():
        sys.exit("먼저 scripts/docx/render_assets.py 를 실행해 그림을 만드십시오.")
    md = assemble()
    src = BUILD / "book.md"
    src.write_text(md)
    print(f"원고 {len(md):,}자")

    if not (BUILD / "reference.docx").exists():
        import make_ref
        make_ref.main()

    out = BUILD / OUT_NAME
    cmd = [find_pandoc(), str(src), "-o", str(out),
           "--reference-doc", str(BUILD / "reference.docx"),
           "--from", "markdown+raw_attribute+pipe_tables+tex_math_dollars",
           "--toc", "--toc-depth=3", "--resource-path", str(BUILD),
           "--metadata", f"title={TITLE}",
           "--metadata", f"subtitle={SUBTITLE}",
           "--metadata", f"date={DATE}",
           "--metadata", "toc-title=목차"]
    subprocess.run(cmd, check=True)
    n = polish_tables(out)
    print(f"표 {n}개 다듬음 · {out.name} {out.stat().st_size/1024/1024:.1f} MB")

    import toc
    print("목차 쪽번호 계산")
    entries = toc.fill(out)
    print(f"목차 {sum(1 for e in entries if e[3])}항목 완성 · "
          f"{out.stat().st_size/1024/1024:.1f} MB")


if __name__ == "__main__":
    main()
