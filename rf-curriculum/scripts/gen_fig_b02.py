#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B02 (시간 영역 — 스코프·프로브·지터) 그림 생성기.

만드는 그림
  B02-1  스코프 대역폭이 상승시간을 얼마나 부풀리는가
  B02-3  프로브 접지 리드 길이가 만드는 링잉
  B02-4  아이 다이어그램 해부
  B02-5  이중 디랙 모델과 배스터브 곡선

지터 쪽은 **닫힌 식과 수치 곡선을 각각 구해 대조**한다. 배스터브에서 읽은
총 지터가 TJ = DJ + 2·Q·RJ 와 맞는지 보는 것이 이 파일의 교차검증이다.

실행: python3 scripts/gen_fig_b02.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.special import erfc, erfcinv

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rf_style as S  # noqa: E402

MOD = "B02"

K_RISE = 0.35            # 단극 응답의 상승시간-대역폭 곱 (10~90 %)

# 프로브 모형
C_TIP_PF = 10.0          # 수동 프로브 팁 용량
R_SRC_OHM = 20.0         # 구동원 저항 (빠른 로직 출력을 가정)
L_PER_MM_NH = 20.0 / 25.4  # 접지 리드 인덕턴스. 계측사 자료의 "인치당 20 nH"
                           # 를 mm 로 옮긴 값 (≈ 0.79 nH/mm)
LEAD_MM = (10.0, 30.0, 100.0)

# 지터 모형
UI_PS = 100.0            # 10 Gb/s
DJ_PS = 20.0             # 이중 디랙 결정성 지터 (peak-to-peak)
RJ_PS = 2.0              # 무작위 지터 rms


# ── 상승시간과 대역폭 ────────────────────────────────────────────────────
def rise_error(ratio):
    """스코프 대역폭이 신호 대역폭의 r 배일 때 상승시간이 부풀려지는 비율.

    t_meas = sqrt(t_sig^2 + t_scope^2) 이고 t = K/BW 이므로
    t_meas/t_sig = sqrt(1 + (BW_sig/BW_scope)^2) = sqrt(1 + 1/r^2).
    신호 상승시간이 얼마든 **비율 r 만으로 정해진다.**
    """
    r = np.asarray(ratio, float)
    return np.sqrt(1.0 + 1.0 / r ** 2) - 1.0


def ratio_for(err):
    """목표 오차를 넘지 않으려면 대역폭 비가 얼마여야 하는가."""
    e = np.asarray(err, float)
    return 1.0 / np.sqrt((1.0 + e) ** 2 - 1.0)


def fig_rise():
    S.setup()
    fig, ax = S.figure(7.0, 4.2)
    r = np.linspace(1.0, 8.0, 400)
    ax.plot(r, rise_error(r) * 100, color=S.COLORS[0], lw=2.2, ls="-")

    for rr, col in ((2.0, S.MUTED), (3.0, S.MUTED), (5.0, S.ACCENT)):
        e = float(rise_error(rr)) * 100
        ax.plot([rr], [e], "o", ms=8,
                color=S.ACCENT if rr == 5 else S.COLORS[1], zorder=6)
        ax.annotate(S.txt(f"{rr:.0f}배 → {e:.1f} %"),
                    xy=(rr, e), xytext=(rr + 0.25, e + 2.5),
                    fontsize=10, fontweight="bold",
                    color=S.ACCENT if rr == 5 else S.COLORS[1])

    S.limit_line(ax, 2.0, S.txt("실무에서 흔히 잡는 한계 2 %"), side="upper")
    ax.set_xlabel(S.txt("스코프 대역폭 / 신호 대역폭"))
    ax.set_ylabel(S.txt("상승시간이 부풀려지는 비율 (%)"))
    ax.set_title(S.txt("그림 B02-1  대역폭이 모자라면 상승시간이 느려 보인다"))
    ax.set_xlim(1, 8)
    ax.set_ylim(0, 45)
    S.save(fig, MOD, "rise_bandwidth")
    return [float(rise_error(x)) for x in (1, 2, 3, 4, 5)]


