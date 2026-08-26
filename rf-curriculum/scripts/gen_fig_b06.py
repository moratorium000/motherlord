#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B06 (위상잡음과 지터 — 상관 방식과 그 함정) 그림 생성기.

만드는 그림
  B06-1  교차상관이 바닥을 낮추는 정도 (평균 횟수별)
  B06-2  교차 스펙트럼 붕괴 — 분배기 열잡음이 반상관으로 들어올 때
  B06-3  스퍼인가 잡음인가 — 분해대역폭을 바꿔 본다
  B06-4  앨런 편차 — 백색 FM 과 랜덤워크 FM
  B06-5  위상잡음을 지터로 — 누적 적분

교차검증 네 갈래
  ① 교차상관 잔여 바닥의 수치 실험 vs 5·log10(M) 법칙
  ② 붕괴의 수치 실험 vs 닫힌 식 (측정값 = S_dut - S_분배기)
  ③ 앨런 편차: **주파수 영역**의 L(f) 에서 예측한 값 vs **시간 영역**
     시계열에서 계산한 값 (완전히 다른 경로)
  ④ 지터 적분: 구간별 멱함수 닫힌 식 vs 세밀한 격자의 사다리꼴 적분

실행: python3 scripts/gen_fig_b06.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rf_style as S  # noqa: E402

MOD = "B06"
RNG = np.random.default_rng(20260828)

KT_DBM_HZ = -174.0          # 290 K 의 열잡음 밀도
P_CARRIER_DBM = 10.0        # 분배기에 들어가는 반송파 전력


# ══ 교차상관 ════════════════════════════════════════════════════════════
def xcorr_floor_law(m):
    """평균 M 회일 때 바닥이 얼마나 내려가는가 (dB).

    한 채널만 보면 계측기 잡음이 그대로 바닥이다. 두 채널의 교차항은
    평균하면 **1/√M 로 줄어든다.** 전력으로 √M 이므로 dB 로는 5·log10(M).
    """
    return 5.0 * np.log10(np.asarray(m, float))


def xcorr_sim(m, trials=600, n_bin=64, s_dut=0.0, s_inst=1.0, rng=None):
    """교차상관 측정을 그대로 흉내낸다.

    한 번의 평균마다 DUT 성분(두 채널 공통)과 계측기 잡음(각각 독립)을
    새로 뽑아 Y1·conj(Y2) 를 만들고, M 개를 평균한다.
    """
    rng = rng or np.random.default_rng(7)
    out = np.empty(trials)
    for t in range(trials):
        sd = np.sqrt(s_dut / 2) * (rng.normal(size=(m, n_bin))
                                   + 1j * rng.normal(size=(m, n_bin)))
        n1 = np.sqrt(s_inst / 2) * (rng.normal(size=(m, n_bin))
                                    + 1j * rng.normal(size=(m, n_bin)))
        n2 = np.sqrt(s_inst / 2) * (rng.normal(size=(m, n_bin))
                                    + 1j * rng.normal(size=(m, n_bin)))
        cs = np.mean((sd + n1) * np.conj(sd + n2), axis=0)
        out[t] = np.mean(np.abs(cs))
    return float(np.mean(out))


def splitter_pn_dbc(p_dbm=P_CARRIER_DBM, t_k=290.0):
    """분배기 저항의 열잡음이 만드는 등가 위상잡음 밀도 (dBc/Hz).

    열잡음 전력의 절반이 위상 쪽으로 간다(나머지 절반은 진폭).
    L = kT/P - 3 dB.
    """
    ktb = KT_DBM_HZ + 10 * np.log10(t_k / 290.0)
    return ktb - p_dbm - 3.0


def collapse_closed(s_dut_dbc, s_spl_dbc):
    """반상관 성분이 있을 때 화면에 찍히는 값 (dBc/Hz).

    측정값 = S_dut - S_분배기. 두 채널에 **위상이 반대로** 들어오므로
    평균을 아무리 늘려도 안 사라지고 그대로 빠진다.
    """
    sd = 10 ** (np.asarray(s_dut_dbc, float) / 10.0)
    sp = 10 ** (np.asarray(s_spl_dbc, float) / 10.0)
    val = sd - sp
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(val > 0, 10 * np.log10(np.abs(val)), np.nan), val


