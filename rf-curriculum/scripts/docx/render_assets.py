"""교재 그림을 워드가 읽을 수 있는 PNG 로 만든다.

본문의 그림은 두 갈래다.
  · `assets/**/*.svg`  — 스크립트가 생성한 플롯과 손그림 회로도
  · 본문 안의 ```mermaid 블록 — 블록도·결정 트리

워드는 SVG 를 제대로 못 읽고 mermaid 는 아예 모르므로, 둘 다 PNG 로 바꾼 뒤
어느 그림이 어느 파일이 되었는지를 `img_meta.json` · `mmd_meta.json` 에 적어 둔다.
build.py 가 그 표를 보고 본문의 그림 자리를 바꿔 끼운다.

    python3 scripts/docx/render_assets.py
"""
import json
import pathlib
import re
import subprocess
import sys

import cairosvg
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent                      # rf-curriculum/
BUILD = ROOT / "_build"
IMG = BUILD / "img"

PNG_WIDTH = 1700          # 인쇄해도 뭉개지지 않을 만큼
MMD_SCALE = "2"           # mermaid 는 2배로 그려야 글자가 선명하다

SOURCES = (sorted((ROOT / "01_모듈").glob("*.md"))
           + sorted((ROOT / "02_캡스톤").glob("*.md"))
           + sorted((ROOT / "03_부록").glob("*.md"))
           + sorted(ROOT.glob("00_*.md")))


def find_mmdc():
    """mermaid-cli 를 찾는다. 없으면 어떻게 까는지 알려 준다."""
    for c in (HERE / "node_modules/.bin/mmdc", BUILD / "node_modules/.bin/mmdc"):
        if c.exists():
            return c
    found = subprocess.run(["which", "mmdc"], capture_output=True, text=True)
    if found.returncode == 0:
        return pathlib.Path(found.stdout.strip())
    sys.exit("mermaid-cli 가 없습니다.  npm i @mermaid-js/mermaid-cli  후 다시 실행하십시오.")


def render_svgs():
    """본문이 실제로 참조하는 SVG 만 PNG 로 바꾼다."""
    refs = {}
    for f in SOURCES:
        for m in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", f.read_text()):
            p = (f.parent / m).resolve()
            if not p.exists():
                sys.exit(f"{f.name} 이 없는 그림을 가리킵니다: {m}")
            refs[p] = None

    meta = {}
    for src in sorted(refs):
        dst = IMG / f"{src.parent.name}_{src.stem}.png"
        cairosvg.svg2png(url=str(src), write_to=str(dst), output_width=PNG_WIDTH)
        w, h = Image.open(dst).size
        meta[str(src)] = dict(png=dst.name, w=w, h=h)
    (BUILD / "img_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1))
    return len(meta)


def render_mermaid():
    """본문 안의 mermaid 블록을 등장 순서대로 PNG 로 그린다."""
    mmdc = find_mmdc()
    # mermaid-cli 는 크로미엄을 띄운다. 컨테이너에서는 샌드박스를 꺼야 뜬다.
    pp = BUILD / "puppeteer.json"
    pp.write_text('{"args":["--no-sandbox","--disable-setuid-sandbox"]}')

    idx, tmp = {}, BUILD / "mmd"
    tmp.mkdir(exist_ok=True)
    for f in SOURCES:
        key = f.stem.split("_")[0]
        blocks = re.findall(r"```mermaid\n(.*?)```", f.read_text(), re.S)
        for i, b in enumerate(blocks, 1):
            src = tmp / f"{key}_{i}.mmd"
            src.write_text(b)
            png = IMG / f"mmd_{key}_{i}.png"
            r = subprocess.run(
                [str(mmdc), "-p", str(pp), "-i", str(src), "-o", str(png),
                 "-b", "white", "-w", str(PNG_WIDTH), "-s", MMD_SCALE],
                capture_output=True, text=True, cwd=BUILD)
            if r.returncode:
                sys.exit(f"{f.name} 의 mermaid {i}번을 못 그렸습니다:\n{r.stderr[-500:]}")
            idx[f"{f.relative_to(ROOT)}::{i}"] = png.name
    (BUILD / "mmd_meta.json").write_text(
        json.dumps(idx, ensure_ascii=False, indent=1))
    return len(idx)


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    n_svg = render_svgs()
    n_mmd = render_mermaid()
    mb = sum(p.stat().st_size for p in IMG.glob("*.png")) / 1024 / 1024
    print(f"SVG {n_svg}개 · mermaid {n_mmd}개 -> PNG ({mb:.1f} MB)")


if __name__ == "__main__":
    main()
