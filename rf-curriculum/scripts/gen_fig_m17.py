"""M17 — RF 보드 설계와 인증. 데이터 그림과 자체 검산.

보드 설계는 "그려 놓고 나중에 재는" 일이 아니라, **만들기 전에 계산으로
결정하는** 일이다. 그래서 이 모듈의 그림은 전부 설계 판단에 쓰는 숫자다.

두 경로로 독립 계산해 맞춰 보는 곳
  · 마이크로스트립 손실: 손으로 쓴 도체손실+유전체손실 vs scikit-rf MLine
  · 임피던스 제조 공차: 편미분 감도의 RSS vs 몬테카를로 20만 회
  · PDN 임피던스: 손으로 쓴 병렬 합성 vs scikit-rf 회로 조립
"""
import numpy as np
import skrf as rf
from skrf.media import MLine

import rf_style as S

C0 = 299_792_458.0
MU0 = 4e-7 * np.pi
RHO_CU = 1.72e-8            # 구리 비저항 (Ω·m)


# ══════════════════════════════════════ 마이크로스트립 기본식
def microstrip(w, h, er):
    """Hammerstad 근사식. Z0 와 유효 유전율을 돌려준다.

    식 자체는 M02 가 소유한다. 여기서는 **재료·공차 판단의 도구**로만 쓴다.
    공차 몬테카를로에서 20만 번 부르므로 배열로 한 번에 계산한다.
    """
    u = np.asarray(w, dtype=float) / np.asarray(h, dtype=float)
    er = np.asarray(er, dtype=float)

    e_narrow = (er + 1) / 2 + (er - 1) / 2 * (
        (1 + 12 / u) ** -0.5 + 0.04 * np.clip(1 - u, 0, None) ** 2)
    e_wide = (er + 1) / 2 + (er - 1) / 2 * (1 + 12 / u) ** -0.5
    e_eff = np.where(u <= 1.0, e_narrow, e_wide)

    z_narrow = 60 / np.sqrt(e_eff) * np.log(8 / u + u / 4)
    z_wide = 120 * np.pi / (np.sqrt(e_eff)
                            * (u + 1.393 + 0.667 * np.log(u + 1.444)))
    z0 = np.where(u <= 1.0, z_narrow, z_wide)

    if np.isscalar(w) and np.isscalar(h) and np.ndim(er) == 0:
        return float(z0), float(e_eff)
    return z0, e_eff


def width_for_50(h, er, z_target=50.0):
    """이분법으로 목표 임피던스가 되는 선폭을 찾는다."""
    lo, hi = 0.02 * h, 20.0 * h
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        z, _ = microstrip(mid, h, er)
        if z > z_target:          # 선폭이 좁으면 임피던스가 높다
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ══════════════════════════════════════ ① 재료별 손실
def loss_by_hand(f, w, h, t, er, tand, k_rough=1.0):
    """마이크로스트립 손실 (dB/m). 도체손실과 유전체손실을 따로 계산한다.

    유전체손실 (모든 교재가 같은 식)
        alpha_d = pi/lambda0 * (e_eff-1)/(e_eff-1+... ) 형태의 채움계수를 쓴다.
        여기서는 널리 쓰이는 형태를 그대로 쓴다:
        alpha_d [Np/m] = pi*f/c * (er*(e_eff-1))/(sqrt(e_eff)*(er-1)) * tand

    도체손실 (표피효과)
        Rs = sqrt(pi*f*mu0*rho)  [Ω/sq]
        alpha_c [Np/m] = Rs / (Z0 * w)      (넓은 선폭 근사)
        거칠기는 Hammerstad 계수로 Rs 를 키운다.
    """
    z0, e_eff = microstrip(w, h, er)

    alpha_d = (np.pi * f / C0) * (er * (e_eff - 1.0)) / (
        np.sqrt(e_eff) * (er - 1.0)) * tand

    rs = np.sqrt(np.pi * f * MU0 * RHO_CU)
    alpha_c = k_rough * rs / (z0 * w)

    return alpha_c * 8.6859, alpha_d * 8.6859, z0, e_eff


