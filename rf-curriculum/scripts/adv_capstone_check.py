#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""심화 캡스톤 자체 검산 도구 — 받은 보드를 양산으로 넘길 수 있는가.

기본 캡스톤의 `capstone_check.py` 가 **설계가 요구를 만족하는가**를 물었다면,
이 도구는 **이미 만들어진 보드가 왜 사양과 다른가**를 묻는다.

    python3 scripts/adv_capstone_check.py          # 받은 보드로 돌려 본다
    python3 scripts/adv_capstone_check.py --self   # 도구 자체의 검산

이 도구는 심화 모듈의 계산기를 **그대로 불러 쓴다.** 같은 식을 두 번 적지
않기 위해서이기도 하고(지침 5), 캡스톤에서 나오는 숫자가 본문 그림의
숫자와 반드시 일치하도록 하기 위해서이기도 하다.

  · 잡음 파라미터 F(Γs), Γms      gen_fig_b05  (→ B05 §2·§4)
  · 로드풀 R_opt, 대신호 ACLR     gen_fig_b04  (→ B04 §7·§8)
  · 공통모드 방사와 한계          gen_fig_b07  (→ B07 §5)
  · 게이지 R&R 분산 분해          gen_fig_b11  (→ B11 §4)
  · 가드밴드·빠뜨림·재시험        gen_fig_b12  (→ B12 §6·§7)

받은 보드에는 **다섯 개의 문제가 심어져 있다.** 학습자에게는 증상만 주고,
아래 `problem_*()` 가 그 증상의 크기를 계산으로 확정한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_fig_b04 as B04  # noqa: E402
import gen_fig_b05 as B05  # noqa: E402
import gen_fig_b07 as B07  # noqa: E402
import gen_fig_b11 as B11  # noqa: E402
import gen_fig_b12 as B12  # noqa: E402


def db(x):
    return 10.0 * np.log10(x)


def un(x):
    return 10.0 ** (np.asarray(x, float) / 10.0)


KT0_DBM_HZ = -174.0


# ══════════════════════════════════════════════════════════════════════
# 받은 보드 — 학습자가 손에 쥐는 것
# ══════════════════════════════════════════════════════════════════════
# 기본 캡스톤이 만든 2.4 GHz 트랜시버 모듈 3차 시제품 20장이라고 둔다.
# 아래는 **설계 사양서에 적힌 값**이지 측정값이 아니다.
SPEC = dict(
    band_hz=(2400e6, 2483.5e6),
    bw_hz=20e6,
    nf_max_db=3.0,          # 수신 잡음지수 상한 (모듈 입력 기준)
    sens_dbm=-93.0,         # 위 잡음지수와 아래 SNR 로부터 나온 값
    snr_req_db=5.0,
    pout_dbm=20.0,          # 안테나 단자 평균 출력
    aclr_max_dbc=-33.0,     # 인접 채널 누설비 상한
    evm_max_pct=3.0,
    emc_f_hz=240e6,         # 사전 시험에서 걸린 주파수
    gain_db=12.0,           # 수신 이득 (게이지 R&R 대상 항목)
    gain_tol_db=1.0,        # 공차 ±1.0 dB
)

# 수신 사슬. LNA 의 잡음지수만 비워 두었다 — 그 값이 **정합망이 어디에
# 맞춰져 있는가**에 따라 정해지기 때문이다 (심은 문제 ①).
def rx_chain(lna_nf_db):
    return [
        dict(name="T/R 스위치", gain=-0.8, nf=0.8),
        dict(name="대역통과 필터", gain=-0.8, nf=0.8),
        dict(name="LNA", gain=18.0, nf=lna_nf_db),
        dict(name="이미지 필터", gain=-1.0, nf=1.0),
        dict(name="믹서 이후 전단", gain=8.0, nf=10.0),
    ]


def cascade_nf_db(chain):
    """프리스 누적 (→ M12 §2). 첫 단의 잡음지수가 거의 전부를 정한다."""
    f_tot, g_cum = un(chain[0]["nf"]), un(chain[0]["gain"])
    for st in chain[1:]:
        f_tot += (un(st["nf"]) - 1.0) / g_cum
        g_cum *= un(st["gain"])
    return float(db(f_tot))


def sensitivity_dbm(nf_db, bw_hz=SPEC["bw_hz"], snr_db=SPEC["snr_req_db"]):
    return KT0_DBM_HZ + nf_db + 10 * np.log10(bw_hz) + snr_db


