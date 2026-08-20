#!/usr/bin/env python3
"""
M10 (안테나와 전파) 데이터 그림 생성기
======================================

    python3 scripts/gen_fig_m10.py

출력: assets/M10/*.svg
각 함수가 본문 인용값을 돌려주고 __main__ 에서 자체 검산까지 출력한다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt

import rf_style as S

C = 299792458.0


# ══════════════════════════════════════ 공통 계산
def fspl_db(d_m, f_hz):
    """자유공간 경로손실 [dB]."""
    return 20 * np.log10(4 * np.pi * np.asarray(d_m) * np.asarray(f_hz) / C)


def dipole_pattern(theta):
    """반파장 다이폴의 전계 패턴 F(theta). theta 는 축으로부터의 각 [rad]."""
    st = np.sin(theta)
    out = np.zeros_like(theta)
    m = np.abs(st) > 1e-9
    out[m] = np.cos(np.pi / 2 * np.cos(theta[m])) / st[m]
    return np.abs(out)


def array_factor(phi, n=8, d_lambda=0.5):
    """균일 선형 배열의 배열인자. phi 는 배열축에서 잰 각 [rad]."""
    psi = 2 * np.pi * d_lambda * np.cos(phi)
    num = np.sin(n * psi / 2)
    den = n * np.sin(psi / 2)
    out = np.ones_like(phi)
    m = np.abs(den) > 1e-12
    out[m] = np.abs(num[m] / den[m])
    return out


def first_sidelobe(ang, patt_db):
    """첫 부엽의 (각도[도], 레벨[dB]).

    '주엽에서 일정 각도 떨어진 곳의 최댓값' 으로 찾으면 주엽의 치맛자락을
    부엽으로 잘못 집는다 (실제로 −8.4 dB 가 나왔다). 국소 최대를 찾아야 한다.
    """
    k = int(np.argmax(patt_db))
    peaks = [i for i in range(1, len(patt_db) - 1)
             if patt_db[i] > patt_db[i - 1] and patt_db[i] >= patt_db[i + 1]
             and abs(i - k) > 2]
    if not peaks:
        return None, None
    j = max(peaks, key=lambda i: patt_db[i])
    return np.rad2deg(ang[j]), patt_db[j]


def hpbw_deg(ang, patt_db):
    """−3 dB 빔폭 [도]. patt_db 는 최댓값이 0 dB 로 정규화된 값."""
    k = int(np.argmax(patt_db))
    lo = hi = k
    while lo > 0 and patt_db[lo] > -3.0:
        lo -= 1
    while hi < len(patt_db) - 1 and patt_db[hi] > -3.0:
        hi += 1
    return np.rad2deg(ang[hi] - ang[lo])


def directivity_dbi(theta, patt):
    """축 대칭 패턴의 지향성 [dBi]. D = 4pi Umax / P_rad."""
    u = patt ** 2
    p = 2 * np.pi * np.trapezoid(u * np.sin(theta), theta)
    return 10 * np.log10(4 * np.pi * u.max() / p)


# ══════════════════════════════════════ M10-2: 방사 패턴
def m10_pattern():
    S.setup()
    fig = plt.figure(figsize=(10.6, 4.8))
    fig.patch.set_facecolor("white")

    th = np.linspace(1e-6, np.pi - 1e-6, 4000)
    dip = dipole_pattern(th)
    dip_db = 20 * np.log10(dip / dip.max())
    arr = array_factor(th, 8, 0.5)
    arr_db = 20 * np.log10(np.maximum(arr, 1e-6))

    # 왼쪽: 극좌표 (등방·다이폴·배열)
    ax = fig.add_subplot(1, 2, 1, projection="polar")
    full = np.concatenate([th, th + np.pi])
    for patt_db, name, col, ls in ((np.zeros_like(th), "등방성 (0 dBi 기준)",
                                    S.MUTED, ":"),
                                   (dip_db, "반파장 다이폴", S.COLORS[0], "-"),
                                   (arr_db, "8소자 배열", S.COLORS[1], "--")):
        r = np.clip(patt_db, -30, 0) + 30
        ax.plot(full, np.concatenate([r, r[::-1]]), lw=2.0, ls=ls, color=col,
                label=name)
    ax.set_theta_zero_location("N")
    ax.set_rlim(0, 32)
    ax.set_rticks([0, 10, 20, 30])
    ax.set_yticklabels(["−30", "−20", "−10", "0 dB"], fontsize=8)
    ax.set_thetagrids(range(0, 360, 30), fontsize=8)
    ax.set_title("방사 패턴 (같은 최댓값으로 정규화)", fontsize=10.5, pad=16)
    ax.legend(fontsize=8.0, loc="lower center", bbox_to_anchor=(0.5, -0.26))

    # 오른쪽: 직교좌표 컷 + 빔폭·부엽 표시
    ax = fig.add_subplot(1, 2, 2)
    deg = np.rad2deg(th)
    ax.plot(deg, dip_db, color=S.COLORS[0], lw=2.2, ls="-", label="반파장 다이폴")
    ax.plot(deg, arr_db, color=S.COLORS[1], lw=2.2, ls="--", label="8소자 배열")
    ax.axhline(-3, color=S.MUTED, ls=":", lw=1.4)
    ax.text(178, -2.6, "−3 dB", ha="right", fontsize=8.6, color=S.MUTED)

    bw_d = hpbw_deg(th, dip_db)
    bw_a = hpbw_deg(th, arr_db)
    sll_deg, sll = first_sidelobe(th, arr_db)

    ax.annotate(f"다이폴 빔폭 {bw_d:.0f}도", xy=(90 - bw_d / 2, -3),
                xytext=(6, -9), fontsize=9, color=S.COLORS[0],
                fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.COLORS[0], alpha=0.96, lw=0.9),
                arrowprops=dict(arrowstyle="->", color=S.COLORS[0], lw=1.2))
    ax.annotate(f"배열 빔폭 {bw_a:.0f}도", xy=(90 + bw_a / 2, -3),
                xytext=(126, -6), fontsize=9, color=S.COLORS[1],
                fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.COLORS[1], alpha=0.96, lw=0.9),
                arrowprops=dict(arrowstyle="->", color=S.COLORS[1], lw=1.2))
    ax.annotate(f"첫 부엽 {sll:.1f} dB\n(균일 급전 배열의 고유값)",
                xy=(sll_deg, sll), xytext=(124, -22), fontsize=9,
                color=S.ACCENT, fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.96, lw=0.9),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))

    ax.set_xlim(0, 180)
    ax.set_ylim(-40, 3)
    ax.set_xticks(range(0, 181, 30))
    ax.set_xlabel("각도 (도)")
    ax.set_ylabel("정규화 이득 (dB)")
    ax.set_title("같은 것을 직교좌표로 펴 보면", fontsize=10.5)
    ax.grid(alpha=0.45)
    ax.legend(fontsize=8.8, loc="lower right")

    fig.suptitle("그림 M10-2  방사 패턴 — 지향성이란 에너지를 한쪽으로 모으는 것",
                 fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M10", "pattern")
    return dict(d_dipole=directivity_dbi(th, dip),
                d_array=directivity_dbi(th, arr),
                bw_dipole=bw_d, bw_array=bw_a, sll=sll, sll_deg=sll_deg)


# ══════════════════════════════════════ M10-5: 경로손실
def m10_fspl():
    fig, ax = S.figure(8.2, 5.0)
    d = np.logspace(0, 6, 800)
    for f, name, ls in ((433e6, "433 MHz", "-."),
                        (900e6, "900 MHz", ":"),
                        (2.44e9, "2.44 GHz", "-"),
                        (28e9, "28 GHz (밀리미터파)", "--")):
        ax.plot(d, fspl_db(d, f), lw=2.2, ls=ls, label=name)

    for d0, f0, lab in ((20.0, 2.44e9, "Wi-Fi 실내 20 m"),
                        (1e6, 2.2e9, "LEO 위성 1000 km")):
        v = fspl_db(d0, f0)
        ax.plot([d0], [v], "o", color=S.ACCENT, ms=9, zorder=9)
        ax.annotate(f"{lab}\n{v:.0f} dB", xy=(d0, v),
                    xytext=(d0 * 0.06, v + 22), fontsize=9, color=S.ACCENT,
                    fontweight="bold", ha="left",
                    bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=1.0),
                    arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.3))

    ax.annotate("", xy=(1e3, fspl_db(1e3, 2.44e9)),
                xytext=(2e3, fspl_db(2e3, 2.44e9)),
                arrowprops=dict(arrowstyle="<->", color=S.INK, lw=1.6))
    ax.text(2.2e3, fspl_db(1.4e3, 2.44e9) - 12,
            "거리가 2배 → +6 dB\n주파수가 2배 → +6 dB\n(둘 다 진폭이 절반)",
            fontsize=9, color=S.INK, ha="left",
            bbox=dict(fc="white", ec=S.GRID, alpha=0.97))

    ax.set_xscale("log")
    ax.set_xticks([1, 10, 1e2, 1e3, 1e4, 1e5, 1e6])
    ax.set_xticklabels(["1 m", "10 m", "100 m", "1 km", "10 km", "100 km",
                        "1000 km"])
    ax.xaxis.set_minor_formatter(lambda *_: "")
    ax.set_xlabel("거리")
    ax.set_ylabel("자유공간 경로손실 (dB)")
    ax.set_title("그림 M10-5  자유공간 경로손실 — 거리와 주파수가 각각 6 dB/옥타브")
    ax.set_ylim(20, 200)
    ax.grid(which="both", alpha=0.35)
    ax.legend(fontsize=9, loc="lower right")
    S.save(fig, "M10", "fspl")
    return dict(wifi=fspl_db(20.0, 2.44e9), leo=fspl_db(1e6, 2.2e9),
                const=20 * np.log10(4 * np.pi * 1e3 * 1e6 / C))


# ══════════════════════════════════════ M10-3: VSWR 는 얼마나 나쁜가
def m10_vswr():
    S.setup()
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.5))
    fig.patch.set_facecolor("white")

    v = np.linspace(1.0, 6.0, 800)
    g = (v - 1) / (v + 1)
    rl = -20 * np.log10(np.maximum(g, 1e-9))
    refl = g ** 2 * 100
    ml = -10 * np.log10(1 - g ** 2)

    ax = axes[0]
    ax.plot(v, refl, color=S.COLORS[0], lw=2.4, ls="-", label="반사되는 전력 (%)")
    ax2 = ax.twinx()
    ax2.plot(v, rl, color=S.COLORS[1], lw=2.0, ls="--")
    ax2.set_ylabel("반사손실 (dB)", color=S.COLORS[1])
    ax2.tick_params(axis="y", labelcolor=S.COLORS[1])
    ax2.set_ylim(0, 40)
    ax2.grid(False)
    ax.set_xlabel("VSWR")
    ax.set_ylabel("반사되는 전력 (%)", color=S.COLORS[0])
    ax.tick_params(axis="y", labelcolor=S.COLORS[0])
    ax.set_xlim(1, 6)
    ax.set_ylim(0, 55)
    ax.set_title("VSWR 를 세 가지 언어로", fontsize=10.5)
    ax.grid(alpha=0.45)
    ax2.annotate("반사손실 (오른쪽 축)", xy=(3.4, -20 * np.log10(0.545)),
                 fontsize=9, color=S.COLORS[1], ha="left")

    ax = axes[1]
    S.emph(ax, v, ml, color=S.COLORS[2])
    for vv in (1.5, 2.0, 3.0, 5.0):
        gg = (vv - 1) / (vv + 1)
        mm = -10 * np.log10(1 - gg ** 2)
        ax.plot([vv], [mm], "o", color=S.ACCENT, ms=8, zorder=8)
        ax.annotate(f"VSWR {vv:.1f}\n{mm:.2f} dB", xy=(vv, mm),
                    xytext=(vv + 0.34, mm - 0.30), fontsize=8.8,
                    color=S.ACCENT, fontweight="bold", ha="left",
                    bbox=dict(fc="white", ec="none", alpha=0.9))
    ax.text(1.12, 3.05, "VSWR 2:1 이 나쁘다는 말은\n전력으로는 0.5 dB 라는 뜻이다.\n"
                        "겁먹을 값이 아니다 — 진짜 문제는\n반사가 아니라 그 뒤의 것들이다.",
            fontsize=9.0, color=S.INK, ha="left", va="top",
            bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=1.0))
    ax.set_xlabel("VSWR")
    ax.set_ylabel("정합손실 (dB)")
    ax.set_xlim(1, 6)
    ax.set_ylim(0, 3.9)
    ax.set_title("그래서 실제로 잃는 전력은?", fontsize=10.5)
    ax.grid(alpha=0.45)

    fig.suptitle("그림 M10-3  VSWR 2:1 은 정말 얼마나 나쁜가", fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M10", "vswr")
    return {f"{vv}": dict(g=(vv - 1) / (vv + 1),
                          rl=-20 * np.log10((vv - 1) / (vv + 1)),
                          refl=((vv - 1) / (vv + 1)) ** 2 * 100,
                          ml=-10 * np.log10(1 - ((vv - 1) / (vv + 1)) ** 2))
            for vv in (1.2, 1.5, 2.0, 3.0, 5.0)}


# ══════════════════════════════════════ M10-4: 근거리장 / 원거리장
def m10_nearfield():
    fig, ax = S.figure(8.2, 5.0)
    d_ap = np.logspace(-2, 0.6, 500)
    for f, name, ls in ((900e6, "900 MHz", ":"),
                        (2.44e9, "2.44 GHz", "-"),
                        (6e9, "6 GHz", "-."),
                        (28e9, "28 GHz", "--")):
        lam = C / f
        ax.plot(d_ap, 2 * d_ap ** 2 / lam, lw=2.2, ls=ls, label=name)

    cases = [(0.1, 2.44e9, "휴대폰 안테나\n(10 cm)", S.COLORS[2]),
             (0.3, 2.44e9, "Wi-Fi 공유기\n(30 cm)", S.COLORS[0]),
             (1.0, 28e9, "5G 밀리미터파 배열\n(1 m)", S.ACCENT)]
    for d0, f0, lab, col in cases:
        lam = C / f0
        y = 2 * d0 ** 2 / lam
        ax.plot([d0], [y], "o", color=col, ms=10, zorder=9)
        ax.annotate(f"{lab}\n원거리장 {y:.2f} m 부터",
                    xy=(d0, y), xytext=(d0 * 0.14, y * 3.2), fontsize=9,
                    color=col, fontweight="bold", ha="left",
                    bbox=dict(fc="white", ec=col, alpha=0.97, lw=1.0),
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.3))

    ax.axhspan(10, 1e4, color=S.ACCENT, alpha=0.10)
    ax.text(0.011, 300, "이 위쪽은 보통 실험실에\n들어가지 않는 거리\n"
                        "→ CATR 이나 근거리장 스캐닝이 필요",
            fontsize=9, color=S.ACCENT, fontweight="bold", va="top",
            bbox=dict(fc="white", ec=S.ACCENT, alpha=0.95, lw=0.9))

    ax.set_xscale("log")
    ax.set_yscale("log")
    S.plain_log(ax, axis="y")
    ax.set_xticks([0.01, 0.03, 0.1, 0.3, 1.0, 3.0])
    ax.set_xticklabels(["1 cm", "3 cm", "10 cm", "30 cm", "1 m", "3 m"])
    ax.xaxis.set_minor_formatter(lambda *_: "")
    ax.set_xlabel("안테나의 최대 치수 D")
    ax.set_ylabel("원거리장 시작 거리  2D²/λ  (m)")
    ax.set_title("그림 M10-4  원거리장은 얼마나 멀리서 시작하는가")
    ax.set_ylim(1e-3, 1e4)
    ax.grid(which="both", alpha=0.35)
    ax.legend(fontsize=9, loc="lower right")
    S.save(fig, "M10", "nearfield")
    return {lab.split("\n")[0]: 2 * d0 ** 2 / (C / f0)
            for d0, f0, lab, _ in cases}


# ══════════════════════════════════════ M10-6: 링크 버짓 폭포 차트
WIFI = [("송신 전력", +20.0), ("송신 안테나 이득", +2.0),
        ("자유공간 경로손실 (20 m)", None), ("벽 2개 통과", -14.0),
        ("수신 안테나 이득", +2.0)]
LEO = [("송신 전력 (1 W)", +30.0), ("위성 안테나 이득", +6.0),
       ("자유공간 경로손실 (1000 km)", None),
       ("지향·편파·대기 손실", -3.0), ("지상국 안테나 이득", +25.0)]


def _waterfall(ax, steps, floor_dbm, floor_label, title, fspl):
    labels, vals = [], []
    for name, v in steps:
        labels.append(name)
        vals.append(-fspl if v is None else v)
    run = np.cumsum(vals)
    start = np.concatenate([[0.0], run[:-1]])
    for i, (lab, v) in enumerate(zip(labels, vals)):
        col = S.COLORS[2] if v > 0 else S.ACCENT
        ax.bar(i, v, bottom=start[i], color=col, alpha=0.85, width=0.62,
               zorder=3)
        ax.text(i, start[i] + v + (2.5 if v > 0 else -5.5),
                f"{v:+.0f}", ha="center", fontsize=9, color=col,
                fontweight="bold")
        if i:
            ax.plot([i - 0.31, i + 0.31], [start[i]] * 2, color=S.MUTED,
                    lw=1.0, ls=":")
    ax.bar(len(vals), run[-1] - (-140), bottom=-140, color=S.COLORS[0],
           alpha=0.85, width=0.62, zorder=3)
    ax.text(len(vals), run[-1] + 3, f"{run[-1]:.0f} dBm", ha="center",
            fontsize=9.6, color=S.COLORS[0], fontweight="bold")
    labels.append("수신 전력")

    ax.axhline(floor_dbm, color=S.INK, ls="--", lw=1.8)
    ax.text(-0.62, floor_dbm + 2.0, floor_label, ha="left", va="bottom",
            fontsize=8.8, color=S.INK, fontweight="bold",
            bbox=dict(fc="white", ec=S.INK, alpha=0.95, lw=0.9))
    xm = len(vals) + 0.75
    ax.annotate("", xy=(xm, run[-1]), xytext=(xm, floor_dbm),
                arrowprops=dict(arrowstyle="<->", color=S.COLORS[1], lw=2.0))
    ax.text(xm - 0.12, (run[-1] + floor_dbm) / 2,
            f"마진\n{run[-1]-floor_dbm:.1f} dB", ha="right", va="center",
            fontsize=9.6, color=S.COLORS[1], fontweight="bold",
            bbox=dict(fc="white", ec=S.COLORS[1], alpha=0.97, lw=1.0))

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=28, ha="right", fontsize=8.2)
    ax.set_ylabel("전력 (dBm)")
    ax.set_title(title, fontsize=10.5)
    ax.grid(axis="y", alpha=0.4)
    ax.set_xlim(-0.75, len(labels) + 0.55)
    return run[-1]


def m10_linkbudget():
    S.setup()
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 5.4))
    fig.patch.set_facecolor("white")

    # 바닥값은 본문·실습과 같은 방식으로 계산한다. 데이터시트의 '감도' 를
    # 그대로 쓰면 본문 표와 마진이 어긋난다 (실제로 5 dB 어긋났었다).
    l_wifi = fspl_db(20.0, 2.44e9)
    nf_w, bw_w, snr_w = 6.0, 20e6, 20.0
    noise_w = -174 + 10 * np.log10(bw_w) + nf_w
    floor_w = noise_w + snr_w
    pr_wifi = _waterfall(axes[0], WIFI, floor_w,
                         f"필요 수신 전력 {floor_w:.1f} dBm\n"
                         f"(잡음 {noise_w:.1f} + 요구 SNR {snr_w:.0f} dB)",
                         "① Wi-Fi 실내 링크 (2.44 GHz, 20 m, 벽 2개)",
                         l_wifi)
    axes[0].set_ylim(-95, 30)

    l_leo = fspl_db(1e6, 2.2e9)
    nf, bw = 1.5, 1e6
    floor = -174 + 10 * np.log10(bw) + nf + 6.0     # 잡음 + 요구 SNR 6 dB
    pr_leo = _waterfall(axes[1], LEO, floor,
                        f"필요 수신 전력 {floor:.1f} dBm\n"
                        f"(잡음 {-174+10*np.log10(bw)+nf:.1f} + 요구 SNR 6 dB)",
                        "② LEO 위성 하향 링크 (2.2 GHz, 1000 km)", l_leo)
    axes[1].set_ylim(-130, 45)

    fig.suptitle("그림 M10-6  링크 버짓 — 더하고 빼면 끝난다", fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M10", "linkbudget")
    return dict(wifi_fspl=l_wifi, wifi_pr=pr_wifi,
                wifi_floor=floor_w, wifi_noise=noise_w,
                wifi_margin=pr_wifi - floor_w,
                leo_fspl=l_leo, leo_pr=pr_leo, leo_floor=floor,
                leo_margin=pr_leo - floor,
                leo_noise=-174 + 10 * np.log10(bw) + nf)


if __name__ == "__main__":
    pt = m10_pattern()
    fs = m10_fspl()
    vs = m10_vswr()
    nf_ = m10_nearfield()
    lb = m10_linkbudget()

    print("\n[본문에 인용할 계산값]")
    print(f"  다이폴: 지향성 {pt['d_dipole']:.2f} dBi, 빔폭 {pt['bw_dipole']:.1f}도")
    print(f"  8소자 배열: 지향성 {pt['d_array']:.2f} dBi, "
          f"빔폭 {pt['bw_array']:.1f}도, "
          f"첫 부엽 {pt['sll']:.2f} dB @ {pt['sll_deg']:.1f}도")
    print(f"  FSPL 상수(km·MHz 기준) {fs['const']:.2f} dB")
    print(f"  FSPL: Wi-Fi 20 m {fs['wifi']:.2f} dB, LEO 1000 km {fs['leo']:.2f} dB")
    print("  VSWR:", {k: f"RL {v['rl']:.2f} dB / 반사 {v['refl']:.1f}% / "
                         f"정합손실 {v['ml']:.3f} dB" for k, v in vs.items()})
    print("  원거리장 시작 거리:", {k: f"{v:.2f} m" for k, v in nf_.items()})
    print(f"  Wi-Fi 링크: 수신 {lb['wifi_pr']:.1f} dBm, 마진 {lb['wifi_margin']:.1f} dB")
    print(f"  LEO 링크: 수신 {lb['leo_pr']:.1f} dBm, 잡음 {lb['leo_noise']:.1f} dBm, "
          f"필요 {lb['leo_floor']:.1f} dBm, 마진 {lb['leo_margin']:.1f} dB")

    print("\n[자체 검산]")
    ok = []
    ok.append(("반파장 다이폴 지향성 = 2.15 dBi",
               abs(pt["d_dipole"] - 2.15) < 0.05))
    ok.append(("반파장 다이폴 빔폭 = 78도", abs(pt["bw_dipole"] - 78) < 1.5))
    # N = 8 의 정확한 첫 부엽은 −12.8 dB 다. 흔히 인용되는 −13.2 dB 는
    # N -> 무한대 극한값이므로 그대로 쓰면 틀린다.
    ok.append(("8소자 균일 배열 첫 부엽 = −12.8 dB",
               abs(pt["sll"] + 12.8) < 0.2))
    ok.append(("8소자 배열 빔폭 = 약 12.8도",
               abs(pt["bw_array"] - 12.8) < 1.0))
    ok.append(("FSPL 상수 32.44 dB", abs(fs["const"] - 32.44) < 0.02))
    ok.append(("거리 2배 -> +6.02 dB",
               abs((fspl_db(2e3, 2.44e9) - fspl_db(1e3, 2.44e9)) - 6.02) < 0.01))
    ok.append(("주파수 2배 -> +6.02 dB",
               abs((fspl_db(1e3, 4.88e9) - fspl_db(1e3, 2.44e9)) - 6.02) < 0.01))
    ok.append(("VSWR 2:1 의 정합손실 = 0.51 dB",
               abs(vs["2.0"]["ml"] - 0.512) < 0.005))
    ok.append(("VSWR 2:1 의 반사손실 = 9.54 dB",
               abs(vs["2.0"]["rl"] - 9.54) < 0.02))
    ok.append(("VSWR 2:1 에서 반사되는 전력 = 11.1 %",
               abs(vs["2.0"]["refl"] - 11.11) < 0.05))
    ok.append(("28 GHz·1 m 배열의 원거리장이 100 m 를 넘는다",
               nf_["5G 밀리미터파 배열"] > 100))
    ok.append(("Wi-Fi 링크 마진이 양수", lb["wifi_margin"] > 0))
    ok.append(("LEO 링크 마진이 양수", lb["leo_margin"] > 0))
    ok.append(("링크식 검산: Pr = Pt+Gt+Gr−FSPL−기타",
               abs(lb["leo_pr"] - (30 + 6 + 25 - lb["leo_fspl"] - 3)) < 1e-9))
    for name, v in ok:
        print(f"  [{'OK ' if v else 'FAIL'}] {name}")
    print(f"\n{'전부 통과' if all(v for _, v in ok) else '검산 실패 항목 있음'}")