def roughness_factor(f, rq):
    """Hammerstad 거칠기 계수. 표피깊이보다 거칠면 도체손실이 커진다.

    K = 1 + (2/pi) * arctan(1.4 * (Rq/delta)^2),  최대 2배까지 간다.
    """
    delta = np.sqrt(RHO_CU / (np.pi * f * MU0))
    return 1.0 + (2.0 / np.pi) * np.arctan(1.4 * (rq / delta) ** 2)


MATERIALS = [
    # 이름,        Dk,   Df,     거칠기 Rq(m), 색, 선모양
    ("FR-4",       4.30, 0.0200, 2.0e-6, 0, "-"),
    ("RO4350B",    3.66, 0.0037, 0.4e-6, 1, "--"),
    ("PTFE 계열",  2.20, 0.0009, 0.3e-6, 2, ":"),
]
H_SUB = 0.508e-3        # 20 mil
T_CU = 35e-6            # 1 oz


def fig_material_loss():
    f = np.logspace(np.log10(0.1e9), np.log10(20e9), 300)

    fig, (ax1, ax2) = S.figure(9.0, 7.2, nrows=2,
                               gridspec_kw=dict(hspace=0.34))

    rows, checks = [], []
    for name, er, tand, rq, ci, ls in MATERIALS:
        w = width_for_50(H_SUB, er)
        kr = roughness_factor(f, rq)
        ac, ad, z0, e_eff = loss_by_hand(f, w, H_SUB, T_CU, er, tand, kr)
        total = ac + ad

        ax1.plot(f, total / 100.0, color=S.COLORS[ci], lw=2.4, ls=ls,
                 label=f"{name}  (Dk {er}, Df {tand})")

        # 5.8 GHz 에서 두 손실의 몫
        k = int(np.argmin(np.abs(f - 5.8e9)))
        rows.append(dict(name=name, er=er, tand=tand, w=w, z0=z0,
                         e_eff=e_eff, rq=rq,
                         ac=ac[k] / 100.0, ad=ad[k] / 100.0,
                         tot=total[k] / 100.0, kr=kr[k]))
        checks.append((name, w, f, total))

        # 아래 칸: FR-4 만 도체/유전체를 갈라 보인다
        if name == "FR-4":
            ax2.plot(f, ac / 100.0, color=S.COLORS[0], lw=2.4,
                     label="도체 손실 (표피효과 + 거칠기)")
            ax2.plot(f, ad / 100.0, color=S.COLORS[1], lw=2.4, ls="--",
                     label="유전체 손실 (Df)")
            ax2.plot(f, total / 100.0, color=S.INK, lw=1.6, ls=":",
                     label="합계")
            kx = int(np.argmin(np.abs(ac - ad)))
            f_cross = f[kx]
            ax2.axvline(f_cross, color=S.MUTED, lw=1.2, ls="-.")
            ax2.annotate(f"여기서 뒤바뀐다\n{f_cross/1e9:.2f} GHz",
                         xy=(f_cross, ac[kx] / 100.0),
                         xytext=(f_cross * 2.6, ac[kx] / 100.0 * 0.30),
                         fontsize=9, color=S.MUTED, fontweight="bold",
                         ha="center",
                         bbox=dict(fc="white", ec=S.MUTED, lw=1.0, alpha=0.96),
                         arrowprops=dict(arrowstyle="->", color=S.MUTED, lw=1.3))

    for ax in (ax1, ax2):
        ax.set_xscale("log")
        ax.set_yscale("log")
        S.plain_log(ax)
        S.hz_ticks(ax, [1e8, 3e8, 1e9, 3e9, 1e10, 2e10])
        ax.set_xlim(1e8, 2e10)
    ax1.set_ylabel("삽입손실 (dB/cm)")
    ax1.set_xlabel("주파수")
    ax1.legend(fontsize=8.6, loc="upper left", framealpha=0.96)
    ax1.set_title("그림 M17-1  재료가 손실을 정한다 — 50 Ω 마이크로스트립, 기판 0.508 mm")
    ax2.set_ylabel("삽입손실 (dB/cm)")
    ax2.set_xlabel("주파수")
    ax2.legend(fontsize=8.6, loc="upper left", framealpha=0.96)
    ax2.set_title("FR-4 의 손실을 갈라 보면 — 낮은 데서는 도체, 높은 데서는 유전체")
    S.save(fig, "M17", "material_loss")

    return rows, checks, f_cross


