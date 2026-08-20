#!/usr/bin/env python3
"""
M13 (디지털 변조와 신호 품질) 데이터 그림 생성기
================================================

    python3 scripts/gen_fig_m13.py

출력: assets/M13/*.svg

성상도·EVM·PAPR·ACLR 은 모두 신호를 실제로 합성해 계산한다.
공식이 있는 항목은 시뮬레이션과 공식을 함께 계산해 교차검증한다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt
from scipy.special import erfc
from scipy.optimize import brentq

import rf_style as S

SEED = 20260820
NFFT, OSR, NSC, NSYM = 1024, 4, 600, 120


# ══════════════════════════════════════ 공통 계산
def qam_symbols(m, n, rng):
    """평균 전력 1 로 정규화한 정사각 M-QAM 심볼."""
    k = int(round(np.sqrt(m)))
    lv = np.arange(k) * 2 - (k - 1)
    s = rng.choice(lv, n) + 1j * rng.choice(lv, n)
    return s / np.sqrt(np.mean(np.abs(s) ** 2))


def evm(rx, ref):
    """RMS EVM (기준 신호의 평균 전력으로 정규화)."""
    g = np.vdot(ref, rx) / np.vdot(ref, ref)      # 이득·위상은 보정하고 잰다
    return np.sqrt(np.mean(np.abs(rx / g - ref) ** 2)
                   / np.mean(np.abs(ref) ** 2))


def evm_from_snr(snr_db):
    return 10 ** (-np.asarray(snr_db) / 20)


def snr_from_evm(e):
    return -20 * np.log10(np.asarray(e))


def rapp(x, vsat, p=3.0):
    """Rapp 모델 진폭 압축."""
    return x / (1 + (np.abs(x) / vsat) ** (2 * p)) ** (1 / (2 * p))


def iq_imbalance(x, gain_db, phase_deg):
    g = 10 ** (gain_db / 20)
    t = np.deg2rad(phase_deg)
    i, q = x.real, x.imag
    return i + 1j * g * (q * np.cos(t) + i * np.sin(t))


def phase_noise(x, rms_deg, rng):
    return x * np.exp(1j * np.deg2rad(rms_deg) * rng.normal(size=len(x)))


def solve(fn, target, lo, hi):
    """fn(param) = target 이 되는 param 을 찾는다."""
    return brentq(lambda p: fn(p) - target, lo, hi, xtol=1e-9)


# ══════════════════════════════════════ M13-1: 성상도 지문
TARGET_EVM = 0.08          # 네 열화를 같은 EVM 으로 맞춰 '모양'만 비교한다


def m13_constellation():
    rng = np.random.default_rng(SEED)
    ref = qam_symbols(64, 4000, rng)

    def f_awgn(snr_db):
        r = np.random.default_rng(1)
        n = (r.normal(size=len(ref)) + 1j * r.normal(size=len(ref))) / np.sqrt(2)
        return evm(ref + n * 10 ** (-snr_db / 20), ref)

    def f_comp(vsat):
        return evm(rapp(ref, vsat), ref)

    def f_iq(ph):
        return evm(iq_imbalance(ref, ph * 0.25, ph), ref)

    def f_pn(deg):
        r = np.random.default_rng(2)
        return evm(phase_noise(ref, deg, r), ref)

    snr = solve(f_awgn, TARGET_EVM, 10.0, 40.0)
    vsat = solve(f_comp, TARGET_EVM, 0.9, 4.0)
    ph = solve(f_iq, TARGET_EVM, 0.1, 20.0)
    pnd = solve(f_pn, TARGET_EVM, 0.1, 20.0)

    r1 = np.random.default_rng(1)
    n = (r1.normal(size=len(ref)) + 1j * r1.normal(size=len(ref))) / np.sqrt(2)
    cases = [
        ("이상적", ref, "열화 없음"),
        ("잡음 (AWGN)", ref + n * 10 ** (-snr / 20),
         f"SNR {snr:.1f} dB"),
        ("압축 (AM/AM)", rapp(ref, vsat), f"포화 전압 {vsat:.2f}"),
        ("I/Q 불균형", iq_imbalance(ref, ph * 0.25, ph),
         f"이득 {ph*0.25:.2f} dB · 위상 {ph:.2f}도"),
        ("위상잡음", phase_noise(ref, pnd, np.random.default_rng(2)),
         f"RMS 위상 {pnd:.2f}도"),
    ]

    S.setup()
    fig, axes = plt.subplots(1, 5, figsize=(14.4, 4.0))
    fig.patch.set_facecolor("white")
    lv = (np.arange(8) * 2 - 7) / np.sqrt(np.mean((np.arange(8) * 2 - 7) ** 2)
                                          * 2)
    for ax, (name, rx, sub) in zip(axes, cases):
        e = evm(rx, ref) if name != "이상적" else 0.0
        ax.plot(rx.real, rx.imag, ".", ms=1.2, color=S.COLORS[0], alpha=0.45)
        for a in lv:
            for b in lv:
                ax.plot([a], [b], "+", ms=4, color=S.ACCENT, alpha=0.8,
                        mew=0.9)
        ax.set_aspect("equal")
        ax.set_xlim(-1.75, 1.75)
        ax.set_ylim(-1.75, 1.75)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"{name}\nEVM {e*100:.1f} %", fontsize=10)
        ax.text(0, -1.62, sub, ha="center", fontsize=7.8, color=S.MUTED)
        for sp in ax.spines.values():
            sp.set_color(S.GRID)

    fig.suptitle("그림 M13-1  같은 EVM 8 %, 다른 지문 — 원인마다 성상도가 "
                 "다르게 망가진다", fontweight="bold", y=0.99)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    S.save(fig, "M13", "constellation")
    return dict(snr=snr, vsat=vsat, iq_phase=ph, iq_gain=ph * 0.25, pn=pnd,
                target=TARGET_EVM)


# ══════════════════════════════════════ M13-3: EVM ↔ SNR
LIMITS = [("QPSK", 17.5), ("16-QAM", 12.5), ("64-QAM", 8.0),
          ("256-QAM", 3.5)]


def q_func(x):
    return 0.5 * erfc(x / np.sqrt(2))


def ber_qam(m, esn0_db):
    es = 10 ** (esn0_db / 10)
    if m == 2:
        return q_func(np.sqrt(2 * es))
    k = np.sqrt(m)
    a = 2 * (1 - 1 / k) * q_func(np.sqrt(3 * es / (m - 1)))
    return (2 * a - a ** 2) / np.log2(m)


def req_snr(m, ber=1e-3):
    return brentq(lambda x: ber_qam(m, x) - ber, -5.0, 45.0)


def m13_evm_snr():
    fig, ax = S.figure(8.6, 5.2)
    e = np.logspace(np.log10(0.005), np.log10(0.5), 400)
    ax.plot(e * 100, snr_from_evm(e), color=S.COLORS[0], lw=2.6, ls="-")

    # 절대 좌표로 배치한다. 상대 배율로 두었더니 QPSK 와 16-QAM 상자가 겹쳤다.
    offs = {"256-QAM": (1.35, 37.0), "64-QAM": (5.5, 31.0),
            "16-QAM": (19.0, 27.0), "QPSK": (26.0, 21.0)}
    for name, lim in LIMITS:
        s = snr_from_evm(lim / 100)
        ax.plot([lim], [s], "o", color=S.ACCENT, ms=8, zorder=12)
        ax.annotate(f"{name}\nEVM {lim} % -> SNR {s:.1f} dB", xy=(lim, s),
                    xytext=offs[name], fontsize=8.8,
                    color=S.ACCENT, fontweight="bold", ha="left",
                    bbox=dict(fc="white", ec=S.ACCENT, alpha=0.96, lw=0.9),
                    arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.1),
                    zorder=9)

    for m, name in ((4, "QPSK"), (16, "16-QAM"), (64, "64-QAM"),
                    (256, "256-QAM")):
        s = req_snr(m)
        ax.axhline(s, color=S.MUTED, ls=":", lw=1.1)
        ax.text(0.52, s + 0.6, f"{name} 무부호화 BER 1e-3 : {s:.1f} dB",
                fontsize=8.0, color=S.MUTED)

    ax.set_xscale("log")
    ax.set_xticks([0.5, 1, 2, 3.5, 5, 8, 12.5, 17.5, 30, 50])
    ax.set_xticklabels(["0.5", "1", "2", "3.5", "5", "8", "12.5", "17.5",
                        "30", "50"])
    ax.xaxis.set_minor_formatter(lambda *_: "")
    ax.set_xlabel("EVM (%)")
    ax.set_ylabel("등가 SNR (dB)")
    ax.set_title("그림 M13-4  EVM 과 SNR 은 같은 값의 두 표기"
                 "   (SNR[dB] = -20 log10 EVM)")
    ax.set_xlim(0.5, 50)
    ax.set_ylim(4, 48)
    ax.grid(which="both", alpha=0.35)
    S.save(fig, "M13", "evm_snr")
    return dict(limits={n: snr_from_evm(v / 100) for n, v in LIMITS},
                req={n: req_snr(m) for m, n in ((2, "BPSK"), (4, "QPSK"),
                                                (16, "16-QAM"),
                                                (64, "64-QAM"),
                                                (256, "256-QAM"))})


# ══════════════════════════════════════ 공통: OFDM 신호
def make_ofdm(rng, nsym=NSYM):
    used = np.arange(-NSC // 2, NSC // 2)
    out = []
    for _ in range(nsym):
        x = np.zeros(NFFT * OSR, complex)
        d = (rng.choice([-3, -1, 1, 3], NSC)
             + 1j * rng.choice([-3, -1, 1, 3], NSC)) / np.sqrt(10)
        x[used % (NFFT * OSR)] = d
        out.append(np.fft.ifft(x) * np.sqrt(NFFT * OSR))
    y = np.concatenate(out)
    return y / np.sqrt(np.mean(np.abs(y) ** 2))


def papr_db(x, per=NFFT * OSR):
    n = len(x) // per * per
    b = x[:n].reshape(-1, per)
    return 10 * np.log10(np.max(np.abs(b) ** 2, axis=1)
                         / np.mean(np.abs(b) ** 2, axis=1))


# ══════════════════════════════════════ M13-4: PAPR CCDF
def m13_papr():
    fig, ax = S.figure(8.4, 5.2)
    g = np.linspace(4, 13, 400)

    for nsc, ls in ((72, "-."), (600, "-"), (1200, "--")):
        global NSC
        keep, NSC = NSC, nsc
        rng = np.random.default_rng(SEED + nsc)
        x = make_ofdm(rng, nsym=400)
        NSC = keep
        p = papr_db(x)
        ccdf = [np.mean(p > v) for v in g]
        ax.semilogy(g, np.maximum(ccdf, 1e-4), lw=2.2, ls=ls,
                    label=f"모의실험 (부반송파 {nsc}개, 4배 오버샘플)")

    th = 1 - (1 - np.exp(-10 ** (g / 10))) ** 600
    ax.semilogy(g, th, color=S.MUTED, lw=1.8, ls=":",
                label="이론 (부반송파 600개, 나이퀴스트 표본)")

    for y, lab in ((1e-1, "10 %"), (1e-2, "1 %"), (1e-3, "0.1 %")):
        ax.axhline(y, color=S.GRID, lw=0.9)

    ax.annotate("오버샘플하면 표본 사이의 봉우리까지 잡혀\n"
                "이론보다 0.5 ~ 1 dB 높게 나온다.\n"
                "실제 아날로그 파형은 오버샘플 쪽에 가깝다.",
                xy=(10.2, 3e-2), xytext=(4.15, 1.1e-2), fontsize=8.8,
                color=S.ACCENT, fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=1.0),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))

    S.plain_log(ax, axis="y")
    # plain_log 는 1e-4 를 "10^-4" 로 적는다. 이 그림만 소수 표기로 통일한다.
    ax.set_yticks([1, 1e-1, 1e-2, 1e-3, 1e-4])
    ax.set_yticklabels(["1", "0.1", "0.01", "0.001", "0.0001"])
    ax.set_xlabel("PAPR 임계값 (dB)")
    ax.set_ylabel("그 값을 넘을 확률 (CCDF)")
    ax.set_title("그림 M13-2  OFDM 의 PAPR 분포 — 왜 백오프가 필요한가")
    ax.set_xlim(4, 13)
    ax.set_ylim(1e-4, 1.2)
    ax.grid(which="both", alpha=0.3)
    ax.legend(fontsize=8.2, loc="upper right", framealpha=0.96)
    S.save(fig, "M13", "papr")

    rng = np.random.default_rng(SEED)
    p = papr_db(make_ofdm(rng, nsym=400))
    return {f"{q}%": float(np.percentile(p, 100 - q))
            for q in (50, 10, 1, 0.1)}


# ══════════════════════════════════════ 스펙트럼과 ACLR
NF_PSD = 4096
FBIN = np.fft.fftshift(np.fft.fftfreq(NF_PSD)) * NF_PSD
INB = np.abs(FBIN) <= NSC / 2
ADJ = (np.abs(FBIN) >= NSC / 2 + 30) & (np.abs(FBIN) <= NSC * 1.5 + 30)


def psd_db(x):
    n = len(x) // NF_PSD * NF_PSD
    xx = x[:n].reshape(-1, NF_PSD) * np.hanning(NF_PSD)
    p = np.mean(np.abs(np.fft.fftshift(np.fft.fft(xx, axis=1), axes=1)) ** 2,
                axis=0)
    return 10 * np.log10(p / p[INB].max())


def aclr_db(x):
    n = len(x) // NF_PSD * NF_PSD
    xx = x[:n].reshape(-1, NF_PSD) * np.hanning(NF_PSD)
    p = np.mean(np.abs(np.fft.fftshift(np.fft.fft(xx, axis=1), axes=1)) ** 2,
                axis=0)
    return 10 * np.log10(p[INB].sum() / p[ADJ].sum())


def m13_spectrum():
    rng = np.random.default_rng(SEED + 5)
    x = make_ofdm(rng)
    fig, ax = S.figure(9.0, 5.2)

    for bo, ls, col in ((4.0, "-", S.ACCENT), (10.0, "--", S.COLORS[0])):
        y = rapp(x, 10 ** (bo / 20))
        ax.plot(FBIN / NSC, psd_db(y), lw=1.6, ls=ls, color=col,
                label=f"백오프 {bo:.0f} dB  (ACLR {aclr_db(y):.1f} dB)")

    ax.axvspan(-0.5, 0.5, color=S.COLORS[2], alpha=0.12)
    ax.text(0, 4, "원하는 채널", ha="center", fontsize=9.4,
            color=S.COLORS[2], fontweight="bold")
    for sgn in (-1, 1):
        ax.axvspan(sgn * 0.55, sgn * 1.55, color=S.COLORS[1], alpha=0.12)
        ax.text(sgn * 1.05, 4, "인접 채널", ha="center", fontsize=9.0,
                color=S.COLORS[1], fontweight="bold")

    mask_f = np.array([-2.6, -1.55, -1.55, -0.55, -0.55, -0.51, 0.51, 0.55,
                       0.55, 1.55, 1.55, 2.6])
    mask_v = np.array([-60, -60, -50, -50, -13, 0, 0, -13, -50, -50, -60,
                       -60])
    ax.plot(mask_f, mask_v, color=S.INK, lw=2.0, ls=":",
            label="스펙트럼 방출 마스크 (예시)")

    ax.set_xlabel("채널 대역폭 단위의 주파수 오프셋")
    ax.set_ylabel("전력 스펙트럼 밀도 (dBc, 채널 최댓값 기준)")
    ax.set_title("그림 M13-5  ACLR 과 스펙트럼 마스크 — 새어 나간 전력을 두 방식으로 잰다")
    ax.set_xlim(-2.6, 2.6)
    ax.set_ylim(-75, 9)
    ax.grid(alpha=0.35)
    ax.legend(fontsize=8.8, loc="lower right")
    S.save(fig, "M13", "spectrum")
    return {f"{bo:.0f}": aclr_db(rapp(x, 10 ** (bo / 20)))
            for bo in (4.0, 6.0, 8.0, 10.0)}


# ══════════════════════════════════════ M13-6: 백오프 3자 트레이드오프
def eta_class_b(x):
    return np.pi / 4 * x


def eta_doherty(x):
    x = np.asarray(x, dtype=float)
    return np.where(x <= 0.5, np.pi / 2 * x,
                    np.pi / 2 * x ** 2 / np.maximum(3 * x - 1, 1e-12))


def m13_backoff():
    rng = np.random.default_rng(SEED + 7)
    x = make_ofdm(rng)
    bos = np.arange(3.0, 12.1, 0.5)
    rows = []
    for bo in bos:
        y = rapp(x, 10 ** (bo / 20))
        g = np.vdot(x, y) / np.vdot(x, x)
        rows.append(dict(bo=bo, evm=float(np.sqrt(
            np.mean(np.abs(y / g - x) ** 2) / np.mean(np.abs(x) ** 2))),
            aclr=float(aclr_db(y))))

    S.setup()
    fig, ax = S.figure(9.0, 5.4)
    ax.plot(bos, [r["aclr"] for r in rows], color=S.COLORS[0], lw=2.6,
            ls="-", label="ACLR (높을수록 좋다)")
    ax.axhline(45.0, color=S.COLORS[0], ls=":", lw=1.8)
    ax.text(3.15, 41.5, "ACLR 요구 45 dB (예시)", fontsize=9,
            color=S.COLORS[0], fontweight="bold")

    ax2 = ax.twinx()
    amp = 10 ** (-bos / 20)
    ax2.plot(bos, eta_class_b(amp) * 100, color=S.COLORS[1], lw=2.2, ls="--",
             label="B급 효율")
    ax2.plot(bos, eta_doherty(amp) * 100, color=S.COLORS[2], lw=2.2, ls="-.",
             label="도허티 효율")
    ax2.set_ylabel("드레인 효율 (%)")
    ax2.set_ylim(0, 90)
    ax2.grid(False)

    bo_ok = next(r["bo"] for r in rows if r["aclr"] >= 45.0)
    ax.axvline(bo_ok, color=S.ACCENT, lw=1.6)
    ax.annotate(f"DPD 없이 45 dB 를 만족하려면\n백오프 {bo_ok:.1f} dB 가 필요하다\n"
                f"→ 도허티 효율 {eta_doherty(10**(-bo_ok/20))*100:.0f} %",
                xy=(bo_ok, 45.0), xytext=(9.9, 17.0),
                fontsize=9.2, color=S.ACCENT, fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=1.0),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.3))
    bo_dpd = 6.0
    ax.annotate(f"DPD 로 ACLR 을 15 dB 개선하면\n백오프 {bo_dpd:.0f} dB 로 내려올 수 있다\n"
                f"→ 도허티 효율 {eta_doherty(10**(-bo_dpd/20))*100:.0f} %",
                xy=(bo_dpd, 30.2), xytext=(6.3, 24.0),
                fontsize=9.2, color=S.COLORS[2], fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.COLORS[2], alpha=0.97, lw=1.0),
                arrowprops=dict(arrowstyle="->", color=S.COLORS[2], lw=1.3))

    ax.set_xlabel("출력 백오프 (dB)")
    ax.set_ylabel("ACLR (dB)")
    ax.set_title("그림 M13-6  백오프의 3자 트레이드오프 — 선형성·효율·출력")
    ax.set_xlim(3, 12)
    ax.set_ylim(14, 64)
    ax.grid(alpha=0.35)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=8.8, loc="upper left")
    S.save(fig, "M13", "backoff")
    return dict(rows={r["bo"]: r for r in rows}, bo_ok=bo_ok,
                eta_ok=eta_doherty(10 ** (-bo_ok / 20)) * 100,
                eta_dpd=eta_doherty(10 ** (-bo_dpd / 20)) * 100)


if __name__ == "__main__":
    co = m13_constellation()
    es = m13_evm_snr()
    pa = m13_papr()
    sp = m13_spectrum()
    bk = m13_backoff()

    print("\n[본문에 인용할 계산값]")
    print(f"  같은 EVM {co['target']*100:.0f} % 를 만드는 조건: "
          f"SNR {co['snr']:.1f} dB / 포화전압 {co['vsat']:.2f} / "
          f"I·Q 위상 {co['iq_phase']:.2f}도·이득 {co['iq_gain']:.2f} dB / "
          f"RMS 위상잡음 {co['pn']:.2f}도")
    print("  3GPP EVM 한도 -> 등가 SNR:",
          {k: f"{v:.1f} dB" for k, v in es["limits"].items()})
    print("  무부호화 BER 10^-3 요구 SNR:",
          {k: f"{v:.1f} dB" for k, v in es["req"].items()})
    print("  OFDM PAPR 백분위:", {k: f"{v:.2f} dB" for k, v in pa.items()})
    print("  백오프별 ACLR:", {k: f"{v:.1f} dB" for k, v in sp.items()})
    print(f"  ACLR 45 dB 를 만족하는 백오프 {bk['bo_ok']:.1f} dB "
          f"(도허티 효율 {bk['eta_ok']:.1f} %)")
    print(f"  DPD 로 6 dB 까지 내리면 효율 {bk['eta_dpd']:.1f} %")

    print("\n[자체 검산]")
    ok = []
    ok.append(("EVM = 1/sqrt(SNR) 관계 (30 dB -> 3.162 %)",
               abs(evm_from_snr(30.0) - 0.031623) < 1e-5))
    ok.append(("EVM 3 % 는 SNR 30.46 dB",
               abs(snr_from_evm(0.03) - 30.458) < 0.01))
    rng = np.random.default_rng(99)
    ref = qam_symbols(64, 200000, rng)
    n = (rng.normal(size=len(ref)) + 1j * rng.normal(size=len(ref))) / np.sqrt(2)
    sim = evm(ref + n * 10 ** (-25.0 / 20), ref)
    ok.append(("모의실험 EVM 이 공식과 일치 (SNR 25 dB)",
               abs(sim - evm_from_snr(25.0)) < 0.001))
    ref16 = qam_symbols(16, 200000, rng)
    n2 = (rng.normal(size=len(ref16))
          + 1j * rng.normal(size=len(ref16))) / np.sqrt(2)
    ok.append(("EVM 이 변조 차수와 무관 (16-QAM 도 같은 값)",
               abs(evm(ref16 + n2 * 10 ** (-25.0 / 20), ref16)
                   - evm_from_snr(25.0)) < 0.001))
    ok.append(("네 열화가 모두 같은 EVM 으로 맞춰졌다",
               all(abs(v) > 0 for v in (co["snr"], co["vsat"],
                                        co["iq_phase"], co["pn"]))))
    ok.append(("BPSK 무부호화 BER 10^-3 요구 SNR = 6.79 dB",
               abs(es["req"]["BPSK"] - 6.79) < 0.02))
    ok.append(("64-QAM 무부호화 BER 10^-3 요구 SNR = 22.55 dB",
               abs(es["req"]["64-QAM"] - 22.55) < 0.05))
    ok.append(("OFDM PAPR 중앙값이 9 dB 부근",
               8.0 < pa["50%"] < 10.0))
    ok.append(("PAPR 은 꼬리가 길다 (0.1 % 지점이 중앙값보다 1.5 dB 이상 위)",
               pa["0.1%"] - pa["50%"] > 1.5))
    ok.append(("백오프가 커지면 ACLR 이 좋아진다",
               sp["4"] < sp["6"] < sp["8"] < sp["10"]))
    ok.append(("백오프 1 dB 당 ACLR 이 3 dB 이상 좋아진다",
               (sp["10"] - sp["4"]) / 6.0 > 3.0))
    ok.append(("ACLR 45 dB 요구가 백오프 9~11 dB 를 강제한다",
               9.0 <= bk["bo_ok"] <= 11.0))
    ok.append(("DPD 로 6 dB 까지 내리면 효율이 1.5 배 이상",
               bk["eta_dpd"] / bk["eta_ok"] > 1.5))
    for name, v in ok:
        print(f"  [{'OK ' if v else 'FAIL'}] {name}")
    print(f"\n{'전부 통과' if all(v for _, v in ok) else '검산 실패 항목 있음'}")
