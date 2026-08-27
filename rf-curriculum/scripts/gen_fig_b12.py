#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B12 (양산 이관 — 벤치에서 시험기로) 그림 생성기.

만드는 그림
  B12-1  시험 시간 예산 — 초가 곧 돈이다
  B12-2  항목 상관 행렬 — 무엇을 빼도 되는가
  B12-3  벤치-ATE 상관과 가드밴드 — 한계를 얼마나 당길 것인가
  B12-4  수율 파레토와 재시험 정책 — 붙을 때까지 다시 재면 생기는 일

교차검증 네 갈래
  ① 처리량: 닫힌 식 UPH vs 핸들러 이산사건 시뮬레이션
  ② 항목 상관: 생성에 쓴 상관 행렬 vs 표본에서 추정한 행렬,
     빠뜨림(escape)은 몬테카를로 두 벌(전체 항목 / 줄인 항목)로 직접 셈
  ③ 가드밴드: 정규분포 닫힌 식 vs 몬테카를로
  ④ 재시험: 1-(1-p)^(1+R) 닫힌 식의 수치적분 vs 재시험 정책 시뮬레이션

실행: python3 scripts/gen_fig_b12.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rf_style as S  # noqa: E402

MOD = "B12"

# ── 시험 항목 (2.4 GHz 트랜시버 모듈. 캡스톤 보드를 양산으로 넘긴다) ────
# (이름, ATE 초, 벤치 초)
ITEMS = [
    ("정지 전류", 0.3, 20),
    ("주파수 오차", 0.8, 60),
    ("송신 출력", 1.2, 90),
    ("송신 EVM", 2.5, 240),
    ("스펙트럼 마스크", 3.5, 300),
    ("하모닉", 2.0, 420),
    ("수신 감도", 4.0, 600),
    ("수신 선택도", 3.0, 480),
    ("이득 평탄도", 1.5, 180),
    ("잡음지수", 2.2, 360),
]

T_INDEX_S = 0.8               # 핸들러가 물건을 바꿔 무는 시간
RATE_WON_H = 120_000          # 시험기 시간당 비용 (감가·인건·설비)
VOLUME_YEAR = 2_000_000       # 연간 생산량

# 병렬 시험이라도 계측기를 나눠 쓰는 항목이 있어 완전 병렬은 안 된다.
SERIAL_FRAC = {"계측기 전용 (이상적)": 0.0, "계측기 공유 20 %": 0.2}


# ══ 처리량 ══════════════════════════════════════════════════════════════
def test_time_s(items=None):
    return sum(t for _, t, _ in (items or ITEMS))


def uph_closed(t_test, n_site, serial_frac, t_index=T_INDEX_S):
    """시간당 처리량 (units per hour, UPH) 닫힌 식.

    n_site 개를 한 번에 물리지만, 계측기를 공유하는 몫(serial_frac)만큼은
    사이트를 차례로 돌아야 한다. 그래서 한 묶음에 걸리는 시간은
    t*(serial_frac*n + (1-serial_frac)) + 인덱스 시간이다.
    """
    cycle = t_test * (serial_frac * n_site + (1 - serial_frac)) + t_index
    return 3600.0 * n_site / cycle


def uph_sim(t_test, n_site, serial_frac, t_index=T_INDEX_S, hours=2.0):
    """같은 것을 핸들러 이산사건 시뮬레이션으로 (교차검증 ①).

    시계를 0 부터 굴리며 '물기 -> 시험 -> 놓기' 를 반복해 실제로 몇 개가
    나오는지 센다. 닫힌 식이 맞는지 확인하는 것이 목적이므로 고장·재시험
    같은 것은 넣지 않는다.
    """
    t, done, end = 0.0, 0, hours * 3600.0
    while True:
        t += t_index
        t += t_test * (serial_frac * n_site + (1 - serial_frac))
        if t > end:
            break
        done += n_site
    return done / hours


def cost_per_unit(uph, rate=RATE_WON_H):
    return rate / uph


# ══ 항목 상관 ═══════════════════════════════════════════════════════════
# 항목 사이의 상관은 공통 원인에서 온다. 이득이 낮은 개체는 출력도 낮고
# 평탄도도 나쁘다 — 같은 트랜지스터가 만든 결과이기 때문이다.
# 요인 적재 행렬로 상관을 만들면 양의 정부호가 저절로 보장된다.
FACTORS = {
    #                       [증폭단 세기, 국부발진 품질, 필터 정합]
    "정지 전류":        (0.55, 0.05, 0.00),
    "주파수 오차":      (0.00, 0.88, 0.05),
    "송신 출력":        (0.92, 0.05, 0.10),
    "송신 EVM":         (0.30, 0.80, 0.15),
    "스펙트럼 마스크":  (0.25, 0.35, 0.82),
    "하모닉":           (0.45, 0.05, 0.72),
    # 감도와 잡음지수는 물리적으로 거의 같은 말이다 —
    # 감도 = kTB + NF + 필요 SNR. 그래서 상관이 0.98 까지 올라간다.
    "수신 감도":        (0.985, 0.10, 0.08),
    "수신 선택도":      (0.15, 0.20, 0.88),
    "이득 평탄도":      (0.88, 0.10, 0.20),
    "잡음지수":         (0.975, 0.12, 0.10),
}