def collapse_sim(s_dut, s_spl, s_inst=10.0, m=20000, n_bin=256, rng=None):
    """같은 것을 수치로. 계측기 잡음도 넣어 평균으로 지워지는지 함께 본다."""
    rng = rng or np.random.default_rng(3)
    def cg(var, shape):
        return np.sqrt(var / 2) * (rng.normal(size=shape)
                                   + 1j * rng.normal(size=shape))
    sd = cg(s_dut, (m, n_bin))
    sp = cg(s_spl, (m, n_bin))          # 분배기 열잡음: 두 채널에 반대 위상
    n1 = cg(s_inst, (m, n_bin))
    n2 = cg(s_inst, (m, n_bin))
    cs = np.mean((sd + sp + n1) * np.conj(sd - sp + n2), axis=0)
    return float(np.mean(np.real(cs)))


# ══ 스퍼인가 잡음인가 ═══════════════════════════════════════════════════
def rbw_reading(noise_dbc_hz, spur_dbc, rbw_hz):
    """분해대역폭 RBW 에서 화면에 찍히는 값 (dBc/Hz 로 정규화한 뒤).

    잡음은 대역폭에 비례해 커졌다가 정규화로 되돌아와 **RBW 와 무관**하다.
    스퍼는 대역폭과 무관하게 일정한데, 1 Hz 로 나누면 **RBW 만큼 낮아 보인다.**
    """
    rbw = np.asarray(rbw_hz, float)
    noise = 10 ** (np.asarray(noise_dbc_hz, float) / 10.0) * rbw
    spur = 10 ** (np.asarray(spur_dbc, float) / 10.0)
    return 10 * np.log10((noise + spur) / rbw)


# ══ 앨런 편차 ═══════════════════════════════════════════════════════════
def avar_from_phase(x, tau0, ms):
    """위상 시계열 x(초 단위)에서 앨런 분산을 구한다.

    σy²(τ) = <(x_{i+2m} - 2x_{i+m} + x_i)²> / (2τ²)
    """
    out = []
    for m in ms:
        m = int(m)
        d = x[2 * m:] - 2 * x[m:-m] + x[:-2 * m]
        out.append(np.mean(d ** 2) / (2 * (m * tau0) ** 2))
    return np.array(out)


def avar_white_fm(tau, h0):
    """백색 FM 의 닫힌 식. σy²(τ) = h0 / (2τ)."""
    return h0 / (2.0 * np.asarray(tau, float))


def h0_from_pn(f_hz, l_dbc, f0_hz):
    """-20 dB/dec 구간의 L(f) 에서 백색 FM 계수 h0 를 얻는다.

    Sφ = 2L,  Sy = (f/f0)²·Sφ  →  h0 = 2·L(f)·f²/f0²
    **주파수 영역에서 시간 영역 안정도를 예측하는 다리**다.
    """
    lf = 10 ** (np.asarray(l_dbc, float) / 10.0)
    return 2.0 * lf * np.asarray(f_hz, float) ** 2 / f0_hz ** 2


# ══ 위상잡음 → 지터 ═════════════════════════════════════════════════════
# 10 GHz 합성기를 흉내낸 구간별 멱함수 모형 (꺾은점, dBc/Hz)
PN_BREAKS = ((10.0, -55.0), (100.0, -85.0), (1e3, -105.0), (1e4, -115.0),
             (1e5, -120.0), (1e6, -140.0), (1e7, -150.0))
J_BAND_LO = 12e3            # 통신 규격이 흔히 쓰는 적분 하한
J_BAND_HI = 20e6
F0_HZ = 10e9


def pn_db(f):
    """꺾은점 사이를 로그-로그 직선으로 이은 L(f)."""
    f = np.asarray(f, float)
    fb = np.array([b[0] for b in PN_BREAKS])
    lb = np.array([b[1] for b in PN_BREAKS])
    return np.interp(np.log10(f), np.log10(fb), lb)


