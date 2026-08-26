#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B03 (다포트·차동 S-파라미터와 픽스처 제거) 그림 생성기.

만드는 그림
  B03-2  차동 쌍의 길이 어긋남이 만드는 모드 변환
  B03-4  2x-Thru 디임베딩 — 두 반쪽이 다르면 무슨 일이 생기는가
  B03-5  S-파라미터 파일 품질 — 수동성과 인과성

교차검증 두 갈래
  · 혼합모드 변환을 **손으로 구현한 것**과 `scikit-rf` 의 se2gmm 을 대조
  · 모드 변환의 닫힌 식 |Sdc21| = |sin(π f Δτ)| 를 수치 결과와 대조

실행: python3 scripts/gen_fig_b03.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import skrf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rf_style as S  # noqa: E402

MOD = "B03"

C0 = 299_792_458.0
EPS_EFF = 3.3            # FR-4 마이크로스트립의 유효 유전율 (대략)
V_PROP = C0 / np.sqrt(EPS_EFF)

SKEWS_PS = (1.0, 5.0, 20.0)
F_MARK = 5e9             # 본문이 인용하는 주파수


# ── 혼합모드 변환 (손으로 구현) ─────────────────────────────────────────
def se2mm(s4):
    """단일단 4포트 S 를 혼합모드로 바꾼다.

    포트 순서는 (1+, 1-, 2+, 2-) 이다. 변환 행렬 M 은 차동/공통 좌표로
    가는 직교 변환이고, 결과 순서는 (d1, d2, c1, c2) 로 둔다 —
    `scikit-rf` 의 se2gmm 과 같은 배치라 그대로 대조할 수 있다.
    """
    r2 = 1.0 / np.sqrt(2.0)
    M = r2 * np.array([
        [1, -1, 0, 0],     # d1
        [0, 0, 1, -1],     # d2
        [1, 1, 0, 0],      # c1
        [0, 0, 1, 1],      # c2
    ], dtype=float)
    Mi = np.linalg.inv(M)
    return np.einsum("ij,fjk,kl->fil", M, s4, Mi)


def skewed_pair(freq, tau_a, tau_b):
    """결합 없는 두 이상적 선로로 만든 차동 쌍. 포트 (1+,1-,2+,2-)."""
    w = 2 * np.pi * freq.f
    s = np.zeros((len(freq), 4, 4), dtype=complex)
    s[:, 2, 0] = s[:, 0, 2] = np.exp(-1j * w * tau_a)   # + 쪽 선
    s[:, 3, 1] = s[:, 1, 3] = np.exp(-1j * w * tau_b)   # - 쪽 선
    return skrf.Network(frequency=freq, s=s)


def sdc21_closed(f_hz, skew_s):
    """모드 변환의 닫힌 식.

    Sdc21 = ½(e^{-jωτa} - e^{-jωτb}) 이므로 크기는 |sin(ω Δτ / 2)|,
    즉 |sin(π f Δτ)| 이다. **평균 지연과 무관하고 어긋난 양만으로 정해진다.**
    """
    return np.abs(np.sin(np.pi * np.asarray(f_hz, float) * skew_s))


def skew_for(db, f_hz=F_MARK):
    """목표 모드 변환(dB)을 넘지 않으려면 지연 차가 얼마여야 하는가.

    |Sdc21| = |sin(π f Δτ)| 를 Δτ 에 대해 푼 것. 본문과 확인 문제가 이
    역산을 쓰므로 여기서 계산해 검산까지 걸어 둔다.
    """
    lin = 10 ** (np.asarray(db, float) / 20.0)
    tau = np.arcsin(np.clip(lin, 0, 1)) / (np.pi * f_hz)
    return tau, tau * V_PROP * 1e3          # (초, mm)