def corr_true():
    """요인 적재로 만든 참 상관 행렬."""
    lam = np.array(list(FACTORS.values()))
    cov = lam @ lam.T
    d = np.sqrt(1.0 - np.clip(np.sum(lam ** 2, axis=1), 0, 0.999))
    cov = cov + np.diag(d ** 2)
    s = np.sqrt(np.diag(cov))
    return cov / np.outer(s, s)


def draw_units(n, rng=None):
    """상관을 가진 표준화 측정값 n 개를 뽑는다. 값이 클수록 나쁘다."""
    rng = rng or np.random.default_rng(17)
    lam = np.array(list(FACTORS.values()))
    d = np.sqrt(1.0 - np.clip(np.sum(lam ** 2, axis=1), 0, 0.999))
    f = rng.normal(0.0, 1.0, (n, lam.shape[1]))
    e = rng.normal(0.0, 1.0, (n, len(FACTORS))) * d
    z = f @ lam.T + e
    return z / z.std(axis=0, keepdims=True)


# 한 항목만 봤을 때 약 0.3 % 가 떨어지도록 한계를 둔다 (양쪽 합쳐서).
LIMIT_SIGMA = 2.97

# 항목을 빼도 좋다고 볼 선. 출하 감사(outgoing audit)가 잡아 줄 수 있는
# 수준으로 잡았다. 이 값은 회사의 품질 목표가 정하는 것이지 계산으로
# 나오는 것이 아니다.
DROP_TARGET_PPM = 500.0


def escape_if_dropped(z, drop_idx, limit=LIMIT_SIGMA):
    """그 항목을 빼면 몇 ppm 이 걸러지지 않고 나가는가.

    빠뜨림 = (뺀 항목은 떨어졌어야 하는데) and (남긴 항목은 전부 통과).
    """
    bad = np.abs(z[:, drop_idx]) > limit
    keep = [j for j in range(z.shape[1]) if j != drop_idx]
    pass_rest = np.all(np.abs(z[:, keep]) <= limit, axis=1)
    return float(np.mean(bad & pass_rest)) * 1e6


# ══ 벤치-ATE 상관과 가드밴드 ════════════════════════════════════════════
def bench_ate(n=60, sd_unit=0.45, sd_bench=0.06, sd_ate=0.16,
              offset=0.09, rng=None):
    """같은 물건을 벤치와 ATE 로 잰다. ATE 는 픽스처 때문에 더 흔들린다."""
    rng = rng or np.random.default_rng(31)
    x = rng.normal(0.0, sd_unit, n)
    return (x + rng.normal(0.0, sd_bench, n),
            x + offset + rng.normal(0.0, sd_ate, n))


def guard_closed(sd_unit, sd_diff, limit, guard, n=200_001, span=8.0):
    """가드밴드를 g 만큼 당겼을 때의 빠뜨림·헛수고를 닫힌 식으로.

    참값 X ~ N(0, sd_unit) 이고 ATE 가 읽는 값은 X + D, D ~ N(0, sd_diff).
    ATE 판정선은 limit - guard. 벤치(=참값에 가까운 쪽) 기준으로 채점한다.
    """
    x = np.linspace(-span * sd_unit, span * sd_unit, n)
    fx = stats.norm.pdf(x, 0.0, sd_unit)
    lim = limit - guard
    p_in = (stats.norm.cdf((lim - x) / sd_diff)
            - stats.norm.cdf((-lim - x) / sd_diff))
    good = np.abs(x) <= limit
    escape = np.trapezoid(fx * (~good) * p_in, x)
    overkill = np.trapezoid(fx * good * (1.0 - p_in), x)
    return float(escape), float(overkill)


def guard_mc(sd_unit, sd_diff, limit, guard, n=4_000_000, rng=None):
    """같은 것을 몬테카를로로 (교차검증 ③)."""
    rng = rng or np.random.default_rng(77)
    x = rng.normal(0.0, sd_unit, n)
    m = x + rng.normal(0.0, sd_diff, n)
    good, pas = np.abs(x) <= limit, np.abs(m) <= limit - guard
    return float(np.mean(~good & pas)), float(np.mean(good & ~pas))