def seg_integral(f1, f2, l1_db, l2_db):
    """L(f) = L1·(f/f1)^n 인 한 구간의 ∫L df (닫힌 식).

    n ≠ -1 이면 L1·f1^(-n)·(f2^(n+1) - f1^(n+1))/(n+1),
    n = -1 이면 L1·f1·ln(f2/f1).
    """
    l1 = 10 ** (l1_db / 10.0)
    l2 = 10 ** (l2_db / 10.0)
    n = np.log(l2 / l1) / np.log(f2 / f1)
    if abs(n + 1.0) < 1e-12:
        return l1 * f1 * np.log(f2 / f1)
    return l1 * f1 ** (-n) * (f2 ** (n + 1) - f1 ** (n + 1)) / (n + 1)


def phase_var_closed(f_lo, f_hi):
    """구간별 닫힌 식을 이어 붙여 σφ² (rad²) 를 구한다. σφ² = 2∫L df."""
    total = 0.0
    edges = [f_lo] + [b[0] for b in PN_BREAKS if f_lo < b[0] < f_hi] + [f_hi]
    for a, b in zip(edges[:-1], edges[1:]):
        total += seg_integral(a, b, float(pn_db(a)), float(pn_db(b)))
    return 2.0 * total


def phase_var_numeric(f_lo, f_hi, n=2_000_001):
    """같은 것을 세밀한 격자의 사다리꼴 적분으로 (교차검증 ④)."""
    f = np.logspace(np.log10(f_lo), np.log10(f_hi), n)
    return 2.0 * float(np.trapezoid(10 ** (pn_db(f) / 10.0), f))


def jitter_s(phase_var, f0=F0_HZ):
    """rms 위상 흔들림(rad²) 을 시간 지터(초) 로."""
    return np.sqrt(phase_var) / (2 * np.pi * f0)


def spur_jitter_s(spur_dbc, f0=F0_HZ):
    """스퍼 하나가 더하는 지터. σφ² = 2·10^(L/10)."""
    return np.sqrt(2 * 10 ** (np.asarray(spur_dbc, float) / 10.0)) / (2 * np.pi * f0)


