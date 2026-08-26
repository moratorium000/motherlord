#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B04 (대신호 — 변조 파형·펄스·메모리 효과·NPR) 그림 생성기.

만드는 그림
  B04-1  AM-AM 과 AM-PM
  B04-2  메모리 효과 — 히스테리시스와 IM3 비대칭
  B04-3  펄스 측정 — 자기가열을 떼어 내기
  B04-4  NPR — 노치가 메워지는 정도와 측정 바닥
  B04-5  로드풀 — 수동 튜너가 닿지 못하는 영역
  B04-6  DPD — 무기억 보정과 기억 보정의 ACLR 차이

교차검증 세 갈래
  ① IM3 비대칭: 시간영역 FFT 로 읽은 값 vs 3차 모형의 닫힌 식
       IM3_상 = A^3(a3 + b·H(Δf)),  IM3_하 = A^3(a3 + b·H(Δf)*)
  ② 펄스 자기가열: 시간 적분(오일러) vs 주기 펄스열의 닫힌 식
       ΔT_max = P·Rth·(1 - e^(-W/τ)) / (1 - e^(-T/τ))
  ③ 다중톤 파고율: 위상 전부 0 일 때 PAPR = 10·log10(N) 이라는 정확한 값

실행: python3 scripts/gen_fig_b04.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.signal import welch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rf_style as S  # noqa: E402

MOD = "B04"
RNG = np.random.default_rng(20260826)

# ── 정적 비선형 (Rapp + AM-PM) ───────────────────────────────────────────
A_SAT = 1.0        # 포화 진폭 (정규화)
P_RAPP = 2.4       # Rapp 매끄러움 지수. 클수록 무릎이 각진다
AMPM_MAX = 0.42    # 포화 부근에서의 위상 회전 (rad, 약 24°)
AMPM_KNEE = 0.75   # 위상이 돌기 시작하는 진폭

# ── 3차 모형 (IM3 비대칭 해석용) ─────────────────────────────────────────
A1 = 1.0 + 0j
A3 = 0.055 * np.exp(1j * 1.15)   # 복소 3차 계수. 위상이 있어야 비대칭이 생긴다
B_BIAS = 0.0030 * np.exp(1j * 0.30)   # 바이어스망 경로 결합
B_THERM = 0.012 * np.exp(1j * 2.55)   # 열 경로 결합

R_B, L_B, C_B = 15.0, 22e-6, 12e-9    # 바이어스망(포락선 대역) 등가 RLC
TAU_TH_S = 50e-6                      # 열 시상수

# ── 펄스·열 모형 ─────────────────────────────────────────────────────────
P_DISS_W = 40.0      # 소자가 열로 버리는 전력
RTH_CW = 2.5         # 접합-플랜지 열저항 (°C/W)
TAU_TH_PULSE = 100e-6
K_GAIN_DBC = 0.012   # 이득 온도계수 (dB/°C)

# ── 로드풀 ───────────────────────────────────────────────────────────────
Z0 = 50.0
VDD, VKNEE = 50.0, 5.0
GAMMA_TUNER = 0.95
DEVICE_W = (10.0, 50.0, 100.0, 300.0)

# ── 변조 신호 ────────────────────────────────────────────────────────────
CH_BW_HZ = 20e6              # 채널 폭 (ACLR 을 재는 창)
SIG_BW_HZ = 18e6             # 실제로 신호가 차지하는 폭. 나머지는 보호대역
OSR = 8                      # 과표본율
FS_HZ = CH_BW_HZ * OSR
NSAMP = 1 << 18
PAPR_TARGET_DB = 8.0


# ══ 정적 모형 ═══════════════════════════════════════════════════════════
def rapp_gain(r):
    """진폭 r 에서의 **복소 이득** (선형 이득 1 로 정규화).

    크기는 Rapp 모형, 위상은 포화 부근에서만 도는 AM-PM 항이다.
    """
    r = np.asarray(r, float)
    mag = 1.0 / (1.0 + (r / A_SAT) ** (2 * P_RAPP)) ** (1.0 / (2 * P_RAPP))
    phi = AMPM_MAX * (r / AMPM_KNEE) ** 2 / (1.0 + (r / AMPM_KNEE) ** 2)
    return mag * np.exp(1j * phi)


def static_pa(x):
    """정적(무기억) 대신호 응답."""
    r = np.abs(x)
    return x * rapp_gain(r)


# ══ 포락선 영역 메모리 (바이어스망 + 열) ════════════════════════════════
def h_bias(f):
    """바이어스망이 포락선 주파수 f 에서 보이는 정규화 임피던스. H(0)=1."""
    w = 2 * np.pi * np.asarray(f, float)
    zl = R_B + 1j * w * L_B
    yc = 1j * w * C_B
    z = zl / (1.0 + zl * yc)          # (R+jwL) ∥ (1/jwC)
    return z / R_B


def h_therm(f):
    """열 경로의 1극 저역 응답. H(0)=1."""
    return 1.0 / (1.0 + 1j * np.asarray(f, float) / (1.0 / (2 * np.pi * TAU_TH_S)))


def env_filter(u, fs):
    """포락선 신호 u 를 두 메모리망에 각각 통과시킨다.

    두 망은 **실수 회로**이므로 음의 주파수에는 켤레를 넣어야 결과가 실수로
    나온다. 결합계수 b 는 복소수지만 그것은 필터가 아니라 되섞임 계수라서
    여기서 곱하지 않는다 — 이 구분을 놓치면 IM3 비대칭의 부호가 뒤집힌다.
    """
    n = len(u)
    f = np.fft.fftfreq(n, 1 / fs)
    U = np.fft.fft(u)
    out = []
    for h in (h_bias, h_therm):
        hp = h(np.abs(f))
        hh = np.where(f >= 0, hp, np.conj(hp))
        out.append(np.real(np.fft.ifft(U * hh)))
    return out


def h_mem(f, conj=False):
    """3차 모형의 메모리 항 b_e·H_e + b_t·H_t.

    conj=True 면 **필터만** 켤레를 취한다 (하측 IM3 가 타는 경로).
    """
    he, ht = h_bias(f), h_therm(f)
    if conj:
        he, ht = np.conj(he), np.conj(ht)
    return B_BIAS * he + B_THERM * ht


