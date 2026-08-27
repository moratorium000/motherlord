#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B11 (측정 시스템 분석 — 반복성·재현성·상관) 그림 생성기.

만드는 그림
  B11-1  게이지 R&R 분산 분해 — 산포의 몇 할이 측정기 몫인가
  B11-2  구별 범주 수(ndc) — 이 측정기는 등급을 몇 개로 나눌 수 있는가
  B11-3  Cpk 와 수율, 그리고 측정 오차가 만드는 오판정
  B11-4  장비 두 대의 상관 — 최소제곱이 기울기를 깎는 이유

교차검증 네 갈래
  ① 분산 분해: 분산분석(ANOVA) vs 평균-범위(X-bar/R) 법 vs 생성에 쓴 참값
  ② ndc 와 %GRR: 두 판정 기준이 서로 어긋나는 지점을 닫힌 식으로 확인
  ③ 수율: 정규분포 닫힌 식 vs 몬테카를로, 오판정률은 2차원 수치적분 vs 몬테카를로
  ④ 상관: 최소제곱 기울기의 감쇠 계수를 이론값과 반복 시뮬레이션 평균으로 대조

실행: python3 scripts/gen_fig_b11.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rf_style as S  # noqa: E402

MOD = "B11"
RNG = np.random.default_rng(20260901)

# ── 연구 대상 ───────────────────────────────────────────────────────────
# 2.4 GHz 증폭기 모듈의 **이득(dB)** 을 잰다. 공차는 12.0 ± 1.0 dB.
NOMINAL_DB = 12.0
TOL_HALF_DB = 1.0

# 연구 설계: 부품 10개 × 측정자 3명 × 반복 3회 (AIAG 표준 설계)
N_PART, N_OP, N_TRIAL = 10, 3, 3

# ── 게이지 세 가지 (참값. 단위 dB) ──────────────────────────────────────
# sd_part 는 게이지가 아니라 **공정**의 성질이다. 세 번째 경우가 그 점을
# 드러내려고 있다 — 같은 게이지인데 공정이 좋아지면 판정이 뒤집힌다.
GAUGES = {
    "좋은 게이지": dict(sd_part=0.300, sd_op=0.010, sd_int=0.005, sd_rep=0.020),
    "나쁜 게이지": dict(sd_part=0.300, sd_op=0.090, sd_int=0.045, sd_rep=0.135),
    "좋은 게이지 · 좁아진 공정":
        dict(sd_part=0.100, sd_op=0.010, sd_int=0.005, sd_rep=0.020),
}
# 세 번째 경우는 **첫 번째와 같은 게이지 데이터**를 쓴다. 난수를 새로 뽑으면
# 표본 흔들림이 섞여 "공정만 바뀌었다" 는 이야기가 흐려지기 때문이다.
# 부품 효과만 0.100/0.300 배로 줄인다.
SAME_GAUGE_AS = {"좋은 게이지 · 좁아진 공정": ("좋은 게이지", 0.100 / 0.300)}

# AIAG 평균-범위 법의 상수 (교차검증 ①에 쓴다)
K1 = {2: 0.8862, 3: 0.5908}          # 반복 횟수별
K2 = {2: 0.7071, 3: 0.5231}          # 측정자 수별
K3 = {5: 0.4030, 10: 0.3146}         # 부품 수별


# ══ 연구 데이터 생성 ═════════════════════════════════════════════════════
def make_study(sd_part, sd_op, sd_int, sd_rep,
               n_part=N_PART, n_op=N_OP, n_trial=N_TRIAL, rng=None):
    """y[부품, 측정자, 반복] 배열을 만든다.

    참값을 알고 시작하므로, 뒤에서 분산 분해가 그 참값을 되찾아 오는지
    확인할 수 있다 (교차검증 ①).
    """
    rng = rng or np.random.default_rng(7)
    part = rng.normal(0.0, sd_part, n_part)[:, None, None]
    op = rng.normal(0.0, sd_op, n_op)[None, :, None]
    inter = rng.normal(0.0, sd_int, (n_part, n_op))[:, :, None]
    err = rng.normal(0.0, sd_rep, (n_part, n_op, n_trial))
    return NOMINAL_DB + part + op + inter + err, part


def shrink_parts(y, part, ratio):
    """같은 게이지·같은 측정자로 **더 균일한 배치**를 잰 셈 치고 다시 만든다.

    측정계가 만든 흔들림(측정자·교호작용·반복)은 손대지 않고 부품 간 차이만
    ratio 배로 줄인다. 게이지는 그대로인데 판정이 바뀌는 것을 보이려면
    난수를 새로 뽑아서는 안 된다 — 표본 흔들림이 섞여 이야기가 흐려진다.
    """
    return y - part + part * ratio