# ══════════════════════════════════════════════════════════════════════
# 심은 문제 ① — 데이터시트 NF 와 보드 NF 가 다르다
# ══════════════════════════════════════════════════════════════════════
def problem_1():
    """정합망이 Γopt 가 아니라 Γms(이득 최대점)에 맞춰져 있다.

    증상: "LNA 데이터시트는 0.65 dB 인데 우리 보드 수신 잡음지수는
    4.34 dB 입니다. 예산표로는 2.89 dB 여야 합니다."
    학습자는 대개 측정 오류를 의심하며 며칠을 쓴다. 답은 B05 §4 에 있다 —
    잡음지수는 **소스 임피던스의 함수**이고, 이득 최대점과 잡음 최소점은
    같은 자리가 아니다.
    """
    gms = B05.gamma_ms()
    cases = {
        "데이터시트 (Γopt 에 맞췄을 때)": B05.G_OPT,
        "50 Ω 로 그냥 물렸을 때": 0.0 + 0j,
        "이 보드 (Γms · 이득 최대점)": gms,
    }
    out = {}
    for name, gs in cases.items():
        f_lna = float(B05.f_of_gs(gs))
        out[name] = dict(
            gamma=gs,
            lna_nf_db=f_lna,
            cascade_nf_db=cascade_nf_db(rx_chain(f_lna)),
            gain_avail_db=float(B05.gain_avail_db(gs)),
        )
    for v in out.values():
        v["sens_dbm"] = sensitivity_dbm(v["cascade_nf_db"])
    return out, complex(gms)


# ══════════════════════════════════════════════════════════════════════
# 심은 문제 ② — 50 Ω 에서는 ACLR 합격, 안테나에서 불합격
# ══════════════════════════════════════════════════════════════════════
def psat_ratio(r_over_ropt):
    """부하가 최적에서 벗어났을 때 남는 포화 전력의 비.

    R < Ropt 면 전압 스윙이 남고 전류가 먼저 차서 P = I²R/2 (R 에 비례),
    R > Ropt 면 반대로 P = V²/2R (R 에 반비례). 최적점에서 둘이 만난다.
    """
    r = np.asarray(r_over_ropt, float)
    return np.minimum(r, 1.0 / r)


def load_pull_worst(gamma_mag):
    """|Γ_L| 원 위에서 포화 전력이 가장 많이 깎이는 지점.

    실축 위의 두 끝이 최악이다. R/Ropt 는 (1+Γ)/(1-Γ) 와 그 역수.
    """
    hi = (1.0 + gamma_mag) / (1.0 - gamma_mag)
    return float(min(psat_ratio(hi), psat_ratio(1.0 / hi)))


def aclr_at_backoff(backoff_db, seed=3):
    """주어진 백오프에서 메모리 다항식 PA 의 ACLR 을 잰다 (→ B04 §8)."""
    x = B04.make_signal(seed=seed) if "seed" in B04.make_signal.__code__.co_varnames \
        else B04.make_signal()
    x = x / np.sqrt(np.mean(np.abs(x) ** 2))
    # 백오프는 **첨두**를 A_SAT 아래로 얼마나 내리는가로 정의한다.
    peak = np.max(np.abs(x))
    x = x * (B04.A_SAT / peak) * 10 ** (-backoff_db / 20.0)
    y = B04.pa_mp(x)
    lo, hi = B04.aclr_db(y)
    return float(lo), float(hi)


def problem_2(gamma_ant=0.30, backoff_db=1.5):
    """안테나 정재파비가 PA 를 압축으로 밀어 넣는다.

    증상: "50 Ω 부하로는 ACLR -34.5 dBc 인데 실제 안테나를 달면
    -31.6 dBc 로 사양(-33)을 넘습니다."
    답: 안테나가 50 Ω 이 아니면 PA 가 보는 부하선이 달라져 **포화 전력이
    내려가고**, 같은 구동이 곧 더 깊은 압축이 된다 (→ B04 §7).
    """
    ratio = load_pull_worst(gamma_ant)
    loss_db = -10 * np.log10(ratio)
    vswr = (1 + gamma_ant) / (1 - gamma_ant)
    lo50, hi50 = aclr_at_backoff(backoff_db)
    loa, hia = aclr_at_backoff(backoff_db - loss_db)
    return dict(
        gamma=gamma_ant, vswr=vswr, psat_loss_db=loss_db,
        aclr_50=(lo50, hi50), aclr_ant=(loa, hia),
        worst_50=max(lo50, hi50), worst_ant=max(loa, hia),
        degraded_db=max(loa, hia) - max(lo50, hi50),
    )


