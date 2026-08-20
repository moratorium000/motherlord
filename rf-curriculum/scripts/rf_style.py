#!/usr/bin/env python3
"""
RF 커리큘럼 공용 플롯 스타일
============================

설계서 §8.3 "그림 품질 규약"을 코드로 강제한다. 모든 데이터 플롯은
이 모듈의 `setup()` 을 호출한 뒤 그려야 한다.

    import rf_style
    fig, ax = rf_style.figure()
    ...
    rf_style.save(fig, "M08", "compression_curve")

이 모듈이 해결하는 문제
-----------------------
1. **한글 깨짐** — 컨테이너 기본 폰트(DejaVu Sans)에는 한글 글리프가 없어
   축 이름을 한글로 쓰면 네모 상자로 나온다. koreanize-matplotlib이 제공하는
   NanumGothic을 등록해 해결한다.

2. **보는 사람 환경에 따라 글자가 달라지는 문제** — SVG로 저장할 때
   기본값(svg.fonttype='none')은 글자를 <text>로 남겨 두어, 한글 폰트가 없는
   PC에서 다시 깨진다. `svg.fonttype='path'` 로 글자를 벡터 경로로 변환해
   **어떤 환경에서도 동일하게** 보이도록 한다. (파일이 조금 커지는 대신
   재현성을 얻는다.)

3. **색상만으로 정보를 전달하는 문제** — 흑백 인쇄와 색각 이상을 고려해
   `CYCLE` 은 색과 선 모양(실선/파선/점선)을 함께 바꾼다.

4. **마이너스 기호 깨짐** — RF는 −95 dBm 처럼 음수를 항상 쓴다.
   유니코드 마이너스가 폰트에 없으면 깨지므로 ASCII 하이픈으로 통일한다.
"""

from pathlib import Path
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt          # noqa: E402
from cycler import cycler                # noqa: E402

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# 색각 이상을 고려한 팔레트 (Okabe-Ito 계열)
COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"]
DASHES = ["-", "--", "-.", ":", (0, (5, 1, 1, 1)), (0, (3, 1, 3, 1))]

GRID = "#D9D9D9"
INK = "#1A1A1A"
ACCENT = "#C0392B"      # 강조: 판정선, 규격 한계선
MUTED = "#7F7F7F"       # 보조: 이상적 연장선, 참고선

_READY = False


def setup():
    """rcParams 를 커리큘럼 규약에 맞춘다. 여러 번 불러도 안전하다."""
    global _READY
    if _READY:
        return
    try:
        import koreanize_matplotlib  # noqa: F401  (import 만으로 폰트가 등록됨)
        family = "NanumGothic"
    except Exception:                      # 폰트 패키지가 없는 환경 대비
        family = "DejaVu Sans"
        print("[rf_style] 경고: koreanize-matplotlib 미설치. 한글이 깨질 수 있습니다. "
              "pip install koreanize-matplotlib")

    plt.rcParams.update({
        "font.family": family,
        "axes.unicode_minus": False,       # 유니코드 마이너스 대신 ASCII 하이픈
        "svg.fonttype": "path",            # 글자를 경로로 → 환경 무관 재현
        "figure.dpi": 110,
        "savefig.dpi": 110,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",      # 다크 테마에서도 읽히도록 배경 명시
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "axes.linewidth": 1.0,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "xtick.color": INK,
        "ytick.color": INK,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "legend.frameon": True,
        "legend.framealpha": 0.92,
        "legend.edgecolor": GRID,
        "lines.linewidth": 1.9,
        "axes.prop_cycle": cycler(color=COLORS) + cycler(linestyle=DASHES),
    })
    _READY = True


def figure(w=7.0, h=4.2, **kw):
    """규약에 맞춘 figure/axes 한 쌍을 만든다."""
    setup()
    return plt.subplots(figsize=(w, h), **kw)


def limit_line(ax, y, label, side="upper"):
    """규격 한계선을 그린다. 측정 리포트 그림에서 반복적으로 쓰인다."""
    ax.axhline(y, color=ACCENT, lw=1.6, ls="--", zorder=5)
    va = "bottom" if side == "upper" else "top"
    ax.annotate(label, xy=(0.99, y), xycoords=("axes fraction", "data"),
                ha="right", va=va, color=ACCENT, fontsize=9,
                fontweight="bold")


def reference_line(ax, *args, **kw):
    """이상적 연장선 등 보조선."""
    kw.setdefault("color", MUTED)
    kw.setdefault("lw", 1.2)
    kw.setdefault("ls", ":")
    kw.setdefault("zorder", 1)
    return ax.plot(*args, **kw)


def save(fig, module, name, formats=("svg",)):
    """assets/<module>/<name>.<fmt> 로 저장한다.

    module: "M08" 처럼 모듈 번호. 그림이 어느 모듈 소유인지 경로로 드러낸다.
    """
    out = ASSETS / module
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for fmt in formats:
        p = out / f"{name}.{fmt}"
        fig.savefig(p, format=fmt)
        paths.append(p)
    plt.close(fig)
    return paths


def caption(module, name, title, howto):
    """설계서 §8.3이 요구하는 '캡션 + 읽는 법' 마크다운을 만든다.

    그림마다 읽는 법을 붙이는 이유: 초심자는 그림을 '볼' 줄 모른다.
    축이 무엇이고 어느 지점을 봐야 하는지 문장으로 알려 주어야 한다.
    """
    return (f"![{title}](../assets/{module}/{name}.svg)\n\n"
            f"*그림 {module}-{name}. {title}. {howto}*\n")


if __name__ == "__main__":
    # 자체 점검: 한글 라벨, 음수, 한계선, 선 구분이 모두 정상인지 확인한다.
    import numpy as np

    fig, ax = figure()
    x = np.linspace(-30, 10, 200)
    for i, g in enumerate([20, 17, 14]):
        y = x + g - np.log1p(np.exp((x + g - 5) * 0.6)) / 0.6
        ax.plot(x, y, label=f"이득 {g} dB")
    reference_line(ax, x, x + 20, label="이상적 선형 연장선")
    limit_line(ax, 5, "규격 한계 +5 dBm")
    ax.set_xlabel("입력 전력 (dBm)")
    ax.set_ylabel("출력 전력 (dBm)")
    ax.set_title("자체 점검용 이득 압축 곡선")
    ax.legend(loc="upper left")
    p = save(fig, "_selftest", "style_check", formats=("svg", "png"))
    print("자체 점검 그림 저장:", *[str(x) for x in p], sep="\n  ")