# ══ 수율 파레토와 재시험 ════════════════════════════════════════════════
# 실제 라인에서 나오는 모양 — 몇 개 항목이 불량의 대부분을 차지한다.
BINS = {
    "수신 감도": 4120,
    "송신 EVM": 2340,
    "스펙트럼 마스크": 1180,
    "정지 전류": 640,
    "하모닉": 410,
    "주파수 오차": 220,
    "이득 평탄도": 150,
    "그 밖": 90,
}


def retest_escape_closed(sd_unit, sd_meas, limit, n_retry,
                         n=200_001, span=8.0):
    """'떨어지면 다시 재고, 한 번이라도 붙으면 통과' 정책의 빠뜨림.

    참으로 불합격인 개체(|x| > limit)가 1+n_retry 번 중 한 번이라도
    한계 안에 들어올 확률은 1 - (1-p(x))^(1+n_retry) 이다.
    """
    x = np.linspace(-span * sd_unit, span * sd_unit, n)
    for edge in (-limit, limit):
        x = np.append(x, np.linspace(edge - 10 * sd_meas,
                                     edge + 10 * sd_meas, 4001))
    x = np.unique(x)
    fx = stats.norm.pdf(x, 0.0, sd_unit)
    p = (stats.norm.cdf((limit - x) / sd_meas)
         - stats.norm.cdf((-limit - x) / sd_meas))
    bad = np.abs(x) > limit
    p_any = 1.0 - (1.0 - p) ** (1 + n_retry)
    return float(np.trapezoid(fx * bad * p_any, x))


def retest_escape_mc(sd_unit, sd_meas, limit, n_retry, n=3_000_000, rng=None):
    """같은 것을 정책 시뮬레이션으로 (교차검증 ④)."""
    rng = rng or np.random.default_rng(91)
    x = rng.normal(0.0, sd_unit, n)
    shipped = np.zeros(n, dtype=bool)
    left = np.ones(n, dtype=bool)
    for _ in range(1 + n_retry):
        m = x[left] + rng.normal(0.0, sd_meas, int(left.sum()))
        ok = np.abs(m) <= limit
        idx = np.flatnonzero(left)
        shipped[idx[ok]] = True
        left[idx[ok]] = False
    return float(np.mean(shipped & (np.abs(x) > limit)))


def retest_escape_median(sd_unit, sd_meas, limit, n_rep,
                         n=3_000_000, rng=None):
    """대안 정책: n_rep 번 재서 **중앙값**으로 판정한다."""
    rng = rng or np.random.default_rng(93)
    x = rng.normal(0.0, sd_unit, n)
    m = x[:, None] + rng.normal(0.0, sd_meas, (n, n_rep))
    med = np.median(m, axis=1)
    return float(np.mean((np.abs(med) <= limit) & (np.abs(x) > limit)))


# ══ 그림 1 · 시험 시간 예산 ═════════════════════════════════════════════
def fig1_time():
    fig, (ax1, ax2) = S.figure(12.6, 4.8, ncols=2,
                               gridspec_kw=dict(width_ratios=[1.1, 1]))

    names = [n for n, _, _ in ITEMS]
    ate = np.array([t for _, t, _ in ITEMS])
    bench = np.array([t for _, _, t in ITEMS])
    order = np.argsort(ate)
    y = np.arange(len(ITEMS))

    ax1.barh(y, ate[order], color=S.COLORS[0], height=0.62)
    def bench_str(s):
        return f"{s / 60:.0f} 분" if s >= 60 else f"{s:.0f} 초"

    for i, k in enumerate(order):
        ax1.text(ate[k] + 0.12, i, f"{ate[k]:.1f} s  "
                 f"(벤치 {bench_str(bench[k])})", va="center", fontsize=9)
    ax1.set_yticks(y)
    ax1.set_yticklabels([names[k] for k in order], fontsize=9)
    ax1.set_xlabel("ATE 시험 시간 (초)")
    ax1.set_xlim(0, max(ate) * 1.85)
    t_all = test_time_s()
    ax1.set_title(f"(a) 항목별 시간 — 합계 {t_all:.1f} 초 "
                  f"(벤치로는 {bench.sum() / 60:.0f} 분)")

    # (b) 사이트 수와 처리량
    sites = np.arange(1, 9)
    for (lab, sf), c, ls in zip(SERIAL_FRAC.items(),
                                [S.COLORS[2], S.COLORS[1]], ["-", "--"]):
        u = [uph_closed(t_all, s, sf) for s in sites]
        ax2.plot(sites, u, color=c, ls=ls, lw=2.4, label=f"닫힌 식 · {lab}")
        sim = [uph_sim(t_all, s, sf) for s in sites]
        ax2.plot(sites, sim, "o", ms=6, color=c, ls="none", mfc="white",
                 mew=1.8)
    ax2.plot([], [], "o", ms=6, color=S.MUTED, ls="none", mfc="white",
             mew=1.8, label="핸들러 시뮬레이션")

    u4 = uph_closed(t_all, 4, SERIAL_FRAC["계측기 공유 20 %"])
    u1 = uph_closed(t_all, 1, 0.0)
    ax2.annotate(f"4 사이트 · 공유 20 %\n{u4:.0f} UPH · "
                 f"개당 {cost_per_unit(u4):,.0f} 원",
                 xy=(4, u4), xytext=(4.4, u4 * 0.45), fontsize=9,
                 color=S.INK, linespacing=1.4,
                 arrowprops=dict(arrowstyle="->", color=S.INK, lw=1.2))
    ax2.annotate(f"1 사이트\n{u1:.0f} UPH · "
                 f"개당 {cost_per_unit(u1):,.0f} 원",
                 xy=(1, u1), xytext=(1.3, u1 * 3.2), fontsize=9,
                 color=S.INK, linespacing=1.4,
                 arrowprops=dict(arrowstyle="->", color=S.INK, lw=1.2))
    ax2.set_xlabel("병렬 시험 사이트 수")
    ax2.set_ylabel("시간당 처리량 (UPH)")
    ax2.set_title("(b) 사이트를 늘려도 계측기를 나눠 쓰면 안 는다")
    ax2.legend(loc="upper left", fontsize=9)

    S.save(fig, MOD, "test_time")
    return t_all, u1, u4


