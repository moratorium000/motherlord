#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B09 (안테나와 OTA — 챔버 안에서) 그림 생성기.

만드는 그림
  B09-1  구면 표본화 격자와 표본 간격별 TRP 오차
  B09-2  케이블이 패턴과 TRP 를 바꾼다
  B09-3  TIS 시험 시간 예산 — 왜 그렇게 오래 걸리는가
  B09-4  OTA 불확도 항목

교차검증 네 갈래
  ① 등방 패턴의 이산 적분 편향: 닫힌 식 (π/2N)·cot(π/2N) vs 실제 합
  ② 해석해가 있는 패턴의 지향성: sin²θ → 1.5, cos^q θ → 2(q+1)
  ③ **서로 다른 두 구적법**: CTIA 사각형 규칙 vs 가우스-르장드르
  ④ TIS 의 조화평균 관계: TIS = EIS_iso / mean(G) 를 이산합과 대조

실행: python3 scripts/gen_fig_b09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rf_style as S  # noqa: E402

MOD = "B09"

C0 = 299_792_458.0
F_TEST = 2.45e9
LAM = C0 / F_TEST


# ══ 패턴 ════════════════════════════════════════════════════════════════
def pat_iso(th, ph):
    """등방. 적분 규칙 자체를 검산하는 데 쓴다."""
    return np.ones_like(np.asarray(th, float) * np.asarray(ph, float))


def pat_dipole(th, ph):
    """미소 다이폴. U ∝ sin²θ, 지향성 1.5 (해석해)."""
    return np.sin(np.asarray(th, float)) ** 2 + 0 * np.asarray(ph, float)


def pat_directive(th, ph, q=20.0):
    """U ∝ cos^q θ (앞쪽 반구만). 지향성 2(q+1) (해석해)."""
    c = np.cos(np.asarray(th, float))
    return np.where(c > 0, np.maximum(c, 0.0) ** q, 0.0) + 0 * np.asarray(ph, float)


def pat_with_cable(th, ph, a=0.55, d_lam=0.85, psi=0.0):
    """단말 안테나 + 케이블. 두 개의 미소 다이폴 배열로 본다.

    원점의 안테나와, z 축으로 d 만큼 떨어진 곳의 케이블 전류를 함께 본다.
    **전류가 새어 나간 만큼 안테나 쪽이 줄도록** 진폭을 √(1-a²) 로 둔다.
    그래야 "없던 전력이 생기는" 일이 없고, TRP 변화가 두 방향으로 난다 —
    상호 결합이 방사저항을 바꾸는 실제 현상과 같은 꼴이다.
    """
    th = np.asarray(th, float)
    k = 2 * np.pi
    af = (np.sqrt(1.0 - a ** 2)
          + a * np.exp(1j * (psi + k * d_lam * np.cos(th))))
    return np.sin(th) ** 2 * np.abs(af) ** 2 + 0 * np.asarray(ph, float)


# ══ 구면 적분 ═══════════════════════════════════════════════════════════
def trp_ctia(pattern, n_th, n_ph, **kw):
    """CTIA 방식의 이산 합 (사각형 규칙).

    TRP ≈ (π / (2·N·M)) · Σ_{i=1}^{N-1} Σ_{j=0}^{M-1} U(θi, φj) · sin(θi)
    극점(θ=0, π)은 sinθ = 0 이라 어차피 기여가 없어 뺀다.
    """
    i = np.arange(1, n_th)
    th = i * np.pi / n_th
    ph = np.arange(n_ph) * 2 * np.pi / n_ph
    tg, pg = np.meshgrid(th, ph, indexing="ij")
    u = pattern(tg, pg, **kw)
    return float(np.pi / (2 * n_th * n_ph) * np.sum(u * np.sin(tg)))


