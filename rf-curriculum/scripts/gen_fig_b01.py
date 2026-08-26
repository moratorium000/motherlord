#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B01 (벤치 방법론) 그림 생성기.

본문에 인용하는 숫자는 전부 여기서 계산해 출력한다. 손으로 적으면 본문과
그림이 어긋난다 — M17 에서 실제로 세 줄 중 두 줄이 틀렸던 적이 있다.

만드는 그림
  B01-2  워밍업 드리프트가 만드는 가짜 개선
  B01-3  재연결 반복성과 "몇 번 재야 하는가"

실행: python3 scripts/gen_fig_b01.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rf_style as S  # noqa: E402

MOD = "B01"

# ── 드리프트 모형 ────────────────────────────────────────────────────────
# 증폭기 이득이 켠 뒤 지수적으로 올라간다. 최종 상승분과 시상수는 실제
# 소자마다 다르므로, 본문에서는 "이런 모양"으로만 쓰고 결론은 비율로 낸다.
DRIFT_TOTAL_DB = 0.40      # 워밍업이 끝나면 이득이 이만큼 올라간다
DRIFT_TAU_MIN = 8.0        # 시상수 (분)

T_BEFORE = 2.0             # 성급한 사람이 "변경 전"을 재는 시각
T_AFTER = 15.0             # 변경 후 다시 재는 시각
T_WARM = 30.0              # 기다린 사람이 "변경 전"을 재는 시각
T_WARM2 = 43.0             # 같은 간격을 두고 "변경 후"


def gain(t_min):
    """켠 뒤 t분에서의 이득 상승분(dB). 변경의 효과는 0으로 둔다."""
    return DRIFT_TOTAL_DB * (1.0 - np.exp(-np.asarray(t_min, float)
                                          / DRIFT_TAU_MIN))


# ── 반복성 모형 ──────────────────────────────────────────────────────────
SIGMA_DB = 0.030           # 커넥터를 다시 조일 때마다 생기는 산포(가정)
Z95 = 1.959963985          # 양측 95 %


def n_needed(delta_db, sigma=SIGMA_DB, z=Z95):
    """양쪽 각 n회 재서 차이 delta 를 95 %로 가려내려면 n 이 얼마여야 하는가.

    두 평균의 차의 표준오차는 sigma*sqrt(2/n) 이므로
        delta > z * sigma * sqrt(2/n)   →   n > 2 (z sigma / delta)^2
    """
    d = np.asarray(delta_db, float)
    return 2.0 * (z * sigma / d) ** 2


def fig_drift():
    S.setup()
    fig, ax = S.figure(7.2, 4.3)

    t = np.linspace(0, 60, 600)
    ax.plot(t, gain(t), color=S.COLORS[0], lw=2.0, ls="-",
            label=S.txt("실제 이득 (변경의 효과는 0)"))

    gb, ga = float(gain(T_BEFORE)), float(gain(T_AFTER))
    gw, gw2 = float(gain(T_WARM)), float(gain(T_WARM2))

    # 성급한 측정 두 점
    ax.plot([T_BEFORE, T_AFTER], [gb, ga], "o", ms=8,
            color=S.ACCENT, zorder=6)
    ax.annotate(S.txt(f"변경 전 {gb:+.3f} dB"), xy=(T_BEFORE, gb),
                xytext=(T_BEFORE + 1.2, gb + 0.035), color=S.ACCENT,
                fontsize=9, fontweight="bold")
    ax.annotate(S.txt(f"변경 후 {ga:+.3f} dB"), xy=(T_AFTER, ga),
                xytext=(T_AFTER + 1.2, ga + 0.022), color=S.ACCENT,
                fontsize=9, fontweight="bold")
    ax.annotate("", xy=(T_AFTER, ga), xytext=(T_AFTER, gb),
                arrowprops=dict(arrowstyle="<->", color=S.ACCENT, lw=1.6))
    ax.text(T_AFTER - 0.6, (ga + gb) / 2,
            S.txt(f"{ga - gb:+.3f} dB\n\"좋아졌다\""),
            ha="right", va="center", color=S.ACCENT,
            fontsize=10, fontweight="bold")

    # 기다린 뒤 측정 두 점
    ax.plot([T_WARM, T_WARM2], [gw, gw2], "s", ms=7,
            color=S.COLORS[2], zorder=6)
    ax.annotate(S.txt(f"30분 기다린 뒤 두 번 재면 차이는 "
                      f"{gw2 - gw:+.3f} dB"),
                xy=(T_WARM2, gw2), xytext=(26, 0.135),
                color=S.COLORS[2], fontsize=9, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=S.COLORS[2], lw=1.2))

    ax.axvspan(0, 3 * DRIFT_TAU_MIN, color="#F2F2F2", zorder=0)
    ax.text(3 * DRIFT_TAU_MIN / 2, 0.435,
            S.txt(f"워밍업 구간 (시상수 {DRIFT_TAU_MIN:.0f}분)"),
            ha="center", fontsize=9, color=S.MUTED)

    ax.set_xlabel(S.txt("장비를 켠 뒤 지난 시간 (분)"))
    ax.set_ylabel(S.txt("이득 상승분 (dB)"))
    ax.set_title(S.txt("그림 B01-3  워밍업이 만드는 가짜 개선"))
    ax.set_xlim(0, 60)
    ax.set_ylim(-0.02, 0.46)
    ax.legend(loc="lower right", fontsize=9)
    S.save(fig, MOD, "warmup_illusion")
    return gb, ga, gw, gw2


