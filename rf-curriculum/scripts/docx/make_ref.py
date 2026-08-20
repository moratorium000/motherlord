"""pandoc 기본 reference.docx 를 한국어 기술서에 맞게 고친다.

pandoc 의 기본값은 A4 가 아니고 본문 글꼴이 테마에서 오므로 한글이 깨진다.
여기서 글꼴·크기·행간·여백·쪽번호를 직접 박아 넣는다.
"""
import pathlib
import re
import shutil
import sys
import zipfile
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent                      # rf-curriculum/
BUILD = ROOT / "_build"
REF = BUILD / "ref"
KO = "맑은 고딕"          # 윈도 워드 기본 한글 글꼴
MONO = "D2Coding"        # 없으면 워드가 대체한다
NAVY = "1F3864"
INK = "222222"
RULE = "BFBFBF"


def rfonts(ascii_=KO, ea=KO):
    return f'<w:rFonts w:ascii="{ascii_}" w:hAnsi="{ascii_}" w:eastAsia="{ea}" w:cs="{ascii_}"/>'


def para_style(sid, name, size_half_pt, *, color=INK, bold=False, before=0,
               after=120, based="Normal", outline=None, mono=False, italic=False,
               keep_next=False, page_break=False, bdr="", shd="", ind="",
               jc="both"):
    """pPr 의 자식 요소는 스키마가 순서를 강제한다.
    keepNext -> keepLines -> pageBreakBefore -> pBdr -> shd -> spacing -> ind
    -> jc -> outlineLvl 순서를 지켜야 워드가 파일을 연다."""
    ppr = ""
    if keep_next:
        ppr += "<w:keepNext/>"
    ppr += "<w:keepLines/>"
    if page_break:
        ppr += "<w:pageBreakBefore/>"
    ppr += bdr + shd
    ppr += f'<w:spacing w:before="{before}" w:after="{after}"/>'
    ppr += ind
    ppr += f'<w:jc w:val="{jc}"/>'
    if outline is not None:
        ppr += f'<w:outlineLvl w:val="{outline}"/>'
    b = "<w:b/><w:bCs/>" if bold else ""
    i = "<w:i/>" if italic else ""
    return (f'<w:style w:type="paragraph" w:styleId="{sid}">'
            f'<w:name w:val="{name}"/><w:basedOn w:val="{based}"/><w:qFormat/>'
            f'<w:pPr>{ppr}</w:pPr>'
            f'<w:rPr>{rfonts(MONO if mono else KO)}{b}{i}<w:color w:val="{color}"/>'
            f'<w:sz w:val="{size_half_pt}"/><w:szCs w:val="{size_half_pt}"/>'
            f'</w:rPr></w:style>')


