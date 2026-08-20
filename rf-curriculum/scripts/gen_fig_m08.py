#!/usr/bin/env python3
"""
M08 (증폭기) 데이터 그림 생성기
================================

    python3 scripts/gen_fig_m08.py

출력: assets/M08/*.svg

이 모듈의 그림은 계산이 까다로워, 각 함수가 본문에 인용할 값을 함께
돌려주고 __main__ 에서 자체 검산까지 출력한다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt

import rf_style as S

# ── 예제 트랜지스터 (한 주파수에서의 S-파라미터와 잡음 파라미터) ────────
# 교육용으로 만든 값이며 특정 실제 소자가 아니다. K < 1 (조건부 안정)이
# 되도록 골랐다 — 실무에서 흔하고, 안정도 원을 그릴 이유가 생기기 때문.
S11 = 0.80 * np.exp(1j * np.deg2rad(-80))
S21 = 2.50 * np.exp(1j * np.deg2rad(+80))
S12 = 0.06 * np.exp(1j * np.deg2rad(+40))
S22 = 0.70 * np.exp(1j * np.deg2rad(-60))

FMIN_DB = 0.8                    # 최소 잡음지수 [dB]
GAMMA_OPT = 0.50 * np.exp(1j * np.deg2rad(60))
RN = 15.0                        # 등가 잡음 저항 [ohm]
Z0 = 50.0


def delta():
    return S11 * S22 - S12 * S21


def k_factor():
    d = abs(delta())
    return ((1 - abs(S11) ** 2 - abs(S22) ** 2 + d ** 2)
            / (2 * abs(S12 * S21)))


def mu_factor():
    """mu 계수. mu > 1 하나로 무조건 안정 — K 와 |delta| 를 함께 봐야 하는
    Rollett 판정보다 실수할 여지가 적다. 이 형태는 모든 수동 부하(|GammaL| <= 1)
    를 훑는 판정이며, S11 과 S22 를 바꾸면 소스 쪽 판정이 된다."""
    d = delta()
    return ((1 - abs(S11) ** 2)
            / (abs(S22 - d * np.conj(S11)) + abs(S12 * S21)))


def source_stability_circle():
    d = delta()
    c = np.conj(S11 - d * np.conj(S22)) / (abs(S11) ** 2 - abs(d) ** 2)
    r = abs(S12 * S21 / (abs(S11) ** 2 - abs(d) ** 2))
    return c, r


def load_stability_circle():
    d = delta()
    c = np.conj(S22 - d * np.conj(S11)) / (abs(S22) ** 2 - abs(d) ** 2)
    r = abs(S12 * S21 / (abs(S22) ** 2 - abs(d) ** 2))
    return c, r


def nf_db(gamma_s):
    """소스 반사계수 gamma_s 일 때의 잡음지수 [dB]."""
    fmin = 10 ** (FMIN_DB / 10)
    f = (fmin + 4 * RN / Z0 * abs(gamma_s - GAMMA_OPT) ** 2
         / ((1 - abs(gamma_s) ** 2) * abs(1 + GAMMA_OPT) ** 2))
    return 10 * np.log10(f)


def nf_circle(f_db):
    """잡음지수가 f_db 인 등잡음 원의 중심과 반지름."""
    f = 10 ** (f_db / 10)
    fmin = 10 ** (FMIN_DB / 10)
    n = (f - fmin) * abs(1 + GAMMA_OPT) ** 2 / (4 * RN / Z0)
    c = GAMMA_OPT / (1 + n)
    r = np.sqrt(n * (n + 1 - abs(GAMMA_OPT) ** 2)) / (1 + n)
    return c, r


def gamma_out(gamma_s):
    return S22 + S12 * S21 * gamma_s / (1 - S11 * gamma_s)


def gain_available_db(gamma_s):
    """가용 이득 Ga [dB] — 소스만 정하면 정해지는 이득."""
    go = gamma_out(gamma_s)
    ga = (abs(S21) ** 2 * (1 - abs(gamma_s) ** 2)
          / (abs(1 - S11 * gamma_s) ** 2 * (1 - abs(go) ** 2)))
    return 10 * np.log10(ga)


def gain_circle(g_db):
    """등가용이득 원 (Gonzalez 표기)."""
    d = delta()
    ga = 10 ** (g_db / 10) / abs(S21) ** 2
    # 가용이득(Ga) 원은 소스 평면에 그린다 -> C1 을 쓴다.
    # C2 (= S22 - d*conj(S11)) 는 부하 평면의 동작이득(Gp) 원 공식이다.
    # 둘을 바꿔 쓰면 원 위의 점이 요구한 이득을 주지 않는다 (실제로 겪은 실수).
    c1 = S11 - d * np.conj(S22)
    den = 1 + ga * (abs(S11) ** 2 - abs(d) ** 2)
    c = ga * np.conj(c1) / den
    disc = 1 - 2 * k_factor() * abs(S12 * S21) * ga + (abs(S12 * S21) * ga) ** 2
    r = np.sqrt(max(disc, 0.0)) / abs(den)
    return c, r


# ══════════════════════════════════════════════════════════ 그림들
def m08_noise():
    """잡음지수의 정의(SNR 저하)와 잡음온도 환산."""
    # setup() 을 먼저 부른다. Figure 를 만든 뒤에 부르면 축 라벨과 눈금
    # 글씨가 이미 기본 폰트로 굳어 버려 한글이 네모(□)로 나온다.
    S.setup()
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.6))
    fig.patch.set_facecolor("white")

    # ── 왼쪽: 증폭기 하나를 통과할 때 신호와 잡음이 어떻게 되는가 ──
    bw_hz = 1e6
    n_in = -174.0 + 10 * np.log10(bw_hz)      # 열잡음 바닥 [dBm]
    s_in = -80.0                              # 입력 신호 [dBm]
    gain, nf = 20.0, 3.0
    s_out = s_in + gain
    n_out = n_in + gain + nf
    snr_in, snr_out = s_in - n_in, s_out - n_out
    floor = -132

    ax = axes[0]
    for x, sg, ns in ((0, s_in, n_in), (1, s_out, n_out)):
        ax.bar(x, ns - floor, bottom=floor, width=0.36, color=S.MUTED,
               alpha=0.5, zorder=2)
        ax.bar(x, sg - ns, bottom=ns, width=0.36, color=S.COLORS[0],
               alpha=0.88, zorder=3)
        ax.plot([x - 0.24, x + 0.24], [sg, sg], color=S.INK, lw=2.2, zorder=5)
        ax.text(x, sg + 2.2, f"신호 {sg:.0f} dBm", ha="center", fontsize=9.2,
                fontweight="bold", color=S.INK)
        ax.text(x, ns - 7.0, f"잡음 {ns:.0f} dBm", ha="center", fontsize=9.2,
                color="#4d4d4d")
        ax.text(x, (sg + ns) / 2, f"SNR\n{sg-ns:.0f} dB", ha="center",
                va="center", fontsize=10.5, fontweight="bold", color="white",
                zorder=6)

    ax.annotate(f"SNR 이 {snr_in - snr_out:.0f} dB 나빠졌다.\n"
                f"이 저하량이 곧 잡음지수 NF = {nf:.0f} dB 다.",
                xy=(0.5, -96), xytext=(-0.50, -58), va="top",
                fontsize=9.4, color=S.ACCENT, fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=1.0),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.3))

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["증폭기 입력", "증폭기 출력"])
    ax.set_ylabel("전력 (dBm)")
    ax.set_ylim(floor, -48)
    ax.set_xlim(-0.55, 1.55)
    ax.set_title(f"이득 {gain:.0f} dB · NF {nf:.0f} dB 증폭기 한 단",
                 fontsize=10.5)
    ax.grid(axis="y", alpha=0.4)

    # ── 오른쪽: NF 와 잡음온도는 같은 것을 두 가지로 적은 것 ──
    ax = axes[1]
    nf_ax = np.linspace(0.02, 6.0, 500)
    te = 290.0 * (10 ** (nf_ax / 10) - 1)
    ax.plot(nf_ax, te, color=S.COLORS[0], lw=2.4, ls="-")

    marks = (0.5, 1.0, 2.0, 3.0)
    for f in marks:
        t = 290.0 * (10 ** (f / 10) - 1)
        ax.plot([f], [t], "o", color=S.ACCENT, ms=7, zorder=8)
    tbl = "\n".join(f"NF {f:.1f} dB  =  {290.0*(10**(f/10)-1):.0f} K"
                     for f in marks)
    ax.text(0.25, 960, "Te = T0 · (F − 1),   T0 = 290 K\n"
                       "F 는 배수, NF 는 그 배수를 dB 로 적은 것",
            fontsize=9.2, color=S.INK, ha="left", va="top",
            bbox=dict(fc="white", ec=S.GRID, alpha=0.97))
    ax.text(0.25, 820, tbl, fontsize=9.2, color=S.ACCENT, ha="left",
            va="top", fontweight="bold",
            bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=0.9))
    ax.text(3.15, 210, "위성 수신기·전파천문에서는 K 로,\n"
                       "이동통신에서는 dB 로 부른다.\n같은 물리량이다.",
            fontsize=9, color="#4d4d4d", ha="left", va="top",
            bbox=dict(fc="white", ec="none", alpha=0.85))
    ax.set_xlabel("잡음지수 NF (dB)")
    ax.set_ylabel("등가 잡음온도 Te (K)")
    ax.set_title("잡음지수와 잡음온도는 같은 값의 두 표기", fontsize=10.5)
    ax.set_xlim(0, 6.2)
    ax.set_ylim(0, 1050)
    ax.grid(alpha=0.4)

    fig.suptitle("그림 M08-2  잡음지수 — SNR 이 얼마나 나빠지는가",
                 fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M08", "noise")
    return dict(n_in=n_in, s_in=s_in, s_out=s_out, n_out=n_out,
                snr_in=snr_in, snr_out=snr_out, nf=nf, gain=gain, bw=bw_hz,
                te={f: 290.0 * (10 ** (f / 10) - 1)
                    for f in (0.5, 1.0, 2.0, 3.0, 6.0)})


def m08_compression():
    """이득 압축 곡선과 P1dB."""
    fig, ax = S.figure(7.6, 4.6)
    g0, psat = 20.0, 22.0                 # 소신호 이득 [dB], 포화 출력 [dBm]
    pin = np.linspace(-30, 12, 900)

    # Rapp 형 연성 포화 모델
    lin = pin + g0
    p = 3.0
    pout = lin - 10 / p * np.log10(1 + 10 ** (p * (lin - psat) / 10))

    S.reference_line(ax, pin, lin, label="이상적인 선형 연장선")
    ax.plot(pin, pout, color=S.COLORS[0], lw=2.4, ls="-", label="실제 출력")

    i1 = np.argmin(np.abs((lin - pout) - 1.0))
    p1_in, p1_out = pin[i1], pout[i1]
    ax.plot([p1_in], [p1_out], "o", color=S.ACCENT, ms=9, zorder=9)
    ax.annotate(f"P1dB\n입력 {p1_in:.1f} dBm / 출력 {p1_out:.1f} dBm\n"
                f"(이상선보다 정확히 1 dB 낮은 점)",
                xy=(p1_in, p1_out), xytext=(-29.0, 4.5), fontsize=9,
                color=S.ACCENT, fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.96, lw=0.9),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.3))

    ax.axhline(psat, color=S.MUTED, ls=":", lw=1.3)
    ax.text(-29, psat + 0.7, f"포화 출력 약 {psat:.0f} dBm", fontsize=9,
            color=S.MUTED)

    ax2 = ax.twinx()
    ax2.plot(pin, pout - pin, color=S.COLORS[1], ls="--", lw=1.8)
    ax2.set_ylabel("이득 (dB)", color=S.COLORS[1])
    ax2.tick_params(axis="y", labelcolor=S.COLORS[1])
    ax2.set_ylim(10, 22)
    ax2.grid(False)
    ax2.annotate("오른쪽 축: 이득\n이 값이 줄어드는 것이 '압축'",
                 xy=(-6.5, 14.6), fontsize=9,
                 color=S.COLORS[1], ha="center",
                 bbox=dict(fc="white", ec=S.COLORS[1], alpha=0.92, lw=0.8))

    ax.set_xlabel("입력 전력 (dBm)")
    ax.set_ylabel("출력 전력 (dBm)")
    ax.set_title("그림 M08-3  이득 압축 곡선과 1 dB 압축점")
    ax.set_ylim(-14, 26)
    ax.legend(loc="center right", fontsize=9)
    S.save(fig, "M08", "compression")
    return dict(p1_in=p1_in, p1_out=p1_out, g0=g0, psat=psat)


def m08_twotone():
    """2톤 시험의 스펙트럼 — IM3 는 왜 골치 아픈가."""
    fig, ax = S.figure(7.8, 4.4)
    f1, f2 = 2400.0, 2401.0                # MHz
    p_tone, iip3 = -20.0, 0.0              # dBm

    oip3 = iip3 + 20.0                     # 이득 20 dB 가정
    p_out = p_tone + 20.0
    im3 = 3 * p_out - 2 * oip3             # IM3 절대 레벨
    im5 = im3 - 25.0                       # 5차는 훨씬 작다 (예시)

    lines = [(2 * f1 - f2, im3, "IM3\n2f1-f2", S.ACCENT),
             (f1, p_out, "f1", S.COLORS[0]),
             (f2, p_out, "f2", S.COLORS[0]),
             (2 * f2 - f1, im3, "IM3\n2f2-f1", S.ACCENT),
             (3 * f1 - 2 * f2, im5, "IM5", S.COLORS[4]),
             (3 * f2 - 2 * f1, im5, "IM5", S.COLORS[4])]
    for f, p, name, col in lines:
        ax.plot([f, f], [-90, p], ls="-", lw=3.0, color=col,
                solid_capstyle="butt")
        ax.annotate(name, xy=(f, p), xytext=(f, p + 3.5), ha="center",
                    fontsize=8.8, color=col, fontweight="bold")

    ax.annotate(f"두 주 신호와 IM3 의 차이\n= {p_out - im3:.0f} dB",
                xy=(2400.5, (p_out + im3) / 2), ha="center", fontsize=9,
                color=S.INK, fontweight="bold",
                bbox=dict(fc="white", ec=S.GRID, alpha=0.95))
    ax.annotate("IM3 는 주 신호 바로 옆에 떨어진다\n= 필터로 걸러낼 수 없다",
                xy=(2 * f1 - f2, im3), xytext=(2397.15, -14), fontsize=9,
                color=S.ACCENT, fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.96, lw=0.9),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))

    ax.set_xlim(2397, 2404)
    ax.set_ylim(-90, 14)
    ax.set_xlabel("주파수 (MHz)")
    ax.set_ylabel("출력 전력 (dBm)")
    ax.set_title("그림 M08-4  2톤 시험의 출력 스펙트럼")
    S.save(fig, "M08", "twotone")
    return dict(p_out=p_out, im3=im3, oip3=oip3, delta=p_out - im3)


def m08_ip3():
    """IP3 는 외삽으로만 존재하는 가상의 점이다."""
    fig, ax = S.figure(7.6, 4.6)
    g0, iip3, psat = 20.0, 0.0, 22.0
    pin = np.linspace(-40, 8, 600)

    lin = pin + g0
    p = 3.0
    fund = lin - 10 / p * np.log10(1 + 10 ** (p * (lin - psat) / 10))
    im3_ideal = 3 * (pin - iip3) + (iip3 + g0)      # 기울기 3, IP3 에서 만남

    m = pin < -6
    ax.plot(pin[m], fund[m], color=S.COLORS[0], lw=2.4, ls="-",
            label="기본파 (기울기 1)")
    ax.plot(pin[m], im3_ideal[m], color=S.ACCENT, lw=2.4, ls="-",
            label="IM3 (기울기 3)")
    S.reference_line(ax, pin, lin, label="기본파 외삽")
    ax.plot(pin, im3_ideal, color=S.ACCENT, ls=":", lw=1.4, alpha=0.75)
    ax.plot(pin, fund, color=S.COLORS[0], ls="--", lw=1.2, alpha=0.5,
            label="실제 기본파 (압축됨)")

    oip3 = iip3 + g0
    ax.plot([iip3], [oip3], "X", color=S.INK, ms=14, zorder=10)
    ax.annotate(f"IP3\nIIP3 = {iip3:.0f} dBm\nOIP3 = {oip3:.0f} dBm\n"
                "실제로는 도달할 수 없는 가상의 점",
                xy=(iip3, oip3), xytext=(-39.0, 40.0), fontsize=9, va="top",
                color=S.INK, fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.INK, alpha=0.96, lw=1.0),
                arrowprops=dict(arrowstyle="->", color=S.INK, lw=1.3))

    ax.axvline(-12.0, color=S.MUTED, ls=":", lw=1.2)
    ax.annotate("실제 측정은 이 근처 한 점에서만 하고\n나머지는 외삽한다\n"
                "(압축이 시작되기 전, 잡음보다는 위)",
                xy=(-12, -36), xytext=(-39, -62), fontsize=8.8,
                color=S.INK, ha="left",
                bbox=dict(fc="white", ec=S.MUTED, alpha=0.96, lw=0.8),
                arrowprops=dict(arrowstyle="->", color=S.MUTED, lw=1.1))

    ax.set_xlabel("입력 전력, 톤 하나당 (dBm)")
    ax.set_ylabel("출력 전력 (dBm)")
    ax.set_title("그림 M08-5  IP3 외삽 — 두 직선이 만나는 가상의 점")
    ax.set_ylim(-92, 46)
    ax.legend(loc="lower right", fontsize=8.6)
    S.save(fig, "M08", "ip3")
    return dict(iip3=iip3, oip3=oip3)


def _smith_grid(ax, r_vals=(0, 0.2, 0.5, 1, 2, 5), x_vals=(0.2, 0.5, 1, 2, 5)):
    th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(th), np.sin(th), color=S.INK, lw=1.4)
    ax.plot([-1, 1], [0, 0], color=S.INK, lw=1.0)
    for r in r_vals:
        c, rad = r / (1 + r), 1 / (1 + r)
        ax.plot(c + rad * np.cos(th), rad * np.sin(th), color="#D5D5D5", lw=0.8)
    for x in x_vals:
        rad = 1 / x
        for sgn in (+1, -1):
            t = np.linspace(0, 2 * np.pi, 900)
            xs, ys = 1 + rad * np.cos(t), sgn * rad + rad * np.sin(t)
            mm = xs ** 2 + ys ** 2 <= 1.0
            ax.plot(xs[mm], ys[mm], color="#D5D5D5", lw=0.8)
    ax.set_aspect("equal")
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    ax.axis("off")


def _circle(ax, c, r, **kw):
    th = np.linspace(0, 2 * np.pi, 400)
    return ax.plot(c.real + r * np.cos(th), c.imag + r * np.sin(th), **kw)


def best_on_nf_circle(f_db, margin=0.10):
    """NF 가 f_db 인 원 위에서, 안정 영역 안에 있으면서 Ga 가 가장 큰 점.

    설계자가 실제로 하는 일을 그대로 코드로 옮긴 것이다 —
    "잡음은 이만큼까지 양보한다. 그 안에서 이득을 최대로."
    """
    c, r = nf_circle(f_db)
    cs, rs = source_stability_circle()
    best = None
    for a in np.linspace(0, 360, 3601):
        g = c + r * np.exp(1j * np.deg2rad(a))
        if abs(g) >= 0.95:                       # 물리적으로 무리한 소스
            continue
        if abs(g - cs) < rs + margin:            # 불안정 원에서 margin 만큼 떨어뜨림
            continue
        v = gain_available_db(g)
        if best is None or v > best[0]:
            best = (v, g)
    return best[1]


def m08_design_chart():
    """LNA 설계 차트 — 안정도 원 · 잡음 원 · 이득 원을 한 장에."""
    fig, ax = S.figure(8.0, 8.0)
    _smith_grid(ax)
    ax.set_ylim(-1.12, 1.62)

    cs, rs = source_stability_circle()

    # 불안정 영역 칠하기.
    # 원 위의 점만 이어 칠하면 '활꼴'이 되어 실제 영역과 다르다.
    # 실제 불안정 영역은 (원 안쪽) ∩ (스미스 차트 안쪽) 이므로 격자로 칠한다.
    gx = np.linspace(-1.05, 1.05, 700)
    GX, GY = np.meshgrid(gx, gx)
    mask = (((GX - cs.real) ** 2 + (GY - cs.imag) ** 2 <= rs ** 2)
            & (GX ** 2 + GY ** 2 <= 1.0)).astype(float)
    ax.contourf(GX, GY, mask, levels=[0.5, 1.5], colors=[S.ACCENT],
                alpha=0.16, zorder=1)
    _circle(ax, cs, rs, color=S.ACCENT, lw=2.4, ls="-", zorder=4,
            label=f"소스 안정도 원 (K = {k_factor():.2f} < 1)")

    for f_db, ls in ((1.0, "-"), (1.5, "--"), (2.0, "-.")):
        c, r = nf_circle(f_db)
        _circle(ax, c, r, color=S.COLORS[2], lw=1.7, ls=ls, zorder=3,
                label=f"등잡음 원  NF = {f_db:.1f} dB")

    for g_db, ls in ((12.0, "-."), (14.0, "--"), (16.0, "-")):
        c, r = gain_circle(g_db)
        _circle(ax, c, r, color=S.COLORS[0], lw=1.7, ls=ls, zorder=3,
                label=f"등이득 원  Ga = {g_db:.0f} dB")

    g_des = best_on_nf_circle(1.0)

    pts = [(0 + 0j, "Γs = 0 (그냥 50 Ω)", S.MUTED, (-0.98, -0.46), "left"),
           (GAMMA_OPT, "Γ_opt (잡음 최소)", S.COLORS[2], (0.16, -0.40), "left"),
           (g_des, "Γ_설계 (절충안)", S.COLORS[0], (-1.16, 0.30), "left")]
    for g, name, col, off, ha in pts:
        ax.plot([g.real], [g.imag], "o", color=col, ms=11, zorder=11,
                mec="white", mew=1.4)
        ax.annotate(f"{name}\nNF {nf_db(g):.2f} dB / Ga "
                    f"{gain_available_db(g):.2f} dB",
                    xy=(g.real, g.imag),
                    xytext=(g.real + off[0], g.imag + off[1]),
                    fontsize=9, color=col, fontweight="bold", ha=ha,
                    bbox=dict(fc="white", ec=col, alpha=0.97, lw=0.9),
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.2),
                    zorder=12)

    ax.annotate("칠해진 곳이 불안정 영역\n(소스를 여기 두면 발진할 수 있다)",
                xy=(cs.real - 0.24, 0.93), xytext=(0.30, 1.30),
                fontsize=9.2, color=S.ACCENT, fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=0.9),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2),
                zorder=12)
    ax.text(-1.30, 1.36, "등이득 원은 불안정 영역에 붙을수록 이득이 크다.\n"
                          "Ga = 16 dB 원이 안정도 원에 닿아 있는 것이 그 증거다.",
            fontsize=8.8, color=S.COLORS[0], ha="left", va="top",
            bbox=dict(fc="white", ec=S.COLORS[0], alpha=0.97, lw=0.8),
            zorder=12)
    ax.text(-0.30, -0.74, "쓸 만한 영역이 모두 차트 위쪽 반에 있다\n"
                          "= 이 소자는 유도성 소스를 좋아한다\n"
                          f"(Γ_opt 는 {Z0*(1+GAMMA_OPT)/(1-GAMMA_OPT):.0f} 옴)",
            fontsize=8.6, color=S.INK, ha="left", va="top",
            bbox=dict(fc="white", ec=S.GRID, alpha=0.95), zorder=12)

    ax.set_title("그림 M08-6  LNA 설계 차트 — 안정도·잡음·이득을 한 장에",
                 fontweight="bold", y=1.03)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 0.045), ncol=2,
              fontsize=8.6, framealpha=0.97)
    S.save(fig, "M08", "design_chart")
    return dict(k=k_factor(), mu=mu_factor(),
                cs=cs, rs=rs, cl=load_stability_circle()[0],
                rl=load_stability_circle()[1],
                g_des=g_des,
                nf_des=nf_db(g_des), ga_des=gain_available_db(g_des),
                nf_opt=nf_db(GAMMA_OPT), ga_opt=gain_available_db(GAMMA_OPT),
                nf_50=nf_db(0), ga_50=gain_available_db(0))


def _class_eff(alpha):
    """도통각 alpha [rad] 인 감소 도통각 증폭기의 최대 효율."""
    a2 = alpha / 2
    idc = (2 * np.sin(a2) - alpha * np.cos(a2)) / (1 - np.cos(a2))
    i1 = (alpha - np.sin(alpha)) / (1 - np.cos(a2))
    return 0.5 * i1 / idc


def m08_classes():
    """증폭기 급 — 도통각과 효율의 맞바꿈."""
    S.setup()
    fig, axes = plt.subplots(1, 2, figsize=(9.8, 4.3))
    fig.patch.set_facecolor("white")

    # 왼쪽: 도통 파형
    t = np.linspace(-np.pi, np.pi, 1200)
    for alpha, name, col in ((2 * np.pi, "A급 (360도)", S.COLORS[0]),
                             (1.4 * np.pi, "AB급 (약 250도)", S.COLORS[1]),
                             (np.pi, "B급 (180도)", S.COLORS[2]),
                             (0.6 * np.pi, "C급 (약 110도)", S.COLORS[3])):
        i = np.cos(t) - np.cos(alpha / 2)
        i = np.where(np.abs(t) <= alpha / 2, i, 0.0)
        i = i / (1 - np.cos(alpha / 2))
        axes[0].plot(np.rad2deg(t), i, ls="-", lw=2.0, color=col, label=name)
    axes[0].axhline(0, color=S.MUTED, lw=0.9)
    axes[0].annotate("", xy=(-90, -0.10), xytext=(90, -0.10),
                     arrowprops=dict(arrowstyle="<->", color=S.COLORS[2],
                                     lw=1.4))
    axes[0].text(0, -0.20, "B급의 도통각 = 180도", fontsize=8.6, ha="center",
                 va="center", color=S.COLORS[2], fontweight="bold")
    axes[0].set_xlabel("한 주기 안에서의 위상 (도)")
    axes[0].set_ylabel("드레인 전류 (최댓값을 1 로 정규화)")
    axes[0].set_title("도통각 = 전류가 0 보다 큰 구간의 폭", fontsize=10.5)
    axes[0].set_xlim(-180, 180)
    axes[0].set_ylim(-0.30, 1.14)
    axes[0].set_xticks([-180, -90, 0, 90, 180])
    axes[0].legend(fontsize=8.4, loc="upper right", framealpha=0.95)
    axes[0].grid(alpha=0.5)

    # 오른쪽: 효율 곡선
    al = np.linspace(0.05 * np.pi, 2 * np.pi, 600)
    eff = np.array([_class_eff(a) for a in al])
    axes[1].plot(np.rad2deg(al), eff * 100, color=S.COLORS[0], ls="-", lw=2.4)
    for a, name, tx in ((2 * np.pi, "A급  50.0 %", (296, 28)),
                        (np.pi, "B급  78.5 %", (232, 88)),
                        (0.6 * np.pi, "C급(110도)  91.5 %", (150, 99))):
        e = _class_eff(a) * 100
        axes[1].plot([np.rad2deg(a)], [e], "o", color=S.ACCENT, ms=8, zorder=8)
        axes[1].annotate(name, xy=(np.rad2deg(a), e), xytext=tx, fontsize=8.8,
                         color=S.ACCENT, fontweight="bold", ha="center",
                         bbox=dict(fc="white", ec=S.ACCENT, alpha=0.95,
                                   lw=0.8),
                         arrowprops=dict(arrowstyle="->", color=S.ACCENT,
                                         lw=1.0))
    axes[1].axvspan(180, 360, color=S.COLORS[2], alpha=0.12)
    axes[1].annotate("AB급 구간\n(선형성과 효율의 절충)", xy=(270, 9),
                     ha="center", fontsize=8.8, color=S.INK,
                     bbox=dict(fc="white", ec=S.GRID, alpha=0.96))
    axes[1].set_xlabel("도통각 (도)")
    axes[1].set_ylabel("이론 최대 효율 (%)")
    axes[1].set_title("도통각이 줄면 효율은 오르고 선형성은 떨어진다",
                      fontsize=10.5)
    axes[1].text(8, 6, "가로축을 왼쪽으로 갈수록 도통각이 짧다\n"
                       "(세로축은 손실이 전혀 없다고 볼 때의 상한)",
                 fontsize=8.2, color=S.MUTED, ha="left")
    axes[1].set_xlim(0, 370)
    axes[1].set_ylim(0, 114)
    axes[1].grid(alpha=0.5)

    fig.suptitle("그림 M08-7  증폭기 급 — 도통각과 효율", fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M08", "classes")
    return {name: _class_eff(a) for a, name in
            ((2 * np.pi, "A"), (1.4 * np.pi, "AB(250도)"),
             (np.pi, "B"), (0.6 * np.pi, "C(110도)"))}


def eta_class_b(x):
    """B급 이상 효율. x = 정규화 출력 전압 진폭 (1 이 최대 출력)."""
    return np.pi / 4 * x


def eta_class_a(x):
    """A급 이상 효율. 직류 전류가 일정하므로 출력 전력에 그대로 비례한다."""
    return 0.5 * x ** 2


def eta_doherty(x):
    """이상적 대칭 도허티 효율.

    유도 (본문 §8.9 와 같은 기호):
      주 증폭기가 x = 0.5 에서 전압 포화한다. 그 아래에서는 주 증폭기만
      동작하고, 그 위에서는 보조 증폭기가 켜지며 주 증폭기의 부하를 낮춘다.
        x <= 0.5 : eta = (pi/2) x
        x >= 0.5 : eta = (pi/2) x^2 / (3x - 1)
      두 식은 x = 0.5 에서 값이 같고(연속), x = 1 과 x = 0.5 에서 모두
      pi/4 = 78.54 % 로 최대가 된다. 그 사이 x = 2/3 (백오프 3.52 dB)에서
      69.81 % 로 살짝 내려앉는다 — 도허티 곡선의 '안장'이다.
    """
    x = np.asarray(x, dtype=float)
    return np.where(x <= 0.5, np.pi / 2 * x,
                    np.pi / 2 * x ** 2 / np.maximum(3 * x - 1, 1e-12))


def m08_backoff():
    """출력 백오프와 효율 — 왜 도허티가 필요한가."""
    fig, ax = S.figure(7.8, 4.6)
    bo = np.linspace(0, 16, 800)               # 최대 출력 대비 백오프 [dB]
    x = 10 ** (-bo / 20)                       # 정규화 출력 전압 진폭

    ax.plot(bo, eta_class_a(x) * 100, ls="--", lw=2.0, color=S.COLORS[1],
            label="A급 (이상)")
    ax.plot(bo, eta_class_b(x) * 100, ls="-", lw=2.0, color=S.COLORS[0],
            label="B급 (이상)")
    S.emph(ax, bo, eta_doherty(x) * 100, color=S.COLORS[2],
           label="도허티 (이상, 6 dB 대칭)")

    ax.axvline(6, color=S.ACCENT, ls=":", lw=1.6)
    e6 = eta_doherty(10 ** (-6 / 20)) * 100
    ax.plot([6], [e6], "o", color=S.ACCENT, ms=9, zorder=10)
    ax.annotate(f"6 dB 백오프에서 효율이\n다시 {e6:.0f} %로 솟는다",
                xy=(6, e6), xytext=(7.6, 68), fontsize=9.2,
                color=S.ACCENT, fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.96, lw=0.9),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))

    xs = 2 / 3
    bs = -20 * np.log10(xs)
    es = eta_doherty(xs) * 100
    ax.plot([bs], [es], "o", color=S.MUTED, ms=7, zorder=10)
    ax.annotate(f"안장 {es:.0f} % ({bs:.1f} dB)", xy=(bs, es),
                xytext=(bs + 0.5, es + 9), fontsize=8.8, color=S.MUTED,
                arrowprops=dict(arrowstyle="->", color=S.MUTED, lw=1.0))

    b8 = 8.0
    ax.annotate("현대 변조 신호(OFDM)는 PAPR 이 커서\n"
                "평균 전력이 이 부근에 놓인다 (→ M13)\n"
                f"여기서 B급 {eta_class_b(10**(-b8/20))*100:.0f} % 대 "
                f"도허티 {eta_doherty(10**(-b8/20))*100:.0f} %",
                xy=(b8, 12), fontsize=9, color=S.INK, ha="left",
                bbox=dict(fc="white", ec=S.GRID, alpha=0.96))

    ax.set_xlabel("출력 백오프 (최대 출력 대비, dB)")
    ax.set_ylabel("드레인 효율 (%)")
    ax.set_title("그림 M08-8  백오프와 효율 — 도허티가 푸는 문제")
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 92)
    ax.legend(fontsize=9.2, loc="upper right")
    S.save(fig, "M08", "backoff")
    return dict(e_max=eta_doherty(1.0) * 100, e6=e6, es=es, bs=bs,
                b8_b=eta_class_b(10 ** (-b8 / 20)) * 100,
                b8_d=eta_doherty(10 ** (-b8 / 20)) * 100,
                b8_a=eta_class_a(10 ** (-b8 / 20)) * 100)


if __name__ == "__main__":
    nz = m08_noise()
    c = m08_compression()
    t = m08_twotone()
    i3 = m08_ip3()
    d = m08_design_chart()
    cl = m08_classes()
    bk = m08_backoff()

    z = lambda g: Z0 * (1 + g) / (1 - g)

    print("\n[본문에 인용할 계산값]")
    print(f"  잡음: 입력 신호 {nz['s_in']:.0f} dBm, 잡음바닥 {nz['n_in']:.0f} dBm "
          f"(1 MHz), SNR_in {nz['snr_in']:.0f} dB")
    print(f"        출력 신호 {nz['s_out']:.0f} dBm, 잡음 {nz['n_out']:.0f} dBm, "
          f"SNR_out {nz['snr_out']:.0f} dB, 저하 {nz['snr_in']-nz['snr_out']:.0f} dB")
    print("        NF -> Te:", {k: f"{v:.1f} K" for k, v in nz['te'].items()})
    print(f"  압축: 소신호 이득 {c['g0']:.0f} dB, "
          f"P1dB 입력 {c['p1_in']:.1f} dBm / 출력 {c['p1_out']:.1f} dBm")
    print(f"  2톤: 출력 톤 {t['p_out']:.0f} dBm, OIP3 {t['oip3']:.0f} dBm, "
          f"IM3 {t['im3']:.0f} dBm, 차이 {t['delta']:.0f} dB")
    print(f"  IP3: IIP3 {i3['iip3']:.0f} dBm, OIP3 {i3['oip3']:.0f} dBm")
    print(f"  트랜지스터: |S21|^2 = {20*np.log10(abs(S21)):.2f} dB, "
          f"|delta| = {abs(delta()):.4f}, K = {d['k']:.4f}, mu = {d['mu']:.4f}")
    print(f"  소스 안정도 원: 중심 {d['cs']:.3f} (크기 {abs(d['cs']):.3f}, "
          f"각 {np.rad2deg(np.angle(d['cs'])):.1f}도), 반지름 {d['rs']:.3f}")
    print(f"  부하 안정도 원: 중심 {d['cl']:.3f} (크기 {abs(d['cl']):.3f}), "
          f"반지름 {d['rl']:.3f}")
    print(f"  Γs = 0   (50 옴)   : NF {d['nf_50']:.2f} dB, Ga {d['ga_50']:.2f} dB")
    print(f"  Γs = Γ_opt        : NF {d['nf_opt']:.2f} dB, Ga {d['ga_opt']:.2f} dB, "
          f"Zs = {z(GAMMA_OPT):.2f} 옴")
    print(f"  Γs = Γ_design     : {d['g_des']:.4f} "
          f"(크기 {abs(d['g_des']):.3f}, 각 {np.rad2deg(np.angle(d['g_des'])):.1f}도), "
          f"NF {d['nf_des']:.2f} dB, Ga {d['ga_des']:.2f} dB, "
          f"Zs = {z(d['g_des']):.2f} 옴")
    print(f"  절충 이득: Γ_opt 대비 +{d['ga_des']-d['ga_opt']:.2f} dB, "
          f"잡음 대가 +{d['nf_des']-d['nf_opt']:.2f} dB")
    print("  급별 이론 최대 효율:", {k: f"{v*100:.1f} %" for k, v in cl.items()})

    print("\n[자체 검산]")
    ok = []
    ok.append(("K < 1 (조건부 안정)", k_factor() < 1))
    ok.append(("mu < 1 과 일치", (mu_factor() < 1) == (k_factor() < 1)))
    ok.append(("소스 안정도 원이 차트와 겹침",
               abs(d["cs"]) - d["rs"] < 1.0))
    ok.append(("Γs = 0 은 안정 영역 (원 바깥)",
               abs(0 - d["cs"]) > d["rs"]))
    ok.append(("Γ_opt 도 안정 영역", abs(GAMMA_OPT - d["cs"]) > d["rs"]))
    for f in (1.0, 1.5, 2.0):
        cc, rr = nf_circle(f)
        ok.append((f"NF 원({f} dB) 위의 점이 정말 {f} dB",
                   abs(nf_db(cc + rr * 0.999) - f) < 0.01))
    for g in (12.0, 14.0, 16.0):
        cc, rr = gain_circle(g)
        ok.append((f"Ga 원({g:.0f} dB) 위의 점이 정말 {g:.0f} dB",
                   abs(gain_available_db(cc + rr * 0.999) - g) < 0.05))
    ok.append(("Γ_opt 에서 NF 가 정확히 Fmin",
               abs(nf_db(GAMMA_OPT) - FMIN_DB) < 1e-9))
    ok.append(("NF 정의: SNR 저하량 = NF",
               abs((nz["snr_in"] - nz["snr_out"]) - nz["nf"]) < 1e-9))
    ok.append(("Te(290 K) 는 NF 3.0103 dB",
               abs(290.0 * (10 ** (3.0103 / 10) - 1) - 290.0) < 0.1))
    ok.append(("A급 효율 50 %", abs(_class_eff(2 * np.pi) - 0.5) < 1e-6))
    ok.append(("B급 효율 78.54 %",
               abs(_class_eff(np.pi) - np.pi / 4) < 1e-6))
    ok.append(("P1dB 점이 이상선보다 1 dB 아래",
               abs((c["p1_in"] + c["g0"] - c["p1_out"]) - 1.0) < 0.05))
    ok.append(("IM3 가 톤보다 2*(OIP3-Pout) 만큼 아래",
               abs(t["delta"] - 2 * (t["oip3"] - t["p_out"])) < 1e-9))
    for name, v in ok:
        print(f"  [{'OK ' if v else 'FAIL'}] {name}")
    print(f"\n{'전부 통과' if all(v for _, v in ok) else '검산 실패 항목 있음'}")
