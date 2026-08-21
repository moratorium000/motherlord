"""캡스톤 자체 검산 도구 — 내가 짠 예산이 요구를 만족하는가.

학습자가 **자기 숫자를 넣어 돌리는 도구**다. 아래 REQ·RX_*·TX_* 를 자기
설계로 바꾸고 실행하면, 요구별로 합격·불합격과 마진을 표로 찍어 준다.

이 파일은 답안이 아니다. 아래 기준 설계는 "이런 모양으로 채우면 된다"를
보이기 위한 **예시 한 벌**이며, 부품값은 실제 제품의 데이터시트로 바꿔야 한다.

    python3 scripts/capstone_check.py            # 기준 설계로 돌려 본다
    python3 scripts/capstone_check.py --self     # 도구 자체의 검산

쓰는 공식의 주인 모듈
  · 캐스케이드 잡음지수·IP3      M12 §2·§3
  · 감도와 MDS                  M12 §5
  · 이득 배분과 AGC             M12 §4 · M11 §8
  · 백오프와 EVM                M13 §7
  · 스퍼 차트                   M09 §6
"""
import math
import sys


# ────────────────────────────────────────────── 단위
def db(x):
    return 10.0 * math.log10(x)


def un(x):
    return 10.0 ** (x / 10.0)


K_T0 = -174.0          # dBm/Hz, 290 K 에서의 열잡음 밀도 (→ M01)


# ══════════════════════════════════════════════ 요구사항
# 설계서 §5 의 예시 요구를 그대로 옮겨 놓았다. 일부러 **모순을 남겨 두었다** —
# 그 모순을 찾아내는 것이 P1 의 첫 과제다.
REQ = dict(
    band=(2400e6, 2483.5e6),
    bw=20e6,                    # 기준 대역폭
    # 수신
    sens_dbm=-95.0,             # 감도 요구
    nf_max_db=4.0,              # 잡음지수 상한
    iip3_min_dbm=-10.0,         # 입력 3차 절점 하한
    snr_req_db=5.0,             # 이 파형이 실제로 요구하는 SNR (MCS0 급)
    # 송신
    pout_dbm=20.0,              # 안테나 단자에서의 평균 출력
    evm_max_pct=3.0,
    papr_db=10.0,               # OFDM 첨두대평균 (→ M13 §3)
    # 규제
    eirp_limit_dbm=20.0,        # EN 300 328 (2.4 GHz 광대역)
    ant_gain_dbi=2.0,
)

# 스퍼를 몇 차 하모닉까지 볼 것인가. 아주 높은 차수는 세기가 잡음바닥
# 아래로 내려가 의미가 없다 — 끊지 않으면 표가 수백 줄이 되어 못 쓴다.
SPUR_MAX_ORDER = 100


# ══════════════════════════════════════════════ 기준 설계 (예시)
# 이득 dB · 잡음지수 dB · 입력 IP3 dBm — 자기 부품값으로 바꿔 쓸 것.
# LNA 와 VGA 는 AGC 로 이득이 바뀌므로 모드별로 두 벌을 만든다 (→ M12 §4).
def rx_chain(lna_gain, lna_nf, lna_iip3, vga_gain):
    return [
        dict(name="T/R 스위치",      gain=-1.0,      nf=1.0,      iip3=40.0),
        dict(name="대역통과 필터",   gain=-1.5,      nf=1.5,      iip3=50.0),
        dict(name="LNA",             gain=lna_gain,  nf=lna_nf,   iip3=lna_iip3),
        dict(name="대역통과 필터 2", gain=-1.5,      nf=1.5,      iip3=50.0),
        dict(name="능동 믹서",       gain=8.0,       nf=10.0,     iip3=0.0),
        dict(name="저역통과 필터",   gain=-1.0,      nf=1.0,      iip3=40.0),
        dict(name="기저대역 VGA",    gain=vga_gain,  nf=15.0,     iip3=5.0),
    ]


