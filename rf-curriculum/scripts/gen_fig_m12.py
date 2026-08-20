#!/usr/bin/env python3
"""
M12 (시스템 예산 설계) 데이터 그림 생성기
=========================================

    python3 scripts/gen_fig_m12.py

출력: assets/M12/*.svg

이 모듈은 커리큘럼 이론의 정점이므로, 캐스케이드 계산을 서로 다른 두
경로(잡음인자 / 잡음온도)로 각각 구현해 결과가 같은지 검산한다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt

import rf_style as S

T0 = 290.0
BW = 20e6          # 채널 대역폭 [Hz]
SNR_REQ = 2.0      # 복조에 필요한 SNR [dB]
SENS_REQ = -95.0   # 요구 감도 [dBm]
BLOCK_REQ = -30.0  # 차단 시험의 간섭 세기 (톤 하나당) [dBm]


def db(x):
    return 10 * np.log10(x)


def un(x):
    return 10 ** (np.asarray(x, dtype=float) / 10)


# ── 예제 수신 체인 (이름, 이득 dB, NF dB, IIP3 dBm) ────────────────
HIGH_GAIN = [
    ("케이블·스위치", -0.5, 0.5, 100.0),
    ("RF 대역통과 필터", -1.0, 1.0, 100.0),
    ("LNA", 22.0, 0.8, 15.0),
    ("대역 필터", -2.5, 2.5, 100.0),
    ("믹서", -7.0, 7.0, 18.0),
    ("IF 필터", -3.0, 3.0, 100.0),
    ("IF 증폭기", 25.0, 4.0, 10.0),
]

LOW_GAIN = [
    ("케이블·스위치", -0.5, 0.5, 100.0),
    ("RF 대역통과 필터", -1.0, 1.0, 100.0),
    ("LNA 바이패스", -1.0, 1.0, 100.0),
    ("대역 필터", -2.5, 2.5, 100.0),
    ("믹서", -7.0, 7.0, 18.0),
    ("IF 필터", -3.0, 3.0, 100.0),
    ("IF 증폭기(이득 낮춤)", 12.0, 4.0, 10.0),
]


def cascade(chain):
    """단별 누적값과 기여도를 함께 돌려준다."""
    F, G, inv = 1.0, 1.0, 0.0
    rows = []
    for name, g_db, nf_db, iip3 in chain:
        f_contrib = (un(nf_db) - 1.0) / G          # 이 단이 F 에 보탠 양
        i_contrib = G / un(iip3)                   # 이 단이 1/IIP3 에 보탠 양
        F += f_contrib
        inv += i_contrib
        G *= un(g_db)
        rows.append(dict(name=name, g_db=g_db, nf_db=nf_db, iip3=iip3,
                         cum_g=db(G), cum_nf=db(F), cum_iip3=-db(inv),
                         f_contrib=f_contrib, i_contrib=i_contrib))
    return rows


def cascade_by_temperature(chain):
    """완전히 다른 경로(잡음온도)로 같은 NF 를 계산한다 — 교차검증용."""
    te, g = 0.0, 1.0
    for _, g_db, nf_db, _ in chain:
        te += T0 * (un(nf_db) - 1.0) / g
        g *= un(g_db)
    return db(1.0 + te / T0)


def totals(chain):
    r = cascade(chain)[-1]
    return r["cum_g"], r["cum_nf"], r["cum_iip3"]


def noise_floor(nf_db, bw=BW):
    return -174.0 + db(bw) + nf_db


def sensitivity(nf_db, snr_req=SNR_REQ, bw=BW):
    return noise_floor(nf_db, bw) + snr_req


def im3_input(p_int, iip3):
    """간섭 두 개가 만드는 IM3 를 입력 환산으로."""
    return 3 * p_int - 2 * iip3


# ══════════════════════════════════════ M12-2: Friis 기여도
def m12_friis():
    S.setup()
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.8))
    fig.patch.set_facecolor("white")

    for ax, chain, title in ((axes[0], HIGH_GAIN, "고이득 모드 (LNA 22 dB)"),
                             (axes[1], LOW_GAIN, "저이득 모드 (LNA 바이패스)")):
        rows = cascade(chain)
        tot = sum(r["f_contrib"] for r in rows)
        share = [100 * r["f_contrib"] / tot for r in rows]
        names = [r["name"] for r in rows]
        cols = [S.ACCENT if s > 25 else S.COLORS[0] for s in share]
        y = np.arange(len(names))
        ax.barh(y, share, color=cols, alpha=0.88, height=0.6)
        for i, s_ in enumerate(share):
            ax.text(s_ + 1.2, i, f"{s_:.1f} %", va="center", fontsize=9,
                    color=cols[i], fontweight="bold")
        ax.set_yticks(y)
        ax.set_yticklabels(names, fontsize=8.8)
        ax.invert_yaxis()
        ax.set_xlim(0, max(share) * 1.30)
        ax.set_xlabel("전체 잡음인자 증가분에서 차지하는 비율 (%)")
        ax.set_title(f"{title}   NF = {totals(chain)[1]:.2f} dB", fontsize=10.5)
        ax.grid(axis="x", alpha=0.4)

    axes[0].annotate("앞의 세 단이 64 %를 차지한다.\n"
                     "다만 믹서와 IF 필터의 손실로 누적 이득이 다시 떨어져\n"
                     "IF 증폭기의 기여가 22 %로 되살아난다 — 이것도 Friis 다.",
                     xy=(0.30, 0.44), xycoords="axes fraction", fontsize=8.8,
                     color=S.ACCENT, fontweight="bold", ha="left",
                     bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=1.0))

    fig.suptitle("그림 M12-2  Friis 기여도 — 잡음은 앞단이 지배한다",
                 fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M12", "friis")
    return dict(high=[(r["name"], r["f_contrib"]) for r in cascade(HIGH_GAIN)],
                nf_high=totals(HIGH_GAIN)[1], nf_low=totals(LOW_GAIN)[1])


# ══════════════════════════════════════ M12-3: 캐스케이드 IP3 기여도
def m12_ip3():
    fig, ax = S.figure(9.0, 4.8)
    rows = cascade(HIGH_GAIN)
    tot = sum(r["i_contrib"] for r in rows)
    share = [100 * r["i_contrib"] / tot for r in rows]
    names = [r["name"] for r in rows]
    cols = [S.ACCENT if s > 25 else S.COLORS[0] for s in share]
    y = np.arange(len(names))
    ax.barh(y, share, color=cols, alpha=0.88, height=0.6)
    for i, s_ in enumerate(share):
        ax.text(s_ + 1.2, i, f"{s_:.1f} %", va="center", fontsize=9,
                color=cols[i], fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, max(share) * 1.32)
    ax.set_xlabel("전체 1/IIP3 에서 차지하는 비율 (%)")
    ax.set_title("그림 M12-3  캐스케이드 IP3 기여도 — 선형성은 뒷단이 지배한다"
                 f"   (IIP3 = {totals(HIGH_GAIN)[2]:.1f} dBm)")
    ax.annotate("앞에서 이득을 얻은 만큼\n뒷단이 큰 신호를 받는다\n"
                "→ 선형성은 뒷단이 지배한다",
                xy=(0.46, 0.24), xycoords="axes fraction", fontsize=9.4,
                color=S.ACCENT, fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=1.0))
    ax.grid(axis="x", alpha=0.4)
    S.save(fig, "M12", "ip3")
    return dict(share=list(zip(names, share)), iip3=totals(HIGH_GAIN)[2])


# ══════════════════════════════════════ M12-4: 이득 배분 트레이드오프
def sweep_lna(gains):
    out = []
    for g in gains:
        ch = [list(c) for c in HIGH_GAIN]
        ch[2][1] = float(g)
        _, nf, iip3 = totals(ch)
        nfl = noise_floor(nf)
        out.append(dict(g=float(g), nf=nf, iip3=iip3, sens=sensitivity(nf),
                        sfdr=2.0 / 3.0 * (iip3 - nfl),
                        p_block=(nfl + 2 * iip3) / 3.0))
    return out


def m12_tradeoff():
    fig, ax = S.figure(9.2, 5.6)
    gains = np.arange(4, 30.01, 0.5)
    sw = sweep_lna(gains)

    ax.plot(gains, [r["sens"] for r in sw], color=S.COLORS[0], lw=2.6, ls="-",
            label="감도 (낮을수록 좋다)")
    ax.plot(gains, [r["p_block"] for r in sw], color=S.COLORS[1], lw=2.6,
            ls="--", label="견딜 수 있는 간섭 세기 (높을수록 좋다)")

    ax.axhline(SENS_REQ, color=S.COLORS[0], ls=":", lw=1.8)
    ax.text(4.3, SENS_REQ + 1.6, f"감도 요구 {SENS_REQ:.0f} dBm", fontsize=9,
            color=S.COLORS[0], fontweight="bold")
    ax.axhline(BLOCK_REQ, color=S.COLORS[1], ls=":", lw=1.8)
    ax.text(4.3, BLOCK_REQ + 1.6, f"차단 요구 {BLOCK_REQ:.0f} dBm", fontsize=9,
            color=S.COLORS[1], fontweight="bold")

    g_sens = next(r["g"] for r in sw if r["sens"] <= SENS_REQ)
    g_block = max(r["g"] for r in sw if r["p_block"] >= BLOCK_REQ)
    ax.axvspan(4, g_block, color=S.COLORS[1], alpha=0.10)
    ax.axvspan(g_sens, 30, color=S.COLORS[0], alpha=0.10)
    ax.axvline(g_sens, color=S.COLORS[0], lw=1.4)
    ax.axvline(g_block, color=S.COLORS[1], lw=1.4)

    ax.annotate(f"감도를 만족하려면\nLNA 이득 ≥ {g_sens:.0f} dB",
                xy=(g_sens, SENS_REQ), xytext=(g_sens + 1.4, -73),
                fontsize=9.2, color=S.COLORS[0], fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.COLORS[0], alpha=0.97, lw=1.0),
                arrowprops=dict(arrowstyle="->", color=S.COLORS[0], lw=1.3))
    ax.annotate(f"차단을 만족하려면\nLNA 이득 ≤ {g_block:.0f} dB",
                xy=(g_block, BLOCK_REQ), xytext=(5.4, -46),
                fontsize=9.2, color=S.COLORS[1], fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.COLORS[1], alpha=0.97, lw=1.0),
                arrowprops=dict(arrowstyle="->", color=S.COLORS[1], lw=1.3))

    ax.text(17.0, -110,
            "두 요구를 동시에 만족하는 이득이 없다.\n"
            "→ 한 가지 이득으로는 못 푼다. AGC 로 모드를 나눈다.",
            fontsize=10, color=S.ACCENT, fontweight="bold", ha="center",
            bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=1.2))

    ax.set_xlabel("LNA 이득 (dB)")
    ax.set_ylabel("전력 (dBm)")
    ax.set_title("그림 M12-4  이득 배분 — 감도와 선형성이 반대 방향으로 당긴다")
    ax.set_xlim(4, 30)
    ax.set_ylim(-118, -18)
    ax.grid(alpha=0.4)
    ax.legend(fontsize=9.2, loc="upper right")
    S.save(fig, "M12", "tradeoff")
    return dict(g_sens=g_sens, g_block=g_block,
                sw={int(r["g"]): r for r in sw if r["g"].is_integer()})


# ══════════════════════════════════════ M12-5: 레벨 다이어그램
def m12_level():
    S.setup()
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 5.6))
    fig.patch.set_facecolor("white")

    for ax, chain, title in ((axes[0], HIGH_GAIN, "고이득 모드"),
                             (axes[1], LOW_GAIN, "저이득 모드")):
        rows = cascade(chain)
        names = ["안테나"] + [r["name"] for r in rows]
        p_in = -95.0
        sig = [p_in] + [p_in + r["cum_g"] for r in rows]
        ktb = -174.0 + db(BW)
        noi = [ktb] + [ktb + r["cum_nf"] + r["cum_g"] for r in rows]
        x = np.arange(len(names))

        ax.plot(x, sig, color=S.COLORS[0], lw=2.6, marker="o", ms=6,
                label="신호")
        ax.plot(x, noi, color=S.ACCENT, lw=2.6, ls="--", marker="s", ms=5,
                label="잡음 (채널 대역폭 안)")
        ax.fill_between(x, noi, sig, color=S.COLORS[0], alpha=0.12)

        for i in (0, len(names) - 1):
            ax.annotate("", xy=(x[i], sig[i]), xytext=(x[i], noi[i]),
                        arrowprops=dict(arrowstyle="<->", color=S.COLORS[2],
                                        lw=1.8))
            ax.text(x[i] + (0.16 if i == 0 else -0.16),
                    (sig[i] + noi[i]) / 2, f"SNR\n{sig[i]-noi[i]:.1f} dB",
                    fontsize=8.8, color=S.COLORS[2], fontweight="bold",
                    va="center", ha="left" if i == 0 else "right")

        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=26, ha="right", fontsize=8.4)
        ax.set_title(f"{title}   NF {totals(chain)[1]:.2f} dB", fontsize=10.5)
        ax.grid(alpha=0.4)
    for ax in axes:
        ax.set_ylabel("전력 (dBm)")
        ax.set_ylim(-118, -44)
    axes[0].legend(fontsize=9, loc="upper left")
    axes[1].annotate("저이득 모드는 −95 dBm 을 받을 수 없다 (SNR 이 음수).\n"
                     "강한 신호가 있을 때만 쓰는 모드이기 때문이다.",
                     xy=(0.50, 0.06), xycoords="axes fraction", fontsize=8.8,
                     color=S.ACCENT, fontweight="bold", ha="center",
                     bbox=dict(fc="white", ec=S.ACCENT, alpha=0.97, lw=1.0))

    fig.suptitle("그림 M12-6  레벨 다이어그램 — 신호와 잡음의 간격이 곧 SNR "
                 "(입력 −95 dBm)", fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M12", "level")
    r = cascade(HIGH_GAIN)[-1]
    ktb = -174.0 + db(BW)
    return dict(snr_in=-95.0 - ktb, snr_out=-95.0 - ktb - r["cum_nf"],
                degradation=r["cum_nf"])


# ══════════════════════════════════════ M12-6: 감도 계산 폭포
def m12_sensitivity():
    fig, ax = S.figure(8.8, 5.2)
    nf = totals(HIGH_GAIN)[1]
    steps = [("열잡음 밀도\n−174 dBm/Hz", -174.0),
             ("대역폭 20 MHz\n+10·log₁₀(B)", db(BW)),
             (f"수신기 잡음지수\n+{nf:.2f} dB", nf),
             (f"요구 SNR\n+{SNR_REQ:.0f} dB", SNR_REQ)]
    vals = [v for _, v in steps]
    run = np.cumsum(vals)
    start = np.concatenate([[0.0], run[:-1]])

    for i, ((lab, v), s0) in enumerate(zip(steps, start)):
        col = S.ACCENT if v < 0 else S.COLORS[1]
        ax.bar(i, v, bottom=s0, color=col, alpha=0.85, width=0.6, zorder=3)
        ax.text(i, s0 + v + (2.4 if v > 0 else -5.0), f"{v:+.2f}",
                ha="center", fontsize=9.2, color=col, fontweight="bold")
        if i:
            ax.plot([i - 0.3, i + 0.3], [s0] * 2, color=S.MUTED, lw=1.0,
                    ls=":")
    ax.bar(len(vals), run[-1] + 190, bottom=-190, color=S.COLORS[0],
           alpha=0.85, width=0.6, zorder=3)
    ax.text(len(vals), run[-1] + 2.8, f"{run[-1]:.2f} dBm", ha="center",
            fontsize=10, color=S.COLORS[0], fontweight="bold")

    ax.axhline(SENS_REQ, color=S.INK, ls="--", lw=1.8)
    ax.text(-0.44, SENS_REQ + 3.0, f"요구 감도 {SENS_REQ:.0f} dBm",
            fontsize=9.4, color=S.INK, fontweight="bold", va="bottom",
            bbox=dict(fc="white", ec=S.INK, alpha=0.95, lw=0.9))
    ax.annotate("", xy=(len(vals) + 0.62, run[-1]),
                xytext=(len(vals) + 0.62, SENS_REQ),
                arrowprops=dict(arrowstyle="<->", color=S.COLORS[2], lw=2.0))
    ax.text(len(vals) + 0.52, (run[-1] + SENS_REQ) / 2,
            f"마진\n{SENS_REQ - run[-1]:.2f} dB", ha="right", va="center",
            fontsize=9.6, color=S.COLORS[2], fontweight="bold",
            bbox=dict(fc="white", ec=S.COLORS[2], alpha=0.97, lw=1.0))

    ax.set_xticks(range(len(steps) + 1))
    ax.set_xticklabels([l for l, _ in steps] + ["감도"], fontsize=8.6)
    ax.set_ylabel("전력 (dBm)")
    ax.set_title("그림 M12-5  감도는 네 항의 덧셈이다")
    ax.set_ylim(-190, -58)
    ax.set_xlim(-0.75, len(steps) + 0.95)
    ax.grid(axis="y", alpha=0.4)
    S.save(fig, "M12", "sensitivity")
    return dict(nf=nf, sens=run[-1], margin=SENS_REQ - run[-1])


if __name__ == "__main__":
    fr = m12_friis()
    i3 = m12_ip3()
    td = m12_tradeoff()
    lv = m12_level()
    se = m12_sensitivity()

    gh, nfh, iph = totals(HIGH_GAIN)
    gl, nfl, ipl = totals(LOW_GAIN)

    print("\n[본문에 인용할 계산값]")
    print(f"  고이득 모드: 이득 {gh:.2f} dB, NF {nfh:.2f} dB, IIP3 {iph:.2f} dBm")
    print(f"    잡음 바닥 {noise_floor(nfh):.2f} dBm, "
          f"감도 {sensitivity(nfh):.2f} dBm "
          f"(요구 대비 {SENS_REQ - sensitivity(nfh):+.2f} dB)")
    print(f"    간섭 {BLOCK_REQ:.0f} dBm 두 개 -> "
          f"IM3 {im3_input(BLOCK_REQ, iph):.1f} dBm "
          f"(잡음 바닥 대비 {im3_input(BLOCK_REQ, iph) - noise_floor(nfh):+.1f} dB)")
    print(f"  저이득 모드: 이득 {gl:.2f} dB, NF {nfl:.2f} dB, IIP3 {ipl:.2f} dBm")
    print(f"    잡음 바닥 {noise_floor(nfl):.2f} dBm, "
          f"감도 {sensitivity(nfl):.2f} dBm")
    print(f"    간섭 {BLOCK_REQ:.0f} dBm 두 개 -> "
          f"IM3 {im3_input(BLOCK_REQ, ipl):.1f} dBm "
          f"(잡음 바닥 대비 {im3_input(BLOCK_REQ, ipl) - noise_floor(nfl):+.1f} dB)")
    print(f"  LNA 이득 요구 구간: 감도 >= {td['g_sens']:.0f} dB, "
          f"차단 <= {td['g_block']:.0f} dB  -> 겹치는 구간 없음")
    tot_f = sum(v for _, v in fr["high"])
    print("  Friis 기여도(고이득):",
          {n: f"{100*v/tot_f:.1f} %" for n, v in fr["high"][:3]})
    print("  IP3 기여도(뒤 세 단):",
          {n: f"{v:.1f} %" for n, v in i3["share"][-3:]})
    print(f"  SNR: 입력 {lv['snr_in']:.2f} dB -> 출력 {lv['snr_out']:.2f} dB "
          f"(저하 {lv['degradation']:.2f} dB)")

    print("\n[자체 검산]")
    ok = []
    ok.append(("Friis 와 잡음온도 경로의 NF 가 일치 (고이득)",
               abs(cascade_by_temperature(HIGH_GAIN) - nfh) < 1e-9))
    ok.append(("Friis 와 잡음온도 경로의 NF 가 일치 (저이득)",
               abs(cascade_by_temperature(LOW_GAIN) - nfl) < 1e-9))
    passive = [("a", -1.0, 1.0, 100.0), ("b", -2.0, 2.0, 100.0),
               ("c", -3.0, 3.0, 100.0)]
    ok.append(("수동 소자만의 체인은 NF = 총 손실 (6 dB)",
               abs(totals(passive)[1] - 6.0) < 1e-9))
    single = [("only", 20.0, 3.0, 10.0)]
    ok.append(("한 단짜리 체인의 NF·IIP3 는 그 단의 값 그대로",
               abs(totals(single)[1] - 3.0) < 1e-9
               and abs(totals(single)[2] - 10.0) < 1e-9))
    huge = [("big", 60.0, 1.0, 10.0), ("tail", 0.0, 30.0, 30.0)]
    ok.append(("앞단 이득이 아주 크면 뒷단 잡음이 사라진다",
               abs(totals(huge)[1] - 1.0) < 0.01))
    ok.append(("SNR 저하량이 곧 시스템 NF",
               abs((lv["snr_in"] - lv["snr_out"]) - nfh) < 1e-9))
    ok.append(("감도 = 잡음바닥 + 요구 SNR",
               abs(sensitivity(nfh) - (noise_floor(nfh) + SNR_REQ)) < 1e-9))
    ok.append(("감도 폭포 차트의 합이 감도와 일치",
               abs(se["sens"] - sensitivity(nfh)) < 1e-9))
    ok.append(("고이득 모드가 감도 요구를 만족", sensitivity(nfh) <= SENS_REQ))
    ok.append(("고이득 모드가 차단 요구에는 실패",
               im3_input(BLOCK_REQ, iph) > noise_floor(nfh)))
    ok.append(("저이득 모드가 차단 요구를 만족",
               im3_input(BLOCK_REQ, ipl) < noise_floor(nfl)))
    ok.append(("두 요구를 동시에 만족하는 단일 LNA 이득이 없다",
               td["g_sens"] > td["g_block"]))
    ok.append(("대역폭을 1/4 로 줄이면 감도가 6.02 dB 좋아진다",
               abs((sensitivity(nfh, bw=BW) - sensitivity(nfh, bw=BW / 4))
                   - 6.0206) < 0.001))
    for name, v in ok:
        print(f"  [{'OK ' if v else 'FAIL'}] {name}")
    print(f"\n{'전부 통과' if all(v for _, v in ok) else '검산 실패 항목 있음'}")