# ══ 그림 ════════════════════════════════════════════════════════════════
def fig1_floor():
    fig, ax = S.figure(w=7.6, h=4.6)
    ms = np.array([1, 2, 4, 10, 30, 100, 300, 1000, 3000, 10000])
    law = -xcorr_floor_law(ms)
    sim = np.array([10 * np.log10(xcorr_sim(int(m), trials=200)) for m in ms])
    sim = sim - sim[0]
    ax.semilogx(ms, law, lw=2.4, ls="-", color=S.COLORS[0],
                label=S.txt("-5·log10(M) 법칙"))
    ax.plot(ms, sim, "o", ms=7, ls="none", color=S.ACCENT, mfc="none", mew=1.8,
            label=S.txt("수치 실험"))
    for m in (100, 10000):
        i = int(np.argmax(ms >= m))
        ax.annotate(S.txt(f"M = {m:,} → {law[i]:.0f} dB"),
                    xy=(ms[i], law[i]), xytext=(ms[i] * 0.16, law[i] + 3.2),
                    fontsize=9, color=S.ACCENT, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    ax.set_xlabel(S.txt("평균 횟수 M"))
    ax.set_ylabel(S.txt("계측기 바닥이 내려간 정도 (dB)"))
    S.plain_log(ax, axis="x")
    ax.set_ylim(-24, 4)
    ax.set_title(S.txt("교차상관 — 10배 평균에 5 dB"))
    ax.legend(loc="lower left", fontsize=9)
    fig.tight_layout()
    S.save(fig, MOD, "crosscorr_floor")
    return ms, law, sim


def fig2_collapse():
    fig, (a1, a2) = S.figure(w=11.2, h=4.6, ncols=2)
    spl = splitter_pn_dbc()

    dut = np.linspace(spl - 6.0, spl + 20.0, 400)
    meas, _ = collapse_closed(dut, spl)
    a1.plot(dut, dut, lw=1.8, ls=":", color=S.MUTED,
            label=S.txt("반상관이 없다면 (참값)"))
    S.emph(a1, dut, meas, label=S.txt("실제로 찍히는 값"))
    a1.axvline(spl, color=S.COLORS[0], lw=1.6, ls="--")
    a1.annotate(S.txt(f"분배기 열잡음\n{spl:.0f} dBc/Hz"),
                xy=(spl, spl - 12), xytext=(spl + 8.0, spl - 16),
                fontsize=9, color=S.COLORS[0], fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=S.COLORS[0], lw=1.2))
    for d in (3.0, 6.0, 10.0):
        x = spl + d
        y = float(collapse_closed(x, spl)[0])
        a1.plot(x, y, "o", ms=7, color=S.ACCENT, zorder=7)
        a1.annotate(S.txt(f"{y - x:+.1f} dB"), xy=(x, y),
                    xytext=(x + 0.6, y - 3.4), fontsize=8.5, color=S.ACCENT,
                    fontweight="bold")
    a1.set_xlabel(S.txt("DUT 의 참 위상잡음 (dBc/Hz)"))
    a1.set_ylabel(S.txt("측정값 (dBc/Hz)"))
    a1.set_title(S.txt("붕괴 — 참값에 가까울수록 크게 틀린다"))
    a1.legend(loc="upper left", fontsize=8.5)

    # 평균을 늘리면 나아지는가 — 반상관 성분은 안 사라진다
    ms = np.array([100, 300, 1000, 3000, 10000, 30000])
    for ratio, col, ls in ((10.0, S.COLORS[0], "-"), (3.0, S.COLORS[1], "--")):
        sd, sp = ratio, 1.0
        vals = []
        for m in ms:
            v = collapse_sim(sd, sp, s_inst=30.0, m=int(m), n_bin=64,
                             rng=np.random.default_rng(int(m)))
            vals.append(10 * np.log10(abs(v)) - 10 * np.log10(sd))
        a2.semilogx(ms, vals, lw=2.2, ls=ls, color=col, marker="o", ms=5,
                    label=S.txt(f"DUT 이 분배기보다 {10 * np.log10(ratio):.0f} dB 높을 때"))
        a2.axhline(10 * np.log10((sd - sp) / sd), color=col, lw=1.0, ls=":")
    a2.axhline(0, color=S.MUTED, lw=1.2, ls=":")
    a2.set_xlabel(S.txt("평균 횟수 M"))
    a2.set_ylabel(S.txt("참값 대비 오차 (dB)"))
    S.plain_log(a2, axis="x")
    a2.set_ylim(-4.5, 1.0)
    a2.set_title(S.txt("평균을 늘려도 안 없어진다 — 틀린 값에 수렴한다"))
    a2.legend(loc="lower right", fontsize=8.5)
    fig.tight_layout()
    S.save(fig, MOD, "collapse")
    return spl, {d: float(collapse_closed(spl + d, spl)[0]) - (spl + d)
                 for d in (0.5, 1.0, 3.0, 6.0, 10.0, 20.0)}


def fig3_spur():
    fig, ax = S.figure(w=7.8, h=4.6)
    noise, spur = -120.0, -80.0
    rbws = np.logspace(0, 4, 200)
    ax.semilogx(rbws, rbw_reading(noise, -400.0, rbws), lw=2.4, ls="-",
                color=S.COLORS[0], label=S.txt("잡음만 (RBW 무관)"))
    ax.semilogx(rbws, rbw_reading(-400.0, spur, rbws), lw=2.4, ls="--",
                color=S.COLORS[1], label=S.txt("스퍼만 (RBW 10배에 10 dB)"))
    S.emph(ax, rbws, rbw_reading(noise, spur, rbws),
           label=S.txt("둘이 겹쳐 있을 때"))
    for r in (1.0, 100.0):
        v = float(rbw_reading(noise, spur, r))
        ax.plot(r, v, "o", ms=7, color=S.ACCENT, zorder=7)
        ax.annotate(S.txt(f"RBW {r:.0f} Hz\n{v:.1f} dBc/Hz"), xy=(r, v),
                    xytext=(r * 1.6, v + 9), fontsize=8.5, color=S.ACCENT,
                    fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.1))
    ax.set_xlabel(S.txt("분해대역폭 RBW (Hz)"))
    ax.set_ylabel(S.txt("1 Hz 로 정규화해 찍힌 값 (dBc/Hz)"))
    S.plain_log(ax, axis="x")
    ax.set_ylim(-135, -55)
    ax.set_title(S.txt("RBW 를 바꿔 보면 정체가 드러난다"))
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    S.save(fig, MOD, "spur_vs_noise")
    return noise, spur


