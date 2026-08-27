#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B07 (EMC 벤치 디버그 — 방사원을 찾아내는 법) 그림 생성기.

만드는 그림
  B07-1  클럭 하모닉과 규격 한도 — 무엇이 문제가 될지 미리 안다
  B07-2  근접장 프로브 — 고리 지름과 분해능의 절충
  B07-3  근접장 스캔 지도 — 어디서 나오는가
  B07-4  공통모드 전류가 만드는 방사
  B07-5  대책별 개선량 — 페라이트와 차폐는 주파수를 탄다

교차검증 네 갈래
  ① 사다리꼴 클럭의 FFT vs 포락선 닫힌 식 (0 → -20 → -40 dB/dec)
  ② 고리 프로브의 자속을 수치 적분한 값 vs 무한 직선 도체의 닫힌 식
     Φ = μ0·I·L/(2π)·ln(r2/r1)
  ③ 공통모드 방사 닫힌 식 vs 미소 다이폴 원거리장 식 (접지면 반사 2배 포함),
     그리고 계측사 자료의 사례(30 MHz · 1 m · 3 m · 8 uA → 100 uV/m) 재현
  ④ 페라이트 삽입손실의 회로 계산 vs 임피던스 비 근사

실행: python3 scripts/gen_fig_b07.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rf_style as S  # noqa: E402

MOD = "B07"

MU0 = 4e-7 * np.pi
C0 = 299_792_458.0
ETA0 = 376.730313668

# ── 클럭 ────────────────────────────────────────────────────────────────
F_CLK = 25e6            # 기준 클럭
V_SWING = 3.3
DUTY = 0.5
T_RISE = 1.5e-9         # 10~90 % 상승시간

# ── 방사 규격 (3 m 거리, 준첨두) ────────────────────────────────────────
# FCC/CISPR class B 계열의 대표값. 정확한 값은 규격 원문 확인
LIMIT_3M = ((30e6, 88e6, 40.0), (88e6, 216e6, 43.5), (216e6, 960e6, 46.0),
            (960e6, 6e9, 54.0))

# ── 근접장 프로브 ───────────────────────────────────────────────────────
PROBE_D_MM = (2.0, 6.0, 20.0)
SCAN_H_MM = 2.0


# ══ 클럭 스펙트럼 ═══════════════════════════════════════════════════════
def trapezoid(t, f=F_CLK, duty=DUTY, tr=T_RISE, amp=V_SWING):
    """사다리꼴 클럭 파형. 상승·하강 시간이 같다고 본다."""
    period = 1.0 / f
    ph = np.mod(np.asarray(t, float), period)
    hi = duty * period
    y = np.zeros_like(ph)
    y = np.where(ph < tr, ph / tr, y)
    y = np.where((ph >= tr) & (ph < hi), 1.0, y)
    y = np.where((ph >= hi) & (ph < hi + tr), 1.0 - (ph - hi) / tr, y)
    return amp * y


def harmonic_envelope_dbuv(n, f=F_CLK, duty=DUTY, tr=T_RISE, amp=V_SWING):
    """사다리꼴의 n 차 하모닉 진폭 (dBuV). 닫힌 식.

    |c_n| = 2·A·d·|sinc(n·d)|·|sinc(n·tr/T)|
    (여기서 sinc(x) = sin(pi x)/(pi x))
    """
    n = np.asarray(n, float)
    def sinc(x):
        return np.sinc(x)                       # numpy 의 sinc 는 sin(pi x)/(pi x)
    cn = 2 * amp * duty * np.abs(sinc(n * duty)) * np.abs(sinc(n * tr * f))
    return 20 * np.log10(np.maximum(cn, 1e-15) * 1e6)


def harmonic_fft_dbuv(nmax, f=F_CLK, duty=DUTY, tr=T_RISE, amp=V_SWING):
    """같은 것을 실제 파형의 FFT 로 (교차검증 ①)."""
    n_cyc, per_cyc = 64, 1 << 14
    n = n_cyc * per_cyc
    t = np.arange(n) / (per_cyc * f)
    y = trapezoid(t, f, duty, tr, amp)
    sp = np.fft.rfft(y) / n
    out = []
    for k in range(1, nmax + 1):
        out.append(20 * np.log10(2 * np.abs(sp[k * n_cyc]) * 1e6))
    return np.array(out)


def limit_dbuv(f_hz):
    f = np.asarray(f_hz, float)
    out = np.full(f.shape, np.nan)
    for lo, hi, lv in LIMIT_3M:
        out = np.where((f >= lo) & (f < hi), lv, out)
    return out


