"""마크다운 원본을 pandoc 이 docx 로 잘 옮길 수 있는 형태로 다듬는다.

원본은 GitHub 에서 읽히도록 쓰여 있어 docx 로 그대로 옮기면 깨지는 것들이 있다.
  · <details>/<summary> 접이식 블록   -> 워드에는 접이식이 없으므로 펼친다
  · <br> 줄바꿈 (표 칸 안)            -> pandoc 파이프 표는 칸 안 줄바꿈을 못 받는다
  · SVG 이미지                        -> 워드가 못 읽으므로 PNG 로 교체
  · mermaid 코드 블록                 -> 렌더한 PNG 로 교체
  · 문서 간 상대 링크                  -> 한 권으로 합치므로 링크를 풀고 이름만 남긴다
"""
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent                      # rf-curriculum/
BUILD = ROOT / "_build"
IMG = json.load(open(BUILD / "img_meta.json"))
MMD = json.load(open(BUILD / "mmd_meta.json"))

TEXT_W_CM = 16.0      # A4 폭 21 cm - 좌우 여백 2.5 cm 씩
MAX_H_CM = 19.0       # 그림 하나가 한 쪽을 넘지 않게
TALL_H_CM = 23.5      # 세로로 긴 도표는 쪽 높이를 끝까지 쓴다

PAGEBREAK = '\n\n```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```\n\n'

# ── 가로 쪽 (넓은 도표용)
# 가로 쪽 본문은 24.7 x 16.0 cm 이지만, 캡션이 같은 쪽에 앉도록
# 그림 높이는 14 cm 로 묶는다 (안 그러면 캡션만 다음 쪽으로 넘어간다)
LAND_W_CM, LAND_H_CM = 24.7, 13.0     # A4 가로, 여백 2.5 cm
MIN_PT = 6.5                          # 이보다 작아지면 읽을 수 없다고 본다
_FTR = '<w:footerReference w:type="default" r:id="rIdFtr"/>'
_A4 = ('<w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1418" w:right="1418" '
       'w:bottom="1418" w:left="1418" w:header="709" w:footer="709" w:gutter="0"/>')
_A4L = ('<w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/>'
        '<w:pgMar w:top="1418" w:right="1418" w:bottom="1418" w:left="1418" '
        'w:header="709" w:footer="709" w:gutter="0"/>')


def _sect(kind):
    # 구역을 끊는 빈 문단이다. 기본 높이로 두면 그림이 꽉 찬 쪽 뒤에
    # 빈 쪽이 하나 더 생기므로, 글자 크기와 여백을 최소로 만든다.
    return ("\n\n```{=openxml}\n"
            '<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="20" '
            'w:lineRule="exact"/><w:rPr><w:sz w:val="2"/></w:rPr><w:sectPr>'
            + _FTR + (_A4L if kind == "land" else _A4)
            + "</w:sectPr></w:pPr></w:p>\n```\n\n")


def est_pt(w, h, disp_cm):
    """도표 안 글자가 몇 pt 로 인쇄될지 어림한다 (렌더 배율 2배 기준 28 px)."""
    return 28 / w * disp_cm * 28.35


def landscape_fit(w, h):
    """가로 쪽에 놓을 때의 표시 폭."""
    return min(LAND_W_CM, LAND_H_CM * w / h)


def img_tag(png_name, w, h):
    """가로는 본문 폭에 맞추되, 세로로 긴 그림은 높이로 제한한다."""
    width = TEXT_W_CM
    if h / w * width > MAX_H_CM:
        width = MAX_H_CM * w / h
    return f"![](img/{png_name}){{width={width:.2f}cm}}"


def demote(md, by=1):
    """모듈 제목이 2수준이 되도록 모든 제목을 한 단계 내린다 (1수준은 Part 용)."""
    out, in_code = [], False
    for ln in md.split("\n"):
        if ln.lstrip().startswith("```"):
            in_code = not in_code
        if not in_code and re.match(r"^#{1,5} ", ln):
            ln = "#" * by + ln
        out.append(ln)
    return "\n".join(out)