def trp_gauss(pattern, n_th=200, n_ph=400, **kw):
    """같은 적분을 **가우스-르장드르 구적**으로 (교차검증 ③).

    cosθ 로 치환하면 dΩ = dφ d(cosθ) 라 가중치가 그대로 쓰인다.
    사각형 규칙과 완전히 다른 계열의 규칙이므로 서로를 검산한다.
    """
    x, w = np.polynomial.legendre.leggauss(n_th)
    th = np.arccos(x)
    ph = (np.arange(n_ph) + 0.5) * 2 * np.pi / n_ph
    tg, pg = np.meshgrid(th, ph, indexing="ij")
    u = pattern(tg, pg, **kw)
    return float(np.sum(w[:, None] * u) * (2 * np.pi / n_ph) / (4 * np.pi))


def iso_bias_closed(n_th):
    """등방 패턴에서 사각형 규칙이 만드는 편향 (닫힌 식).

    Σ_{i=1}^{N-1} sin(iπ/N) = cot(π/2N) 이므로
    TRP_이산 / TRP_참 = (π/2N)·cot(π/2N).
    """
    n = np.asarray(n_th, float)
    return np.pi / (2 * n) / np.tan(np.pi / (2 * n))


def directivity(pattern, **kw):
    """최대 / 평균. 이산 적분으로 구한다."""
    th = np.linspace(1e-6, np.pi - 1e-6, 721)
    ph = np.linspace(0, 2 * np.pi, 361)
    tg, pg = np.meshgrid(th, ph, indexing="ij")
    u = pattern(tg, pg, **kw)
    return float(np.max(u) / trp_gauss(pattern, **kw))


# ══ TIS ═════════════════════════════════════════════════════════════════
def tis_from_gain(pattern, n_th, n_ph, eis_iso_dbm=-100.0, **kw):
    """TIS = 4π / ∮(1/EIS) dΩ.

    EIS(θ,φ) = EIS_iso / G(θ,φ) 이므로 1/EIS ∝ G 이고,
    결과는 **이득의 조화평균이 아니라 산술평균**으로 나온다 — 그래서
    TIS 는 TRP 와 같은 꼴의 적분이 된다.
    """
    i = np.arange(1, n_th)
    th = i * np.pi / n_th
    ph = np.arange(n_ph) * 2 * np.pi / n_ph
    tg, pg = np.meshgrid(th, ph, indexing="ij")
    g = pattern(tg, pg, **kw)
    eis_lin = 10 ** (eis_iso_dbm / 10.0) / np.maximum(g, 1e-12)
    s = np.pi / (2 * n_th * n_ph) * np.sum(np.sin(tg) / eis_lin)
    return 10 * np.log10(1.0 / s)


# ══ 시험 시간 ═══════════════════════════════════════════════════════════
def n_points(step_deg):
    """θ 를 1..N-1, φ 를 0..M-1 로 훑을 때의 점 개수 (극 제외)."""
    n_th = int(round(180.0 / step_deg))
    n_ph = int(round(360.0 / step_deg))
    return (n_th - 1) * n_ph, n_th, n_ph


def trp_time_s(step_deg, t_point=0.05, t_move=0.60, n_pol=2, n_ch=3):
    """TRP 시험 시간. 점마다 전력을 한 번 읽으면 된다."""
    npt = n_points(step_deg)[0]
    return npt * n_pol * n_ch * (t_point + t_move)


def tis_time_s(step_deg, n_bisect=10, n_pkt=400, t_pkt=5e-3, t_move=0.60,
               n_pol=2, n_ch=3):
    """TIS 시험 시간. 점마다 **감도 탐색**을 해야 한다.

    한 점의 EIS 를 찾으려면 전력을 이분 탐색하며 매번 오류율을 재야 하고,
    오류율 하나를 재려면 패킷을 충분히 보내야 한다.
    """
    npt = n_points(step_deg)[0]
    t_search = n_bisect * n_pkt * t_pkt
    return npt * n_pol * n_ch * (t_search + t_move)