# ══ 근접장 프로브 ═══════════════════════════════════════════════════════
def flux_wire_closed(i_a, length_m, r1, r2):
    """무한 직선 도체 옆 사각 고리를 지나는 자속 (닫힌 식).

    Φ = μ0·I·L/(2π)·ln(r2/r1)
    """
    return MU0 * i_a * length_m / (2 * np.pi) * np.log(r2 / r1)


def flux_wire_numeric(i_a, length_m, r1, r2, n=200_001):
    """같은 것을 수치 적분으로 (교차검증 ②). B = μ0 I/(2πr) 를 면적에 적분."""
    r = np.linspace(r1, r2, n)
    b = MU0 * i_a / (2 * np.pi * r)
    return float(np.trapezoid(b, r)) * length_m


def probe_response(x_mm, wire_x_mm, d_mm, h_mm=SCAN_H_MM, i_a=1e-3):
    """지름 d 의 원형 고리를 보드 위 h 높이에서 x 로 훑을 때의 유도 자속.

    고리 면을 도체와 나란한 수직면에 둔다(자기장이 고리를 통과하는 방향).
    원 안을 격자로 나눠 B 의 수직 성분을 적분한다.
    """
    x = np.asarray(x_mm, float)
    d = d_mm * 1e-3
    a = d / 2
    ny = 41
    yy = np.linspace(-a * 0.995, a * 0.995, ny)          # 고리 중심 기준 높이
    out = np.empty(x.shape)
    for k, xc in enumerate(x):
        tot = 0.0
        for y in yy:
            half = np.sqrt(a ** 2 - y ** 2)               # 그 높이에서의 폭 절반
            xs = np.linspace(xc - half, xc + half, 41) * 1e-3
            zc = (h_mm + d_mm / 2) * 1e-3 + y             # 보드에서의 높이
            dx = xs - wire_x_mm * 1e-3
            r2 = dx ** 2 + zc ** 2
            # 도체가 y 방향으로 흐를 때 B 의 x 성분 (고리 법선 방향)
            bx = MU0 * i_a / (2 * np.pi) * (-zc) / r2
            tot += np.trapezoid(bx, xs) * (yy[1] - yy[0])
        out[k] = tot
    return out