# ══ 그림 2 · 항목 상관 ══════════════════════════════════════════════════
def fig2_corr():
    names = list(FACTORS)
    z = draw_units(500_000, rng=np.random.default_rng(1234))
    r = np.corrcoef(z, rowvar=False)

    fig, (ax1, ax2) = S.figure(13.0, 5.0, ncols=2,
                               gridspec_kw=dict(width_ratios=[1.2, 1]))

    im = ax1.imshow(np.abs(r), cmap="Blues", vmin=0, vmax=1)
    ax1.set_xticks(range(len(names)))
    ax1.set_yticks(range(len(names)))
    ax1.set_xticklabels(names, rotation=45, ha="right", fontsize=8.5)
    ax1.set_yticklabels(names, fontsize=8.5)
    ax1.grid(False)
    for i in range(len(names)):
        for j in range(len(names)):
            ax1.text(j, i, f"{abs(r[i, j]):.2f}", ha="center", va="center",
                     fontsize=7.6,
                     color="white" if abs(r[i, j]) > 0.6 else S.INK)
    # 색막대는 두지 않는다. 칸마다 숫자가 적혀 있어 정보가 겹치는데다,
    # 세로 색막대의 이름표가 오른쪽 그림의 항목 이름과 부딪친다.
    ax1.set_title("(a) 항목끼리 얼마나 같은 말을 하는가 (|상관계수|)")

    # (b) 항목을 하나씩 빼 보고 빠뜨림을 센다
    esc = np.array([escape_if_dropped(z, i) for i in range(len(names))])
    rmax = np.array([max(abs(r[i, j]) for j in range(len(names)) if j != i)
                     for i in range(len(names))])
    o = np.argsort(esc)
    cols = [S.COLORS[2] if e < DROP_TARGET_PPM else S.ACCENT for e in esc[o]]
    ax2.barh(np.arange(len(names)), esc[o], color=cols, height=0.62)
    for i, k in enumerate(o):
        ax2.text(esc[k] + max(esc) * 0.02, i,
                 f"{esc[k]:,.0f} ppm  (최대 상관 {rmax[k]:.2f})",
                 va="center", fontsize=8.5)
    ax2.set_yticks(np.arange(len(names)))
    ax2.set_yticklabels([names[k] for k in o], fontsize=8.5)
    ax2.set_xlabel("그 항목을 빼면 새로 새어 나가는 양 (ppm)")
    ax2.set_xlim(0, max(esc) * 1.75)
    ax2.axvline(DROP_TARGET_PPM, color=S.ACCENT, ls="--", lw=1.5)
    ax2.text(DROP_TARGET_PPM, len(names) - 0.9,
             f" 뺄 수 있는 선 {DROP_TARGET_PPM:.0f} ppm", color=S.ACCENT,
             fontsize=9, va="top")
    ax2.set_title("(b) 뺄 수 있는 항목은 남은 항목이 대신 잡아 주는 것뿐")

    S.save(fig, MOD, "item_correlation")
    return names, r, esc, rmax, z