# ── 접지 리드 링잉 ───────────────────────────────────────────────────────
def ring(lead_mm, t):
    """2차 계단 응답. 리드 인덕턴스와 팁 용량이 만드는 공진이다."""
    L = lead_mm * L_PER_MM_NH * 1e-9
    C = C_TIP_PF * 1e-12
    w0 = 1.0 / np.sqrt(L * C)
    zeta = (R_SRC_OHM / 2.0) * np.sqrt(C / L)
    wd = w0 * np.sqrt(1.0 - zeta ** 2)
    y = 1.0 - np.exp(-zeta * w0 * t) * (
        np.cos(wd * t) + zeta / np.sqrt(1 - zeta ** 2) * np.sin(wd * t))
    return y, w0 / (2 * np.pi), zeta, wd / (2 * np.pi)


def probe_load(c_pf, f_hz, z_src=50.0):
    """프로브가 노드를 얼마나 끌어내리는가.

    프로브를 용량으로만 보고, 등가 소스 임피던스 z_src 와의 분압으로 본다.
    반환: (|Z_probe| Ω, 노드 전압비 dB)
    """
    zp = 1.0 / (2 * np.pi * np.asarray(f_hz, float) * c_pf * 1e-12)
    ratio = zp / np.abs(z_src - 1j * zp)
    return zp, 20 * np.log10(ratio)


def overshoot(zeta):
    return np.exp(-np.pi * zeta / np.sqrt(1.0 - zeta ** 2))


def fig_ring():
    S.setup()
    fig, ax = S.figure(7.2, 4.2)
    t = np.linspace(0, 25e-9, 3000)
    rows = []
    for i, mm in enumerate(LEAD_MM):
        y, f0, z, fd = ring(mm, t)
        os_pct = overshoot(z) * 100
        rows.append((mm, f0, z, fd, os_pct))
        ax.plot(t * 1e9, y, color=S.COLORS[i], ls=S.DASHES[i], lw=1.9,
                label=S.txt(f"{mm:.0f} mm — {fd / 1e6:.0f} MHz, "
                            f"오버슈트 {os_pct:.0f} %"))
    ax.axhline(1.0, color=S.MUTED, ls=":", lw=1.2)
    # 곡선이 지나는 자리를 피해 빈 곳에 놓고 화살표로 가리킨다
    ax.annotate(S.txt("실제 신호는 이 계단이다"), xy=(20.0, 1.0),
                xytext=(13.0, 1.62), fontsize=9, color=S.MUTED,
                arrowprops=dict(arrowstyle="->", color=S.MUTED, lw=1.0))
    ax.set_xlabel(S.txt("시간 (ns)"))
    ax.set_ylabel(S.txt("프로브가 보여주는 파형 (정규화)"))
    ax.set_title(S.txt("그림 B02-2  접지 리드 길이가 파형을 만들어 낸다"))
    ax.legend(loc="lower right", fontsize=9, title=S.txt("접지 리드 길이"))
    ax.set_xlim(0, 25)
    S.save(fig, MOD, "probe_ringing")
    return rows


# ── 아이 다이어그램 ──────────────────────────────────────────────────────
def make_eye(n_bits=6000, sps=128, seed=11):
    """1차 채널을 지난 NRZ 파형과 지터를 섞어 아이를 만든다.

    창을 자를 때 **채널 지연을 빼야** 한다. 안 빼면 눈이 옆으로 밀려
    판정 시점이 교차점 위에 앉는다 (처음에 실제로 그렇게 나왔다).
    """
    rng = np.random.default_rng(seed)
    bits = rng.integers(0, 2, n_bits)
    x = np.repeat(bits * 2.0 - 1.0, sps).astype(float)

    ui_s = UI_PS * 1e-12
    fs = sps / ui_s
    fc = 0.55 / ui_s
    a = np.exp(-2 * np.pi * fc / fs)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = a * acc + (1 - a) * v
        y[i] = acc

    # 1극 저역통과의 50 % 지연(샘플). 계단이 절반까지 오르는 데 걸리는 시간.
    delay = np.log(2.0) / (2 * np.pi * fc / fs)

    seg = []
    span = 2 * sps                     # 2 UI 창
    center_off = sps // 2 + int(round(delay))   # 비트 한가운데 + 채널 지연
    for k in range(4, n_bits - 4):
        j = rng.normal(0.0, RJ_PS * 1e-12) * fs
        s = int(round(k * sps + center_off - span / 2 + j))
        if s < 0 or s + span >= len(y):
            continue
        seg.append(y[s:s + span])
        if len(seg) >= 2000:
            break
    return np.array(seg), sps