def im3_closed(a, df):
    """3차 모형의 IM3 상·하측파대 진폭 (닫힌 식).

    y = a1·x + a3·x|x|^2 + x·(b_e·v_e + b_t·v_t) 에
    x = A(e^{jΩt}+e^{-jΩt}) 를 넣으면 포락선 제곱 |x|^2 이 직류와
    2Ω(= 톤 간격) 성분을 갖는다. 그 성분이 다시 x 와 섞여 ±3Ω 로 올라가는데,
    필터가 실수 회로이므로 상측은 H(Δf), 하측은 H(Δf)* 를 탄다.
    """
    return (np.abs(a ** 3 * (A3 + h_mem(df))),
            np.abs(a ** 3 * (A3 + h_mem(df, conj=True))))


def two_tone_numeric(a, df):
    """같은 3차 모형을 시간영역에서 돌려 IM3 를 읽는다 (닫힌 식 검증용).

    표본율을 톤 간격의 64배로 잡아 Δf 와 1.5Δf 가 FFT 격자에 **정확히**
    얹히게 한다. 그래야 누설 없이 진폭을 읽는다.
    """
    n = 4096
    fs = 64.0 * df
    t = np.arange(n) / fs
    om = np.pi * df                                    # Ω = Δω/2
    x = a * (np.exp(1j * om * t) + np.exp(-1j * om * t))
    ve, vt = env_filter(np.abs(x) ** 2, fs)
    y = A1 * x + A3 * x * np.abs(x) ** 2 + x * (B_BIAS * ve + B_THERM * vt)
    Y = np.fft.fft(y) / n
    k = int(round(1.5 * df * n / fs))                  # = 96
    return np.abs(Y[k]), np.abs(Y[-k])


# ══ 펄스 열 모형 ════════════════════════════════════════════════════════
def dt_pulse_closed(width_s, period_s, p=P_DISS_W, rth=RTH_CW, tau=TAU_TH_PULSE):
    """주기 펄스열이 정상상태에 들었을 때의 펄스 끝 온도 상승."""
    w = np.asarray(width_s, float)
    t = np.asarray(period_s, float)
    return p * rth * (1.0 - np.exp(-w / tau)) / (1.0 - np.exp(-t / tau))


def dt_pulse_numeric(width_s, period_s, cycles=30,
                     p=P_DISS_W, rth=RTH_CW, tau=TAU_TH_PULSE):
    """같은 것을 시간 적분으로 (닫힌 식 검증용).

    dT/dt = (P·Rth·on - T)/tau 를 오일러 전진법으로 푼다. 닫힌 식과는 다른
    경로로 구한 값이라 **서로를 검산한다**. 재귀식이 선형이라 lfilter 로
    한 번에 돌린다 — 그래야 걸음을 잘게 쪼갤 수 있다.
    """
    from scipy.signal import lfilter

    dt = min(width_s, tau) / 200.0
    steps = max(8, int(round(period_s / dt)))
    dt = period_s / steps
    on = (np.arange(steps) * dt) < width_s
    drive = np.tile(np.where(on, p * rth, 0.0), cycles)
    al = dt / tau
    temp = lfilter([0.0, al], [1.0, -(1.0 - al)], drive)
    last = temp[-steps:]
    return float(np.max(last[on]))


# ══ 로드풀 ══════════════════════════════════════════════════════════════
def r_opt(pout_w, vdd=VDD, vknee=VKNEE):
    """부하선 관점의 최적 부하 저항. Ropt = (Vdd - Vknee)^2 / (2·Pout)."""
    return (vdd - vknee) ** 2 / (2.0 * np.asarray(pout_w, float))


def gamma_of(r, z0=Z0):
    return (np.asarray(r, float) - z0) / (np.asarray(r, float) + z0)


def reach_passive(loss_db, gamma_tuner=GAMMA_TUNER):
    """튜너와 DUT 사이 손실이 있을 때 DUT 면에서 얻을 수 있는 최대 |Γ|."""
    return gamma_tuner * 10 ** (-2 * np.asarray(loss_db, float) / 20.0)


def p_inject_w(gamma, pout_w, loss_db):
    """능동 로드풀에서 그 Γ 를 만들려면 주입기가 내야 하는 전력."""
    return (np.asarray(gamma, float) ** 2 * np.asarray(pout_w, float)
            * 10 ** (np.asarray(loss_db, float) / 10.0))


# ══ 변조 신호와 메모리 다항식 PA ════════════════════════════════════════
K_ORD = (1, 3, 5, 7)
M_TAP = (0, 1, 2)
TAP_SCALE = {(1, 1): 0.030, (3, 1): 0.120, (5, 1): 0.100, (7, 1): 0.050,
             (1, 2): 0.010, (3, 2): 0.050, (5, 2): 0.030, (7, 2): 0.020}
TAP_PHASE = {(1, 1): 2.00, (3, 1): -1.20, (5, 1): 0.80, (7, 1): 2.60,
             (1, 2): 0.40, (3, 2): 2.90, (5, 2): -2.10, (7, 2): 1.30}


def fit_static_poly():
    """Rapp 정적 곡선을 홀수차 복소 다항식으로 맞춘다 → a[k][0]."""
    r = np.linspace(1e-3, 1.15, 400)
    g = rapp_gain(r)                                  # 목표 복소 이득
    basis = np.stack([r ** (k - 1) for k in K_ORD], axis=1)
    coef, *_ = np.linalg.lstsq(basis, g, rcond=None)
    return coef


A_K0 = fit_static_poly()


def pa_taps():
    """메모리 다항식 계수 a[k][m]."""
    a = {}
    for i, k in enumerate(K_ORD):
        a[(k, 0)] = A_K0[i]
        for m in (1, 2):
            a[(k, m)] = (TAP_SCALE[(k, m)] * abs(A_K0[i])
                         * np.exp(1j * TAP_PHASE[(k, m)]))
    return a


A_KM = pa_taps()


def mp_basis(x, ks=K_ORD, ms=M_TAP):
    """메모리 다항식 기저 행렬. 신호를 주기로 보고 np.roll 로 지연을 준다."""
    cols = []
    for m in ms:
        xd = np.roll(x, m)
        for k in ks:
            cols.append(xd * np.abs(xd) ** (k - 1))
    return np.stack(cols, axis=1)


def pa_mp(x):
    """짧은 메모리를 가진 PA (정합 대역폭 기인). 이 모형이 §9의 DUT 다."""
    w = np.array([A_KM[(k, m)] for m in M_TAP for k in K_ORD])
    return mp_basis(x) @ w


G_LIN = sum(A_KM[(1, m)] for m in M_TAP)


