#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B10 (시스템 디버그 — 디센스와 공존) 그림 생성기.

만드는 그림
  B10-1  클럭 하모닉 충돌 지도 — 무엇이 수신 대역에 떨어지는가
  B10-2  디센스의 크기 — 간섭 대 잡음비와 켜기/끄기 실험
  B10-3  상호변조 사냥 — 두 개가 만나 세 번째를 만든다
  B10-4  스프레드 스펙트럼 클럭 — 첨두는 내려가고 총전력은 그대로다

교차검증 네 갈래
  ① 하모닉 충돌: 전수 탐색 vs 나머지 연산 지름길
  ② 디센스: 10·log10(1 + I/N) 닫힌 식 vs 잡음 전력의 직접 합
  ③ 상호변조: 차수별 전수 계산 vs 시간영역 시뮬레이션 스펙트럼의 실제 선
  ④ SSC: 첨두 저감은 RBW 를 따라가지만 **파세발 정리로 총전력은 불변**

실행: python3 scripts/gen_fig_b10.py
"""

from __future__ import annotations

import sys
from itertools import product
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rf_style as S  # noqa: E402

MOD = "B10"
RNG = np.random.default_rng(20260830)

# ── 플랫폼의 클럭들 (MHz) ───────────────────────────────────────────────
CLOCKS_MHZ = {
    "기준 TCXO": 26.0,
    "디스플레이 픽셀": 74.25,
    "메모리 (DDR)": 400.0,
    "카메라 MIPI": 62.5,
    "DC-DC 스위칭": 2.2,
    "USB 기준": 24.0,
}

# ── 수신 대역들 ─────────────────────────────────────────────────────────
RX_BANDS_MHZ = {
    "GNSS L1": (1574.42, 1576.42),
    "LTE B5 하향": (869.0, 894.0),
    "LTE B1 하향": (2110.0, 2170.0),
    "Wi-Fi 2.4 GHz": (2400.0, 2483.5),
    "BLE": (2402.0, 2480.0),
}

# ── 수신기 ──────────────────────────────────────────────────────────────
NF_DB = 5.0
BW_HZ = 1e6
KT_DBM_HZ = -174.0


# ══ 하모닉 충돌 ═════════════════════════════════════════════════════════
def noise_floor_dbm(nf_db=NF_DB, bw_hz=BW_HZ):
    return KT_DBM_HZ + nf_db + 10 * np.log10(bw_hz)


def harmonics_in_band(f_clk, lo, hi, n_max=2000):
    """전수 탐색 — n 을 1 부터 훑어 대역에 드는 것을 모은다."""
    out = []
    for n in range(1, n_max + 1):
        f = n * f_clk
        if lo <= f <= hi:
            out.append((n, f))
        if f > hi:
            break
    return out


def harmonics_in_band_fast(f_clk, lo, hi):
    """같은 것을 나머지 연산으로 (교차검증 ①). n 의 범위를 바로 계산한다."""
    n_lo = int(np.ceil(lo / f_clk - 1e-12))
    n_hi = int(np.floor(hi / f_clk + 1e-12))
    return [(n, n * f_clk) for n in range(max(n_lo, 1), n_hi + 1)]


def collision_map():
    """클럭 × 수신 대역 표. 몇 차 하모닉이 몇 개 떨어지는가."""
    out = {}
    for cname, fc in CLOCKS_MHZ.items():
        for bname, (lo, hi) in RX_BANDS_MHZ.items():
            hits = harmonics_in_band_fast(fc, lo, hi)
            out[(cname, bname)] = hits
    return out


def mix_collisions(f_clk, f_lo, lo, hi, n_max=40, m_max=6):
    """클럭 하모닉이 **국부발진기 하모닉과 섞여** 대역에 떨어지는 경우.

    |n·f_clk ± m·f_LO| 가 수신 대역 안에 오는 조합을 찾는다.
    """
    out = []
    for n in range(1, n_max + 1):
        for m in range(1, m_max + 1):
            for sgn in (+1, -1):
                f = abs(n * f_clk + sgn * m * f_lo)
                if lo <= f <= hi:
                    out.append((n, m, sgn, f))
    return out


# ══ 디센스 ══════════════════════════════════════════════════════════════
def desense_db(i_over_n_db):
    """간섭이 잡음 바닥 대비 얼마일 때 감도가 몇 dB 나빠지는가.

    잡음과 간섭이 무관하면 전력이 더해진다 → 10·log10(1 + I/N).
    """
    r = 10 ** (np.asarray(i_over_n_db, float) / 10.0)
    return 10 * np.log10(1.0 + r)


def i_over_n_for(desense_target_db):
    """거꾸로: 목표 디센스를 만드는 I/N."""
    d = 10 ** (np.asarray(desense_target_db, float) / 10.0)
    return 10 * np.log10(d - 1.0)


SUBSYSTEMS = (
    # (이름, 켰을 때 수신 대역에 더해지는 간섭 전력 [잡음 바닥 대비 dB])
    ("기준 상태 (전부 끔)", None),
    ("디스플레이", -3.0),
    ("메모리 (DDR)", -8.0),
    ("카메라", -14.0),
    ("DC-DC", +1.5),
    ("USB", -11.0),
)


def sensitivity_with(subset):
    """켠 서브시스템들의 간섭을 **전력으로 더해** 감도 열화를 구한다."""
    tot = 0.0
    for name, i_db in SUBSYSTEMS:
        if i_db is None or name not in subset:
            continue
        tot += 10 ** (i_db / 10.0)
    return 10 * np.log10(1.0 + tot)


# ══ 상호변조 ════════════════════════════════════════════════════════════
def im_products(f1, f2, order_max=7):
    """m·f1 ± n·f2 를 차수 |m|+|n| <= order_max 까지 전부."""
    out = []
    for m, n in product(range(-order_max, order_max + 1), repeat=2):
        if m == 0 and n == 0:
            continue
        order = abs(m) + abs(n)
        if order > order_max or order < 2:
            continue
        f = m * f1 + n * f2
        if f > 0:
            out.append((order, m, n, f))
    return sorted(out, key=lambda x: x[3])


def im_sim_spectrum(f1, f2, fs, n=1 << 20, a3=0.02, a5=0.004):
    """같은 것을 시간영역 비선형으로 (교차검증 ③).

    y = x + a3·x³ + a5·x⁵ 를 통과시키고 스펙트럼에 실제로 서는 선을 본다.
    """
    t = np.arange(n) / fs
    x = np.cos(2 * np.pi * f1 * t) + np.cos(2 * np.pi * f2 * t)
    y = x + a3 * x ** 3 + a5 * x ** 5
    w = np.blackman(n)
    sp = np.fft.rfft(y * w) / np.sum(w) * 2
    f = np.fft.rfftfreq(n, 1 / fs)
    return f, 20 * np.log10(np.abs(sp) + 1e-18)


# ══ 스프레드 스펙트럼 클럭 ══════════════════════════════════════════════
def ssc_spectrum(f_carrier, spread_frac, f_mod, fs, n=1 << 20, shape="triangle"):
    """SSC 를 건 하모닉 하나의 스펙트럼.

    주파수를 삼각파로 흔든다. 위상은 그 적분이다.
    """
    t = np.arange(n) / fs
    if shape == "none":
        ph = 2 * np.pi * f_carrier * t
    else:
        # 삼각파의 적분 = 조각별 2차 곡선. 수치 적분으로 만든다
        tri = 2 * np.abs(2 * ((t * f_mod) % 1.0) - 1.0) - 1.0     # -1..+1
        dev = f_carrier * spread_frac * (tri - 1.0) / 2.0          # 아래로만 흔듦
        ph = 2 * np.pi * np.cumsum(f_carrier + dev) / fs
    return np.cos(ph)


def spectrum_db(x, fs, nperseg):
    """분해대역폭이 nperseg 로 정해지는 스펙트럼 (첨두 유지)."""
    from scipy.signal import welch
    f, p = welch(x, fs=fs, nperseg=nperseg, noverlap=nperseg // 2,
                 window="blackmanharris", scaling="spectrum")
    return f, 10 * np.log10(p + 1e-20)


def band_power(x, fs, f_lo, f_hi):
    """대역 안의 총 전력. 파세발 정리로 확인할 값."""
    n = len(x)
    sp = np.fft.rfft(x) / n
    f = np.fft.rfftfreq(n, 1 / fs)
    m = (f >= f_lo) & (f < f_hi)
    return float(2 * np.sum(np.abs(sp[m]) ** 2))


# ══ 그림 ════════════════════════════════════════════════════════════════
def fig1_collision():
    cm = collision_map()
    clocks = list(CLOCKS_MHZ)
    bands = list(RX_BANDS_MHZ)
    grid = np.array([[len(cm[(c, b)]) for b in bands] for c in clocks],
                    float)
    fig, (a1, a2) = S.figure(w=11.8, h=4.8, ncols=2,
                             gridspec_kw={"width_ratios": [1.0, 1.15]})
    im = a1.pcolormesh(np.arange(len(bands) + 1), np.arange(len(clocks) + 1),
                       grid, cmap="YlOrRd", shading="flat", vmin=0,
                       vmax=6)          # DC-DC 한 줄이 눈금을 다 먹지 않게
    for i in range(len(clocks)):
        for j in range(len(bands)):
            v = int(grid[i, j])
            a1.text(j + 0.5, i + 0.5, str(v) if v else "-", ha="center",
                    va="center", fontsize=9.5,
                    color="white" if v >= 5 else S.INK, fontweight="bold")
    a1.set_xticks(np.arange(len(bands)) + 0.5)
    a1.set_xticklabels([S.txt(b) for b in bands], fontsize=8, rotation=25,
                       ha="right")
    a1.set_yticks(np.arange(len(clocks)) + 0.5)
    a1.set_yticklabels([S.txt(f"{c}\n{CLOCKS_MHZ[c]:g} MHz") for c in clocks],
                       fontsize=8)
    a1.invert_yaxis()
    a1.grid(False)
    cb = fig.colorbar(im, ax=a1, extend="max")
    cb.set_label(S.txt("대역에 드는 하모닉 개수"), fontsize=9)
    a1.set_title(S.txt("클럭 x 수신 대역 충돌 지도"))

    # GNSS 대역 근처를 자세히
    lo, hi = RX_BANDS_MHZ["GNSS L1"]
    span = 40.0
    show = ["기준 TCXO", "디스플레이 픽셀", "카메라 MIPI", "DC-DC 스위칭"]
    for cname, col, y in zip(show, (S.COLORS[0], S.COLORS[1], S.COLORS[2],
                                    S.COLORS[4]), (3, 2, 1, 0)):
        fc = CLOCKS_MHZ[cname]
        ns = [n for n in range(1, 3000)
              if lo - span <= n * fc <= hi + span]
        for n in ns:
            f = n * fc
            inside = lo <= f <= hi
            a2.plot([f, f], [y, y + 0.72], lw=2.4 if inside else 1.2,
                    color=S.ACCENT if inside else col,
                    ls="-", zorder=5 if inside else 3)
            if inside:
                a2.annotate(S.txt(f"{n}차"), xy=(f, y + 0.72),
                            xytext=(f, y + 0.95), ha="center", fontsize=8,
                            color=S.ACCENT, fontweight="bold")
        a2.text(lo - span + 1, y + 0.36, S.txt(f"{cname} ({fc:g})"),
                fontsize=8.5, va="center")
    a2.axvspan(lo, hi, color=S.COLORS[2], alpha=0.18, lw=0, zorder=0)
    a2.text((lo + hi) / 2, 4.0, S.txt("GNSS L1"), ha="center", fontsize=9.5,
            color=S.COLORS[2], fontweight="bold")
    a2.set_xlim(lo - span, hi + span)
    a2.set_ylim(-0.2, 4.4)
    a2.set_yticks([])
    a2.grid(False)
    a2.set_xlabel(S.txt("주파수 (MHz)"))
    a2.set_title(S.txt("대역 근처를 펼쳐 보면"))
    fig.tight_layout()
    S.save(fig, MOD, "clock_collision")
    return cm, grid, clocks, bands


def fig2_desense():
    fig, (a1, a2) = S.figure(w=11.4, h=4.6, ncols=2)
    ion = np.linspace(-20, 12, 400)
    a1.plot(ion, desense_db(ion), lw=2.6, ls="-", color=S.COLORS[0])
    for tgt, col in ((1.0, S.COLORS[2]), (3.0, S.COLORS[1]),
                     (6.0, S.ACCENT)):
        x = float(i_over_n_for(tgt))
        a1.plot(x, tgt, "o", ms=8, color=col, zorder=7)
        a1.annotate(S.txt(f"{tgt:.0f} dB 디센스\n= I/N {x:+.1f} dB"),
                    xy=(x, tgt), xytext=(x - 9.5, tgt + 1.4), fontsize=8.5,
                    color=col, fontweight="bold",
                    bbox=dict(fc="white", ec=col, lw=0.8, alpha=0.95, pad=2),
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.1))
    a1.set_xlabel(S.txt("간섭 / 잡음 바닥 (dB)"))
    a1.set_ylabel(S.txt("감도 열화 (dB)"))
    a1.set_ylim(0, 13)
    a1.set_title(S.txt(f"잡음 바닥 {noise_floor_dbm():.0f} dBm "
                       f"(NF {NF_DB:.0f} dB · BW 1 MHz)"))

    names = [n for n, _ in SUBSYSTEMS]
    vals = []
    for i, (name, _) in enumerate(SUBSYSTEMS):
        subset = {n for n, _ in SUBSYSTEMS[1:i + 1]}
        vals.append(sensitivity_with(subset))
    a2.bar(range(len(names)), vals, 0.6,
           color=[S.MUTED] + [S.COLORS[0]] * (len(names) - 1))
    for i, v in enumerate(vals):
        a2.text(i, v + 0.12, f"{v:.2f}", ha="center", fontsize=8.5,
                fontweight="bold")
    delta = [vals[i] - vals[i - 1] for i in range(1, len(vals))]
    iworst = int(np.argmax(delta)) + 1
    a2.annotate(S.txt(f"이 하나가 {delta[iworst - 1]:.2f} dB"),
                xy=(iworst, vals[iworst]), xytext=(iworst - 1.2,
                                                   max(vals) * 0.55),
                fontsize=9, color=S.ACCENT, fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.ACCENT, lw=0.8, alpha=0.95, pad=3),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    a2.set_xticks(range(len(names)))
    a2.set_xticklabels([S.txt(n.replace(" (", "\n(")) for n in names],
                       fontsize=8, rotation=18, ha="right")
    a2.set_ylabel(S.txt("누적 감도 열화 (dB)"))
    a2.set_ylim(0, max(vals) * 1.32)
    a2.set_title(S.txt("하나씩 켜며 더해 간다"))
    fig.tight_layout()
    S.save(fig, MOD, "desense_onoff")
    return dict(zip(names, vals)), delta


def fig3_im():
    f1, f2 = 880.0, 905.0          # MHz — 두 송신
    rx = (925.0, 960.0)            # 수신 대역
    prods = [p for p in im_products(f1, f2, 7) if rx[0] <= p[3] <= rx[1]]
    fig, (a1, a2) = S.figure(w=11.4, h=4.6, ncols=2)

    for order, col in ((2, S.COLORS[2]), (3, S.COLORS[0]), (5, S.COLORS[4]),
                       (7, S.COLORS[1])):
        fs_ = [p[3] for p in im_products(f1, f2, 7) if p[0] == order]
        a1.vlines(fs_, 0, 1, color=col, lw=1.4,
                  label=S.txt(f"{order}차"))
    for f, col in ((f1, S.ACCENT), (f2, S.ACCENT)):
        a1.vlines([f], 0, 1.35, color=col, lw=2.6)
    a1.text(f1, 1.4, S.txt(f"f1 {f1:g}"), ha="center", fontsize=8.5,
            color=S.ACCENT, fontweight="bold")
    a1.text(f2, 1.55, S.txt(f"f2 {f2:g}"), ha="center", fontsize=8.5,
            color=S.ACCENT, fontweight="bold")
    a1.axvspan(rx[0], rx[1], color=S.COLORS[1], alpha=0.16, lw=0)
    a1.text((rx[0] + rx[1]) / 2, 1.4, S.txt("수신 대역"), ha="center",
            fontsize=9, color=S.COLORS[1], fontweight="bold")
    a1.set_xlim(820, 1010)
    a1.set_ylim(0, 1.75)
    a1.set_yticks([])
    a1.set_xlabel(S.txt("주파수 (MHz)"))
    a1.set_title(S.txt(f"7차까지의 모든 조합 — "
                       f"{len(prods)} 개가 대역 안"))
    a1.legend(loc="upper left", fontsize=8.5, ncol=2)

    # 시간영역 시뮬레이션의 실제 선 (교차검증 ③)
    fs = 6000.0
    f, sp = im_sim_spectrum(f1, f2, fs)
    m = (f >= 820) & (f <= 1010)
    a2.plot(f[m], sp[m] - np.max(sp), lw=1.0, ls="-", color=S.COLORS[0])
    for order, col in ((3, S.ACCENT), (5, S.COLORS[4])):
        for p in im_products(f1, f2, 7):
            if p[0] != order or not (820 <= p[3] <= 1010):
                continue
            a2.plot(p[3], -3, "v", ms=7, color=col, zorder=7)
    a2.axvspan(rx[0], rx[1], color=S.COLORS[1], alpha=0.16, lw=0)
    a2.set_xlim(820, 1010)
    a2.set_ylim(-95, 6)
    a2.set_xlabel(S.txt("주파수 (MHz)"))
    a2.set_ylabel(S.txt("상대 세기 (dB)"))
    a2.set_title(S.txt("실제로 서는 선 (삼각형 = 계산이 예측한 자리)"))
    fig.tight_layout()
    S.save(fig, MOD, "im_hunting")
    return f1, f2, rx, prods


def fig4_ssc():
    # SSC 는 **높은 하모닉에서** 효과가 난다. 기준 클럭 자체는 흔들어도
    # 편이량이 변조 주파수와 비슷해 잘 안 퍼진다. 400 MHz 하모닉을 본다.
    fs = 2.0e9
    n = 1 << 21
    f_h = 400.0e6          # 클럭의 어느 하모닉
    spread = 0.01          # 1 % 아래로 흔듦 → 편이 4 MHz
    f_mod = 33e3
    x_off = ssc_spectrum(f_h, 0.0, f_mod, fs, n, shape="none")
    x_on = ssc_spectrum(f_h, spread, f_mod, fs, n)

    fig, (a1, a2) = S.figure(w=11.4, h=4.6, ncols=2)
    for nperseg, ls, alpha in ((1 << 16, "-", 1.0),):
        f, s_off = spectrum_db(x_off, fs, nperseg)
        _, s_on = spectrum_db(x_on, fs, nperseg)
        ref = np.max(s_off)
        m = (f > f_h * 0.985) & (f < f_h * 1.004)
        a1.plot(f[m] / 1e6, s_off[m] - ref, lw=1.8, ls="-",
                color=S.COLORS[1], label=S.txt("SSC 끔"))
        a1.plot(f[m] / 1e6, s_on[m] - ref, lw=1.8, ls="-",
                color=S.COLORS[0], label=S.txt("SSC 켬 (1 %)"))
    a1.set_xlabel(S.txt("주파수 (MHz)"))
    a1.set_ylabel(S.txt("상대 세기 (dB)"))
    a1.set_ylim(-60, 6)
    a1.set_title(S.txt(f"{f_h / 1e6:.0f} MHz 하모닉을 RBW {fs / (1 << 16) / 1e3:.0f} kHz 로 본 것"))
    a1.legend(loc="upper left", fontsize=9)

    # RBW 를 바꿔 가며 첨두 저감 / 그리고 대역 총전력
    rbws, peaks = [], []
    for nperseg in (1 << 12, 1 << 14, 1 << 16, 1 << 18, 1 << 20):
        f, s_off = spectrum_db(x_off, fs, nperseg)
        _, s_on = spectrum_db(x_on, fs, nperseg)
        band = (f > f_h * 0.982) & (f < f_h * 1.006)
        rbws.append(fs / nperseg)
        peaks.append(np.max(s_on[band]) - np.max(s_off[band]))
    a2.semilogx(np.array(rbws) / 1e3, peaks, lw=2.4, ls="-",
                color=S.COLORS[0], marker="o", ms=6,
                label=S.txt("첨두 저감"))
    p_off = band_power(x_off, fs, f_h * 0.975, f_h * 1.008)
    p_on = band_power(x_on, fs, f_h * 0.975, f_h * 1.008)
    tot_db = 10 * np.log10(p_on / p_off)
    a2.axhline(tot_db, color=S.ACCENT, lw=2.2, ls="--")
    a2.annotate(S.txt(f"대역 총전력 변화 {tot_db:+.2f} dB\n"
                      f"— 에너지는 어디 안 갔다"),
                xy=(30, tot_db), xytext=(30, tot_db - 11), fontsize=9,
                color=S.ACCENT, fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.ACCENT, lw=0.8, alpha=0.95, pad=3),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    a2.axvline(f_mod / 1e3, color=S.COLORS[2], lw=1.6, ls=":")
    a2.annotate(S.txt(f"변조 주파수 {f_mod / 1e3:.0f} kHz\n"
                      f"— 이 아래로는 안 늘어난다"),
                xy=(f_mod / 1e3, -19), xytext=(f_mod / 1e3 * 0.6, -27),
                fontsize=9, color=S.COLORS[2], fontweight="bold",
                ha="center",
                bbox=dict(fc="white", ec=S.COLORS[2], lw=0.8, alpha=0.95,
                          pad=3),
                arrowprops=dict(arrowstyle="->", color=S.COLORS[2], lw=1.2))
    a2.set_xlabel(S.txt("분해대역폭 RBW (kHz)"))
    a2.set_ylabel(S.txt("SSC 로 얻은 값 (dB)"))
    S.plain_log(a2, axis="x")
    a2.set_ylim(-34, 6)
    a2.set_title(S.txt("좁게 볼수록 많이 벌어 보인다"))
    a2.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    S.save(fig, MOD, "ssc_tradeoff")
    return dict(zip([r / 1e3 for r in rbws], peaks)), tot_db


# ══ 본문 ════════════════════════════════════════════════════════════════
def main() -> int:
    print("B10 그림 생성")
    print("=" * 62)

    cm, grid, clocks, bands = fig1_collision()
    print(f"  [1] 충돌 지도          전체 {int(grid.sum())} 건 · "
          f"가장 많은 클럭 {clocks[int(np.argmax(grid.sum(axis=1)))]}")

    sens, delta = fig2_desense()
    print(f"  [2] 디센스             전부 켜면 {max(sens.values()):.2f} dB · "
          f"최악 하나 {max(delta):.2f} dB")

    f1, f2, rx, prods = fig3_im()
    print(f"  [3] 상호변조           {f1:g} 와 {f2:g} MHz 로 "
          f"{rx[0]:g}~{rx[1]:g} 대역에 {len(prods)} 개")

    peaks, tot_db = fig4_ssc()
    print("  [4] SSC                첨두 저감 = " +
          ", ".join(f"RBW {k:.1f}kHz {v:.1f}dB" for k, v in peaks.items()) +
          f" · 총전력 {tot_db:+.2f} dB")

    print()
    print("본문에 쓰는 값")
    print("-" * 62)
    print(f"  수신 잡음 바닥                {noise_floor_dbm():.1f} dBm "
          f"(NF {NF_DB:.0f} dB · BW 1 MHz)")
    for d in (0.5, 1.0, 3.0, 6.0, 10.0):
        print(f"  디센스 {d:4.1f} dB 를 만드는 I/N   "
              f"{float(i_over_n_for(d)):+6.2f} dB "
              f"(= {noise_floor_dbm() + float(i_over_n_for(d)):.1f} dBm)")
    for (c, b), hits in sorted(cm.items()):
        if hits:
            print(f"  {c:14s} → {b:14s} {len(hits)} 개 "
                  f"({', '.join(f'{n}차 {f:.2f} MHz' for n, f in hits[:3])})")
    for name, v in sens.items():
        print(f"  {name:20s} 누적 열화 {v:5.2f} dB")
    print(f"  상호변조: 7차까지 전체 조합    "
          f"{len(im_products(f1, f2, 7))} 개 · 수신 대역 안 {len(prods)} 개")
    for order, m, n, f in prods[:6]:
        sign = "+" if n >= 0 else "-"
        print(f"    {order}차  {m:+d}·f1 {sign} {abs(n)}·f2 = {f:.1f} MHz")
    for k, v in peaks.items():
        print(f"  SSC 첨두 저감 (RBW {k:7.1f} kHz)  {v:6.2f} dB")
    print(f"  SSC 대역 총전력 변화           {tot_db:+.3f} dB")

    # ── 자체 검산 ───────────────────────────────────────────────────────
    print()
    print("[자체 검산]")
    ok = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  {'OK ' if cond else 'X  '} {msg}")

    # 하모닉 (교차검증 ①)
    for cname, fc in CLOCKS_MHZ.items():
        for bname, (lo, hi) in RX_BANDS_MHZ.items():
            a = harmonics_in_band(fc, lo, hi, n_max=5000)
            b = harmonics_in_band_fast(fc, lo, hi)
            if a != b:
                chk(False, f"{cname} x {bname}: 전수 {a} vs 지름길 {b}")
                break
    else:
        chk(True, f"클럭 {len(CLOCKS_MHZ)} x 대역 {len(RX_BANDS_MHZ)} = "
                  f"{len(CLOCKS_MHZ) * len(RX_BANDS_MHZ)} 조합에서 "
                  f"전수 탐색과 나머지 연산이 정확히 일치")
    chk(len(harmonics_in_band_fast(26.0, 1574.42, 1576.42)) == 0,
        "26 MHz 의 하모닉은 GNSS L1 에 안 떨어진다 (1560·1586 사이)")
    chk(len(harmonics_in_band_fast(2.2, 1574.42, 1576.42)) >= 1,
        f"2.2 MHz 스위칭은 2.2 MHz 마다 선이 서므로 폭 2 MHz 인 GNSS 대역에도 "
        f"{len(harmonics_in_band_fast(2.2, 1574.42, 1576.42))} 개가 들어온다")
    mixes = mix_collisions(26.0, 1550.0, 1574.42, 1576.42)
    chk(len(mixes) > 0,
        f"직접 하모닉이 없어도 국부발진기와 섞이면 {len(mixes)} 조합이 들어온다")

    # 디센스 (교차검증 ②)
    for d in (0.5, 1.0, 3.0, 6.0):
        r = float(i_over_n_for(d))
        chk(abs(float(desense_db(r)) - d) < 1e-9,
            f"I/N {r:+.2f} dB → 디센스 {float(desense_db(r)):.3f} dB (목표 {d})")
    chk(abs(float(desense_db(0.0)) - 3.0103) < 1e-3,
        "간섭이 잡음과 같으면 정확히 3.01 dB")
    chk(float(i_over_n_for(1.0)) < -5.0,
        f"1 dB 만 나빠지게 하려면 I/N 이 {float(i_over_n_for(1.0)):.2f} dB — "
        f"잡음보다 한참 작아도 보인다")
    # 켠 것을 전력으로 더한 값이 개별 합과 맞는가
    all_on = sensitivity_with({n for n, v in SUBSYSTEMS if v is not None})
    lin = sum(10 ** (v / 10.0) for _, v in SUBSYSTEMS if v is not None)
    chk(abs(all_on - 10 * np.log10(1 + lin)) < 1e-12,
        f"전부 켠 열화 {all_on:.4f} dB = 전력 합으로 계산한 값")
    chk(all_on < sum(sensitivity_with({n}) for n, v in SUBSYSTEMS
                     if v is not None),
        "dB 를 그냥 더하면 과대평가한다 (전력으로 더해야 한다)")

    # 상호변조 (교차검증 ③)
    fs = 6000.0
    f, sp = im_sim_spectrum(f1, f2, fs)
    for order in (3, 5):
        for p in im_products(f1, f2, 7):
            if p[0] != order or not (830 <= p[3] <= 1000):
                continue
            k = int(np.argmin(np.abs(f - p[3])))
            local = sp[max(0, k - 3):k + 4]
            floor = np.median(sp[(f > 830) & (f < 1000)])
            chk(np.max(local) > floor + 20,
                f"{order}차 {p[1]:+d}f1{p[2]:+d}f2 = {p[3]:.1f} MHz 에 "
                f"실제로 선이 선다 (바닥 대비 "
                f"{np.max(local) - floor:.0f} dB)")
    chk(all(p[0] % 2 == 1 for p in prods),
        "수신 대역에 든 것이 전부 홀수 차 — 짝수 차는 멀리 떨어진다")
    chk(im_products(f1, f2, 3) == [p for p in im_products(f1, f2, 7)
                                   if p[0] <= 3],
        "차수 제한이 제대로 걸린다")

    # SSC (교차검증 ④)
    chk(abs(tot_db) < 0.15,
        f"SSC 를 켜도 대역 총전력은 {tot_db:+.3f} dB 로 그대로다 "
        f"(파세발)")
    ks = sorted(peaks)
    chk(peaks[ks[0]] < peaks[ks[-1]],
        f"좁은 RBW 일수록 저감이 커 보인다 "
        f"({peaks[ks[0]]:.1f} dB @ {ks[0]:.1f} kHz vs "
        f"{peaks[ks[-1]]:.1f} dB @ {ks[-1]:.1f} kHz)")
    chk(peaks[ks[0]] < -15,
        f"가장 좁은 RBW({ks[0]:.1f} kHz)에서 {peaks[ks[0]]:.1f} dB 나 "
        f"벌어 보인다")
    chk(peaks[ks[-1]] > peaks[ks[0]] + 8,
        f"넓은 RBW({ks[-1]:.0f} kHz)에서는 {peaks[ks[-1]]:.1f} dB 뿐 — "
        f"수신 대역이 넓으면 소용없다")
    # RBW 를 좁히면 저감이 커지지만, 변조 주파수(33 kHz) 아래로 가면 멈춘다.
    # 스펙트럼이 33 kHz 간격의 빗으로 분해되기 때문이다.
    chk(abs(peaks[ks[0]] - peaks[ks[1]]) < 0.4,
        f"RBW 를 {ks[1]:.1f} → {ks[0]:.1f} kHz 로 더 좁혀도 저감이 "
        f"{peaks[ks[1]]:.2f} → {peaks[ks[0]]:.2f} dB 로 **멈춘다** "
        f"(변조 주파수 33 kHz 아래)")
    wide = sorted(k for k in peaks if k > 100)
    chk(abs(abs(peaks[wide[0]] - peaks[wide[-1]])
            - 10 * np.log10(wide[-1] / wide[0])) < 1.5,
        f"넓은 쪽에서는 규칙을 따른다: RBW {wide[-1]:.0f} → {wide[0]:.0f} kHz "
        f"에 {abs(peaks[wide[0]] - peaks[wide[-1]]):.2f} dB 더 벌어진다 "
        f"(10log10 비 {10 * np.log10(wide[-1] / wide[0]):.2f})")
    sat = 10 * np.log10(400.0e6 * 0.01 / 33e3)   # 편이 4 MHz / 변조 33 kHz
    chk(abs(abs(peaks[ks[0]]) - sat) < 4.0,
        f"포화값 {abs(peaks[ks[0]]):.1f} dB ≈ 10log10(편이/변조주파수) "
        f"{sat:.1f} dB")

    print()
    if not all(ok):
        return 1
    print(f"  검산 {len(ok)}항목 전부 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