# ══ 분산 분해 ═══════════════════════════════════════════════════════════
def anova_grr(y):
    """균형 이원 배치 분산분석으로 분산 성분을 가른다.

    측정값이 흔들리는 이유는 넷이다 — 부품이 정말 다르거나(부품 산포),
    측정자마다 버릇이 다르거나(재현성), 특정 측정자가 특정 부품에서만
    다르거나(교호작용), 같은 사람이 같은 부품을 두 번 재도 다르거나(반복성).
    분산분석은 이 넷을 제곱합으로 갈라낸다.
    """
    p, o, r = y.shape
    gm = y.mean()
    m_part = y.mean(axis=(1, 2))                      # 부품별 평균
    m_op = y.mean(axis=(0, 2))                        # 측정자별 평균
    m_cell = y.mean(axis=2)                           # 칸(부품×측정자) 평균

    ss_part = o * r * np.sum((m_part - gm) ** 2)
    ss_op = p * r * np.sum((m_op - gm) ** 2)
    ss_int = r * np.sum((m_cell - m_part[:, None] - m_op[None, :] + gm) ** 2)
    ss_err = np.sum((y - m_cell[:, :, None]) ** 2)

    ms_part = ss_part / (p - 1)
    ms_op = ss_op / (o - 1)
    ms_int = ss_int / ((p - 1) * (o - 1))
    ms_err = ss_err / (p * o * (r - 1))

    # 음수가 나오면 0 으로 자른다. 분산은 음수일 수 없고, 참 성분이 0에
    # 가까울 때 추정값이 음수로 내려가는 것은 이 방법의 알려진 성질이다.
    v_rep = ms_err
    v_int = max(0.0, (ms_int - ms_err) / r)
    v_op = max(0.0, (ms_op - ms_int) / (p * r))
    v_part = max(0.0, (ms_part - ms_int) / (o * r))

    v_repro = v_op + v_int
    v_grr = v_rep + v_repro
    return dict(rep=v_rep, op=v_op, inter=v_int, repro=v_repro,
                part=v_part, grr=v_grr, total=v_grr + v_part,
                ms=(ms_part, ms_op, ms_int, ms_err))


def xbar_r_grr(y):
    """같은 것을 AIAG 평균-범위 법으로 (교차검증 ①).

    분산분석이 없던 시절 현장에서 손으로 계산하던 방법이다. 범위(최대-최소)에
    상수를 곱해 표준편차를 어림한다. 교호작용을 따로 떼지 않으므로
    분산분석과 정확히 같지는 않다 — 그 차이 자체가 §2의 이야깃거리다.
    """
    p, o, r = y.shape
    r_bar = np.mean(np.ptp(y, axis=2))                # 반복 안의 평균 범위
    ev = r_bar * K1[r]                                # 반복성 (장비 산포)

    op_mean = y.mean(axis=(0, 2))
    x_diff = op_mean.max() - op_mean.min()
    av_sq = (x_diff * K2[o]) ** 2 - ev ** 2 / (p * r)
    av = np.sqrt(max(0.0, av_sq))                     # 재현성 (측정자 산포)

    grr = np.hypot(ev, av)
    part_rng = np.ptp(y.mean(axis=(1, 2)))
    pv = part_rng * K3[p]                             # 부품 산포
    return dict(ev=ev, av=av, grr=grr, part=pv, total=np.hypot(grr, pv))


def pct_grr_study(v):
    """산포 대비 %GRR — 총 산포 중 측정계 몫."""
    return 100.0 * np.sqrt(v["grr"] / v["total"])


def pct_grr_tol(v, tol_half=TOL_HALF_DB):
    """공차 대비 %GRR — 공차 폭 중 측정계 몫. 6 시그마를 쓴다."""
    return 100.0 * 6.0 * np.sqrt(v["grr"]) / (2.0 * tol_half)


def ndc(v):
    """구별 범주 수. 1.41 = sqrt(2). 내림한다 (AIAG 규약)."""
    return int(np.floor(1.41 * np.sqrt(v["part"] / v["grr"])))


def ndc_from_pct(pct):
    """%GRR(산포 대비) 하나만으로 ndc 를 얻는 닫힌 식 (교차검증 ②).

    p = sigma_grr / sigma_total 이므로 sigma_part/sigma_grr = sqrt(1/p^2 - 1).
    """
    p = pct / 100.0
    if p >= 1.0:
        return 0
    return 1.41 * np.sqrt(1.0 / p ** 2 - 1.0)


# ══ 수율과 오판정 ═══════════════════════════════════════════════════════
def yield_closed(cpk_c):
    """중심에 맞춘 공정의 수율. Cp = Cpk 이므로 2*Phi(3Cpk) - 1."""
    return 2.0 * stats.norm.cdf(3.0 * cpk_c) - 1.0


def yield_mc(cpk_c, n=2_000_000, rng=None):
    """같은 것을 몬테카를로로 (교차검증 ③)."""
    rng = rng or np.random.default_rng(3)
    sd = 1.0 / (3.0 * cpk_c)                          # 규격 반폭을 1 로 두고
    x = rng.normal(0.0, sd, n)
    return float(np.mean(np.abs(x) < 1.0))


