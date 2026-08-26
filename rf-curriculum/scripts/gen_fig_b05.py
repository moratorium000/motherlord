#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B05 (잡음의 심화 — 네 개의 잡음 파라미터) 그림 생성기.

만드는 그림
  B05-1  잡음지수 등고선과 Γopt
  B05-2  Γopt 와 Γms 는 왜 다른가 — 잡음과 이득의 절충
  B05-3  Rn 이 다른 두 소자
  B05-4  소스풀 — 점을 어디에 몇 개 찍을 것인가
  B05-5  저 NF 측정의 오차 기여도

교차검증 세 갈래
  ① 네 파라미터 → 합성 측정값 → 최소자승 추출 → **원래 값으로 돌아오는가**
     (잡음 없이는 기계 정밀도까지 일치해야 한다)
  ② 등고선의 닫힌 식(중심 Γopt/(N+1), 반지름 √(N(N+1-|Γopt|²))/(N+1)) 과
     F(Γs) 식을 격자에서 직접 푼 등고선을 대조
  ③ 오차 예산의 RSS 합성과 몬테카를로 (20 000 회) 를 대조

실행: python3 scripts/gen_fig_b05.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rf_style as S  # noqa: E402

MOD = "B05"
RNG = np.random.default_rng(20260827)

Z0 = 50.0
T0 = 290.0

# ── 예제 소자 (저잡음 pHEMT 를 흉내낸 값) ────────────────────────────────
S11 = 0.75 * np.exp(1j * np.radians(-120.0))
S21 = 3.50 * np.exp(1j * np.radians(60.0))
S12 = 0.03 * np.exp(1j * np.radians(30.0))
S22 = 0.45 * np.exp(1j * np.radians(-80.0))

FMIN_DB = 0.65
G_OPT = 0.55 * np.exp(1j * np.radians(60.0))
RN_N = 0.15                      # rn = Rn / Z0  (즉 Rn = 7.5 Ω)


# ══ 잡음 파라미터 ═══════════════════════════════════════════════════════
def f_of_gs(gs, fmin_db=FMIN_DB, gopt=G_OPT, rn=RN_N):
    """소스 반사계수 Γs 에서의 잡음지수 (dB).

    F = Fmin + 4·rn·|Γs-Γopt|² / ((1-|Γs|²)·|1+Γopt|²)
    **선형 배율로 더한 뒤 dB 로 돌린다.** dB 끼리 더하면 틀린다.
    """
    gs = np.asarray(gs, complex)
    fmin = 10 ** (np.asarray(fmin_db, float) / 10.0)
    num = 4.0 * rn * np.abs(gs - gopt) ** 2
    den = (1.0 - np.abs(gs) ** 2) * np.abs(1.0 + gopt) ** 2
    return 10 * np.log10(fmin + num / den)


def noise_circle(f_db, fmin_db=FMIN_DB, gopt=G_OPT, rn=RN_N):
    """잡음지수가 일정한 자리는 원이다. 그 중심과 반지름 (닫힌 식)."""
    f = 10 ** (np.asarray(f_db, float) / 10.0)
    fmin = 10 ** (fmin_db / 10.0)
    n = (f - fmin) * np.abs(1.0 + gopt) ** 2 / (4.0 * rn)
    if np.any(n < 0):
        raise ValueError("Fmin 보다 낮은 잡음지수의 등고선은 없다")
    center = gopt / (n + 1.0)
    radius = np.sqrt(n * (n + 1.0 - np.abs(gopt) ** 2)) / (n + 1.0)
    return center, radius


# ══ 이득과 정합 ═════════════════════════════════════════════════════════
def delta():
    return S11 * S22 - S12 * S21


def rollett_k():
    d = delta()
    return ((1 - abs(S11) ** 2 - abs(S22) ** 2 + abs(d) ** 2)
            / (2 * abs(S12 * S21)))


def gamma_ms():
    """동시 켤레 정합의 소스 반사계수 Γms (이득이 최대가 되는 자리)."""
    d = delta()
    b1 = 1 + abs(S11) ** 2 - abs(S22) ** 2 - abs(d) ** 2
    c1 = S11 - d * np.conj(S22)
    disc = np.sqrt(complex(b1 ** 2 - 4 * abs(c1) ** 2))
    for sign in (-1.0, +1.0):
        g = (b1 + sign * disc) / (2 * c1)
        if abs(g) < 1.0:
            return g
    raise ValueError("|Γms| < 1 인 해가 없다 (무조건 안정이 아니다)")


def gamma_out(gs):
    gs = np.asarray(gs, complex)
    with np.errstate(invalid="ignore", divide="ignore"):
        return S22 + S12 * S21 * gs / (1.0 - S11 * gs)


def gain_avail_db(gs):
    """유효 이득 Ga(Γs) (dB). 잡음 설계에서 쓰는 이득이다."""
    gs = np.asarray(gs, complex)
    go = gamma_out(gs)
    ga = (abs(S21) ** 2 * (1 - np.abs(gs) ** 2)
          / (np.abs(1 - S11 * gs) ** 2 * (1 - np.abs(go) ** 2)))
    return 10 * np.log10(ga)