def fig4_allan():
    fig, ax = S.figure(w=7.8, h=4.8)
    tau0 = 1e-3
    n = 1 << 21
    sig_y = 2.0e-11                 # 백색 FM 의 표본 표준편차
    sig_w = 4.0e-14                 # 랜덤워크 FM 의 걸음 표준편차
    y = (sig_y * RNG.normal(size=n)
         + np.cumsum(sig_w * RNG.normal(size=n)))
    x = np.cumsum(y) * tau0
    ms = np.unique(np.round(np.logspace(0, 4.6, 26)).astype(int))
    taus = ms * tau0
    adev = np.sqrt(avar_from_phase(x, tau0, ms))
    ax.loglog(taus, adev, "o", ms=6, ls="none", color=S.ACCENT, mfc="none",
              mew=1.7, label=S.txt("시계열에서 계산"))

    h0 = 2 * sig_y ** 2 * tau0
    ax.loglog(taus, np.sqrt(avar_white_fm(taus, h0)), lw=2.0, ls="--",
              color=S.COLORS[0], label=S.txt("백색 FM 닫힌 식  h0/(2tau)"))
    # 랜덤워크 FM 은 τ^(+1/2). 계수는 시뮬레이션 값에서 맞춘다
    i_hi = -1
    c_rw = adev[i_hi] / np.sqrt(taus[i_hi])
    ax.loglog(taus, c_rw * np.sqrt(taus), lw=2.0, ls="-.", color=S.COLORS[2],
              label=S.txt("랜덤워크 FM  tau^(+1/2)"))
    i_min = int(np.argmin(adev))
    ax.plot(taus[i_min], adev[i_min], "*", ms=16, color=S.COLORS[1], zorder=8)
    ax.annotate(S.txt(f"바닥 {adev[i_min]:.2e}\n@ {taus[i_min]:.2f} s"),
                xy=(taus[i_min], adev[i_min]),
                xytext=(taus[i_min] * 0.06, adev[i_min] * 0.45), fontsize=9,
                color=S.COLORS[1], fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=S.COLORS[1], lw=1.2))
    S.plain_log(ax, axis="both")
    ax.set_xlabel(S.txt("평균 시간 tau (s)"))
    ax.set_ylabel(S.txt("앨런 편차 sigma_y(tau)"))
    ax.set_title(S.txt("시간 영역으로 보면 최적 평균 시간이 보인다"))
    ax.legend(loc="lower left", fontsize=8.5)
    fig.tight_layout()
    S.save(fig, MOD, "allan_deviation")
    return tau0, sig_y, h0, taus, adev, ms


