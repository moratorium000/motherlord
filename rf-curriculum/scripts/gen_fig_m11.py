#!/usr/bin/env python3
"""
M11 (트랜시버 아키텍처) 데이터 그림 생성기
==========================================

    python3 scripts/gen_fig_m11.py

출력: assets/M11/*.svg
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt

import rf_style as S


# ══════════════════════════════════════ 공통 계산
def irr_db(gain_err_db, phase_err_deg):
    """I/Q 불균형이 만드는 이미지 억압비 [dB]."""
    a = 10 ** (np.asarray(gain_err_db) / 20)
    t = np.deg2rad(np.asarray(phase_err_deg))
    return 10 * np.log10((1 + 2 * a * np.cos(t) + a ** 2)
                         / (1 - 2 * a * np.cos(t) + a ** 2))


def nyquist_zone(f, fs):
    """신호 주파수 f 가 속한 나이퀴스트 존 (1부터)."""
    return int(np.floor(f / (fs / 2))) + 1


def alias_freq(f, fs):
    """샘플링 뒤 1차 존에 나타나는 주파수."""
    return abs(f - fs * round(f / fs))


# ══════════════════════════════════════ M11-5: I/Q 불균형
def m11_iq():
    S.setup()
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.6))
    fig.patch.set_facecolor("white")

    # 왼쪽: 저-IF 수신기의 복소 스펙트럼
    ax = axes[0]
    f_if = 2.0                     # MHz (저-IF)
    wanted, adjacent = -35.0, -15.0
    for g_db, ph, col, dx, name in ((0.5, 2.0, S.ACCENT, 0.30,
                                     "보정 전 (IRR 30 dB)"),
                                    (0.02, 0.1, S.COLORS[2], 0.62,
                                     "디지털 보정 후 (IRR 57 dB)")):
        r = irr_db(g_db, ph)
        # 실제로는 원래 신호와 같은 주파수에 겹친다. 보이게 하려고 벌려 그린다.
        ax.plot([-f_if + dx, -f_if + dx], [-110, wanted - r], lw=3.0,
                color=col, ls="-", solid_capstyle="butt", zorder=4)
        ax.plot([f_if + dx, f_if + dx], [-110, adjacent - r], lw=3.0,
                color=col, ls="-", solid_capstyle="butt", zorder=4,
                label=name)

    ax.plot([f_if, f_if], [-110, wanted], lw=4.2, color=S.COLORS[0],
            solid_capstyle="butt", zorder=6)
    ax.text(f_if, wanted + 3, f"원하는 채널\n{wanted:.0f} dBm", ha="center",
            fontsize=9, color=S.COLORS[0], fontweight="bold")
    ax.plot([-f_if, -f_if], [-110, adjacent], lw=4.2, color=S.MUTED,
            solid_capstyle="butt", zorder=5)
    ax.text(-f_if, adjacent + 3, f"인접 채널\n{adjacent:.0f} dBm", ha="center",
            fontsize=9, color=S.MUTED, fontweight="bold")

    ax.annotate("인접 채널이 접혀 온 것\n= 원하는 채널 위에 얹힌다\n"
                "(보이게 하려고 옆으로 벌려 그렸다)",
                xy=(f_if + 0.30, adjacent - 30), xytext=(3.1, -74),
                fontsize=8.8, color=S.ACCENT, fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=1.0),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.3))

    ax.axvline(0, color=S.INK, lw=1.2)
    ax.text(0, -108, "0 Hz (LO 자리)", ha="center", va="bottom",
            fontsize=8.4, color=S.INK)
    ax.set_xlim(-6, 6)
    ax.set_ylim(-110, -2)
    ax.set_xlabel("복소 기저대역 주파수 (MHz)")
    ax.set_ylabel("레벨 (dBm)")
    ax.set_title("저-IF 수신기의 복소 스펙트럼", fontsize=10.5)
    ax.legend(fontsize=8.0, loc="lower right", framealpha=0.96)
    ax.grid(alpha=0.4)

    # 오른쪽: IRR vs 오차
    ax = axes[1]
    ph = np.linspace(0.02, 6, 800)
    for g, ls in ((0.0, "-"), (0.1, "--"), (0.3, "-."),
                  (1.0, (0, (5, 1, 1, 1)))):
        ax.plot(ph, irr_db(g, ph), lw=2.0, ls=ls, label=f"이득 오차 {g:.1f} dB")
    for y in (25, 40, 60):
        ax.axhline(y, color=S.MUTED, ls=":", lw=1.2)
    ax.text(0.024, 12.5, "25 dB  아날로그만으로 흔히 얻는 수준\n"
                         "40 dB  정성껏 맞춘 아날로그의 한계\n"
                         "60 dB  디지털 보정이 필요한 영역",
            fontsize=8.4, color=S.MUTED, ha="left", va="bottom",
            bbox=dict(fc="white", ec=S.GRID, alpha=0.96))
    ax.set_xscale("log")
    S.plain_log(ax, axis="x")
    ax.set_xlabel("위상 오차 (도)")
    ax.set_ylabel("이미지 억압비 IRR (dB)")
    ax.set_title("IRR 은 두 오차 중 나쁜 쪽이 정한다", fontsize=10.5)
    ax.set_ylim(10, 75)
    ax.grid(which="both", alpha=0.35)
    ax.legend(fontsize=8.6, loc="upper right")

    fig.suptitle("그림 M11-5  I/Q 불균형 — 자기 신호의 거울상이 자기 위에 얹힌다",
                 fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M11", "iq")
    return {f"{g}/{p}": irr_db(g, p)
            for g, p in ((0.5, 2.0), (0.2, 1.0), (0.05, 0.2), (0.02, 0.1))}


# ══════════════════════════════════════ M11-6: 나이퀴스트 존
def m11_nyquist():
    S.setup()
    fig, axes = plt.subplots(2, 1, figsize=(9.6, 6.2),
                             gridspec_kw=dict(height_ratios=[2.0, 1.0]))
    fig.patch.set_facecolor("white")

    fs = 500.0                        # MSPS
    fmax = 3000.0
    nz = int(np.ceil(fmax / (fs / 2)))

    ax = axes[0]
    for z in range(1, nz + 1):
        a, b = (z - 1) * fs / 2, z * fs / 2
        inv = (z % 2 == 0)
        ax.axvspan(a, b, color=S.COLORS[1] if inv else S.COLORS[0],
                   alpha=0.13, zorder=1)
        ax.text((a + b) / 2, 1.06, f"{z}", ha="center", fontsize=8.6,
                color=S.INK, fontweight="bold")
        if inv:
            ax.text((a + b) / 2, 0.93, "반전", ha="center", fontsize=7.4,
                    color=S.COLORS[1])

    signals = [(2400.0, "원하는 신호 2400 MHz", S.COLORS[2], 0.80, -1),
               (2450.0, "인접 신호 2450 MHz", S.COLORS[3], 0.58, +1),
               (600.0, "저주파 간섭 600 MHz", S.ACCENT, 0.80, +1)]
    for f, lab, col, h, side in signals:
        al = alias_freq(f, fs)
        ax.plot([f, f], [0, h], lw=3.4, color=col, zorder=5)
        ax.text(f + side * 40, h + 0.04, f"{lab}\n→ 접히면 {al:.0f} MHz",
                ha="left" if side > 0 else "right", fontsize=8.4, color=col,
                fontweight="bold",
                bbox=dict(fc="white", ec=col, alpha=0.95, lw=0.8))

    ax.set_xlim(0, fmax)
    ax.set_ylim(0, 1.18)
    ax.set_yticks([])
    ax.set_xlabel("ADC 입력 주파수 (MHz)")
    ax.set_title(f"샘플링 주파수 {fs:.0f} MSPS — 모든 존이 1차 존으로 접힌다",
                 fontsize=10.5)
    ax.grid(axis="x", alpha=0.35)

    ax = axes[1]
    for i, (f, lab, col, _h, _s) in enumerate(signals):
        al = alias_freq(f, fs)
        ax.plot([al + i * 1.4, al + i * 1.4], [0, 1], lw=4.0, color=col)
    ax.text(100, 1.10, "100 MHz", ha="center", fontsize=8.8, color=S.INK,
            fontweight="bold")
    ax.text(50, 1.10, "50 MHz", ha="center", fontsize=8.8, color=S.COLORS[3],
            fontweight="bold")
    ax.annotate("2400 MHz 와 600 MHz 가 같은 100 MHz 로 접혔다.\n"
                "디지털에서는 둘을 구별할 방법이 없다\n"
                "— 그래서 ADC 앞의 대역통과 필터가 필수다.",
                xy=(101, 0.5), xytext=(122, 1.30), fontsize=9,
                color=S.ACCENT, fontweight="bold", ha="left", va="top",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=1.0),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    ax.set_xlim(0, fs / 2)
    ax.set_ylim(0, 1.7)
    ax.set_yticks([])
    ax.set_xlabel("디지털에서 보이는 주파수 (MHz)")
    ax.set_title("1차 존 (0 ~ fs/2) — 셋이 구별되지 않는다면 되돌릴 방법이 없다",
                 fontsize=10.5)
    ax.grid(axis="x", alpha=0.35)

    fig.suptitle("그림 M11-6  나이퀴스트 존과 대역통과 샘플링",
                 fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M11", "nyquist")
    return {f"{f:.0f}": dict(zone=nyquist_zone(f, fs), alias=alias_freq(f, fs),
                             inverted=nyquist_zone(f, fs) % 2 == 0)
            for f, *_ in signals}


# ══════════════════════════════════════ M11-7: 레벨 다이어그램과 AGC
CHAIN = [("안테나", 0.0, None), ("RF 필터", -1.5, None),
         ("LNA", +18.0, +18.0), ("이미지 필터", -2.0, None),
         ("믹서", -7.0, +1.0), ("IF 필터", -2.5, None),
         ("IF 증폭기 (AGC)", +25.0, +10.0), ("ADC 입력", 0.0, None)]


def chain_levels(p_in, agc_gain):
    out, p = [], p_in
    for name, g, p1 in CHAIN:
        gg = agc_gain if name.startswith("IF 증폭기") else g
        p += gg
        out.append((name, p, p1))
    return out


def m11_level():
    fig, ax = S.figure(9.2, 5.2)
    x = np.arange(len(CHAIN))

    # AGC 의 목표는 '어떤 입력에서도 ADC 입력을 일정하게' 유지하는 것이다.
    # 고정 이득 합이 +5 dB 이므로 −10 dBm 을 맞추려면 AGC 가 75 / 15 dB 여야 한다.
    for p_in, agc, name, col, ls in ((-90.0, 75.0,
                                      "약한 신호 (−90 dBm, AGC 75 dB)",
                                      S.COLORS[0], "-"),
                                     (-30.0, 15.0,
                                      "강한 신호 (−30 dBm, AGC 15 dB)",
                                      S.COLORS[1], "--")):
        lv = chain_levels(p_in, agc)
        ax.plot(x, [v for _, v, _ in lv], lw=2.6, ls=ls, color=col,
                marker="o", ms=6, label=name)

    p1s = [p1 for _, _, p1 in CHAIN]
    for i, p1 in enumerate(p1s):
        if p1 is not None:
            ax.plot([i - 0.3, i + 0.3], [p1, p1], color=S.ACCENT, lw=2.6)
            ax.text(i, p1 + 2.5, f"P1dB {p1:+.0f}", ha="center", fontsize=8.4,
                    color=S.ACCENT, fontweight="bold")

    ax.axhline(0, color=S.INK, ls=":", lw=1.8)
    ax.text(0.1, 2.0, "ADC 풀스케일 0 dBm", fontsize=9, color=S.INK,
            fontweight="bold")
    ax.axhline(-10.0, color=S.COLORS[2], ls="--", lw=1.6)
    ax.text(0.1, -8.0, "AGC 목표 −10 dBm (두 경우 모두 같은 자리)",
            fontsize=9, color=S.COLORS[2], fontweight="bold")

    lv = chain_levels(-30.0, 15.0)
    i_mix = 4
    ax.annotate(f"강한 신호일 때 믹서 여유는\n{p1s[i_mix] - lv[i_mix][1]:.0f} dB 뿐이다",
                xy=(i_mix, lv[i_mix][1]), xytext=(0.15, -46), fontsize=9,
                color=S.ACCENT, fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=1.0),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.3))

    ax.set_xticks(x)
    ax.set_xticklabels([n for n, _, _ in CHAIN], rotation=22, ha="right",
                       fontsize=8.6)
    ax.set_ylabel("신호 레벨 (dBm)")
    ax.set_title("그림 M11-7  레벨 다이어그램 — AGC 는 어디를 얼마나 움직이는가")
    ax.set_ylim(-100, 30)
    ax.grid(alpha=0.4)
    ax.legend(fontsize=9, loc="upper left")
    S.save(fig, "M11", "level")
    weak = chain_levels(-90.0, 75.0)
    strong = chain_levels(-30.0, 15.0)
    return dict(weak=weak, strong=strong,
                agc_range=75.0 - 15.0,
                mixer_headroom_strong=p1s[4] - strong[4][1],
                mixer_headroom_weak=p1s[4] - weak[4][1])


# ══════════════════════════════════════ M11-8: ADC 사양 읽기
def m11_adc():
    fig, ax = S.figure(8.6, 5.0)
    bw = np.logspace(5, 8.6, 500)
    fs = 500e6

    for snr_fs, name, ls in ((68.0, "SNR 68 dBFS (ENOB 11.0)", "-"),
                             (62.0, "SNR 62 dBFS (ENOB 10.0)", "--"),
                             (74.0, "SNR 74 dBFS (ENOB 12.0)", "-.")):
        nsd = -snr_fs - 10 * np.log10(fs / 2)
        ax.plot(bw / 1e6, -(nsd + 10 * np.log10(bw)), lw=2.2, ls=ls,
                label=name)

    nsd68 = -68.0 - 10 * np.log10(fs / 2)
    for b, lab in ((1e6, "1 MHz\n(협대역)"), (20e6, "20 MHz\n(LTE)"),
                   (100e6, "100 MHz\n(5G NR)")):
        v = -(nsd68 + 10 * np.log10(b))
        ax.plot([b / 1e6], [v], "o", color=S.ACCENT, ms=8, zorder=8)
        ax.annotate(f"{lab}\n{v:.0f} dB", xy=(b / 1e6, v),
                    xytext=(b / 1e6 * 0.30, v - 11), fontsize=8.8,
                    color=S.ACCENT, fontweight="bold", ha="center",
                    bbox=dict(fc="white", ec=S.ACCENT, alpha=0.96, lw=0.9),
                    arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.1))

    ax.text(5.0, 104,
            f"NSD = −SNR − 10·log₁₀(fs/2) = {nsd68:.0f} dBFS/Hz\n"
            "채널이 좁을수록 그만큼 처리 이득을 번다\n"
            "(대역폭 1/10 → 10 dB 이득)",
            fontsize=8.8, color=S.INK, ha="left", va="top",
            bbox=dict(fc="white", ec=S.GRID, alpha=0.97))

    ax.set_xscale("log")
    S.plain_log(ax, axis="x")
    ax.set_xlabel("채널 대역폭 (MHz)")
    ax.set_ylabel("채널 안에서 쓸 수 있는 SNR (dB)")
    ax.set_title("그림 M11-8  ADC 는 '몇 비트'가 아니라 NSD 로 읽는다")
    ax.set_ylim(55, 105)
    ax.grid(which="both", alpha=0.35)
    ax.legend(fontsize=9, loc="lower left")
    S.save(fig, "M11", "adc")
    return dict(nsd=nsd68, enob=(68.0 - 1.76) / 6.02,
                snr_1m=-(nsd68 + 60), snr_20m=-(nsd68 + 10 * np.log10(20e6)),
                snr_100m=-(nsd68 + 80),
                pg_20m=10 * np.log10(fs / 2 / 20e6))


if __name__ == "__main__":
    iq = m11_iq()
    ny = m11_nyquist()
    lv = m11_level()
    ad = m11_adc()

    print("\n[본문에 인용할 계산값]")
    print("  I/Q 불균형 -> IRR:", {k: f"{v:.1f} dB" for k, v in iq.items()})
    print("  나이퀴스트:", {k: f"존 {v['zone']}, 앨리어스 {v['alias']:.0f} MHz, "
                          f"{'반전' if v['inverted'] else '정상'}"
                          for k, v in ny.items()})
    print(f"  AGC 범위 {lv['agc_range']:.0f} dB, "
          f"믹서 여유 (강한 신호) {lv['mixer_headroom_strong']:.0f} dB / "
          f"(약한 신호) {lv['mixer_headroom_weak']:.0f} dB")
    print(f"  ADC: NSD {ad['nsd']:.1f} dBFS/Hz, ENOB {ad['enob']:.2f} 비트")
    print(f"    채널 SNR: 1 MHz {ad['snr_1m']:.1f} dB, "
          f"20 MHz {ad['snr_20m']:.1f} dB, 100 MHz {ad['snr_100m']:.1f} dB")
    print(f"    20 MHz 채널의 처리 이득 {ad['pg_20m']:.2f} dB")

    print("\n[자체 검산]")
    ok = []
    ok.append(("IRR 공식이 M09 의 이미지 억압 공식과 같은 형태 "
               "(0.5 dB·10도 -> 20.7 dB)",
               abs(irr_db(0.5, 10.0) - 20.7) < 0.2))
    ok.append(("오차가 0 이면 IRR 이 무한대로", irr_db(0.0, 0.001) > 90))
    ok.append(("2400 MHz @ 500 MSPS -> 10번 존",
               ny["2400"]["zone"] == 10))
    ok.append(("짝수 존이므로 스펙트럼 반전", ny["2400"]["inverted"]))
    ok.append(("2400 MHz 의 앨리어스가 100 MHz",
               abs(ny["2400"]["alias"] - 100.0) < 1e-9))
    ok.append(("2450 MHz 의 앨리어스가 50 MHz",
               abs(ny["2450"]["alias"] - 50.0) < 1e-9))
    ok.append(("600 MHz 도 같은 1차 존으로 접힌다 (100 MHz)",
               abs(ny["600"]["alias"] - 100.0) < 1e-9))
    ok.append(("이상적 14비트 SNR = 86.04 dB",
               abs(6.02 * 14 + 1.76 - 86.04) < 0.01))
    ok.append(("SNR 68 dBFS 는 ENOB 11.0 비트",
               abs(ad["enob"] - 11.0) < 0.01))
    ok.append(("대역폭 1/10 -> 채널 SNR 10 dB 개선",
               abs((ad["snr_1m"] - ad["snr_20m"])
                   - 10 * np.log10(20.0)) < 0.01))
    ok.append(("20 MHz 채널의 처리 이득 = 10.97 dB",
               abs(ad["pg_20m"] - 10.97) < 0.02))
    ok.append(("강한 신호에서도 믹서에 여유가 남는다",
               lv["mixer_headroom_strong"] > 10.0))
    ok.append(("AGC 가 두 경우의 ADC 입력을 같은 자리에 놓는다",
               abs(lv["weak"][-1][1] - lv["strong"][-1][1]) < 1e-9))
    ok.append(("그 자리가 풀스케일보다 10 dB 아래",
               abs(lv["weak"][-1][1] + 10.0) < 1e-9))
    for name, v in ok:
        print(f"  [{'OK ' if v else 'FAIL'}] {name}")
    print(f"\n{'전부 통과' if all(v for _, v in ok) else '검산 실패 항목 있음'}")
