#!/usr/bin/env python3
"""
M09 (주파수 변환과 신호원) 데이터 그림 생성기
=============================================

    python3 scripts/gen_fig_m09.py

출력: assets/M09/*.svg

M08 과 같은 방식으로, 각 함수가 본문에 인용할 값을 돌려주고
__main__ 에서 자체 검산까지 출력한다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt

import rf_style as S

# ── 이 모듈 전체에서 쓰는 예제 주파수 계획 (2.4 GHz ISM 수신기) ────────
RF_LO, RF_HI = 2400.0, 2483.5      # ISM 대역 [MHz]
RF = 2450.0                        # 대표 채널
IF = 350.0                         # 중간주파수
LO = RF + IF                       # 하이사이드 LO = 2800 MHz
IMAGE = LO + IF                    # 이미지 = 3150 MHz
HALF_IF = RF + IF / 2              # 하프-IF 스퍼 = 2625 MHz

K_B = 1.380649e-23
T0 = 290.0
F0_VCO = 2.4e9


def _stem(ax, f, p, label, col, lw=3.0, dy=3.0, fs=9.0, ha="center"):
    ax.plot([f, f], [-90, p], ls="-", lw=lw, color=col, solid_capstyle="butt",
            zorder=4)
    if label:
        ax.annotate(label, xy=(f, p), xytext=(f, p + dy), ha=ha, fontsize=fs,
                    color=col, fontweight="bold", zorder=6)


# ══════════════════════════════════════════ M09-1: 주파수 변환
def m09_conversion():
    """곱하면 합과 차가 나온다 — 스펙트럼 세 장."""
    S.setup()
    fig, axes = plt.subplots(3, 1, figsize=(8.4, 7.4), sharex=True)
    fig.patch.set_facecolor("white")

    for ax in axes:
        ax.set_xlim(0, 5600)
        ax.set_ylim(-46, 30)
        ax.grid(alpha=0.4)
        ax.set_ylabel("레벨 (dBm)")

    _stem(axes[0], RF, -30, f"RF {RF:.0f} MHz\n(약한 신호)", S.COLORS[0],
          ha="right")
    _stem(axes[0], LO, 7, f"LO {LO:.0f} MHz\n(내가 만든 강한 신호)", S.COLORS[1])
    axes[0].set_title("① 믹서에 들어가는 것 — 받은 신호와 내가 만든 신호",
                      fontsize=10.5)

    _stem(axes[1], LO - RF, -37, f"차 (LO−RF)\n{LO-RF:.0f} MHz  ← 이것이 IF",
          S.ACCENT, ha="left")
    _stem(axes[1], LO + RF, -37, f"합 (LO+RF)\n{LO+RF:.0f} MHz", S.COLORS[2],
          ha="right")
    _stem(axes[1], LO, -22, "LO 누설", S.MUTED, lw=2.0, fs=8.5)
    axes[1].text(2900, 20, "믹서 출력에는 이 넷이 함께 나온다", fontsize=9,
                 color=S.INK, ha="left",
                 bbox=dict(fc="white", ec=S.GRID, alpha=0.96))
    _stem(axes[1], RF, -37, "RF 누설", S.MUTED, lw=2.0, fs=8.5, dy=12)
    axes[1].set_title("② 곱셈의 결과 — 합과 차가 동시에 나온다", fontsize=10.5)

    _stem(axes[2], LO - RF, -37, f"IF = {IF:.0f} MHz\n원하는 것만 남았다",
          S.ACCENT, ha="left", dy=5)
    fx = np.linspace(0, 5600, 2000)
    # 통과대역에서 0, 바깥에서 -60 dB. 분모 형태를 그대로 쓰면 부호가
    # 뒤집혀 '노치'가 그려진다 (실제로 한 번 그렇게 그렸다).
    filt = -60 * (1 - 1 / (1 + ((fx - IF) / 60) ** 6))
    axes[2].plot(fx, filt + 16, ls="--", lw=1.8, color=S.COLORS[3],
                 label="IF 대역통과 필터 (통과대역만 0 dB)")
    axes[2].legend(loc="upper right", fontsize=9)
    axes[2].set_title("③ IF 필터를 지나면 — 나머지는 전부 버린다", fontsize=10.5)
    axes[2].set_xlabel("주파수 (MHz)")

    fig.suptitle("그림 M09-1  믹서는 주파수를 옮긴다 — 합과 차가 함께 나온다",
                 fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M09", "conversion")
    return dict(rf=RF, lo=LO, if_=LO - RF, sum_=LO + RF)


# ══════════════════════════════════════════ M09-2: 이미지 주파수
def m09_image():
    """이미지 주파수 — LO 를 사이에 두고 대칭인 두 신호."""
    S.setup()
    fig, axes = plt.subplots(2, 1, figsize=(8.6, 6.4))
    fig.patch.set_facecolor("white")

    ax = axes[0]
    ax.set_xlim(2250, 3350)
    ax.set_ylim(-58, 22)
    _stem(ax, RF, -30, f"원하는 신호\n{RF:.0f} MHz", S.COLORS[0], dy=4)
    _stem(ax, IMAGE, -30, f"이미지\n{IMAGE:.0f} MHz", S.ACCENT, dy=4)
    _stem(ax, LO, 7, f"LO {LO:.0f}", S.COLORS[1], dy=3)

    for f, col, yy in ((RF, S.COLORS[0], -44), (IMAGE, S.ACCENT, -52)):
        ax.annotate("", xy=(LO, yy), xytext=(f, yy),
                    arrowprops=dict(arrowstyle="<->", color=col, lw=1.5))
        ax.text((LO + f) / 2, yy + 1.5, f"{abs(LO-f):.0f} MHz", ha="center",
                va="bottom", fontsize=9, color=col, fontweight="bold",
                bbox=dict(fc="white", ec="none", alpha=0.9))

    fx = np.linspace(2250, 3350, 2000)
    rej = -55 * (1 - 1 / (1 + ((fx - (RF_LO + RF_HI) / 2) / 55) ** 8))
    ax.plot(fx, rej + 18, ls="--", lw=1.8, color=S.COLORS[2],
            label="RF 대역통과 필터 (이미지를 막는 유일한 수단)")
    ax.legend(loc="lower left", fontsize=8.8)
    ax.set_ylabel("레벨 (dBm)")
    ax.set_xlabel("입력 주파수 (MHz)")
    ax.set_title("① LO 에서 같은 거리에 있는 두 신호", fontsize=10.5)
    ax.grid(alpha=0.4)

    ax = axes[1]
    ax.set_xlim(320, 380)
    ax.set_ylim(-58, 8)
    # 두 신호는 실제로 같은 주파수에 있다. 보이게 하려고 조금 벌려 그린다.
    _stem(ax, IF - 0.8, -30, "", S.COLORS[0], lw=4.0)
    _stem(ax, IF + 0.8, -30, "", S.ACCENT, lw=4.0)
    ax.text(IF, -24, "둘 다 350 MHz", ha="center", fontsize=9.6,
            fontweight="bold", color=S.INK)
    ax.annotate("원하는 신호 (2450 MHz 에서 옴)", xy=(IF - 0.8, -34),
                xytext=(332, -46), fontsize=9, color=S.COLORS[0],
                fontweight="bold", ha="left",
                arrowprops=dict(arrowstyle="->", color=S.COLORS[0], lw=1.2))
    ax.annotate("이미지 (3150 MHz 에서 옴)", xy=(IF + 0.8, -34),
                xytext=(354, -46), fontsize=9, color=S.ACCENT,
                fontweight="bold", ha="left",
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    ax.text(IF, -8, "실제로는 정확히 같은 주파수라 완전히 겹친다.\n"
                    "IF 필터로는 절대 구별할 수 없다.", ha="center",
            fontsize=9.4, color=S.ACCENT, fontweight="bold",
            bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=1.0))
    ax.text(IF, -55, "(보이게 하려고 좌우로 조금 벌려 그렸다)", ha="center",
            fontsize=8.2, color=S.MUTED)
    ax.set_ylabel("레벨 (dBm)")
    ax.set_xlabel("IF 주파수 (MHz)")
    ax.set_title("② 믹서를 지난 뒤 — 둘이 겹쳐 버렸다", fontsize=10.5)
    ax.grid(alpha=0.4)

    fig.suptitle("그림 M09-2  이미지 주파수 — 왜 RF 필터가 반드시 앞에 있어야 하는가",
                 fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M09", "image")
    return dict(rf=RF, lo=LO, image=IMAGE, sep=IMAGE - RF)


# ══════════════════════════════════════════ M09-3: 스퍼 응답 차트
def spur_responses(lo, if_, mmax=4, nmax=4, fmin=0.0, fmax=6000.0):
    """어떤 입력 주파수가 IF 대역으로 떨어지는가.

    m·f_in ± n·f_LO = ±IF  ->  f_in = (n·LO ± IF) / m
    """
    out = []
    for m in range(1, mmax + 1):
        for n in range(1, nmax + 1):
            for sgn in (+1, -1):
                f = (n * lo + sgn * if_) / m
                if fmin <= f <= fmax:
                    out.append(dict(m=m, n=n, sgn=sgn, f=f, order=m + n))
    return sorted(out, key=lambda r: r["f"])


def m09_spur():
    """스퍼 응답 차트."""
    fig, ax = S.figure(9.6, 5.6)
    rows = spur_responses(LO, IF, 4, 4, 300.0, 6100.0)

    special = {RF: ("원하는 신호", S.COLORS[0], 2.9),
               HALF_IF: ("하프-IF", S.COLORS[1], 4.9),
               IMAGE: ("이미지", S.ACCENT, 2.9)}

    for r in rows:
        col, lw, z = S.MUTED, 1.6, 3
        for fs, (_, c, _h) in special.items():
            if abs(r["f"] - fs) < 0.5:
                col, lw, z = c, 3.6, 6
        ax.plot([r["f"], r["f"]], [0, r["order"]], ls="-", lw=lw, color=col,
                solid_capstyle="butt", zorder=z)
        ax.plot([r["f"]], [r["order"]], "o", ms=4.5, color=col, zorder=z + 1)
        if r["order"] <= 4:
            ax.text(r["f"], r["order"] + 0.14, f"{r['m']}×{r['n']}",
                    ha="center", fontsize=7.4, color=col, zorder=z)

    for f, (name, col, h) in special.items():
        ax.text(f, h, name, ha="center", va="bottom", fontsize=9,
                color=col, fontweight="bold", zorder=9,
                bbox=dict(fc="white", ec=col, alpha=0.97, lw=0.9))

    ax.axvspan(RF_LO, RF_HI, color=S.COLORS[0], alpha=0.16, zorder=1)
    ax.axvspan(5150, 5350, color=S.COLORS[3], alpha=0.18, zorder=1)
    ax.text((RF_LO + RF_HI) / 2, 0.24, "ISM", ha="center", fontsize=8.4,
            color=S.COLORS[0], fontweight="bold")
    ax.text(5250, 0.24, "5 GHz Wi-Fi", ha="center", fontsize=8.4,
            color=S.COLORS[3], fontweight="bold")

    ax.text(340, 9.15,
            f"LO {LO:.0f} MHz · IF {IF:.0f} MHz 일 때\n"
            f"원하는 신호 {RF:.0f} MHz (1×1) · 이미지 {IMAGE:.0f} MHz (1×1)\n"
            f"하프-IF {HALF_IF:.0f} MHz (2×2) — RF 필터로 막기 어렵다",
            fontsize=9, color=S.INK, ha="left", va="top",
            bbox=dict(fc="white", ec=S.GRID, alpha=0.97), zorder=10)

    ax.annotate("1×2 스퍼가 5 GHz Wi-Fi 대역 한복판에 있다\n"
                "= 옆방 공유기가 내 2.4 GHz 수신기를 방해한다",
                xy=(5250, 3.1), xytext=(3250, 6.6), fontsize=9,
                color=S.COLORS[3], fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.COLORS[3], alpha=0.97, lw=1.0),
                arrowprops=dict(arrowstyle="->", color=S.COLORS[3], lw=1.3),
                zorder=10)

    ax.set_xlim(300, 6100)
    ax.set_ylim(0, 9.6)
    ax.set_yticks(range(0, 10))
    ax.set_xlabel("믹서 입력 주파수 (MHz)")
    ax.set_ylabel("차수 m + n  (낮을수록 세게 나온다)")
    ax.set_title("그림 M09-3  스퍼 응답 차트 — 어떤 입력이 IF 로 새어 들어오는가")
    S.save(fig, "M09", "spur")
    return dict(rows=rows, n=len(rows), rf=RF, image=IMAGE, half_if=HALF_IF,
                wifi=[r for r in rows if 5150 <= r["f"] <= 5350])


# ══════════════════════════════════════════ M09-4: 위상잡음과 Leeson
def leeson(f, f0=F0_VCO, q_l=100.0, nf_db=10.0, ps_dbm=0.0, fc=1e5):
    """Leeson 모델의 단측파대 위상잡음 L(f) [배수, dBc/Hz 아님]."""
    nf = 10 ** (nf_db / 10)
    ps = 10 ** (ps_dbm / 10) / 1000
    f_l = f0 / (2 * q_l)
    return (nf * K_B * T0 / ps) * (1 + (f_l / f) ** 2) * (1 + fc / f)


def m09_phasenoise():
    """위상잡음 곡선의 세 영역."""
    fig, ax = S.figure(8.4, 5.2)
    f = np.logspace(2, 8, 2000)
    l_db = 10 * np.log10(leeson(f))
    ax.plot(f, l_db, color=S.COLORS[0], lw=2.6, ls="-")

    f_l = F0_VCO / (2 * 100.0)
    for x, lab, col in ((1e5, f"플리커 코너\n{1e5/1e3:.0f} kHz", S.COLORS[1]),
                        (f_l, f"Leeson 코너\nf0/(2Q_L) = {f_l/1e6:.0f} MHz",
                         S.COLORS[2])):
        ax.axvline(x, color=col, ls=":", lw=1.6)
        ax.text(x * 0.85 if x > 1e6 else x * 1.15, -30, lab, fontsize=8.8,
                color=col, fontweight="bold", va="top",
                ha="right" if x > 1e6 else "left",
                bbox=dict(fc="white", ec="none", alpha=0.9))

    regions = [(3e2, 6e4, "1/f³  (−30 dB/decade)\n소자의 플리커 잡음", S.ACCENT,
                18),
               (2e5, 6e6, "1/f²  (−20 dB/decade)\n공진기의 Q 가 지배",
                S.COLORS[2], 30),
               (2.2e7, 8e7, "바닥 (0 dB/decade)\n열잡음", S.COLORS[1], 16)]
    for a, b, lab, col, dy in regions:
        ya = 10 * np.log10(leeson(np.sqrt(a * b)))
        ax.annotate("", xy=(a, ya + dy), xytext=(b, ya + dy),
                    arrowprops=dict(arrowstyle="<->", color=col, lw=1.6))
        ax.text(np.sqrt(a * b), ya + dy + 4, lab, ha="center", fontsize=8.8,
                color=col, fontweight="bold",
                bbox=dict(fc="white", ec="none", alpha=0.9))

    for off in (1e4, 1e5, 1e6):
        v = 10 * np.log10(leeson(off))
        ax.plot([off], [v], "o", color=S.INK, ms=6, zorder=8)
        ax.annotate(f"{v:.0f} dBc/Hz\n@ {off/1e3:.0f} kHz", xy=(off, v),
                    xytext=(off * 0.30, v - 16), fontsize=8.4, color=S.INK,
                    ha="center",
                    bbox=dict(fc="white", ec=S.GRID, alpha=0.95),
                    arrowprops=dict(arrowstyle="->", color=S.MUTED, lw=1.0))

    ax.set_xscale("log")
    S.hz_ticks(ax, [1e2, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8])
    ax.set_xlabel("반송파로부터의 오프셋 주파수")
    ax.set_ylabel("위상잡음 L(f) (dBc/Hz)")
    ax.set_title("그림 M09-4  위상잡음 곡선의 세 영역 (Leeson 모델, 2.4 GHz VCO)")
    ax.set_ylim(-175, -20)
    ax.grid(which="both", alpha=0.35)
    S.save(fig, "M09", "phasenoise")
    return {f"{o:.0f}": 10 * np.log10(leeson(o))
            for o in (1e3, 1e4, 1e5, 1e6, 1e7)} | dict(
        f_leeson=f_l, floor=10 * np.log10(leeson(1e9)))


# ══════════════════════════════════════════ M09-5: PLL 루프 대역폭
def loop_noise(f, floor_db=-110.0, fc=1e4):
    """PLL 안쪽(기준·검출기·분주기)에서 오는 잡음. 루프 안에서 그대로 나온다."""
    return 10 ** (floor_db / 10) * (1 + fc / f)


def pll_out(f, fbw):
    """1차 근사: 루프 대역 안은 기준 쪽, 밖은 VCO 쪽이 지배."""
    h2 = 1 / (1 + (f / fbw) ** 4)
    return loop_noise(f) * h2 + leeson(f) * (1 - h2)


def pll_jitter_fs(fbw, fmin=1e2, fmax=1e8, n=20000):
    f = np.logspace(np.log10(fmin), np.log10(fmax), n)
    var = 2 * np.trapezoid(pll_out(f, fbw), f)      # rad^2
    return np.sqrt(var) / (2 * np.pi * F0_VCO) * 1e15


def m09_pll():
    """루프 대역폭에는 최적값이 있다."""
    S.setup()
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.6))
    fig.patch.set_facecolor("white")

    f = np.logspace(2, 8, 2000)
    ax = axes[0]
    ax.plot(f, 10 * np.log10(leeson(f)), color=S.COLORS[1], lw=2.0, ls="--",
            label="VCO 혼자 (자유 발진)")
    ax.plot(f, 10 * np.log10(loop_noise(f)), color=S.COLORS[2], lw=2.0,
            ls="-.", label="기준·검출기·분주기 쪽")
    S.emph(ax, f, 10 * np.log10(pll_out(f, 4e4)), color=S.COLORS[0],
           label="PLL 출력 (루프 대역폭 40 kHz)")

    xi = np.argmin(np.abs(10 * np.log10(leeson(f)) - 10 * np.log10(loop_noise(f))))
    ax.plot([f[xi]], [10 * np.log10(leeson(f[xi]))], "o", color=S.ACCENT,
            ms=9, zorder=9)
    ax.annotate(f"두 곡선이 만나는 곳\n{f[xi]/1e3:.0f} kHz\n"
                "= 최적 루프 대역폭",
                xy=(f[xi], 10 * np.log10(leeson(f[xi]))),
                xytext=(4e5, -70), fontsize=9, color=S.ACCENT,
                fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=1.0),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.3))

    ax.set_xscale("log")
    S.hz_ticks(ax, [1e2, 1e4, 1e6, 1e8])
    ax.set_xlabel("오프셋 주파수")
    ax.set_ylabel("위상잡음 L(f) (dBc/Hz)")
    ax.set_title("PLL 출력은 두 잡음의 이어붙이기", fontsize=10.5)
    ax.set_ylim(-175, -20)
    ax.grid(which="both", alpha=0.35)
    ax.legend(fontsize=8.2, loc="lower left", framealpha=0.96)

    ax = axes[1]
    bws = np.logspace(3.5, 6.2, 60)
    jit = np.array([pll_jitter_fs(b) for b in bws])
    ax.plot(bws, jit, color=S.COLORS[0], lw=2.6, ls="-")
    k = int(np.argmin(jit))
    ax.plot([bws[k]], [jit[k]], "o", color=S.ACCENT, ms=10, zorder=9)
    ax.annotate(f"최소 {jit[k]:.0f} fs\n@ {bws[k]/1e3:.0f} kHz",
                xy=(bws[k], jit[k]), xytext=(bws[k] * 2.2, jit[k] + 90),
                fontsize=9.2, color=S.ACCENT, fontweight="bold",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=1.0),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.3))
    ax.text(1.1e4, jit.max() * 0.92, "좁으면\nVCO 잡음이 남는다", fontsize=8.8,
            color=S.MUTED, va="top")
    ax.text(7e5, jit.max() * 0.92, "넓으면\n기준 쪽 잡음이 새어 나온다",
            fontsize=8.8, color=S.MUTED, va="top", ha="right")
    ax.set_xscale("log")
    S.hz_ticks(ax, [1e4, 1e5, 1e6])
    ax.set_xlabel("루프 대역폭")
    ax.set_ylabel("적분 지터, 100 Hz~100 MHz (fs)")
    ax.set_title("그래서 루프 대역폭에는 최적값이 있다", fontsize=10.5)
    ax.grid(which="both", alpha=0.35)

    fig.suptitle("그림 M09-5  PLL 루프 대역폭 — 무엇을 얻고 무엇을 잃는가",
                 fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M09", "pll")
    return dict(cross_hz=f[xi], best_bw=bws[k], best_jitter=jit[k],
                j10k=pll_jitter_fs(1e4), j1m=pll_jitter_fs(1e6))


# ══════════════════════════════════════════ M09-6: 상호혼합
def m09_reciprocal():
    """상호혼합 — LO 의 위상잡음이 간섭을 잡음 담요로 바꿔 덮어씌운다."""
    S.setup()
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.8))
    fig.patch.set_facecolor("white")

    P_INT = -30.0          # 간섭 세기 [dBm]
    OFF = 5.0              # 간섭까지의 거리 [MHz]
    P_SIG = -100.0         # 원하는 신호 [dBm]
    BW = 1e6               # 채널 대역폭 [Hz]
    NF = 5.0
    floor = -174.0 + 10 * np.log10(BW) + NF

    def skirt_dbm(delta_mhz, l_at_5mhz):
        """간섭 위에 얹힌 LO 위상잡음이 채널 대역폭 안에 만드는 전력."""
        d = np.maximum(np.abs(delta_mhz), 0.05)
        l = l_at_5mhz - 20 * np.log10(d / OFF)     # 1/f² 기울기
        return P_INT + l + 10 * np.log10(BW)

    # ── 왼쪽: 간섭에 얹힌 잡음 담요가 원하는 채널을 덮는다 ──
    ax = axes[0]
    x = np.linspace(-4, 14, 3000)
    for l5, name, col, ls in ((-130.0, "값싼 합성기", S.ACCENT, "-"),
                              (-145.0, "좋은 합성기", S.COLORS[2], "--")):
        ax.plot(x, skirt_dbm(x - OFF, l5), lw=2.2, ls=ls, color=col,
                label=f"{name} (LO 위상잡음 {l5:.0f} dBc/Hz @ {OFF:.0f} MHz)")

    ax.plot([OFF, OFF], [-135, P_INT], lw=4.0, color=S.INK, zorder=6)
    ax.text(OFF, P_INT + 2.5, f"간섭 {P_INT:.0f} dBm", ha="center", fontsize=9.2,
            color=S.INK, fontweight="bold")
    ax.plot([0, 0], [-135, P_SIG], lw=4.0, color=S.COLORS[0], zorder=6)
    ax.plot([0], [P_SIG], "o", color=S.COLORS[0], ms=8, zorder=7)
    ax.annotate(f"원하는 신호\n{P_SIG:.0f} dBm", xy=(0, P_SIG),
                xytext=(-3.7, -70), fontsize=9.2, color=S.COLORS[0],
                fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.COLORS[0], alpha=0.97, lw=0.9),
                arrowprops=dict(arrowstyle="->", color=S.COLORS[0], lw=1.2))

    ax.axhline(floor, color=S.MUTED, ls=":", lw=1.8)
    ax.text(-3.7, floor + 1.5, f"열잡음 바닥 {floor:.0f} dBm", ha="left",
            fontsize=8.8, color=S.MUTED)

    v = skirt_dbm(np.array([0.0 - OFF]), -130.0)[0]
    ax.plot([0], [v], "o", color=S.ACCENT, ms=9, zorder=8)
    ax.annotate(f"값싼 합성기라면 원하는 채널 안에\n{v:.0f} dBm 의 잡음이 깔린다.\n"
                f"신호도 {P_SIG:.0f} dBm 이므로 SNR = 0 dB — 못 받는다.",
                xy=(0.15, v), xytext=(6.6, -48), fontsize=9, color=S.ACCENT,
                fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=1.0),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.3))

    ax.set_xlim(-4, 14)
    ax.set_ylim(-135, -18)
    ax.set_xlabel("원하는 채널로부터의 거리 (MHz)")
    ax.set_ylabel(f"채널 대역폭 {BW/1e6:.0f} MHz 안의 전력 (dBm)")
    ax.set_title("① 간섭이 LO 의 위상잡음을 그대로 뒤집어쓴다", fontsize=10.5)
    ax.legend(fontsize=8.0, loc="lower right", framealpha=0.96)
    ax.grid(alpha=0.4)

    # ── 오른쪽: 채널 안 잡음 비교 ──
    ax = axes[1]
    names, vals, cols = [], [], []
    for l5, name, col in ((-130.0, "값싼 합성기\n−130 dBc/Hz", S.ACCENT),
                          (-145.0, "좋은 합성기\n−145 dBc/Hz", S.COLORS[2])):
        names.append(name)
        vals.append(P_INT + l5 + 10 * np.log10(BW))
        cols.append(col)
    names.append("열잡음만 있었다면")
    vals.append(floor)
    cols.append(S.MUTED)

    y = np.arange(len(names))
    ax.barh(y, [v + 130 for v in vals], left=-130, color=cols, alpha=0.85,
            height=0.55)
    for yy, v, c in zip(y, vals, cols):
        ax.text(v + 0.8, yy, f"{v:.0f} dBm", va="center", fontsize=9.6,
                color=c, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8.8)
    ax.invert_yaxis()
    ax.axvline(floor, color=S.INK, ls=":", lw=1.8)
    ax.set_xlim(-122, -92)
    ax.set_xlabel("원하는 채널 안에 들어온 잡음 전력 (dBm)")
    ax.set_title("② 합성기를 15 dB 개선하면 잡음도 15 dB 내려간다",
                 fontsize=10.5)
    ax.grid(axis="x", alpha=0.4)

    fig.suptitle("그림 M09-6  상호혼합 — LO 가 나쁘면 간섭이 잡음으로 바뀐다",
                 fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M09", "reciprocal")
    return dict(bad=P_INT - 130.0 + 10 * np.log10(BW),
                good=P_INT - 145.0 + 10 * np.log10(BW),
                floor=floor, sig=P_SIG)


def image_rejection_db(amp_db, ph_deg):
    """진폭 오차 amp_db [dB], 위상 오차 ph_deg [도] 일 때의 이미지 억압 [dB]."""
    a = 10 ** (np.asarray(amp_db) / 20)
    t = np.deg2rad(np.asarray(ph_deg))
    return 10 * np.log10((1 + 2 * a * np.cos(t) + a ** 2)
                         / (1 - 2 * a * np.cos(t) + a ** 2))


def m09_imagerej():
    """I/Q 믹서의 이미지 억압은 정합 오차가 정한다."""
    fig, ax = S.figure(7.8, 4.8)
    ph = np.linspace(0.05, 12, 600)
    for amp, ls in ((0.0, "-"), (0.1, "--"), (0.3, "-."),
                    (0.5, (0, (5, 1, 1, 1)))):
        ax.plot(ph, image_rejection_db(amp, ph), ls=ls, lw=2.0,
                label=f"진폭 오차 {amp:.1f} dB")

    for y, lab in ((20, "보통 수준의 I/Q 믹서"), (30, "잘 만든 I/Q 믹서"),
                   (40, "보정을 넣어야 도달")):
        ax.axhline(y, color=S.MUTED, ls=":", lw=1.2)
        ax.text(0.15, y + 0.7, lab, ha="left", fontsize=8.6, color=S.MUTED)

    p_ok = 0.5
    a_ok = 0.1
    v = image_rejection_db(a_ok, p_ok)
    ax.plot([p_ok], [v], "o", color=S.ACCENT, ms=9, zorder=9)
    ax.annotate(f"위상 {p_ok}도 · 진폭 {a_ok} dB 까지 맞추면\n"
                f"이미지 억압 {v:.0f} dB",
                xy=(p_ok, v), xytext=(1.6, 44), fontsize=9.2, color=S.ACCENT,
                fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=1.0),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.3))
    v10 = image_rejection_db(0.5, 10.0)
    ax.annotate(f"위상 10도 · 진폭 0.5 dB 면 {v10:.0f} dB 밖에 안 된다",
                xy=(10, v10), xytext=(4.2, 13.5), fontsize=9, color=S.INK,
                ha="left",
                bbox=dict(fc="white", ec=S.GRID, alpha=0.97),
                arrowprops=dict(arrowstyle="->", color=S.MUTED, lw=1.1))

    ax.set_xlabel("두 경로의 위상 오차 (도)")
    ax.set_ylabel("이미지 억압 (dB)")
    ax.set_title("그림 M09-8  I/Q 믹서의 이미지 억압은 정합 오차가 정한다")
    ax.set_xlim(0, 12)
    ax.set_ylim(8, 52)
    ax.legend(fontsize=9, loc="upper right")
    S.save(fig, "M09", "imagerej")
    return dict(ideal_1deg=image_rejection_db(0.0, 1.0),
                p05a01=v, p10a05=v10,
                p2a03=image_rejection_db(0.3, 2.0))


if __name__ == "__main__":
    cv = m09_conversion()
    im = m09_image()
    sp = m09_spur()
    pn = m09_phasenoise()
    pl = m09_pll()
    rc = m09_reciprocal()
    ir = m09_imagerej()

    print("\n[본문에 인용할 계산값]")
    print(f"  주파수 계획: RF {RF:.0f}, LO {LO:.0f}, IF {IF:.0f}, "
          f"이미지 {IMAGE:.0f}, 하프-IF {HALF_IF:.0f} MHz")
    print(f"  합 주파수 {cv['sum_']:.0f} MHz, 이미지와 RF 의 간격 {im['sep']:.0f} MHz")
    print(f"  스퍼 응답 개수 (m,n <= 4, 0.3~6.1 GHz): {sp['n']}")
    print("  5 GHz Wi-Fi 대역에 떨어지는 스퍼:",
          [f"{r['m']}x{r['n']} @ {r['f']:.0f} MHz" for r in sp["wifi"]])
    print("  위상잡음(2.4 GHz VCO):",
          {k: f"{v:.1f}" for k, v in pn.items() if k.isdigit()})
    print(f"    Leeson 코너 {pn['f_leeson']/1e6:.0f} MHz, "
          f"바닥 {pn['floor']:.1f} dBc/Hz")
    print(f"  PLL: 곡선 교차 {pl['cross_hz']/1e3:.0f} kHz, "
          f"최적 루프 대역폭 {pl['best_bw']/1e3:.0f} kHz "
          f"(지터 {pl['best_jitter']:.0f} fs)")
    print(f"    루프 10 kHz -> {pl['j10k']:.0f} fs, "
          f"1 MHz -> {pl['j1m']:.0f} fs")
    print(f"  이미지 억압: 위상 0.5도·진폭 0.1 dB -> {ir['p05a01']:.1f} dB, "
          f"위상 2도·진폭 0.3 dB -> {ir['p2a03']:.1f} dB, "
          f"위상 10도·진폭 0.5 dB -> {ir['p10a05']:.1f} dB")
    print(f"  상호혼합: 값싼 LO {rc['bad']:.0f} dBm, 좋은 LO {rc['good']:.0f} dBm, "
          f"열잡음 바닥 {rc['floor']:.0f} dBm")

    print("\n[자체 검산]")
    ok = []
    ok.append(("LO − RF = IF", abs((LO - RF) - IF) < 1e-9))
    ok.append(("이미지 = LO + IF = RF + 2·IF",
               abs(IMAGE - (RF + 2 * IF)) < 1e-9))
    ok.append(("하프-IF 스퍼(2×2)가 RF + IF/2",
               any(r["m"] == 2 and r["n"] == 2 and abs(r["f"] - HALF_IF) < 0.5
                   for r in sp["rows"])))
    ok.append(("1×1 −IF 응답이 곧 원하는 RF",
               any(r["m"] == 1 and r["n"] == 1 and r["sgn"] < 0
                   and abs(r["f"] - RF) < 0.5 for r in sp["rows"])))
    ok.append(("1×1 +IF 응답이 곧 이미지",
               any(r["m"] == 1 and r["n"] == 1 and r["sgn"] > 0
                   and abs(r["f"] - IMAGE) < 0.5 for r in sp["rows"])))
    ok.append(("5 GHz Wi-Fi 대역 스퍼가 존재", len(sp["wifi"]) > 0))
    s1 = 10 * np.log10(leeson(1e3) / leeson(1e4))
    ok.append(("1/f³ 영역의 기울기가 −30 dB/decade", abs(s1 - 30) < 1.0))
    s2 = 10 * np.log10(leeson(2e5) / leeson(2e6))
    ok.append(("1/f² 영역의 기울기가 −20 dB/decade", abs(s2 - 20) < 1.5))
    s3 = 10 * np.log10(leeson(3e7) / leeson(3e8))
    ok.append(("바닥 영역의 기울기가 0 dB/decade", abs(s3) < 1.0))
    ok.append(("최적 루프 대역폭이 두 곡선 교차점 부근",
               0.4 < pl["best_bw"] / pl["cross_hz"] < 3.0))
    ok.append(("최적점이 양쪽보다 지터가 작다",
               pl["best_jitter"] < pl["j10k"] and pl["best_jitter"] < pl["j1m"]))
    ok.append(("이미지 억압 공식이 문헌값과 일치 (0.5 dB·10도 -> 20.7 dB)",
               abs(image_rejection_db(0.5, 10.0) - 20.7) < 0.2))
    ok.append(("오차가 0 이면 이미지 억압이 무한대로 간다",
               image_rejection_db(0.0, 0.001) > 90))
    ok.append(("값싼 LO 의 상호혼합 잡음이 열잡음 바닥보다 큼",
               rc["bad"] > rc["floor"]))
    ok.append(("좋은 LO 는 열잡음 바닥보다 작음", rc["good"] < rc["floor"]))
    for name, v in ok:
        print(f"  [{'OK ' if v else 'FAIL'}] {name}")
    print(f"\n{'전부 통과' if all(v for _, v in ok) else '검산 실패 항목 있음'}")
