#!/usr/bin/env python3
"""
Part 0 + Part I (M00~M03) 데이터 그림 생성기
============================================

    python3 scripts/gen_fig_part1.py

출력: assets/M00/*.svg, assets/M01/*.svg, assets/M02/*.svg, assets/M03/*.svg

모든 그림은 rf_style 규약(한글 폰트, 색각 대응, 벡터 경로 변환)을 따른다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import rf_style as S

C0 = 299_792_458.0          # 진공에서의 빛의 속도 [m/s]
K_B = 1.380649e-23          # 볼츠만 상수 [J/K]  (SI 2019 정의값)
T0 = 290.0                  # 잡음지수 기준 온도 [K]


# ══════════════════════════════════════════════════════════ M00
def m00_spectrum_map():
    """주파수 대역 지도: 명칭과 실제 서비스를 한 장에."""
    fig, ax = S.figure(9.2, 4.6)

    # (이름, 시작 Hz, 끝 Hz, 층)
    itu = [("HF\n단파", 3e6, 30e6), ("VHF\n초단파", 30e6, 300e6),
           ("UHF\n극초단파", 300e6, 3e9), ("SHF\n마이크로파", 3e9, 30e9),
           ("EHF\n밀리미터파", 30e9, 300e9)]
    ieee = [("L", 1e9, 2e9), ("S", 2e9, 4e9), ("C", 4e9, 8e9),
            ("X", 8e9, 12e9), ("Ku", 12e9, 18e9), ("K", 18e9, 27e9),
            ("Ka", 27e9, 40e9)]
    # 실제 서비스는 대역이 서로 겹치므로(Wi-Fi는 셀룰러 FR1 범위 안에 있다)
    # 한 줄에 그리면 글자가 뭉개진다. 소단(lane)으로 나눠 쌓는다.
    svc_lanes = [
        [("FM 라디오 88-108 MHz", 88e6, 108e6),
         ("셀룰러 FR1  0.4-7.1 GHz", 4.1e8, 7.125e9),
         ("5G FR2  24-52 GHz", 24.25e9, 52.6e9)],
        [("Wi-Fi 2.4 GHz", 2.4e9, 2.4835e9),
         ("Wi-Fi 5 GHz", 5.15e9, 5.85e9)],
    ]

    def band(rows, y, h, color, fs=8.5, label_inside=True):
        for i, (name, f1, f2) in enumerate(rows):
            ax.add_patch(Rectangle((np.log10(f1), y), np.log10(f2) - np.log10(f1),
                                   h, facecolor=color, edgecolor=S.INK, lw=0.9,
                                   alpha=0.30 + 0.12 * (i % 2)))
            if label_inside:
                ax.text((np.log10(f1) + np.log10(f2)) / 2, y + h / 2, name,
                        ha="center", va="center", fontsize=fs, color=S.INK)

    band(itu, 2.45, 0.62, S.COLORS[0])
    band(ieee, 1.70, 0.55, S.COLORS[2])
    band(svc_lanes[0], 0.92, 0.48, S.COLORS[1], fs=7.6)
    band(svc_lanes[1], 0.36, 0.48, S.COLORS[1], fs=7.6)

    ax.text(np.log10(2e6), 2.72, "ITU 대역 명칭", fontsize=9.5,
            fontweight="bold", ha="right")
    ax.text(np.log10(2e6), 1.92, "IEEE 레이더 대역", fontsize=9.5,
            fontweight="bold", ha="right")
    ax.text(np.log10(2e6), 0.86, "실제 서비스", fontsize=9.5,
            fontweight="bold", ha="right")

    ax.set_xlim(np.log10(1e6), np.log10(3e11))
    ax.set_ylim(0, 3.25)
    ticks = [1e6, 1e7, 1e8, 1e9, 1e10, 1e11]
    ax.set_xticks([np.log10(t) for t in ticks])
    ax.set_xticklabels(["1 MHz", "10 MHz", "100 MHz", "1 GHz", "10 GHz", "100 GHz"])
    ax.set_yticks([])
    ax.set_xlabel("주파수 (로그 눈금)")
    ax.set_title("그림 M00-1  주파수 대역 지도")
    ax.grid(axis="x", alpha=0.5)
    for s in ("left", "right", "top"):
        ax.spines[s].set_visible(False)
    S.save(fig, "M00", "spectrum_map")


def m00_wavelength_vs_size():
    """파장과 회로 크기 — 언제부터 '선'이 '회로'가 되는가."""
    fig, ax = S.figure(7.6, 4.6)
    f = np.logspace(6, 11, 400)
    lam = C0 / f

    ax.loglog(f, lam * 100, color=S.COLORS[0], lw=2.2, label="파장 λ")
    ax.loglog(f, lam * 100 / 10, color=S.COLORS[1], ls="--", lw=2.0,
              label="λ/10 (분포정수 경계)")

    ax.fill_between(f, 1e-3, lam * 100 / 10, color=S.COLORS[2], alpha=0.10)
    ax.text(1.4e6, 2.5e-2, "이 아래 = 집중정수 소자\n(보통의 회로 이론이 통함)",
            fontsize=9, color=S.INK)
    ax.text(6e9, 6e3, "이 위 = 분포정수\n(전송선로 이론 필요)",
            fontsize=9, color=S.INK, ha="center")

    # 주석을 서로 다른 방향으로 빼내 겹치지 않게 한다
    marks = [(100e6, "FM 100 MHz", (0.10, 0.16)),
             (2.4e9, "Wi-Fi 2.4 GHz", (0.13, 0.055)),
             (28e9, "5G 밀리미터파 28 GHz", (0.10, 0.018))]
    for fm, name, (fx, fy) in marks:
        lm = C0 / fm * 100
        ax.plot([fm], [lm], "o", color=S.ACCENT, ms=7, zorder=8)
        ax.annotate(f"{name}\nλ = {lm:.1f} cm,  λ/10 = {lm/10:.2f} cm",
                    xy=(fm, lm), xytext=(fm * fx, lm * fy), fontsize=8.5,
                    color=S.ACCENT, ha="left", va="top", zorder=9,
                    bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.2),
                    arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.1))

    ax.axhline(1.0, color=S.MUTED, lw=1.1, ls=":")
    ax.text(1.2e6, 1.15, "1 cm — 보통의 PCB 배선 길이", fontsize=8.5, color=S.MUTED)

    ax.set_xlabel("주파수 (Hz)")
    ax.set_ylabel("길이 (cm)")
    ax.set_title("그림 M00-2  파장과 회로 크기")
    ax.set_ylim(1e-2, 1e4)
    ax.legend(loc="upper right")
    S.plain_log(ax, "y")
    S.hz_ticks(ax, [1e6, 1e7, 1e8, 1e9, 1e10, 1e11])
    S.save(fig, "M00", "wavelength_vs_size")


def m00_voltage_along_wire():
    """같은 순간, 전선 위 위치별 전압 — 저주파 vs 고주파."""
    fig, axes = plt.subplots(2, 1, figsize=(7.6, 4.8), sharex=True)
    S.setup()
    fig.patch.set_facecolor("white")
    x = np.linspace(0, 10, 500)          # cm

    for ax, (f, name, col) in zip(axes, [(1e6, "1 MHz — λ = 300 m", S.COLORS[0]),
                                          (2.4e9, "2.4 GHz — λ = 12.5 cm", S.COLORS[1])]):
        lam_cm = C0 / f * 100
        v = np.cos(2 * np.pi * x / lam_cm)
        ax.plot(x, v, color=col, lw=2.2)
        ax.axhline(0, color=S.MUTED, lw=0.8)
        ax.set_ylim(-1.35, 1.35)
        ax.set_ylabel("전압 (정규화)")
        ax.set_title(name, fontsize=10.5, loc="left")
        ax.grid(alpha=0.5)
        v0, v10 = v[0], v[-1]
        ax.plot([0, 10], [v0, v10], "o", color=S.ACCENT, ms=7, zorder=6)
        ax.annotate(f"양 끝 전압 차이: {abs(v0 - v10)*100:.0f} %",
                    xy=(5, -1.05), ha="center", fontsize=9,
                    color=S.ACCENT, fontweight="bold")

    axes[1].set_xlabel("전선 위 위치 (cm)")
    fig.suptitle("그림 M00-3  10 cm 전선 위의 순간 전압 분포", fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M00", "voltage_along_wire")


# ══════════════════════════════════════════════════════════ M01
def m01_linear_vs_db():
    """왜 로그를 쓰는가 — 같은 데이터, 두 눈금."""
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.9))
    S.setup()
    fig.patch.set_facecolor("white")

    stage = ["안테나", "케이블", "LNA", "필터", "믹서", "IF 증폭"]
    p_dbm = [-80, -83, -63, -65, -72, -42]
    p_mw = [10 ** (p / 10) for p in p_dbm]

    axes[0].plot(range(len(stage)), p_mw, "o-", color=S.COLORS[0], lw=2)
    axes[0].set_ylabel("전력 (mW)")
    axes[0].set_title("선형 눈금 — 아무것도 안 보인다", fontsize=10.5)
    axes[0].set_xticks(range(len(stage)))
    axes[0].set_xticklabels(stage, rotation=40, ha="right", fontsize=9)

    axes[1].plot(range(len(stage)), p_dbm, "s-", color=S.COLORS[1], lw=2)
    axes[1].set_ylabel("전력 (dBm)")
    axes[1].set_title("dB 눈금 — 각 단의 기여가 보인다", fontsize=10.5)
    axes[1].set_xticks(range(len(stage)))
    axes[1].set_xticklabels(stage, rotation=40, ha="right", fontsize=9)
    for i in range(1, len(stage)):
        d = p_dbm[i] - p_dbm[i - 1]
        axes[1].annotate(f"{d:+d}", xy=(i - 0.5, (p_dbm[i] + p_dbm[i - 1]) / 2 + 3),
                         ha="center", fontsize=8.5, color=S.ACCENT,
                         fontweight="bold")
    for ax in axes:
        ax.grid(alpha=0.5)
    fig.suptitle("그림 M01-1  같은 수신 체인을 두 눈금으로 본 것", fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M01", "linear_vs_db")


def m01_db_ratio():
    """dB ↔ 배율 환산 곡선과 외울 값."""
    fig, ax = S.figure(7.4, 4.3)
    db = np.linspace(-30, 30, 400)
    ax.semilogy(db, 10 ** (db / 10), color=S.COLORS[0], lw=2.2, label="전력비 (10 log)")
    ax.semilogy(db, 10 ** (db / 20), color=S.COLORS[1], ls="--", lw=2.0,
                label="전압비 (20 log)")

    for d, r, txt, off in [(3, 2, "3 dB = 2배", (-12, 3.0)),
                           (10, 10, "10 dB = 10배", (-13, 3.0)),
                           (20, 100, "20 dB = 100배", (-14, 3.0)),
                           (-3, 0.5, "-3 dB = 1/2배", (1.5, 0.34)),
                           (-10, 0.1, "-10 dB = 1/10배", (1.5, 0.34))]:
        ax.plot([d], [r], "o", color=S.ACCENT, ms=6.5, zorder=8)
        ax.annotate(txt, xy=(d, r), xytext=(d + off[0], r * off[1]),
                    fontsize=8.5, color=S.ACCENT, zorder=9,
                    bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.0))

    ax.axhline(1, color=S.MUTED, lw=1.0, ls=":")
    ax.set_xlabel("dB")
    ax.set_ylabel("배율 (선형)")
    ax.set_title("그림 M01-2  dB와 배율의 관계")
    ax.legend(loc="upper left")
    S.plain_log(ax, "y")
    S.save(fig, "M01", "db_ratio")


def m01_level_diagram():
    """레벨 다이어그램 — RF 엔지니어가 가장 자주 그리는 그림."""
    fig, ax = S.figure(8.4, 4.4)
    stage = ["안테나\n출력", "케이블\n-3 dB", "LNA\n+20 dB", "필터\n-2 dB",
             "믹서\n-7 dB", "IF 증폭\n+30 dB"]
    gain = [0, -3, +20, -2, -7, +30]
    sig = np.cumsum([-80] + gain[1:])
    nf_floor = np.cumsum([-174 + 10 * np.log10(20e6)] + gain[1:]) + 2.0

    xs = np.arange(len(stage))
    ax.step(xs, sig, where="mid", color=S.COLORS[0], lw=2.4, label="신호 레벨")
    ax.step(xs, nf_floor, where="mid", color=S.COLORS[1], ls="--", lw=2.0,
            label="잡음 바닥 (각 단이 잡음을 더하지 않는다는 이상적 가정)")
    ax.fill_between(xs, nf_floor, sig, step="mid", color=S.COLORS[2], alpha=0.15)

    mid = len(stage) // 2
    ax.annotate("이 간격이 SNR(신호대잡음비)",
                xy=(mid, (sig[mid] + nf_floor[mid]) / 2), fontsize=9.5,
                ha="center", color=S.INK, fontweight="bold",
                bbox=dict(fc="white", ec=S.GRID, alpha=0.92))
    ax.annotate("실제로는 각 단이 잡음을 더해\n이 간격이 조금씩 좁아진다 (→ M08, M12)",
                xy=(len(stage) - 1.1, nf_floor[0] - 6), fontsize=8.5,
                ha="right", va="top", color=S.ACCENT,
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.92, lw=0.8))

    ax.set_xticks(xs)
    ax.set_xticklabels(stage, fontsize=8.5)
    ax.set_ylabel("전력 (dBm)")
    ax.set_title("그림 M01-3  수신 체인 레벨 다이어그램 (대역폭 20 MHz)")
    ax.legend(loc="upper left")
    S.save(fig, "M01", "level_diagram")


def m01_ktb():
    """열잡음 바닥은 대역폭이 결정한다."""
    fig, ax = S.figure(7.4, 4.3)
    bw = np.logspace(0, 9, 400)
    n = 10 * np.log10(K_B * T0 * bw / 1e-3)
    ax.semilogx(bw, n, color=S.COLORS[0], lw=2.3)

    # 주석을 번갈아 위/아래로 놓아 겹치지 않게 한다
    for b, name, dy, va in [(1, "1 Hz", -7, "top"),
                            (1e3, "1 kHz", 11, "bottom"),
                            (1e6, "1 MHz", -9, "top"),
                            (20e6, "20 MHz (LTE/5G 채널)", 13, "bottom"),
                            (1e9, "1 GHz", -9, "top")]:
        y = 10 * np.log10(K_B * T0 * b / 1e-3)
        ax.plot([b], [y], "o", color=S.ACCENT, ms=6.5, zorder=8)
        ax.annotate(f"{name}\n{y:.0f} dBm", xy=(b, y), xytext=(b, y + dy),
                    ha="center", va=va, fontsize=8.5, color=S.ACCENT, zorder=9,
                    bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.0))

    ax.axhline(-174, color=S.MUTED, ls=":", lw=1.2)
    ax.text(2e3, -178.5, "-174 dBm/Hz = 상온(290 K)에서 1 Hz 대역폭의 절대 바닥",
            fontsize=9, color=S.MUTED, ha="left", va="bottom")
    ax.set_xlabel("대역폭 (Hz)")
    ax.set_ylabel("열잡음 전력 (dBm)")
    ax.set_title("그림 M01-4  열잡음 전력 = kTB  (T = 290 K)")
    ax.set_ylim(-182, -78)
    ax.set_xlim(0.5, 3e9)
    S.hz_ticks(ax, [1, 1e3, 1e6, 1e9])
    S.save(fig, "M01", "ktb_vs_bw")


def m01_sensitivity_waterfall():
    """감도가 어떻게 만들어지는가 — 폭포 차트."""
    fig, ax = S.figure(7.6, 4.3)
    items = ["열잡음\n-174 dBm/Hz", "대역폭\n+73 dB\n(20 MHz)",
             "잡음지수\n+4 dB", "요구 SNR\n+10 dB"]
    vals = [-174, 10 * np.log10(20e6), 4, 10]
    cum = np.cumsum(vals)
    base = np.concatenate([[0], cum[:-1]])

    for i, (v, b) in enumerate(zip(vals, base)):
        col = S.COLORS[0] if i == 0 else S.COLORS[1]
        ax.bar(i, v, bottom=b if i else 0, color=col, alpha=0.75,
               edgecolor=S.INK, lw=1.0, width=0.62)
        label = f"{v:+.0f} dB" if i else f"{v:.0f} dBm"
        # 막대가 얇으면 글자가 밖으로 넘치므로 막대 옆에 검은 글씨로 붙인다
        if abs(v) >= 25:
            ax.annotate(label, xy=(i, (b + v / 2) if i else v / 2),
                        ha="center", va="center", fontsize=9.5,
                        fontweight="bold", color="white")
        else:
            ax.annotate(label, xy=(i + 0.36, b + v / 2), ha="left",
                        va="center", fontsize=9, fontweight="bold",
                        color=S.INK)

    ax.bar(len(items), cum[-1], color=S.COLORS[2], alpha=0.85,
           edgecolor=S.INK, lw=1.2, width=0.62)
    ax.annotate(f"감도\n{cum[-1]:.0f} dBm", xy=(len(items), cum[-1] / 2),
                ha="center", va="center", fontsize=9.5, fontweight="bold",
                color="white")

    ax.set_xticks(range(len(items) + 1))
    ax.set_xticklabels(items + ["= 수신 감도"], fontsize=8.5)
    ax.set_ylabel("전력 (dBm)")
    ax.set_title("그림 M01-5  수신 감도는 이렇게 만들어진다")
    ax.axhline(0, color=S.INK, lw=1.0)
    ax.set_ylim(-185, 22)
    ax.set_xlim(-0.6, len(items) + 0.6)
    S.save(fig, "M01", "sensitivity_waterfall")


# ══════════════════════════════════════════════════════════ M02
def m02_standing_wave():
    """정재파 — 여러 시점의 스냅샷과 포락선."""
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.6), sharey=True)
    S.setup()
    fig.patch.set_facecolor("white")
    z = np.linspace(0, 1.0, 500)          # 파장 단위 위치
    beta = 2 * np.pi

    for ax, (gam, name) in zip(axes, [(0.0, "Γ = 0  (완전 정합)\nVSWR = 1"),
                                       (0.5, "Γ = 0.5\nVSWR = 3"),
                                       (1.0, "Γ = 1  (개방/단락)\nVSWR = ∞")]):
        env_hi = 1 + abs(gam)
        env_lo = abs(1 - abs(gam))
        for k, ph in enumerate(np.linspace(0, np.pi, 5)):
            v = np.real((np.exp(-1j * beta * z) + gam * np.exp(1j * beta * z))
                        * np.exp(1j * ph))
            # ls 를 명시하지 않으면 rcParams 의 선모양 순환이 적용되어
            # 같은 뜻의 선들이 제각각 다른 모양으로 그려진다.
            ax.plot(z, v, color=S.COLORS[0], ls="-", lw=1.0,
                    alpha=0.25 + 0.11 * k)
        env = np.abs(np.exp(-1j * beta * z) + gam * np.exp(1j * beta * z))
        ax.plot(z, env, color=S.ACCENT, ls="-", lw=2.2)
        ax.plot(z, -env, color=S.ACCENT, ls="-", lw=2.2)
        ax.set_title(name, fontsize=10)
        ax.set_xlabel("위치 (파장 단위)")
        ax.grid(alpha=0.5)
        ax.set_ylim(-2.4, 2.4)
        if gam > 0:
            ax.annotate("", xy=(0.25, env_hi), xytext=(0.25, env_lo),
                        arrowprops=dict(arrowstyle="<->", color=S.INK, lw=1.3))
            note = (f"VSWR = {env_hi:.1f} / {env_lo:.1f} = {env_hi/env_lo:.0f}"
                    if env_lo > 1e-9 else "VSWR = 무한대\n(최솟값이 0)")
            ax.text(0.30, (env_hi + env_lo) / 2, note, fontsize=8.5,
                    va="center", bbox=dict(fc="white", ec=S.GRID, alpha=0.92))

    axes[0].set_ylabel("전압 (정규화)")
    fig.suptitle("그림 M02-3  전송선 위의 정재파 — 얇은 선은 여러 순간, 굵은 선은 포락선",
                 fontweight="bold", fontsize=11)
    fig.tight_layout()
    S.save(fig, "M02", "standing_wave")


def m02_gamma_vswr_rl():
    """Γ ↔ VSWR ↔ 반사손실 ↔ 반사 전력, 한 장에."""
    fig, ax1 = S.figure(7.6, 4.4)
    g = np.linspace(0.001, 0.9, 500)
    vswr = (1 + g) / (1 - g)
    rl = -20 * np.log10(g)

    ax1.plot(g, vswr, color=S.COLORS[0], lw=2.3, label="VSWR (왼쪽 축)")
    ax1.set_xlabel("반사계수 크기 |Γ|")
    ax1.set_ylabel("VSWR", color=S.COLORS[0])
    ax1.set_ylim(1, 10)
    ax1.tick_params(axis="y", labelcolor=S.COLORS[0])

    ax2 = ax1.twinx()
    ax2.plot(g, rl, color=S.COLORS[1], ls="--", lw=2.1, label="반사손실 (오른쪽 축)")
    ax2.set_ylabel("반사손실 (dB)", color=S.COLORS[1])
    ax2.set_ylim(0, 40)
    ax2.tick_params(axis="y", labelcolor=S.COLORS[1])
    ax2.grid(False)

    for v, (dx, dy) in [(1.5, (0.05, 1.5)), (2.0, (0.05, 2.1)),
                        (3.0, (0.05, 2.4))]:
        gg = (v - 1) / (v + 1)
        ax1.plot([gg], [v], "o", color=S.ACCENT, ms=7, zorder=8)
        ax1.annotate(f"VSWR {v}\n|Γ| = {gg:.2f}\nRL = {-20*np.log10(gg):.1f} dB\n"
                     f"반사 전력 {gg**2*100:.0f} %",
                     xy=(gg, v), xytext=(gg + dx, v + dy), fontsize=8,
                     color=S.ACCENT, zorder=9,
                     bbox=dict(fc="white", ec=S.ACCENT, alpha=0.92, lw=0.7),
                     arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.0))

    ax1.set_title("그림 M02-4  Γ · VSWR · 반사손실은 같은 것의 세 얼굴")
    S.save(fig, "M02", "gamma_vswr_rl")


def m02_coax_tradeoff():
    """왜 50 Ω인가 — 세 최적점이 서로 다르다."""
    fig, ax = S.figure(7.8, 4.5)
    k = np.linspace(1.05, 12, 800)          # 외경/내경 비
    z0 = 59.9585 * np.log(k)                # 공기 유전체 동축선

    atten = (k + 1) / np.log(k)             # 도체 손실 ∝ (k+1)/ln k  (외경 고정)
    power = np.log(k) / k ** 2              # 최대 전력 ∝ ln k / k²
    volt = np.log(k) / k                    # 최대 내전압 ∝ ln k / k

    ax.plot(z0, atten / atten.min(), color=S.COLORS[0], lw=2.2,
            label="감쇠 (낮을수록 좋음)")
    ax.plot(z0, power.max() / power.clip(1e-9), color=S.COLORS[1], ls="--",
            lw=2.1, label="전력 한계의 역수 (낮을수록 좋음)")
    ax.plot(z0, volt.max() / volt.clip(1e-9), color=S.COLORS[2], ls="-.",
            lw=2.1, label="내전압의 역수 (낮을수록 좋음)")

    # 라벨 높이를 서로 다르게 두고 흰 배경을 깔아 선·글자 겹침을 막는다
    for zz, name, col, yy in [(30.0, "최대 전력\n30 Ω", S.COLORS[1], 2.86),
                              (60.0, "최대 내전압\n60 Ω", S.COLORS[2], 2.40),
                              (76.7, "최소 감쇠\n77 Ω", S.COLORS[0], 2.86)]:
        ax.axvline(zz, color=col, ls=":", lw=1.4, alpha=0.85)
        ax.annotate(name, xy=(zz, yy), fontsize=8.8, color=col, ha="center",
                    va="top", fontweight="bold", zorder=9,
                    bbox=dict(fc="white", ec="none", alpha=0.92, pad=1.6))

    ax.axvspan(48, 53.5, color=S.ACCENT, alpha=0.13)
    ax.axvline(50, color=S.ACCENT, lw=2.2)
    ax.annotate("50 Ω = 가장 덜 나쁜 절충\n(30과 77의 기하평균 48,\n 산술평균 53.5 사이)",
                xy=(50, 1.30), xytext=(86, 1.90), fontsize=9,
                color=S.ACCENT, fontweight="bold", zorder=10,
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.95, lw=1.0),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.3))

    ax.set_xlim(15, 130)
    ax.set_ylim(0.95, 3.0)
    ax.set_xlabel("동축선 특성 임피던스 Z₀ (Ω, 공기 유전체)")
    ax.set_ylabel("정규화 지표 (1 = 그 항목의 최적)")
    ax.set_title("그림 M02-6  50 Ω의 유래 — 세 최적점의 절충")
    ax.legend(loc="lower right", fontsize=8.6, framealpha=0.95)
    S.save(fig, "M02", "coax_tradeoff")


def _microstrip_z0(w_over_h, er):
    """Hammerstad 근사식으로 마이크로스트립 Z₀와 유효 유전율을 구한다."""
    u = np.asarray(w_over_h, dtype=float)
    ee = np.where(
        u <= 1,
        (er + 1) / 2 + (er - 1) / 2 * ((1 + 12 / u) ** -0.5 + 0.04 * (1 - u) ** 2),
        (er + 1) / 2 + (er - 1) / 2 * (1 + 12 / u) ** -0.5,
    )
    z = np.where(
        u <= 1,
        60 / np.sqrt(ee) * np.log(8 / u + u / 4),
        120 * np.pi / (np.sqrt(ee) * (u + 1.393 + 0.667 * np.log(u + 1.444))),
    )
    return z, ee


def m02_microstrip():
    """기판 위에서 50 Ω을 만들려면 선을 얼마나 넓게?"""
    fig, ax = S.figure(7.6, 4.4)
    u = np.logspace(np.log10(0.1), np.log10(10), 500)

    for er, name in [(2.2, "PTFE 계열  Dk 2.2"), (3.55, "고주파용 Dk 3.55"),
                     (4.4, "FR-4  Dk 4.4"), (9.8, "알루미나  Dk 9.8")]:
        z, _ = _microstrip_z0(u, er)
        ax.semilogx(u, z, lw=2.0, label=name)

    ax.axhline(50, color=S.ACCENT, lw=1.8, ls="--")
    ax.text(0.105, 53, "50 Ω", color=S.ACCENT, fontweight="bold", fontsize=10)

    # 교점 라벨을 계단식으로 내려 붙여 겹치지 않게 한다
    for (er, col), yy in zip([(2.2, S.COLORS[0]), (3.55, S.COLORS[1]),
                              (4.4, S.COLORS[2]), (9.8, S.COLORS[3])],
                             [14.5, 19.5, 26.0, 34.0]):
        z, _ = _microstrip_z0(u, er)
        i = np.argmin(np.abs(z - 50))
        ax.plot([u[i]], [50], "o", color=col, ms=8, zorder=8)
        ax.annotate(f"Dk {er}: W/h = {u[i]:.2f}", xy=(u[i], 50),
                    xytext=(u[i], yy), fontsize=8.4, color=col, ha="center",
                    va="top", zorder=9,
                    bbox=dict(fc="white", ec="none", alpha=0.92, pad=1.0),
                    arrowprops=dict(arrowstyle="->", color=col, lw=0.9,
                                    alpha=0.75))

    ax.set_xlabel("선폭 / 기판 두께  (W/h)")
    ax.set_ylabel("특성 임피던스 Z₀ (Ω)")
    ax.set_title("그림 M02-7  마이크로스트립 Z₀ (Hammerstad 근사식)")
    ax.set_ylim(10, 200)
    ax.legend(fontsize=9)
    S.plain_log(ax, "x")
    S.save(fig, "M02", "microstrip_z0")


# ══════════════════════════════════════════════════════════ M03
def _smith_grid(ax, r_vals=(0, 0.2, 0.5, 1, 2, 5),
                x_vals=(0.2, 0.5, 1, 2, 5), lw=0.8):
    """스미스 차트 눈금(등저항 원, 등리액턴스 호)을 그린다."""
    th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(th), np.sin(th), color=S.INK, lw=1.4)
    ax.plot([-1, 1], [0, 0], color=S.INK, lw=1.0)

    for r in r_vals:                      # 등저항 원
        c, rad = r / (1 + r), 1 / (1 + r)
        ax.plot(c + rad * np.cos(th), rad * np.sin(th), color=S.MUTED, lw=lw)

    for x in x_vals:                      # 등리액턴스 호
        c, rad = 1, 1 / x
        for sgn in (+1, -1):
            t = np.linspace(0, 2 * np.pi, 800)
            xs, ys = c + rad * np.cos(t), sgn * rad + rad * np.sin(t)
            m = xs ** 2 + ys ** 2 <= 1.0
            ax.plot(xs[m], ys[m], color=S.MUTED, lw=lw, ls="-")
    ax.set_aspect("equal")
    ax.set_xlim(-1.18, 1.18)
    ax.set_ylim(-1.18, 1.18)
    ax.axis("off")


def m03_smith_anatomy():
    """스미스 차트 해부도 — 어디가 무엇인가."""
    fig, ax = S.figure(6.4, 6.0)
    _smith_grid(ax)

    pts = [(-1, 0, "단락\n(Z = 0)", (-1.05, 0.13), "right"),
           (1, 0, "개방\n(Z = 무한대)", (1.05, 0.13), "left"),
           (0, 0, "중심 = 50 Ω (완전 정합)", (0.0, 0.17), "center"),
           (0, 1, "순수 유도성 (+j50 Ω)", (0.0, 1.09), "center"),
           (0, -1, "순수 용량성 (-j50 Ω)", (0.0, -1.11), "center")]
    for x, y, name, tp, ha in pts:
        ax.plot([x], [y], "o", color=S.ACCENT, ms=8, zorder=10)
        ax.annotate(name, xy=tp, fontsize=9.3, color=S.ACCENT,
                    fontweight="bold", ha=ha, va="center", zorder=11,
                    bbox=dict(fc="white", ec="none", alpha=0.92, pad=1.4))

    ax.annotate("위쪽 절반 = 유도성 (+jX)", xy=(-0.30, 0.70), fontsize=10,
                ha="center", color=S.COLORS[0], fontweight="bold", zorder=11,
                bbox=dict(fc="white", ec="none", alpha=0.88, pad=1.4))
    ax.annotate("아래쪽 절반 = 용량성 (-jX)", xy=(-0.30, -0.74), fontsize=10,
                ha="center", color=S.COLORS[1], fontweight="bold", zorder=11,
                bbox=dict(fc="white", ec="none", alpha=0.88, pad=1.4))

    # 두 원의 라벨을 차트 안에 쓰면 서로 겹친다. 범례로 빼낸다.
    th = np.linspace(0, 2 * np.pi, 300)
    for g, lab, ls in [(0.333, "|Γ| = 0.33  (VSWR 2, 반사 전력 11 %)", "--"),
                       (0.5, "|Γ| = 0.5   (VSWR 3, 반사 전력 25 %)", (0, (4, 2)))]:
        ax.plot(g * np.cos(th), g * np.sin(th), color=S.COLORS[2], ls=ls,
                lw=1.6, zorder=6, label=lab)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.09), fontsize=8.8,
              framealpha=0.95)

    ax.set_title("그림 M03-3  스미스 차트 해부도", fontweight="bold")
    S.save(fig, "M03", "smith_anatomy")


def m03_lmatch():
    """L형 정합 궤적 — 부하에서 중심(50 Ω)까지 두 걸음."""
    z0 = 50.0
    zl = 20 - 30j                      # 정합할 부하
    f = 2.4e9
    w = 2 * np.pi * f

    # 직렬 L → 병렬 C 로 정합 (Rl < Z0 인 경우의 표준 해)
    rl, xl = zl.real, zl.imag
    q = np.sqrt(z0 / rl - 1)
    xs = q * rl - xl                   # 필요한 직렬 리액턴스
    bp = q / z0                        # 필요한 병렬 서셉턴스
    z_mid = zl + 1j * xs
    # 병렬 커패시터의 어드미턴스는 +jB (jωC) 이다. 부호를 반대로 넣으면
    # 궤적이 중심으로 오지 않는다 — 초판에서 실제로 낸 실수.
    y_end = 1 / z_mid + 1j * bp
    z_end = 1 / y_end

    def g(z):
        return (z - z0) / (z + z0)

    fig, ax = S.figure(6.4, 6.0)
    _smith_grid(ax)

    steps = np.linspace(0, 1, 120)
    tr1 = np.array([g(zl + 1j * xs * t) for t in steps])
    tr2 = np.array([g(1 / (1 / z_mid + 1j * bp * t)) for t in steps])

    ax.plot(tr1.real, tr1.imag, color=S.COLORS[0], lw=2.6,
            label=f"1단계: 직렬 L 추가 (+j{xs:.1f} $\\Omega$ = {xs/w*1e9:.2f} nH)")
    ax.plot(tr2.real, tr2.imag, color=S.COLORS[1], lw=2.6,
            label=f"2단계: 병렬 C 추가 (B = {bp*1e3:.2f} mS = {bp/w*1e12:.2f} pF)")

    for z, name, col in [(zl, f"시작: 부하\n{zl.real:.0f} {zl.imag:+.0f}j Ω", S.ACCENT),
                         (z_mid, "중간", S.COLORS[0]),
                         (z_end, "도착: 50 Ω", S.COLORS[2])]:
        p = g(z)
        ax.plot([p.real], [p.imag], "o", color=col, ms=9, zorder=9)
        ax.annotate(name, xy=(p.real, p.imag),
                    xytext=(p.real + 0.11, p.imag + 0.15),
                    fontsize=9, color=col, fontweight="bold", zorder=11,
                    bbox=dict(fc="white", ec=col, alpha=0.93, lw=0.8),
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.0))

    ax.set_title(f"그림 M03-4  L형 정합 궤적 ({f/1e9:.1f} GHz)", fontweight="bold")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.10), fontsize=9)
    S.save(fig, "M03", "lmatch_trajectory")
    return dict(zl=zl, xs=xs, L_nH=xs / w * 1e9, C_pF=bp / w * 1e12,
                z_end=z_end, q=q)


def m03_quarterwave_bw():
    """λ/4 변환기는 설계 주파수에서만 완벽하다."""
    fig, ax = S.figure(7.6, 4.4)
    z0, zl = 50.0, 100.0
    zt = np.sqrt(z0 * zl)
    fr = np.linspace(0.2, 1.8, 600)                 # f / f0
    theta = np.pi / 2 * fr
    zin = zt * (zl + 1j * zt * np.tan(theta)) / (zt + 1j * zl * np.tan(theta))
    gam = np.abs((zin - z0) / (zin + z0))
    rl = -20 * np.log10(np.clip(gam, 1e-6, None))

    ax.plot(fr, rl, color=S.COLORS[0], lw=2.4,
            label=f"단일 구간 λ/4 변환기 (Z_T = {zt:.1f} Ω)")
    S.limit_line(ax, 20, "반사손실 20 dB 기준선")

    ok = fr[rl >= 20]
    ax.axvspan(ok.min(), ok.max(), color=S.COLORS[2], alpha=0.14)
    ax.annotate(f"20 dB 이상 구간\n{ok.min():.2f}–{ok.max():.2f} f₀\n"
                f"(비대역폭 약 {(ok.max()-ok.min())*100:.0f} %)",
                xy=(1.0, 26), ha="center", fontsize=9, color=S.INK,
                bbox=dict(fc="white", ec=S.GRID, alpha=0.9))

    ax.set_xlabel("주파수 (설계 주파수 f₀ 기준)")
    ax.set_ylabel("반사손실 (dB, 클수록 좋음)")
    ax.set_title("그림 M03-5  λ/4 변환기의 대역폭  (50 Ω → 100 Ω)")
    ax.set_ylim(0, 45)
    ax.legend(loc="lower center")
    S.save(fig, "M03", "quarterwave_bw")
    return dict(zt=zt, lo=ok.min(), hi=ok.max())


# ══════════════════════════════════════════════════════════ 실행
if __name__ == "__main__":
    m00_spectrum_map()
    m00_wavelength_vs_size()
    m00_voltage_along_wire()

    m01_linear_vs_db()
    m01_db_ratio()
    m01_level_diagram()
    m01_ktb()
    m01_sensitivity_waterfall()

    m02_standing_wave()
    m02_gamma_vswr_rl()
    m02_coax_tradeoff()
    m02_microstrip()

    m03_smith_anatomy()
    lm = m03_lmatch()
    qw = m03_quarterwave_bw()

    print("\n[본문에 인용할 계산값]")
    print(f"  L형 정합: 부하 {lm['zl']}, Q={lm['q']:.3f}, "
          f"직렬 L={lm['L_nH']:.3f} nH, 병렬 C={lm['C_pF']:.3f} pF, "
          f"결과 Z={lm['z_end']:.3f}")
    print(f"  λ/4 변환기: Z_T={qw['zt']:.2f} Ω, "
          f"20 dB 대역 {qw['lo']:.3f}~{qw['hi']:.3f} f0")
    for er in (2.2, 3.55, 4.4, 9.8):
        u = np.logspace(-1, 1, 4000)
        z, ee = _microstrip_z0(u, er)
        i = np.argmin(np.abs(z - 50))
        print(f"  Dk {er}: 50 Ω 선폭 W/h={u[i]:.3f}, 유효 Dk={ee[i]:.3f}, "
              f"단축률={1/np.sqrt(ee[i]):.3f}")
    print("\n완료")