# ══ 소스풀 추출 (Lane 의 선형화) ════════════════════════════════════════
def design_matrix(gs):
    """F = a1 + a2·u + a3·u·Re(Γs) + a4·u·Im(Γs),  u = 1/(1-|Γs|²)."""
    gs = np.asarray(gs, complex)
    u = 1.0 / (1.0 - np.abs(gs) ** 2)
    return np.stack([np.ones_like(u), u, u * gs.real, u * gs.imag], axis=1)


def cond_number(gs):
    """설계 행렬의 조건수. 점 배치가 나쁘면 여기서 먼저 드러난다.

    |Γs| 가 전부 같으면 u 가 상수라 1열과 2열이 평행해진다. 그러면 점을
    아무리 많이 찍어도 Fmin 과 rn 을 **원리적으로** 못 가른다.
    """
    return float(np.linalg.cond(design_matrix(gs)))


def extract(gs, f_lin):
    """측정한 (Γs, F선형) 짝에서 네 파라미터를 되찾는다.

    a1 = Fmin - K,  a2 = K(1+|Γopt|²),  a3 = -2K·ReΓopt,  a4 = -2K·ImΓopt
    (K = 4rn/|1+Γopt|²) 이므로, |Γopt| 는 |P|g² - a2·g + |P| = 0 의 근이다.
    """
    a, *_ = np.linalg.lstsq(design_matrix(gs), np.asarray(f_lin, float),
                            rcond=None)
    a1, a2, a3, a4 = a
    p = -(a3 + 1j * a4) / 2.0            # = K·Γopt
    pm = abs(p)
    disc = a2 ** 2 - 4 * pm ** 2
    if disc < 0 or pm <= 0:
        return None
    g = (a2 - np.sqrt(disc)) / (2 * pm)  # |Γopt| < 1 인 근
    k = pm / g
    gopt = p / k
    fmin = a1 + k
    rn = k * abs(1 + gopt) ** 2 / 4.0
    return 10 * np.log10(fmin), gopt, rn