# ══ 불확도 ══════════════════════════════════════════════════════════════
OTA_UNC = {
    "기준 안테나 이득 교정": (0.45, "B"),
    "경로 손실 교정": (0.30, "B"),
    "챔버 반사 (정재파)": (0.35, "B"),
    "위치 정렬 오차": (0.20, "B"),
    "표본 간격 (30 deg)": (0.10, "B"),
    "측정기 전력 확도": (0.25, "B"),
    "케이블·지그 영향": (0.40, "B"),
    "반복성 (A 형)": (0.22, "A"),
}


def ota_budget(unc=None):
    unc = unc or OTA_UNC
    tot = np.sqrt(sum(v[0] ** 2 for v in unc.values()))
    return tot, {k: v[0] for k, v in unc.items()}


# ══ 그림 ════════════════════════════════════════════════════════════════
def fig1_sampling():
    fig, (a1, a2) = S.figure(w=11.4, h=4.8, ncols=2)

    # (A) 격자 — 30° 와 15° 를 정사영으로
    for step, col, mk, ms in ((30.0, S.COLORS[1], "o", 7),
                              (15.0, S.COLORS[0], ".", 5)):
        _, n_th, n_ph = n_points(step)
        th = np.arange(1, n_th) * np.pi / n_th
        ph = np.arange(n_ph) * 2 * np.pi / n_ph
        tg, pg = np.meshgrid(th, ph, indexing="ij")
        x = np.sin(tg) * np.cos(pg)
        y = np.cos(tg)
        a1.plot(x.ravel(), y.ravel(), mk, ms=ms, ls="none", color=col,
                mfc="none" if mk == "o" else col, mew=1.4,
                label=S.txt(f"{step:.0f} deg 간격 · "
                            f"{n_points(step)[0]} 점"))
    thc = np.linspace(0, 2 * np.pi, 361)
    a1.plot(np.cos(thc), np.sin(thc), color=S.INK, lw=1.4, ls="-")
    a1.set_aspect("equal")
    a1.set_xticks([]); a1.set_yticks([])
    a1.grid(False)
    for s in a1.spines.values():
        s.set_visible(False)
    a1.set_xlim(-1.25, 1.25); a1.set_ylim(-1.25, 1.35)
    a1.set_title(S.txt("구면 표본화 격자 (정사영)"))
    a1.legend(loc="upper center", fontsize=8.5, ncol=2, framealpha=0.9)

    # (B) 표본 간격별 오차
    steps = np.array([45.0, 30.0, 22.5, 15.0, 10.0, 7.5, 5.0, 3.0])
    cases = (("등방", pat_iso, {}), ("미소 다이폴", pat_dipole, {}),
             ("지향성 16 dBi", pat_directive, {"q": 20.0}),
             ("케이블 붙은 단말", pat_with_cable, {}))
    out = {}
    for (name, fn, kw), col, ls in zip(cases, (S.COLORS[2], S.COLORS[0],
                                               S.COLORS[1], S.COLORS[4]),
                                       ("-", "--", "-.", ":")):
        ref = trp_gauss(fn, n_th=400, n_ph=800, **kw)
        errs = []
        for st in steps:
            _, n_th, n_ph = n_points(st)
            errs.append(10 * np.log10(trp_ctia(fn, n_th, n_ph, **kw) / ref))
        a2.semilogx(steps, errs, lw=2.2, ls=ls, color=col, marker="o", ms=5,
                    label=S.txt(name))
        out[name] = dict(zip(steps, errs))
    S.limit_line(a2, -0.25, S.txt("허용 0.25 dB"), side="lower")
    a2.axhline(0, color=S.MUTED, lw=1.0, ls=":")
    a2.set_xticks([45, 30, 15, 10, 5, 3])
    a2.set_xticklabels(["45", "30", "15", "10", "5", "3"])
    a2.xaxis.set_minor_formatter(lambda *_: "")
    a2.set_xlabel(S.txt("표본 간격 (deg)"))
    a2.set_ylabel(S.txt("TRP 오차 (dB)"))
    a2.set_ylim(-6.5, 2.2)
    a2.invert_xaxis()
    a2.set_title(S.txt("패턴이 뾰족할수록 촘촘히 떠야 한다"))
    a2.legend(loc="lower left", fontsize=8.5)
    fig.tight_layout()
    S.save(fig, MOD, "sampling_grid")
    return steps, out