def fig_repeat():
    S.setup()
    fig, (ax1, ax2) = S.figure(7.4, 3.6, ncols=2)

    # (a) 재연결 20회 분포 vs 주장하는 개선량
    rng = np.random.default_rng(20260822)
    n = 20
    before = rng.normal(0.0, SIGMA_DB, n)
    after = rng.normal(0.03, SIGMA_DB, n)      # 실제로 0.03 dB 좋아진 경우
    bins = np.linspace(-0.10, 0.14, 25)
    ax1.hist(before, bins=bins, alpha=0.75, color=S.COLORS[0],
             label=S.txt("변경 전 20회"))
    ax1.hist(after, bins=bins, alpha=0.65, color=S.COLORS[1],
             label=S.txt("변경 후 20회"))
    ax1.axvline(0.0, color=S.MUTED, ls=":", lw=1.2)
    ax1.axvline(0.03, color=S.ACCENT, ls="--", lw=1.6)
    ax1.text(0.031, ax1.get_ylim()[1] * 0.92, S.txt("진짜 차이\n0.03 dB"),
             color=S.ACCENT, fontsize=9, fontweight="bold", va="top")
    ax1.set_xlabel(S.txt("삽입손실 편차 (dB)"))
    ax1.set_ylabel(S.txt("횟수"))
    ax1.set_title(S.txt(f"(a) 재연결 산포 σ = {SIGMA_DB:.3f} dB"), fontsize=10)
    ax1.legend(fontsize=8, loc="upper left")

    # (b) 몇 번 재야 가려낼 수 있는가
    d = np.linspace(0.005, 0.12, 300)
    ax2.plot(d, n_needed(d), color=S.COLORS[0], lw=2.0, ls="-")
    ax2.set_yscale("log")
    S.plain_log(ax2, axis="y")
    for dd in (0.03, 0.05, 0.10):
        nn = np.ceil(n_needed(dd))
        ax2.plot([dd], [n_needed(dd)], "o", color=S.ACCENT, ms=7, zorder=6)
        ax2.annotate(S.txt(f"{dd:.2f} dB → {nn:.0f}회"),
                     xy=(dd, n_needed(dd)), xytext=(dd + 0.004,
                                                   n_needed(dd) * 1.5),
                     fontsize=9, color=S.ACCENT, fontweight="bold")
    ax2.set_xlabel(S.txt("가려내고 싶은 차이 (dB)"))
    ax2.set_ylabel(S.txt("한쪽당 필요한 측정 횟수"))
    ax2.set_title(S.txt("(b) 필요한 반복 횟수 (95 %)"), fontsize=10)
    ax2.set_ylim(0.7, 400)

    fig.suptitle(S.txt("그림 B01-2  한 번 재고 판단하면 안 되는 이유"),
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    S.save(fig, MOD, "repeatability")
    return before, after


def main() -> int:
    gb, ga, gw, gw2 = fig_drift()
    before, after = fig_repeat()

    print("=" * 62)
    print("B01 그림 · 본문 인용값")
    print("=" * 62)
    print(f"  워밍업 총 상승 {DRIFT_TOTAL_DB:.2f} dB, 시상수 "
          f"{DRIFT_TAU_MIN:.0f}분")
    print(f"  {T_BEFORE:.0f}분에 재면 {gb:+.4f} dB, "
          f"{T_AFTER:.0f}분에 재면 {ga:+.4f} dB")
    print(f"  → 아무것도 안 고쳤는데 {ga - gb:+.4f} dB 좋아진 것처럼 보인다")
    print(f"  {T_WARM:.0f}분 기다린 뒤 같은 간격으로 재면 "
          f"{gw2 - gw:+.4f} dB")
    print(f"  줄어든 비율 {(ga - gb) / (gw2 - gw):.0f}배")
    print()
    print(f"  재연결 산포 σ = {SIGMA_DB:.3f} dB 일 때 필요한 측정 횟수")
    for dd in (0.02, 0.03, 0.05, 0.10):
        print(f"    {dd:.2f} dB 를 가려내려면 한쪽당 "
              f"{np.ceil(n_needed(dd)):.0f}회")

    # ── 자체 검산 ────────────────────────────────────────────────────
    print("-" * 62)
    ok = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  [{'OK ' if cond else '실패'}] {msg}")

    chk(abs(gain(0)) < 1e-12, "t=0 에서 상승분 0")
    chk(abs(float(gain(1e6)) - DRIFT_TOTAL_DB) < 1e-9,
        f"충분히 지나면 {DRIFT_TOTAL_DB} dB 에 수렴")
    # 시상수의 정의: 1τ 지나면 63.2 %
    chk(abs(float(gain(DRIFT_TAU_MIN)) / DRIFT_TOTAL_DB - (1 - np.exp(-1)))
        < 1e-12, "1τ 에서 63.2 % 도달 (시상수 정의)")
    chk(ga - gb > 0.2, f"성급한 측정의 가짜 개선이 {ga - gb:.3f} dB 로 큼")
    chk(gw2 - gw < 0.01, f"기다린 뒤에는 {gw2 - gw:.4f} dB 로 사라짐")

    # n 계산을 두 방식으로 대조한다: 닫힌 식 vs 몬테카를로
    rng = np.random.default_rng(7)
    delta, trials = 0.05, 40000
    n_cf = int(np.ceil(n_needed(delta)))
    hits = 0
    for _ in range(trials):
        a = rng.normal(0.0, SIGMA_DB, n_cf)
        b = rng.normal(delta, SIGMA_DB, n_cf)
        # 표준편차를 안다고 보고 z 검정 (닫힌 식과 같은 가정)
        se = SIGMA_DB * np.sqrt(2.0 / n_cf)
        if (b.mean() - a.mean()) / se > Z95:
            hits += 1
    power = hits / trials
    chk(0.45 <= power <= 0.60,
        f"n={n_cf} 에서 검출력 {power:.1%} — 경계값이라 절반 안팎이 맞다")

    # 실제로 2배 더 재면 검출력이 크게 오르는지
    hits2 = 0
    for _ in range(trials):
        a = rng.normal(0.0, SIGMA_DB, 2 * n_cf)
        b = rng.normal(delta, SIGMA_DB, 2 * n_cf)
        se = SIGMA_DB * np.sqrt(2.0 / (2 * n_cf))
        if (b.mean() - a.mean()) / se > Z95:
            hits2 += 1
    chk(hits2 / trials > power + 0.15,
        f"횟수를 2배로 하면 검출력 {hits2 / trials:.1%} 로 오름")

    chk(n_needed(0.03) > n_needed(0.06),
        "가려낼 차이가 작을수록 더 많이 재야 함")
    # 4배 규칙: delta 를 절반으로 하면 n 은 4배
    chk(abs(n_needed(0.025) / n_needed(0.05) - 4.0) < 1e-9,
        "차이가 절반이면 횟수는 4배 (제곱 관계)")

    print()
    if not all(ok):
        return 1
    print(f"  검산 {len(ok)}항목 전부 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