def misjudge_quad(sd_part, sd_gauge, half=1.0, n=4001, span=7.0):
    """오판정률을 2차원 적분으로 계산한다.

    참값 X ~ N(0, sd_part), 측정값 M = X + E, E ~ N(0, sd_gauge).
    - 헛되이 버림: 진짜 합격인데 측정이 밖으로 나감
    - 놓쳐서 보냄: 진짜 불합격인데 측정이 안으로 들어옴
    X 로 적분하고, 각 X 에서 E 의 조건부 확률을 닫힌 식으로 넣는다.
    """
    # 게이지가 아주 좋으면 적분할 것이 규격선 바로 옆 폭 몇 sigma_gauge 안에만
    # 몰린다. 고른 격자로는 그 좁은 봉우리를 몇 점으로만 찍어 두 오판정률의
    # 크기 순서까지 뒤집힌다 (sd_gauge 0.005 에서 실제로 뒤집혔다).
    # 그래서 규격선 둘레를 따로 촘촘히 깐다.
    x = np.linspace(-span * sd_part, span * sd_part, n)
    for edge in (-half, half):
        x = np.append(x, np.linspace(edge - 10 * sd_gauge,
                                     edge + 10 * sd_gauge, 2001))
    x = np.unique(x)
    fx = stats.norm.pdf(x, 0.0, sd_part)
    # 측정이 규격 안에 들어올 조건부 확률
    p_in = (stats.norm.cdf((half - x) / sd_gauge)
            - stats.norm.cdf((-half - x) / sd_gauge))
    good = np.abs(x) < half
    false_rej = np.trapezoid(fx * good * (1.0 - p_in), x)
    false_acc = np.trapezoid(fx * (~good) * p_in, x)
    return float(false_rej), float(false_acc)


def misjudge_mc(sd_part, sd_gauge, half=1.0, n=4_000_000, rng=None):
    """같은 것을 몬테카를로로 (교차검증 ③)."""
    rng = rng or np.random.default_rng(11)
    x = rng.normal(0.0, sd_part, n)
    m = x + rng.normal(0.0, sd_gauge, n)
    good, pas = np.abs(x) < half, np.abs(m) < half
    return float(np.mean(good & ~pas)), float(np.mean(~good & pas))


# ══ 장비 간 상관 ════════════════════════════════════════════════════════
def two_testers(n=40, sd_true=0.30, sd_a=0.10, sd_b=0.06,
                offset=-0.12, rng=None):
    """같은 부품 n 개를 장비 두 대로 잰다. 참 기울기는 1, 참 오프셋은 offset."""
    rng = rng or np.random.default_rng(5)
    x_true = rng.normal(NOMINAL_DB, sd_true, n)
    a = x_true + rng.normal(0.0, sd_a, n)
    b = x_true + offset + rng.normal(0.0, sd_b, n)
    return a, b


def ols_fit(x, y):
    """보통 최소제곱. x 에도 오차가 있으면 기울기가 0 쪽으로 깎인다."""
    sxx = np.var(x, ddof=1)
    sxy = np.cov(x, y, ddof=1)[0, 1]
    slope = sxy / sxx
    return slope, y.mean() - slope * x.mean()


def deming_fit(x, y, lam):
    """데밍 회귀. lam = 오차분산비 (y 쪽 / x 쪽).

    두 축 모두에 오차가 있을 때 쓰는 회귀다. lam = 1 이면 직교회귀와 같다.
    장비 두 대를 맞댈 때 최소제곱을 쓰면 안 되는 이유가 여기 있다 — 어느
    쪽을 x 로 놓느냐에 따라 기울기가 달라지는데, 데밍은 달라지지 않는다.
    """
    sxx = np.var(x, ddof=1)
    syy = np.var(y, ddof=1)
    sxy = np.cov(x, y, ddof=1)[0, 1]
    num = syy - lam * sxx + np.sqrt((syy - lam * sxx) ** 2 + 4 * lam * sxy ** 2)
    slope = num / (2 * sxy)
    return slope, y.mean() - slope * x.mean()


def attenuation(sd_true, sd_a):
    """최소제곱 기울기가 깎이는 비율 (이론값, 교차검증 ④)."""
    return sd_true ** 2 / (sd_true ** 2 + sd_a ** 2)