def loss_via_skrf(w, er, tand, f):
    """같은 손실을 scikit-rf 의 MLine 으로 계산한다 — 교차검증용.

    scikit-rf 는 도체 거칠기를 따로 모형화하므로 rough=0 으로 두고
    **매끈한 도체**끼리 비교한다. 유전체 분산도 끄고 상수 Dk 로 맞춘다.
    """
    freq = rf.Frequency.from_f(f / 1e9, unit="ghz")
    m = MLine(frequency=freq, w=w, h=H_SUB, t=T_CU, ep_r=er, tand=tand,
              rho=RHO_CU, rough=0.0, diel="frequencyinvariant",
              disp="hammerstadjensen")
    return m.alpha * 8.6859, m.z0.real


# ══════════════════════════════════════ ② 임피던스 제조 공차
TOL = dict(w=15e-6,        # 에칭 공차 ±15 um (1 sigma)
           h=15e-6,        # 프리프레그 두께 ±15 um
           er=0.05)        # Dk 산포 ±0.05


def z0_sensitivity(w0, h0, er0):
    """편미분으로 감도를 구하고 RSS 로 합친다 (M14 §10 의 불확도 합성과 같은 방법)."""
    d = 1e-9
    dz_dw = (microstrip(w0 + d, h0, er0)[0] - microstrip(w0 - d, h0, er0)[0]) / (2 * d)
    dz_dh = (microstrip(w0, h0 + d, er0)[0] - microstrip(w0, h0 - d, er0)[0]) / (2 * d)
    de = 1e-6
    dz_de = (microstrip(w0, h0, er0 + de)[0] - microstrip(w0, h0, er0 - de)[0]) / (2 * de)

    parts = dict(w=abs(dz_dw) * TOL["w"],
                 h=abs(dz_dh) * TOL["h"],
                 er=abs(dz_de) * TOL["er"])
    rss = np.sqrt(sum(v ** 2 for v in parts.values()))
    return parts, rss