def fig2_cable():
    fig, (a1, a2) = S.figure(w=11.4, h=4.8, ncols=2,
                             subplot_kw=None)
    th = np.linspace(0, np.pi, 721)
    ref = trp_gauss(pat_dipole)
    def db(u):                                   # 극점의 log10(0) 회피
        return 10 * np.log10(np.maximum(u / ref, 1e-6))
    a1.plot(np.degrees(th), db(pat_dipole(th, 0.0)),
            lw=2.4, ls="-", color=S.COLORS[0], label=S.txt("케이블 없음"))
    res = {}
    for d, col, ls in ((0.35, S.COLORS[2], "--"), (0.85, S.COLORS[1], "-."),
                       (1.60, S.COLORS[4], ":")):
        r2 = trp_gauss(pat_with_cable, d_lam=d)
        a1.plot(np.degrees(th),
                db(pat_with_cable(th, 0.0, d_lam=d)),
                lw=1.9, ls=ls, color=col,
                label=S.txt(f"케이블 {d:.2f} lambda · TRP "
                            f"{10 * np.log10(r2 / ref):+.2f} dB"))
        res[d] = 10 * np.log10(r2 / ref)
    a1.set_xlabel(S.txt("theta (deg)"))
    a1.set_ylabel(S.txt("상대 이득 (dBi)"))
    a1.set_xlim(0, 180)
    a1.set_ylim(-22, 10)
    a1.set_xticks([0, 45, 90, 135, 180])
    a1.set_title(S.txt("같은 안테나, 케이블 위치만 바꿨다"))
    a1.legend(loc="lower center", fontsize=8)

    ds = np.linspace(0.1, 2.0, 200)
    dtrp = np.array([10 * np.log10(trp_gauss(pat_with_cable, d_lam=float(d))
                                   / ref) for d in ds])
    a2.plot(ds, dtrp, lw=2.4, ls="-", color=S.COLORS[0])
    imax, imin = int(np.argmax(dtrp)), int(np.argmin(dtrp))
    for i, lab in ((imax, "최대"), (imin, "최소")):
        a2.plot(ds[i], dtrp[i], "o", ms=8, color=S.ACCENT, zorder=7)
    a2.annotate(S.txt(f"같은 물건인데 케이블 위치로\n"
                      f"{dtrp[imax] - dtrp[imin]:.2f} dB 가 움직인다"),
                xy=(ds[imin], dtrp[imin]), xytext=(1.15, dtrp[imax] - 0.15),
                fontsize=9, color=S.ACCENT, fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.ACCENT, lw=0.8, alpha=0.95, pad=3),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    a2.axhline(0, color=S.MUTED, lw=1.0, ls=":")
    a2.set_xlabel(S.txt("케이블 전류 중심까지의 거리 (파장)"))
    a2.set_ylabel(S.txt("TRP 변화 (dB)"))
    a2.set_title(S.txt("TRP 도 함께 움직인다"))
    fig.tight_layout()
    S.save(fig, MOD, "cable_effect")
    return res, float(dtrp[imax] - dtrp[imin])


