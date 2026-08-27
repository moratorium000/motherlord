#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B08 (전원·바이어스·열 — 벤치에서 재는 법) 그림 생성기.

만드는 그림
  B08-1  바이어스 인가 순서와 돌입 전류
  B08-2  전류를 재는 세 가지 방법의 절충
  B08-3  안정화 곡선 — 언제부터 값이 안 움직이는가
  B08-4  PAE 와 손실 분해 — 무엇을 분모에 넣는가
  B08-5  안전 동작 영역과 디레이팅

교차검증 네 갈래
  ① 돌입 전류: 직렬 RLC 계단 응답의 닫힌 식 vs 시간 적분
  ② 안정화: 2극 열 모형의 닫힌 식 vs 수치 적분, 그리고 정착 시간 판정
  ③ PAE: 에너지 수지가 닫히는가 (Pdc + Pin = Pout + 손실 합)
  ④ 접합온도: 열저항 사슬의 합 vs 단계별 온도 상승의 누적

실행: python3 scripts/gen_fig_b08.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rf_style as S  # noqa: E402

MOD = "B08"

# ── 소자와 전원 ─────────────────────────────────────────────────────────
VDD = 50.0
C_BULK = 470e-6          # 드레인 쪽 대용량 커패시터
ESR = 0.030              # 그 커패시터의 등가 직렬 저항
R_PATH = 0.045           # 전원-보드 경로 저항 (케이블 + 배선)
L_PATH = 350e-9          # 같은 경로의 인덕턴스

# ── 열 ──────────────────────────────────────────────────────────────────
RTH_JC = 0.55            # 접합-케이스 (°C/W)
RTH_CS = 0.20            # 케이스-히트싱크 (열전도 패드)
RTH_SA = 1.10            # 히트싱크-주위
TAU_DIE = 0.020          # 다이 쪽 빠른 시상수 (s)
TAU_SINK = 240.0         # 히트싱크 쪽 느린 시상수 (s)
K_GAIN_DB_C = 0.010      # 이득 온도계수 (dB/°C)
T_AMB = 25.0
TJ_MAX = 225.0

# ── 대신호 동작점 ───────────────────────────────────────────────────────
P_OUT_W = 42.0
GAIN_DB = 13.0
I_DC_A = 1.55


# ══ 돌입 전류 ═══════════════════════════════════════════════════════════
def inrush_closed(t, v=VDD, r=R_PATH + ESR, l=L_PATH, c=C_BULK):
    """빈 커패시터에 전압을 걸었을 때의 전류 (직렬 RLC 계단 응답).

    감쇠가 큰 쪽(과감쇠)이면 두 지수의 차, 적으면 감쇠 진동이다.
    두 경우를 한 식으로 쓰기 위해 복소수로 계산하고 실수부만 취한다.
    """
    t = np.asarray(t, float)
    a = r / (2 * l)
    w0 = 1.0 / np.sqrt(l * c)
    s = np.sqrt(complex(a ** 2 - w0 ** 2))
    if abs(s) < 1e-12:                       # 임계 감쇠
        return v / l * t * np.exp(-a * t)
    return np.real(v / (l * 2 * s) * (np.exp((-a + s) * t)
                                      - np.exp((-a - s) * t)))


def inrush_numeric(t_end, n=400_001, v=VDD, r=R_PATH + ESR, l=L_PATH,
                   c=C_BULK):
    """같은 것을 시간 적분으로 (교차검증 ①). L di/dt = V - iR - vC."""
    dt = t_end / (n - 1)
    i = 0.0
    vc = 0.0
    ts = np.empty(n)
    iss = np.empty(n)
    for k in range(n):
        ts[k] = k * dt
        iss[k] = i
        di = (v - i * r - vc) / l
        dvc = i / c
        i += di * dt
        vc += dvc * dt
    return ts, iss


def inrush_peak_closed(v=VDD, r=R_PATH + ESR, l=L_PATH, c=C_BULK):
    t = np.linspace(0, 8e-4, 400_001)
    i = inrush_closed(t, v, r, l, c)
    k = int(np.argmax(i))
    return float(i[k]), float(t[k])


# ══ 전류 측정 ═══════════════════════════════════════════════════════════
def shunt_burden_v(i_a, r_shunt):
    """션트가 만드는 전압 강하. 이것이 DUT 에서 빠진다."""
    return np.asarray(i_a, float) * np.asarray(r_shunt, float)


def shunt_bw_hz(r_shunt, l_par=2e-9):
    """션트의 기생 인덕턴스가 정하는 대역폭. f = R / (2πL)."""
    return np.asarray(r_shunt, float) / (2 * np.pi * l_par)


