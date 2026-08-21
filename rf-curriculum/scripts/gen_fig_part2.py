#!/usr/bin/env python3
"""
Part II (M04, M05) 데이터 그림 생성기
=====================================

    python3 scripts/gen_fig_part2.py

출력: assets/M04/*.svg, assets/M05/*.svg
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import rf_style as S

C0 = 299_792_458.0
RNG = np.random.default_rng(20260820)      # 재현 가능한 난수


# ══════════════════════════════════════════════════════════ M04
def m04_cable_phase():
    """케이블 길이가 조금만 변해도 위상은 크게 변한다."""
    fig, ax = S.figure(7.6, 4.4)
    f = np.linspace(0.1e9, 6e9, 500)

    for dl_mm, ls in [(0.1, "-"), (0.5, "--"), (1.0, "-."), (5.0, ":")]:
        dphi = 360 * (dl_mm / 1000) / (C0 / f) / 0.7      # 단축률 0.7 케이블
        ax.plot(f / 1e9, dphi, ls=ls, lw=2.0,
                label=f"길이 변화 {dl_mm} mm")

    S.limit_line(ax, 5, "위상 오차 5도 기준선")
    y24 = 360 * 0.001 / (C0 / 2.4e9) / 0.7
    ax.plot([2.4], [y24], "o", color=S.ACCENT, ms=8, zorder=8)
    ax.annotate(f"2.4 GHz에서 1 mm 변화\n= 약 {y24:.1f}도\n(5 GHz대에서는 2배 이상)",
                xy=(2.4, y24), xytext=(2.9, 26), fontsize=9,
                color=S.ACCENT, fontweight="bold",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.94, lw=0.9),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))

    ax.set_xlabel("주파수 (GHz)")
    ax.set_ylabel("생기는 위상 오차 (도)")
    ax.set_title("그림 M04-6  케이블 길이 변화가 만드는 위상 오차")
    ax.set_ylim(0, 55)
    ax.legend(loc="upper left", fontsize=9)
    S.save(fig, "M04", "cable_phase")


def m04_power_headroom():
    """장비를 태우지 않으려면 — 레벨 관리 창."""
    fig, ax = S.figure(7.8, 4.6)

    rows = [
        ("스펙트럼 분석기\n(입력 감쇠기 0 dB)", -150, -20, +10),
        ("스펙트럼 분석기\n(입력 감쇠기 20 dB)", -130, 0, +30),
        ("VNA 수신 포트", -110, -5, +20),
        ("전력계 센서", -70, +20, +23),
    ]
    for i, (name, danl, p_max_safe, p_damage) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.barh(y, p_max_safe - danl, left=danl, height=0.42,
                color=S.COLORS[2], alpha=0.45, edgecolor=S.INK, lw=1.0)
        ax.barh(y, p_damage - p_max_safe, left=p_max_safe, height=0.42,
                color=S.COLORS[4], alpha=0.55, edgecolor=S.INK, lw=1.0)
        ax.plot([p_damage], [y], "X", color=S.ACCENT, ms=13, zorder=8)
        ax.text(danl - 3, y, name, ha="right", va="center", fontsize=9)
        ax.text((danl + p_max_safe) / 2, y + 0.30, "쓸 수 있는 범위",
                ha="center", fontsize=7.6, color=S.INK)
        ax.text(p_damage + 3, y, f"손상 {p_damage:+d} dBm", ha="left",
                va="center", fontsize=8, color=S.ACCENT, fontweight="bold")

    ax.axvline(0, color=S.MUTED, lw=1.0, ls=":")
    ax.text(0, len(rows) - 0.35, "0 dBm", ha="center", fontsize=8.5,
            color=S.MUTED)

    ax.set_yticks([])
    ax.set_xlim(-175, 60)
    ax.set_ylim(-0.7, len(rows) - 0.15)
    ax.set_xlabel("입력 전력 (dBm)")
    ax.set_title("그림 M04-2  장비별 안전 입력 범위 (대표값, 반드시 자기 장비 사양 확인)")
    ax.grid(axis="x", alpha=0.5)
    for s in ("left", "right", "top"):
        ax.spines[s].set_visible(False)
    S.save(fig, "M04", "power_headroom")


# ══════════════════════════════════════════════════════════ M05
def _sa_trace(f_mhz, tones, rbw_khz, nf_db=20.0, seed=0):
    """스펙트럼 분석기 트레이스를 흉내 낸다.

    잡음 바닥 = -174 + NF + 10log(RBW).  신호는 RBW 필터 모양(가우시안 근사)
    으로 퍼져 보인다 — 이것이 '분해능'의 실체다.
    """
    rng = np.random.default_rng(seed)
    floor = -174 + nf_db + 10 * np.log10(rbw_khz * 1e3)
    lin = 10 ** (floor / 10) * rng.chisquare(2, size=f_mhz.size) / 2
    sigma = rbw_khz * 1e-3 / 2.355        # RBW(MHz)를 반치폭으로 보는 근사
    for f0, p_dbm in tones:
        lin += 10 ** (p_dbm / 10) * np.exp(-0.5 * ((f_mhz - f0) / sigma) ** 2)
    return 10 * np.log10(lin)


def m05_rbw_noise_floor():
    """RBW를 좁히면 잡음 바닥이 내려가고 소인 시간이 늘어난다."""
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.2))
    S.setup()
    fig.patch.set_facecolor("white")

    f = np.linspace(999.0, 1001.0, 2400)
    rbws = [1000, 100, 10, 1]                      # kHz
    for i, rbw in enumerate(rbws):
        tr = _sa_trace(f, [(1000.0, -60.0)], rbw, seed=i)
        axes[0].plot(f, tr, lw=1.1, label=f"RBW {rbw} kHz")

    axes[0].set_xlabel("주파수 (MHz)")
    axes[0].set_ylabel("전력 (dBm)")
    axes[0].set_title("RBW를 좁히면 잡음 바닥이 내려간다", fontsize=10.5)
    axes[0].legend(fontsize=8.5, loc="upper right")
    axes[0].set_ylim(-130, -50)

    # 오른쪽: 잡음 바닥과 소인 시간
    rb = np.logspace(0, 3.5, 100)                  # kHz
    floor = -174 + 20 + 10 * np.log10(rb * 1e3)
    span_mhz, k = 2.0, 2.0
    sweep_ms = k * (span_mhz * 1e6) / (rb * 1e3) ** 2 * 1e3

    ax1 = axes[1]
    ax1.semilogx(rb, floor, color=S.COLORS[0], lw=2.2)
    ax1.set_xlabel("RBW (kHz)")
    ax1.set_ylabel("잡음 바닥 (dBm)", color=S.COLORS[0])
    ax1.tick_params(axis="y", labelcolor=S.COLORS[0])
    ax2 = ax1.twinx()
    ax2.loglog(rb, sweep_ms, color=S.COLORS[1], ls="--", lw=2.1)
    ax2.set_ylabel("소인 시간 (ms, 스팬 2 MHz)", color=S.COLORS[1])
    ax2.tick_params(axis="y", labelcolor=S.COLORS[1])
    ax2.grid(False)
    S.plain_log(ax1, "x")
    S.plain_log(ax2, "y")
    ax1.set_title("얻는 것과 잃는 것", fontsize=10.5)
    ax1.annotate("RBW를 10배 좁히면\n잡음 바닥 -10 dB,\n소인 시간 100배",
                 xy=(10, -104), xytext=(30, -118), fontsize=8.6,
                 color=S.INK, ha="left",
                 bbox=dict(fc="white", ec=S.GRID, alpha=0.96),
                 arrowprops=dict(arrowstyle="->", color=S.INK, lw=1.0))

    fig.suptitle("그림 M05-4  분해능 대역폭(RBW)의 3중 효과", fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M05", "rbw_noise_floor")


def m05_resolution():
    """가까운 두 신호를 구별하려면 RBW가 충분히 좁아야 한다."""
    fig, axes = plt.subplots(1, 3, figsize=(10.0, 3.7), sharey=True)
    S.setup()
    fig.patch.set_facecolor("white")

    fc = 1000.0                                    # 중심 주파수 (MHz)
    f = np.linspace(fc - 0.3, fc + 0.3, 1800)
    tones = [(fc - 0.1, -50.0), (fc + 0.1, -50.0)]  # 200 kHz 간격
    for ax, rbw, verdict in zip(axes, [300, 100, 10],
                                ["구별 못 함", "겨우 보임", "확실히 분해"]):
        tr = _sa_trace(f, tones, rbw, seed=7)
        # 절대 MHz 로 그리면 축이 '+1e3' 오프셋 표기가 되어 읽기 어렵다.
        # 중심 주파수로부터의 오프셋(kHz)으로 그린다 — 실제 장비 사용법과도 맞다.
        ax.plot((f - fc) * 1000, tr, color=S.COLORS[0], lw=1.2)
        ax.set_title(f"RBW {rbw} kHz — {verdict}", fontsize=10)
        ax.set_xlabel(f"중심 {fc:.0f} MHz 로부터의 오프셋 (kHz)", fontsize=9.5)
        ax.grid(alpha=0.5)
        for f0, _ in tones:
            ax.axvline((f0 - fc) * 1000, color=S.MUTED, ls=":", lw=1.0)
        ax.set_xticks([-200, -100, 0, 100, 200])
    axes[0].set_ylabel("전력 (dBm)")
    axes[0].set_ylim(-125, -40)
    fig.suptitle("그림 M05-5  200 kHz 떨어진 두 신호 — RBW가 분해능을 정한다",
                 fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M05", "resolution")


def m05_detectors():
    """같은 신호도 검출기를 바꾸면 다르게 보인다."""
    fig, ax = S.figure(8.0, 4.4)

    rng = np.random.default_rng(3)
    n_disp, n_per = 60, 40                       # 표시점 60개, 점당 샘플 40개
    floor_dbm = -100.0
    lin = 10 ** (floor_dbm / 10) * rng.chisquare(2, size=(n_disp, n_per)) / 2
    lin[30] += 10 ** (-88 / 10)                  # 한 점에만 짧은 신호

    x = np.arange(n_disp)
    peak = 10 * np.log10(lin.max(axis=1))
    samp = 10 * np.log10(lin[:, 0])
    rms = 10 * np.log10(lin.mean(axis=1))

    ax.step(x, peak, where="mid", color=S.COLORS[0], lw=1.8,
            label="첨두(peak) — 가장 큰 값. 신호를 놓치지 않음")
    ax.step(x, samp, where="mid", color=S.COLORS[1], lw=1.5, ls="--",
            label="샘플(sample) — 한 점만. 신호를 놓칠 수 있음")
    ax.step(x, rms, where="mid", color=S.COLORS[2], lw=2.0, ls="-.",
            label="RMS 평균 — 잡음 전력을 정확히 읽음")

    ax.axvline(30, color=S.ACCENT, lw=1.4, ls=":")
    ax.annotate("여기에 짧은 신호가 있다", xy=(30, peak[30]),
                xytext=(36, peak[30] + 6), fontsize=9, color=S.ACCENT,
                fontweight="bold",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.94, lw=0.9),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    ax.axhline(floor_dbm, color=S.MUTED, ls=":", lw=1.2)
    ax.text(1, floor_dbm + 1.2, "실제 잡음 전력 -100 dBm", fontsize=8.5,
            color=S.MUTED)

    ax.set_xlabel("화면의 가로 표시점 (bucket)")
    ax.set_ylabel("표시 전력 (dBm)")
    ax.set_title("그림 M05-6  검출기(detector) 세 종류가 같은 데이터를 다르게 읽는다")
    ax.legend(loc="lower left", fontsize=8.6)
    ax.set_ylim(-118, -78)
    S.save(fig, "M05", "detectors")


def m05_attenuator_window():
    """입력 감쇠기는 위쪽 한계와 아래쪽 바닥을 함께 밀어 올린다."""
    fig, ax = S.figure(7.8, 4.4)

    att = np.array([0, 10, 20, 30, 40])
    danl = -150 + att              # 감쇠기만큼 잡음 바닥이 올라간다
    pmax = -20 + att               # 안전 최대 입력도 함께 올라간다

    ax.fill_between(att, danl, pmax, color=S.COLORS[2], alpha=0.22,
                    label="측정 가능 범위")
    ax.plot(att, danl, "o-", color=S.COLORS[0], lw=2.2,
            label="표시 평균 잡음 레벨 (DANL)")
    ax.plot(att, pmax, "s--", color=S.COLORS[1], lw=2.2,
            label="안전 최대 입력")

    for a, d, p in zip(att, danl, pmax):
        ax.annotate(f"{p - d:.0f} dB", xy=(a, (d + p) / 2 + 12), ha="center",
                    fontsize=8.6, color=S.INK, fontweight="bold",
                    bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.0))

    ax.annotate("창의 폭(130 dB)은 그대로인 채 통째로 위로 올라간다\n"
                "= 큰 신호에 안전해지지만 작은 신호는 못 본다",
                xy=(20, -138), fontsize=9, ha="center", va="top",
                color=S.ACCENT, fontweight="bold",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.96, lw=0.9))

    ax.set_xlabel("입력 감쇠기 설정 (dB)")
    ax.set_ylabel("전력 (dBm)")
    ax.set_title("그림 M05-7  입력 감쇠기가 측정 창을 움직인다 (대표값)")
    ax.set_ylim(-168, 40)
    ax.set_xticks(att)
    ax.legend(loc="upper left", fontsize=9)
    S.save(fig, "M05", "attenuator_window")


if __name__ == "__main__":
    m04_cable_phase()
    m04_power_headroom()
    m05_rbw_noise_floor()
    m05_resolution()
    m05_detectors()
    m05_attenuator_window()

    print("\n[본문에 인용할 계산값]")
    for f_ghz in (0.9, 2.4, 5.8):
        dphi = 360 * 0.001 / (C0 / (f_ghz * 1e9)) / 0.7
        print(f"  {f_ghz} GHz 에서 1 mm 길이 변화 → {dphi:.1f}도")
    for rbw in (1e6, 1e5, 1e4, 1e3):
        print(f"  RBW {rbw/1e3:>6.0f} kHz → 잡음 바닥 {-174+20+10*np.log10(rbw):.1f} dBm (NF 20 dB 가정)")
    print("완료")