def fig_skew():
    S.setup()
    fig, ax = S.figure(7.2, 4.3)
    f = np.linspace(0.1e9, 20e9, 800)
    rows = []
    for i, ps in enumerate(SKEWS_PS):
        conv = sdc21_closed(f, ps * 1e-12)
        ax.plot(f / 1e9, 20 * np.log10(np.clip(conv, 1e-6, None)),
                color=S.COLORS[i], ls=S.DASHES[i], lw=2.0,
                label=S.txt(f"{ps:g} ps  ({ps * 1e-12 * V_PROP * 1e3:.2f} mm)"))
        v = float(sdc21_closed(F_MARK, ps * 1e-12))
        rows.append((ps, ps * 1e-12 * V_PROP * 1e3, 20 * np.log10(v)))
        ax.plot([F_MARK / 1e9], [20 * np.log10(v)], "o", ms=7,
                color=S.COLORS[i], zorder=6)

    ax.axvline(F_MARK / 1e9, color=S.MUTED, ls=":", lw=1.0)
    ax.text(F_MARK / 1e9 + 0.3, -58, S.txt("5 GHz"), fontsize=9,
            color=S.MUTED)
    S.limit_line(ax, -30, S.txt("흔히 잡는 목표 -30 dB"), side="upper")
    ax.set_xlabel(S.txt("주파수 (GHz)"))
    ax.set_ylabel(S.txt("모드 변환 |Sdc21| (dB)"))
    ax.set_title(S.txt("그림 B03-2  길이가 어긋나면 차동이 공통으로 샌다"))
    ax.set_xlim(0, 20)
    ax.set_ylim(-60, 3)
    ax.legend(loc="lower right", fontsize=9, title=S.txt("두 선의 지연 차"))
    S.save(fig, MOD, "skew_mode_conversion")
    return rows


# ── 픽스처와 2x-Thru ────────────────────────────────────────────────────
def tline(freq, length_m, a_db_per_m_at_1g=6.0):
    """정합된 손실 선로. 손실은 √f 로 늘어나는 도체 손실만 넣는다."""
    w = 2 * np.pi * freq.f
    beta = w / V_PROP
    a_np = (a_db_per_m_at_1g / 8.686) * np.sqrt(freq.f / 1e9)
    gl = (a_np + 1j * beta) * length_m
    s = np.zeros((len(freq), 2, 2), dtype=complex)
    s[:, 1, 0] = s[:, 0, 1] = np.exp(-gl)
    return skrf.Network(frequency=freq, s=s)


def shunt_c(freq, c_f, z0=50.0):
    """선로에 병렬로 걸린 커패시터 — 커넥터 런치의 불연속을 흉내낸다."""
    y = 1j * 2 * np.pi * freq.f * c_f
    s = np.zeros((len(freq), 2, 2), dtype=complex)
    s[:, 0, 0] = s[:, 1, 1] = -y * z0 / (2 + y * z0)
    s[:, 1, 0] = s[:, 0, 1] = 2 / (2 + y * z0)
    return skrf.Network(frequency=freq, s=s)


def half_fixture(freq, length_mm, c_pf):
    """픽스처 반쪽 = 커넥터 불연속 + 선로."""
    return shunt_c(freq, c_pf * 1e-12) ** tline(freq, length_mm * 1e-3)


def attenuator(freq, db):
    a = 10 ** (-db / 20.0)
    s = np.zeros((len(freq), 2, 2), dtype=complex)
    s[:, 1, 0] = s[:, 0, 1] = a
    return skrf.Network(frequency=freq, s=s)


def averaged_half(freq, la, ca, lb, cb):
    """2x-Thru 가 내놓는 "한쪽 반쪽"을 두 반쪽의 평균으로 본다.

    실제 자동 픽스처 제거(AFR)는 시간영역으로 가르고 임피던스 프로파일까지
    살리지만, **양쪽에 같은 것을 쓴다**는 점은 같다. 쿠폰의 반쪽 하나를
    뽑아 양쪽에 쓰는 것이므로, 실제 두 반쪽이 다르면 그 차이는 결과에
    남는다. 여기서는 그 성질만 남긴 가장 단순한 형태로 둔다 — 두 반쪽이
    같으면(la=lb, ca=cb) 이 모형은 **정확**하고, 오차는 오직 비대칭에서만
    나온다. 임피던스 프로파일을 흉내내지 못하는 더 거친 근사를 쓰면
    "비대칭 때문에 생긴 오차"와 "근사가 거칠어서 생긴 오차"가 섞여
    무엇을 보고 있는지 알 수 없게 된다.
    """
    return half_fixture(freq, (la + lb) / 2.0, (ca + cb) / 2.0)