# ══ 그림 3 · 벤치-ATE 상관과 가드밴드 ═══════════════════════════════════
def fig3_guard():
    sd_unit, sd_bench, sd_ate, off = 0.45, 0.06, 0.16, 0.09
    b, a = bench_ate(sd_unit=sd_unit, sd_bench=sd_bench, sd_ate=sd_ate,
                     offset=off)
    d = a - b
    sd_diff = float(np.hypot(sd_bench, sd_ate))
    limit = 1.0

    fig, (ax1, ax2) = S.figure(12.6, 4.8, ncols=2)

    xs = np.linspace(min(b.min(), -1.2), max(b.max(), 1.2), 50)
    ax1.plot(b, a, "o", ms=6, color=S.COLORS[0], ls="none",
             label=f"부품 {len(b)}개")
    ax1.plot(xs, xs, color=S.MUTED, ls=":", lw=1.6, label="완전 일치")
    ax1.fill_between(xs, xs + d.mean() - 2 * d.std(ddof=1),
                     xs + d.mean() + 2 * d.std(ddof=1),
                     color=S.COLORS[0], alpha=0.13,
                     label=f"평균 차 {d.mean():+.3f} ± 2s ({d.std(ddof=1):.3f})")
    for v, c in ((limit, S.ACCENT),):
        ax1.axvline(v, color=c, ls="--", lw=1.4)
        ax1.axhline(v, color=c, ls="--", lw=1.4)
        ax1.axvline(-v, color=c, ls="--", lw=1.4)
        ax1.axhline(-v, color=c, ls="--", lw=1.4)
    ax1.text(limit, ax1.get_ylim()[0], "규격 한계 ", color=S.ACCENT,
             fontsize=9, va="bottom", ha="right")
    ax1.set_xlabel("벤치가 읽은 값 (규격 반폭 = 1)")
    ax1.set_ylabel("ATE 가 읽은 값")
    ax1.set_title("(a) 벤치-ATE 상관 — 치우침과 흩어짐을 함께 본다")
    ax1.legend(loc="upper left", fontsize=8.5)

    # (b) 가드밴드를 얼마나 당길 것인가
    gs = np.linspace(0.0, 0.6, 121)
    esc = np.array([guard_closed(sd_unit, sd_diff, limit, g)[0] * 1e6
                    for g in gs])
    ovk = np.array([guard_closed(sd_unit, sd_diff, limit, g)[1] * 1e6
                    for g in gs])
    ax2.semilogy(gs, np.maximum(esc, 1e-2), color=S.COLORS[1], ls="-",
                 lw=2.4, label="빠뜨림 (불량이 나간다)")
    ax2.semilogy(gs, np.maximum(ovk, 1e-2), color=S.COLORS[2], ls="--",
                 lw=2.4, label="헛수고 (좋은 물건을 떨군다)")
    target = 100.0
    i = int(np.argmin(np.abs(esc - target)))
    ax2.plot(gs[i], esc[i], "o", ms=8, color=S.ACCENT)
    ax2.axvline(gs[i], color=S.ACCENT, ls=":", lw=1.4)
    ax2.annotate(f"빠뜨림 {target:.0f} ppm 을 맞추려면\n"
                 f"가드밴드 {gs[i]:.2f} (= {gs[i] / sd_diff:.1f} s)\n"
                 f"이때 헛수고 {ovk[i]:,.0f} ppm",
                 xy=(gs[i], esc[i]), xytext=(0.155, 1.1e4), ha="left",
                 fontsize=9, color=S.INK, linespacing=1.4,
                 arrowprops=dict(arrowstyle="->", color=S.INK, lw=1.2))
    S.plain_log(ax2, axis="y")
    ax2.set_ylim(1e-2, 2e6)
    ax2.set_xlabel("가드밴드 (규격 반폭 대비)")
    ax2.set_ylabel("ppm")
    ax2.set_title("(b) 당길수록 안 새지만 멀쩡한 물건을 버린다")
    ax2.legend(loc="lower left", fontsize=9)

    S.save(fig, MOD, "bench_ate")
    return sd_unit, sd_diff, limit, gs[i], esc[i], ovk[i], d