def build_styles():
    p = REF / "word/styles.xml"
    t = p.read_text()

    # ── 문서 기본값: 글꼴·크기·행간
    t = re.sub(
        r"<w:rPrDefault>.*?</w:rPrDefault>",
        f'<w:rPrDefault><w:rPr>{rfonts()}<w:color w:val="{INK}"/>'
        f'<w:sz w:val="20"/><w:szCs w:val="20"/>'
        f'<w:lang w:val="en-US" w:eastAsia="ko-KR"/></w:rPr></w:rPrDefault>',
        t, flags=re.S)
    t = re.sub(
        r"<w:pPrDefault>.*?</w:pPrDefault>",
        '<w:pPrDefault><w:pPr><w:spacing w:after="110" w:line="288" '
        'w:lineRule="auto"/><w:jc w:val="both"/></w:pPr></w:pPrDefault>',
        t, flags=re.S)

    # ── 기존 제목/본문 스타일을 통째로 갈아 끼운다
    replace = {
        "Heading1": para_style(
            "Heading1", "heading 1", 40, color=NAVY, bold=True, after=260,
            outline=0, page_break=True, jc="left",
            bdr=f'<w:pBdr><w:bottom w:val="single" w:sz="12" w:space="6" '
                f'w:color="{NAVY}"/></w:pBdr>'),
        "Heading2": para_style("Heading2", "heading 2", 30, color=NAVY, bold=True,
                               before=360, after=160, outline=1, keep_next=True,
                               jc="left"),
        "Heading3": para_style("Heading3", "heading 3", 24, color=NAVY, bold=True,
                               before=300, after=120, outline=2, keep_next=True,
                               jc="left"),
        "Heading4": para_style("Heading4", "heading 4", 21, bold=True, before=240,
                               after=100, outline=3, keep_next=True, jc="left"),
        "Heading5": para_style("Heading5", "heading 5", 20, bold=True, before=200,
                               after=80, outline=4, keep_next=True, jc="left"),
        "BodyText": para_style("BodyText", "Body Text", 20),
        "FirstParagraph": para_style("FirstParagraph", "First Paragraph", 20,
                                     based="BodyText"),
        # Compact 는 표 칸과 촘촘한 목록에 쓰인다. 좁은 칸에서 양쪽정렬을 하면
        # 글자 사이가 흉하게 벌어지므로 왼쪽정렬로 둔다.
        "Compact": para_style("Compact", "Compact", 20, after=40, based="BodyText",
                              jc="left"),
        "Title": para_style("Title", "Title", 56, color=NAVY, bold=True, after=200,
                            jc="center"),
        "Subtitle": para_style("Subtitle", "Subtitle", 26, color=NAVY, after=160,
                               jc="center"),
        "Author": para_style("Author", "Author", 20, after=60, jc="center"),
        "Date": para_style("Date", "Date", 20, after=60, jc="center"),
        # 인용 상자 — 원문의 📌 ⚠️ 💡 상자가 여기로 온다
        "BlockText": para_style(
            "BlockText", "Block Text", 19, after=100,
            bdr=f'<w:pBdr><w:left w:val="single" w:sz="18" w:space="8" '
                f'w:color="{NAVY}"/></w:pBdr>',
            shd='<w:shd w:val="clear" w:fill="F4F6FA"/>',
            ind='<w:ind w:left="284"/>'),
        "ImageCaption": para_style("ImageCaption", "Image Caption", 18,
                                   color="555555", italic=True, after=200,
                                   jc="center"),
        "Caption": para_style("Caption", "Caption", 18, color="555555", italic=True),
        "TOCHeading": para_style("TOCHeading", "TOC Heading", 34, color=NAVY,
                                 bold=True, after=200, jc="left"),
    }
    for sid, xml in replace.items():
        pat = rf'<w:style w:type="paragraph"([^>]*)w:styleId="{sid}">.*?</w:style>'
        m = re.search(pat, t, flags=re.S)
        assert m, f"{sid} 스타일을 못 찾았다"
        # pandoc 이 붙여 둔 w:customStyle 표시는 그대로 물려받는다
        if "customStyle" in m.group(1):
            xml = xml.replace('<w:style w:type="paragraph" w:styleId=',
                              '<w:style w:type="paragraph" w:customStyle="1" w:styleId=')
        t = t[:m.start()] + xml + t[m.end():]

    # ── 코드: 블록(SourceCode)과 인라인(VerbatimChar)
    # 실습 출력에 한글이 섞여 있어 줄이 길다. 책에서 가장 긴 코드 줄이
    # 106칸이므로, 7.5 pt 로 두면 거의 모든 줄이 접히지 않고 한 줄에 들어간다.
    src = para_style("SourceCode", "Source Code", 15, mono=True, after=0,
                     jc="left", shd='<w:shd w:val="clear" w:fill="F5F5F5"/>',
                     ind='<w:ind w:left="142" w:right="0"/>')
    # 워드가 F9 로 목차를 다시 만들 때 쓰는 스타일. 없으면 제멋대로 그린다.
    toc = "".join(
        para_style(f"TOC{i}", f"toc {i}", sz, after=0, jc="left",
                   bold=(i == 1), before=(40 if i == 1 else 0),
                   ind=f'<w:ind w:left="{ind}" w:right="480"/>')
        for i, sz, ind in ((1, 20, 0), (2, 19, 240), (3, 18, 480)))
    t = t.replace("</w:styles>", src + toc + "</w:styles>")
    t = re.sub(r'<w:style w:type="character" w:styleId="VerbatimChar">.*?</w:style>',
               '<w:style w:type="character" w:styleId="VerbatimChar">'
               '<w:name w:val="Verbatim Char"/><w:qFormat/>'
               f'<w:rPr>{rfonts(MONO)}<w:sz w:val="18"/>'
               '<w:shd w:val="clear" w:fill="F0F0F0"/></w:rPr></w:style>',
               t, flags=re.S)

    # ── 표: 가는 실선 + 머리행 음영
    border = ('<w:tblBorders>' + "".join(
        f'<w:{e} w:val="single" w:sz="4" w:space="0" w:color="{RULE}"/>'
        for e in ("top", "left", "bottom", "right", "insideH", "insideV")) +
        '</w:tblBorders>')
    t = re.sub(r'<w:style w:type="table" w:styleId="Table">.*?</w:style>',
               '<w:style w:type="table" w:styleId="Table">'
               '<w:name w:val="Table"/><w:qFormat/>'
               f'<w:rPr>{rfonts()}<w:sz w:val="18"/></w:rPr>'
               f'<w:tblPr>{border}<w:tblCellMar>'
               '<w:top w:w="60" w:type="dxa"/><w:left w:w="90" w:type="dxa"/>'
               '<w:bottom w:w="60" w:type="dxa"/><w:right w:w="90" w:type="dxa"/>'
               '</w:tblCellMar></w:tblPr>'
               '<w:tblStylePr w:type="firstRow"><w:rPr><w:b/></w:rPr>'
               '<w:tcPr><w:shd w:val="clear" w:fill="E8EDF5"/></w:tcPr>'
               '</w:tblStylePr></w:style>',
               t, flags=re.S)
    p.write_text(t)