def fig3_time():
    fig, (a1, a2) = S.figure(w=11.4, h=4.6, ncols=2)
    steps = (45.0, 30.0, 22.5, 15.0, 10.0)
    x = np.arange(len(steps))
    trp_t = [trp_time_s(s) / 60 for s in steps]
    tis_t = [tis_time_s(s) / 60 for s in steps]
    a1.bar(x - 0.19, trp_t, 0.36, color=S.COLORS[0], label=S.txt("TRP"))
    a1.bar(x + 0.19, tis_t, 0.36, color=S.COLORS[1], label=S.txt("TIS"))
    for i, (a, b) in enumerate(zip(trp_t, tis_t)):
        a1.text(x[i] - 0.19, a * 1.15, f"{a:.0f}", ha="center", fontsize=8.5)
        a1.text(x[i] + 0.19, b * 1.15, f"{b:.0f}", ha="center", fontsize=8.5)
    a1.set_yscale("log")
    a1.set_xticks(x)
    a1.set_xticklabels([f"{s:g}" for s in steps])
    a1.set_xlabel(S.txt("표본 간격 (deg)"))
    a1.set_ylabel(S.txt("시험 시간 (분) · 3 채널 · 2 편파"))
    S.plain_log(a1, axis="y")
    a1.set_ylim(1, 6000)
    a1.set_title(S.txt("같은 격자면 TIS 가 30배 넘게 걸린다"))
    a1.legend(loc="upper left", fontsize=9)

    # TIS 한 점의 시간이 무엇으로 이뤄지는가
    n_bis, n_pkt, t_pkt, t_move = 10, 400, 5e-3, 0.60
    parts = {"이분 탐색 10단계 x 패킷 400개": n_bis * n_pkt * t_pkt,
             "위치기 이동": t_move}
    labels = list(parts)
    vals = [parts[k] for k in labels]
    a2.barh([0, 1], vals, 0.5, color=[S.COLORS[1], S.MUTED])
    for i, v in enumerate(vals):
        a2.text(v + 0.15, i, f"{v:.2f} s", va="center", fontsize=9,
                fontweight="bold")
    a2.set_yticks([0, 1])
    a2.set_yticklabels([S.txt(k) for k in labels], fontsize=9)
    a2.set_xlabel(S.txt("한 점 · 한 편파 · 한 채널에 드는 시간 (s)"))
    a2.set_xlim(0, max(vals) * 1.42)
    npt30 = n_points(30.0)[0]
    a2.set_title(S.txt(f"30 deg 격자면 이것이 {npt30} x 2 x 3 = "
                       f"{npt30 * 6} 번"))
    fig.tight_layout()
    S.save(fig, MOD, "tis_time")
    return {s: (trp_time_s(s) / 60, tis_time_s(s) / 60) for s in steps}


def fig4_uncertainty():
    tot, items = ota_budget()
    fig, ax = S.figure(w=8.8, h=4.6)
    keys = sorted(items, key=lambda k: items[k], reverse=True)
    vals = [items[k] for k in keys]
    cols = [S.ACCENT if v >= 0.35 else S.COLORS[0] for v in vals]
    ax.barh(range(len(keys)), vals, 0.6, color=cols)
    for i, v in enumerate(vals):
        ax.text(v + 0.012, i, f"{v:.2f}", va="center", fontsize=9,
                fontweight="bold")
    ax.set_yticks(range(len(keys)))
    ax.set_yticklabels([S.txt(k) for k in keys], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel(S.txt("표준 불확도 기여 (dB)"))
    ax.set_xlim(0, tot * 1.22)
    ax.axvline(tot, color=S.INK, lw=1.8, ls="--")
    ax.annotate(S.txt(f"합성 {tot:.2f} dB\n(k=2 면 ±{2 * tot:.2f} dB)"),
                xy=(tot, len(keys) - 1.6), xytext=(tot * 0.72, len(keys) - 3.0),
                fontsize=9.5, color=S.INK, fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.INK, lw=0.8, alpha=0.95, pad=3),
                arrowprops=dict(arrowstyle="->", color=S.INK, lw=1.2))
    ax.set_title(S.txt("OTA 불확도 — 챔버가 아니라 교정이 지배한다"))
    fig.tight_layout()
    S.save(fig, MOD, "ota_uncertainty")
    return tot, items