def shunt_snr_db(i_a, r_shunt, v_noise=20e-6):
    """계측 증폭기 입력 환산 잡음 대비 신호."""
    return 20 * np.log10(shunt_burden_v(i_a, r_shunt) / v_noise)


# ══ 안정화 ══════════════════════════════════════════════════════════════
def temp_rise(t, p_w, rjc=RTH_JC, rcs=RTH_CS, rsa=RTH_SA,
              tau_die=TAU_DIE, tau_sink=TAU_SINK):
    """2극 열 모형의 접합 온도 상승 (닫힌 식).

    빠른 극은 다이-케이스, 느린 극은 히트싱크-주위. 둘을 더한다.
    """
    t = np.asarray(t, float)
    r_fast = rjc + rcs
    r_slow = rsa
    return (p_w * r_fast * (1 - np.exp(-t / tau_die))
            + p_w * r_slow * (1 - np.exp(-t / tau_sink)))


def temp_rise_numeric(t_end, p_w, n=400_001, **kw):
    """같은 것을 두 개의 1차 미분방정식으로 (교차검증 ②).

    오일러 전진법은 빠른 극(20 ms)에서 걸음이 굵어 1 % 넘게 벌어진다.
    2차(호인)법을 쓰면 같은 걸음으로 오차가 세제곱으로 줄어든다.
    """
    rjc = kw.get("rjc", RTH_JC); rcs = kw.get("rcs", RTH_CS)
    rsa = kw.get("rsa", RTH_SA)
    tau_die = kw.get("tau_die", TAU_DIE); tau_sink = kw.get("tau_sink", TAU_SINK)
    dt = t_end / (n - 1)
    a = b = 0.0
    a_inf, b_inf = p_w * (rjc + rcs), p_w * rsa
    ts = np.empty(n); out = np.empty(n)
    for k in range(n):
        ts[k] = k * dt
        out[k] = a + b
        for val, inf, tau in (("a", a_inf, tau_die), ("b", b_inf, tau_sink)):
            y = a if val == "a" else b
            k1 = (inf - y) / tau
            k2 = (inf - (y + dt * k1)) / tau
            y = y + dt * 0.5 * (k1 + k2)
            if val == "a":
                a = y
            else:
                b = y
    return ts, out


def settle_time(tol_db, p_w, k=K_GAIN_DB_C, t_max=3000.0):
    """이득이 최종값의 ±tol_db 안으로 들어오는 시간."""
    t = np.linspace(0, t_max, 300_001)
    g = -k * temp_rise(t, p_w)
    g_inf = g[-1]
    bad = np.abs(g - g_inf) > tol_db
    return float(t[np.max(np.where(bad)[0])]) if np.any(bad) else 0.0


# ══ PAE ═════════════════════════════════════════════════════════════════
def pae(p_out_w, p_in_w, p_dc_w):
    return (p_out_w - p_in_w) / p_dc_w * 100.0


def drain_eff(p_out_w, p_dc_w):
    return p_out_w / p_dc_w * 100.0


def module_budget(p_out_w=P_OUT_W, gain_db=GAIN_DB, i_dc=I_DC_A, vdd=VDD,
                  loss_out_db=0.35, loss_in_db=0.25,
                  drv_dc_w=3.2, gate_dc_w=0.15, cable_r=0.045):
    """소자 기준 PAE 와 모듈 기준 PAE 를 함께 계산한다.

    벤치에서 갈리는 지점 셋: 출력 정합·케이블 손실을 어디까지 세는가,
    드라이버 단과 게이트 전원을 분모에 넣는가, 전원 케이블 손실은.
    """
    p_in_w = p_out_w / 10 ** (gain_db / 10.0)
    # 소자 기준: 커넥터에서 잰 값을 손실만큼 되돌린다
    p_out_dev = p_out_w * 10 ** (loss_out_db / 10.0)
    p_in_dev = p_in_w / 10 ** (loss_in_db / 10.0)
    p_dc_dev = vdd * i_dc
    # 모듈 기준: 커넥터 값 그대로, 분모에 드라이버·게이트·케이블 손실 추가
    p_cable = i_dc ** 2 * cable_r
    p_dc_mod = p_dc_dev + drv_dc_w + gate_dc_w + p_cable
    return {
        "p_in_w": p_in_w, "p_out_dev": p_out_dev, "p_in_dev": p_in_dev,
        "p_dc_dev": p_dc_dev, "p_dc_mod": p_dc_mod, "p_cable": p_cable,
        "drv_dc_w": drv_dc_w, "gate_dc_w": gate_dc_w,
        "loss_out_w": p_out_dev - p_out_w,
        "loss_in_w": p_in_dev - p_in_w,
        "pae_dev": pae(p_out_dev, p_in_dev, p_dc_dev),
        "pae_mod": pae(p_out_w, p_in_w, p_dc_mod),
        "de_dev": drain_eff(p_out_dev, p_dc_dev),
        "p_diss_dev": p_dc_dev + p_in_dev - p_out_dev,
    }