RX_MODES = {
    # 약한 신호를 받을 때: LNA 를 켠다. 잡음지수가 좋아진다.
    "고이득": rx_chain(lna_gain=22.0, lna_nf=0.9, lna_iip3=-10.0, vga_gain=30.0),
    # 센 신호·강한 간섭이 있을 때: LNA 를 우회한다. 선형성이 좋아진다.
    "저이득": rx_chain(lna_gain=-2.0, lna_nf=2.0, lna_iip3=25.0, vga_gain=54.0),
}
# 어느 요구를 어느 모드에서 만족시킬 것인가 — 이것이 설계 결정이다
MODE_FOR = dict(nf="고이득", sens="고이득", iip3="저이득")

# 송신: PA 출력에서 안테나 단자까지의 손실
TX_LOSS = [
    dict(name="하모닉 필터", loss=1.5),
    dict(name="T/R 스위치",  loss=1.0),
]
PA = dict(name="PA", p1db_dbm=32.0, gain=30.0)

# 주파수 계획
PLAN = dict(f_rf=2437.0e6, ch_bw=20e6,      # Wi-Fi 채널 6
            ref_clk=40.0e6, mcu_clk=26.0e6, smps=2.0e6)


# ══════════════════════════════════════════════ 캐스케이드
def cascade(chain):
    """Friis 로 잡음지수를, 역수합으로 IIP3 를 합친다 (→ M12 §2·§3).

    두 법칙이 서로 반대 방향으로 당긴다:
      · 잡음지수는 앞단 이득을 키울수록 **좋아진다**
      · IIP3 는 앞단 이득을 키울수록 **나빠진다**
    그래서 한 모드로 둘 다 만족시키지 못하는 일이 흔하다. AGC 가 그 답이다.
    """
    g_total, f_total, inv_iip3, rows = 0.0, 1.0, 0.0, []
    for st in chain:
        g_prev = un(g_total)             # 이 단 앞까지의 누적 이득 (선형)
        f_total += (un(st["nf"]) - 1.0) / g_prev
        inv_iip3 += g_prev / un(st["iip3"])
        g_total += st["gain"]
        rows.append(dict(name=st["name"], gain=st["gain"], g_cum=g_total,
                         nf_cum=db(f_total), iip3_cum=db(1.0 / inv_iip3)))
    return dict(gain=g_total, nf=db(f_total), iip3=db(1.0 / inv_iip3), rows=rows)


def sensitivity(nf_db, bw_hz, snr_db):
    """감도 = 열잡음 + 잡음지수 + 필요한 SNR (→ M12 §5)."""
    return K_T0 + db(bw_hz) + nf_db + snr_db