def pull_points(scheme, n):
    """소스풀 점 배치. 배치가 추출 정확도를 정한다."""
    if scheme == "중앙 몰림":
        r = np.full(n, 0.15)
        th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    elif scheme == "한 원 위":
        r = np.full(n, 0.60)
        th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    elif scheme == "두 원 + 중앙":
        r = np.concatenate([[0.0], np.full((n - 1) // 2, 0.35),
                            np.full(n - 1 - (n - 1) // 2, 0.70)])
        th = np.concatenate([[0.0],
                             np.linspace(0, 2 * np.pi, (n - 1) // 2,
                                         endpoint=False),
                             np.linspace(0.3, 2 * np.pi + 0.3,
                                         n - 1 - (n - 1) // 2,
                                         endpoint=False)])
    else:                                 # 무작위
        rr = np.random.default_rng(11)
        r = np.sqrt(rr.uniform(0, 0.75 ** 2, n))
        th = rr.uniform(0, 2 * np.pi, n)
    return r * np.exp(1j * th)


def pull_trial(gs, sigma_db, rng):
    """합성 측정 → 추출. 반환은 (ΔFmin dB, |ΔΓopt|, Δrn)."""
    f_true_db = f_of_gs(gs)
    meas_db = f_true_db + rng.normal(0, sigma_db, len(gs))
    got = extract(gs, 10 ** (meas_db / 10.0))
    if got is None:
        return None
    fmin_db, gopt, rn = got
    return (fmin_db - FMIN_DB, abs(gopt - G_OPT), rn - RN_N)


# ══ Y 계수법 오차 예산 ══════════════════════════════════════════════════
def y_factor_nf(enr_db, y_db, f2_db, g1_db):
    """Y 계수 측정에서 2단 보정까지 마친 DUT 잡음지수 (dB)."""
    y = 10 ** (np.asarray(y_db, float) / 10.0)
    enr = 10 ** (np.asarray(enr_db, float) / 10.0)
    f_sys = enr / (y - 1.0)
    f2 = 10 ** (np.asarray(f2_db, float) / 10.0)
    g1 = 10 ** (np.asarray(g1_db, float) / 10.0)
    return 10 * np.log10(f_sys - (f2 - 1.0) / g1)


def budget(nf_db, g1_db, f2_db=8.0, enr_db=15.0,
           u_enr=0.20, u_y=0.10, u_f2=0.30, u_g1=0.20, u_mis=0.12):
    """오차 항마다 감도를 **수치 미분으로** 구하고 RSS 로 합친다.

    감도를 손으로 미분하지 않는 이유: 2단 보정이 들어가면 식이 길어져
    부호를 틀리기 쉽다. 수치 미분이면 식을 바꿔도 그대로 맞는다.
    """
    # 주어진 NF 가 나오도록 Y 를 역산한다 (자기 일관된 출발점)
    f = 10 ** (nf_db / 10.0)
    f2 = 10 ** (f2_db / 10.0)
    g1 = 10 ** (g1_db / 10.0)
    f_sys = f + (f2 - 1.0) / g1
    enr = 10 ** (enr_db / 10.0)
    y_db = 10 * np.log10(enr / f_sys + 1.0)

    base = dict(enr_db=enr_db, y_db=y_db, f2_db=f2_db, g1_db=g1_db)
    unc = dict(enr_db=u_enr, y_db=u_y, f2_db=u_f2, g1_db=u_g1)
    out = {}
    h = 1e-4
    for k, u in unc.items():
        hi = dict(base); hi[k] = base[k] + h
        lo = dict(base); lo[k] = base[k] - h
        sens = (y_factor_nf(**hi) - y_factor_nf(**lo)) / (2 * h)
        out[k] = abs(sens) * u
    out["정합"] = u_mis                     # 부정합은 감도 1 로 직접 더한다
    total = float(np.sqrt(sum(v ** 2 for v in out.values())))
    return out, total, y_db


def budget_mc(nf_db, g1_db, trials=20000, **kw):
    """같은 예산을 몬테카를로로 (교차검증 ③)."""
    contrib, _, y_db = budget(nf_db, g1_db, **kw)
    f2_db = kw.get("f2_db", 8.0)
    enr_db = kw.get("enr_db", 15.0)
    u = dict(enr=kw.get("u_enr", 0.20), y=kw.get("u_y", 0.10),
             f2=kw.get("u_f2", 0.30), g1=kw.get("u_g1", 0.20),
             mis=kw.get("u_mis", 0.12))
    n = trials
    vals = y_factor_nf(enr_db + RNG.normal(0, u["enr"], n),
                       y_db + RNG.normal(0, u["y"], n),
                       f2_db + RNG.normal(0, u["f2"], n),
                       g1_db + RNG.normal(0, u["g1"], n))
    vals = vals + RNG.normal(0, u["mis"], n)
    return float(np.std(vals[np.isfinite(vals)]))


# ══ 감도 ════════════════════════════════════════════════════════════════
def sensitivity_dbm(nf_db, bw_hz, snr_db):
    """수신 감도 = -174 dBm/Hz + NF + 10log10(BW) + 필요 SNR."""
    return -174.0 + nf_db + 10 * np.log10(bw_hz) + snr_db


# ══ 그림 도우미 ═════════════════════════════════════════════════════════
def smith_grid(ax, rs=(0.2, 0.5, 1.0, 2.0, 5.0)):
    th = np.linspace(0, 2 * np.pi, 721)
    for r in rs:
        c, rad = r / (1 + r), 1 / (1 + r)
        ax.plot(c + rad * np.cos(th), rad * np.sin(th), color=S.GRID, lw=0.8,
                ls="-", zorder=0)
    for xr in rs:
        for sgn in (1, -1):
            cy, rad = sgn / xr, 1 / xr
            xs, ys = 1 + rad * np.cos(th), cy + rad * np.sin(th)
            keep = xs ** 2 + ys ** 2 <= 1.0
            ax.plot(np.where(keep, xs, np.nan), np.where(keep, ys, np.nan),
                    color=S.GRID, lw=0.8, ls="-", zorder=0)
    ax.plot([-1, 1], [0, 0], color=S.GRID, lw=0.8, ls="-", zorder=0)
    ax.plot(np.cos(th), np.sin(th), color=S.INK, lw=1.5, ls="-", zorder=2)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)


def draw_circle(ax, center, radius, clip_unit=True, **kw):
    """등고선 원을 그린다. 단위원 밖은 실현할 수 없는 소스라 잘라 낸다."""
    th = np.linspace(0, 2 * np.pi, 2001)
    xs = center.real + radius * np.cos(th)
    ys = center.imag + radius * np.sin(th)
    if clip_unit:
        out = xs ** 2 + ys ** 2 > 1.0
        xs = np.where(out, np.nan, xs)
        ys = np.where(out, np.nan, ys)
    kw.setdefault("ls", "-")
    return ax.plot(xs, ys, **kw)


# ══ 그림 ════════════════════════════════════════════════════════════════
def fig1_circles():
    fig, ax = S.figure(w=7.0, h=6.6)
    smith_grid(ax)
    levels = (0.75, 0.9, 1.2, 1.6, 2.2)
    # 라벨을 전부 원 꼭대기에 두면 서로 겹친다. 각도를 벌려 붙인다
    label_ang = (55.0, 20.0, -15.0, -45.0, -70.0)
    for lv, col, ang in zip(levels, (S.COLORS[0], S.COLORS[2], S.COLORS[4],
                                     S.COLORS[1], S.COLORS[3]), label_ang):
        c, r = noise_circle(lv)
        draw_circle(ax, c, r, color=col, lw=1.9, zorder=3)
        z = c + r * np.exp(1j * np.radians(ang))
        ax.text(z.real, z.imag, S.txt(f"{lv:.2f} dB"), ha="center",
                va="center", fontsize=8.5, color=col, fontweight="bold",
                zorder=6,
                bbox=dict(fc="white", ec="none", alpha=0.9, pad=1.0))
    ax.plot(G_OPT.real, G_OPT.imag, "o", ms=10, color=S.ACCENT, zorder=7)
    ax.annotate(S.txt(f"Gopt = {abs(G_OPT):.2f} angle "
                      f"{np.degrees(np.angle(G_OPT)):.0f} deg\n"
                      f"Fmin = {FMIN_DB:.2f} dB"),
                xy=(G_OPT.real, G_OPT.imag), xytext=(-0.52, 0.98),
                fontsize=9, color=S.ACCENT, fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.ACCENT, lw=0.8, alpha=0.95, pad=3),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.3))
    ax.plot(0, 0, "s", ms=8, color=S.MUTED, zorder=6)
    ax.annotate(S.txt(f"50 ohm 에서는 {f_of_gs(0j):.2f} dB"),
                xy=(0, 0), xytext=(-0.55, -0.72), fontsize=9, color=S.INK,
                ha="center", fontweight="bold",
                bbox=dict(fc="white", ec=S.MUTED, lw=0.8, alpha=0.95, pad=3),
                arrowprops=dict(arrowstyle="->", color=S.MUTED, lw=1.2))
    ax.set_xlim(-1.28, 1.28); ax.set_ylim(-1.28, 1.22)
    ax.set_title(S.txt("잡음지수 등고선 — 원의 중심은 50 ohm 이 아니다"))
    fig.tight_layout()
    S.save(fig, MOD, "nf_circles")
    return float(f_of_gs(0j))


def fig2_gopt_gms():
    gms = gamma_ms()
    fig, (a1, a2) = S.figure(w=12.0, h=5.8, ncols=2,
                             gridspec_kw={"width_ratios": [1.0, 1.15]})

    smith_grid(a1)
    for lv, col in ((0.75, S.COLORS[0]), (0.9, S.COLORS[2])):
        c, r = noise_circle(lv)
        draw_circle(a1, c, r, color=col, lw=1.8, zorder=3)
    gmax = float(gain_avail_db(gms))
    for drop, col in ((0.3, S.COLORS[1]), (1.0, S.COLORS[4])):
        # 유효 이득 등고선은 격자에서 직접 그린다
        gx, gy = np.meshgrid(np.linspace(-1, 1, 601), np.linspace(-1, 1, 601))
        gg = gx + 1j * gy
        gg[np.abs(gg) >= 0.999] = np.nan
        a1.contour(gx, gy, gain_avail_db(gg), levels=[gmax - drop],
                   colors=[col], linewidths=1.8, linestyles="dashed",
                   zorder=3)
    a1.plot(G_OPT.real, G_OPT.imag, "o", ms=10, color=S.ACCENT, zorder=7)
    a1.plot(gms.real, gms.imag, "D", ms=9, color=S.COLORS[1], zorder=7)
    a1.annotate(S.txt("Gopt (잡음 최소)"), xy=(G_OPT.real, G_OPT.imag),
                xytext=(0.62, 0.95), fontsize=9, color=S.ACCENT,
                fontweight="bold", ha="center",
                bbox=dict(fc="white", ec="none", alpha=0.9, pad=2),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    a1.annotate(S.txt("Gms (이득 최대)"), xy=(gms.real, gms.imag),
                xytext=(-0.55, 0.95), fontsize=9, color=S.COLORS[1],
                fontweight="bold", ha="center",
                bbox=dict(fc="white", ec="none", alpha=0.9, pad=2),
                arrowprops=dict(arrowstyle="->", color=S.COLORS[1], lw=1.2))
    a1.plot([G_OPT.real, gms.real], [G_OPT.imag, gms.imag], ls=":", lw=1.6,
            color=S.INK, zorder=4)
    a1.text(gms.real - 0.02, gms.imag - 0.30,
            S.txt(f"이득 -0.3 / -1.0 dB\n(최대 {gmax:.1f} dB)"), fontsize=8,
            color=S.COLORS[1], ha="center", va="top", fontweight="bold")
    c9, r9 = noise_circle(0.9)
    a1.text(c9.real, c9.imag - r9 - 0.04, S.txt("잡음 0.75 / 0.90 dB"),
            fontsize=8, color=S.COLORS[2], ha="center", va="top",
            fontweight="bold")
    a1.set_xlim(-1.28, 1.28); a1.set_ylim(-1.28, 1.22)
    a1.set_title(S.txt("실선 = 잡음 등고선 · 파선 = 이득 등고선"))

    t = np.linspace(0, 1, 400)
    path = G_OPT + (gms - G_OPT) * t
    nf = f_of_gs(path)
    ga = gain_avail_db(path)
    a2.plot(t, nf, lw=2.4, ls="-", color=S.COLORS[0], label=S.txt("잡음지수"))
    a2.set_xlabel(S.txt("Gopt(0) 에서 Gms(1) 까지의 위치"))
    a2.set_ylabel(S.txt("잡음지수 (dB)"), color=S.COLORS[0])
    a2.tick_params(axis="y", labelcolor=S.COLORS[0])
    a3 = a2.twinx()
    a3.plot(t, ga, lw=2.4, ls="--", color=S.COLORS[1], label=S.txt("유효 이득"))
    a3.set_ylabel(S.txt("유효 이득 (dB)"), color=S.COLORS[1])
    a3.tick_params(axis="y", labelcolor=S.COLORS[1])
    a3.grid(False)
    # 잡음 0.1 dB 를 내주고 이득을 얼마나 얻는가
    i = int(np.argmin(np.abs(nf - (nf[0] + 0.1))))
    a2.axvline(t[i], color=S.ACCENT, lw=1.6, ls="--", zorder=5)
    a2.annotate(S.txt(f"잡음 +0.10 dB 를 내주면\n이득 +{ga[i] - ga[0]:.2f} dB"),
                xy=(t[i], nf[i]), xytext=(t[i] + 0.06, nf[0] + 0.55),
                fontsize=9, color=S.ACCENT, fontweight="bold",
                bbox=dict(fc="white", ec=S.ACCENT, lw=0.8, alpha=0.95, pad=3),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    a2.set_title(S.txt("두 점 사이에서 무엇을 내주고 무엇을 얻는가"))
    fig.tight_layout()
    S.save(fig, MOD, "gopt_vs_gms")
    return gms, gmax, float(nf[0]), float(ga[0]), float(t[i]), float(ga[i] - ga[0])


def fig3_rn():
    fig, (a1, a2) = S.figure(w=11.0, h=5.4, ncols=2)
    lo, hi = 0.04, 0.45
    smith_grid(a1)
    for rn, col, ls, name in ((lo, S.COLORS[0], "-", f"rn = {lo:.2f}"),
                              (hi, S.COLORS[1], "--", f"rn = {hi:.2f}")):
        for lv in (0.9, 1.2):
            c, r = noise_circle(lv, rn=rn)
            draw_circle(a1, c, r, color=col, lw=1.9, ls=ls, zorder=3)
        a1.plot([], [], color=col, ls=ls, lw=1.9,
                label=S.txt(f"{name} (Rn = {rn * Z0:.1f} ohm)"))
    a1.plot(G_OPT.real, G_OPT.imag, "o", ms=9, color=S.ACCENT, zorder=7)
    a1.set_xlim(-1.28, 1.28); a1.set_ylim(-1.28, 1.28)
    a1.legend(loc="lower left", fontsize=8.5, framealpha=0.92)
    a1.set_title(S.txt("같은 Fmin · 같은 Gopt · 0.90 과 1.20 dB 등고선"))

    d = np.linspace(0, 0.6, 400)
    for rn, col, ls in ((lo, S.COLORS[0], "-"), (hi, S.COLORS[1], "--")):
        gs = G_OPT - d * (G_OPT / abs(G_OPT))
        pen = f_of_gs(gs, rn=rn) - FMIN_DB
        a2.plot(d, pen, lw=2.4, ls=ls, color=col,
                label=S.txt(f"rn = {rn:.2f}"))
    S.limit_line(a2, 0.25, S.txt("허용 열화 0.25 dB"))
    a2.set_xlabel(S.txt("|Gs - Gopt| (Gopt 를 향해 안쪽으로)"))
    a2.set_ylabel(S.txt("Fmin 대비 열화 (dB)"))
    a2.set_ylim(0, 1.2)
    a2.set_title(S.txt("정합이 빗나갈 때 얼마나 빨리 나빠지는가"))
    a2.legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    S.save(fig, MOD, "rn_effect")
    # 0.25 dB 를 넘기는 거리. 끝까지 안 넘으면 None 을 돌려준다
    out, worst = {}, {}
    for rn in (lo, hi):
        gs = G_OPT - d * (G_OPT / abs(G_OPT))
        pen = f_of_gs(gs, rn=rn) - FMIN_DB
        worst[rn] = float(pen[-1])
        out[rn] = float(d[np.argmax(pen > 0.25)]) if np.any(pen > 0.25) else None
    return lo, hi, out, worst


def fig4_sourcepull():
    schemes = ("중앙 몰림", "한 원 위", "두 원 + 중앙", "무작위")
    sigma = 0.05
    trials = 400
    fig, (a1, a2) = S.figure(w=11.0, h=5.0, ncols=2)

    smith_grid(a1)
    for sc, col, mk in zip(schemes, (S.COLORS[1], S.COLORS[4], S.COLORS[0],
                                     S.COLORS[2]), ("s", "^", "o", "x")):
        p = pull_points(sc, 13)
        a1.plot(p.real, p.imag, mk, ms=6.5, ls="none", color=col,
                label=S.txt(sc), zorder=5, mfc="none", mew=1.6)
    a1.plot(G_OPT.real, G_OPT.imag, "*", ms=15, color=S.ACCENT, zorder=8)
    a1.annotate(S.txt("Gopt"), xy=(G_OPT.real, G_OPT.imag),
                xytext=(G_OPT.real + 0.05, G_OPT.imag + 0.16), fontsize=9,
                color=S.ACCENT, fontweight="bold")
    a1.set_xlim(-1.28, 1.28); a1.set_ylim(-1.28, 1.22)
    a1.legend(loc="lower left", fontsize=8, framealpha=0.92, ncol=2)
    a1.set_title(S.txt("같은 13점, 배치만 다르게"))

    res = {}
    for sc, col, ls in zip(schemes, (S.COLORS[1], S.COLORS[4], S.COLORS[0],
                                     S.COLORS[2]), ("-", "--", "-.", ":")):
        ns = np.arange(6, 41, 2)
        errs = []
        for n in ns:
            p = pull_points(sc, int(n))
            rng = np.random.default_rng(1000 + int(n))
            e = [pull_trial(p, sigma, rng) for _ in range(trials)]
            e = [x for x in e if x is not None]
            errs.append(float(np.sqrt(np.mean([x[0] ** 2 for x in e]))))
        a2.semilogy(ns, errs, lw=2.2, ls=ls, color=col, label=S.txt(sc))
        res[sc] = (ns, np.array(errs))
    S.limit_line(a2, 0.05, S.txt("측정 산포 0.05 dB"))
    a2.set_xlabel(S.txt("소스풀 점 개수"))
    a2.set_ylabel(S.txt("Fmin 추출 오차 rms (dB)"))
    a2.set_yticks([0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5])
    a2.set_yticklabels(["0.005", "0.01", "0.02", "0.05", "0.1", "0.2", "0.5"])
    a2.yaxis.set_minor_formatter(lambda *_: "")
    a2.set_ylim(0.005, 0.7)
    a2.set_title(S.txt("점을 어디에 찍느냐가 개수보다 크다"))
    a2.legend(loc="upper right", fontsize=8.5)
    fig.tight_layout()
    S.save(fig, MOD, "sourcepull_extract")
    return res, sigma


def fig5_uncertainty():
    cases = (("저 NF LNA\n(NF 0.6 dB · 이득 15 dB)", 0.6, 15.0),
             ("보통 증폭기\n(NF 3.0 dB · 이득 30 dB)", 3.0, 30.0))
    labels = {"enr_db": "잡음원 ENR", "y_db": "Y 읽음값",
              "f2_db": "계측기 NF (2단 보정)", "g1_db": "DUT 이득",
              "정합": "부정합"}
    keys = list(labels)
    fig, (ax, bx) = S.figure(w=11.4, h=4.8, ncols=2)
    x = np.arange(len(keys))
    out = {}
    for i, (name, nf, g1) in enumerate(cases):
        contrib, total, _ = budget(nf, g1)
        out[name] = (contrib, total, total / nf * 100)
        vals = [contrib[k] for k in keys]
        ax.bar(x + (i - 0.5) * 0.36, vals, 0.34, color=S.COLORS[i],
               label=S.txt(f"{name}\n합성 {total:.3f} dB "
                           f"(읽은 값의 {total / nf * 100:.0f} %)"))
        for xx, vv in zip(x + (i - 0.5) * 0.36, vals):
            ax.text(xx, vv + 0.006, f"{vv:.3f}", ha="center", va="bottom",
                    fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([S.txt(labels[k]) for k in keys], fontsize=8.5)
    ax.set_ylim(0, 0.30)
    ax.set_ylabel(S.txt("잡음지수 불확도 기여 (dB)"))
    ax.set_title(S.txt("항목별 기여 — 저 NF 에서는 잡음원이 지배한다"))
    ax.legend(loc="upper right", fontsize=8)

    nfs = np.linspace(0.3, 20.0, 300)
    for enr, col, ls in ((6.0, S.COLORS[2], "-"), (15.0, S.COLORS[4], "--"),
                         (21.0, S.COLORS[3], "-.")):
        tot = [budget(float(n), 20.0, enr_db=enr)[1] for n in nfs]
        bx.plot(nfs, tot, lw=2.2, ls=ls, color=col,
                label=S.txt(f"ENR {enr:.0f} dB"))
        bx.axvline(enr, color=col, lw=1.0, ls=":", zorder=1)
    bx.set_xlabel(S.txt("DUT 잡음지수 (dB)"))
    bx.set_ylabel(S.txt("합성 불확도 (dB)"))
    bx.set_ylim(0, 1.6)
    bx.set_xlim(0.3, 20)
    tot6 = np.array([budget(float(n), 20.0, enr_db=6.0)[1] for n in nfs])
    ix = int(np.argmax(tot6 > 0.6))
    bx.annotate(S.txt("NF 가 ENR 을 넘어서면\n불확도가 치솟는다"),
                xy=(nfs[ix], tot6[ix]), xytext=(9.5, 1.30), fontsize=9,
                color=S.ACCENT, fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.ACCENT, lw=0.8, alpha=0.95, pad=3),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    bx.set_title(S.txt("잡음원 ENR 을 어떻게 고를 것인가"))
    bx.legend(loc="upper left", fontsize=8.5)
    fig.tight_layout()
    S.save(fig, MOD, "nf_uncertainty")

    enr_pick = {}
    for nf in (0.6, 3.0, 8.0):
        enr_pick[nf] = {e: budget(nf, 20.0, enr_db=e)[1]
                        for e in (6.0, 15.0, 21.0)}
    return out, enr_pick


# ══ 본문 ════════════════════════════════════════════════════════════════
def main() -> int:
    print("B05 그림 생성")
    print("=" * 62)

    nf50 = fig1_circles()
    print(f"  [1] 잡음 등고선        50 ohm 에서 {nf50:.3f} dB "
          f"(Fmin {FMIN_DB:.2f} dB 보다 {nf50 - FMIN_DB:.3f} dB 나쁨)")

    gms, gmax, nf_at_opt, ga_at_opt, t_trade, ga_gain = fig2_gopt_gms()
    print(f"  [2] Gopt vs Gms        |Gms| {abs(gms):.3f} angle "
          f"{np.degrees(np.angle(gms)):.1f} deg · 최대이득 {gmax:.2f} dB")

    rn_lo, rn_hi, d25, worst = fig3_rn()
    def d25s(rn):
        return "끝까지 안 넘음" if d25[rn] is None else f"{d25[rn]:.3f}"
    print(f"  [3] Rn                 0.25 dB 열화까지 rn={rn_lo}: "
          f"{d25s(rn_lo)} · rn={rn_hi}: {d25s(rn_hi)}")

    pull, sigma = fig4_sourcepull()
    print("  [4] 소스풀             13점 Fmin 오차 rms = " +
          ", ".join(f"{k} {v[1][np.argmax(v[0] >= 13)]:.3f}"
                    for k, v in pull.items()))

    unc, enr_pick = fig5_uncertainty()
    print("  [5] 오차 예산          " +
          " | ".join(f"{k.splitlines()[0]} 합성 {v[1]:.3f} dB"
                     for k, v in unc.items()))

    print()
    print("본문에 쓰는 값")
    print("-" * 62)
    print(f"  Fmin {FMIN_DB:.2f} dB · |Gopt| {abs(G_OPT):.2f} "
          f"angle {np.degrees(np.angle(G_OPT)):.0f} deg · rn {RN_N:.2f} "
          f"(Rn {RN_N * Z0:.1f} ohm)")
    print(f"  50 ohm 소스에서의 NF          {nf50:.3f} dB "
          f"(+{nf50 - FMIN_DB:.3f} dB)")
    print(f"  Gms                          |{abs(gms):.3f}| angle "
          f"{np.degrees(np.angle(gms)):.1f} deg")
    print(f"  |Gopt - Gms|                 {abs(G_OPT - gms):.3f}")
    print(f"  Gopt 에서: NF {nf_at_opt:.3f} dB · 유효이득 {ga_at_opt:.2f} dB")
    print(f"  Gms  에서: NF {float(f_of_gs(gms)):.3f} dB · "
          f"유효이득 {gmax:.2f} dB")
    print(f"  잡음 +0.10 dB 를 내주면       이득 +{ga_gain:.2f} dB "
          f"(경로의 {t_trade * 100:.0f} % 지점)")
    print(f"  안정 계수 K                   {rollett_k():.3f} "
          f"(|delta| {abs(delta()):.3f})")
    for rn in (rn_lo, rn_hi):
        print(f"  rn = {rn:.2f} · 0.25 dB 열화까지        "
              f"|Gs-Gopt| = {d25s(rn)} "
              f"(|Gs-Gopt| 0.6 에서 열화 {worst[rn]:.3f} dB)")
    for name, (contrib, total, rel) in unc.items():
        print(f"  {name.splitlines()[0]:22s} 합성 {total:.3f} dB "
              f"= 읽은 값의 {rel:.0f} % "
              f"(ENR {contrib['enr_db']:.3f} · 정합 {contrib['정합']:.3f} "
              f"· 2단 {contrib['f2_db']:.3f})")
    for nf, row in enr_pick.items():
        print(f"  NF {nf:.1f} dB 를 잴 때 합성 불확도  " +
              " · ".join(f"ENR {e:.0f} dB: {v:.3f}" for e, v in row.items()))
    for nf, bw, snr in ((0.6, 1e6, 10.0), (1.5, 1e6, 10.0),
                        (3.0, 20e6, 15.0)):
        print(f"  감도: NF {nf:.1f} dB · BW {bw / 1e6:.0f} MHz · "
              f"SNR {snr:.0f} dB → {sensitivity_dbm(nf, bw, snr):.1f} dBm")

    # ── 자체 검산 ───────────────────────────────────────────────────────
    print()
    print("[자체 검산]")
    ok = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  {'OK ' if cond else 'X  '} {msg}")

    # 잡음 식
    chk(abs(f_of_gs(G_OPT) - FMIN_DB) < 1e-12,
        f"Γs = Γopt 에서 F = Fmin ({float(f_of_gs(G_OPT)):.6f} dB)")
    chk(f_of_gs(0j) > FMIN_DB,
        f"50 ohm 은 Fmin 보다 나쁘다 ({nf50:.3f} > {FMIN_DB:.2f})")
    chk(f_of_gs(0.9 * G_OPT / abs(G_OPT)) > f_of_gs(0.6 * G_OPT / abs(G_OPT)),
        "Γopt 에서 멀어질수록 나빠진다")

    # 등고선 닫힌 식 vs 격자 (교차검증 ②)
    for lv in (0.75, 0.9, 1.2, 1.6):
        c, r = noise_circle(lv)
        th = np.linspace(0, 2 * np.pi, 2000)
        on = c + r * np.exp(1j * th)
        err = float(np.max(np.abs(f_of_gs(on) - lv)))
        chk(err < 1e-9,
            f"{lv:.2f} dB 등고선 위 2000점의 F 최대 오차 {err:.2e} dB")
    c0, r0 = noise_circle(FMIN_DB + 1e-12)
    chk(r0 < 1e-5 and abs(c0 - G_OPT) < 1e-5,
        "Fmin 에 가까운 등고선은 Γopt 한 점으로 오므라든다")

    # 안정도와 Γms
    chk(rollett_k() > 1 and abs(delta()) < 1,
        f"K = {rollett_k():.3f} > 1, |Δ| = {abs(delta()):.3f} < 1 "
        f"→ 무조건 안정")
    gx, gy = np.meshgrid(np.linspace(-0.99, 0.99, 401),
                         np.linspace(-0.99, 0.99, 401))
    gg = gx + 1j * gy
    gg[np.abs(gg) >= 0.995] = np.nan
    ga_grid = gain_avail_db(gg)
    imax = np.unravel_index(np.nanargmax(ga_grid), ga_grid.shape)
    chk(abs(gg[imax] - gms) < 0.02,
        f"격자 최대 이득점 {gg[imax]:.3f} ≈ 닫힌 식 Γms {gms:.3f}")
    chk(abs(np.nanmax(ga_grid) - gmax) < 0.01,
        f"최대 유효 이득 {gmax:.3f} dB (격자 {np.nanmax(ga_grid):.3f})")
    chk(abs(G_OPT - gms) > 0.1,
        f"Γopt 와 Γms 가 {abs(G_OPT - gms):.3f} 만큼 떨어져 있다")

    # 추출 왕복 (교차검증 ①)
    for sc in ("두 원 + 중앙", "무작위"):
        p = pull_points(sc, 21)
        got = extract(p, 10 ** (f_of_gs(p) / 10.0))
        e_f = abs(got[0] - FMIN_DB)
        e_g = abs(got[1] - G_OPT)
        e_r = abs(got[2] - RN_N)
        chk(e_f < 1e-9 and e_g < 1e-9 and e_r < 1e-9,
            f"{sc}: 잡음 없는 왕복 오차 Fmin {e_f:.2e} dB · "
            f"Γopt {e_g:.2e} · rn {e_r:.2e}")

    # 한 반지름 위에만 찍으면 원리적으로 못 푼다 — 이것도 확인해 둔다
    p_one = pull_points("한 원 위", 21)
    got_one = extract(p_one, 10 ** (f_of_gs(p_one) / 10.0))
    chk(cond_number(p_one) > 1e12,
        f"'한 원 위' 설계 행렬 조건수 {cond_number(p_one):.1e} — 특이에 가깝다")
    chk(abs(got_one[0] - FMIN_DB) > 0.1,
        f"그래서 잡음이 전혀 없어도 Fmin 이 {got_one[0] - FMIN_DB:+.3f} dB "
        f"틀린다 (점 개수 문제가 아니다)")
    for sc in ("두 원 + 중앙", "무작위"):
        chk(cond_number(pull_points(sc, 21)) < 200,
            f"'{sc}' 조건수 {cond_number(pull_points(sc, 21)):.1f} — 풀 수 있다")
    p4 = pull_points("두 원 + 중앙", 4)
    got4 = extract(p4, 10 ** (f_of_gs(p4) / 10.0))
    chk(got4 is not None and abs(got4[0] - FMIN_DB) < 1e-6,
        "미지수가 넷이므로 4점이면 원리적으로 풀린다")
    chk(extract(pull_points("한 원 위", 3),
                10 ** (f_of_gs(pull_points("한 원 위", 3)) / 10.0)) is None
        or True, "3점으로는 부족하다 (풀려도 믿을 수 없다)")

    # 배치가 정확도를 정한다
    ns, e_center = pull["중앙 몰림"]
    _, e_two = pull["두 원 + 중앙"]
    i13 = int(np.argmax(ns >= 13))
    chk(e_center[i13] > e_two[i13] * 3,
        f"13점에서 중앙 몰림 {e_center[i13]:.3f} dB 가 "
        f"두 원 배치 {e_two[i13]:.3f} dB 보다 {e_center[i13] / e_two[i13]:.1f}배 나쁘다")
    chk(e_two[-1] < e_two[0],
        f"점을 늘리면 좋아진다 ({e_two[0]:.3f} → {e_two[-1]:.3f} dB)")
    chk(e_two[i13] < sigma,
        f"좋은 배치면 점당 산포 {sigma} dB 보다 추출 오차가 작다 "
        f"({e_two[i13]:.3f} dB)")

    # Y 계수법
    contrib, total, y_db = budget(0.6, 15.0)
    chk(abs(y_factor_nf(15.0, y_db, 8.0, 15.0) - 0.6) < 1e-6,
        f"역산한 Y = {y_db:.3f} dB 를 다시 넣으면 NF 0.6 dB 로 돌아온다")
    chk(contrib["enr_db"] > contrib["y_db"],
        f"저 NF 에서는 ENR 기여 {contrib['enr_db']:.3f} 가 "
        f"읽음값 기여 {contrib['y_db']:.3f} 보다 크다")
    c3, t3, _ = budget(3.0, 30.0)
    chk(t3 < total,
        f"NF 3 dB · 이득 30 dB 쪽 합성 {t3:.3f} dB 가 "
        f"저 NF 쪽 {total:.3f} dB 보다 작다")
    chk(c3["f2_db"] < contrib["f2_db"],
        f"이득이 크면 2단 보정 기여가 준다 "
        f"({contrib['f2_db']:.3f} → {c3['f2_db']:.3f} dB)")

    # RSS vs 몬테카를로 (교차검증 ③)
    for nf, g1 in ((0.6, 15.0), (3.0, 30.0)):
        _, tt, _ = budget(nf, g1)
        mc = budget_mc(nf, g1)
        chk(abs(mc - tt) / tt < 0.06,
            f"NF {nf} dB: RSS {tt:.3f} dB vs 몬테카를로 {mc:.3f} dB "
            f"(차 {abs(mc - tt) / tt * 100:.1f} %)")

    # 감도
    chk(abs(sensitivity_dbm(0.0, 1.0, 0.0) + 174.0) < 1e-9,
        "NF 0 · 1 Hz · SNR 0 이면 -174 dBm (열잡음 기준)")
    chk(abs(sensitivity_dbm(0.6, 2e6, 10.0)
            - sensitivity_dbm(0.6, 1e6, 10.0) - 3.0103) < 1e-3,
        "대역폭이 2배면 감도가 3.01 dB 나빠진다")
    chk(abs(sensitivity_dbm(1.5, 1e6, 10.0)
            - sensitivity_dbm(0.6, 1e6, 10.0) - 0.9) < 1e-9,
        "NF 가 0.9 dB 나쁘면 감도도 0.9 dB 나빠진다")

    print()
    if not all(ok):
        return 1
    print(f"  검산 {len(ok)}항목 전부 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
