# 교재를 한 권의 DOCX 로 묶기

저장소의 마크다운 원본(모듈 본문 · 부록 A/D/E · 커리큘럼 설계서)을
**워드 문서 한 권**으로 만드는 도구입니다. 결과물은 `_build/` 아래에 나오고,
바로 열어 볼 수 있도록 **저장소 최상단에도 DOCX·PDF 를 함께 담아 둡니다**
(`rf-curriculum/RF_시스템_엔지니어링_교재.docx` · `.pdf`). 모듈이 추가될
때마다 다시 빌드해 갱신합니다.

수록 모듈은 `build.py` 의 `PARTS` 목록이 정합니다 — **새 모듈을 쓰면 여기에
한 줄 추가**해야 교재에 들어갑니다.

## 실행

```bash
pip install pypandoc_binary cairosvg pillow      # pandoc 은 pypandoc 이 들고 온다
npm i @mermaid-js/mermaid-cli                    # scripts/docx/ 아래에

python3 scripts/docx/render_assets.py            # 그림 -> PNG (한 번만)
python3 scripts/docx/build.py                    # 본문 조립 -> DOCX
```

결과: `_build/RF_시스템_엔지니어링_교재.docx` (M16 까지 반영 시 목차 342항목 · 17.9 MB)

PDF 는 LibreOffice 로 변환합니다.

```bash
soffice --headless --convert-to pdf --outdir _build _build/RF_시스템_엔지니어링_교재.docx
```

원본 마크다운만 고쳤다면 `build.py` 만 다시 돌리면 됩니다. 그림을 새로
생성했거나 mermaid 블록을 고쳤다면 `render_assets.py` 부터 다시 돌립니다.

## 무엇을 하는가

| 파일 | 역할 |
|---|---|
| `render_assets.py` | 본문이 참조하는 SVG 82종과 mermaid 블록 20종을 PNG 로 변환하고, 어느 그림이 어느 파일인지 표로 남긴다 |
| `make_ref.py` | pandoc 의 기본 서식 문서를 꺼내 한국어 기술서용으로 고친다 — 글꼴(맑은 고딕), A4 여백, 제목·인용 상자·코드·표 스타일, 가운데 쪽번호 |
| `prep.py` | 마크다운을 워드가 받아들일 형태로 다듬는다 (아래) |
| `build.py` | 부(Part) 구조로 원고를 엮고 pandoc 을 돌린 뒤 표와 그림을 후처리한다 |
| `toc.py` | 목차의 쪽번호를 실제로 계산해 채운다 |

## 워드로 옮기면서 손봐야 했던 것들

원본은 GitHub 에서 읽히도록 쓰였기 때문에 그대로 옮기면 깨지는 것들이 있습니다.
아래는 전부 **실제로 렌더해 확인한 뒤** 넣은 대응입니다.

**본문 구조**

- `<details>`/`<summary>` 접이식 확인 문제 — 워드에는 접이식이 없어 펼친다
- 표 칸 안의 `<br>` — pandoc 파이프 표가 칸 안 줄바꿈을 못 받아 OOXML 줄바꿈으로 바꾼다
- 문서 간 상대 링크 — 한 권으로 합치므로 링크를 풀고 이름만 남긴다 (바깥 링크는 살린다)

**수식** — LibreOffice·워드가 OMML 로 못 그리는 표기를 같은 뜻의 다른 표기로 바꾼다

| 원본 표기 | 증상 | 대응 |
|---|---|---|
| `\|x\|` | 물음표(¿)로 깨진다 | `\left\| … \right\|` |
| `\lvert` `\rvert` `\vert` | 전부 깨진다 | 위와 같음 |
| `\mathrm{dBm}` | `d B m` 으로 벌어진다 | `\text{dBm}` |
| `\underbrace{}_{}` | 밑의 설명이 통째로 사라진다 | 식에서 떼어 바로 아래 줄로 옮긴다 |
| `\boxed{}` | 상자가 안 그려진다 | 상자를 벗긴다 (내용은 그대로) |

**그림**

- SVG·mermaid 를 PNG 로 바꾸고, 본문 폭(16 cm)에 맞춰 크기를 정한다
- 세로 쪽에서 글자가 6.5 pt 밑으로 내려가는 **넓은 도표 8종은 가로 쪽**에 앉힌다.
  pandoc 이 그림을 참조 문서의 세로 폭으로 깎아 버리므로 변환 뒤에 다시 늘린다
- 세로로 긴 도표는 쪽 높이를 끝까지 쓰게 한다

**표**

- 402개 표의 모든 행에 `cantSplit` 을, 머리행에 `tblHeader` 를 넣어
  쪽 경계에서 행이 잘리지 않고 머리행이 쪽마다 반복되게 한다
- 좁은 칸에서 양쪽정렬은 글자 사이가 벌어지므로 표 안은 왼쪽정렬

**목차**

pandoc 은 목차 자리에 빈 필드만 넣습니다. 워드는 열 때 스스로 채우지만
미리보기·LibreOffice·구글 문서에서는 **빈 쪽**으로 보입니다. 그래서 실제로
PDF 를 뽑아 제목이 몇 쪽에 있는지 읽어 낸 뒤 필드의 '저장된 결과' 자리에
써 넣습니다. 필드는 그대로 살아 있어 워드에서 F9 로 다시 계산됩니다.
목차가 들어가면 뒤쪽 번호가 밀리므로 번호가 안정될 때까지 되풀이합니다.

## 확인 방법

```bash
python3 .../office/validate.py _build/RF_시스템_엔지니어링_교재.docx
soffice --headless --convert-to pdf --outdir _build _build/RF_*.docx
pdftoppm -jpeg -r 80 -f 1 -l 8 _build/RF_*.pdf page      # 눈으로 본다
```

`build.py` 는 스스로도 확인합니다 — 가로 쪽 그림 수가 가로 구역 수와 맞는지,
목차 쪽번호가 문서 순서를 지키는지, 다시 묶은 docx 에 `[Content_Types].xml`
이 들어 있는지(빠지면 워드가 파일을 아예 못 엽니다)를 단언으로 막아 둡니다.