# ══════════════════════════════════════════════════════════════════════
# 심은 문제 ③ — 사전 시험 통과, 시험소 탈락
# ══════════════════════════════════════════════════════════════════════
def problem_3(f_hz=SPEC['emc_f_hz'], i_cm_a=4.0e-6,
              len_bench_m=0.35, len_lab_m=1.20,
              dist_m=3.0):
    """케이블 길이가 다르면 같은 보드가 다른 값을 낸다.

    증상: "사내 사전 시험은 3.0 dB 여유였는데 시험소에서 7.7 dB
    넘었습니다. 보드는 같은 것입니다."
    답: 공통모드 방사는 **전류 × 케이블 길이**에 비례한다 (→ B07 §5).
    벤치에서 짧은 케이블로 재고 시험소에서 규격 길이로 재면 그 차이만큼
    그대로 벌어진다. 보드는 아무것도 안 바뀌었다.
    """
    e_bench = B07.e_from_cm_current(i_cm_a, f_hz, len_bench_m, dist_m)
    e_lab = B07.e_from_cm_current(i_cm_a, f_hz, len_lab_m, dist_m)
    lim = float(B07.limit_dbuv(f_hz))
    return dict(
        f_hz=f_hz, i_cm_a=i_cm_a, limit_dbuv_m=lim,
        bench=dict(length_m=len_bench_m, dbuv_m=float(B07.dbuv_m(e_bench))),
        lab=dict(length_m=len_lab_m, dbuv_m=float(B07.dbuv_m(e_lab))),
        delta_db=float(B07.dbuv_m(e_lab) - B07.dbuv_m(e_bench)),
        i_cm_limit_a=float(B07.cm_current_limit_a(f_hz, len_lab_m, dist_m)),
    )


# ══════════════════════════════════════════════════════════════════════
# 심은 문제 ④ — 작업자 A 는 합격, B 는 불합격
# ══════════════════════════════════════════════════════════════════════
def disagree_rate(sd_part, sd_rep, sd_op, half, n=400_001, span=7.0):
    """두 측정자가 같은 물건을 두고 다른 판정을 낼 확률.

    A 는 +sd_op/2, B 는 -sd_op/2 만큼 치우쳐 읽는다고 두고, 각자 반복성
    잡음을 얹는다. 참값 x 로 적분하되 판정선 둘레를 촘촘히 깐다.
    """
    x = np.linspace(-span * sd_part, span * sd_part, n)
    for edge in (-half, half):
        x = np.append(x, np.linspace(edge - 10 * sd_rep, edge + 10 * sd_rep,
                                     4001))
    x = np.unique(x)
    fx = stats.norm.pdf(x, 0.0, sd_part)

    def p_pass(bias):
        return (stats.norm.cdf((half - x - bias) / sd_rep)
                - stats.norm.cdf((-half - x - bias) / sd_rep))

    pa, pb = p_pass(+sd_op / 2), p_pass(-sd_op / 2)
    # 두 사람의 오차는 독립이다. 어긋날 확률 = pa(1-pb) + (1-pa)pb
    return float(np.trapezoid(fx * (pa * (1 - pb) + (1 - pa) * pb), x))


def disagree_mc(sd_part, sd_rep, sd_op, half, n=4_000_000, rng=None):
    """같은 것을 몬테카를로로 (교차검증)."""
    rng = rng or np.random.default_rng(2026)
    x = rng.normal(0.0, sd_part, n)
    a = np.abs(x + sd_op / 2 + rng.normal(0.0, sd_rep, n)) <= half
    b = np.abs(x - sd_op / 2 + rng.normal(0.0, sd_rep, n)) <= half
    return float(np.mean(a != b))


def problem_4(sd_part=0.45, sd_rep=0.135, sd_op=0.090, sd_int=0.045):
    """이 보드의 이득 측정계가 두 사람 사이에서 갈린다.

    증상: "제가 재면 통과, 옆자리가 재면 탈락입니다. 서로를 의심합니다."
    답: 게이지 R&R 로 판정할 일이다 (→ B11 §4). 값들은 B11 의 '나쁜 게이지'
    를 그대로 쓰되 부품 산포만 이 보드의 것(0.45 dB)으로 바꿨다.

    계산해 보면 다툼의 89 % 가 **반복성** 몫이다 — 측정자 치우침을 0 으로
    둬도 거의 그대로 남는다. 두 사람은 서로를 의심하지만, 한 사람이 두 번
    재도 같은 일이 벌어진다.
    """
    y, _ = B11.make_study(sd_part=sd_part, sd_op=sd_op, sd_int=sd_int,
                          sd_rep=sd_rep, rng=np.random.default_rng(101))
    v = B11.anova_grr(y)
    half = SPEC["gain_tol_db"]
    return dict(
        variance=v,
        pct_study=float(B11.pct_grr_study(v)),
        pct_tol=float(B11.pct_grr_tol(v, tol_half=half)),
        ndc=B11.ndc(v),
        disagree=disagree_rate(sd_part, sd_rep, sd_op, half),
        disagree_mc=disagree_mc(sd_part, sd_rep, sd_op, half),
        truth=dict(sd_part=sd_part, sd_rep=sd_rep, sd_op=sd_op, sd_int=sd_int),
    )