# ══ 열저항 사슬과 SOA ═══════════════════════════════════════════════════
def tj(p_diss_w, t_amb=T_AMB, rjc=RTH_JC, rcs=RTH_CS, rsa=RTH_SA):
    return t_amb + np.asarray(p_diss_w, float) * (rjc + rcs + rsa)


def p_max_derate(t_case, tj_max=TJ_MAX, rjc=RTH_JC):
    """케이스 온도별 허용 손실 전력. (Tjmax - Tc) / Rth_jc."""
    return np.maximum((tj_max - np.asarray(t_case, float)) / rjc, 0.0)


# ══ 그림 ════════════════════════════════════════════════════════════════
def fig1_bias():
    fig, (a1, a2) = S.figure(w=11.4, h=4.8, ncols=2)

    # (A) 시퀀싱 타이밍
    t = np.linspace(-60, 340, 4000)          # ms
    vg_on, vd_on, rf_on = 0.0, 130.0, 200.0
    vg = np.where(t < vg_on, 0.0, -1.0)      # 음의 게이트 (공핍형 GaN)
    vd = np.where(t < vd_on, 0.0, 1.0)
    rf = np.where(t < rf_on, 0.0, 1.0)
    a1.plot(t, vg + 4.6, lw=2.0, ls="-", color=S.COLORS[0])
    a1.plot(t, vd + 2.6, lw=2.0, ls="-", color=S.COLORS[1])
    a1.plot(t, rf + 0.6, lw=2.0, ls="-", color=S.COLORS[2])
    for x, lab, col in ((vg_on, "게이트 (음전압) 먼저", S.COLORS[0]),
                        (vd_on, "드레인", S.COLORS[1]),
                        (rf_on, "RF 구동 마지막", S.COLORS[2])):
        a1.axvline(x, color=col, lw=1.0, ls=":", zorder=1)
    for y, lab in ((4.1, "Vgs"), (2.1, "Vds"), (0.1, "RF")):
        a1.text(-56, y + 0.5, S.txt(lab), fontsize=10, fontweight="bold",
                va="center")
    a1.annotate("", xy=(vg_on, 6.15), xytext=(vd_on, 6.15),
                arrowprops=dict(arrowstyle="<->", color=S.ACCENT, lw=1.4))
    a1.text((vg_on + vd_on) / 2, 6.3, S.txt(f"{vd_on - vg_on:.0f} ms 앞서 건다"),
            fontsize=9, color=S.ACCENT, fontweight="bold", ha="center",
            va="bottom")
    a1.text(336, 1.6, S.txt("끌 때는 정확히 거꾸로\nRF → 드레인 → 게이트"),
            fontsize=9, color=S.ACCENT, fontweight="bold", ha="right",
            va="bottom",
            bbox=dict(fc="white", ec=S.ACCENT, lw=0.8, alpha=0.95, pad=3))
    a1.set_xlim(-60, 340)
    a1.set_ylim(0, 7.1)
    a1.set_yticks([])
    a1.grid(False)
    a1.set_xlabel(S.txt("시간 (ms)"))
    a1.set_title(S.txt("공핍형 소자의 인가 순서"))

    # (B) 돌입 전류
    t2 = np.linspace(0, 5e-4, 6000)
    for c, col, ls in ((C_BULK, S.COLORS[0], "-"),
                       (C_BULK / 10, S.COLORS[2], "--")):
        i = inrush_closed(t2, c=c)
        a2.plot(t2 * 1e6, i, lw=2.2, ls=ls, color=col,
                label=S.txt(f"벌크 {c * 1e6:.0f} uF"))
    ip, tp = inrush_peak_closed()
    a2.plot(tp * 1e6, ip, "o", ms=8, color=S.ACCENT, zorder=7)
    a2.annotate(S.txt(f"첨두 {ip:.0f} A @ {tp * 1e6:.0f} us\n"
                      f"= 정상 전류의 {ip / I_DC_A:.0f}배"),
                xy=(tp * 1e6, ip), xytext=(230, ip * 0.88),
                fontsize=9, color=S.ACCENT, fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.ACCENT, lw=0.8, alpha=0.95, pad=3),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    a2.annotate(S.txt("작은 커패시터는 덜 감쇠해\n음의 방향으로 되튄다"),
                xy=(58, -70), xytext=(250, -160), fontsize=9,
                color=S.COLORS[2], fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.COLORS[2], lw=0.8, alpha=0.95,
                          pad=3),
                arrowprops=dict(arrowstyle="->", color=S.COLORS[2], lw=1.2))
    S.limit_line(a2, I_DC_A, S.txt(f"정상 동작 전류 {I_DC_A:.2f} A"))
    a2.axhline(0, color=S.MUTED, lw=1.0, ls=":")
    a2.set_xlim(0, 500)
    a2.set_ylim(-230, ip * 1.15)
    a2.set_xlabel(S.txt("시간 (us)"))
    a2.set_ylabel(S.txt("전원 전류 (A)"))
    a2.set_title(S.txt("빈 커패시터가 만드는 돌입"))
    a2.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    S.save(fig, MOD, "bias_sequence")
    return ip, tp