# ══════════════════════════════════════════════ 요구 정합성
def requirement_audit(req, modes=None, mode_for=None):
    """요구사항끼리 모순이 없는지 **부품을 고르기 전에** 본다.

    모순인 요구를 받아 놓고 설계를 시작하면, 끝까지 가서야 안 된다는 것을
    알게 된다. 그때는 이미 보드가 나와 있다.
    """
    out = []

    # ① 감도 ↔ 잡음지수 ↔ 대역폭
    floor = K_T0 + db(req["bw"]) + req["nf_max_db"]
    snr_implied = req["sens_dbm"] - floor
    out.append(dict(
        item="감도 ↔ 잡음지수 ↔ 대역폭",
        detail=(f"NF {req['nf_max_db']:.1f} dB 이면 잡음바닥 {floor:.1f} dBm. "
                f"감도 {req['sens_dbm']:.0f} dBm 이려면 SNR {snr_implied:.1f} dB "
                f"로 충분해야 하는데, 이 파형은 {req['snr_req_db']:.1f} dB 를 요구한다"),
        fix="감도를 완화하거나 · 기준 대역폭을 좁히거나 · NF 를 더 조인다",
        ok=snr_implied >= req["snr_req_db"],
        gap=snr_implied - req["snr_req_db"]))

    # ② 송신 출력 ↔ 안테나 이득 ↔ EIRP 규제
    eirp = req["pout_dbm"] + req["ant_gain_dbi"]
    out.append(dict(
        item="송신 출력 ↔ 안테나 이득 ↔ EIRP 규제",
        detail=(f"출력 +{req['pout_dbm']:.0f} dBm + 안테나 "
                f"{req['ant_gain_dbi']:.0f} dBi = EIRP {eirp:.0f} dBm, "
                f"규제 상한 {req['eirp_limit_dbm']:.0f} dBm"),
        fix="출력을 낮추거나 · 안테나 이득을 낮춘다 (규제는 협상 대상이 아니다)",
        ok=eirp <= req["eirp_limit_dbm"],
        gap=req["eirp_limit_dbm"] - eirp))

    # ③ 잡음지수 ↔ 선형성 — 한 모드로 둘 다 되는가
    if modes:
        both = []
        for name, chain in modes.items():
            c = cascade(chain)
            both.append((name, c["nf"] <= req["nf_max_db"],
                         c["iip3"] >= req["iip3_min_dbm"], c))
        single = [n for n, a, b, _ in both if a and b]
        detail = " · ".join(
            f"{n} 모드 NF {c['nf']:.2f} dB / IIP3 {c['iip3']:+.2f} dBm"
            for n, _, _, c in both)
        out.append(dict(
            item="잡음지수 ↔ 선형성 (한 모드로 동시에?)",
            detail=detail,
            fix=("AGC 로 모드를 나누고, 요구서에 **어느 모드에서 만족하는지**를 "
                 "명시한다 (→ M12 §4)"),
            ok=bool(single),
            gap=None))

    # ④ EVM ↔ 백오프 (모순이 아니라 설계 부담)
    evm_db = 20 * math.log10(req["evm_max_pct"] / 100.0)
    out.append(dict(
        item="EVM ↔ 백오프",
        detail=(f"EVM {req['evm_max_pct']:.0f} % = {evm_db:.1f} dB → 송신 "
                f"신호대잡음이 {-evm_db:.1f} dB 이상이어야 한다. "
                f"PAPR {req['papr_db']:.0f} dB 이면 첨두는 평균보다 "
                f"{req['papr_db']:.0f} dB 위"),
        fix="백오프를 키우거나 · CFR 로 PAPR 를 줄이거나 · DPD 를 쓴다 (→ M13 §8)",
        ok=True, gap=None))

    return out


# ══════════════════════════════════════════════ 송신
def tx_budget(pa, losses, req):
    """PA 출력에서 안테나 단자까지, 그리고 백오프를 본다."""
    loss_total = sum(l["loss"] for l in losses)
    pa_out_needed = req["pout_dbm"] + loss_total
    peak = pa_out_needed + req["papr_db"]
    return dict(loss_total=loss_total, pa_out_needed=pa_out_needed, peak=peak,
                backoff=pa["p1db_dbm"] - pa_out_needed,
                headroom=pa["p1db_dbm"] - peak,
                eirp=req["pout_dbm"] + req["ant_gain_dbi"])