# ══ 본문 ════════════════════════════════════════════════════════════════
def main() -> int:
    print("B09 그림 생성")
    print("=" * 62)

    steps, errs = fig1_sampling()
    print(f"  [1] 표본화             30 deg 오차: 등방 "
          f"{errs['등방'][30.0]:+.3f} dB · 지향성 "
          f"{errs['지향성 16 dBi'][30.0]:+.3f} dB")

    cable, spread = fig2_cable()
    print(f"  [2] 케이블             위치만 바꿔 TRP 가 {spread:.2f} dB 움직인다")

    times = fig3_time()
    print(f"  [3] 시험 시간          30 deg: TRP {times[30.0][0]:.1f} 분 vs "
          f"TIS {times[30.0][1]:.0f} 분")

    tot, items = fig4_uncertainty()
    print(f"  [4] 불확도             합성 {tot:.2f} dB (k=2 → ±{2 * tot:.2f})")

    print()
    print("본문에 쓰는 값")
    print("-" * 62)
    for st in (45.0, 30.0, 15.0, 10.0):
        npt, n_th, n_ph = n_points(st)
        print(f"  {st:5.1f} deg 격자   점 {npt:5d} 개 "
              f"(theta {n_th - 1} x phi {n_ph})")
    for name in errs:
        print(f"  TRP 오차 {name:16s} 45 deg {errs[name][45.0]:+.3f} · "
              f"30 deg {errs[name][30.0]:+.3f} · 15 deg {errs[name][15.0]:+.3f} dB")
    print(f"  등방 편향 닫힌 식 (30 deg)    "
          f"{10 * np.log10(iso_bias_closed(6)):+.4f} dB")
    print(f"  등방 편향 닫힌 식 (15 deg)    "
          f"{10 * np.log10(iso_bias_closed(12)):+.4f} dB")
    print(f"  미소 다이폴 지향성            {directivity(pat_dipole):.4f} "
          f"(해석해 1.5)")
    print(f"  cos^20 지향성                 "
          f"{directivity(pat_directive, q=20.0):.3f} (해석해 42)")
    for d, v in cable.items():
        print(f"  케이블 {d:.2f} lambda           TRP {v:+.2f} dB")
    print(f"  케이블 위치가 만드는 TRP 폭   {spread:.2f} dB")
    for st, (a, b) in times.items():
        print(f"  {st:5.1f} deg   TRP {a:6.1f} 분 · TIS {b:7.1f} 분 "
              f"({b / 60:.1f} 시간)")
    print(f"  TIS / TRP 시간 비 (30 deg)     "
          f"{times[30.0][1] / times[30.0][0]:.0f} 배")
    print(f"  불확도 합성                   {tot:.3f} dB · 확장(k=2) "
          f"±{2 * tot:.2f} dB")

    # ── 자체 검산 ───────────────────────────────────────────────────────
    print()
    print("[자체 검산]")
    ok = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  {'OK ' if cond else 'X  '} {msg}")

    # 등방 편향 (교차검증 ①)
    for st in (45.0, 30.0, 15.0, 5.0):
        _, n_th, n_ph = n_points(st)
        num = trp_ctia(pat_iso, n_th, n_ph)
        cf = float(iso_bias_closed(n_th))
        chk(abs(num - cf) < 1e-12,
            f"{st:4.1f} deg 등방: 이산합 {num:.9f} = 닫힌 식 "
            f"(pi/2N)cot(pi/2N) {cf:.9f}")
    chk(iso_bias_closed(6) < iso_bias_closed(12) < iso_bias_closed(60) < 1.0,
        "격자를 촘촘히 할수록 편향이 1 에 다가간다 (아래에서)")

    # 해석해가 있는 지향성 (교차검증 ②)
    chk(abs(directivity(pat_dipole) - 1.5) < 2e-3,
        f"미소 다이폴 지향성 {directivity(pat_dipole):.5f} (해석해 1.5)")
    for q in (2.0, 8.0, 20.0):
        d = directivity(pat_directive, q=q)
        chk(abs(d / (2 * (q + 1)) - 1) < 5e-3,
            f"cos^{q:.0f} 지향성 {d:.3f} (해석해 {2 * (q + 1):.0f})")

    # 두 구적법 대조 (교차검증 ③)
    for name, fn, kw in (("등방", pat_iso, {}), ("다이폴", pat_dipole, {}),
                         ("지향성", pat_directive, {"q": 20.0}),
                         ("케이블", pat_with_cable, {})):
        g = trp_gauss(fn, n_th=400, n_ph=800, **kw)
        r = trp_ctia(fn, 720, 1440, **kw)
        chk(abs(10 * np.log10(r / g)) < 5e-4,
            f"{name}: 가우스-르장드르 {g:.6f} vs 촘촘한 사각형 규칙 "
            f"{r:.6f} (차 {10 * np.log10(r / g):+.5f} dB)")

    # 표본 간격
    chk(errs["등방"][30.0] > -0.15,
        f"등방은 30 deg 로도 {errs['등방'][30.0]:+.3f} dB 밖에 안 틀린다")
    chk(errs["지향성 16 dBi"][30.0] < -0.25,
        f"지향성 안테나는 30 deg 에서 {errs['지향성 16 dBi'][30.0]:+.3f} dB — "
        f"허용치를 넘는다")
    chk(abs(errs["지향성 16 dBi"][10.0]) < abs(errs["지향성 16 dBi"][30.0]),
        "촘촘히 뜨면 좋아진다")

    # 케이블 (교차검증: 케이블 없는 극한)
    chk(abs(10 * np.log10(trp_gauss(pat_with_cable, a=0.0) / trp_gauss(pat_dipole)))
        < 1e-12,
        "케이블 전류를 0 으로 하면 원래 다이폴로 정확히 돌아온다")
    chk(spread > 1.0,
        f"케이블 위치만으로 TRP 가 {spread:.2f} dB 움직인다")
    chk(max(cable.values()) > 0 > min(cable.values()),
        f"위치에 따라 늘기도 하고 줄기도 한다 "
        f"({min(cable.values()):+.2f} ~ {max(cable.values()):+.2f} dB)")

    # TIS (교차검증 ④)
    for pat, kw in ((pat_iso, {}), (pat_dipole, {}),
                    (pat_directive, {"q": 8.0})):
        t = tis_from_gain(pat, 720, 1440, **kw)
        mean_g = trp_ctia(pat, 720, 1440, **kw)
        chk(abs(t - (-100.0 - 10 * np.log10(mean_g))) < 1e-9,
            f"TIS {t:.4f} dBm = EIS_iso - 10log10(평균 이득) "
            f"{-100.0 - 10 * np.log10(mean_g):.4f}")
    tis_d = tis_from_gain(pat_directive, 720, 1440, q=20.0)
    tis_i = tis_from_gain(pat_iso, 720, 1440)
    chk(tis_d > tis_i + 10,
        f"최대 이득이 같아도 지향성 안테나의 TIS 가 {tis_d - tis_i:.1f} dB "
        f"나쁘다 — TIS 는 **평균**이 정한다")

    # 시험 시간
    npt30 = n_points(30.0)[0]
    chk(npt30 == 60, f"30 deg 격자의 점 개수 {npt30} (theta 5 x phi 12)")
    chk(n_points(15.0)[0] == 264,
        f"15 deg 격자의 점 개수 {n_points(15.0)[0]} (theta 11 x phi 24)")
    chk(times[30.0][1] / times[30.0][0] > 25,
        f"TIS 가 TRP 보다 {times[30.0][1] / times[30.0][0]:.0f} 배 오래 걸린다")
    chk(abs(tis_time_s(30.0) / tis_time_s(15.0)
            - n_points(30.0)[0] / n_points(15.0)[0]) < 1e-9,
        "시간은 점 개수에 정비례한다")

    # 불확도
    chk(abs(tot - np.sqrt(sum(v ** 2 for v in items.values()))) < 1e-12,
        f"RSS 합성 {tot:.4f} dB")
    chk(max(items, key=items.get) == "기준 안테나 이득 교정",
        f"가장 큰 항이 '{max(items, key=items.get)}' "
        f"({max(items.values()):.2f} dB)")
    chk(items["표본 간격 (30 deg)"] < items["챔버 반사 (정재파)"],
        "표본 간격보다 챔버 반사가 크다 — 격자만 촘촘히 해도 소용없다")

    print()
    if not all(ok):
        return 1
    print(f"  검산 {len(ok)}항목 전부 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