# ══════════════════════════════════════════════════════════════════════
# 심은 문제 ⑤ — 양산 수율 96 %, 원인 불명
# ══════════════════════════════════════════════════════════════════════
def problem_5(sd_unit=0.40, sd_diff=0.171, guard=0.10):
    """불량의 상당 부분이 진짜 불량이 아니다.

    증상: "수율이 96 % 인데 왜 떨어지는지 모르겠습니다. 빈은 'RF 불합격'
    하나뿐입니다."
    답 둘. ① 빈을 쪼개지 않으면 파레토가 안 나온다 (→ B12 §7).
    ② 떨어진 것 중 상당수가 **가드밴드가 만든 헛수고**다 (→ B12 §6).
    """
    limit = 1.0
    esc, ovk = B12.guard_closed(sd_unit, sd_diff, limit, guard)
    esc0, ovk0 = B12.guard_closed(sd_unit, sd_diff, limit, 0.0)
    # 진짜 불합격률 (참값 기준)
    true_bad = 2 * stats.norm.sf(limit / sd_unit)
    # 시험이 떨구는 전체 = 진짜 불합격 중 걸린 것 + 헛수고
    dropped = (true_bad - esc) + ovk
    return dict(
        guard=guard, true_bad=float(true_bad), dropped=float(dropped),
        yield_pct=100 * (1 - dropped),
        overkill=float(ovk), overkill_share=float(ovk / dropped),
        escape=float(esc), escape_no_guard=float(esc0),
        overkill_no_guard=float(ovk0),
        bins=B12.BINS,
    )


# ══════════════════════════════════════════════════════════════════════
# 학습자용 감사 — 자기 숫자를 넣어 판정한다
# ══════════════════════════════════════════════════════════════════════
def audit(meas: dict) -> list[tuple[str, bool, str]]:
    """측정값 묶음을 사양과 대조해 합·부와 근거를 돌려준다.

    meas 의 키를 자기 보드 값으로 바꿔 쓰는 것이 P2~P4 의 실제 작업이다.
    """
    rows: list[tuple[str, bool, str]] = []

    def add(name, ok, msg):
        rows.append((name, bool(ok), msg))

    nf = meas.get("cascade_nf_db")
    if nf is not None:
        add("수신 잡음지수", nf <= SPEC["nf_max_db"],
            f"{nf:.2f} dB (상한 {SPEC['nf_max_db']:.2f}) · "
            f"감도 환산 {sensitivity_dbm(nf):.1f} dBm")
    aclr = meas.get("aclr_dbc")
    if aclr is not None:
        add("인접 채널 누설비", aclr <= SPEC["aclr_max_dbc"],
            f"{aclr:.1f} dBc (상한 {SPEC['aclr_max_dbc']:.1f})")
    e = meas.get("emission_dbuv_m")
    if e is not None:
        f_emc = meas.get("emission_f_hz", SPEC["emc_f_hz"])
        lim = float(B07.limit_dbuv(f_emc))
        add(f"방사 ({f_emc / 1e6:.0f} MHz, 3 m)", e <= lim,
            f"{e:.1f} dBuV/m (한도 {lim:.1f})")
    g = meas.get("pct_grr_tol")
    if g is not None:
        add("게이지 R&R (공차 대비)", g < 30.0,
            f"%GRR {g:.1f} % · 10 % 미만이면 합격, 30 % 넘으면 불합격")
    n = meas.get("ndc")
    if n is not None:
        add("구별 범주 수", n >= 5, f"ndc {n} (5 이상 필요)")
    t = meas.get("test_time_s")
    if t is not None:
        u = B12.uph_closed(t, meas.get("sites", 4), meas.get("serial_frac", 0.2))
        add("시험 시간 예산", u >= meas.get("uph_target", 400),
            f"{t:.1f} 초 · {u:.0f} UPH · 개당 "
            f"{B12.cost_per_unit(u):,.0f} 원")
    return rows