def fig2_current():
    fig, (a1, a2) = S.figure(w=11.2, h=4.6, ncols=2)
    rs = np.logspace(-4, -0.7, 300)
    v_burden_max = 0.050                       # 허용 부담 전압 (드레인 50 V 의 0.1 %)
    snr_min = 40.0
    a1.loglog(rs * 1e3, shunt_burden_v(I_DC_A, rs) * 1e3, lw=2.4, ls="-",
              color=S.COLORS[0])
    a1.set_xlabel(S.txt("션트 저항 (mohm)"))
    a1.set_ylabel(S.txt(f"부담 전압 (mV) — {I_DC_A:.2f} A 에서"),
                  color=S.COLORS[0])
    a1.tick_params(axis="y", labelcolor=S.COLORS[0])
    a1.axhline(v_burden_max * 1e3, color=S.ACCENT, lw=1.6, ls="--")
    a1.text(0.12, v_burden_max * 1e3 * 1.25,
            S.txt(f"부담 한도 {v_burden_max * 1e3:.0f} mV"), fontsize=8.5,
            color=S.ACCENT, fontweight="bold")
    b1 = a1.twinx()
    b1.semilogx(rs * 1e3, shunt_snr_db(I_DC_A, rs), lw=2.4, ls="--",
                color=S.COLORS[1])
    b1.set_ylabel(S.txt("SNR (dB)"), color=S.COLORS[1])
    b1.tick_params(axis="y", labelcolor=S.COLORS[1])
    b1.axhline(snr_min, color=S.COLORS[1], lw=1.2, ls=":")
    b1.text(120, snr_min + 1.5, S.txt(f"SNR 하한 {snr_min:.0f} dB"),
            fontsize=8.5, color=S.COLORS[1], fontweight="bold", ha="right")
    b1.grid(False)
    b1.set_ylim(0, 95)
    # 쓸 수 있는 창: 부담 한도 아래이면서 SNR 하한 위
    r_hi = v_burden_max / I_DC_A
    r_lo = 10 ** (snr_min / 20.0) * 20e-6 / I_DC_A
    b1.axvspan(r_lo * 1e3, r_hi * 1e3, color=S.COLORS[2], alpha=0.16, lw=0,
               zorder=0)
    b1.annotate(S.txt(f"쓸 수 있는 창\n{r_lo * 1e3:.1f} ~ {r_hi * 1e3:.1f} mohm"),
                xy=(np.sqrt(r_lo * r_hi) * 1e3, 20),
                xytext=(np.sqrt(r_lo * r_hi) * 1e3, 8), fontsize=9,
                color=S.COLORS[2], fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.COLORS[2], lw=0.8, alpha=0.95,
                          pad=3))
    S.plain_log(a1, axis="both")
    a1.set_title(S.txt("션트 저항 하나가 셋을 동시에 정한다"))

    methods = ("션트 저항", "홀 소자", "전류 프로브")
    metrics = {
        "직류를 재는가": (1.0, 1.0, 0.0),
        "회로에 끼어드는가": (1.0, 0.6, 0.0),
        "대역폭": (0.55, 0.35, 1.0),
        "절연": (0.0, 1.0, 1.0),
        "표류·오프셋 없음": (1.0, 0.3, 0.7),
    }
    x = np.arange(len(metrics))
    for i, m in enumerate(methods):
        vals = [metrics[k][i] for k in metrics]
        a2.bar(x + (i - 1) * 0.28, vals, 0.26, color=S.COLORS[i],
               label=S.txt(m))
    a2.set_xticks(x)
    a2.set_xticklabels([S.txt(k) for k in metrics], fontsize=8.5, rotation=12)
    a2.set_yticks([0, 0.5, 1.0])
    a2.set_yticklabels([S.txt("못한다"), S.txt("조건부"), S.txt("된다")],
                       fontsize=9)
    a2.set_ylim(0, 1.25)
    a2.set_title(S.txt("세 방법 — 하나로 다 되지 않는다"))
    a2.legend(loc="upper right", fontsize=8.5, ncol=3)
    fig.tight_layout()
    S.save(fig, MOD, "current_sensing")
    return r_lo, r_hi