def make_signal(n=NSAMP, bw=SIG_BW_HZ, fs=FS_HZ, papr_db=PAPR_TARGET_DB):
    """대역 제한된 복소 신호를 만들고 파고율을 목표까지 깎는다(CFR)."""
    f = np.fft.fftfreq(n, 1 / fs)
    spec = np.zeros(n, complex)
    band = np.abs(f) <= bw / 2
    spec[band] = (RNG.normal(size=band.sum()) + 1j * RNG.normal(size=band.sum()))
    x = np.fft.ifft(spec)
    x /= np.sqrt(np.mean(np.abs(x) ** 2))
    for _ in range(6):                                # 자르고 다시 대역 제한
        lim = 10 ** (papr_db / 20.0)
        r = np.abs(x)
        over = r > lim
        x = np.where(over, x / np.maximum(r, 1e-12) * lim, x)
        Xf = np.fft.fft(x)
        Xf[~band] = 0
        x = np.fft.ifft(Xf)
        x /= np.sqrt(np.mean(np.abs(x) ** 2))
    return x


def papr_db(x):
    return 10 * np.log10(np.max(np.abs(x) ** 2) / np.mean(np.abs(x) ** 2))


def psd_db(x, fs=FS_HZ, nperseg=8192):
    f, p = welch(x, fs=fs, nperseg=nperseg, noverlap=nperseg // 2,
                 window="blackmanharris", return_onesided=False,
                 detrend=False)
    idx = np.argsort(f)
    return f[idx], 10 * np.log10(p[idx] + 1e-30)


def aclr_db(x, bw=CH_BW_HZ, fs=FS_HZ, nperseg=8192):
    """인접 채널 누설비. 같은 폭의 채널을 ±bw 이격에서 적분해 비교한다."""
    f, p = welch(x, fs=fs, nperseg=nperseg, noverlap=nperseg // 2,
                 window="blackmanharris", return_onesided=False,
                 detrend=False)
    def band_pow(lo, hi):
        m = (f >= lo) & (f < hi)
        return np.sum(p[m])
    main = band_pow(-bw / 2, bw / 2)
    low = band_pow(-1.5 * bw, -0.5 * bw)
    high = band_pow(0.5 * bw, 1.5 * bw)
    return (10 * np.log10(low / main), 10 * np.log10(high / main))


def dpd_train(x, pa, ms, iters=3):
    """간접 학습 구조. 후왜곡기를 풀어 그대로 전왜곡기로 쓴다."""
    w = None
    xin = x.copy()
    for _ in range(iters):
        y = pa(xin)
        z = y / G_LIN
        psi = mp_basis(z, ms=ms)
        w, *_ = np.linalg.lstsq(psi, xin, rcond=None)
        xin = mp_basis(x, ms=ms) @ w
        # 전왜곡 후 rms 를 원 신호에 맞춰 둔다 (구동 레벨 비교를 위해)
        xin *= np.sqrt(np.mean(np.abs(x) ** 2) / np.mean(np.abs(xin) ** 2))
    return xin


# ══ NPR ═════════════════════════════════════════════════════════════════
NPR_BW = 40e6
NPR_FS = NPR_BW * 4
NPR_N = 1 << 19
NPR_NOTCH = 0.4e6           # 대역폭의 1 %
SNR_MAX_DB = 60.0           # 최대 구동에서의 출력 잡음 대비 신호 밀도차
SRC_NOTCH_DB = 45.0         # 신호원이 실제로 파 놓은 노치 깊이


def npr_signal():
    f = np.fft.fftfreq(NPR_N, 1 / NPR_FS)
    spec = np.zeros(NPR_N, complex)
    band = np.abs(f) <= NPR_BW / 2
    notch = np.abs(f) <= NPR_NOTCH / 2
    sel = band & ~notch
    spec[sel] = RNG.normal(size=sel.sum()) + 1j * RNG.normal(size=sel.sum())
    x = np.fft.ifft(spec)
    return x / np.sqrt(np.mean(np.abs(x) ** 2))


def npr_distortion_db(x0, backoff_db, nperseg=8192):
    """왜곡만으로 정해지는 NPR (잡음·신호원 한계는 뺀 값)."""
    peak = np.max(np.abs(x0))
    x = x0 * (A_SAT / peak) * 10 ** (-backoff_db / 20.0)
    y = static_pa(x)
    f, p = welch(y, fs=NPR_FS, nperseg=nperseg, noverlap=nperseg // 2,
                 window="blackmanharris", return_onesided=False, detrend=False)
    inn = np.abs(f) <= NPR_NOTCH / 4
    out = (np.abs(f) > NPR_NOTCH) & (np.abs(f) <= NPR_BW / 2 * 0.8)
    return 10 * np.log10(np.mean(p[out]) / np.mean(p[inn])), (f, p)


def npr_measured(npr_d, backoff_db,
                 snr0=SNR_MAX_DB, src=SRC_NOTCH_DB):
    """실제로 화면에 찍히는 NPR — 왜곡·잡음·신호원 노치가 함께 노치를 메운다."""
    npr_n = snr0 - np.asarray(backoff_db, float)
    return -10 * np.log10(10 ** (-np.asarray(npr_d, float) / 10.0)
                          + 10 ** (-npr_n / 10.0)
                          + 10 ** (-src / 10.0))


# ══ 다중톤 파고율 ═══════════════════════════════════════════════════════
def multitone_papr(n_tones, phase="newman", n=1 << 14, seed=7):
    k = np.arange(n_tones)
    if phase == "zero":
        th = np.zeros(n_tones)
    elif phase == "newman":
        th = np.pi * k ** 2 / n_tones
    elif phase == "schroeder":
        th = -np.pi * k * (k + 1) / n_tones
    else:
        th = np.random.default_rng(seed).uniform(0, 2 * np.pi, n_tones)
    t = np.arange(n) / n
    sig = np.sum(np.exp(1j * (2 * np.pi * np.outer(t, k + 1) + th)), axis=1)
    return papr_db(sig)