def fig_eye():
    S.setup()
    fig, ax = S.figure(7.0, 4.2)
    seg, sps = make_eye()
    # 창의 한가운데가 판정 시점(0 ps)이고 좌우 1 UI 지점이 교차점이다
    t = (np.arange(seg.shape[1]) / sps - 1.0) * UI_PS
    for row in seg[:900]:
        ax.plot(t, row, color=S.COLORS[0], lw=0.35, alpha=0.09)

    mid = seg.shape[1] // 2
    col = seg[:, mid]
    hi, lo = col[col > 0], col[col < 0]
    eye_h = hi.min() - lo.max()
    ax.annotate("", xy=(0, lo.max()), xytext=(0, hi.min()),
                arrowprops=dict(arrowstyle="<->", color=S.ACCENT, lw=1.8))
    ax.text(3.0, 0, S.txt(f"눈 높이\n{eye_h:.2f}"), color=S.ACCENT,
            fontsize=10, fontweight="bold", va="center")

    ax.axvline(0, color=S.MUTED, ls=":", lw=1.0)
    ax.text(0, 1.14, S.txt("판정 시점"), ha="center", fontsize=9,
            color=S.MUTED)
    for xc in (-UI_PS / 2, UI_PS / 2):
        ax.axvline(xc, color=S.MUTED, ls=":", lw=0.8)
    ax.text(UI_PS / 2, -1.18, S.txt("교차점"), ha="center", fontsize=9,
            color=S.MUTED)

    ax.set_xlabel(S.txt("판정 시점 기준 시간 (ps)"))
    ax.set_ylabel(S.txt("전압 (정규화)"))
    ax.set_title(S.txt(f"그림 B02-3  아이 다이어그램 "
                       f"(10 Gb/s, UI {UI_PS:.0f} ps)"))
    ax.set_xlim(-70, 70)
    ax.set_ylim(-1.3, 1.3)
    S.save(fig, MOD, "eye_diagram")
    return eye_h


# ── 이중 디랙과 배스터브 ─────────────────────────────────────────────────
def q_of(ber):
    """BER = 0.5·erfc(Q/√2) 를 Q 에 대해 푼 값."""
    return np.sqrt(2.0) * erfcinv(2.0 * np.asarray(ber, float))


def tj_closed(ber, dj=DJ_PS, rj=RJ_PS):
    """이중 디랙 닫힌 식: TJ(BER) = DJ + 2·Q(BER)·RJ."""
    return dj + 2.0 * q_of(ber) * rj


def bathtub(x, ui=UI_PS, dj=DJ_PS, rj=RJ_PS):
    """양쪽 가장자리의 가우스 꼬리를 더한 곡선.

    왼쪽 가장자리는 평균 +dj/2, 오른쪽은 ui−dj/2 에 있다고 본다.
    닫힌 식과 같은 규약을 쓰므로 두 결과가 맞아야 한다.
    """
    left = 0.5 * erfc((x - dj / 2.0) / (rj * np.sqrt(2.0)))
    right = 0.5 * erfc(((ui - dj / 2.0) - x) / (rj * np.sqrt(2.0)))
    return left + right