def fig3_settle():
    fig, ax = S.figure(w=8.0, h=4.8)
    p = 60.0
    t = np.logspace(-3, 3.6, 1200)
    dg = -K_GAIN_DB_C * temp_rise(t, p)
    ax.semilogx(t, dg, lw=2.6, ls="-", color=S.COLORS[0])
    g_inf = float(dg[-1])
    for tol, col in ((0.20, S.COLORS[2]), (0.05, S.ACCENT)):
        ts = settle_time(tol, p)
        ax.axvline(ts, color=col, lw=1.4, ls="--")
        ax.annotate(S.txt(f"±{tol:.2f} dB 안: {ts:.0f} s"
                          f" ({ts / 60:.1f} 분)"),
                    xy=(ts, g_inf * 0.55),
                    xytext=(ts * 0.055, g_inf * (0.30 if tol == 0.2 else 0.62)),
                    fontsize=9, color=col, fontweight="bold",
                    bbox=dict(fc="white", ec=col, lw=0.8, alpha=0.95, pad=3),
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.2))
    ax.axhline(g_inf, color=S.MUTED, lw=1.2, ls=":")
    ax.text(2600, g_inf + 0.045, S.txt(f"최종 {g_inf:.2f} dB"),
            fontsize=9, color=S.INK, fontweight="bold", ha="right",
            bbox=dict(fc="white", ec="none", alpha=0.9, pad=1.5))
    ax.annotate(S.txt("다이가 데워지는 구간\n(수십 ms)"),
                xy=(0.05, -K_GAIN_DB_C * temp_rise(0.05, p)),
                xytext=(0.0035, g_inf * 0.42), fontsize=9, color=S.INK,
                bbox=dict(fc="white", ec=S.MUTED, lw=0.8, alpha=0.9, pad=2),
                arrowprops=dict(arrowstyle="->", color=S.MUTED, lw=1.1))
    ax.set_xlabel(S.txt("전원을 넣고 지난 시간 (s)"))
    ax.set_ylabel(S.txt("이득 변화 (dB)"))
    S.plain_log(ax, axis="x")
    ax.set_title(S.txt(f"손실 {p:.0f} W 를 넣었을 때의 안정화"))
    fig.tight_layout()
    S.save(fig, MOD, "settling_curve")
    return {tol: settle_time(tol, p) for tol in (0.2, 0.05, 0.02)}, g_inf