def fig5_jitter():
    fig, (a1, a2) = S.figure(w=11.2, h=4.6, ncols=2)
    f = np.logspace(1, 7, 2000)
    a1.semilogx(f, pn_db(f), lw=2.4, ls="-", color=S.COLORS[0])
    for fb, lb in PN_BREAKS:
        a1.plot(fb, lb, "o", ms=5, color=S.ACCENT, zorder=6)
    a1.set_xlabel(S.txt("반송파에서의 이격 (Hz)"))
    a1.set_ylabel(S.txt("L(f) (dBc/Hz)"))
    S.hz_ticks(a1, [1e1, 1e2, 1e3, 1e4, 1e5, 1e6, 1e7])
    a1.set_xlim(10, 1e7)
    a1.set_title(S.txt(f"모형 위상잡음 ({F0_HZ / 1e9:.0f} GHz)"))

    ups = np.logspace(np.log10(10.5), 7, 500)
    cum_all = np.array([jitter_s(phase_var_closed(10.0, float(u)))
                        for u in ups])
    ups2 = ups[ups > J_BAND_LO * 1.01]
    cum_band = np.array([jitter_s(phase_var_closed(J_BAND_LO, float(u)))
                         for u in ups2])
    tot = float(cum_all[-1])
    tot_band = float(jitter_s(phase_var_closed(J_BAND_LO, J_BAND_HI)))
    a2.semilogx(ups, cum_all * 1e15, lw=2.4, ls="-", color=S.COLORS[0],
                label=S.txt("10 Hz 부터 적분"))
    a2.semilogx(ups2, cum_band * 1e15, lw=2.4, ls="--", color=S.COLORS[1],
                label=S.txt(f"{J_BAND_LO / 1e3:.0f} kHz 부터 적분"))
    a2.axhline(tot * 1e15, color=S.COLORS[0], lw=1.0, ls=":")
    a2.axhline(tot_band * 1e15, color=S.COLORS[1], lw=1.0, ls=":")
    a2.annotate(S.txt(f"{tot * 1e15:.0f} fs"),
                xy=(1.2e6, tot * 1e15), xytext=(1.2e6, tot * 1e15 - 22),
                fontsize=10, color=S.COLORS[0], fontweight="bold",
                ha="center",
                arrowprops=dict(arrowstyle="->", color=S.COLORS[0], lw=1.2))
    a2.annotate(S.txt(f"{tot_band * 1e15:.1f} fs\n**같은 소자다**"
                      .replace("**", "")),
                xy=(2e6, tot_band * 1e15), xytext=(1.1e5, tot_band * 1e15 + 34),
                fontsize=10, color=S.COLORS[1], fontweight="bold",
                ha="center",
                arrowprops=dict(arrowstyle="->", color=S.COLORS[1], lw=1.2))
    a2.set_xlabel(S.txt("적분 상한 (Hz)"))
    a2.set_ylabel(S.txt("누적 rms 지터 (fs)"))
    S.hz_ticks(a2, [1e2, 1e3, 1e4, 1e5, 1e6, 1e7])
    a2.set_xlim(10.5, 1e7)
    a2.set_ylim(0, tot * 1e15 * 1.25)
    a2.set_title(S.txt("적분 구간을 안 적으면 숫자가 무의미하다"))
    a2.legend(loc="center left", fontsize=9)
    fig.tight_layout()
    S.save(fig, MOD, "jitter_integration")
    return tot, tot_band, ups, cum_all