# ══════════════════════════════════════════════ 스퍼
def spur_table(plan, band, max_order=SPUR_MAX_ORDER):
    """클럭 하모닉이 대역에, 그리고 **운용 채널에** 떨어지는지 본다 (→ M09 §6).

    차수를 끊는 이유: 2 MHz 스위칭의 1220차 하모닉도 산술적으로는 2440 MHz 에
    떨어지지만 세기는 이미 잡음바닥 아래다. 안 끊으면 표가 수백 줄이 되어
    정작 봐야 할 저차 하모닉이 묻힌다.
    """
    lo, hi = band
    ch_lo = plan["f_rf"] - plan["ch_bw"] / 2
    ch_hi = plan["f_rf"] + plan["ch_bw"] / 2
    hits, skipped = [], 0
    for src, f0 in (("기준 클럭", plan["ref_clk"]),
                    ("MCU 클럭", plan["mcu_clk"]),
                    ("스위칭 레귤레이터", plan["smps"])):
        for n in range(1, int(hi // f0) + 2):
            f = n * f0
            if not (lo <= f <= hi):
                continue
            if n > max_order:
                skipped += 1
                continue
            hits.append(dict(src=src, f0=f0, n=n, f=f,
                             delta=f - plan["f_rf"],
                             in_channel=ch_lo <= f <= ch_hi))
    return hits, skipped


def spur_avoidable(band, f0):
    """이 클럭의 하모닉을 대역 밖으로 뺄 수 있는가.

    하모닉 간격이 곧 클럭 주파수다. 그 간격이 대역폭보다 좁으면 어느 하나는
    반드시 대역 안에 들어온다 — **주파수 계획으로는 못 없앤다.**
    """
    lo, hi = band
    n_in = [n for n in range(1, int(hi // f0) + 2) if lo <= n * f0 <= hi]
    return dict(f0=f0, n_in=len(n_in), possible=f0 > (hi - lo))


def isolation_needed(spurs, rx_nf_db, req, margin_db=10.0, src_level_dbm=-30.0):
    """대역 내 하모닉을 못 없앤다면, **얼마나 격리해야 하는가**.

    이것이 진짜 설계 요구다. 배치·접지·차폐(→ M17 §6·§8·§10)가 이 숫자를
    만들어 내야 한다.
    """
    floor = K_T0 + db(req["bw"]) + rx_nf_db
    allowed = floor - margin_db          # 수신 입력에서 허용되는 스퍼 세기
    worst = [s for s in spurs if s["in_channel"]]
    return dict(floor=floor, allowed=allowed, src=src_level_dbm,
                need_db=src_level_dbm - allowed,
                in_channel=len(worst), worst=worst)


# ══════════════════════════════════════════════ 판정
def verdict(req, modes, mode_for, tx, spurs):
    checks = []

    def add(name, value, limit, better_low, unit="dB", note=""):
        ok = value <= limit if better_low else value >= limit
        checks.append(dict(name=name, value=value, limit=limit, ok=ok,
                           margin=(limit - value) if better_low else (value - limit),
                           unit=unit, note=note))

    c_nf = cascade(modes[mode_for["nf"]])
    c_ip = cascade(modes[mode_for["iip3"]])
    add("수신 잡음지수", c_nf["nf"], req["nf_max_db"], True,
        note=f"{mode_for['nf']} 모드")
    add("수신 감도", sensitivity(c_nf["nf"], req["bw"], req["snr_req_db"]),
        req["sens_dbm"], True, "dBm", f"{mode_for['sens']} 모드")
    add("수신 IIP3", c_ip["iip3"], req["iip3_min_dbm"], False, "dBm",
        f"{mode_for['iip3']} 모드")
    add("EIRP", tx["eirp"], req["eirp_limit_dbm"], True, "dBm")
    add("PA 첨두 여유", tx["headroom"], 0.0, False, note="P1dB − 첨두")
    iso = isolation_needed(spurs, c_nf["nf"], req)
    add("클럭 격리 요구", iso["need_db"], 80.0, True,
        note=f"채널 내 하모닉 {iso['in_channel']}건")
    return checks, iso


# ══════════════════════════════════════════════ 출력
def report():
    print("=" * 74)
    print("캡스톤 자체 검산 — 2.4 GHz 송수신 겸용 트랜시버")
    print("=" * 74)

    print("\n[1] 요구사항 정합성 — 부품을 고르기 전에")
    audit = requirement_audit(REQ, RX_MODES, MODE_FOR)
    for a in audit:
        print(f"  [{'OK  ' if a['ok'] else '모순'}] {a['item']}")
        print(f"         {a['detail']}")
        if not a["ok"]:
            if a["gap"] is not None:
                print(f"         → {abs(a['gap']):.1f} dB 모자란다")
            print(f"         → 협의안: {a['fix']}")

    print("\n[2] 수신 캐스케이드 예산 (AGC 두 모드)")
    for mode, chain in RX_MODES.items():
        c = cascade(chain)
        print(f"\n  ── {mode} 모드")
        print(f"  {'단':16s} {'이득':>6s} {'누적이득':>8s} {'누적NF':>7s} {'누적IIP3':>9s}")
        for r in c["rows"]:
            print(f"  {r['name']:16s} {r['gain']:+6.1f} {r['g_cum']:+8.1f}"
                  f" {r['nf_cum']:7.2f} {r['iip3_cum']:+9.2f}")
        sens = sensitivity(c["nf"], REQ["bw"], REQ["snr_req_db"])
        print(f"  {'→ 합계':16s} {'':6s} {c['gain']:+8.1f}"
              f" {c['nf']:7.2f} {c['iip3']:+9.2f}   감도 {sens:.1f} dBm")

    print("\n[3] 송신 예산")
    tx = tx_budget(PA, TX_LOSS, REQ)
    parts = " + ".join(f"{l['name']} {l['loss']:.1f}" for l in TX_LOSS)
    print(f"  PA 뒤 손실 합계        {tx['loss_total']:.1f} dB  ({parts})")
    print(f"  안테나 단자 +{REQ['pout_dbm']:.0f} dBm 이려면 PA 출력"
          f"  {tx['pa_out_needed']:+.1f} dBm")
    print(f"  PAPR {REQ['papr_db']:.0f} dB → 첨두 {tx['peak']:+.1f} dBm")
    print(f"  PA P1dB {PA['p1db_dbm']:+.1f} dBm → 평균 대비 백오프"
          f" {tx['backoff']:.1f} dB · 첨두 여유 {tx['headroom']:+.1f} dB")
    print(f"  EIRP {tx['eirp']:.1f} dBm (안테나 {REQ['ant_gain_dbi']:.0f} dBi)")

    print(f"\n[4] 클럭 하모닉 ({SPUR_MAX_ORDER}차까지) — 운용 채널 "
          f"{PLAN['f_rf']/1e6:.0f} MHz ± {PLAN['ch_bw']/2e6:.0f} MHz")
    spurs, skipped = spur_table(PLAN, REQ["band"])
    for s in spurs:
        mark = " ← 채널 안" if s["in_channel"] else ""
        print(f"  {s['src']:10s} {s['f0']/1e6:6.1f} MHz × {s['n']:3d}"
              f" = {s['f']/1e6:9.3f} MHz   수신 주파수에서"
              f" {s['delta']/1e6:+7.3f} MHz{mark}")
    if skipped:
        print(f"  ({SPUR_MAX_ORDER}차 초과 {skipped}건은 세기가 잡음바닥 아래라 뺐다"
              f" — 대부분 스위칭 레귤레이터다)")

    print("\n  주파수 계획으로 뺄 수 있는가?")
    for name, f0 in (("기준 클럭", PLAN["ref_clk"]), ("MCU 클럭", PLAN["mcu_clk"])):
        a = spur_avoidable(REQ["band"], f0)
        print(f"    {name} {f0/1e6:.1f} MHz: 대역 내 {a['n_in']}개 · "
              f"{'다른 값으로 뺄 수 있다' if a['possible'] else '클럭이 대역폭보다 낮아 못 뺀다'}")
    print(f"    (대역폭 {(REQ['band'][1]-REQ['band'][0])/1e6:.1f} MHz 보다 낮은 클럭은"
          f" 하모닉 간격이 더 좁아 반드시 하나는 들어온다)")

    print("\n[5] 판정")
    checks, iso = verdict(REQ, RX_MODES, MODE_FOR, tx, spurs)
    print(f"  {'항목':14s} {'값':>9s} {'요구':>9s} {'마진':>8s}  판정   비고")
    for c in checks:
        print(f"  {c['name']:14s} {c['value']:9.2f} {c['limit']:9.2f}"
              f" {c['margin']:+8.2f}  {'합격' if c['ok'] else '불합격'}"
              f"   {c['note']}")

    print(f"\n  클럭 격리 요구의 근거: 수신 잡음바닥 {iso['floor']:.1f} dBm,"
          f" 그보다 10 dB 아래인 {iso['allowed']:.1f} dBm 까지만 허용.")
    print(f"  클럭 배선의 하모닉을 {iso['src']:.0f} dBm 로 보면"
          f" **{iso['need_db']:.0f} dB 격리**가 필요하다 — 배치·접지·차폐가 만들 몫이다"
          f" (→ M17 §6·§8·§10).")

    n_bad = sum(1 for c in checks if not c["ok"])
    n_conf = sum(1 for a in audit if not a["ok"])
    print(f"\n  요구 모순 {n_conf}건 · 판정 불합격 {n_bad}건")
    if n_conf:
        print("  ⇒ 요구사항부터 협의해야 한다. 설계로는 못 푼다.")
    return dict(audit=audit, tx=tx, spurs=spurs, checks=checks)


# ══════════════════════════════════════════════ 도구 자체의 검산
def self_test():
    ok = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  [{'OK ' if cond else 'FAIL'}] {msg}")

    print("\n[자체 검산]")

    # ── 캐스케이드를 손으로 푼 2단과 대조
    two = [dict(name="a", gain=10.0, nf=2.0, iip3=0.0),
           dict(name="b", gain=10.0, nf=10.0, iip3=0.0)]
    c = cascade(two)
    f_hand = un(2.0) + (un(10.0) - 1.0) / un(10.0)
    chk(abs(c["nf"] - db(f_hand)) < 1e-9,
        f"Friis 2단: 코드 {c['nf']:.4f} vs 손계산 {db(f_hand):.4f} dB")
    ip_hand = 1.0 / (1.0 / un(0.0) + un(10.0) / un(0.0))
    chk(abs(c["iip3"] - db(ip_hand)) < 1e-9,
        f"IIP3 2단: 코드 {c['iip3']:.4f} vs 손계산 {db(ip_hand):.4f} dBm")

    # ── 두 법칙이 반대로 당기는지 (M12 의 핵심)
    hi = cascade(RX_MODES["고이득"])
    lo = cascade(RX_MODES["저이득"])
    chk(hi["nf"] < lo["nf"] and hi["iip3"] < lo["iip3"],
        f"LNA 를 켜면 NF {lo['nf']:.2f}→{hi['nf']:.2f} dB (좋아짐), "
        f"IIP3 {lo['iip3']:+.2f}→{hi['iip3']:+.2f} dBm (나빠짐)")
    chk(abs(hi["gain"] - lo["gain"]) < 0.01,
        f"두 모드의 총이득을 VGA 로 맞춰 놨다 ({hi['gain']:+.1f} dB)")

    # ── 한 모드로는 두 요구를 동시에 못 만족한다
    both = [(n, cascade(ch)) for n, ch in RX_MODES.items()]
    none_both = all(not (c["nf"] <= REQ["nf_max_db"]
                         and c["iip3"] >= REQ["iip3_min_dbm"])
                    for _, c in both)
    chk(none_both,
        "어느 한 모드도 NF≤4 와 IIP3≥−10 을 동시에 만족하지 못한다 "
        "— AGC 가 필요한 이유")
    chk(hi["nf"] <= REQ["nf_max_db"],
        f"고이득 모드가 잡음지수 요구를 만족한다 ({hi['nf']:.2f} ≤ 4.0 dB)")
    chk(lo["iip3"] >= REQ["iip3_min_dbm"],
        f"저이득 모드가 선형성 요구를 만족한다 ({lo['iip3']:+.2f} ≥ −10 dBm)")

    # ── 감도 공식
    chk(abs((sensitivity(4.0, 80e6, 5.0) - sensitivity(4.0, 20e6, 5.0)) - db(4.0)) < 1e-9,
        "대역폭 4배 → 감도가 6.02 dB 나빠진다 (= 10log10 4)")
    k, t0 = 1.380649e-23, 290.0
    chk(abs(db(k * t0 * 1000.0) - K_T0) < 0.05,
        f"kT0 = {db(k * t0 * 1000.0):.2f} dBm/Hz (쓰는 값 {K_T0})")

    # ── 요구 정합성: 모순 두 건을 실제로 잡아내는가
    audit = requirement_audit(REQ, RX_MODES, MODE_FOR)
    bad = [a["item"] for a in audit if not a["ok"]]
    chk(len(bad) == 3, f"요구 모순 {len(bad)}건을 잡아냄: {' · '.join(bad)}")

    # 감도를 딱 3 dB 완화하면 **마진 0** 이다. 마진 0 은 설계가 아니다.
    floor = K_T0 + db(REQ["bw"]) + REQ["nf_max_db"]
    breakeven = floor + REQ["snr_req_db"]
    chk(abs(breakeven - (-91.9897)) < 0.001,
        f"성립하는 감도의 한계는 {breakeven:.4f} dBm")
    chk(not requirement_audit(dict(REQ, sens_dbm=-92.0))[0]["ok"],
        f"−92.0 dBm 로 완화해도 {abs(-92.0 - breakeven):.4f} dB 모자란다 "
        f"— 딱 맞춰서는 안 된다")
    a91 = requirement_audit(dict(REQ, sens_dbm=-91.0))[0]
    chk(a91["ok"] and a91["gap"] > 0.9,
        f"−91 dBm 이면 마진 {a91['gap']:.2f} dB 로 성립한다")
    chk(requirement_audit(dict(REQ, ant_gain_dbi=0.0))[1]["ok"],
        "안테나를 0 dBi 로 낮추면 두 번째 모순이 풀린다")
    chk(requirement_audit(dict(REQ, bw=10e6))[0]["ok"],
        "기준 대역폭을 10 MHz 로 좁혀도 첫 모순이 풀린다 (다른 협의안)")

    # ── 스퍼
    spurs, skipped = spur_table(PLAN, REQ["band"])
    got = {(s["src"], s["n"]) for s in spurs}
    chk(("기준 클럭", 61) in got, "40 MHz × 61 = 2440 MHz 가 대역 안에 잡힌다")
    chk(("MCU 클럭", 94) in got, "26 MHz × 94 = 2444 MHz 가 대역 안에 잡힌다")
    chk(all(REQ["band"][0] <= s["f"] <= REQ["band"][1] for s in spurs),
        f"잡힌 하모닉 {len(spurs)}건이 모두 대역 안에 있다")
    chk(skipped > 0 and all(s["n"] <= SPUR_MAX_ORDER for s in spurs),
        f"{SPUR_MAX_ORDER}차 초과 {skipped}건은 뺐다 (안 끊으면 표가 못 쓰게 된다)")

    # 대역폭보다 낮은 클럭은 하모닉을 대역 밖으로 못 뺀다
    bw_band = REQ["band"][1] - REQ["band"][0]
    for f0 in (26e6, 40e6, 52e6):
        chk(not spur_avoidable(REQ["band"], f0)["possible"]
            and spur_avoidable(REQ["band"], f0)["n_in"] >= 1,
            f"{f0/1e6:.0f} MHz 클럭({bw_band/1e6:.1f} MHz 미만)은 대역 내 하모닉을 "
            f"못 없앤다 ({spur_avoidable(REQ['band'], f0)['n_in']}개)")
    chk(spur_avoidable(REQ["band"], 100e6)["possible"],
        "100 MHz 클럭은 대역폭보다 높아 원리적으로 뺄 수 있다")
    chk(any(s["in_channel"] for s in spurs),
        f"운용 채널 {PLAN['f_rf']/1e6:.0f} MHz 안에도 하모닉이 있다 "
        f"— 채널을 옮겨도 다른 하모닉을 만난다")

    # 격리 요구가 계산되는가
    iso = isolation_needed(spurs, cascade(RX_MODES["고이득"])["nf"], REQ)
    chk(60.0 < iso["need_db"] < 100.0,
        f"필요한 클럭 격리 {iso['need_db']:.0f} dB "
        f"(잡음바닥 {iso['floor']:.1f} dBm 의 10 dB 아래까지 허용)")

    # ── 송신
    tx = tx_budget(PA, TX_LOSS, REQ)
    chk(abs(tx["pa_out_needed"] - (REQ["pout_dbm"] + 2.5)) < 1e-9,
        f"PA 출력 = 안테나 단자 + 손실 2.5 dB = {tx['pa_out_needed']:+.1f} dBm")
    chk(tx["headroom"] < 0,
        f"첨두 {tx['peak']:+.1f} dBm 가 P1dB {PA['p1db_dbm']:+.1f} dBm 를 "
        f"{-tx['headroom']:.1f} dB 넘는다 → CFR/DPD 나 더 큰 PA 가 필요하다")

    print("\n전부 통과" if all(ok) else f"\n{ok.count(False)}개 실패")
    return all(ok)


if __name__ == "__main__":
    report()
    if "--self" in sys.argv:
        self_test()