def fig4_pae():
    b = module_budget()
    fig, (a1, a2) = S.figure(w=11.4, h=4.6, ncols=2)

    labels = [S.txt(x) for x in ("RF 출력\n(커넥터)", "출력 정합·\n케이블 손실",
                                 "소자 손실\n(열)", "드라이버 단",
                                 "게이트·전원\n케이블")]
    vals = [P_OUT_W, b["loss_out_w"], b["p_diss_dev"], b["drv_dc_w"],
            b["gate_dc_w"] + b["p_cable"]]
    cols = [S.COLORS[2], S.COLORS[4], S.COLORS[1], S.COLORS[0], S.MUTED]
    bottom = 0.0
    last_small = -99.0
    for lab, v, c in zip(labels, vals, cols):
        a1.bar(0, v, 0.55, bottom=bottom, color=c, label=lab)
        if v > 6:
            a1.text(0, bottom + v / 2, f"{v:.1f} W", ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold")
        else:
            ytxt = bottom + v / 2
            if ytxt - last_small < 3.0:          # 작은 조각끼리 겹치지 않게
                ytxt = last_small + 3.0
            last_small = ytxt
            a1.annotate(f"{v:.1f} W", xy=(0.28, bottom + v / 2),
                        xytext=(0.45, ytxt), fontsize=8.5,
                        color=S.INK, va="center", ha="left",
                        arrowprops=dict(arrowstyle="-", color=S.MUTED, lw=0.9))
        bottom += v
    a1.set_xlim(-0.6, 1.5)
    a1.set_xticks([])
    a1.set_ylabel(S.txt("전력 (W)"))
    a1.set_title(S.txt(f"들어간 것 {bottom:.1f} W 가 어디로 갔는가"))
    a1.legend(loc="center right", fontsize=8.5)

    names = ("드레인 효율\n(소자 기준)", "PAE\n(소자 기준)", "PAE\n(모듈 기준)")
    v2 = [b["de_dev"], b["pae_dev"], b["pae_mod"]]
    a2.bar(range(3), v2, 0.5, color=[S.COLORS[2], S.COLORS[0], S.COLORS[1]])
    for i, v in enumerate(v2):
        a2.text(i, v + 0.8, f"{v:.1f} %", ha="center", fontsize=10,
                fontweight="bold")
    a2.set_xticks(range(3))
    a2.set_xticklabels([S.txt(n) for n in names], fontsize=9)
    a2.set_ylabel(S.txt("효율 (%)"))
    a2.set_ylim(0, max(v2) * 1.28)
    a2.annotate(S.txt(f"{b['de_dev'] - b['pae_mod']:.1f} 포인트 차이\n"
                      f"— 같은 측정이다"),
                xy=(2, v2[2]), xytext=(1.1, max(v2) * 1.13), fontsize=9,
                color=S.ACCENT, fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.ACCENT, lw=0.8, alpha=0.95, pad=3),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    a2.set_title(S.txt("무엇을 분자·분모에 넣었는지 밝혀야 한다"))
    fig.tight_layout()
    S.save(fig, MOD, "pae_breakdown")
    return b


def fig5_soa():
    fig, (a1, a2) = S.figure(w=11.2, h=4.6, ncols=2)

    v = np.linspace(1, 75, 500)
    for pmax, col, ls in ((150.0, S.COLORS[0], "-"), (90.0, S.COLORS[2], "--"),
                          (45.0, S.COLORS[1], "-.")):
        a1.plot(v, pmax / v, lw=2.2, ls=ls, color=col,
                label=S.txt(f"허용 손실 {pmax:.0f} W"))
    a1.axvline(65.0, color=S.ACCENT, lw=2.0, ls="--")
    a1.text(63.5, 5.2, S.txt("Vds 최대"), rotation=90, color=S.ACCENT,
            fontsize=9, fontweight="bold", ha="right", va="center")
    a1.axhline(6.0, color=S.ACCENT, lw=2.0, ls="--")
    a1.text(8, 6.35, S.txt("Id 최대"), color=S.ACCENT, fontsize=9,
            fontweight="bold")
    a1.plot(VDD, I_DC_A, "o", ms=10, color=S.INK, zorder=8)
    a1.annotate(S.txt(f"동작점\n{VDD:.0f} V · {I_DC_A:.2f} A"),
                xy=(VDD, I_DC_A), xytext=(26, 3.2), fontsize=9,
                color=S.INK, fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.INK, lw=0.8, alpha=0.95, pad=3),
                arrowprops=dict(arrowstyle="->", color=S.INK, lw=1.2))
    a1.set_xlim(0, 78)
    a1.set_ylim(0, 7)
    a1.set_xlabel(S.txt("드레인 전압 (V)"))
    a1.set_ylabel(S.txt("드레인 전류 (A)"))
    a1.set_title(S.txt("안전 동작 영역 — 세 개의 벽"))
    a1.legend(loc="upper right", fontsize=8.5)

    tc = np.linspace(25, TJ_MAX, 400)
    a2.plot(tc, p_max_derate(tc), lw=2.6, ls="-", color=S.COLORS[0])
    for t_case in (25.0, 85.0, 125.0):
        pm = float(p_max_derate(t_case))
        a2.plot(t_case, pm, "o", ms=8, color=S.ACCENT, zorder=7)
        a2.annotate(S.txt(f"{t_case:.0f} C -> {pm:.0f} W"),
                    xy=(t_case, pm), xytext=(t_case + 12, pm + 22),
                    fontsize=9, color=S.ACCENT, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.1))
    a2.set_xlabel(S.txt("케이스 온도 (C)"))
    a2.set_ylabel(S.txt("허용 손실 전력 (W)"))
    a2.set_xlim(20, TJ_MAX + 5)
    a2.set_ylim(0, p_max_derate(25.0) * 1.25)
    a2.set_title(S.txt(f"디레이팅 — Tj(max) {TJ_MAX:.0f} C · "
                       f"Rth(jc) {RTH_JC:.2f} C/W"))
    fig.tight_layout()
    S.save(fig, MOD, "soa_derating")
    return {t: float(p_max_derate(t)) for t in (25.0, 85.0, 125.0)}