# ══════════════════════════════════════════════════════════════════════
def report() -> None:
    print("심화 캡스톤 — 받은 보드에 심어 둔 다섯 문제")
    print("=" * 68)

    p1, gms = problem_1()
    print("\n[문제 1] 데이터시트 NF 와 보드 NF 가 다르다")
    print(f"  {'경우':<26s} {'|Γs|':>6s} {'LNA NF':>8s} {'사슬 NF':>8s} "
          f"{'가용이득':>8s} {'감도':>9s}")
    for name, v in p1.items():
        print(f"  {name:<26s} {abs(v['gamma']):>6.3f} "
              f"{v['lna_nf_db']:>8.2f} {v['cascade_nf_db']:>8.2f} "
              f"{v['gain_avail_db']:>8.2f} {v['sens_dbm']:>9.1f}")
    ds = p1["데이터시트 (Γopt 에 맞췄을 때)"]
    bd = p1["이 보드 (Γms · 이득 최대점)"]
    print(f"  -> 보드가 사양보다 NF {bd['cascade_nf_db'] - ds['cascade_nf_db']:.2f} dB "
          f"높고 감도는 {bd['sens_dbm'] - ds['sens_dbm']:.2f} dB 나쁘다. "
          f"그 대신 이득을 {bd['gain_avail_db'] - ds['gain_avail_db']:.2f} dB 벌었다")

    p2 = problem_2()
    print("\n[문제 2] 50 Ω 에서는 합격, 안테나에서는 불합격")
    print(f"  안테나 |Γ| {p2['gamma']:.2f} (정재파비 {p2['vswr']:.2f}) "
          f"-> 포화 전력 {p2['psat_loss_db']:.2f} dB 손실")
    print(f"  ACLR  50 Ω {p2['worst_50']:+.1f} dBc  ->  "
          f"안테나 {p2['worst_ant']:+.1f} dBc "
          f"({p2['degraded_db']:+.1f} dB 나빠짐)")
    print(f"  사양 {SPEC['aclr_max_dbc']:.1f} dBc: "
          f"50 Ω {'합격' if p2['worst_50'] <= SPEC['aclr_max_dbc'] else '불합격'} · "
          f"안테나 {'합격' if p2['worst_ant'] <= SPEC['aclr_max_dbc'] else '불합격'}")

    p3 = problem_3()
    print("\n[문제 3] 사전 시험 통과, 시험소 탈락")
    print(f"  공통모드 전류 {p3['i_cm_a'] * 1e6:.1f} µA · "
          f"{p3['f_hz'] / 1e6:.0f} MHz · 한도 {p3['limit_dbuv_m']:.0f} dBµV/m")
    print(f"  벤치 (케이블 {p3['bench']['length_m']:.2f} m) "
          f"{p3['bench']['dbuv_m']:.1f} dBµV/m  -> 여유 "
          f"{p3['limit_dbuv_m'] - p3['bench']['dbuv_m']:+.1f} dB")
    print(f"  시험소 (케이블 {p3['lab']['length_m']:.2f} m) "
          f"{p3['lab']['dbuv_m']:.1f} dBµV/m  -> 여유 "
          f"{p3['limit_dbuv_m'] - p3['lab']['dbuv_m']:+.1f} dB")
    print(f"  -> 보드는 그대로인데 {p3['delta_db']:.1f} dB 가 벌어진다. "
          f"한도에 닿는 전류는 {p3['i_cm_limit_a'] * 1e6:.2f} µA")

    p4 = problem_4()
    print("\n[문제 4] 작업자 A 는 합격, B 는 불합격")
    print(f"  %GRR 산포 대비 {p4['pct_study']:.1f} % · "
          f"공차 대비 {p4['pct_tol']:.1f} % · ndc {p4['ndc']}")
    print(f"  같은 물건에 두 사람이 다른 판정을 낼 확률 "
          f"{p4['disagree'] * 100:.2f} % "
          f"(몬테카를로 {p4['disagree_mc'] * 100:.2f} %)")
    print(f"  -> 100장을 재면 {p4['disagree'] * 100:.1f} 장에서 다툰다. "
          f"사람이 아니라 측정계 문제다")

    p5 = problem_5()
    print("\n[문제 5] 양산 수율 96 %, 원인 불명")
    print(f"  가드밴드 {p5['guard']:.2f} · 수율 {p5['yield_pct']:.1f} %")
    print(f"  떨어지는 것 {p5['dropped'] * 100:.2f} % 중 "
          f"헛수고가 {p5['overkill'] * 100:.2f} %p "
          f"({p5['overkill_share'] * 100:.0f} %)")
    print(f"  진짜 불합격은 {p5['true_bad'] * 100:.2f} % 뿐 · "
          f"가드밴드를 빼면 빠뜨림이 "
          f"{p5['escape'] * 1e6:.0f} -> {p5['escape_no_guard'] * 1e6:,.0f} ppm")
    print(f"  빈이 'RF 불합격' 하나뿐이면 위 어느 것도 안 보인다 "
          f"(쪼개면 상위 3개가 {sum(sorted(p5['bins'].values(), reverse=True)[:3]) / sum(p5['bins'].values()) * 100:.0f} %)")

    print("\n[예시 감사] 받은 보드를 그대로 측정했다고 치면")
    rows = audit(dict(
        cascade_nf_db=bd["cascade_nf_db"],
        aclr_dbc=p2["worst_ant"],
        emission_dbuv_m=p3["lab"]["dbuv_m"],
        pct_grr_tol=p4["pct_tol"],
        ndc=p4["ndc"],
        test_time_s=B12.test_time_s(),
    ))
    for name, ok, msg in rows:
        print(f"  {'합격' if ok else '불합격'}  {name:<20s} {msg}")
    print(f"\n  -> {sum(1 for _, ok, _ in rows if not ok)}/{len(rows)} 항목 불합격. "
          f"이것이 P1 의 출발점이다")