def two_trace_contrast(d_mm, sep_mm, h_mm=SCAN_H_MM):
    """두 도체를 sep 만큼 떼어 놓았을 때 프로브가 둘로 보는가.

    반환은 (골 깊이 dB, 스캔 x, 응답). 골이 얕으면 하나로 뭉쳐 보인다.
    """
    x = np.linspace(-sep_mm * 1.6, sep_mm * 1.6, 241)
    r = (np.abs(probe_response(x, -sep_mm / 2, d_mm, h_mm))
         + np.abs(probe_response(x, +sep_mm / 2, d_mm, h_mm)))
    mid = r[len(r) // 2]
    pk = np.max(r)
    return 20 * np.log10(pk / mid), x, r


# ══ 근접장 스캔 지도 ════════════════════════════════════════════════════
BOARD_SOURCES = (
    # (x0, y0, x1, y1, 전류 mA)  — 보드 위 도체 조각 (mm)
    (10.0, 8.0, 10.0, 42.0, 12.0),     # 클럭 배선 (세로)
    (10.0, 42.0, 46.0, 42.0, 12.0),    # 이어지는 가로 구간
    (30.0, 10.0, 30.0, 26.0, 2.0),     # 조용한 신호선
    (56.0, 6.0, 56.0, 46.0, 5.0),      # 전원 배선
    (20.0, 22.0, 26.0, 22.0, 25.0),    # 귀환 경로가 끊긴 짧은 구간
)


def h_field_map(nx=170, ny=130, h_mm=3.0):
    """보드 위 h 높이에서의 |H| 지도. 유한 길이 도체의 비오-사바르 합."""
    xs = np.linspace(0, 66, nx)
    ys = np.linspace(0, 52, ny)
    gx, gy = np.meshgrid(xs, ys)
    hx = np.zeros_like(gx)
    hy = np.zeros_like(gx)
    hz = np.zeros_like(gx)
    z = h_mm * 1e-3
    for x0, y0, x1, y1, i_ma in BOARD_SOURCES:
        p0 = np.array([x0, y0, 0.0]) * 1e-3
        p1 = np.array([x1, y1, 0.0]) * 1e-3
        seg = p1 - p0
        n_seg = 240
        ts = (np.arange(n_seg) + 0.5) / n_seg
        pts = p0[None, :] + seg[None, :] * ts[:, None]
        dl = seg / n_seg
        for p in pts:
            rx = gx * 1e-3 - p[0]
            ry = gy * 1e-3 - p[1]
            rz = z
            r3 = (rx ** 2 + ry ** 2 + rz ** 2) ** 1.5
            r3 = np.maximum(r3, 1e-12)
            cx = dl[1] * rz - dl[2] * ry
            cy = dl[2] * rx - dl[0] * rz
            cz = dl[0] * ry - dl[1] * rx
            k = (i_ma * 1e-3) / (4 * np.pi * r3)
            hx += k * cx
            hy += k * cy
            hz += k * cz
    return xs, ys, np.sqrt(hx ** 2 + hy ** 2 + hz ** 2)


# ══ 공통모드 전류와 방사 ════════════════════════════════════════════════
def e_from_cm_current(i_a, f_hz, length_m, dist_m=3.0):
    """공통모드 전류가 만드는 원거리 전계 (V/m).

    E = 1.257e-6 · f · I · L / d
    미소 다이폴 식의 **2배**인데, 그 2배가 시험장 접지면 반사다.
    """
    return 1.257e-6 * np.asarray(f_hz, float) * np.asarray(i_a, float) \
        * length_m / dist_m


def e_dipole_freespace(i_a, f_hz, length_m, dist_m=3.0):
    """같은 것을 미소 다이폴 원거리장 식으로 (자유공간, 반사 없음).

    |E| = η0·k·I·L / (4π·r),  k = 2πf/c
    """
    k = 2 * np.pi * np.asarray(f_hz, float) / C0
    return ETA0 * k * np.asarray(i_a, float) * length_m / (4 * np.pi * dist_m)


def dbuv_m(e_v_m):
    return 20 * np.log10(np.asarray(e_v_m, float) * 1e6)


def cm_current_limit_a(f_hz, length_m=1.0, dist_m=3.0):
    """규격 한도를 넘지 않으려면 공통모드 전류가 얼마 이하여야 하는가."""
    lim = 10 ** (limit_dbuv(f_hz) / 20.0) * 1e-6
    return lim * dist_m / (1.257e-6 * np.asarray(f_hz, float) * length_m)


# ══ 대책 ════════════════════════════════════════════════════════════════
def ferrite_z(f_hz, l_h=1.2e-6, r_pk=320.0, f_pk=100e6):
    """페라이트 코어의 임피던스 모형. 저주파는 유도성, 공진 위에서 저항성.

    병렬 RLC 로 본다: 낮은 f 에서 jwL, f_pk 부근에서 R, 그 위에서 용량성.
    """
    f = np.asarray(f_hz, float)
    w = 2 * np.pi * f
    c = 1.0 / (l_h * (2 * np.pi * f_pk) ** 2)
    y = 1.0 / (1j * w * l_h + 1e-12) + 1.0 / r_pk + 1j * w * c
    return 1.0 / y


def ferrite_il_db(f_hz, z_sys=150.0, **kw):
    """공통모드 경로에 직렬로 넣었을 때의 삽입손실 (dB).

    IL = 20·log10(|1 + Z_ferrite / Z_sys|)
    """
    return 20 * np.log10(np.abs(1 + ferrite_z(f_hz, **kw) / z_sys))


def aperture_se_db(f_hz, slot_m):
    """차폐 개구(슬롯)의 차폐 효과 근사. SE = 20·log10(λ / (2·L))."""
    lam = C0 / np.asarray(f_hz, float)
    return np.maximum(20 * np.log10(lam / (2 * slot_m)), 0.0)


# ══ 그림 도우미 ═════════════════════════════════════════════════════════
def mhz_ticks(ax, values_mhz):
    """가로축이 MHz 단위일 때의 눈금. rf_style.hz_ticks 는 Hz 를 가정한다."""
    def name(v):
        return f"{v / 1000:g} GHz" if v >= 1000 else f"{v:g} MHz"
    ax.set_xticks(list(values_mhz))
    ax.set_xticklabels([name(v) for v in values_mhz])
    ax.xaxis.set_minor_formatter(lambda *_: "")


# ══ 그림 ════════════════════════════════════════════════════════════════
K_COUPLE_S = 1e-5          # 하모닉 전압 1 V 가 만드는 공통모드 전류 (A/V)
CABLE_M = 1.0


def fig1_harmonics():
    fig, ax = S.figure(w=8.6, h=4.8)
    nmax = 60
    ns = np.arange(1, nmax + 1)
    fs = ns * F_CLK
    env = harmonic_envelope_dbuv(ns)
    # 하모닉 전압이 케이블에 공통모드 전류를 실어 방사한다고 본다.
    # 결합 계수는 실측으로 정해야 하는 값이라 하나로 고정해 두고 밝힌다.
    v_n = 10 ** (env / 20.0) * 1e-6                 # dBuV -> V
    i_cm = v_n * K_COUPLE_S
    rad = dbuv_m(e_from_cm_current(i_cm, fs, CABLE_M))
    keep = (fs >= 30e6) & (fs <= 1e9)
    ax.plot(fs[keep] / 1e6, rad[keep], "o", ms=6, ls="none",
            color=S.COLORS[0], label=S.txt("예상 방사 (하모닉)"))
    ax.vlines(fs[keep] / 1e6, 0, rad[keep], color=S.COLORS[0], lw=1.2,
              alpha=0.55)
    ff = np.logspace(np.log10(30e6), 9, 2000)
    ax.plot(ff / 1e6, limit_dbuv(ff), lw=2.2, ls="--", color=S.ACCENT,
            label=S.txt("규격 한도 (3 m)"))
    over = keep & (rad > limit_dbuv(fs))
    ax.plot(fs[over] / 1e6, rad[over], "o", ms=11, mfc="none", mew=2.2,
            color=S.ACCENT, zorder=6)
    n_over = int(np.sum(over))
    ax.annotate(S.txt(f"{n_over} 개가 한도를 넘는다\n"
                      f"(최악 {np.max(rad[over] - limit_dbuv(fs[over])):.1f} dB)"),
                xy=(fs[over][-1] / 1e6, rad[over][-1]),
                xytext=(160, 18), fontsize=9, color=S.ACCENT,
                fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.ACCENT, lw=0.8, alpha=0.95, pad=3),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.3))
    ax.set_xscale("log")
    mhz_ticks(ax, [30, 50, 100, 300, 500, 1000])
    ax.set_xlim(28, 1050)
    ax.set_ylim(0, 70)
    ax.set_xlabel(S.txt("주파수"))
    ax.set_ylabel(S.txt("3 m 에서의 전계 (dBuV/m)"))
    ax.set_title(S.txt(f"{F_CLK / 1e6:.0f} MHz 클럭 · 케이블 {CABLE_M:g} m · "
                       f"결합 {K_COUPLE_S * 1e6:.0f} uA/V"))
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    S.save(fig, MOD, "harmonics_vs_limit")
    return ns, env, fs, rad, over