def deembed(meas, left, right):
    """양쪽 픽스처를 벗긴다. 오른쪽은 뒤집어서 물린다."""
    return left.inv ** meas ** right.flipped().inv


def fig_deembed():
    """두 가지를 나란히 본다.

    (a) 표준의 실제 구현 두 가지 — scikit-rf 의 IEEE 370 NZC 와 ZC.
        불연속이 큰 픽스처에서 둘이 갈린다.
    (b) 비대칭만 떼어 본 것 — 두 반쪽이 다르면 얼마가 남는가.
        여기는 알고리즘의 근사 오차가 섞이지 않도록 단순 모형을 쓴다.
    """
    import warnings
    from skrf.calibration.deembedding import (IEEEP370_SE_NZC_2xThru,
                                              IEEEP370_SE_ZC_2xThru)
    S.setup()

    # DC 의 정수배 격자여야 시간영역 분할이 제대로 돈다
    fq = skrf.Frequency.from_f(np.arange(1, 2001) * 10e6, unit="hz")
    dut = attenuator(fq, 6.0)

    # 런치 불연속이 뚜렷한 픽스처 (60 mm, 0.10 pF)
    hard = shunt_c(fq, 0.10e-12) ** tline(fq, 60e-3, 12.0)
    meas = hard ** dut ** hard.flipped()
    coupon = hard ** hard.flipped()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        nzc = IEEEP370_SE_NZC_2xThru(dummy_2xthru=coupon,
                                     name="nzc").deembed(meas)
        zc = IEEEP370_SE_ZC_2xThru(dummy_2xthru=coupon,
                                   dummy_fix_dut_fix=meas,
                                   name="zc").deembed(meas)

    fig, (ax1, ax2) = S.figure(7.8, 3.9, ncols=2)
    fg = fq.f / 1e9
    d_nzc = 20 * np.log10(np.abs(nzc.s[:, 1, 0])) + 6.0
    d_zc = 20 * np.log10(np.abs(zc.s[:, 1, 0])) + 6.0
    ax1.plot(fg, d_nzc, color=S.COLORS[1], ls="--", lw=1.8,
             label=S.txt("임피던스 보정 없음"))
    ax1.plot(fg, d_zc, color=S.COLORS[0], ls="-", lw=1.8,
             label=S.txt("임피던스 보정"))
    ax1.axhline(0, color=S.ACCENT, lw=1.2)
    ax1.axvspan(19, 20, color="#F2F2F2", zorder=0)
    ax1.text(19.5, 3.1, S.txt("대역 끝\n5 %"), ha="center", fontsize=8.5,
             color=S.MUTED)
    ax1.set_xlabel(S.txt("주파수 (GHz)"))
    ax1.set_ylabel(S.txt("참값과의 차 (dB)"))
    ax1.set_title(S.txt("(a) 표준의 두 방법 — 어느 쪽도 공짜가 아니다"),
                  fontsize=10)
    ax1.legend(fontsize=8, loc="upper left")
    ax1.set_ylim(-1.0, 4.0)
    ax1.set_xlim(0, 20)

    inb = fg <= 19.0
    e_nzc = float(np.max(np.abs(d_nzc)))
    e_nzc_in = float(np.max(np.abs(d_nzc[inb])))
    e_zc = float(np.max(np.abs(d_zc)))
    e_zc_in = float(np.max(np.abs(d_zc[inb])))
    e_raw = float(np.max(np.abs(20 * np.log10(np.abs(meas.s[:, 1, 0])) + 6)))

    # (b) 비대칭만 — 알고리즘 근사가 섞이지 않는 단순 모형
    fr = skrf.Frequency(0.05, 20, 800, "ghz")
    d2 = attenuator(fr, 6.0)
    LA, CA, LB, CB = 25.0, 0.25, 27.0, 0.35
    a = half_fixture(fr, LA, CA)
    b = half_fixture(fr, LB, CB)
    m2 = a ** d2 ** b.flipped()
    ideal = deembed(m2, a, b)
    x = averaged_half(fr, LA, CA, LB, CB)
    got = deembed(m2, x, x)
    err_ideal = 20 * np.log10(np.abs(ideal.s[:, 1, 0])) + 6.0
    err_avg = 20 * np.log10(np.abs(got.s[:, 1, 0])) + 6.0

    ax2.plot(fr.f / 1e9, err_avg, color=S.COLORS[1], ls="--", lw=1.8,
             label=S.txt("한쪽 반쪽을 양쪽에 씀"))
    ax2.plot(fr.f / 1e9, err_ideal, color=S.COLORS[0], ls="-", lw=1.8,
             label=S.txt("두 반쪽을 각각 알고 벗김"))
    ax2.axhline(0, color=S.MUTED, ls=":", lw=1.0)
    ax2.set_xlabel(S.txt("주파수 (GHz)"))
    ax2.set_ylabel(S.txt("참값과의 차 (dB)"))
    ax2.set_title(S.txt("(b) 두 반쪽이 다를 때만 생기는 오차"), fontsize=10)
    ax2.legend(fontsize=8, loc="lower left")

    fig.suptitle(S.txt("그림 B03-4  픽스처를 벗기고 남는 것"),
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    S.save(fig, MOD, "deembed_2xthru")
    return dict(raw=e_raw, nzc=e_nzc, zc=e_zc,
                nzc_in=e_nzc_in, zc_in=e_zc_in,
                err_ideal=float(np.max(np.abs(err_ideal))),
                err_avg=float(np.max(np.abs(err_avg))),
                s11_avg=float(np.max(np.abs(got.s[:, 0, 0]))),
                s11_ideal=float(np.max(np.abs(ideal.s[:, 0, 0]))))


# ── S-파라미터 파일 품질 ────────────────────────────────────────────────
def max_sv(net):
    """각 주파수에서 S 의 최대 특이값. 1 을 넘으면 수동성 위반이다."""
    return np.array([np.linalg.svd(sm, compute_uv=False).max()
                     for sm in net.s])


def precursor_ratio(freq_hz, s21, n_fft=4096):
    """임펄스 응답에서 t < 0 쪽에 있는 에너지의 비율.

    인과적인 물건이면 0 에 가깝다. 이 값이 크면 그 파일은 물리적으로
    불가능한 응답을 담고 있다 — 보통 디임베딩을 과하게 한 흔적이다.
    """
    f = np.asarray(freq_hz, float)
    df = f[1] - f[0]
    n_pos = int(round(f[-1] / df)) + 1
    spec = np.zeros(n_pos, dtype=complex)
    idx = np.round(f / df).astype(int)
    spec[idx] = s21
    h = np.fft.irfft(spec, n=n_fft)
    neg = h[n_fft // 2:]                 # FFT 배치에서 뒤쪽 절반이 음의 시간
    return float(np.sum(neg ** 2) / np.sum(h ** 2))


def fig_quality():
    S.setup()
    freq = skrf.Frequency(0.05, 20, 400, "ghz")

    good = half_fixture(freq, 25.0, 0.25) ** attenuator(freq, 3.0)
    # 나쁜 예: 이득이 생긴 것처럼 S 를 부풀린다 (디임베딩 과보정의 전형)
    bad = good.copy()
    bump = 1.0 + 0.5 * np.exp(-((freq.f - 12e9) / 2.5e9) ** 2)
    bad.s[:, 1, 0] *= bump
    bad.s[:, 0, 1] *= bump

    fig, (ax1, ax2) = S.figure(7.6, 3.9, ncols=2)
    fg = freq.f / 1e9
    ax1.plot(fg, max_sv(good), color=S.COLORS[0], ls="-", lw=1.9,
             label=S.txt("정상 파일"))
    ax1.plot(fg, max_sv(bad), color=S.COLORS[1], ls="--", lw=1.9,
             label=S.txt("과보정된 파일"))
    S.limit_line(ax1, 1.0, S.txt("수동성 한계 1.0"), side="upper")
    ax1.set_xlabel(S.txt("주파수 (GHz)"))
    ax1.set_ylabel(S.txt("S 의 최대 특이값"))
    ax1.set_title(S.txt("(a) 수동성 — 1 을 넘으면 없는 에너지가 나온 것"),
                  fontsize=10)
    ax1.legend(fontsize=8, loc="upper left")

    # 인과성: 지연을 음수로 준 가짜 파일과 정상 파일의 임펄스 응답
    w = 2 * np.pi * freq.f
    causal = np.exp(-1j * w * 200e-12) * np.exp(-freq.f / 6e10)
    acausal = np.exp(+1j * w * 200e-12) * np.exp(-freq.f / 6e10)
    rc = precursor_ratio(freq.f, causal)
    ra = precursor_ratio(freq.f, acausal)
    n_fft = 4096
    df = freq.f[1] - freq.f[0]
    t = (np.arange(n_fft) - n_fft // 2) / (n_fft * df) * 1e9

    def imp(s21):
        n_pos = int(round(freq.f[-1] / df)) + 1
        spec = np.zeros(n_pos, dtype=complex)
        spec[np.round(freq.f / df).astype(int)] = s21
        return np.fft.fftshift(np.fft.irfft(spec, n=n_fft))

    ax2.plot(t, imp(causal) / np.max(np.abs(imp(causal))),
             color=S.COLORS[0], ls="-", lw=1.6,
             label=S.txt(f"인과적 (앞선 에너지 {rc:.1e})"))
    ax2.plot(t, imp(acausal) / np.max(np.abs(imp(acausal))),
             color=S.COLORS[1], ls="--", lw=1.6,
             label=S.txt(f"비인과적 (앞선 에너지 {ra:.2f})"))
    ax2.axvline(0, color=S.ACCENT, ls="-", lw=1.2)
    ax2.text(0.05, 0.95, S.txt("t = 0"), color=S.ACCENT, fontsize=9,
             fontweight="bold")
    ax2.set_xlabel(S.txt("시간 (ns)"))
    ax2.set_ylabel(S.txt("임펄스 응답 (정규화)"))
    ax2.set_title(S.txt("(b) 인과성 — t < 0 에 응답이 있으면 안 된다"),
                  fontsize=10)
    ax2.set_xlim(-1.0, 1.0)
    ax2.legend(fontsize=8, loc="upper left")

    fig.suptitle(S.txt("그림 B03-5  파일을 쓰기 전에 세 가지를 본다"),
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    S.save(fig, MOD, "sparam_quality")
    return dict(sv_good=float(max_sv(good).max()),
                sv_bad=float(max_sv(bad).max()),
                pre_causal=rc, pre_acausal=ra)


def main() -> int:
    rows = fig_skew()
    de = fig_deembed()
    q = fig_quality()

    print("=" * 66)
    print("B03 그림 · 본문 인용값")
    print("=" * 66)
    print(f"  전파 속도 {V_PROP / 1e8:.3f}e8 m/s (유효 유전율 {EPS_EFF})")
    print(f"  1 ps 는 {1e-12 * V_PROP * 1e3:.3f} mm 에 해당")
    print(f"  {F_MARK / 1e9:.0f} GHz 에서의 모드 변환")
    for ps, mm, db in rows:
        print(f"    지연차 {ps:5.1f} ps ({mm:5.2f} mm) → {db:6.1f} dB")
    print("  목표 모드 변환에서 역산한 허용 길이 차 (5 GHz)")
    for db in (-30.0, -25.0, -20.0, -18.0):
        tau, mm = skew_for(db)
        print(f"    {db:6.1f} dB → {tau * 1e12:5.2f} ps = {mm:5.2f} mm")
    print()
    print("  (a) 60 mm · 0.10 pF 픽스처, scikit-rf 의 IEEE 370 구현")
    print(f"      벗기기 전 오차 {de['raw']:.2f} dB")
    print(f"      보정 없음   전 대역 {de['nzc']:.3f} dB, "
          f"위 5 % 를 빼면 {de['nzc_in']:.4f} dB")
    print(f"      임피던스 보정 전 대역 {de['zc']:.3f} dB, "
          f"위 5 % 를 빼면 {de['zc_in']:.3f} dB")
    print("  (b) 비대칭만: 왼쪽 25 mm·0.25 pF, 오른쪽 27 mm·0.35 pF")
    print(f"      두 반쪽을 각각 알면 {de['err_ideal']:.1e} dB, "
          f"하나로 뭉치면 {de['err_avg']:.3f} dB")
    print(f"      정합된 DUT 인데 |S11| 이 {de['s11_avg']:.3f} "
          f"({20 * np.log10(de['s11_avg']):.1f} dB) 생긴다")
    print()
    print(f"  최대 특이값 — 정상 {q['sv_good']:.3f}, "
          f"과보정 {q['sv_bad']:.3f}")
    print(f"  t<0 에너지 비율 — 인과적 {q['pre_causal']:.2e}, "
          f"비인과적 {q['pre_acausal']:.3f}")

    # ── 자체 검산 ────────────────────────────────────────────────────
    print("-" * 66)
    ok = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  [{'OK ' if cond else '실패'}] {msg}")

    freq = skrf.Frequency(1, 20, 60, "ghz")
    for ps in SKEWS_PS:
        net = skewed_pair(freq, 100e-12, 100e-12 - ps * 1e-12)

        # ① 손으로 만든 변환 vs scikit-rf 의 se2gmm
        mine = se2mm(net.s)
        ref = net.copy()
        ref.se2gmm(p=2)
        chk(np.max(np.abs(mine - ref.s)) < 1e-12,
            f"{ps:g} ps: 손으로 만든 혼합모드 변환이 scikit-rf 와 일치 "
            f"(최대 차 {np.max(np.abs(mine - ref.s)):.1e})")

        # ② 수치 결과 vs 닫힌 식
        num = np.abs(mine[:, 0, 3])           # S(d1 ← c2) = 모드 변환
        cf = sdc21_closed(freq.f, ps * 1e-12)
        chk(np.max(np.abs(num - cf)) < 1e-12,
            f"{ps:g} ps: |Sdc21| 이 닫힌 식 |sin(π f Δτ)| 와 일치 "
            f"(최대 차 {np.max(np.abs(num - cf)):.1e})")

        # ③ 에너지 보존: |Sdd21|² + |Sdc21|² = 1 (무손실이므로)
        dd = np.abs(mine[:, 1, 0])
        chk(np.max(np.abs(dd ** 2 + num ** 2 - 1.0)) < 1e-12,
            f"{ps:g} ps: 차동으로 지나간 몫과 공통으로 샌 몫의 합이 1")

    # 역산 함수가 정방향과 맞는가 (왕복 확인)
    for db in (-30.0, -25.0, -20.0, -18.0):
        tau, mm = skew_for(db)
        back = 20 * np.log10(float(sdc21_closed(F_MARK, float(tau))))
        chk(abs(back - db) < 1e-9,
            f"{db:.0f} dB → {float(tau) * 1e12:.2f} ps ({float(mm):.2f} mm) "
            f"→ 다시 {back:.1f} dB (왕복 일치)")

    # 어긋남이 없으면 모드 변환도 없다
    net0 = skewed_pair(freq, 100e-12, 100e-12)
    chk(np.max(np.abs(se2mm(net0.s)[:, 0, 3])) < 1e-12,
        "지연차가 0 이면 모드 변환도 0")

    # 디임베딩: 두 반쪽을 정확히 알면 참값이 그대로 나온다
    chk(de["err_ideal"] < 1e-9,
        f"정확히 알고 벗기면 오차 {de['err_ideal']:.1e} dB (사실상 0)")
    chk(de["err_avg"] > 0.05,
        f"두 반쪽이 다르면 {de['err_avg']:.3f} dB 오차가 남는다")
    chk(de["s11_avg"] > de["s11_ideal"] * 10,
        "없던 반사가 생긴다 (참 DUT 는 정합인데)")
    # 두 방법의 성격이 다르다. 어느 쪽이 낫다고 말할 수 없고,
    # 어디가 무너지는지가 다르다 — 그것이 이 그림의 결론이다.
    chk(de["nzc_in"] < 0.02,
        f"보정 없는 방법은 대역 안에서는 거의 정확하다 "
        f"({de['nzc_in']:.4f} dB)")
    chk(de["nzc"] > 20 * de["nzc_in"],
        f"그런데 대역 끝에서 {de['nzc']:.2f} dB 로 터진다 "
        f"(안쪽의 {de['nzc'] / de['nzc_in']:.0f}배)")
    chk(abs(de["zc"] - de["zc_in"]) < 0.1,
        f"임피던스 보정판은 대역 끝이 안쪽과 비슷하다 "
        f"({de['zc']:.3f} vs {de['zc_in']:.3f} dB)")
    chk(de["zc_in"] > de["nzc_in"] * 10,
        f"대신 대역 안에 상시 편차가 남는다 "
        f"({de['zc_in']:.3f} dB) — 이 합성 픽스처에서의 이야기다")
    chk(de["nzc"] < de["raw"] and de["zc"] < de["raw"],
        f"둘 다 안 벗기는 것({de['raw']:.2f} dB)보다는 낫다")

    # 품질 지표
    chk(q["sv_good"] <= 1.0 + 1e-9,
        f"정상 파일의 최대 특이값 {q['sv_good']:.4f} ≤ 1")
    chk(q["sv_bad"] > 1.0,
        f"과보정 파일은 {q['sv_bad']:.3f} 로 수동성 위반")
    # 대역이 잘려 있으면 인과적인 물건도 t<0 에 약간의 에너지가 남는다
    # (깁스 현상). 그래서 절대값이 아니라 **두 경우의 비**로 가른다.
    chk(q["pre_acausal"] / q["pre_causal"] > 50,
        f"인과 판정이 두 경우를 {q['pre_acausal'] / q['pre_causal']:.0f}배로 "
        f"갈라 낸다 (절대값이 아니라 비로 본다)")
    chk(q["pre_causal"] < 0.02,
        f"인과적 파일의 앞선 에너지 {q['pre_causal']:.1e} — "
        f"대역 제한 때문에 0 은 아니다")

    # scikit-rf 에 들어 있는 **표준 구현**을 실제로 돌려 본다.
    # 본문 그림은 비대칭 하나만 떼어 보려고 단순화한 모형을 쓰지만,
    # 실습과 실무에서는 이 구현을 쓰므로 여기서 동작을 확인해 둔다.
    import warnings
    from skrf.calibration.deembedding import IEEEP370_SE_NZC_2xThru
    fg = skrf.Frequency.from_f(np.arange(1, 2001) * 10e6, unit="hz")
    d6 = attenuator(fg, 6.0)
    ha = shunt_c(fg, 0.05e-12) ** tline(fg, 40e-3, 12.0)
    m6 = ha ** d6 ** ha.flipped()
    raw = float(np.max(np.abs(20 * np.log10(np.abs(m6.s[:, 1, 0])) + 6.0)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dm = IEEEP370_SE_NZC_2xThru(dummy_2xthru=ha ** ha.flipped(), name="x")
        out = dm.deembed(m6)
    res = float(np.max(np.abs(20 * np.log10(np.abs(out.s[:, 1, 0])) + 6.0)))
    chk(res < raw / 5,
        f"scikit-rf 의 IEEE 370 NZC 가 픽스처 오차를 {raw:.2f} dB → "
        f"{res:.2f} dB 로 줄인다")
    chk(res < 0.15,
        f"불연속이 작은 픽스처에서는 보정 없이도 {res:.3f} dB 까지 간다 "
        f"— 문제가 되는 것은 불연속이 클 때다")

    # 상호성: 우리가 만든 픽스처 모형은 수동 소자뿐이라 S21 = S12
    f2 = skrf.Frequency(0.05, 20, 200, "ghz")
    hf = half_fixture(f2, 25.0, 0.25)
    chk(np.max(np.abs(hf.s[:, 1, 0] - hf.s[:, 0, 1])) < 1e-15,
        "픽스처 모형이 상호적 (S21 = S12)")

    print()
    if not all(ok):
        return 1
    print(f"  검산 {len(ok)}항목 전부 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
