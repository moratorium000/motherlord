#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""심화 캡스톤 그림 생성기.

만드는 그림
  ACAP-1  받은 보드에 심어 둔 다섯 문제 — 사양에서 얼마나 벗어나 있나
  ACAP-2  P1 · 잡음지수 추적 — 정합망이 어디에 맞춰져 있는가
  ACAP-3  P2 · 부하가 바뀌면 ACLR 이 어떻게 되는가
  ACAP-4  P3 · 케이블 길이가 만드는 10.7 dB
  ACAP-5  P4 · 다투는 이유와 떨어지는 이유

숫자는 전부 `scripts/adv_capstone_check.py` 가 계산한다. 이 파일은 그 값을
**그리기만** 한다 — 같은 값을 두 번 계산하면 언젠가 어긋나기 때문이다.

실행: python3 scripts/gen_fig_advcap.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rf_style as S  # noqa: E402
import adv_capstone_check as AC  # noqa: E402
import gen_fig_b05 as B05  # noqa: E402
import gen_fig_b07 as B07  # noqa: E402

MOD = "AdvCapstone"


# ══ 그림 1 · 다섯 문제의 크기 ═══════════════════════════════════════════
def fig1_problems(p1, p2, p3, p4, p5):
    """다섯 문제를 한 장에.

    단위가 dB 인 것과 % 인 것을 **한 축에 섞지 않는다.** 섞으면 34 %p 짜리
    막대 하나가 1.3 dB 짜리 막대들을 안 보이게 만든다 — 처음 그렸을 때
    실제로 그렇게 됐다.
    """
    bd = p1["이 보드 (Γms · 이득 최대점)"]

    fig, (ax1, ax2) = S.figure(12.6, 4.6, ncols=2,
                               gridspec_kw=dict(width_ratios=[1.3, 1]))

    # (a) dB 로 재는 세 문제 — **초과량 하나로** 그린다.
    # 측정값과 한도를 나란히 그렸더니 ACLR 에서 부호가 꼬였다. ACLR 은
    # 작아질수록(0 에 가까울수록) 나쁘고 나머지 둘은 커질수록 나쁘다.
    # "얼마나 넘었나" 는 셋 다 같은 방향이라 이것만 그리는 편이 안전하다.
    db_rows = [
        ("① 수신 잡음지수 (B05)", bd["cascade_nf_db"] - AC.SPEC["nf_max_db"],
         f"{bd['cascade_nf_db']:.2f} dB  (사양 {AC.SPEC['nf_max_db']:.1f})"),
        ("② 인접 채널 누설비 (B04)",
         p2["worst_ant"] - AC.SPEC["aclr_max_dbc"],
         f"{p2['worst_ant']:.1f} dBc  (사양 {AC.SPEC['aclr_max_dbc']:.0f})"),
        ("③ 방사 240 MHz (B07)",
         p3["lab"]["dbuv_m"] - p3["limit_dbuv_m"],
         f"{p3['lab']['dbuv_m']:.1f} dBµV/m  (한도 "
         f"{p3['limit_dbuv_m']:.0f})"),
    ]
    y = np.arange(len(db_rows))[::-1]
    ax1.barh(y, [r[1] for r in db_rows], height=0.5, color=S.ACCENT)
    for yy, (name, over, detail) in zip(y, db_rows):
        ax1.text(over + 0.2, yy, f"  +{over:.2f} dB 초과", va="center",
                 fontsize=9.5, color=S.ACCENT, fontweight="bold")
        ax1.text(0.985, yy - 0.34, detail,
                 transform=ax1.get_yaxis_transform(), ha="right", va="center",
                 fontsize=9, color=S.MUTED)
    ax1.set_yticks(y)
    ax1.set_yticklabels([r[0] for r in db_rows], fontsize=9.5)
    ax1.set_xlim(0, 11.5)
    ax1.set_ylim(-0.75, len(db_rows) - 0.45)   # 아래 설명줄이 잘리지 않게
    ax1.set_xlabel("사양·한도를 넘어선 양 (dB)")
    ax1.set_title("(a) dB 로 재는 세 문제")

    # (b) 비율로 재는 두 문제
    pct_rows = [
        ("④ 게이지 R&R\n공차 대비 %GRR\n(B11)", p4["pct_tol"], 30.0,
         "불합격 한계"),
        ("⑤ 수율 손실\n(B12)", 100 - p5["yield_pct"], 1.0, "목표"),
    ]
    x = np.arange(len(pct_rows))
    ax2.bar(x - 0.19, [r[1] for r in pct_rows], 0.36, color=S.ACCENT,
            label="이 보드")
    ax2.bar(x + 0.19, [r[2] for r in pct_rows], 0.36, color=S.COLORS[0],
            label="한계·목표")
    for i, (name, meas, lim, lab) in enumerate(pct_rows):
        ax2.text(i - 0.19, meas + 1.5, f"{meas:.1f}", ha="center", fontsize=9,
                 color=S.ACCENT, fontweight="bold")
        ax2.text(i + 0.19, lim + 1.5, f"{lim:.0f}\n({lab})", ha="center",
                 fontsize=8.5, color=S.COLORS[0], linespacing=1.3)
    ax2.set_xticks(x)
    ax2.set_xticklabels([r[0] for r in pct_rows], fontsize=9,
                        linespacing=1.35)
    ax2.set_ylabel("%")
    ax2.set_ylim(0, 78)
    ax2.set_title("(b) 비율로 재는 두 문제")
    ax2.legend(loc="upper right", fontsize=9)

    S.save(fig, MOD, "problems")
    rows = [
        ("① 수신 잡음지수", bd["cascade_nf_db"] - AC.SPEC["nf_max_db"],
         "dB 초과", "B05"),
        ("② 인접 채널 누설비", p2["worst_ant"] - AC.SPEC["aclr_max_dbc"],
         "dB 초과", "B04"),
        ("③ 방사 (240 MHz)", p3["lab"]["dbuv_m"] - p3["limit_dbuv_m"],
         "dB 초과", "B07"),
        ("④ 게이지 R&R", p4["pct_tol"] - 30.0, "%p 초과 (한계 30 %)", "B11"),
        ("⑤ 수율 손실", 100 - p5["yield_pct"], "%p (목표 99 %)", "B12"),
    ]
    return rows