# ══ 그림 1 · 분산 분해 ══════════════════════════════════════════════════
def fig1_variance():
    names = list(GAUGES)
    studies, parts, vs = {}, {}, {}
    for i, nm in enumerate(names):
        if nm in SAME_GAUGE_AS:
            src, ratio = SAME_GAUGE_AS[nm]
            y = shrink_parts(studies[src], parts[src], ratio)
            p = parts[src] * ratio
        else:
            y, p = make_study(**GAUGES[nm], rng=np.random.default_rng(100 + i))
        studies[nm], parts[nm] = y, p
        vs[nm] = anova_grr(y)

    # 축 눈금에 쓸 짧은 이름. 긴 이름을 그대로 쓰면 옆 칸과 부딪친다.
    short = ["좋은 게이지", "나쁜 게이지", "좋은 게이지\n· 좁아진 공정"]

    fig, (ax1, ax2) = S.figure(12.4, 4.6, ncols=2,
                               gridspec_kw=dict(width_ratios=[1.15, 1]))

    # (a) 분산을 백분율로 쌓는다
    parts = ["반복성 (같은 사람이 두 번)", "재현성 (사람이 바뀌면)",
             "부품 산포 (진짜 차이)"]
    cols = [S.COLORS[1], S.COLORS[4], S.COLORS[0]]
    bottom = np.zeros(len(names))
    for key, lab, c in zip(["rep", "repro", "part"], parts, cols):
        vals = np.array([100 * vs[n][key] / vs[n]["total"] for n in names])
        ax1.bar(names, vals, bottom=bottom, color=c, label=lab,
                edgecolor="white", lw=1.2, width=0.62)
        for j, (v, b) in enumerate(zip(vals, bottom)):
            if v > 5:
                ax1.text(j, b + v / 2, f"{v:.0f} %", ha="center",
                         va="center", color="white", fontweight="bold",
                         fontsize=10)
        bottom += vals
    ax1.set_ylabel("전체 분산 중 차지하는 몫 (%)")
    # 막대는 100 까지만 찬다. 위쪽 여백은 범례 자리다 — 범례를 막대 위에
    # 얹으면 1~5 % 짜리 얇은 칸이 가려진다.
    ax1.set_ylim(0, 124)
    ax1.set_yticks([0, 20, 40, 60, 80, 100])
    ax1.set_title("(a) 산포는 어디서 오는가 — 분산분석 분해")
    ax1.legend(loc="upper center", fontsize=9)
    ax1.set_xticks(np.arange(len(names)))
    ax1.set_xticklabels(short, fontsize=9)

    # (b) 같은 게이지, 두 가지 기준
    xs = np.arange(len(names))
    st = np.array([pct_grr_study(vs[n]) for n in names])
    tl = np.array([pct_grr_tol(vs[n]) for n in names])
    ax2.axhspan(0, 10, color=S.COLORS[2], alpha=0.13)
    ax2.axhspan(10, 30, color=S.COLORS[4], alpha=0.15)
    ax2.axhspan(30, 100, color=S.ACCENT, alpha=0.12)
    # 판정 구간 이름은 막대가 없는 오른쪽 여백에 세로로 세운다.
    for y0, lab in ((5, "합격\n10 % 미만"), (20, "조건부\n10~30 %"),
                    (55, "불합격\n30 % 초과")):
        ax2.text(0.985, y0, lab, transform=ax2.get_yaxis_transform(),
                 ha="right", va="center", fontsize=9, color=S.MUTED,
                 linespacing=1.4)
    ax2.bar(xs - 0.19, st, 0.36, color=S.COLORS[0], label="산포 대비")
    ax2.bar(xs + 0.19, tl, 0.36, color=S.COLORS[3], label="공차 대비 (±1.0 dB)")
    # 9.6 을 10 으로 반올림해 적으면 판정선 위에 걸린 것처럼 읽힌다.
    for x, v in zip(xs - 0.19, st):
        ax2.text(x, v + 1.8, f"{v:.1f}", ha="center", fontsize=9)
    for x, v in zip(xs + 0.19, tl):
        ax2.text(x, v + 1.8, f"{v:.1f}", ha="center", fontsize=9)
    ax2.set_xticks(xs)
    ax2.set_xticklabels(short, fontsize=9)
    ax2.set_ylabel("%GRR")
    ax2.set_ylim(0, 80)
    ax2.set_xlim(-0.6, 3.35)
    ax2.set_title("(b) 같은 게이지가 기준에 따라 다르게 판정된다")
    ax2.legend(loc="upper left", fontsize=9)

    S.save(fig, MOD, "grr_variance")
    return studies, vs