def fig2_probe():
    fig, (a1, a2) = S.figure(w=11.2, h=4.6, ncols=2)
    seps = np.array([1.0, 2.0, 3.0, 5.0, 8.0, 12.0, 20.0, 30.0])
    for d, col, ls in zip(PROBE_D_MM, (S.COLORS[0], S.COLORS[2], S.COLORS[1]),
                          ("-", "--", "-.")):
        ct = np.array([two_trace_contrast(d, float(s))[0] for s in seps])
        a1.semilogx(seps, ct, lw=2.2, ls=ls, color=col, marker="o", ms=5,
                    label=S.txt(f"고리 지름 {d:.0f} mm"))
    S.limit_line(a1, 3.0, S.txt("3 dB — 둘로 보이기 시작"))
    a1.set_xlabel(S.txt("두 도체 사이 거리 (mm)"))
    a1.set_ylabel(S.txt("골 깊이 (dB)"))
    a1.set_ylim(0, 14)
    S.plain_log(a1, axis="x")
    a1.set_title(S.txt("작은 고리라야 둘을 가른다"))
    a1.legend(loc="upper left", fontsize=9)

    x = np.linspace(-16, 16, 321)
    for d, col, ls in zip(PROBE_D_MM, (S.COLORS[0], S.COLORS[2], S.COLORS[1]),
                          ("-", "--", "-.")):
        r = (np.abs(probe_response(x, -4.0, d))
             + np.abs(probe_response(x, +4.0, d)))
        a2.plot(x, 20 * np.log10(r / np.max(r)), lw=2.2, ls=ls, color=col,
                label=S.txt(f"{d:.0f} mm  (감도 {20 * np.log10(np.max(r) / _ref_max):+.0f} dB)"
                            if False else f"고리 지름 {d:.0f} mm"))
    for xw in (-4.0, 4.0):
        a2.axvline(xw, color=S.MUTED, lw=1.0, ls=":")
    a2.text(0, 1.5, S.txt("도체 두 개가 8 mm 간격"), ha="center", fontsize=9,
            color=S.MUTED, fontweight="bold")
    a2.set_xlabel(S.txt("스캔 위치 (mm)"))
    a2.set_ylabel(S.txt("정규화 응답 (dB)"))
    a2.set_ylim(-14, 4)
    a2.set_title(S.txt("같은 보드를 훑은 모양"))
    a2.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    S.save(fig, MOD, "probe_resolution")
    sens = {d: float(np.max(np.abs(probe_response(np.array([0.0]), 0.0, d))))
            for d in PROBE_D_MM}
    return seps, sens