# ══ 그림 4 · 수율 파레토와 재시험 ═══════════════════════════════════════
def fig4_pareto():
    fig, (ax1, ax2) = S.figure(12.6, 4.8, ncols=2,
                               gridspec_kw=dict(width_ratios=[1.15, 1]))

    names = list(BINS)
    cnt = np.array([BINS[n] for n in names], float)
    o = np.argsort(-cnt)
    cnt, names = cnt[o], [names[k] for k in o]
    cum = np.cumsum(cnt) / cnt.sum() * 100

    x = np.arange(len(names))
    ax1.bar(x, cnt, color=S.COLORS[0], width=0.64)
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=35, ha="right", fontsize=9)
    ax1.set_ylabel("불량 개수 (100만 개 생산 기준)")
    axc = ax1.twinx()
    axc.grid(False)
    axc.plot(x, cum, color=S.ACCENT, ls="-", lw=2.2, marker="o", ms=5)
    axc.axhline(80, color=S.MUTED, ls=":", lw=1.4)
    k80 = int(np.argmax(cum >= 80)) + 1
    axc.text(len(names) - 0.4, 80, "80 %", color=S.MUTED, fontsize=9,
             va="bottom", ha="right")
    axc.set_ylim(0, 105)
    axc.set_ylabel("누적 (%)", color=S.ACCENT)
    axc.tick_params(axis="y", colors=S.ACCENT)
    ax1.set_title(f"(a) 파레토 — 위 {k80}개가 불량의 {cum[k80 - 1]:.0f} %")

    # (b) 재시험 정책
    sd_unit, sd_meas, limit = 0.45, 0.16, 1.0
    rs = np.arange(0, 5)
    esc_any = np.array([retest_escape_closed(sd_unit, sd_meas, limit, r) * 1e6
                        for r in rs])
    ax2.plot(rs, esc_any, color=S.ACCENT, ls="-", lw=2.4, marker="o", ms=7,
             label="붙을 때까지 다시 잰다")
    med = np.array([retest_escape_median(sd_unit, sd_meas, limit, k,
                                         n=1_500_000,
                                         rng=np.random.default_rng(400 + k))
                    * 1e6 for k in (1, 3, 5)])
    ax2.plot([0, 1, 2], med, color=S.COLORS[2], ls="--", lw=2.4, marker="s",
             ms=7, label="여러 번 재서 중앙값으로 판정")
    ax2.set_xticks([0, 1, 2, 3, 4])
    ax2.set_xticklabels(["0 회\n(1회 판정 /\n1회 측정)",
                         "1 회\n(재시험 1 /\n3회 중앙값)",
                         "2 회\n(재시험 2 /\n5회 중앙값)",
                         "3 회", "4 회"], fontsize=8.5, linespacing=1.3)
    for r, e in zip(rs, esc_any):
        ax2.annotate(f"{e:,.0f}", xy=(r, e), xytext=(0, 9),
                     textcoords="offset points", ha="center", fontsize=9,
                     color=S.ACCENT)
    for k, e in zip([0, 1, 2], med):
        ax2.annotate(f"{e:,.0f}", xy=(k, e), xytext=(0, -16),
                     textcoords="offset points", ha="center", fontsize=9,
                     color=S.COLORS[2])
    ax2.set_xlabel("재시험 횟수 / 반복 측정 횟수")
    ax2.set_ylabel("빠뜨림 (ppm)")
    ax2.set_ylim(0, max(esc_any) * 1.35)
    ax2.set_title("(b) 같은 '다시 재기' 인데 방향이 반대다")
    ax2.legend(loc="upper left", fontsize=9)
    # 왼쪽 그림의 오른쪽 축 이름표와 오른쪽 그림의 왼쪽 축 이름표가
    # 같은 자리에 겹친다. 두 칸 사이를 벌려 준다.
    fig.subplots_adjust(wspace=0.34)

    S.save(fig, MOD, "yield_pareto")
    return names, cnt, cum, k80, rs, esc_any, med