def fig_jitter():
    S.setup()
    fig, (ax1, ax2) = S.figure(7.6, 3.8, ncols=2)

    # (a) 이중 디랙 — 두 델타를 가우스로 흐린 것
    x = np.linspace(-25, 25, 1200)
    g = (np.exp(-(x + DJ_PS / 2) ** 2 / (2 * RJ_PS ** 2))
         + np.exp(-(x - DJ_PS / 2) ** 2 / (2 * RJ_PS ** 2)))
    g /= g.max()
    ax1.plot(x, g, color=S.COLORS[0], lw=2.0, ls="-")
    for s in (-1, +1):
        ax1.axvline(s * DJ_PS / 2, color=S.ACCENT, ls="--", lw=1.4)
    ax1.annotate("", xy=(-DJ_PS / 2, 1.12), xytext=(DJ_PS / 2, 1.12),
                 arrowprops=dict(arrowstyle="<->", color=S.ACCENT, lw=1.6))
    ax1.text(0, 1.16, S.txt(f"DJ(δδ) = {DJ_PS:.0f} ps"), ha="center",
             color=S.ACCENT, fontsize=10, fontweight="bold")
    ax1.text(DJ_PS / 2 + 3, 0.5, S.txt(f"σ = RJ = {RJ_PS:.0f} ps"),
             fontsize=9, color=S.COLORS[0])
    ax1.set_xlabel(S.txt("가장자리 위치 (ps)"))
    ax1.set_ylabel(S.txt("확률밀도 (정규화)"))
    ax1.set_title(S.txt("(a) 이중 디랙 모델"), fontsize=10)
    ax1.set_ylim(0, 1.3)

    # (b) 배스터브
    xs = np.linspace(0, UI_PS, 4000)
    ber = bathtub(xs)
    ax2.semilogy(xs, np.clip(ber, 1e-18, 1), color=S.COLORS[0], lw=2.0,
                 ls="-")
    S.plain_log(ax2, axis="y")
    for b, col in ((1e-6, S.MUTED), (1e-12, S.ACCENT)):
        tj = float(tj_closed(b))
        opening = UI_PS - tj
        ax2.axhline(b, color=col, ls=":", lw=1.2)
        ax2.annotate(S.txt(f"BER {b:g}: 열린 폭 {opening:.1f} ps"),
                     xy=(UI_PS / 2, b), ha="center", va="bottom",
                     fontsize=9, color=col, fontweight="bold")
    ax2.set_xlabel(S.txt("판정 시점 (ps)"))
    ax2.set_ylabel(S.txt("비트 오류율"))
    ax2.set_title(S.txt("(b) 배스터브 곡선"), fontsize=10)
    ax2.set_ylim(1e-16, 1)
    ax2.set_xlim(0, UI_PS)

    fig.suptitle(S.txt("그림 B02-5  지터를 낮은 오류율까지 늘여 보는 법"),
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    S.save(fig, MOD, "jitter_bathtub")


def main() -> int:
    errs = fig_rise()
    rows = fig_ring()
    eye_h = fig_eye()
    fig_jitter()

    print("=" * 64)
    print("B02 그림 · 본문 인용값")
    print("=" * 64)
    print("  대역폭 비에 따른 상승시간 오차")
    for r, e in zip((1, 2, 3, 4, 5), errs):
        print(f"    {r}배 → {e * 100:5.1f} %")
    print(f"  오차 2 % 이내로 두려면 신호 대역폭의 "
          f"{float(ratio_for(0.02)):.2f}배")
    print(f"  오차 3 % 이내로 두려면 {float(ratio_for(0.03)):.2f}배")
    print()
    print(f"  프로브 팁 {C_TIP_PF:.0f} pF, 구동원 {R_SRC_OHM:.0f} Ω 일 때")
    for mm, f0, z, fd, os_pct in rows:
        print(f"    접지 리드 {mm:5.0f} mm → 공진 {fd / 1e6:6.1f} MHz, "
              f"ζ {z:.3f}, 오버슈트 {os_pct:4.1f} %")
    print(f"  10 mm 와 100 mm 의 공진 주파수 비 "
          f"{rows[0][3] / rows[2][3]:.2f}배")
    print()
    print("  프로브 용량이 50 Ω 노드를 끌어내리는 양")
    for c in (10.0, 0.8):
        row = []
        for f in (1e8, 5e8, 1e9, 5e9):
            zp, db = probe_load(c, f)
            row.append(f"{f/1e9:g} GHz: {zp:6.1f} Ω / {db:+5.2f} dB")
        print(f"    {c:4.1f} pF  " + " · ".join(row))
    print()
    print(f"  아이 높이 (판정 시점) {eye_h:.3f}")
    for b in (1e-6, 1e-12, 1e-15):
        print(f"  Q({b:g}) = {float(q_of(b)):.4f}, "
              f"TJ = {float(tj_closed(b)):.2f} ps, "
              f"열린 폭 = {UI_PS - float(tj_closed(b)):.2f} ps")

    # ── 자체 검산 ────────────────────────────────────────────────────
    print("-" * 64)
    ok = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  [{'OK ' if cond else '실패'}] {msg}")

    chk(abs(float(rise_error(1.0)) - (np.sqrt(2) - 1)) < 1e-12,
        "대역폭이 같으면 오차 41.4 % (√2−1)")
    chk(abs(float(ratio_for(rise_error(5.0))) - 5.0) < 1e-9,
        "rise_error 와 ratio_for 가 서로의 역함수")
    chk(float(rise_error(8.0)) < float(rise_error(2.0)),
        "대역폭이 넓을수록 오차가 준다")

    # 링잉: 공진 주파수는 1/√L 이므로 리드가 10배면 √10 배 낮아진다
    chk(abs(rows[0][1] / rows[2][1] - np.sqrt(10.0)) < 1e-6,
        "리드 10배 → 공진 1/√10 배 (LC 공진식)")
    chk(rows[0][4] < rows[1][4] < rows[2][4],
        "리드가 길수록 오버슈트가 커진다")

    # 인용한 사례로 모형을 검증한다: 능동 프로브 1.5 pF 에 3~6 인치 리드면
    # 공진이 350~550 MHz 라는 계측사 설명과 맞는가
    for inch, want in ((3.0, 530.0), (6.0, 375.0)):
        L = inch * 25.4 * L_PER_MM_NH * 1e-9
        f = 1.0 / (2 * np.pi * np.sqrt(L * 1.5e-12)) / 1e6
        chk(abs(f - want) < 15.0,
            f"능동 프로브 1.5 pF · {inch:.0f}인치 리드 → {f:.0f} MHz "
            f"(인용 사례 {want:.0f} MHz 급)")
    # 계단 응답의 최대값이 오버슈트 식과 맞는가 (수치 vs 닫힌 식)
    for mm, f0, z, fd, os_pct in rows:
        t = np.linspace(0, 60e-9, 400000)
        y, *_ = ring(mm, t)
        num = (y.max() - 1.0) * 100
        chk(abs(num - os_pct) < 0.5,
            f"{mm:.0f} mm 오버슈트 수치 {num:.1f} % ≈ 식 {os_pct:.1f} %")

    # Q 값이 널리 쓰이는 표와 맞는가
    chk(abs(float(q_of(1e-12)) - 7.0345) < 2e-3,
        f"Q(1e-12) = {float(q_of(1e-12)):.4f} (표준표 7.034)")
    chk(abs(float(q_of(1e-6)) - 4.7534) < 2e-3,
        f"Q(1e-6) = {float(q_of(1e-6)):.4f} (표준표 4.753)")

    # 배스터브에서 읽은 총 지터가 닫힌 식과 맞는가 — 이 파일의 교차검증
    for b in (1e-6, 1e-9, 1e-12, 1e-15):
        xs = np.linspace(0, UI_PS, 2_000_001)
        curve = bathtub(xs)
        left = xs[np.argmax(curve < b)]
        right = xs[len(xs) - 1 - np.argmax(curve[::-1] < b)]
        tj_num = UI_PS - (right - left)
        tj_cf = float(tj_closed(b))
        chk(abs(tj_num - tj_cf) < 0.02,
            f"BER {b:g}: 곡선에서 읽은 TJ {tj_num:.3f} ps "
            f"≈ 식 {tj_cf:.3f} ps")

    chk(float(tj_closed(1e-15)) > float(tj_closed(1e-12)),
        "오류율을 더 낮게 잡으면 총 지터가 커진다 (RJ 는 끝이 없다)")
    chk(abs((float(tj_closed(1e-15)) - float(tj_closed(1e-12)))
            - 2 * RJ_PS * (float(q_of(1e-15)) - float(q_of(1e-12)))) < 1e-9,
        "TJ 차이는 RJ 항에서만 온다 (DJ 는 상수)")
    chk(0.2 < eye_h < 1.9, f"아이 높이 {eye_h:.3f} 가 그럴듯한 범위")

    # 프로브 부하: 용량이 작을수록, 주파수가 낮을수록 덜 끌어내린다
    z10, d10 = probe_load(10.0, 1e9)
    z08, d08 = probe_load(0.8, 1e9)
    chk(abs(z10 - 15.92) < 0.05, f"10 pF 의 1 GHz 임피던스 {z10:.2f} Ω")
    chk(d08 > d10 + 8, f"1 GHz 에서 0.8 pF 가 10 pF 보다 "
                       f"{d08 - d10:.1f} dB 덜 끌어내린다")
    chk(probe_load(10.0, 1e8)[1] > probe_load(10.0, 1e9)[1],
        "같은 프로브라도 주파수가 높으면 더 끌어내린다")

    print()
    if not all(ok):
        return 1
    print(f"  검산 {len(ok)}항목 전부 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