_ref_max = 1.0


def fig3_map():
    fig, (a1, a2) = S.figure(w=11.6, h=4.6, ncols=2)
    maps = {h: h_field_map(h_mm=h) for h in (3.0, 12.0)}
    ref = np.max(maps[3.0][2])          # 두 패널을 **같은 기준**으로 정규화한다
    for ax, h in ((a1, 3.0), (a2, 12.0)):
        xs, ys, hmag = maps[h]
        db = 20 * np.log10(hmag / ref)
        im = ax.pcolormesh(xs, ys, db, cmap="inferno", vmin=-42, vmax=0,
                           shading="auto")
        for x0, y0, x1, y1, i_ma in BOARD_SOURCES:
            ax.plot([x0, x1], [y0, y1], color="white", lw=1.4, ls="-",
                    alpha=0.75)
        ax.set_aspect("equal")
        ax.set_xlabel(S.txt("x (mm)"))
        ax.set_title(S.txt(f"스캔 높이 {h:.0f} mm"))
        fig.colorbar(im, ax=ax,
                     label=S.txt("|H| (dB, 3 mm 스캔의 최대 기준)"))
    a1.set_ylabel(S.txt("y (mm)"))
    a1.annotate(S.txt("여기가 가장 세다"), xy=(23, 22), xytext=(44, 16),
                color="white", fontsize=9, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="white", lw=1.4))
    fig.tight_layout()
    S.save(fig, MOD, "emission_map")
    return float(np.max(maps[3.0][2]) / np.max(maps[12.0][2]))


def fig4_cm():
    fig, (a1, a2) = S.figure(w=11.2, h=4.6, ncols=2)
    ff = np.logspace(np.log10(30e6), 9, 400)
    for i_ua, col, ls in ((3.0, S.COLORS[0], "-"), (8.0, S.COLORS[2], "--"),
                          (30.0, S.COLORS[1], "-.")):
        e = dbuv_m(e_from_cm_current(i_ua * 1e-6, ff, 1.0))
        a1.semilogx(ff / 1e6, e, lw=2.2, ls=ls, color=col,
                    label=S.txt(f"공통모드 전류 {i_ua:.0f} uA"))
    a1.semilogx(ff / 1e6, limit_dbuv(ff), lw=2.4, ls="--", color=S.ACCENT,
                label=S.txt("규격 한도"))
    e8 = dbuv_m(e_from_cm_current(8e-6, 30e6, 1.0))
    a1.plot(30, e8, "o", ms=9, color=S.ACCENT, zorder=7)
    a1.annotate(S.txt(f"30 MHz · 1 m · 8 uA\n= {e8:.1f} dBuV/m"),
                xy=(30, e8), xytext=(75, 22), fontsize=9, color=S.ACCENT,
                fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.ACCENT, lw=0.8, alpha=0.95, pad=3),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    mhz_ticks(a1, [30, 50, 100, 300, 500, 1000])
    a1.set_xlim(28, 1050)
    a1.set_ylim(10, 80)
    a1.set_xlabel(S.txt("주파수"))
    a1.set_ylabel(S.txt("3 m 에서의 전계 (dBuV/m)"))
    a1.set_title(S.txt("케이블 1 m 에 흐르는 공통모드 전류"))
    a1.legend(loc="upper left", fontsize=8.5)

    for lm, col, ls in ((0.3, S.COLORS[0], "-"), (1.0, S.COLORS[2], "--"),
                        (3.0, S.COLORS[1], "-.")):
        a2.loglog(ff / 1e6, cm_current_limit_a(ff, lm) * 1e6, lw=2.2, ls=ls,
                  color=col, label=S.txt(f"케이블 {lm:g} m"))
    a2.set_xlabel(S.txt("주파수"))
    a2.set_ylabel(S.txt("허용 공통모드 전류 (uA)"))
    mhz_ticks(a2, [30, 50, 100, 300, 500, 1000])
    a2.set_xlim(28, 1050)
    a2.set_yticks([1, 2, 5, 10, 20])
    a2.set_yticklabels(["1", "2", "5", "10", "20"])
    a2.yaxis.set_minor_formatter(lambda *_: "")
    a2.set_ylim(0.55, 30)
    a2.set_title(S.txt("전류 프로브로 이 값만 지키면 된다"))
    a2.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    S.save(fig, MOD, "cm_current")
    return float(e8), {lm: float(cm_current_limit_a(30e6, lm) * 1e6)
                       for lm in (0.3, 1.0, 3.0)}