FOOTER = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:p><w:pPr><w:spacing w:before="120"/><w:jc w:val="center"/></w:pPr>
<w:r><w:rPr>%s<w:color w:val="777777"/><w:sz w:val="17"/></w:rPr>
<w:fldChar w:fldCharType="begin"/></w:r>
<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>
<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>''' % rfonts()


def build_layout():
    """A4 세로, 여백 2.5 cm, 가운데 쪽번호."""
    (REF / "word/footer1.xml").write_text(FOOTER)

    r = REF / "word/_rels/document.xml.rels"
    t = r.read_text()
    assert "footer1.xml" not in t
    t = t.replace("</Relationships>",
                  '<Relationship Id="rIdFtr" Type="http://schemas.openxmlformats.org/'
                  'officeDocument/2006/relationships/footer" Target="footer1.xml"/>'
                  "</Relationships>")
    r.write_text(t)

    c = REF / "[Content_Types].xml"
    t = c.read_text()
    # pandoc 은 그림 확장자 선언을 참조 문서에서 물려받는다. 없으면 워드도
    # LibreOffice 도 파일을 아예 못 연다.
    assert 'Extension="png"' not in t
    t = t.replace(
        "</Types>",
        '<Default Extension="png" ContentType="image/png"/>'
        '<Default Extension="jpeg" ContentType="image/jpeg"/>'
        '<Default Extension="jpg" ContentType="image/jpeg"/>'
        '<Override PartName="/word/footer1.xml" ContentType="application/vnd.'
        'openxmlformats-officedocument.wordprocessingml.footer+xml"/></Types>')
    c.write_text(t)

    d = REF / "word/document.xml"
    t = d.read_text()
    t = re.sub(r"<w:sectPr>.*?</w:sectPr>",
               '<w:sectPr><w:footerReference w:type="default" r:id="rIdFtr"/>'
               '<w:pgSz w:w="11906" w:h="16838"/>'      # A4
               '<w:pgMar w:top="1418" w:right="1418" w:bottom="1418" w:left="1418" '
               'w:header="709" w:footer="709" w:gutter="0"/>'
               "</w:sectPr>", t, flags=re.S)
    d.write_text(t)


def main():
    """pandoc 의 기본 참조 문서를 꺼내 한국어 기술서용으로 고친다."""
    sys.path.insert(0, str(HERE))
    from build import find_pandoc, repack

    BUILD.mkdir(parents=True, exist_ok=True)
    default = BUILD / "reference_default.docx"
    default.write_bytes(subprocess.run(
        [find_pandoc(), "--print-default-data-file", "reference.docx"],
        capture_output=True, check=True).stdout)

    shutil.rmtree(REF, ignore_errors=True)
    REF.mkdir(parents=True)
    with zipfile.ZipFile(default) as z:
        z.extractall(REF)

    build_styles()
    build_layout()
    out = BUILD / "reference.docx"
    n = repack(REF, out)
    print(f"reference.docx {out.stat().st_size:,} bytes / {n} parts")
    return out


if __name__ == "__main__":
    main()