def unfold_details(md):
    md = re.sub(r"[ \t]*</?details>[ \t]*\n?", "", md)
    md = re.sub(r"<summary>(.*?)</summary>",
                lambda m: "\n" + re.sub(r"</?b>", "**", m.group(1)).strip() + "\n", md, flags=re.S)
    return md


def fix_inline_html(md):
    # w:br 은 반드시 w:r 안에 있어야 한다. 문단 바로 밑에 두면 스키마 위반이다.
    md = re.sub(r"<br\s*/?>", "`<w:r><w:br/></w:r>`{=openxml}", md)
    md = re.sub(r"</?b>", "**", md)
    return md


def swap_images(md, src_file):
    base = src_file.parent

    def one(m):
        p = (base / m.group(1)).resolve()
        e = IMG.get(str(p))
        return img_tag(e["png"], e["w"], e["h"]) if e else m.group(0)

    return re.sub(r"!\[[^\]]*\]\(([^)]+)\)", one, md)


def swap_mermaid(md, src_file):
    from PIL import Image
    rel = str(src_file.relative_to(ROOT))
    n = [0]

    def one(_):
        n[0] += 1
        name = MMD.get(f"{rel}::{n[0]}")
        if not name:
            return ""
        w, h = Image.open(BUILD / "img" / name).size
        # 세로로 긴 도표는 어차피 한 쪽을 다 쓰므로 쪽 높이를 끝까지 쓴다
        tall_cap = TALL_H_CM if h > 2 * w else MAX_H_CM
        pw = min(TEXT_W_CM, tall_cap * w / h)
        lw = landscape_fit(w, h)
        # 가로로 돌려서 실제로 더 커지고, 세로로는 글자가 너무 작을 때만 돌린다
        if lw > pw * 1.15 and est_pt(w, h, pw) < MIN_PT:
            return f"<<<LAND>>>![](img/{name}){{width={lw:.2f}cm}}"
        return f"![](img/{name}){{width={pw:.2f}cm}}"

    md = re.sub(r"```mermaid\n.*?```", one, md, flags=re.S)
    return wrap_landscape(md)


def wrap_landscape(md):
    """<<<LAND>>> 로 표시된 그림과 그 캡션을 가로 쪽 구역으로 감싼다.

    OOXML 에서 구역 속성은 '그 구역의 마지막 문단' 에 붙는다. 그래서
    그림 앞에 세로 sectPr 을, 캡션 뒤에 가로 sectPr 을 놓으면
    그 사이만 가로 쪽이 된다.
    """
    lines, out = md.split("\n"), []
    for i, ln in enumerate(lines):
        if not ln.startswith("<<<LAND>>>"):
            out.append(ln)
            continue
        out.append(_sect("portrait"))          # 여기까지가 세로 구역
        out.append(ln.replace("<<<LAND>>>", ""))
        lines[i] = ""
        # 바로 뒤의 캡션(기울임 한 줄)까지 같은 구역에 넣는다
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            out.append(lines[j]); lines[j] = ""; j += 1
        if j < len(lines) and lines[j].startswith("*그림"):
            out.append(lines[j]); lines[j] = ""
        out.append(_sect("land"))              # 여기까지가 가로 구역
    return "\n".join(x for x in out if x is not None)


def flatten_links(md):
    """한 권으로 합치므로 문서 간 링크는 이름만 남기고, 바깥 링크만 살린다."""
    def one(m):
        label, target = m.group(1), m.group(2)
        if target.startswith(("http://", "https://")):
            return m.group(0)
        return f"**{label}**" if not label.startswith("!") else label
    return re.sub(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)", one, md)


def strip_repo_only(md):
    """저장소에서만 뜻이 있는 줄(문서 번호 머리글 등)은 책에서 뺀다."""
    md = re.sub(r"^\*\*문서 번호\*\*.*\n", "", md, flags=re.M)
    return md


def convert(src_file, drop_title=False):
    md = pathlib.Path(src_file).read_text()
    md = strip_repo_only(md)
    md = swap_mermaid(md, pathlib.Path(src_file))
    md = swap_images(md, pathlib.Path(src_file))
    md = unfold_details(md)
    md = fix_inline_html(md)
    md = flatten_links(md)
    md = demote(md)
    if drop_title:
        md = re.sub(r"^##[^#\n]*\n", "", md, count=1)
    return md.strip() + "\n"