# ══ 본문 ════════════════════════════════════════════════════════════════
def main() -> int:
    print("B06 그림 생성")
    print("=" * 62)

    ms_x, law, sim = fig1_floor()
    print(f"  [1] 교차상관 바닥      M=10000 에서 {law[-1]:.1f} dB "
          f"(수치 {sim[-1]:.1f} dB)")

    spl, coll = fig2_collapse()
    print(f"  [2] 붕괴               분배기 열잡음 {spl:.0f} dBc/Hz · "
          f"참값이 +3 dB 위면 {coll[3.0]:+.2f} dB 오차")

    noise, spur = fig3_spur()
    print(f"  [3] 스퍼 판별          잡음 {noise:.0f} dBc/Hz · "
          f"스퍼 {spur:.0f} dBc")

    tau0, sig_y, h0, taus, adev, ms_a = fig4_allan()
    print(f"  [4] 앨런 편차          h0 = {h0:.3e} · "
          f"바닥 {np.min(adev):.3e} @ {taus[int(np.argmin(adev))]:.2f} s")

    tot, tot_band, ups, cum = fig5_jitter()
    print(f"  [5] 지터               10 Hz ~ 10 MHz 적분 "
          f"{tot * 1e15:.1f} fs · {J_BAND_LO / 1e3:.0f} kHz ~ "
          f"{J_BAND_HI / 1e6:.0f} MHz 적분 {tot_band * 1e15:.1f} fs")

    print()
    print("본문에 쓰는 값")
    print("-" * 62)
    for m in (10, 100, 1000, 10000):
        print(f"  평균 {m:6d} 회               바닥 {xcorr_floor_law(m):.1f} dB "
              f"하강")
    print(f"  분배기 열잡음 등가 위상잡음   {spl:.1f} dBc/Hz "
          f"(반송파 {P_CARRIER_DBM:.0f} dBm)")
    for d, e in coll.items():
        print(f"  참값이 분배기보다 {d:4.1f} dB 위   측정 오차 {e:+.2f} dB")
    print(f"  스퍼 판별: RBW 1 Hz -> "
          f"{float(rbw_reading(noise, spur, 1.0)):.1f} dBc/Hz · "
          f"RBW 100 Hz -> {float(rbw_reading(noise, spur, 100.0)):.1f}")
    print(f"  앨런 편차 바닥                {np.min(adev):.3e} "
          f"@ tau = {taus[int(np.argmin(adev))]:.2f} s")
    print(f"  지터 (10 Hz ~ 10 MHz)         {tot * 1e15:.2f} fs")
    print(f"  지터 ({J_BAND_LO / 1e3:.0f} kHz ~ "
          f"{J_BAND_HI / 1e6:.0f} MHz)      {tot_band * 1e15:.2f} fs "
          f"— 같은 소자, {tot / tot_band:.1f}배 차이")
    for lo, hi in ((10.0, 1e2), (1e2, 1e3), (1e3, 1e4),
                   (1e4, 1e5), (1e5, 1e6), (1e6, 1e7)):
        j = float(jitter_s(phase_var_closed(lo, hi)))
        print(f"    {lo:8.0f} ~ {hi:9.0f} Hz 구간   {j * 1e15:6.2f} fs "
              f"({(j / tot) ** 2 * 100:5.1f} % 의 전력)")
    for sp in (-80.0, -70.0, -60.0):
        print(f"  스퍼 {sp:.0f} dBc 하나가 더하는 지터  "
              f"{float(spur_jitter_s(sp)) * 1e15:.2f} fs")

    # ── 자체 검산 ───────────────────────────────────────────────────────
    print()
    print("[자체 검산]")
    ok = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  {'OK ' if cond else 'X  '} {msg}")

    # 교차상관 (교차검증 ①)
    chk(abs(xcorr_floor_law(100) - 10.0) < 1e-12,
        "M = 100 이면 정확히 10 dB (5·log10(100))")
    chk(abs(xcorr_floor_law(10000) - 20.0) < 1e-12,
        "M = 10000 이면 20 dB. 100배 평균에 10 dB 뿐이다")
    err = np.max(np.abs(sim - law))
    chk(err < 0.6,
        f"수치 실험이 법칙에서 최대 {err:.2f} dB 벗어난다")
    chk(sim[-1] < sim[0] - 15,
        f"수치에서도 실제로 내려간다 ({sim[0]:.1f} → {sim[-1]:.1f} dB)")

    # 붕괴 (교차검증 ②)
    chk(abs(splitter_pn_dbc(10.0) - (-187.0)) < 0.01,
        f"반송파 +10 dBm 의 분배기 열잡음 등가 {splitter_pn_dbc(10.0):.1f} dBc/Hz")
    chk(abs(splitter_pn_dbc(20.0) - splitter_pn_dbc(10.0) + 10.0) < 1e-9,
        "반송파를 10 dB 올리면 등가 위상잡음이 10 dB 내려간다")
    for ratio_db in (3.0, 6.0, 10.0, 20.0):
        sd = 10 ** (ratio_db / 10.0)
        num = collapse_sim(sd, 1.0, s_inst=30.0, m=40000, n_bin=64,
                           rng=np.random.default_rng(int(ratio_db * 7)))
        closed = sd - 1.0
        chk(abs(10 * np.log10(num / closed)) < 0.25,
            f"참값이 +{ratio_db:.0f} dB 위: 수치 {10 * np.log10(num):.3f} vs "
            f"닫힌 식 {10 * np.log10(closed):.3f} (dB 단위 상대값)")
    chk(coll[0.5] < -8.0,
        f"참값이 분배기보다 0.5 dB 위면 {coll[0.5]:.1f} dB 나 낮게 찍힌다")
    chk(coll[20.0] > -0.05,
        f"참값이 20 dB 위면 오차가 {coll[20.0]:.3f} dB 로 무시할 만하다")
    chk(np.isnan(collapse_closed(spl - 3.0, spl)[0]),
        "참값이 분배기보다 낮으면 교차 스펙트럼이 음수가 된다 (표시 불가)")

    # 스퍼 판별
    chk(abs(float(rbw_reading(-120.0, -400.0, 1.0))
            - float(rbw_reading(-120.0, -400.0, 1000.0))) < 1e-9,
        "잡음만 있으면 RBW 를 1000배 바꿔도 같은 값이 찍힌다")
    d = (float(rbw_reading(-400.0, -80.0, 1.0))
         - float(rbw_reading(-400.0, -80.0, 100.0)))
    chk(abs(d - 20.0) < 1e-9,
        f"스퍼만 있으면 RBW 100배에 {d:.1f} dB 내려가 보인다")
    chk(float(rbw_reading(-120.0, -80.0, 1.0)) > -80.5,
        "RBW 1 Hz 에서는 스퍼가 잡음을 압도한다")

    # 앨런 편차 (교차검증 ③ — 주파수 영역 예측 vs 시간 영역 계산)
    i_small = ms_a < 30
    pred = np.sqrt(avar_white_fm(taus[i_small], h0))
    rel = np.max(np.abs(adev[i_small] / pred - 1.0))
    chk(rel < 0.08,
        f"짧은 τ 에서 시계열 ADEV 가 백색 FM 닫힌 식과 "
        f"최대 {rel * 100:.1f} % 차이")
    slope_lo = np.polyfit(np.log10(taus[i_small]),
                          np.log10(adev[i_small]), 1)[0]
    chk(abs(slope_lo + 0.5) < 0.06,
        f"짧은 τ 기울기 {slope_lo:+.3f} ≈ -1/2 (백색 FM)")
    i_big = taus > 3.0
    slope_hi = np.polyfit(np.log10(taus[i_big]), np.log10(adev[i_big]), 1)[0]
    chk(abs(slope_hi - 0.5) < 0.15,
        f"긴 τ 기울기 {slope_hi:+.3f} ≈ +1/2 (랜덤워크 FM)")
    # L(f) 에서 h0 를 뽑아 같은 ADEV 가 나오는가
    f_probe = 100.0
    l_probe = 10 * np.log10(h0 * F0_HZ ** 2 / (2 * f_probe ** 2))
    chk(abs(h0_from_pn(f_probe, l_probe, F0_HZ) / h0 - 1.0) < 1e-12,
        "L(f) ↔ h0 변환이 왕복한다 (Sφ=2L, Sy=(f/f0)²Sφ)")

    # 지터 (교차검증 ④)
    for lo, hi in ((10.0, 1e7), (1e3, 1e6), (100.0, 1e4)):
        c = phase_var_closed(lo, hi)
        nnum = phase_var_numeric(lo, hi, n=400_001)
        chk(abs(c / nnum - 1.0) < 2e-3,
            f"{lo:.0f}~{hi:.0e} Hz: 닫힌 식 {jitter_s(c) * 1e15:.3f} fs vs "
            f"수치 {jitter_s(nnum) * 1e15:.3f} fs")
    chk(abs(seg_integral(10.0, 100.0, -60.0, -60.0) - 1e-6 * 90.0) < 1e-15,
        "평평한 구간의 적분은 L × 대역폭 (기울기 0 의 특수해)")
    ratio = (phase_var_closed(10.0, 1e7)
             / phase_var_closed(10.0, 1e3))
    chk(ratio > 1.0, f"적분 상한을 넓히면 지터가 는다 ({ratio:.2f}배 전력)")
    j80 = float(spur_jitter_s(-80.0))
    j70 = float(spur_jitter_s(-70.0))
    chk(abs(j70 / j80 - np.sqrt(10.0)) < 1e-9,
        "스퍼가 10 dB 커지면 그 지터 기여는 √10 배")
    chk(abs(jitter_s(2 * 10 ** (-8.0)) - spur_jitter_s(-80.0)) < 1e-30,
        "스퍼 지터 식이 σφ² = 2·10^(L/10) 과 같다")

    print()
    if not all(ok):
        return 1
    print(f"  검산 {len(ok)}항목 전부 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