def fig_tolerance():
    er0 = 3.66
    h0 = H_SUB
    w0 = width_for_50(h0, er0)
    z_nom, _ = microstrip(w0, h0, er0)

    parts, rss = z0_sensitivity(w0, h0, er0)

    # 몬테카를로 — 근사 없이 Hammerstad 식을 그대로 20만 번 돌린다
    rng = np.random.default_rng(20260821)
    n = 200_000
    ws = rng.normal(w0, TOL["w"], n)
    hs = rng.normal(h0, TOL["h"], n)
    ers = rng.normal(er0, TOL["er"], n)
    zs = microstrip(ws, hs, ers)[0]

    fig, (ax1, ax2) = S.figure(9.0, 7.2, nrows=2,
                               gridspec_kw=dict(hspace=0.36))

    ax1.hist(zs, bins=140, density=True, color=S.COLORS[0], alpha=0.55,
             label=f"제조 산포 (Hammerstad 식 몬테카를로 {n//10000}만 회)")
    xs = np.linspace(zs.min(), zs.max(), 400)
    ax1.plot(xs, np.exp(-0.5 * ((xs - z_nom) / rss) ** 2)
             / (rss * np.sqrt(2 * np.pi)),
             color=S.COLORS[1], lw=2.4, ls="--",
             label=f"감도 RSS 로 계산한 분포 (σ = {rss:.2f} Ω)")

    yields = {}
    for band, col, ls in ((10.0, S.ACCENT, "-"), (5.0, S.COLORS[2], ":")):
        lo, hi = 50 * (1 - band / 100), 50 * (1 + band / 100)
        y = float(np.mean((zs >= lo) & (zs <= hi))) * 100
        yields[band] = (lo, hi, y)
        for x in (lo, hi):
            ax1.axvline(x, color=col, lw=2.0, ls=ls)
    # 라벨은 축 안쪽으로. 바깥에 두면 그림 가장자리에서 잘린다.
    ax1.text(54.85, 0.115,
             S.txt(f"±10 % 규격 45 ~ 55 Ω\n{yields[10.0][2]:.1f} % 통과"),
             color=S.ACCENT, fontsize=9, fontweight="bold", ha="right",
             va="center", bbox=dict(fc="white", ec=S.ACCENT, lw=0.9, alpha=0.95))
    ax1.text(52.40, 0.255,
             S.txt(f"±5 % 규격 47.5 ~ 52.5 Ω\n{yields[5.0][2]:.1f} % 통과"),
             color=S.COLORS[2], fontsize=9, fontweight="bold", ha="right",
             va="center", bbox=dict(fc="white", ec=S.COLORS[2], lw=0.9, alpha=0.95))
    ax1.set_xlabel("만들어진 선로의 특성 임피던스 (Ω)")
    ax1.set_ylabel("확률밀도")
    ax1.legend(fontsize=8.6, loc="upper left", framealpha=0.96)
    ax1.set_title("그림 M17-3  같은 도면으로 만들어도 임피던스는 흩어진다")

    # 아래: 무엇이 얼마나 기여하는가
    names = {"w": "선폭 W  (±15 μm)", "h": "기판 두께 h  (±15 μm)",
             "er": "유전율 Dk  (±0.05)"}
    keys = ["er", "w", "h"]          # barh 는 아래부터 그린다 -> 큰 것이 위로
    vals = [parts[k] for k in keys]
    bars = ax2.barh([names[k] for k in keys], vals,
                    color=[S.COLORS[0], S.COLORS[1], S.COLORS[4]], height=0.55)
    for b, v in zip(bars, vals):
        ax2.text(v + 0.02, b.get_y() + b.get_height() / 2,
                 f"{v:.2f} Ω  ({v**2/rss**2*100:.0f} %)",
                 va="center", fontsize=9, fontweight="bold", color=S.INK)
    ax2.axvline(rss, color=S.ACCENT, lw=2.0, ls="--")
    ax2.text(rss * 1.02, 2.42, S.txt(f"RSS 합계 {rss:.2f} Ω"), color=S.ACCENT,
             fontsize=9.5, fontweight="bold", ha="left", va="top")
    ax2.set_ylim(-0.6, 2.6)
    ax2.set_xlim(0, max(vals) * 1.45)
    ax2.set_xlabel("임피던스 산포에 대한 기여 (Ω, 1σ)")
    ax2.set_title("무엇을 조여야 하는가 — 기여도 순")
    S.save(fig, "M17", "tolerance")

    return dict(w0=w0, h0=h0, er0=er0, z_nom=z_nom, parts=parts, rss=rss,
                zs=zs, yields=yields)


# ══════════════════════════════════════ ③ PDN 임피던스
def pdn_by_hand(f, vrm, caps, plane_l):
    """전원 분배망의 |Z| 를 손으로 병렬 합성한다.

    VRM 은 낮은 주파수에서만 낮은 임피던스를 낸다: R + jwL
    커패시터 하나는 R_esr + jwL_esl + 1/(jwC)  (M06 의 SRF 모형 그대로)
    평면의 확산 인덕턴스는 마지막에 직렬로 붙는다.
    """
    w = 2 * np.pi * f
    y = 1.0 / (vrm["r"] + 1j * w * vrm["l"])
    for c in caps:
        z = c["esr"] + 1j * w * c["esl"] + 1.0 / (1j * w * c["c"])
        y = y + c["n"] / z
    return 1.0 / y + 1j * w * plane_l