# ══ 그림 ════════════════════════════════════════════════════════════════
def fig1_am_am_pm():
    fig, (a1, a2) = S.figure(w=10.4, h=4.2, ncols=2)
    r = np.linspace(0, 1.35, 500)
    g = rapp_gain(r)
    pin = 20 * np.log10(np.maximum(r, 1e-4))
    pout = pin + 20 * np.log10(np.abs(g))

    a1.plot(pin, pout, lw=2.4, color=S.COLORS[0], label="실측 AM-AM")
    S.reference_line(a1, pin, pin, label="선형 연장선")
    # P1dB
    i1 = np.argmax(20 * np.log10(np.abs(g)) < -1.0)
    a1.plot(pin[i1], pout[i1], "o", ms=8, color=S.ACCENT, zorder=6)
    a1.annotate(S.txt(f"P1dB\n출력 {pout[i1]:.2f} dB"),
                xy=(pin[i1], pout[i1]), xytext=(pin[i1] - 13, pout[i1] + 1.2),
                color=S.ACCENT, fontsize=9, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    a1.set_xlim(-22, 3)
    a1.set_ylim(-24, 3)
    a1.set_xlabel(S.txt("입력 전력 (dB, 포화 기준 상대값)"))
    a1.set_ylabel(S.txt("출력 전력 (dB, 선형 이득 기준)"))
    a1.set_title(S.txt("AM-AM — 진폭이 눌리는 정도"))
    a1.legend(loc="upper left", fontsize=9)

    ph = np.degrees(np.angle(g))
    a2.plot(pin, ph, lw=2.4, color=S.COLORS[1])
    a2.plot(pin[i1], ph[i1], "o", ms=8, color=S.ACCENT, zorder=6)
    a2.annotate(S.txt(f"P1dB 에서 이미 {ph[i1]:.1f} deg"),
                xy=(pin[i1], ph[i1]), xytext=(pin[i1] - 16, ph[i1] - 4.5),
                color=S.ACCENT, fontsize=9, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    a2.axhline(0, color=S.MUTED, lw=1.0, ls=":")
    a2.set_xlim(-22, 3)
    a2.set_xlabel(S.txt("입력 전력 (dB, 포화 기준 상대값)"))
    a2.set_ylabel(S.txt("출력 위상 변화 (deg)"))
    a2.set_title(S.txt("AM-PM — 진폭이 위상을 돌린다"))
    fig.tight_layout()
    S.save(fig, MOD, "am_am_pm")
    return pout[i1] - pin[i1], ph[i1], pin[i1]


def fig2_memory():
    fig, (a1, a2) = S.figure(w=10.4, h=4.2, ncols=2)

    # (A) 히스테리시스 — 포락선이 오르내릴 때 같은 진폭에서 이득이 다르다
    fs = 40e6
    n = 4000
    t = np.arange(n) / fs
    env = 0.62 * (1 + 0.75 * np.sin(2 * np.pi * 300e3 * t))
    x = env * np.exp(1j * 2 * np.pi * 1e6 * t)
    u = np.abs(x) ** 2
    ve, vt = env_filter(u, fs)
    y_mem = A1 * x + A3 * x * u + x * (B_BIAS * ve + B_THERM * vt)
    y_nom = A1 * x + (A3 + h_mem(0.0)) * x * u
    keep = slice(n // 4, None)
    g_mem = 20 * np.log10(np.abs(y_mem[keep]) / np.abs(x[keep]))
    g_nom = 20 * np.log10(np.abs(y_nom[keep]) / np.abs(x[keep]))
    a1.plot(np.abs(x[keep]), g_nom, lw=2.0, ls="-", color=S.MUTED,
            label=S.txt("메모리 없음 — 선 하나"))
    a1.plot(np.abs(x[keep]), g_mem, lw=1.4, ls="-", color=S.COLORS[0],
            label=S.txt("메모리 있음 — 고리가 벌어진다"))
    a1.set_xlabel(S.txt("순간 입력 진폭 |x|"))
    a1.set_ylabel(S.txt("순간 이득 (dB)"))
    a1.set_title(S.txt("AM-AM 히스테리시스 (포락선 300 kHz)"))
    a1.legend(loc="lower left", fontsize=9)
    loop = float(np.ptp(g_mem[np.abs(np.abs(x[keep]) - 0.62) < 0.01]))

    # (B) IM3 비대칭 — 톤 간격을 쓸어 본다
    df = np.logspace(2, 7, 400)
    up, lo = im3_closed(0.30, df)
    ref = np.abs(0.30 ** 3 * A3)
    a2.semilogx(df, 20 * np.log10(up / ref), lw=2.2, ls="-", color=S.COLORS[0],
                label=S.txt("상측 IM3"))
    a2.semilogx(df, 20 * np.log10(lo / ref), lw=2.2, ls="--",
                color=S.COLORS[1], label=S.txt("하측 IM3"))
    a2.axhline(0, color=S.MUTED, lw=1.0, ls=":")
    asym = 20 * np.log10(up / lo)
    imax = int(np.argmax(np.abs(asym)))
    a2.annotate(S.txt(f"최대 비대칭 {abs(asym[imax]):.1f} dB\n"
                      f"@ 톤 간격 {df[imax] / 1e3:.0f} kHz"),
                xy=(df[imax], 20 * np.log10(up[imax] / ref)),
                xytext=(df[imax] * 0.012, 4.4),
                color=S.ACCENT, fontsize=9, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    a2.set_xlabel(S.txt("톤 간격 (Hz)"))
    a2.set_ylabel(S.txt("IM3 세기 (dB, 정적 항 기준)"))
    a2.set_title(S.txt("같은 소자, 같은 전력 — 간격만 바꿨다"))
    a2.legend(loc="lower left", fontsize=9)
    S.hz_ticks(a2, [1e2, 1e3, 1e4, 1e5, 1e6, 1e7])
    a2.set_xlim(1e2, 1e7)
    a2.set_ylim(-2.6, 5.4)
    fig.tight_layout()
    S.save(fig, MOD, "memory_hysteresis")
    return loop, float(asym[imax]), float(df[imax])


def fig3_pulse():
    fig, (a1, a2) = S.figure(w=10.4, h=4.4, ncols=2)

    # (A) 타이밍도 — 눈으로 읽히도록 듀티 20 % 조건으로 그린다
    period, width = 100e-6, 20e-6
    n = 20000
    t = np.linspace(0, 3.05 * period, n)
    on = (t % period) < width
    a1.step(t * 1e6, on * 1.0 + 3.5, where="post", lw=1.8, ls="-",
            color=S.COLORS[0])
    a1.step(t * 1e6, on * 1.0 + 2.0, where="post", lw=1.8, ls="-",
            color=S.COLORS[1])
    temp = np.zeros(n)
    dtstep = np.diff(t, prepend=t[0])
    tt = 0.0
    for i in range(n):
        tt += dtstep[i] * ((P_DISS_W * RTH_CW if on[i] else 0.0) - tt) / TAU_TH_PULSE
        temp[i] = tt
    a1.plot(t * 1e6, 0.15 + temp / (P_DISS_W * RTH_CW) * 3.4, lw=1.8, ls="-",
            color=S.COLORS[2])
    for x0 in (0, period, 2 * period, 3 * period):
        a1.axvspan((x0 + width * 0.6) * 1e6, (x0 + width) * 1e6,
                   color=S.ACCENT, alpha=0.30, lw=0)
    a1.annotate(S.txt("측정창 — 펄스 뒤쪽만 딴다"),
                xy=((width * 0.82) * 1e6, 4.55), xytext=(52, 5.0),
                color=S.ACCENT, fontsize=9, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    for y0, lab in ((4.0, "드레인 바이어스 펄스"), (2.5, "RF 펄스"),
                    (1.0, "접합 온도 상승")):
        a1.text(304, y0, S.txt(lab), fontsize=9, ha="right", va="center",
                bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5))
    a1.set_xlim(0, 305)
    a1.set_ylim(0, 5.6)
    a1.set_yticks([])
    a1.grid(False)
    a1.set_xlabel(S.txt("시간 (us)"))
    a1.set_title(S.txt(f"펄스폭 {width * 1e6:.0f} us · 주기 "
                       f"{period * 1e6:.0f} us (듀티 "
                       f"{width / period * 100:.0f} %)"))

    # (B) 펄스폭을 쓸면 자기가열이 드러난다
    duty = 0.10
    widths = np.logspace(-6.3, -1.7, 300)
    dt_end = dt_pulse_closed(widths, widths / duty)
    dg = -K_GAIN_DBC * dt_end
    dg_cw = -K_GAIN_DBC * P_DISS_W * RTH_CW
    a2.semilogx(widths * 1e6, dg, lw=2.4, ls="-", color=S.COLORS[0],
                label=S.txt(f"펄스 (듀티 {duty * 100:.0f} %)"))
    S.limit_line(a2, dg_cw, S.txt(f"CW 값 {dg_cw:.2f} dB"), side="upper")
    a2.axhline(0, color=S.MUTED, lw=1.0, ls=":")
    a2.annotate(S.txt("여기서는 소자가 아직 안 뜨겁다\n= 등온 특성"),
                xy=(2, dg[np.argmin(np.abs(widths - 2e-6))]),
                xytext=(1.4, dg_cw * 0.52),
                fontsize=9, color=S.ACCENT, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    a2.set_ylim(dg_cw * 1.22, 0.08)
    a2.set_xlabel(S.txt("펄스폭 (us)"))
    a2.set_ylabel(S.txt("이득 변화 (dB)"))
    a2.set_title(S.txt("펄스폭을 쓸면 열 시상수가 보인다"))
    a2.legend(loc="upper right", fontsize=9)
    S.plain_log(a2, axis="x")
    fig.tight_layout()
    S.save(fig, MOD, "pulsed_thermal")
    return dg_cw, float(dt_pulse_closed(10e-6, 1000e-6))


def fig4_npr():
    fig, (a1, a2) = S.figure(w=10.4, h=4.2, ncols=2)
    x0 = npr_signal()

    for bo, col, ls in ((3.0, S.COLORS[1], "-"), (12.0, S.COLORS[0], "--")):
        d, (f, p) = npr_distortion_db(x0, bo)
        idx = np.argsort(f)
        f, p = f[idx], p[idx]
        ref = 10 * np.log10(np.mean(p[(np.abs(f) > NPR_NOTCH) &
                                      (np.abs(f) < NPR_BW / 2 * 0.8)]))
        a1.plot(f / 1e6, 10 * np.log10(p + 1e-30) - ref, lw=1.5, ls=ls,
                color=col,
                label=S.txt(f"백오프 {bo:.0f} dB · 왜곡 NPR {d:.1f} dB"))
    a1.set_xlim(-1.6, 1.6)
    a1.set_ylim(-52, 8)
    a1.axvspan(-NPR_NOTCH / 2 / 1e6, NPR_NOTCH / 2 / 1e6, color=S.ACCENT,
               alpha=0.12, lw=0)
    a1.text(0, 4, S.txt("파 놓은 노치"), ha="center", fontsize=9,
            color=S.ACCENT, fontweight="bold")
    a1.set_xlabel(S.txt("중심에서의 이격 (MHz)"))
    a1.set_ylabel(S.txt("출력 밀도 (dB, 대역 내 평균 기준)"))
    a1.set_title(S.txt("노치가 메워진다 — 그게 왜곡이다"))
    a1.legend(loc="lower right", fontsize=8.5)

    bos = np.arange(0.0, 18.1, 1.0)
    dd = np.array([npr_distortion_db(x0, b)[0] for b in bos])
    meas = npr_measured(dd, bos)
    a2.plot(bos, dd, lw=1.8, ls="--", color=S.COLORS[0],
            label=S.txt("왜곡만 있을 때"))
    a2.plot(bos, SNR_MAX_DB - bos, lw=1.8, ls="-.", color=S.COLORS[2],
            label=S.txt("잡음만 있을 때"))
    a2.axhline(SRC_NOTCH_DB, lw=1.6, ls=":", color=S.MUTED)
    a2.text(0.4, SRC_NOTCH_DB + 1.0, S.txt(f"신호원 노치 {SRC_NOTCH_DB:.0f} dB"),
            ha="left", fontsize=9, color=S.MUTED, fontweight="bold")
    S.emph(a2, bos, meas, label=S.txt("화면에 찍히는 값"))
    ipk = int(np.argmax(meas))
    a2.plot(bos[ipk], meas[ipk], "o", ms=8, color=S.ACCENT, zorder=7)
    a2.annotate(S.txt(f"최적 백오프 {bos[ipk]:.0f} dB\nNPR {meas[ipk]:.1f} dB"),
                xy=(bos[ipk], meas[ipk]), xytext=(bos[ipk] + 1.5, meas[ipk] - 12),
                fontsize=9, color=S.ACCENT, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    a2.set_xlim(0, 18)
    a2.set_ylim(0, 62)
    a2.set_xlabel(S.txt("입력 백오프 (dB)"))
    a2.set_ylabel(S.txt("NPR (dB)"))
    a2.set_title(S.txt("NPR 은 세 가지가 함께 정한다"))
    a2.legend(loc="lower right", fontsize=8.5)
    fig.tight_layout()
    S.save(fig, MOD, "npr_spectrum")
    return float(meas[ipk]), float(bos[ipk]), dd, bos


def fig5_loadpull():
    fig, ax = S.figure(w=7.0, h=6.8)
    th = np.linspace(0, 2 * np.pi, 721)
    # 스미스 격자 (얇게). ls 를 명시하지 않으면 색 순환기가 점선을 물려 준다
    for r in (0.2, 0.5, 1.0, 2.0, 5.0):
        c, rad = r / (1 + r), 1 / (1 + r)
        ax.plot(c + rad * np.cos(th), rad * np.sin(th), color=S.GRID, lw=0.8,
                ls="-", zorder=0)
    for xr in (0.2, 0.5, 1.0, 2.0, 5.0):
        for sgn in (1, -1):
            cy, rad = sgn / xr, 1 / xr
            xs, ys = 1 + rad * np.cos(th), cy + rad * np.sin(th)
            keep = xs ** 2 + ys ** 2 <= 1.0
            ax.plot(np.where(keep, xs, np.nan), np.where(keep, ys, np.nan),
                    color=S.GRID, lw=0.8, ls="-", zorder=0)
    ax.plot(np.cos(th), np.sin(th), color=S.INK, lw=1.6, ls="-", zorder=2)
    ax.plot([-1, 1], [0, 0], color=S.GRID, lw=0.8, ls="-", zorder=0)

    lab_ang = (128, 143, 158, 173)
    for (loss, col), ang in zip(((0.0, S.COLORS[0]), (0.5, S.COLORS[2]),
                                 (1.0, S.COLORS[4]), (2.0, S.COLORS[1])),
                                lab_ang):
        g = reach_passive(loss)
        ax.plot(g * np.cos(th), g * np.sin(th), color=col, ls="-", lw=2.0,
                zorder=3)
        rad = np.radians(ang)
        ax.annotate(S.txt(f"손실 {loss:.1f} dB -> |G| {g:.2f}"),
                    xy=(g * np.cos(rad), g * np.sin(rad)),
                    xytext=(1.02 * np.cos(rad) - 0.05,
                            1.02 * np.sin(rad) + 0.06),
                    fontsize=8.5, color=col, fontweight="bold",
                    ha="center", va="center",
                    bbox=dict(fc="white", ec="none", alpha=0.9, pad=1.2),
                    arrowprops=dict(arrowstyle="-", color=col, lw=0.9))

    for i, p in enumerate(DEVICE_W):
        gm = float(gamma_of(r_opt(p)))
        ax.plot(gm, 0, "o", ms=9, color=S.ACCENT, zorder=6)
        dy = -0.13 if i % 2 == 0 else -0.30
        ax.annotate(S.txt(f"{p:.0f} W · |G|={abs(gm):.2f}"),
                    xy=(gm, 0), xytext=(gm, dy), ha="center", va="top",
                    fontsize=8.5, color=S.ACCENT, fontweight="bold",
                    bbox=dict(fc="white", ec="none", alpha=0.9, pad=1.2),
                    arrowprops=dict(arrowstyle="-", color=S.ACCENT, lw=0.9))
    g300 = float(abs(gamma_of(r_opt(300.0))))
    ax.annotate(S.txt("300 W 는 손실 0.5 dB 만 있어도\n수동 튜너가 못 닿는다"),
                xy=(-g300, 0.0), xytext=(0.30, -0.72),
                fontsize=9, color=S.ACCENT, fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.ACCENT, lw=0.8, alpha=0.95, pad=3),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.3))
    ax.set_aspect("equal")
    ax.set_xlim(-1.30, 1.30)
    ax.set_ylim(-1.30, 1.22)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(S.txt("반사계수 평면 — 튜너가 닿는 곳과 소자가 원하는 곳"))
    fig.tight_layout()
    S.save(fig, MOD, "loadpull_coverage")
    return {p: float(abs(gamma_of(r_opt(p)))) for p in DEVICE_W}


def fig6_dpd():
    fig, (a1, a2) = S.figure(w=10.4, h=4.2, ncols=2)
    x = make_signal()
    peak = np.max(np.abs(x))
    x = x * (0.92 * A_SAT / peak)

    y_raw = pa_mp(x)
    x_ml = dpd_train(x, pa_mp, ms=(0,))
    y_ml = pa_mp(x_ml)
    x_mm = dpd_train(x, pa_mp, ms=M_TAP)
    y_mm = pa_mp(x_mm)

    res = {}
    for name, sig in (("입력 신호", x), ("보정 없음", y_raw),
                      ("무기억 DPD", y_ml), ("기억 DPD", y_mm)):
        res[name] = aclr_db(sig)

    for (name, sig), col, ls in zip(
            (("보정 없음", y_raw), ("무기억 DPD", y_ml), ("기억 DPD", y_mm),
             ("입력 신호 (측정 바닥)", x)),
            (S.COLORS[1], S.COLORS[4], S.COLORS[0], S.MUTED),
            ("-", "--", "-", ":")):
        f, p = psd_db(sig)
        p = p - np.max(p)
        a1.plot(f / 1e6, p, lw=2.0 if name == "기억 DPD" else 1.5,
                ls=ls, color=col, label=S.txt(name))
    a1.axvspan(CH_BW_HZ / 2 / 1e6, 1.5 * CH_BW_HZ / 1e6, color=S.ACCENT,
               alpha=0.08, lw=0)
    a1.axvspan(-1.5 * CH_BW_HZ / 1e6, -CH_BW_HZ / 2 / 1e6, color=S.ACCENT,
               alpha=0.08, lw=0)
    a1.set_xlim(-45, 45)
    a1.set_ylim(-125, 5)
    a1.set_xlabel(S.txt("중심에서의 이격 (MHz)"))
    a1.set_ylabel(S.txt("출력 밀도 (dB, 최대 기준)"))
    a1.set_title(S.txt("인접 채널로 새어 나간 것"))
    a1.legend(loc="lower center", fontsize=8, ncol=2)

    names = ["보정 없음", "무기억 DPD", "기억 DPD"]
    lows = [res[n][0] for n in names]
    highs = [res[n][1] for n in names]
    xpos = np.arange(3)
    a2.bar(xpos - 0.19, lows, 0.36, color=S.COLORS[0], label=S.txt("하측 채널"))
    a2.bar(xpos + 0.19, highs, 0.36, color=S.COLORS[1], label=S.txt("상측 채널"))
    for i in range(3):
        a2.text(xpos[i] - 0.19, lows[i] - 1.6, f"{lows[i]:.1f}", ha="center",
                va="top", fontsize=8.5)
        a2.text(xpos[i] + 0.19, highs[i] - 1.6, f"{highs[i]:.1f}", ha="center",
                va="top", fontsize=8.5)
    floor = max(res["입력 신호"])
    a2.axhline(floor, color=S.MUTED, lw=1.4, ls=":")
    a2.text(2.45, floor + 1.2, S.txt(f"측정 바닥 {floor:.1f} dBc"), ha="right",
            fontsize=9, color=S.MUTED)
    a2.set_xticks(xpos)
    a2.set_xticklabels([S.txt(n) for n in names])
    a2.set_ylabel(S.txt("ACLR (dBc)"))
    a2.set_ylim(-125, 0)
    a2.set_title(S.txt("두 채널을 따로 봐야 메모리가 보인다"))
    a2.legend(loc="lower left", fontsize=9)
    fig.tight_layout()
    S.save(fig, MOD, "dpd_aclr")
    return res, papr_db(x), papr_db(x_mm)


# ══ 본문 ════════════════════════════════════════════════════════════════
def main() -> int:
    print("B04 그림 생성")
    print("=" * 62)

    g1db, ph1db, pin1db = fig1_am_am_pm()
    print(f"  [1] AM-AM/AM-PM        P1dB 입력 {pin1db:.2f} dB, "
          f"그 점의 AM-PM {ph1db:.1f} deg")

    loop, asym, asym_df = fig2_memory()
    print(f"  [2] 메모리             히스테리시스 폭 {loop:.3f} dB, "
          f"최대 IM3 비대칭 {abs(asym):.1f} dB @ {asym_df / 1e3:.0f} kHz")

    dg_cw, dt10 = fig3_pulse()
    print(f"  [3] 펄스               CW 이득 강하 {dg_cw:.2f} dB, "
          f"10 us/1 % 온도 상승 {dt10:.1f} C")

    npr_pk, npr_bo, npr_dd, npr_bos = fig4_npr()
    print(f"  [4] NPR                최고 {npr_pk:.1f} dB @ 백오프 "
          f"{npr_bo:.0f} dB")

    gammas = fig5_loadpull()
    print("  [5] 로드풀             필요 |G| = " +
          ", ".join(f"{k:.0f} W:{v:.3f}" for k, v in gammas.items()))

    aclr, papr_in, papr_pd = fig6_dpd()
    print("  [6] DPD                ACLR(하/상) = " +
          " | ".join(f"{k} {v[0]:.1f}/{v[1]:.1f}" for k, v in aclr.items()))

    print()
    print("본문에 쓰는 값")
    print("-" * 62)
    print(f"  P1dB 에서의 AM-PM             {ph1db:.1f} deg")
    print(f"  IM3 비대칭 최대               {abs(asym):.1f} dB "
          f"(톤 간격 {asym_df / 1e3:.0f} kHz)")
    print(f"  바이어스망 공진               "
          f"{1 / (2 * np.pi * np.sqrt(L_B * C_B)) / 1e3:.0f} kHz")
    print(f"  열 경로 코너                  "
          f"{1 / (2 * np.pi * TAU_TH_S) / 1e3:.2f} kHz")
    print(f"  CW 접합 온도 상승             {P_DISS_W * RTH_CW:.0f} C "
          f"→ 이득 {dg_cw:.2f} dB")
    print(f"  10 us 펄스 · 듀티 1 %         {dt10:.1f} C "
          f"→ 이득 {-K_GAIN_DBC * dt10:.2f} dB")
    print(f"  NPR 최고값                    {npr_pk:.1f} dB "
          f"@ 백오프 {npr_bo:.0f} dB")
    for p in DEVICE_W:
        print(f"  {p:5.0f} W 소자 Ropt            {r_opt(p):6.2f} ohm "
              f"→ |Γ| {gammas[p]:.3f}")
    for lo in (0.0, 0.5, 1.0, 2.0):
        print(f"  수동 튜너 · 손실 {lo:.1f} dB      최대 |Γ| "
              f"{reach_passive(lo):.3f}")
    print(f"  300 W · |Γ| {gammas[300.0]:.2f} 를 능동으로 만들려면 "
          f"{p_inject_w(gammas[300.0], 300.0, 1.0):.0f} W 주입")
    for k, v in aclr.items():
        print(f"  ACLR {k:12s}         하 {v[0]:6.1f} / 상 {v[1]:6.1f} dBc")
    print(f"  신호 파고율                   입력 {papr_in:.2f} dB → "
          f"전왜곡 후 {papr_pd:.2f} dB")
    for n in (16, 64, 256):
        print(f"  다중톤 {n:3d}개 PAPR           "
              f"전부 동위상 {multitone_papr(n, 'zero'):.2f} dB · "
              f"뉴먼 {multitone_papr(n, 'newman'):.2f} dB · "
              f"무작위 {multitone_papr(n, 'random'):.2f} dB")

    # ── 자체 검산 ───────────────────────────────────────────────────────
    print()
    print("[자체 검산]")
    ok = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  {'OK ' if cond else 'X  '} {msg}")

    # 정적 모형
    chk(abs(20 * np.log10(abs(rapp_gain(0.0))) - 0.0) < 1e-9,
        "작은 신호에서 이득 압축이 0 dB")
    chk(abs(np.angle(rapp_gain(0.0))) < 1e-9,
        "작은 신호에서 AM-PM 이 0 rad")
    chk(g1db < 0 and abs(g1db + 1.0) < 0.02,
        f"P1dB 점의 압축량 {g1db:.3f} dB (정의상 -1 dB)")
    chk(2.0 < ph1db < 20.0,
        f"P1dB 에서의 AM-PM {ph1db:.1f} deg 가 그럴듯한 범위")
    chk(abs(rapp_gain(10.0)) < abs(rapp_gain(1.0)) < abs(rapp_gain(0.1)),
        "구동이 커질수록 이득이 단조 감소")

    # 메모리 — 닫힌 식과 수치의 대조 (교차검증 ①)
    for df in (3e3, 3e4, 3e5, 1.5e6):
        cu, cl = im3_closed(0.30, df)
        nu, nl = two_tone_numeric(0.30, df)
        e_u = abs(20 * np.log10(nu / cu))
        e_l = abs(20 * np.log10(nl / cl))
        chk(e_u < 0.02 and e_l < 0.02,
            f"톤 간격 {df / 1e3:8.1f} kHz: FFT 와 닫힌 식 차 "
            f"{max(e_u, e_l):.4f} dB")

    chk(abs(h_bias(0.0) - 1.0) < 1e-12 and abs(h_therm(0.0) - 1.0) < 1e-12,
        "두 메모리 경로 모두 직류에서 H(0)=1 로 정규화")
    u0, l0 = im3_closed(0.30, 1.0)
    chk(abs(20 * np.log10(u0 / l0)) < 0.02,
        f"톤 간격이 0 에 가까우면 상·하 IM3 가 같다 "
        f"({20 * np.log10(u0 / l0):+.4f} dB)")
    u9, l9 = im3_closed(0.30, 1e9)
    chk(abs(20 * np.log10(u9 / l9)) < 0.05,
        "톤 간격이 아주 크면 메모리 경로가 죽어 다시 대칭이 된다")
    chk(abs(asym) > 2.0,
        f"중간 간격에서는 비대칭이 {abs(asym):.1f} dB 로 크다")
    f_res = 1 / (2 * np.pi * np.sqrt(L_B * C_B))
    chk(0.2 * f_res < asym_df < 5 * f_res,
        f"최대 비대칭 위치 {asym_df / 1e3:.0f} kHz 가 바이어스망 공진 "
        f"{f_res / 1e3:.0f} kHz 근처")
    ua, la = im3_closed(0.30, 3e5)
    ub, lb = im3_closed(0.60, 3e5)
    chk(abs(20 * np.log10(ub / ua) - 20 * np.log10(2) * 3) < 1e-9,
        "3차 항이므로 진폭 2배에 IM3 는 정확히 18.06 dB 오른다")
    chk(loop > 0.02, f"메모리가 있으면 히스테리시스 고리가 열린다 ({loop:.3f} dB)")

    # 펄스 — 닫힌 식과 시간적분의 대조 (교차검증 ②)
    for w, per in ((10e-6, 1000e-6), (50e-6, 500e-6), (200e-6, 400e-6)):
        c = float(dt_pulse_closed(w, per))
        nnum = dt_pulse_numeric(w, per)
        chk(abs(c - nnum) / c < 0.01,
            f"펄스 {w * 1e6:5.0f} us / 주기 {per * 1e6:4.0f} us: "
            f"닫힌 식 {c:6.2f} C vs 적분 {nnum:6.2f} C")
    chk(abs(float(dt_pulse_closed(1.0, 1.0000001)) - P_DISS_W * RTH_CW)
        / (P_DISS_W * RTH_CW) < 1e-3,
        "듀티를 100 % 로 밀면 CW 값에 수렴한다")
    chk(float(dt_pulse_closed(1e-7, 1e-2)) < 0.02 * P_DISS_W * RTH_CW,
        "아주 짧은 펄스는 CW 대비 2 % 미만만 데운다")
    chk(dt10 < P_DISS_W * RTH_CW / 5,
        f"10 us/1 % 조건의 상승 {dt10:.1f} C 가 CW "
        f"{P_DISS_W * RTH_CW:.0f} C 보다 훨씬 작다")

    # NPR
    chk(npr_dd[-1] > npr_dd[0] + 15,
        f"백오프를 주면 왜곡 NPR 이 개선된다 "
        f"({npr_dd[0]:.1f} → {npr_dd[-1]:.1f} dB)")
    slope = np.polyfit(npr_bos[2:9], npr_dd[2:9], 1)[0]
    chk(1.4 < slope < 3.0,
        f"왜곡 NPR 기울기 {slope:.2f} dB/dB (3차 왜곡이면 2 부근)")
    chk(npr_pk < SRC_NOTCH_DB,
        f"화면에 찍히는 NPR {npr_pk:.1f} dB 는 신호원 노치 "
        f"{SRC_NOTCH_DB:.0f} dB 를 절대 못 넘는다")
    chk(float(npr_measured(80.0, 30.0)) < SNR_MAX_DB - 30.0 + 0.01,
        "왜곡이 아무리 작아도 잡음 바닥이 NPR 을 잡는다")
    chk(0 < npr_bo < 18, f"최적 백오프 {npr_bo:.0f} dB 가 쓸어본 범위 안")

    # 로드풀
    chk(abs(r_opt(50.0) - 20.25) < 1e-9, f"50 W · Ropt {r_opt(50.0):.2f} ohm")
    chk(gammas[300.0] > reach_passive(0.5),
        f"300 W 소자가 원하는 |Γ| {gammas[300.0]:.3f} 는 손실 0.5 dB "
        f"수동 튜너의 한계 {reach_passive(0.5):.3f} 를 넘는다")
    chk(gammas[50.0] < reach_passive(2.0),
        f"50 W 소자 {gammas[50.0]:.3f} 는 손실 2 dB 튜너로도 닿는다")
    chk(abs(reach_passive(0.0) - GAMMA_TUNER) < 1e-12,
        "손실이 없으면 튜너 |Γ| 가 그대로 DUT 면에 온다")
    chk(p_inject_w(0.874, 300.0, 1.0) > 250.0,
        f"|Γ|=0.87 을 300 W 소자에 능동으로 만들려면 "
        f"{p_inject_w(0.874, 300.0, 1.0):.0f} W 가 든다")

    # DPD 와 ACLR
    floor = max(aclr["입력 신호"])
    chk(floor < -70.0, f"측정 바닥 {floor:.1f} dBc (창함수 누설 한계)")
    chk(max(aclr["보정 없음"]) > floor + 25,
        f"보정 없는 ACLR {max(aclr['보정 없음']):.1f} dBc 가 바닥보다 "
        f"충분히 위 — 읽어도 되는 값")
    chk(max(aclr["무기억 DPD"]) < max(aclr["보정 없음"]) - 5,
        f"무기억 DPD 만으로도 {max(aclr['보정 없음']):.1f} → "
        f"{max(aclr['무기억 DPD']):.1f} dBc")
    chk(max(aclr["기억 DPD"]) < max(aclr["무기억 DPD"]) - 5,
        f"기억 항을 넣으면 {max(aclr['무기억 DPD']):.1f} → "
        f"{max(aclr['기억 DPD']):.1f} dBc 로 더 내려간다")
    chk(abs(aclr["보정 없음"][0] - aclr["보정 없음"][1]) > 0.5,
        f"보정 전 상·하 ACLR 이 {abs(aclr['보정 없음'][0] - aclr['보정 없음'][1]):.1f} dB "
        f"다르다 — 메모리의 흔적")
    chk(papr_pd > papr_in,
        f"전왜곡은 파고율을 키운다 ({papr_in:.2f} → {papr_pd:.2f} dB)")

    # 다중톤 파고율 (교차검증 ③)
    for n in (16, 64, 256):
        chk(abs(multitone_papr(n, "zero") - 10 * np.log10(n)) < 0.05,
            f"동위상 {n:3d} 톤 PAPR {multitone_papr(n, 'zero'):.2f} dB "
            f"= 10log10(N) {10 * np.log10(n):.2f} dB")
    chk(multitone_papr(64, "newman") < 6.0,
        f"뉴먼 위상 64 톤 PAPR {multitone_papr(64, 'newman'):.2f} dB < 6 dB")
    chk(multitone_papr(64, "newman") < multitone_papr(64, "random"),
        "뉴먼 위상이 무작위 위상보다 파고율이 낮다")

    print()
    if not all(ok):
        return 1
    print(f"  검산 {len(ok)}항목 전부 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
