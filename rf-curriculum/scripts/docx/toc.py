"""목차 채우기.

pandoc 은 목차 자리에 '빈 TOC 필드' 만 넣는다. 워드는 열 때 스스로 채우지만,
그 밖의 뷰어(미리보기·LibreOffice·구글 문서)에서는 **빈 쪽**으로 보인다.
그래서 실제로 PDF 를 뽑아 제목이 몇 쪽에 있는지 읽어 낸 뒤, 그 값을 필드의
'저장된 결과' 자리에 미리 써 넣는다. 워드에서는 필드가 그대로 살아 있어
쪽이 밀리면 F9 로 다시 계산된다.

목차가 들어가면 뒷쪽 번호가 통째로 밀리므로, 번호가 더 이상 안 바뀔 때까지
같은 과정을 되풀이한다.
"""
import pathlib
import re
import shutil
import subprocess
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent                      # rf-curriculum/
BUILD = ROOT / "_build"
TEXT_W_DXA = 9071          # A4 폭에서 좌우 여백을 뺀 본문 폭
INDENT = {1: 0, 2: 240, 3: 480}
SIZE = {1: 20, 2: 19, 3: 18}


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def read_headings(doc_xml):
    """문서 순서대로 (수준, 제목, 북마크이름) 을 뽑는다."""
    out = []
    for m in re.finditer(
            r'(?:<w:bookmarkStart w:id="\d+" w:name="([^"]*)"\s*/>\s*)?'
            r'<w:p><w:pPr><w:pStyle w:val="Heading([1-3])"\s*/></w:pPr>(.*?)</w:p>',
            doc_xml, re.S):
        anchor, lvl, body = m.group(1), int(m.group(2)), m.group(3)
        text = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", body, re.S))
        text = (text.replace("&amp;", "&").replace("&lt;", "<")
                    .replace("&gt;", ">").replace("&quot;", '"')).strip()
        if text:
            out.append((lvl, text, anchor))
    return out


def page_map(pdf, headings):
    """PDF 쪽별 글자를 훑어 각 제목이 처음 나오는 쪽을 찾는다."""
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                         capture_output=True, text=True, check=True).stdout
    pages = txt.split("\f")
    flat = [re.sub(r"\s+", "", p) for p in pages]

    # 목차를 한 번 채워 넣고 나면 목차 쪽에도 모든 제목이 적혀 있다.
    # 그대로 훑으면 전부 목차 쪽에서 걸려 쪽번호가 죄다 2가 된다.
    # 점선(리더)이 많은 앞쪽 연속 구간을 목차로 보고 건너뛴다.
    start = 0
    for i, raw in enumerate(pages[:40]):
        if raw.count("....") >= 5:
            start = i + 1
        elif start:
            break
    pos, res = start, []
    for lvl, text, anchor in headings:
        key = re.sub(r"\s+", "", text)
        found = None
        for i in range(pos, len(flat)):
            if key and key in flat[i]:
                found = i + 1
                pos = i          # 제목은 문서 순서대로 나오므로 뒤로만 찾는다
                break
        res.append((lvl, text, anchor, found))
    return res


# 모듈마다 되풀이되는 꼬리 절은 목차에서 뺀다 (본문에는 그대로 있다)
SKIP = {"다음 모듈", "변경 이력"}


def toc_xml(entries):
    parts = []
    for lvl, text, anchor, page in entries:
        if page is None or text.strip() in SKIP:
            continue
        run = (f'<w:rPr><w:rFonts w:ascii="맑은 고딕" w:hAnsi="맑은 고딕" '
               f'w:eastAsia="맑은 고딕"/><w:sz w:val="{SIZE[lvl]}"/>'
               + ("<w:b/>" if lvl == 1 else "") + "</w:rPr>")
        inner = (f'<w:r>{run}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'
                 f'<w:r>{run}<w:tab/><w:t>{page}</w:t></w:r>')
        if anchor:
            inner = f'<w:hyperlink w:anchor="{esc(anchor)}">{inner}</w:hyperlink>'
        parts.append(
            f'<w:p><w:pPr><w:pStyle w:val="TOC{lvl}"/>'
            f'<w:tabs><w:tab w:val="right" w:leader="dot" w:pos="{TEXT_W_DXA}"/></w:tabs>'
            f'<w:spacing w:before="{40 if lvl == 1 else 0}" w:after="0"/>'
            f'<w:ind w:left="{INDENT[lvl]}" w:right="480" w:hanging="0"/>'
            f'<w:jc w:val="left"/></w:pPr>{inner}</w:p>')
    return "".join(parts)


def inject(docx, entries):
    work = BUILD / "_toc"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir()
    with zipfile.ZipFile(docx) as z:
        z.extractall(work)
    p = work / "word/document.xml"
    t = p.read_text()
    body = toc_xml(entries)
    # 필드의 '저장된 결과' 자리(separate 와 end 사이)에 목차를 써 넣는다.
    new, n = re.subn(
        r'(<w:fldChar w:fldCharType="separate"\s*/>)(.*?)(<w:fldChar w:fldCharType="end"\s*/>)',
        lambda m: m.group(1) + "</w:r></w:p>" + body + "<w:p><w:r>" + m.group(3),
        t, count=1, flags=re.S)
    assert n == 1, "TOC 필드를 못 찾았다"
    p.write_text(new)

    from build import repack
    repack(work, docx)
    return sum(1 for e in entries if e[3])


def render(docx):
    pdf = docx.with_suffix(".pdf")
    pdf.unlink(missing_ok=True)
    subprocess.run(["soffice", "--headless",
                    "-env:UserInstallation=file:///tmp/lo_p3",
                    "--convert-to", "pdf", "--outdir", str(docx.parent), str(docx)],
                   capture_output=True, timeout=900)
    assert pdf.exists(), "PDF 변환 실패"
    return pdf


def fill(docx, rounds=4):
    prev = None
    for i in range(1, rounds + 1):
        pdf = render(docx)
        with zipfile.ZipFile(docx) as z:
            doc = z.read("word/document.xml").decode()
        entries = page_map(pdf, read_headings(doc))
        nums = [e[3] for e in entries]
        missing = [e[1] for e in entries if e[3] is None]
        got = [n for n in nums if n]
        # 잘못 찾아 놓고 '안정됐다' 고 넘어가는 일이 없도록 확인한다
        assert got == sorted(got), "쪽번호가 문서 순서와 어긋난다"
        import zipfile as _z  # noqa
        last_page = int(subprocess.run(
            ["pdfinfo", str(pdf)], capture_output=True, text=True,
            check=True).stdout.split("Pages:")[1].split()[0])
        assert got and got[-1] > last_page * 0.5, (
            f"마지막 제목이 {got[-1] if got else None}쪽 — 전체 {last_page}쪽에 비해 "
            "너무 앞이다. 목차 쪽을 잘못 건너뛴 것 같다")
        print(f"  {i}회차: 항목 {len(entries)}개 · 쪽 못 찾음 {len(missing)}개"
              + (f" {missing[:3]}" if missing else ""))
        if nums == prev:
            print("  쪽번호가 안정됨")
            return entries
        prev = nums
        inject(docx, entries)
    return entries