def pdn_via_skrf(f, vrm, caps, plane_l):
    """같은 망을 scikit-rf 로 **부품 하나씩 조립해** 확인한다 — 교차검증용.

    손계산은 어드미턴스를 더하는 한 줄이고, 이쪽은 S-파라미터 회로망을
    직렬·병렬로 이어 붙인 뒤 Z 파라미터로 되돌린다. 계산 경로가 다르다.
    """
    freq = rf.Frequency.from_f(f / 1e9, unit="ghz")
    med = rf.media.DefinedGammaZ0(frequency=freq, z0=50)

    def branch(r, l, c=None):
        n = med.resistor(r) ** med.inductor(l)
        if c is not None:
            n = n ** med.capacitor(c)
        return n ** med.short()

    net = med.inductor(plane_l)                      # 평면 확산 인덕턴스
    net = net ** med.shunt(branch(vrm["r"], vrm["l"]))
    for c in caps:
        for _ in range(c["n"]):
            net = net ** med.shunt(branch(c["esr"], c["esl"], c["c"]))
    return (net ** med.open()).z[:, 0, 0]


def fig_pdn():
    f = np.logspace(np.log10(1e3), np.log10(1e9), 900)

    # 레귤레이터는 제어 루프가 도는 동안만 임피던스가 낮다. 그 위로는
    # 출력 인덕턴스만 남으므로 R + jwL 로 본다.
    vrm = dict(r=0.005, l=150e-9)
    caps = [
        dict(name="벌크 100 μF ×4", n=4, c=100e-6, esr=0.025, esl=2.0e-9),
        dict(name="10 μF ×4", n=4, c=10e-6, esr=0.005, esl=1.0e-9),
        dict(name="100 nF ×10", n=10, c=100e-9, esr=0.020, esl=0.6e-9),
        dict(name="1 nF ×6", n=6, c=1e-9, esr=0.060, esl=0.4e-9),
    ]
    plane_l = 0.05e-9           # 평면 확산 인덕턴스 (배치가 정한다)

    z_all = np.abs(pdn_by_hand(f, vrm, caps, plane_l))
    z_novrm = np.abs(pdn_by_hand(f, vrm, [], plane_l))
    # 100 nF 를 빼면 어떻게 되는가 (반공진 시연)
    z_gap = np.abs(pdn_by_hand(f, vrm, [c for c in caps
                                        if not c["name"].startswith("100 nF")],
                               plane_l))

    dv, di = 0.05, 1.0          # 허용 리플 50 mV, 과도 전류 1 A
    z_target = dv / di

    fig, ax = S.figure(9.0, 5.4)
    ax.plot(f, z_novrm, color=S.MUTED, lw=1.8, ls=":",
            label="VRM 만 (커패시터 없음)")
    ax.plot(f, z_gap, color=S.COLORS[4], lw=2.0, ls="--",
            label="100 nF 를 뺀 경우 — 반공진 봉우리")
    ax.plot(f, z_all, color=S.COLORS[0], lw=2.6, label="전체 디커플링")
    ax.axhline(z_target, color=S.ACCENT, lw=2.2, ls="-")
    ax.text(2e3, z_target * 1.35,
            S.txt(f"목표 임피던스 {z_target*1000:.0f} mΩ  "
                  f"(= {dv*1000:.0f} mV / {di:.0f} A)"),
            color=S.ACCENT, fontsize=9.5, fontweight="bold", ha="left")

    k = int(np.argmax(z_gap[(f > 3e6) & (f < 3e8)]))
    idx = np.where((f > 3e6) & (f < 3e8))[0][k]
    ax.annotate(f"{f[idx]/1e6:.0f} MHz 에서 {z_gap[idx]*1000:.0f} mΩ\n"
                f"— 커패시터를 뺐더니 목표의 {z_gap[idx]/z_target:.1f} 배",
                xy=(f[idx], z_gap[idx]),
                xytext=(f[idx] * 0.055, z_gap[idx] * 2.2),
                fontsize=9, color=S.COLORS[4], fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.COLORS[4], lw=1.0, alpha=0.96),
                arrowprops=dict(arrowstyle="->", color=S.COLORS[4], lw=1.3))

    ax.set_xscale("log")
    ax.set_yscale("log")
    S.plain_log(ax)
    S.hz_ticks(ax, [1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9])
    ax.set_xlim(1e3, 1e9)
    ax.set_ylim(1e-3, 3e1)
    ax.set_xlabel("주파수")
    ax.set_ylabel("전원망 임피던스 |Z| (Ω)")
    ax.legend(fontsize=8.8, loc="upper left", framealpha=0.96)
    ax.set_title("그림 M17-8  전원 분배망 — 목표선 아래로 눌러 두는 일")

    # 목표선을 지키는 상한 주파수 — 여기서부터는 커패시터로 안 된다
    under = z_all <= z_target
    f_hold = float(f[np.where(~under)[0][0] - 1]) if (~under).any() else float(f[-1])
    k_hold = int(np.argmin(np.abs(f - f_hold)))
    ax.axvline(f_hold, color=S.COLORS[2], lw=1.8, ls="--")
    ax.annotate(f"여기까지만 지켜진다\n{f_hold/1e6:.0f} MHz\n"
                f"— 위쪽은 평면 인덕턴스가 정한다",
                xy=(f_hold, z_target),
                xytext=(f_hold * 0.10, z_target * 0.16),
                fontsize=9, color=S.COLORS[2], fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.COLORS[2], lw=1.0, alpha=0.96),
                arrowprops=dict(arrowstyle="->", color=S.COLORS[2], lw=1.3))
    S.save(fig, "M17", "pdn")

    return dict(f=f, z_all=z_all, z_gap=z_gap, z_target=z_target,
                vrm=vrm, caps=caps, plane_l=plane_l,
                peak_f=f[idx], peak_z=z_gap[idx],
                f_hold=f_hold, k_hold=k_hold,
                worst_hold=float(np.max(z_all[f <= f_hold])))