# ══ 본문 ════════════════════════════════════════════════════════════════
def main() -> int:
    print("B08 그림 생성")
    print("=" * 62)

    ip, tp = fig1_bias()
    print(f"  [1] 바이어스           돌입 첨두 {ip:.0f} A @ {tp * 1e6:.0f} us "
          f"(정상 {I_DC_A:.2f} A 의 {ip / I_DC_A:.0f}배)")

    r_lo, r_hi = fig2_current()
    print(f"  [2] 전류 측정          쓸 수 있는 션트 창 "
          f"{r_lo * 1e3:.1f} ~ {r_hi * 1e3:.1f} mohm")

    settle, g_inf = fig3_settle()
    print(f"  [3] 안정화             ±0.05 dB 까지 {settle[0.05]:.0f} s "
          f"({settle[0.05] / 60:.1f} 분) · 최종 {g_inf:.2f} dB")

    b = fig4_pae()
    print(f"  [4] PAE                소자 {b['pae_dev']:.1f} % vs 모듈 "
          f"{b['pae_mod']:.1f} %")

    der = fig5_soa()
    print("  [5] SOA                디레이팅 = " +
          ", ".join(f"{t:.0f}C {v:.0f}W" for t, v in der.items()))

    print()
    print("본문에 쓰는 값")
    print("-" * 62)
    print(f"  돌입 첨두                     {ip:.0f} A @ {tp * 1e6:.0f} us "
          f"= 정상 전류의 {ip / I_DC_A:.0f}배")
    print(f"  커패시터에 담기는 에너지       "
          f"{0.5 * C_BULK * VDD ** 2:.2f} J")
    print(f"  벌크를 1/10 로 줄이면 첨두      "
          f"{inrush_peak_closed(c=C_BULK / 10)[0]:.0f} A")
    for r in (0.001, 0.01, 0.1):
        print(f"  션트 {r * 1e3:5.1f} mohm            부담 "
              f"{shunt_burden_v(I_DC_A, r) * 1e3:6.2f} mV · 대역 "
              f"{shunt_bw_hz(r) / 1e3:8.1f} kHz · SNR "
              f"{shunt_snr_db(I_DC_A, r):5.1f} dB")
    for tol, t in settle.items():
        print(f"  안정화 ±{tol:.2f} dB            {t:7.1f} s "
              f"({t / 60:5.1f} 분)")
    print(f"  최종 이득 변화                {g_inf:.2f} dB")
    print(f"  소자 기준 드레인 효율          {b['de_dev']:.1f} %")
    print(f"  소자 기준 PAE                 {b['pae_dev']:.1f} %")
    print(f"  모듈 기준 PAE                 {b['pae_mod']:.1f} %")
    print(f"  소자 손실 (열)                {b['p_diss_dev']:.1f} W")
    print(f"  접합 온도 (Ta 25 C)            "
          f"{float(tj(b['p_diss_dev'])):.1f} C "
          f"(사슬 합 {RTH_JC + RTH_CS + RTH_SA:.2f} C/W)")
    for t, v in der.items():
        print(f"  케이스 {t:5.0f} C 허용 손실       {v:6.1f} W")

    # ── 자체 검산 ───────────────────────────────────────────────────────
    print()
    print("[자체 검산]")
    ok = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  {'OK ' if cond else 'X  '} {msg}")

    # 돌입 (교차검증 ①)
    ts, iss = inrush_numeric(3e-3, n=300_001)
    ic = inrush_closed(ts)
    err = float(np.max(np.abs(ic - iss)) / np.max(np.abs(ic)))
    chk(err < 5e-3,
        f"돌입 닫힌 식과 시간 적분의 최대 차 {err * 100:.3f} %")
    chk(abs(float(inrush_closed(0.0))) < 1e-12,
        "t = 0 에서 전류가 0 이다 (인덕턴스가 막는다)")
    chk(ip > 100 * I_DC_A,
        f"돌입 첨두 {ip:.0f} A 가 정상 전류의 {ip / I_DC_A:.0f}배")
    e_cap = 0.5 * C_BULK * VDD ** 2
    chk(abs(e_cap - 0.5875) < 1e-3,
        f"470 uF 에 50 V 면 {e_cap:.4f} J 가 담긴다")
    ip10 = inrush_peak_closed(c=C_BULK / 10)[0]
    chk(ip10 < ip,
        f"벌크를 1/10 로 줄이면 첨두가 {ip:.0f} → {ip10:.0f} A")

    # 전류 측정
    chk(abs(shunt_burden_v(1.0, 0.01) - 0.01) < 1e-12,
        "1 A 가 10 mohm 을 지나면 10 mV")
    chk(shunt_bw_hz(0.1) > shunt_bw_hz(0.001),
        "션트가 크면 대역폭이 넓다 (같은 기생 인덕턴스에서)")
    chk(shunt_snr_db(I_DC_A, 0.1) - shunt_snr_db(I_DC_A, 0.01) > 19.9,
        "션트를 10배 키우면 SNR 이 20 dB 좋아진다")
    chk(shunt_burden_v(I_DC_A, 0.1) > 0.1,
        f"그 대신 부담 전압이 {shunt_burden_v(I_DC_A, 0.1) * 1e3:.0f} mV — "
        f"드레인 전압이 그만큼 낮아진다")

    # 안정화 (교차검증 ②)
    tn, dn = temp_rise_numeric(600.0, 60.0, n=400_001)
    dc = temp_rise(tn, 60.0)
    err2 = float(np.max(np.abs(dc - dn)) / np.max(dc))
    chk(err2 < 5e-3,
        f"열 모형 닫힌 식과 적분의 최대 차 {err2 * 100:.3f} %")
    chk(abs(temp_rise(1e6, 60.0)
            - 60.0 * (RTH_JC + RTH_CS + RTH_SA)) < 1e-6,
        f"충분히 오래 두면 P × 사슬 합 = "
        f"{60.0 * (RTH_JC + RTH_CS + RTH_SA):.1f} C")
    chk(settle[0.05] > settle[0.2],
        f"더 엄한 기준이 더 오래 걸린다 ({settle[0.2]:.0f} → "
        f"{settle[0.05]:.0f} s)")
    chk(settle[0.05] > 5 * TAU_DIE,
        "다이 시상수만 보고 기다리면 한참 모자란다 "
        f"(다이 5τ = {5 * TAU_DIE:.2f} s vs 실제 {settle[0.05]:.0f} s)")
    fast_only = -K_GAIN_DB_C * 60.0 * (RTH_JC + RTH_CS)
    chk(abs(fast_only / g_inf) < 0.45,
        f"빠른 극만으로는 최종 변화의 {abs(fast_only / g_inf) * 100:.0f} % "
        f"밖에 설명 못 한다")

    # PAE (교차검증 ③)
    lhs = b["p_dc_dev"] + b["p_in_dev"]
    rhs = b["p_out_dev"] + b["p_diss_dev"]
    chk(abs(lhs - rhs) < 1e-9,
        f"소자 에너지 수지: 들어간 {lhs:.3f} W = 나간 {rhs:.3f} W")
    lhs_m = b["p_dc_mod"] + b["p_in_w"]
    rhs_m = (P_OUT_W + b["loss_out_w"] + b["p_diss_dev"] + b["drv_dc_w"]
             + b["gate_dc_w"] + b["p_cable"] - b["loss_in_w"])
    chk(abs(lhs_m - rhs_m) < 1e-9,
        f"모듈 에너지 수지도 닫힌다 ({lhs_m:.3f} = {rhs_m:.3f} W)")
    chk(b["de_dev"] > b["pae_dev"] > b["pae_mod"],
        f"드레인 효율 {b['de_dev']:.1f} > 소자 PAE {b['pae_dev']:.1f} > "
        f"모듈 PAE {b['pae_mod']:.1f} %")
    chk(abs(b["de_dev"] - b["pae_dev"]
            - b["p_in_dev"] / b["p_dc_dev"] * 100) < 1e-9,
        "드레인 효율과 PAE 의 차이는 정확히 Pin/Pdc")
    chk(abs(pae(100.0, 0.0, 200.0) - 50.0) < 1e-12,
        "이득이 무한대면 PAE 와 드레인 효율이 같아진다")
    hi = module_budget(gain_db=25.0)
    chk(hi["de_dev"] - hi["pae_dev"] < 1.0,
        f"이득 25 dB 면 두 값의 차가 "
        f"{hi['de_dev'] - hi['pae_dev']:.2f} 포인트로 준다")

    # 열저항 사슬 (교차검증 ④)
    p = b["p_diss_dev"]
    step = T_AMB + p * RTH_SA
    step += p * RTH_CS
    step += p * RTH_JC
    chk(abs(step - float(tj(p))) < 1e-9,
        f"단계별 누적 {step:.2f} C = 사슬 합 계산 {float(tj(p)):.2f} C")
    chk(float(tj(p)) < TJ_MAX,
        f"접합 온도 {float(tj(p)):.1f} C < 최대 {TJ_MAX:.0f} C")
    chk(abs(float(p_max_derate(TJ_MAX))) < 1e-12,
        "케이스가 Tj(max) 면 허용 손실이 0")
    chk(abs(float(p_max_derate(25.0)) - (TJ_MAX - 25.0) / RTH_JC) < 1e-9,
        f"25 C 에서 허용 손실 {float(p_max_derate(25.0)):.0f} W")
    chk(der[125.0] < der[85.0] < der[25.0],
        f"케이스가 뜨거울수록 허용 손실이 준다 ({der[25.0]:.0f} → "
        f"{der[85.0]:.0f} → {der[125.0]:.0f} W)")

    print()
    if not all(ok):
        return 1
    print(f"  검산 {len(ok)}항목 전부 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