def fig5_mitigation():
    fig, (a1, a2) = S.figure(w=11.2, h=4.6, ncols=2)
    ff = np.logspace(6, 9.3, 500)
    for (rpk, fpk, lh), col, ls in (((320.0, 100e6, 1.2e-6), S.COLORS[0], "-"),
                                    ((120.0, 300e6, 0.12e-6), S.COLORS[2],
                                     "--")):
        a1.semilogx(ff / 1e6, ferrite_il_db(ff, l_h=lh, r_pk=rpk, f_pk=fpk),
                    lw=2.2, ls=ls, color=col,
                    label=S.txt(f"페라이트 |Z|max {rpk:.0f} ohm "
                                f"@ {fpk / 1e6:.0f} MHz"))
    a1.set_xlabel(S.txt("주파수"))
    a1.set_ylabel(S.txt("공통모드 삽입손실 (dB)"))
    mhz_ticks(a1, [1, 10, 100, 1000])
    a1.set_xlim(1, 2000)
    a1.set_ylim(0, 10)
    a1.set_title(S.txt("페라이트는 자기 공진 부근에서만 듣는다"))
    a1.legend(loc="upper left", fontsize=8.5)

    fa = np.logspace(6, 10.6, 600)
    for slot_mm, col, ls, ytxt in ((5.0, S.COLORS[0], "-", 11.0),
                                   (20.0, S.COLORS[2], "--", 7.0),
                                   (50.0, S.COLORS[1], "-.", 3.0)):
        a2.semilogx(fa / 1e6, aperture_se_db(fa, slot_mm * 1e-3), lw=2.2,
                    ls=ls, color=col,
                    label=S.txt(f"슬롯 {slot_mm:.0f} mm"))
        f_zero = C0 / (2 * slot_mm * 1e-3)
        a2.plot(f_zero / 1e6, 0.0, "v", ms=9, color=col, zorder=6)
        a2.annotate(S.txt(f"{f_zero / 1e9:.1f} GHz"), xy=(f_zero / 1e6, 0),
                    xytext=(f_zero / 1e6, ytxt), ha="center", fontsize=8.5,
                    color=col, fontweight="bold",
                    bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.0))
    a2.set_xlabel(S.txt("주파수"))
    a2.set_ylabel(S.txt("차폐 효과 (dB)"))
    mhz_ticks(a2, [1, 10, 100, 1000, 10000])
    a2.set_xlim(1, 4e4)
    a2.set_ylim(0, 80)
    a2.set_title(S.txt("차폐는 구멍이 정한다 — 금속 두께가 아니다"))
    a2.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    S.save(fig, MOD, "mitigation")
    return {f: float(ferrite_il_db(f)) for f in (10e6, 100e6, 500e6, 1e9)}, \
           {s: float(C0 / (2 * s * 1e-3) / 1e6) for s in (5.0, 20.0, 50.0)}