# ══════════════════════════════════════ ④ 비아 스티칭 λ/20
def via_spacing_table():
    """λ/20 규칙을 재료·주파수별로 계산한다. 표로만 쓴다."""
    rows = []
    for name, er, *_ in MATERIALS:
        w = width_for_50(H_SUB, er)
        _, e_eff = microstrip(w, H_SUB, er)
        for f in (2.45e9, 5.8e9, 10e9):
            lam = C0 / (f * np.sqrt(e_eff))
            rows.append(dict(mat=name, f=f, e_eff=e_eff,
                             lam=lam, s20=lam / 20, s10=lam / 10))
    return rows


# ══════════════════════════════════════ 검산
def main():
    S.setup()
    ok = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  [{'OK ' if cond else 'FAIL'}] {msg}")

    mat_rows, mat_checks, f_cross = fig_material_loss()
    tol = fig_tolerance()
    pdn = fig_pdn()
    vias = via_spacing_table()

    print("\n[본문 인용값]")
    print("  50 Ω 선폭 (기판 0.508 mm) 과 5.8 GHz 손실")
    for r in mat_rows:
        print(f"    {r['name']:9s} Dk {r['er']:.2f} Df {r['tand']:.4f}"
              f" -> W {r['w']*1e3:.3f} mm · Z0 {r['z0']:.2f} Ω"
              f" · ε_eff {r['e_eff']:.2f}")
        print(f"      5.8 GHz: 도체 {r['ac']:.4f} + 유전체 {r['ad']:.4f}"
              f" = {r['tot']:.4f} dB/cm  (10 cm 면 {r['tot']*10:.2f} dB)"
              f" · 거칠기 계수 {r['kr']:.2f}")
    print(f"  FR-4 에서 도체손실과 유전체손실이 뒤바뀌는 곳: {f_cross/1e9:.2f} GHz")

    print(f"\n  임피던스 공차 (RO4350B, W {tol['w0']*1e3:.3f} mm,"
          f" h {tol['h0']*1e3:.3f} mm, Dk {tol['er0']})")
    print(f"    공칭 {tol['z_nom']:.2f} Ω · 산포 1σ = {tol['rss']:.2f} Ω")
    for k, lbl in (("h", "기판 두께"), ("w", "선폭"), ("er", "유전율")):
        v = tol["parts"][k]
        print(f"      {lbl:6s} 기여 {v:.3f} Ω  ({v**2/tol['rss']**2*100:.0f} %)")
    for band, (lo, hi, y) in sorted(tol["yields"].items()):
        print(f"    ±{band:.0f} % ({lo:.1f} ~ {hi:.1f} Ω) 안에 드는 비율: {y:.1f} %")

    print(f"\n  PDN 목표 임피던스 {pdn['z_target']*1000:.0f} mΩ")
    print(f"    전체 디커플링: {pdn['f_hold']/1e6:.0f} MHz 까지 목표선 아래"
          f" (그 구간 최악 {pdn['worst_hold']*1000:.1f} mΩ)")
    print(f"    100 nF 를 빼면: {pdn['peak_f']/1e6:.0f} MHz 에서"
          f" {pdn['peak_z']*1000:.0f} mΩ (목표의 {pdn['peak_z']/pdn['z_target']:.1f} 배)")

    print("\n  비아 스티칭 간격 (λ/20)")
    for r in vias:
        if r["f"] in (2.45e9, 5.8e9):
            print(f"    {r['mat']:9s} {r['f']/1e9:.2f} GHz:"
                  f" ε_eff {r['e_eff']:.2f} · λ {r['lam']*1e3:.1f} mm"
                  f" -> λ/20 = {r['s20']*1e3:.2f} mm")

    print("\n[자체 검산]")

    # ── 마이크로스트립 기본
    for name, er, *_ in MATERIALS:
        w = width_for_50(H_SUB, er)
        z, _ = microstrip(w, H_SUB, er)
        chk(abs(z - 50.0) < 0.01, f"{name}: 선폭 {w*1e3:.3f} mm 에서 Z0 {z:.3f} Ω")

    chk(mat_rows[0]["w"] < mat_rows[2]["w"],
        "Dk 가 낮을수록 50 Ω 선폭이 넓다 "
        f"(FR-4 {mat_rows[0]['w']*1e3:.2f} < PTFE {mat_rows[2]['w']*1e3:.2f} mm)")

    # ── 손실: 손계산 vs scikit-rf
    f_chk = np.array([1e9, 5.8e9, 20e9])
    for name, er, tand, rq, *_ in MATERIALS:
        w = width_for_50(H_SUB, er)
        mine, _, _, _ = loss_by_hand(f_chk, w, H_SUB, T_CU, er, tand, 1.0)
        mine_d = loss_by_hand(f_chk, w, H_SUB, T_CU, er, tand, 1.0)[1]
        mine_tot = mine + mine_d
        theirs, z_skrf = loss_via_skrf(w, er, tand, f_chk)
        rel = np.max(np.abs(mine_tot - theirs) / theirs) * 100
        # 두 모형은 도체손실의 전류분포 처리가 달라 완전히 같지 않다.
        # 그 차이 자체를 본문 §4 에서 "왜 제조사 확인이 필요한가"로 쓴다.
        chk(rel < 30.0,
            f"{name}: 손계산 손실이 scikit-rf 와 {rel:.1f} % 안에서 일치 "
            f"(5.8 GHz: {mine_tot[1]/100:.4f} vs {theirs[1]/100:.4f} dB/cm)")
        chk(abs(z_skrf[1] - 50.0) < 3.0,
            f"{name}: scikit-rf 가 본 Z0 도 {z_skrf[1]:.2f} Ω")

    chk(mat_rows[0]["tot"] > mat_rows[1]["tot"] > mat_rows[2]["tot"],
        "5.8 GHz 손실이 FR-4 > RO4350B > PTFE "
        f"({mat_rows[0]['tot']:.3f} > {mat_rows[1]['tot']:.3f}"
        f" > {mat_rows[2]['tot']:.3f} dB/cm)")
    chk(0.3e9 < f_cross < 5e9,
        f"FR-4 는 {f_cross/1e9:.2f} GHz 부터 유전체 손실이 도체 손실을 넘는다")
    chk(mat_rows[0]["tot"] / mat_rows[1]["tot"] > 2.0,
        f"5.8 GHz 에서 FR-4 가 RO4350B 보다 "
        f"{mat_rows[0]['tot']/mat_rows[1]['tot']:.1f} 배 손실이 크다")

    # ── 공차: 감도 RSS vs 몬테카를로
    sd_exact = float(np.std(tol["zs"]))
    mean_exact = float(np.mean(tol["zs"]))
    chk(abs(sd_exact - tol["rss"]) / tol["rss"] < 0.05,
        f"감도 RSS {tol['rss']:.3f} Ω vs 몬테카를로 {sd_exact:.3f} Ω "
        f"(차이 {abs(sd_exact-tol['rss'])/tol['rss']*100:.1f} %)")
    chk(abs(mean_exact - tol["z_nom"]) < 0.05,
        f"몬테카를로 평균 {mean_exact:.3f} Ω 이 공칭 {tol['z_nom']:.3f} Ω 과 같다 "
        f"(공차가 치우침을 만들지 않는다)")
    chk(tol["parts"]["h"] > tol["parts"]["w"] > tol["parts"]["er"],
        "기여도가 기판 두께 > 선폭 > 유전율 순이다")
    chk(tol["yields"][10.0][2] > 99.0,
        f"±10 % 규격은 {tol['yields'][10.0][2]:.1f} % 가 통과한다")
    chk(tol["yields"][5.0][2] < tol["yields"][10.0][2],
        f"±5 % 로 조이면 {tol['yields'][5.0][2]:.1f} % 로 떨어진다")

    # ── PDN: 손계산 vs scikit-rf
    f_p = np.array([1e4, 1e6, 1e7, 1e8])
    mine = pdn_by_hand(f_p, pdn["vrm"], pdn["caps"], pdn["plane_l"])
    theirs = pdn_via_skrf(f_p, pdn["vrm"], pdn["caps"], pdn["plane_l"])
    rel = np.max(np.abs(mine - theirs) / np.abs(theirs))
    chk(rel < 1e-9,
        f"PDN: 손으로 한 병렬 합성이 scikit-rf 조립과 일치 (상대차 {rel:.2e})")
    chk(pdn["worst_hold"] <= pdn["z_target"] * 1.001,
        f"전체 디커플링이면 {pdn['f_hold']/1e6:.0f} MHz 까지 목표선 아래 "
        f"(최악 {pdn['worst_hold']*1000:.1f} <= {pdn['z_target']*1000:.0f} mΩ)")
    z_plane_only = 2 * np.pi * pdn["f_hold"] * pdn["plane_l"]
    chk(z_plane_only > pdn["z_target"] * 0.3,
        f"상한 주파수는 평면 인덕턴스가 정한다 "
        f"({pdn['f_hold']/1e6:.0f} MHz 에서 jωL = {z_plane_only*1000:.1f} mΩ,"
        f" 목표 {pdn['z_target']*1000:.0f} mΩ 의 {z_plane_only/pdn['z_target']*100:.0f} %)")
    chk(pdn["peak_z"] > pdn["z_target"],
        f"커패시터 한 종을 빼면 반공진이 목표선을 "
        f"{pdn['peak_z']/pdn['z_target']:.1f} 배 넘는다")

    # ── 비아
    v58 = [r for r in vias if r["f"] == 5.8e9]
    chk(all(0.5e-3 < r["s20"] < 8e-3 for r in v58),
        "5.8 GHz λ/20 간격이 재료별로 "
        + " · ".join(f"{r['mat']} {r['s20']*1e3:.2f} mm" for r in v58))
    fr4 = [r for r in vias if r["mat"] == "FR-4" and r["f"] == 2.45e9][0]
    ptfe = [r for r in vias if r["mat"] == "PTFE 계열" and r["f"] == 2.45e9][0]
    chk(fr4["s20"] < ptfe["s20"],
        f"Dk 가 높으면 파장이 짧아 비아를 더 촘촘히 박아야 한다 "
        f"(FR-4 {fr4['s20']*1e3:.2f} < PTFE {ptfe['s20']*1e3:.2f} mm)")

    print("\n전부 통과" if all(ok) else f"\n{ok.count(False)}개 실패")


if __name__ == "__main__":
    main()