# ══ 그림 2 · 구별 범주 수 ═══════════════════════════════════════════════
def fig2_ndc():
    fig, (ax1, ax2) = S.figure(12.4, 4.6, ncols=2,
                               gridspec_kw=dict(width_ratios=[1.25, 1]))

    # (a) 부품 12개를 재 본다. 오차 막대가 겹치면 등급을 못 가른다.
    rng = np.random.default_rng(42)
    n = 12
    true = np.sort(rng.normal(0.0, 0.30, n))
    cases = [("ndc = 15 (측정계가 좋을 때)", 0.028, 0.10),
             ("ndc = 2 (측정계가 나쁠 때)", 0.170, -0.10)]
    got = []
    # 나쁜 쪽의 등급 띠를 먼저 깐다. ndc 가 곧 "부품 산포 6시그마를 몇 칸으로
    # 나눌 수 있는가" 이므로, 칸을 그려 놓고 그 위에 오차 막대를 얹으면
    # 왜 2칸밖에 못 나누는지가 바로 보인다.
    sg_bad = cases[1][1]
    k_bad = int(np.floor(1.41 * 0.30 / sg_bad))
    lo, span = -3 * 0.30, 6 * 0.30
    for i in range(k_bad):
        y0 = lo + span * i / k_bad
        ax1.axhspan(y0, y0 + span / k_bad, color=S.ACCENT,
                    alpha=0.10 if i % 2 else 0.03, zorder=0)
        ax1.text(-0.85, y0 + span / (2 * k_bad), f"등급\n{i + 1}",
                 ha="center", va="center", fontsize=9, color=S.ACCENT,
                 linespacing=1.3)

    for (lab, sg, dy), c in zip(cases, [S.COLORS[0], S.ACCENT]):
        meas = true + rng.normal(0.0, sg, n)
        k = int(np.floor(1.41 * 0.30 / sg))
        got.append(k)
        ax1.errorbar(np.arange(1, n + 1) + dy, meas, yerr=1.96 * sg, fmt="o",
                     ms=5, capsize=3, lw=1.6, color=c, label=lab)
    ax1.plot(np.arange(1, n + 1), true, ls=":", color=S.MUTED, marker="s",
             ms=4, label="참값 (알고 있다고 치자)")
    ax1.set_xlabel("부품 번호 (참값 순으로 정렬)")
    ax1.set_ylabel("공칭 대비 이득 편차 (dB)")
    ax1.set_xlim(-1.5, n + 0.8)
    ax1.set_xticks(np.arange(1, n + 1))
    ax1.set_title(f"(a) 나쁜 측정계는 {k_bad}칸으로밖에 못 나눈다")
    ax1.legend(loc="upper left", fontsize=9)

    # (b) %GRR 과 ndc 는 같은 규칙이 아니다
    pct = np.linspace(4, 60, 400)
    ax2.plot(pct, [ndc_from_pct(p) for p in pct], color=S.COLORS[0], ls="-",
             lw=2.2, label="ndc (내림 전)")
    ax2.axhline(5, color=S.ACCENT, ls="--", lw=1.6)
    ax2.axvline(30, color=S.MUTED, ls=":", lw=1.6)
    cross = 100.0 / np.sqrt((5 / 1.41) ** 2 + 1.0)
    ax2.axvline(cross, color=S.COLORS[2], ls="-.", lw=1.6)
    ax2.annotate(f"ndc 5 의 경계는\n%GRR {cross:.1f} %",
                 xy=(cross, 5), xytext=(11, 12.5),
                 ha="left", fontsize=9, color=S.COLORS[2], linespacing=1.4,
                 arrowprops=dict(arrowstyle="->", color=S.COLORS[2], lw=1.2,
                                 connectionstyle="arc3,rad=-0.25"))
    ax2.annotate("%GRR 30 % 는\n조건부 합격이지만\n여기서 ndc 는 4",
                 xy=(30.6, ndc_from_pct(30)), xytext=(36, 9.5),
                 fontsize=9, color=S.ACCENT, linespacing=1.4,
                 arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    ax2.set_xlabel("%GRR (산포 대비)")
    ax2.set_ylabel("구별 범주 수 ndc")
    ax2.set_ylim(0, 22)
    ax2.set_title("(b) 두 판정 기준은 겹치지 않는다")
    ax2.legend(loc="upper right", fontsize=9)

    S.save(fig, MOD, "ndc")
    return got, cross


# ══ 그림 3 · Cpk 와 수율, 오판정 ════════════════════════════════════════
def fig3_cpk():
    fig, (ax1, ax2) = S.figure(12.4, 4.6, ncols=2)

    # (a) Cpk 와 수율
    cp = np.linspace(0.6, 2.0, 300)
    ax1.semilogy(cp, (1.0 - yield_closed(cp)) * 1e6, color=S.COLORS[0],
                 ls="-", lw=2.4, label="닫힌 식  2*Phi(3Cpk) - 1")
    # 몬테카를로는 200만 번 뽑아야 겨우 1 ppm 을 가른다. Cpk 1.67 (0.6 ppm)
    # 은 이 표본 수로는 확인이 안 되므로 점을 찍지 않는다 — 못 찍는다는 것
    # 자체가 §7 에서 "수율은 시뮬레이션으로 확인할 수 없다"는 근거가 된다.
    mc_cp = np.array([0.8, 1.0, 1.33])
    mc = np.array([(1 - yield_mc(c, rng=np.random.default_rng(50 + i))) * 1e6
                   for i, c in enumerate(mc_cp)])
    ax1.plot(mc_cp, mc, "o", ms=8, color=S.ACCENT, ls="none",
             label="몬테카를로 200만 회")
    # 첫 점의 값표는 오른쪽으로 빼면 Cpk 1.00 안내선을 가로지른다.
    for c, m, dx, ha in zip(mc_cp, mc, (-10, 10, 10), ("right",) + ("left",) * 2):
        ax1.annotate(f"{m:,.0f} ppm", xy=(c, m), xytext=(dx, -2),
                     textcoords="offset points", fontsize=9, color=S.ACCENT,
                     va="center", ha=ha)
    for c, lab in ((1.0, "Cpk 1.00\n(3 시그마)"), (4 / 3, "Cpk 1.33\n(업계 관행)")):
        ax1.axvline(c, color=S.MUTED, ls=":", lw=1.2)
        ax1.text(c, 1.5e-3, lab, fontsize=9, color=S.MUTED, ha="center",
                 va="bottom", linespacing=1.4)
    ax1.set_ylim(1e-3, 3e5)
    S.plain_log(ax1, axis="y")
    ax1.set_xlabel("Cpk (중심에 맞춘 공정)")
    ax1.set_ylabel("불합격률 (ppm)")
    ax1.set_title("(a) Cpk 가 0.33 오르면 불합격이 자릿수로 준다")
    ax1.legend(loc="upper right", fontsize=9)

    # (b) 측정 오차가 만드는 오판정
    # 공정은 그대로(Cpk 1.33) 두고 게이지만 나빠지게 한다.
    sd_part = 1.0 / (3 * 4 / 3)
    # %GRR 이 딱 10 / 30 % 가 되는 게이지를 역산해 격자에 끼워 넣는다.
    # 가장 가까운 점을 골라 "약 12 %" 라고 적으면 판정선 이야기가 흐려진다.
    def sd_for_pct(pct):
        p = pct / 100.0
        return sd_part * p / np.sqrt(1.0 - p ** 2)

    grid = np.union1d(np.linspace(0.005, sd_for_pct(50.0), 90),
                      [sd_for_pct(10.0), sd_for_pct(30.0)])
    pcts, rej, acc = [], [], []
    for sd_g in grid:
        v = dict(grr=sd_g ** 2, part=sd_part ** 2,
                 total=sd_g ** 2 + sd_part ** 2)
        fr, fa = misjudge_quad(sd_part, sd_g)
        pcts.append(pct_grr_study(v))
        rej.append(fr * 1e6)
        acc.append(fa * 1e6)
    ax2.semilogy(pcts, rej, color=S.COLORS[1], ls="-", lw=2.4,
                 label="헛되이 버림 (좋은 물건을 떨군다)")
    ax2.semilogy(pcts, acc, color=S.COLORS[2], ls="--", lw=2.4,
                 label="놓쳐서 보냄 (불량이 나간다)")
    for m, dx, dy, ha in ((10.0, 9, 26, "left"), (30.0, 10, -30, "left")):
        i = int(np.argmin(np.abs(np.array(pcts) - m)))
        ax2.plot(pcts[i], rej[i], "o", ms=7, color=S.COLORS[1])
        ax2.plot(pcts[i], acc[i], "s", ms=7, color=S.COLORS[2])
        ax2.axvline(m, color=S.MUTED, ls=":", lw=1.2)
        ax2.annotate(f"%GRR {m:.0f} %\n버림 {rej[i]:,.0f} ppm\n"
                     f"보냄 {acc[i]:,.0f} ppm",
                     xy=(pcts[i], rej[i]), xytext=(dx, dy),
                     textcoords="offset points", fontsize=9, ha=ha,
                     color=S.INK, linespacing=1.4)
    S.plain_log(ax2, axis="y")
    ax2.set_ylim(1, 3e4)
    ax2.set_xlabel("%GRR (산포 대비)")
    ax2.set_ylabel("오판정 (ppm)")
    ax2.set_title("(b) 공정은 그대로인데 게이지만 나빠질 때 (Cpk 4/3)")
    ax2.legend(loc="upper left", fontsize=9)

    S.save(fig, MOD, "cpk_yield")
    return pcts, rej, acc


# ══ 그림 4 · 장비 간 상관 ═══════════════════════════════════════════════
def fig4_correlation():
    sd_true, sd_a, sd_b, off = 0.30, 0.10, 0.06, -0.12
    a, b = two_testers(sd_true=sd_true, sd_a=sd_a, sd_b=sd_b, offset=off,
                       rng=np.random.default_rng(20260901))
    s_ols, i_ols = ols_fit(a, b)
    s_dem, i_dem = deming_fit(a, b, lam=(sd_b / sd_a) ** 2)

    fig, (ax1, ax2) = S.figure(12.4, 4.6, ncols=2)

    xs = np.linspace(a.min() - 0.15, a.max() + 0.15, 50)
    ax1.plot(a, b, "o", ms=6, color=S.COLORS[0], ls="none",
             label=f"부품 {len(a)}개")
    ax1.plot(xs, xs + off, color=S.MUTED, ls=":", lw=1.8,
             label=f"참 관계 (기울기 1, 오프셋 {off:+.2f} dB)")
    ax1.plot(xs, s_ols * xs + i_ols, color=S.ACCENT, ls="--", lw=2.2,
             label=f"최소제곱: 기울기 {s_ols:.3f}")
    ax1.plot(xs, s_dem * xs + i_dem, color=S.COLORS[2], ls="-", lw=2.2,
             label=f"데밍 회귀: 기울기 {s_dem:.3f}")
    ax1.set_xlabel("장비 A 가 읽은 이득 (dB)")
    ax1.set_ylabel("장비 B 가 읽은 이득 (dB)")
    ax1.set_title("(a) 최소제곱은 기울기를 깎는다")
    ax1.legend(loc="upper left", fontsize=9)

    # (b) 차이 그림 — 실제로 오프셋을 정할 때 보는 그림
    mean = (a + b) / 2
    diff = b - a
    bias, sd_d = diff.mean(), diff.std(ddof=1)
    ax2.plot(mean, diff, "o", ms=6, color=S.COLORS[0], ls="none")
    S.emph(ax2, [mean.min() - 0.1, mean.max() + 0.1], [bias, bias],
           color=S.COLORS[3], lw=2.2)
    # 글자는 왼쪽에 붙인다. 오른쪽 끝에 두면 축 밖으로 잘려 나간다.
    ax2.text(mean.min(), bias, f"평균 차 {bias:+.3f} dB ", va="bottom",
             ha="left", fontsize=9, color=S.COLORS[3], fontweight="bold")
    for k, ls in ((1.96, "--"), (-1.96, "--")):
        ax2.axhline(bias + k * sd_d, color=S.ACCENT, ls=ls, lw=1.5)
    ax2.text(mean.max(), bias + 1.96 * sd_d,
             f"일치 한계 {bias + 1.96 * sd_d:+.3f} / "
             f"{bias - 1.96 * sd_d:+.3f} dB",
             va="bottom", ha="right", fontsize=9, color=S.ACCENT)
    ax2.set_ylim(bias - 2.6 * sd_d, bias + 2.9 * sd_d)
    ax2.axhline(0, color=S.MUTED, ls=":", lw=1.2)
    ax2.set_xlabel("두 장비의 평균 (dB)")
    ax2.set_ylabel("차이  B - A  (dB)")
    ax2.set_title("(b) 차이 그림 — 오프셋을 정하는 곳")
    S.save(fig, MOD, "tester_correlation")
    return (s_ols, s_dem, bias, sd_d, sd_true, sd_a, sd_b, off)


# ══ 본체 ════════════════════════════════════════════════════════════════
def main() -> int:
    print("B11 그림 생성")
    print("=" * 62)

    studies, vs = fig1_variance()
    for nm in GAUGES:
        v = vs[nm]
        print(f"  [1] {nm:<20s} %GRR 산포 {pct_grr_study(v):5.1f} % · "
              f"공차 {pct_grr_tol(v):5.1f} % · ndc {ndc(v):2d}")

    got, cross = fig2_ndc()
    print(f"  [2] ndc 시각화          {got} · "
          f"ndc 5 와 만나는 %GRR {cross:.1f} %")

    pcts, rej, acc = fig3_cpk()
    print(f"  [3] Cpk 와 오판정       Cpk 1.33 -> "
          f"{(1 - yield_closed(4 / 3)) * 1e6:.0f} ppm · "
          f"%GRR 30 % 에서 버림 {rej[int(np.argmin(np.abs(np.array(pcts) - 30)))]:,.0f} ppm")

    s_ols, s_dem, bias, sd_d, sd_true, sd_a, sd_b, off = fig4_correlation()
    print(f"  [4] 장비 상관           최소제곱 {s_ols:.3f} · "
          f"데밍 {s_dem:.3f} · 평균 차 {bias:+.3f} dB")

    # ── 자체 검산 ───────────────────────────────────────────────────────
    print("\n[자체 검산]")
    ok: list[bool] = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  {'OK ' if cond else 'X  '} {msg}")

    # ① 분산 분해: 참값 되찾기 · 두 방법 대조
    big, _ = make_study(**GAUGES["나쁜 게이지"], n_part=60, n_op=6, n_trial=8,
                        rng=np.random.default_rng(999))
    vb = anova_grr(big)
    g = GAUGES["나쁜 게이지"]
    chk(abs(np.sqrt(vb["rep"]) - g["sd_rep"]) < 0.01,
        f"큰 표본에서 반복성 참값 {g['sd_rep']:.3f} 을 "
        f"{np.sqrt(vb['rep']):.3f} dB 로 되찾는다")
    chk(abs(np.sqrt(vb["part"]) - g["sd_part"]) < 0.05,
        f"부품 산포 참값 {g['sd_part']:.3f} 을 "
        f"{np.sqrt(vb['part']):.3f} dB 로 되찾는다")
    chk(abs(np.sqrt(vb["inter"]) - g["sd_int"]) < 0.02,
        f"교호작용 참값 {g['sd_int']:.3f} 을 "
        f"{np.sqrt(vb['inter']):.3f} dB 로 되찾는다")

    for nm in GAUGES:
        xr = xbar_r_grr(studies[nm])
        an = np.sqrt(vs[nm]["grr"])
        rel = abs(xr["grr"] - an) / an * 100
        chk(rel < 35,
            f"{nm}: 평균-범위 법 {xr['grr']:.3f} vs 분산분석 {an:.3f} dB "
            f"({rel:.0f} % 차)")

    chk(pct_grr_study(vs["좋은 게이지"]) < 10,
        f"좋은 게이지는 산포 대비 "
        f"{pct_grr_study(vs['좋은 게이지']):.1f} % — 합격")
    chk(pct_grr_study(vs["나쁜 게이지"]) > 30,
        f"나쁜 게이지는 산포 대비 "
        f"{pct_grr_study(vs['나쁜 게이지']):.1f} % — 불합격")
    v3 = vs["좋은 게이지 · 좁아진 공정"]
    chk(pct_grr_study(v3) > 10 and pct_grr_tol(v3) < 10,
        f"공정이 좁아지면 같은 게이지가 산포 대비 {pct_grr_study(v3):.1f} % "
        f"(조건부) · 공차 대비 {pct_grr_tol(v3):.1f} % (합격) 로 갈린다")
    chk(abs(pct_grr_tol(vs["좋은 게이지"])
            - pct_grr_tol(v3)) < 1.5,
        "공차 대비 값은 공정이 좁아져도 거의 안 변한다 "
        f"({pct_grr_tol(vs['좋은 게이지']):.1f} -> {pct_grr_tol(v3):.1f} %)")

    # ② ndc 와 %GRR
    for nm in GAUGES:
        direct = 1.41 * np.sqrt(vs[nm]["part"] / vs[nm]["grr"])
        via = ndc_from_pct(pct_grr_study(vs[nm]))
        chk(abs(direct - via) < 1e-6,
            f"{nm}: ndc 를 %GRR 만으로 계산해도 같다 ({direct:.2f})")
    chk(ndc(vs["좋은 게이지"]) >= 5,
        f"좋은 게이지 ndc {ndc(vs['좋은 게이지'])} — 5 이상")
    chk(ndc(vs["나쁜 게이지"]) < 5,
        f"나쁜 게이지 ndc {ndc(vs['나쁜 게이지'])} — 5 미만")
    chk(abs(cross - 27.1) < 0.3,
        f"ndc 5 의 경계는 %GRR {cross:.1f} % — 30 % 가 아니다")
    chk(int(np.floor(ndc_from_pct(30.0))) == 4,
        f"%GRR 정확히 30 % 인 게이지의 ndc 는 "
        f"{int(np.floor(ndc_from_pct(30.0)))} — 두 기준이 어긋난다")

    # ③ 수율과 오판정
    for c in (1.0, 1.33, 1.67):
        cl, m = yield_closed(c), yield_mc(c, n=1_000_000,
                                          rng=np.random.default_rng(int(c * 100)))
        chk(abs(cl - m) < 4e-4,
            f"Cpk {c:.2f}: 닫힌 식 {cl * 1e2:.4f} % vs "
            f"몬테카를로 {m * 1e2:.4f} %")
    # 흔히 인용되는 "63 ppm" 은 Cpk = 4/3 를 끝까지 쓴 값이다. 1.33 으로
    # 반올림해 넣으면 66 ppm 이 나온다 — 자릿수를 말할 때만 같은 값이다.
    chk(abs((1 - yield_closed(4 / 3)) * 1e6 - 63.3) < 0.5,
        f"Cpk 4/3 은 {(1 - yield_closed(4 / 3)) * 1e6:.1f} ppm "
        f"(1.33 로 반올림하면 {(1 - yield_closed(1.33)) * 1e6:.1f} ppm)")
    sd_p = 1.0 / (3 * 1.33)
    for sd_g in (0.05, 0.15):
        q = misjudge_quad(sd_p, sd_g)
        m = misjudge_mc(sd_p, sd_g, n=4_000_000,
                        rng=np.random.default_rng(int(sd_g * 1000)))
        chk(abs(q[0] - m[0]) < 1.5e-4 and abs(q[1] - m[1]) < 1.5e-4,
            f"게이지 {sd_g:.2f}: 수치적분 ({q[0] * 1e6:.0f}, {q[1] * 1e6:.0f}) "
            f"vs 몬테카를로 ({m[0] * 1e6:.0f}, {m[1] * 1e6:.0f}) ppm")
    i30 = int(np.argmin(np.abs(np.array(pcts) - 30)))
    i10 = int(np.argmin(np.abs(np.array(pcts) - 10)))
    chk(rej[i30] > rej[i10] * 5,
        f"%GRR 10 -> 30 % 로 나빠지면 헛되이 버리는 양이 "
        f"{rej[i10]:,.0f} -> {rej[i30]:,.0f} ppm")
    chk(all(r > a for r, a in zip(rej, acc)),
        "언제나 '헛되이 버림' 이 '놓쳐서 보냄' 보다 많다 "
        "(공정 중심이 규격 안쪽이므로)")

    # ④ 상관
    att = attenuation(sd_true, sd_a)
    slopes_o, slopes_d = [], []
    for k in range(400):
        aa, bb = two_testers(n=40, sd_true=sd_true, sd_a=sd_a, sd_b=sd_b,
                             offset=off, rng=np.random.default_rng(3000 + k))
        slopes_o.append(ols_fit(aa, bb)[0])
        slopes_d.append(deming_fit(aa, bb, lam=(sd_b / sd_a) ** 2)[0])
    mo, md = float(np.mean(slopes_o)), float(np.mean(slopes_d))
    chk(abs(mo - att) < 0.02,
        f"최소제곱 기울기 평균 {mo:.3f} = 이론 감쇠 계수 {att:.3f}")
    chk(abs(md - 1.0) < 0.02,
        f"데밍 기울기 평균 {md:.3f} = 참 기울기 1.000")
    chk(mo < 0.95,
        f"최소제곱은 참 기울기 1 을 {mo:.3f} 로 깎는다 — "
        f"이 값으로 보정식을 세우면 안 된다")
    aa, bb = two_testers(sd_true=sd_true, sd_a=sd_a, sd_b=sd_b, offset=off,
                         rng=np.random.default_rng(20260901))
    s_ab = ols_fit(aa, bb)[0]
    s_ba = ols_fit(bb, aa)[0]
    chk(abs(s_ab - 1.0 / s_ba) > 0.05,
        f"최소제곱은 축을 바꾸면 달라진다: B~A {s_ab:.3f} vs "
        f"1/(A~B) {1 / s_ba:.3f}")
    d_ab = deming_fit(aa, bb, lam=(sd_b / sd_a) ** 2)[0]
    d_ba = deming_fit(bb, aa, lam=(sd_a / sd_b) ** 2)[0]
    chk(abs(d_ab - 1.0 / d_ba) < 1e-9,
        f"데밍은 축을 바꿔도 같다: {d_ab:.4f} = 1/{d_ba:.4f}")
    chk(abs(bias - off) < 0.04,
        f"차이 그림의 평균 차 {bias:+.3f} dB 가 참 오프셋 {off:+.2f} dB 를 "
        f"짚는다")
    chk(abs(sd_d - np.hypot(sd_a, sd_b)) < 0.03,
        f"차이의 표준편차 {sd_d:.3f} = 두 장비 오차의 제곱합 "
        f"{np.hypot(sd_a, sd_b):.3f} dB")

    print()
    if not all(ok):
        return 1
    print(f"  검산 {len(ok)}항목 전부 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