# ══ 그림 2 · P1 잡음지수 추적 ═══════════════════════════════════════════
def fig2_nf(p1, gms):
    fig, (ax1, ax2) = S.figure(12.6, 4.8, ncols=2,
                               gridspec_kw=dict(width_ratios=[1, 1.1]))

    # (a) Γ 평면 위의 세 점과 잡음 등고선
    B05.smith_grid(ax1)
    for f_db, c in ((0.9, S.COLORS[5]), (1.5, S.COLORS[0]),
                    (2.3, S.COLORS[4])):
        ctr, rad = B05.noise_circle(f_db)
        B05.draw_circle(ax1, ctr, rad, color=c, lw=1.6, ls="-")
        # 원의 꼭대기에 붙이면 세 이름표가 겹친다. 원마다 반지름이 다르므로
        # 왼쪽 아래(225°) 로 내리면 자연히 벌어진다.
        ax1.annotate(f"F = {f_db:.1f} dB",
                     xy=(ctr.real - rad * 0.707, ctr.imag - rad * 0.707),
                     xytext=(-2, -2), textcoords="offset points",
                     fontsize=8.5, color=c, ha="right", va="top")
    pts = [("Γopt (데이터시트)", B05.G_OPT, S.COLORS[2], (10, 10)),
           ("50 Ω", 0 + 0j, S.MUTED, (10, -14)),
           ("Γms (이 보드)", gms, S.ACCENT, (-8, 12))]
    for name, g, c, off in pts:
        ax1.plot([g.real], [g.imag], "o", ms=9, color=c, ls="none", zorder=6)
        ax1.annotate(name, xy=(g.real, g.imag), xytext=off,
                     textcoords="offset points", fontsize=9, color=c,
                     fontweight="bold")
    ax1.set_aspect("equal")
    ax1.set_xlim(-1.15, 1.15)
    ax1.set_ylim(-1.15, 1.15)
    ax1.set_xticks([])
    ax1.set_yticks([])
    ax1.grid(False)
    ax1.set_title("(a) 정합망은 어디에 맞춰져 있나")

    # (b) 세 경우의 사슬 잡음지수와 가용이득
    names = list(p1)
    short = ["Γopt\n(데이터시트)", "50 Ω\n(그냥 물림)", "Γms\n(이 보드)"]
    x = np.arange(3)
    nf = [p1[n]["cascade_nf_db"] for n in names]
    ga = [p1[n]["gain_avail_db"] for n in names]
    b = ax2.bar(x - 0.19, nf, 0.36, color=S.COLORS[0], label="사슬 잡음지수")
    ax2.bar(x + 0.19, ga, 0.36, color=S.COLORS[2], label="가용이득")
    for xx, v in zip(x - 0.19, nf):
        ax2.text(xx, v + 0.25, f"{v:.2f}", ha="center", fontsize=9)
    for xx, v in zip(x + 0.19, ga):
        ax2.text(xx, v + 0.25, f"{v:.2f}", ha="center", fontsize=9)
    # limit_line 은 이름표를 오른쪽 끝에 붙이는데, 그 자리에 16 dB 짜리
    # 이득 막대가 서 있어 글자가 묻힌다. 여기서는 왼쪽에 직접 적는다.
    ax2.axhline(AC.SPEC["nf_max_db"], color=S.ACCENT, lw=1.6, ls="--",
                zorder=5)
    # 막대 오른쪽에 빈 자리를 만들어 이름표를 거기 둔다.
    ax2.set_xlim(-0.55, 3.35)
    ax2.text(3.3, AC.SPEC["nf_max_db"] + 0.25,
             f"잡음지수 사양 {AC.SPEC['nf_max_db']:.1f} dB", fontsize=9,
             color=S.ACCENT, fontweight="bold", va="bottom", ha="right")
    ax2.annotate("사양 초과", xy=(x[2] - 0.19, nf[2]), xytext=(-6, 14),
                 textcoords="offset points", ha="right", fontsize=9,
                 color=S.ACCENT, fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    ax2.set_xticks(x)
    ax2.set_xticklabels(short, fontsize=9, linespacing=1.3)
    ax2.set_ylabel("dB")
    ax2.set_ylim(0, 19)
    ax2.set_title("(b) 잡음을 1.46 dB 내주고 이득을 4.88 dB 샀다")
    ax2.legend(loc="upper left", fontsize=9)

    S.save(fig, MOD, "nf_trace")


# ══ 그림 3 · P2 부하와 ACLR ═════════════════════════════════════════════
def fig3_aclr(p2):
    fig, (ax1, ax2) = S.figure(12.6, 4.6, ncols=2)

    # (a) 안테나 반사계수가 깎는 포화 전력
    g = np.linspace(0.0, 0.45, 200)
    loss = np.array([-10 * np.log10(AC.load_pull_worst(v)) for v in g])
    S.emph(ax1, g, loss, color=S.COLORS[1])
    ax1.plot([p2["gamma"]], [p2["psat_loss_db"]], "o", ms=9, color=S.ACCENT)
    ax1.annotate(f"이 안테나\n|Γ| {p2['gamma']:.2f} (정재파비 "
                 f"{p2['vswr']:.2f})\n포화 전력 {p2['psat_loss_db']:.2f} dB 손실",
                 xy=(p2["gamma"], p2["psat_loss_db"]), xytext=(0.12, 3.4),
                 fontsize=9, linespacing=1.4, color=S.INK,
                 arrowprops=dict(arrowstyle="->", color=S.INK, lw=1.2))
    for v, lab in ((1.5, "정재파비 1.5"), (2.0, "정재파비 2.0")):
        gg = (v - 1) / (v + 1)
        ax1.axvline(gg, color=S.MUTED, ls=":", lw=1.2)
        ax1.text(gg, 0.1, f" {lab}", fontsize=8.5, color=S.MUTED,
                 rotation=90, va="bottom")
    ax1.set_xlabel("안테나 반사계수 |Γ|")
    ax1.set_ylabel("포화 전력 손실 (dB)")
    ax1.set_ylim(0, 4.2)
    ax1.set_title("(a) 안테나가 50 Ω 이 아니면 PA 가 손해를 본다")

    # (b) 그 손실이 ACLR 로 나타난다
    # 안테나를 달면 실효 백오프가 음수가 된다 — 곡선을 거기까지 그려야
    # 점이 곡선 위에 앉는다. 처음에는 0 부터 그려서 점이 허공에 떴다.
    bo = np.array([1.5 - p2["psat_loss_db"] - 1.0, 1.5 - p2["psat_loss_db"],
                   0.0, 1.5, 3.0, 4.5, 6.0, 8.0, 10.0, 12.0])
    aclr = np.array([max(AC.aclr_at_backoff(float(b))) for b in bo])
    S.emph(ax2, bo, aclr, color=S.COLORS[0])
    S.limit_line(ax2, AC.SPEC["aclr_max_dbc"],
                 f"사양 {AC.SPEC['aclr_max_dbc']:.0f} dBc", side="lower")
    b50, bant = 1.5, 1.5 - p2["psat_loss_db"]
    # 사양선(-33 dBc)이 두 점 사이를 지나므로 이름표를 그 위아래로 갈라 둔다.
    for x0, v, lab, c, off in (
            (b50, p2["worst_50"], "50 Ω 부하", S.COLORS[2], (16, -26)),
            (bant, p2["worst_ant"], "실제 안테나", S.ACCENT, (12, 14))):
        ax2.plot([x0], [v], "o", ms=9, color=c, zorder=6)
        ax2.annotate(f"{lab}\n{v:.1f} dBc", xy=(x0, v), xytext=off,
                     textcoords="offset points", fontsize=9, color=c,
                     fontweight="bold", linespacing=1.4)
    ax2.set_xlabel("첨두 백오프 (dB)")
    ax2.set_ylabel("인접 채널 누설비 (dBc)")
    ax2.set_xlim(-3.0, 13.5)
    ax2.set_ylim(min(aclr) - 1.5, max(aclr) + 3.0)
    ax2.set_title("(b) 같은 구동인데 백오프가 2.7 dB 줄어든 셈이 된다")

    S.save(fig, MOD, "aclr_load")
    return bo, aclr


# ══ 그림 4 · P3 케이블 길이 ═════════════════════════════════════════════
def fig4_emc(p3):
    fig, (ax1, ax2) = S.figure(12.6, 4.6, ncols=2)

    # (a) 케이블 길이 대 방사
    L = np.linspace(0.1, 2.0, 200)
    e = np.array([B07.dbuv_m(B07.e_from_cm_current(p3["i_cm_a"], p3["f_hz"],
                                                   float(x), 3.0)) for x in L])
    S.emph(ax1, L, e, color=S.COLORS[0])
    S.limit_line(ax1, p3["limit_dbuv_m"],
                 f"한도 {p3['limit_dbuv_m']:.0f} dBµV/m")
    for key, lab, c in (("bench", "사내 사전 시험", S.COLORS[2]),
                        ("lab", "시험소", S.ACCENT)):
        d = p3[key]
        ax1.plot([d["length_m"]], [d["dbuv_m"]], "o", ms=9, color=c, zorder=6)
        ax1.annotate(f"{lab}\n케이블 {d['length_m']:.2f} m\n"
                     f"{d['dbuv_m']:.1f} dBµV/m "
                     f"(여유 {p3['limit_dbuv_m'] - d['dbuv_m']:+.1f})",
                     xy=(d["length_m"], d["dbuv_m"]),
                     xytext=(16, -6),
                     textcoords="offset points", fontsize=9, color=c,
                     linespacing=1.4, fontweight="bold",
                     va="top" if key == "bench" else "center")
    ax1.set_xlabel("케이블 길이 (m)")
    ax1.set_ylabel(f"{p3['f_hz'] / 1e6:.0f} MHz 방사 (dBµV/m, 3 m)")
    ax1.set_title("(a) 보드는 그대로인데 셋업이 10.7 dB 를 만든다")

    # (b) 무엇을 고쳐야 하나 — 전류를 줄이는 쪽
    need_db = p3["lab"]["dbuv_m"] - p3["limit_dbuv_m"]
    steps = [("아무것도 안 함", 0.0), ("페라이트 (240 MHz)", 8.5),
             ("+ 케이블 재배치", 3.0), ("+ 접지 보강", 2.5)]
    cum, labels, vals = 0.0, [], []
    for name, d in steps:
        cum += d
        labels.append(name)
        vals.append(p3["lab"]["dbuv_m"] - cum)
    cols = [S.ACCENT if v > p3["limit_dbuv_m"] else S.COLORS[2] for v in vals]
    ax2.bar(range(len(vals)), vals, color=cols, width=0.6)
    for i, v in enumerate(vals):
        ax2.text(i, v + 0.4, f"{v:.1f}", ha="center", fontsize=9)
    S.limit_line(ax2, p3["limit_dbuv_m"],
                 f"한도 {p3['limit_dbuv_m']:.0f} dBµV/m")
    ax2.set_xticks(range(len(labels)))
    ax2.set_xticklabels(labels, fontsize=8.5, rotation=12, ha="right")
    ax2.set_ylabel("dBµV/m")
    # 마지막 막대가 39.7 이라 40 에서 자르면 잘려 나간다.
    ax2.set_ylim(38, 57)
    ax2.set_title(f"(b) {need_db:.1f} dB 를 벌어야 한다 — 한 가지로는 안 된다")

    S.save(fig, MOD, "emc_setup")
    return need_db


# ══ 그림 5 · P4 다툼과 수율 ═════════════════════════════════════════════
def fig5_yield(p4, p5):
    fig, (ax1, ax2) = S.figure(12.6, 4.6, ncols=2)

    # (a) 게이지가 좋아지면 다툼이 사라진다
    sd_part = p4["truth"]["sd_part"]
    reps = np.linspace(0.01, 0.20, 40)
    dis = np.array([AC.disagree_rate(sd_part, float(r), p4["truth"]["sd_op"],
                                     AC.SPEC["gain_tol_db"]) * 100
                    for r in reps])
    S.emph(ax1, reps, dis, color=S.COLORS[1])
    ax1.plot([p4["truth"]["sd_rep"]], [p4["disagree"] * 100], "o", ms=9,
             color=S.ACCENT, zorder=6)
    ax1.annotate(f"이 보드\n반복성 {p4['truth']['sd_rep']:.3f} dB\n"
                 f"100장 중 {p4['disagree'] * 100:.1f} 장에서 다툼",
                 xy=(p4["truth"]["sd_rep"], p4["disagree"] * 100),
                 xytext=(24, -52), textcoords="offset points", ha="left",
                 fontsize=9, color=S.ACCENT, linespacing=1.4,
                 fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    good = AC.disagree_rate(sd_part, 0.024, 0.010, AC.SPEC["gain_tol_db"]) * 100
    ax1.plot([0.024], [good], "s", ms=8, color=S.COLORS[2], zorder=6)
    ax1.annotate(f"좋은 게이지로 바꾸면\n{good:.2f} %", xy=(0.024, good),
                 xytext=(18, 22), textcoords="offset points", fontsize=9,
                 color=S.COLORS[2], linespacing=1.4,
                 arrowprops=dict(arrowstyle="->", color=S.COLORS[2], lw=1.2))
    ax1.set_xlabel("측정 반복성 σ (dB)")
    ax1.set_ylabel("두 사람의 판정이 갈리는 비율 (%)")
    ax1.set_title("(a) 다투는 것은 사람이 아니라 측정계다")

    # (b) 떨어지는 4 % 의 정체
    parts = [("진짜 불합격이라 떨어진 것",
              (p5["true_bad"] - p5["escape"]) * 100, S.ACCENT),
             ("멀쩡한데 떨어진 것 (헛수고)", p5["overkill"] * 100,
              S.COLORS[4])]
    left = 0.0
    for name, v, c in parts:
        ax2.barh([0], [v], left=left, color=c, height=0.5, label=name)
        ax2.text(left + v / 2, 0, f"{v:.2f} %p", ha="center", va="center",
                 color="white", fontweight="bold", fontsize=10)
        left += v
    ax2.barh([-0.9], [p5["escape"] * 100], color=S.COLORS[2], height=0.5,
             label="불합격인데 통과한 것 (빠뜨림)")
    ax2.text(p5["escape"] * 100 + 0.06, -0.9,
             f"{p5['escape'] * 1e6:,.0f} ppm", va="center", fontsize=9,
             color=S.COLORS[2], fontweight="bold")
    ax2.set_yticks([0, -0.9])
    ax2.set_yticklabels([f"떨어진 {left:.2f} %", "나간 것 중 불량"],
                        fontsize=9.5)
    ax2.set_xlabel("전체 생산량 대비 (%)")
    ax2.set_xlim(0, left * 1.25)
    ax2.set_ylim(-1.6, 0.7)
    ax2.set_title(f"(b) 수율 {p5['yield_pct']:.1f} % — 떨어진 것의 "
                  f"{p5['overkill_share'] * 100:.0f} % 는 멀쩡했다")
    ax2.legend(loc="lower right", fontsize=9)

    S.save(fig, MOD, "yield_split")
    return good


# ══ 본체 ════════════════════════════════════════════════════════════════
def main() -> int:
    print("심화 캡스톤 그림 생성")
    print("=" * 62)

    p1, gms = AC.problem_1()
    p2 = AC.problem_2()
    p3 = AC.problem_3()
    p4 = AC.problem_4()
    p5 = AC.problem_5()

    rows = fig1_problems(p1, p2, p3, p4, p5)
    print("  [1] 다섯 문제           " + " · ".join(
        f"{r[0][0]}{r[1]:+.1f}" for r in rows))
    fig2_nf(p1, gms)
    bd = p1["이 보드 (Γms · 이득 최대점)"]
    ds = p1["데이터시트 (Γopt 에 맞췄을 때)"]
    print(f"  [2] 잡음지수 추적       사슬 NF {ds['cascade_nf_db']:.2f} -> "
          f"{bd['cascade_nf_db']:.2f} dB · 이득 "
          f"{bd['gain_avail_db'] - ds['gain_avail_db']:+.2f} dB")
    bo, aclr = fig3_aclr(p2)
    print(f"  [3] 부하와 ACLR         {p2['worst_50']:.1f} -> "
          f"{p2['worst_ant']:.1f} dBc (백오프 {p2['psat_loss_db']:.2f} dB 잠식)")
    need = fig4_emc(p3)
    print(f"  [4] 케이블 길이         {p3['delta_db']:.1f} dB 차 · "
          f"{need:.1f} dB 를 벌어야 한다")
    good = fig5_yield(p4, p5)
    print(f"  [5] 다툼과 수율         {p4['disagree'] * 100:.1f} % -> "
          f"{good:.2f} % · 수율 {p5['yield_pct']:.1f} % 중 헛수고 "
          f"{p5['overkill'] * 100:.2f} %p")

    # ── 자체 검산 ───────────────────────────────────────────────────────
    print("\n[자체 검산]")
    ok: list[bool] = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  {'OK ' if cond else 'X  '} {msg}")

    chk(all(r[1] > 0 for r in rows),
        "다섯 문제가 모두 사양을 **넘는** 쪽이다 (그림이 부호를 뒤집지 않았다)")
    chk(len(rows) == 5, "그림에 그린 문제 수가 다섯")
    ratio = ((bd["cascade_nf_db"] - ds["cascade_nf_db"])
             / (bd["lna_nf_db"] - ds["lna_nf_db"]))
    chk(0.80 < ratio < 0.95,
        f"LNA 잡음지수 차 {bd['lna_nf_db'] - ds['lna_nf_db']:.2f} dB 중 "
        f"{bd['cascade_nf_db'] - ds['cascade_nf_db']:.2f} dB "
        f"({ratio * 100:.0f} %)가 사슬로 넘어온다 — 뒷단이 조금 희석한다")
    chk(all(b < a for a, b in zip(aclr, aclr[1:])),
        "ACLR 곡선이 백오프에 대해 단조롭다 (그림의 화살표 방향이 맞다)")
    i50 = int(np.argmin(np.abs(bo - 1.5)))
    chk(abs(aclr[i50] - p2["worst_50"]) < 0.5,
        f"곡선 위의 1.5 dB 점({aclr[i50]:.1f})이 표에 적은 50 Ω 값"
        f"({p2['worst_50']:.1f} dBc)과 같다")
    chk(abs(need - (p3["lab"]["dbuv_m"] - p3["limit_dbuv_m"])) < 1e-9,
        f"벌어야 하는 양 {need:.1f} dB 가 초과량과 같다")
    chk(good < p4["disagree"] * 100 / 5,
        f"게이지만 바꿔도 다툼이 {p4['disagree'] * 100:.2f} -> {good:.2f} % "
        f"로 준다 ({p4['disagree'] * 100 / good:.0f}배) — 부품 산포는 "
        f"그대로 두고 잰 값이다")
    tot = (p5["true_bad"] - p5["escape"]) + p5["overkill"]
    chk(abs(tot - p5["dropped"]) < 1e-12,
        f"그림 (b) 의 두 칸 합 {tot * 100:.4f} % 가 전체 불합격률과 일치")
    chk(p5["overkill"] > p5["true_bad"] - p5["escape"],
        f"헛수고({p5['overkill'] * 100:.2f} %p)가 진짜 불합격"
        f"({(p5['true_bad'] - p5['escape']) * 100:.2f} %p)보다 크다 "
        f"— 막대의 순서가 이야기와 맞는다")

    print()
    if not all(ok):
        return 1
    print(f"  검산 {len(ok)}항목 전부 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