# ══ 본체 ════════════════════════════════════════════════════════════════
def main() -> int:
    print("B12 그림 생성")
    print("=" * 62)

    t_all, u1, u4 = fig1_time()
    print(f"  [1] 시험 시간 예산      합계 {t_all:.1f} 초 · "
          f"1 사이트 {u1:.0f} UPH ({cost_per_unit(u1):,.0f} 원) · "
          f"4 사이트 {u4:.0f} UPH ({cost_per_unit(u4):,.0f} 원)")

    names, r, esc, rmax, z = fig2_corr()
    drops = [n for n, e in zip(names, esc) if e < DROP_TARGET_PPM]
    print(f"  [2] 항목 상관 행렬      {DROP_TARGET_PPM:.0f} ppm 아래로 뺄 수 있는 항목 "
          f"{len(drops)}개: {', '.join(drops) if drops else '없음'}")

    sd_unit, sd_diff, limit, g_star, e_star, o_star, d = fig3_guard()
    print(f"  [3] 가드밴드            차이 표준편차 {sd_diff:.3f} · "
          f"100 ppm 목표에 가드밴드 {g_star:.2f} "
          f"({g_star / sd_diff:.1f} s) · 헛수고 {o_star:,.0f} ppm")

    pnames, cnt, cum, k80, rs, esc_any, med = fig4_pareto()
    print(f"  [4] 파레토·재시험       위 {k80}개가 {cum[k80 - 1]:.0f} % · "
          f"재시험 0 -> 2 회에 빠뜨림 {esc_any[0]:,.0f} -> "
          f"{esc_any[2]:,.0f} ppm")

    # ── 자체 검산 ───────────────────────────────────────────────────────
    print("\n[자체 검산]")
    ok: list[bool] = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  {'OK ' if cond else 'X  '} {msg}")

    # ① 처리량
    for s in (1, 2, 4, 8):
        for lab, sf in SERIAL_FRAC.items():
            c, m = uph_closed(t_all, s, sf), uph_sim(t_all, s, sf)
            chk(abs(c - m) / c < 0.01,
                f"{s} 사이트 · {lab}: 닫힌 식 {c:.1f} vs 시뮬레이션 "
                f"{m:.1f} UPH")
    chk(uph_closed(t_all, 8, 0.2) < uph_closed(t_all, 8, 0.0) / 2,
        f"계측기를 20 % 공유하면 8 사이트에서 처리량이 "
        f"{uph_closed(t_all, 8, 0.0):.0f} -> "
        f"{uph_closed(t_all, 8, 0.2):.0f} UPH 로 주저앉는다")
    # §3 에서 뺄 수 있다고 판정된 항목(감도 / 잡음지수)만 빼 본다.
    # 둘 중 하나만 뺄 수 있으므로 두 경우를 각각 계산한다.
    base = cost_per_unit(uph_closed(t_all, 4, 0.2))
    for drop in ("수신 감도", "잡음지수"):
        tc = test_time_s([it for it in ITEMS if it[0] != drop])
        save = (base - cost_per_unit(uph_closed(tc, 4, 0.2))) * VOLUME_YEAR
        chk(save > 5e7,
            f"'{drop}'({t_all - tc:.1f} 초)을 빼면 연 {save / 1e8:.2f} 억원이 "
            f"줄어든다 — 상관 분석이 돈이 되는 이유")
    chk(sum(b for _, _, b in ITEMS) / t_all > 100,
        f"벤치는 같은 항목에 {sum(b for _, _, b in ITEMS) / t_all:.0f} 배를 쓴다 "
        f"({sum(b for _, _, b in ITEMS) / 60:.0f} 분 vs {t_all:.1f} 초)")

    # ② 항목 상관
    rt = corr_true()
    chk(np.max(np.abs(r - rt)) < 0.01,
        f"표본 50만 개의 상관 행렬이 참 행렬과 최대 "
        f"{np.max(np.abs(r - rt)):.4f} 밖에 안 벌어진다")
    chk(np.all(np.linalg.eigvalsh(rt) > 0),
        f"참 상관 행렬이 양의 정부호 (최소 고유값 "
        f"{np.linalg.eigvalsh(rt).min():.3f})")
    i_hi = int(np.argmax(rmax))
    i_lo = int(np.argmin(rmax))
    chk(esc[i_hi] < esc[i_lo],
        f"남과 가장 닮은 항목({names[i_hi]}, 상관 {rmax[i_hi]:.2f})을 뺄 때가 "
        f"가장 안 닮은 항목({names[i_lo]}, {rmax[i_lo]:.2f})을 뺄 때보다 "
        f"덜 샌다 ({esc[i_hi]:,.0f} vs {esc[i_lo]:,.0f} ppm)")
    chk(np.corrcoef(rmax, np.log(esc))[0, 1] < -0.6,
        f"'최대 상관' 과 '빠뜨림' 은 뚜렷한 역상관 "
        f"({np.corrcoef(rmax, np.log(esc))[0, 1]:.2f})")
    z2 = draw_units(500_000, rng=np.random.default_rng(4321))
    e2 = np.array([escape_if_dropped(z2, i) for i in range(len(names))])
    rel = np.max(np.abs(e2 - esc) / esc) * 100
    chk(list(np.argsort(e2)) == list(np.argsort(esc)),
        f"다른 난수로 다시 뽑아도 빠뜨림 **순위**가 그대로 "
        f"(값은 최대 {rel:.0f} % 흔들린다)")
    chk(rel < 20,
        f"50만 개 표본이면 빠뜨림 값 자체도 {rel:.0f} % 안에서 재현된다")
    chk(all(e > 0 for e in esc),
        "어떤 항목을 빼도 빠뜨림은 0 이 아니다 — 완전히 겹치는 항목은 없다")
    # 서로를 덮어 주는 짝은 **둘 중 하나만** 뺄 수 있다.
    i_s, i_n = names.index("수신 감도"), names.index("잡음지수")
    keep = [j for j in range(len(names)) if j not in (i_s, i_n)]
    both = float(np.mean(
        ((np.abs(z[:, i_s]) > LIMIT_SIGMA) | (np.abs(z[:, i_n]) > LIMIT_SIGMA))
        & np.all(np.abs(z[:, keep]) <= LIMIT_SIGMA, axis=1))) * 1e6
    chk(both > 2.5 * max(esc[i_s], esc[i_n]),
        f"감도와 잡음지수를 **둘 다** 빼면 {both:,.0f} ppm — "
        f"하나만 뺄 때({max(esc[i_s], esc[i_n]):,.0f} ppm)의 "
        f"{both / max(esc[i_s], esc[i_n]):.0f} 배다. 서로를 덮어 주던 짝이라 "
        f"둘 중 하나는 남겨야 한다")

    # ③ 가드밴드
    for g in (0.0, 0.2, 0.4):
        c = guard_closed(sd_unit, sd_diff, limit, g)
        m = guard_mc(sd_unit, sd_diff, limit, g,
                     rng=np.random.default_rng(int(g * 100) + 1))
        # 허용 오차는 고정값이 아니라 몬테카를로 자신의 표본 오차로 잡는다.
        # p 가 클수록 se 가 커지므로 고정 문턱은 큰 쪽에서 반드시 걸린다.
        se = [np.sqrt(max(v, 1e-12) * (1 - v) / 4_000_000) for v in m]
        chk(abs(c[0] - m[0]) < 4 * se[0] and abs(c[1] - m[1]) < 4 * se[1],
            f"가드밴드 {g:.1f}: 닫힌 식 ({c[0] * 1e6:.0f}, {c[1] * 1e6:.0f}) "
            f"vs 몬테카를로 ({m[0] * 1e6:.0f}, {m[1] * 1e6:.0f}) ppm "
            f"(표본 오차 4 배 안)")
    e0, o0 = (v * 1e6 for v in guard_closed(sd_unit, sd_diff, limit, 0.0))
    chk(e_star < e0 and o_star > o0,
        f"가드밴드를 {g_star:.2f} 당기면 빠뜨림 {e0:,.0f} -> "
        f"{e_star:,.0f} ppm, 헛수고 {o0:,.0f} -> {o_star:,.0f} ppm")
    chk(o_star / o0 > 5,
        f"빠뜨림을 {e0 / e_star:.0f} 분의 1 로 줄이는 값이 헛수고 "
        f"{o_star / o0:.0f} 배 — 가드밴드는 공짜가 아니다")
    chk(abs(np.mean(d) - 0.09) < 0.05,
        f"산점도에서 읽은 평균 차 {np.mean(d):+.3f} 가 참 오프셋 +0.090 을 "
        f"짚는다")
    chk(abs(np.std(d, ddof=1) - sd_diff) < 0.04,
        f"차이의 표준편차 {np.std(d, ddof=1):.3f} = 두 계의 제곱합 "
        f"{sd_diff:.3f}")
    # 오프셋을 그대로 두면 가드밴드가 한쪽으로만 필요해진다.
    e_off, _ = guard_closed(sd_unit, sd_diff, limit, 0.0)
    chk(e_off * 1e6 > 1000,
        f"가드밴드 없이 그냥 넘기면 {e_off * 1e6:,.0f} ppm 이 샌다")

    # ④ 재시험
    for rr in (0, 1, 2, 3):
        c = retest_escape_closed(sd_unit, sd_meas := 0.16, limit, rr)
        m = retest_escape_mc(sd_unit, sd_meas, limit, rr,
                             rng=np.random.default_rng(700 + rr))
        chk(abs(c - m) < 1.5e-4,
            f"재시험 {rr} 회: 닫힌 식 {c * 1e6:,.0f} vs 시뮬레이션 "
            f"{m * 1e6:,.0f} ppm")
    chk(esc_any[2] > esc_any[0] * 1.8,
        f"재시험 2 회면 빠뜨림이 {esc_any[0]:,.0f} -> {esc_any[2]:,.0f} ppm "
        f"으로 {esc_any[2] / esc_any[0]:.1f} 배가 된다")
    chk(all(b > a for a, b in zip(esc_any, esc_any[1:])),
        "재시험을 늘릴수록 빠뜨림은 단조 증가한다 — 공짜 재시험은 없다")
    chk(med[2] < med[0],
        f"반대로 중앙값 판정은 반복할수록 줄어든다 "
        f"({med[0]:,.0f} -> {med[2]:,.0f} ppm)")
    chk(esc_any[2] > med[2] * 3,
        f"같은 3 번 측정인데 정책에 따라 {esc_any[2]:,.0f} ppm 과 "
        f"{med[2]:,.0f} ppm 으로 갈린다")
    chk(abs(cum[k80 - 1] - 80) < 20 and k80 <= 3,
        f"파레토: 위 {k80}개 항목이 불량의 {cum[k80 - 1]:.0f} % 를 차지한다")

    print()
    if not all(ok):
        return 1
    print(f"  검산 {len(ok)}항목 전부 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