# ══ 본문 ════════════════════════════════════════════════════════════════
def main() -> int:
    print("B07 그림 생성")
    print("=" * 62)

    ns, env, fs, rad, over = fig1_harmonics()
    print(f"  [1] 하모닉             {int(np.sum(over))} 개가 한도 초과 "
          f"(최악 {np.max(rad[over] - limit_dbuv(fs[over])):.1f} dB)")

    seps, sens = fig2_probe()
    print("  [2] 프로브             감도 비 = " +
          ", ".join(f"{d:.0f}mm {sens[d] / sens[2.0]:.0f}배"
                    for d in PROBE_D_MM))

    hratio = fig3_map()
    print(f"  [3] 스캔 지도          높이 3 → 12 mm 에서 최대 |H| 가 "
          f"{20 * np.log10(hratio):.1f} dB 낮아진다")

    e8, cmlim = fig4_cm()
    print(f"  [4] 공통모드           8 uA · 1 m · 30 MHz → {e8:.1f} dBuV/m")

    fer, slots = fig5_mitigation()
    print("  [5] 대책               페라이트 삽입손실 = " +
          ", ".join(f"{f / 1e6:.0f}MHz {v:.1f}dB" for f, v in fer.items()))

    print()
    print("본문에 쓰는 값")
    print("-" * 62)
    print(f"  클럭 {F_CLK / 1e6:.0f} MHz · 상승시간 {T_RISE * 1e9:.1f} ns")
    print(f"  포락선 꺾임 1: 1/(pi·d·T) = "
          f"{1 / (np.pi * DUTY / F_CLK) / 1e6:.1f} MHz")
    print(f"  포락선 꺾임 2: 1/(pi·tr)  = "
          f"{1 / (np.pi * T_RISE) / 1e6:.1f} MHz")
    print(f"  상승시간을 3 ns 로 늦추면 두 번째 꺾임이 "
          f"{1 / (np.pi * 3e-9) / 1e6:.1f} MHz 로 내려온다")
    for d in PROBE_D_MM:
        ct8 = two_trace_contrast(d, 8.0)[0]
        print(f"  고리 {d:4.1f} mm    감도 {sens[d] / sens[2.0]:5.1f}배 · "
              f"8 mm 간격 골 깊이 {ct8:5.2f} dB")
    print(f"  스캔 높이 3 → 12 mm       최대 |H| {20 * np.log10(hratio):.1f} dB 감소")
    print(f"  8 uA · 1 m · 30 MHz       {e8:.1f} dBuV/m "
          f"(한도 {float(limit_dbuv(30e6)):.0f})")
    for lm, v in cmlim.items():
        print(f"  30 MHz 허용 전류 (케이블 {lm:g} m)  {v:.1f} uA")
    for f, v in fer.items():
        print(f"  페라이트 삽입손실 {f / 1e6:6.0f} MHz   {v:5.2f} dB")
    for s, v in slots.items():
        print(f"  슬롯 {s:4.0f} mm → 차폐 효과 0 dB 가 되는 주파수  {v:.0f} MHz")

    # ── 자체 검산 ───────────────────────────────────────────────────────
    print()
    print("[자체 검산]")
    ok = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  {'OK ' if cond else 'X  '} {msg}")

    # 클럭 스펙트럼 (교차검증 ①)
    fftv = harmonic_fft_dbuv(40)
    envv = harmonic_envelope_dbuv(np.arange(1, 41))
    odd = np.arange(1, 41) % 2 == 1
    err = np.max(np.abs(fftv[odd] - envv[odd]))
    chk(err < 0.05,
        f"홀수 하모닉 40개까지 FFT 와 닫힌 식 최대 차 {err:.4f} dB")
    chk(np.all(fftv[~odd] < envv[odd].min() - 20),
        "듀티 50 % 라 짝수 하모닉이 사실상 없다")
    f1 = 1 / (np.pi * DUTY / F_CLK)
    f2 = 1 / (np.pi * T_RISE)
    # 포락선 기울기는 넓은 차수 범위에서 봐야 한다
    nn = np.arange(1, 4001)
    ee = harmonic_envelope_dbuv(nn)
    ff_n = nn * F_CLK
    od = nn % 2 == 1
    mid = od & (ff_n > f1 * 1.5) & (ff_n < f2 * 0.6)
    sl_mid = np.polyfit(np.log10(ff_n[mid]), ee[mid], 1)[0]
    chk(abs(sl_mid + 20) < 1.5,
        f"첫 꺾임과 둘째 꺾임 사이 기울기 {sl_mid:.1f} dB/dec (이론 -20)")
    hi = od & (ff_n > f2 * 3)
    sl_hi = np.polyfit(np.log10(ff_n[hi]), ee[hi], 1)[0]
    chk(abs(sl_hi + 40) < 2.0,
        f"둘째 꺾임 위 기울기 {sl_hi:.1f} dB/dec (이론 -40)")
    chk(abs(f2 - 212.2e6) < 1e6,
        f"1/(pi·tr) = {f2 / 1e6:.1f} MHz")
    chk(1 / (np.pi * 3e-9) < f2,
        "상승시간을 늦추면 둘째 꺾임이 낮은 주파수로 내려온다")

    # 프로브 (교차검증 ②)
    for r1, r2 in ((1e-3, 5e-3), (2e-3, 20e-3), (0.5e-3, 3e-3)):
        c = flux_wire_closed(1e-3, 10e-3, r1, r2)
        n = flux_wire_numeric(1e-3, 10e-3, r1, r2)
        chk(abs(c / n - 1) < 1e-6,
            f"자속 닫힌 식 {c:.4e} vs 수치 {n:.4e} Wb "
            f"(r {r1 * 1e3:.1f}~{r2 * 1e3:.0f} mm)")
    chk(sens[20.0] > sens[2.0] * 5,
        f"20 mm 고리가 2 mm 고리보다 {sens[20.0] / sens[2.0]:.0f}배 민감하다")
    ct = {d: two_trace_contrast(d, 8.0)[0] for d in PROBE_D_MM}
    chk(ct[2.0] > ct[6.0] > ct[20.0],
        f"고리가 클수록 골이 얕다 ({ct[2.0]:.1f} > {ct[6.0]:.1f} > "
        f"{ct[20.0]:.1f} dB)")
    chk(ct[20.0] < 3.0 < ct[2.0],
        "8 mm 간격에서 2 mm 고리는 둘로 보고 20 mm 고리는 못 본다")

    # 스캔 지도
    chk(hratio > 3.0,
        f"낮게 훑을수록 세다 (3 mm 가 12 mm 보다 {hratio:.1f}배)")

    # 공통모드 (교차검증 ③)
    ratio = float(e_from_cm_current(1e-6, 100e6, 1.0)
                  / e_dipole_freespace(1e-6, 100e6, 1.0))
    chk(abs(ratio - 2.0) < 0.005,
        f"닫힌 식이 자유공간 다이폴의 {ratio:.4f} 배 — 접지면 반사 2배")
    chk(abs(e_from_cm_current(8e-6, 30e6, 1.0) * 1e6 - 100.6) < 1.0,
        f"계측사 사례 재현: 30 MHz·1 m·8 uA → "
        f"{e_from_cm_current(8e-6, 30e6, 1.0) * 1e6:.1f} uV/m (자료 100)")
    chk(abs(float(limit_dbuv(30e6)) - 40.0) < 1e-9,
        "30~88 MHz 한도 40 dBuV/m = 100 uV/m")
    chk(abs(cmlim[1.0] - 7.96) < 0.2,
        f"그래서 1 m 케이블의 30 MHz 허용 전류가 {cmlim[1.0]:.2f} uA")
    chk(abs(cmlim[0.3] / cmlim[1.0] - 1 / 0.3) < 0.01,
        "케이블이 짧으면 그만큼 더 흘려도 된다 (길이에 반비례)")
    chk(e_from_cm_current(8e-6, 60e6, 1.0) > e_from_cm_current(8e-6, 30e6, 1.0),
        "같은 전류라도 주파수가 높으면 더 방사한다")

    # 대책 (교차검증 ④)
    zf = ferrite_z(100e6)
    chk(abs(abs(zf) - 320.0) / 320.0 < 0.02,
        f"공진에서 |Z| = {abs(zf):.0f} ohm (설계값 320)")
    il_num = float(ferrite_il_db(100e6))
    il_apx = 20 * np.log10(1 + 320.0 / 150.0)
    chk(abs(il_num - il_apx) < 0.1,
        f"공진에서 삽입손실 {il_num:.2f} dB ≈ 임피던스 비 근사 {il_apx:.2f} dB")
    chk(fer[1e9] < fer[100e6] - 3,
        f"1 GHz 에서는 {fer[1e9]:.2f} dB 로 떨어진다 "
        f"(100 MHz 의 {fer[100e6]:.2f} dB 대비)")
    chk(fer[10e6] < 3.0,
        f"10 MHz 에서도 {fer[10e6]:.2f} dB 밖에 안 된다 — 아래위 모두 안 듣는다")
    f_half = C0 / (2 * 0.05)
    chk(abs(aperture_se_db(f_half, 0.05)) < 1e-9,
        f"슬롯이 반파장({f_half / 1e9:.2f} GHz)이 되면 차폐 효과가 0 이 된다")
    chk(abs(aperture_se_db(300e6, 0.05) - 20 * np.log10(1.0 / 0.1)) < 0.02,
        f"300 MHz 에서 50 mm 슬롯의 차폐 효과 "
        f"{float(aperture_se_db(300e6, 0.05)):.2f} dB (λ/2L = 10 배)")
    chk(aperture_se_db(300e6, 0.005) > aperture_se_db(300e6, 0.05),
        "슬롯을 10배 짧게 하면 20 dB 좋아진다")

    print()
    if not all(ok):
        return 1
    print(f"  검산 {len(ok)}항목 전부 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