# ══════════════════════════════════════════════════════════════════════
def self_test() -> int:
    print("심화 캡스톤 도구 자체 검산")
    print("=" * 68)
    ok: list[bool] = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  {'OK ' if cond else 'X  '} {msg}")

    # ── 사슬 계산 ─────────────────────────────────────────────────────
    chk(abs(cascade_nf_db([dict(name="a", gain=20.0, nf=1.0)]) - 1.0) < 1e-12,
        "한 단만 있으면 사슬 잡음지수 = 그 단의 잡음지수")
    two = [dict(name="a", gain=20.0, nf=1.0), dict(name="b", gain=10.0, nf=10.0)]
    manual = db(un(1.0) + (un(10.0) - 1.0) / un(20.0))
    chk(abs(cascade_nf_db(two) - manual) < 1e-12,
        f"두 단 프리스 식이 손계산과 일치 ({cascade_nf_db(two):.4f} dB)")
    loss_first = [dict(name="손실", gain=-3.0, nf=3.0),
                  dict(name="증폭", gain=20.0, nf=1.0)]
    chk(abs(cascade_nf_db(loss_first) - 4.0) < 1e-9,
        "앞단 손실 3 dB 는 잡음지수에 그대로 3 dB 를 더한다 "
        f"({cascade_nf_db(loss_first):.3f} dB)")

    # ── 문제 ① ───────────────────────────────────────────────────────
    p1, gms = problem_1()
    ds = p1["데이터시트 (Γopt 에 맞췄을 때)"]
    bd = p1["이 보드 (Γms · 이득 최대점)"]
    fifty = p1["50 Ω 로 그냥 물렸을 때"]
    chk(abs(ds["lna_nf_db"] - B05.FMIN_DB) < 1e-9,
        f"Γopt 에서 LNA 잡음지수가 정확히 Fmin ({ds['lna_nf_db']:.3f} dB)")
    chk(bd["lna_nf_db"] > fifty["lna_nf_db"] > ds["lna_nf_db"],
        f"Γms({bd['lna_nf_db']:.2f}) > 50 Ω({fifty['lna_nf_db']:.2f}) > "
        f"Γopt({ds['lna_nf_db']:.2f}) dB")
    chk(bd["gain_avail_db"] > ds["gain_avail_db"] + 4.0,
        f"그 대신 가용이득을 {bd['gain_avail_db'] - ds['gain_avail_db']:.2f} dB "
        f"더 얻는다 — 설계자가 그렇게 맞춘 이유")
    chk(bd["cascade_nf_db"] > SPEC["nf_max_db"] >= ds["cascade_nf_db"],
        f"사양 {SPEC['nf_max_db']:.1f} dB 를 Γopt 판({ds['cascade_nf_db']:.2f})은 "
        f"지키고 이 보드({bd['cascade_nf_db']:.2f})는 어긴다")
    chk(abs((bd["sens_dbm"] - ds["sens_dbm"])
            - (bd["cascade_nf_db"] - ds["cascade_nf_db"])) < 1e-9,
        "감도 차이는 잡음지수 차이와 정확히 같다 (같은 대역폭·같은 SNR)")
    chk(abs(abs(B05.G_OPT - gms) - 0.7547) < 1e-3,
        f"|Γopt - Γms| = {abs(B05.G_OPT - gms):.4f} — B05 §4 의 값과 같다")

    # ── 문제 ② ───────────────────────────────────────────────────────
    chk(abs(psat_ratio(1.0) - 1.0) < 1e-12,
        "최적 부하에서 포화 전력 손실 0")
    chk(abs(psat_ratio(2.0) - psat_ratio(0.5)) < 1e-12,
        "R 을 2배로 하나 1/2 로 하나 같은 만큼 잃는다 (대칭)")
    r = np.linspace(0.2, 5.0, 401)
    chk(np.all(psat_ratio(r) <= 1.0 + 1e-12),
        "어떤 부하에서도 최적점보다 좋아지지 않는다")
    p2 = problem_2()
    chk(abs(p2["psat_loss_db"] - 2.69) < 0.05,
        f"|Γ| 0.30 (정재파비 {p2['vswr']:.2f}) 은 포화 전력 "
        f"{p2['psat_loss_db']:.2f} dB 를 깎는다")
    chk(p2["worst_50"] <= SPEC["aclr_max_dbc"] < p2["worst_ant"],
        f"50 Ω {p2['worst_50']:.1f} dBc 합격 / 안테나 "
        f"{p2['worst_ant']:.1f} dBc 불합격 — 사양 "
        f"{SPEC['aclr_max_dbc']:.1f}")
    chk(p2["degraded_db"] > 2.0,
        f"부하만 바뀌었는데 ACLR 이 {p2['degraded_db']:.1f} dB 나빠진다")
    bo = [1.5, 4.0, 8.0, 12.0]
    curve = [max(aclr_at_backoff(b)) for b in bo]
    chk(all(b < a for a, b in zip(curve, curve[1:])),
        "백오프를 키우면 ACLR 이 단조롭게 좋아진다: "
        + " -> ".join(f"{v:.1f}" for v in curve) + " dBc")
    chk(curve[-1] < -48.0,
        f"백오프 {bo[-1]:.0f} dB 에서 {curve[-1]:.1f} dBc — 압축이 풀리면 "
        f"메모리 다항식이 남기는 몫만 남는다")

    # ── 문제 ③ ───────────────────────────────────────────────────────
    p3 = problem_3()
    ratio_db = 20 * np.log10(p3["lab"]["length_m"] / p3["bench"]["length_m"])
    chk(abs(p3["delta_db"] - ratio_db) < 1e-9,
        f"길이 비가 그대로 dB 로 온다: "
        f"20log10({p3['lab']['length_m']:.2f}/{p3['bench']['length_m']:.2f}) "
        f"= {ratio_db:.2f} dB")
    chk(p3["bench"]["dbuv_m"] < p3["limit_dbuv_m"] < p3["lab"]["dbuv_m"],
        f"벤치 {p3['bench']['dbuv_m']:.1f} 합격 / 시험소 "
        f"{p3['lab']['dbuv_m']:.1f} 불합격 (한도 {p3['limit_dbuv_m']:.0f})")
    chk(abs(p3["i_cm_limit_a"] - p3["i_cm_a"]
            * 10 ** (-(p3["lab"]["dbuv_m"] - p3["limit_dbuv_m"]) / 20)) < 1e-9,
        f"한도에 딱 닿는 전류 {p3['i_cm_limit_a'] * 1e6:.2f} µA 가 "
        f"역산과 일치")
    chk(p3["i_cm_a"] < 1e-5,
        f"문제를 만드는 전류가 {p3['i_cm_a'] * 1e6:.0f} µA 밖에 안 된다 "
        f"— 신호 전류의 백만분의 몇")

    # ── 문제 ④ ───────────────────────────────────────────────────────
    p4 = problem_4()
    se = np.sqrt(p4["disagree_mc"] * (1 - p4["disagree_mc"]) / 4_000_000)
    chk(abs(p4["disagree"] - p4["disagree_mc"]) < 4 * se,
        f"불일치율: 수치적분 {p4['disagree'] * 100:.3f} % vs 몬테카를로 "
        f"{p4['disagree_mc'] * 100:.3f} % (표본 오차 4배 안)")
    chk(p4["pct_study"] > 30 and p4["ndc"] < 5,
        f"%GRR {p4['pct_study']:.1f} % · ndc {p4['ndc']} — 두 기준 모두 불합격")
    v = p4["variance"]
    chk(abs(np.sqrt(v["rep"]) - p4["truth"]["sd_rep"]) < 0.03,
        f"분산분석이 반복성 참값 {p4['truth']['sd_rep']:.3f} 을 "
        f"{np.sqrt(v['rep']):.3f} 로 되찾는다")
    # 같은 부품 산포에서 게이지만 바꿔야 비교가 된다. 부품 산포까지 함께
    # 바꾸면 무엇이 좋아진 것인지 알 수 없다.
    clean = disagree_rate(p4["truth"]["sd_part"], 0.024, 0.010,
                          SPEC["gain_tol_db"])
    chk(clean < p4["disagree"] / 5,
        f"게이지만 좋은 것으로 바꾸면 불일치가 {p4['disagree'] * 100:.2f} -> "
        f"{clean * 100:.3f} % 로 준다 ({p4['disagree'] / clean:.0f}배)")
    sdp = p4["truth"]["sd_part"]
    no_bias = disagree_rate(sdp, p4["truth"]["sd_rep"], 0.0,
                            SPEC["gain_tol_db"])
    chk(0.0 < no_bias < p4["disagree"],
        f"측정자 치우침을 0 으로 둬도 반복성만으로 {no_bias * 100:.2f} % 가 "
        f"남는다 (전체 {p4['disagree'] * 100:.2f} %) — 사람을 통일해도 "
        f"{no_bias / p4['disagree'] * 100:.0f} % 는 그대로다")
    chk(no_bias / p4["disagree"] > 0.8,
        f"다툼의 {no_bias / p4['disagree'] * 100:.0f} % 는 **반복성** 몫이다 "
        f"— 두 사람은 서로를 의심하지만, 한 사람이 두 번 재도 같은 일이 "
        f"벌어진다")

    # ── 문제 ⑤ ───────────────────────────────────────────────────────
    p5 = problem_5()
    chk(95.5 < p5["yield_pct"] < 96.5,
        f"수율이 {p5['yield_pct']:.2f} % 로 나온다 — 증상과 맞는다")
    chk(p5["overkill_share"] > 0.5,
        f"떨어지는 것의 {p5['overkill_share'] * 100:.0f} % 가 헛수고 "
        f"— 절반 넘게 멀쩡한 물건이다")
    chk(p5["escape"] < p5["escape_no_guard"],
        f"가드밴드를 빼면 빠뜨림이 {p5['escape'] * 1e6:.0f} -> "
        f"{p5['escape_no_guard'] * 1e6:,.0f} ppm 으로 는다 — 그냥 없앨 수 없다")
    top3 = sum(sorted(p5["bins"].values(), reverse=True)[:3])
    chk(top3 / sum(p5["bins"].values()) > 0.8,
        f"빈을 쪼개면 상위 3개가 "
        f"{top3 / sum(p5['bins'].values()) * 100:.0f} % — 고칠 곳이 보인다")

    # ── 감사 함수 ─────────────────────────────────────────────────────
    rows = audit(dict(cascade_nf_db=bd["cascade_nf_db"],
                      aclr_dbc=p2["worst_ant"],
                      emission_dbuv_m=p3["lab"]["dbuv_m"],
                      pct_grr_tol=p4["pct_tol"], ndc=p4["ndc"]))
    chk(len(rows) == 5 and not any(o for _, o, _ in rows),
        f"받은 보드는 감사 {len(rows)}항목을 전부 떨어뜨린다 "
        f"— 심은 문제가 실제로 판정에 걸린다")
    good = audit(dict(cascade_nf_db=ds["cascade_nf_db"],
                      aclr_dbc=p2["worst_50"],
                      emission_dbuv_m=p3["bench"]["dbuv_m"],
                      pct_grr_tol=6.8, ndc=14))
    chk(all(o for _, o, _ in good),
        "문제를 다 고친 값을 넣으면 전부 합격 — 감사 함수가 한쪽으로 "
        "치우쳐 있지 않다")
    chk(audit({}) == [],
        "빈 측정값을 넣으면 아무 판정도 하지 않는다 (없는 것을 합격시키지 "
        "않는다)")

    print()
    if not all(ok):
        return 1
    print(f"  검산 {len(ok)}항목 전부 통과")
    return 0


if __name__ == "__main__":
    if "--self" in sys.argv:
        sys.exit(self_test())
    report()
