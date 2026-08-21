"""M16 — DUT 스펙 검증·튜닝·디버그·자동화. 데이터 그림과 자체 검산.

이 모듈은 "판정"과 "고치기"를 다룬다. 그래서 그림도 판정이 어떻게 틀리는지,
튜닝이 어디로 가는지를 계산으로 보인다.

두 경로로 독립 계산해 맞춰 보는 곳
  · 가드밴딩의 오합격·오불합격 확률: 해석식(정규분포) vs 몬테카를로
  · 정합 튜닝의 최종 반사계수: 손으로 쓴 변환식 vs scikit-rf
"""
import numpy as np
import skrf as rf
from scipy import stats

import rf_style as S

Z0 = 50.0
F0 = 2.45e9


# ══════════════════════════════════════ 가드밴딩
def risks_analytic(limit, guard, mu, sigma_p, u):
    """참값이 정규분포이고 측정오차도 정규분포일 때의 오판정 확률.

    참값 X ~ N(mu, sigma_p),  측정값 M = X + E,  E ~ N(0, u)

    오합격(false accept) : 참값은 한계를 넘는데 측정값이 합격선 안
    오불합격(false reject): 참값은 한계 안인데 측정값이 합격선 밖

    (X, M) 은 이변량 정규분포이므로 그 확률로 바로 적분한다.
    """
    al = limit - guard                      # 합격선(acceptance limit)
    sm = np.sqrt(sigma_p ** 2 + u ** 2)     # 측정값의 표준편차
    rho = sigma_p / sm                      # X 와 M 의 상관계수

    # P(X > limit, M <= al) 과 P(X <= limit, M > al)
    a = (limit - mu) / sigma_p
    b = (al - mu) / sm
    mvn = stats.multivariate_normal(mean=[0.0, 0.0], cov=[[1.0, rho], [rho, 1.0]])
    p_both_low = mvn.cdf([a, b])            # P(X<=limit, M<=al)
    p_x_low = stats.norm.cdf(a)
    p_m_low = stats.norm.cdf(b)

    pfa = p_m_low - p_both_low               # X>limit 이면서 M<=al
    pfr = p_x_low - p_both_low               # X<=limit 이면서 M>al
    return pfa, pfr, p_m_low


def risks_monte_carlo(limit, guard, mu, sigma_p, u, n=4_000_000, seed=3):
    """같은 확률을 난수로 — 해석식을 잘못 옮겨 적지 않았는지 확인용."""
    r = np.random.default_rng(seed)
    x = r.normal(mu, sigma_p, n)
    m = x + r.normal(0.0, u, n)
    al = limit - guard
    return (np.mean((x > limit) & (m <= al)),
            np.mean((x <= limit) & (m > al)),
            np.mean(m <= al))


def m16_guardband():
    """가드밴드를 넓힐수록 오합격은 줄고 오불합격은 는다."""
    limit, mu, sigma_p, u = 3.0, 2.55, 0.30, 0.27   # 잡음지수 한계 3.0 dB
    guards = np.linspace(0.0, 0.8, 161)
    pfa, pfr = [], []
    for g in guards:
        a, b, _ = risks_analytic(limit, g, mu, sigma_p, u)
        pfa.append(100 * a)
        pfr.append(100 * b)
    pfa, pfr = np.array(pfa), np.array(pfr)

    fig, (ax1, ax2) = S.figure(9.0, 7.0, nrows=2,
                               gridspec_kw=dict(hspace=0.34))

    # 위: 무슨 일이 벌어지는지 그림으로
    xs = np.linspace(1.4, 4.2, 500)
    ax1.plot(xs, stats.norm.pdf(xs, mu, sigma_p), color=S.COLORS[0], lw=2.4,
             label="DUT 들의 참값 분포")
    ax1.plot(xs, stats.norm.pdf(xs, mu, np.sqrt(sigma_p ** 2 + u ** 2)),
             color=S.COLORS[1], lw=2.2, ls="--", label="측정값의 분포 (참값 + 측정오차)")
    ax1.axvline(limit, color=S.ACCENT, lw=2.2)
    # 라벨은 두 곡선이 지나가지 않는 자리에 놓고, 흰 상자를 깔아 겹침을 막는다.
    box = dict(fc="white", ec="none", alpha=0.92, pad=1.6)
    ax1.text(limit + 0.05, 0.72, S.txt("규격 한계\n3.0 dB"), color=S.ACCENT,
             fontsize=9, fontweight="bold", ha="left", va="center", bbox=box)
    g_show = 0.54                                      # 확장불확도 (k=2)
    ax1.axvline(limit - g_show, color=S.COLORS[2], lw=2.2, ls=":")
    ax1.text(limit - g_show - 0.04, 1.30, S.txt("합격선 2.46 dB"),
             color=S.COLORS[2], fontsize=9, fontweight="bold", ha="right",
             va="center", bbox=box)
    ax1.annotate("", xy=(limit, 0.18), xytext=(limit - g_show, 0.18),
                 arrowprops=dict(arrowstyle="<->", color=S.COLORS[2], lw=1.6))
    ax1.text(limit - g_show / 2, 0.27, S.txt("가드밴드"), color=S.COLORS[2],
             fontsize=9.5, ha="center", fontweight="bold")
    ax1.set_xlabel("잡음지수 (dB)")
    ax1.set_ylabel("확률밀도")
    ax1.set_ylim(0, 1.45)
    ax1.legend(fontsize=8.4, loc="upper right", framealpha=0.96)
    ax1.set_title("그림 M16-3  가드밴딩 — 불확도를 판정에 넣는 법")

    # 아래: 가드밴드를 넓힐 때의 두 위험
    ax2.plot(guards, pfa, color=S.ACCENT, lw=2.6, label="오합격 (불량을 통과시킴)")
    ax2.plot(guards, pfr, color=S.COLORS[0], lw=2.6, ls="--",
             label="오불합격 (양품을 버림)")
    ax2.axvline(g_show, color=S.COLORS[2], lw=1.6, ls=":")
    k = int(np.argmin(np.abs(guards - g_show)))
    ax2.plot([g_show], [pfa[k]], "o", color=S.ACCENT, ms=8, zorder=6)
    ax2.annotate(f"확장불확도만큼 가드밴드를 두면\n"
                 f"오합격 {pfa[k]:.2f} % · 오불합격 {pfr[k]:.1f} %",
                 xy=(g_show, pfa[k]), xytext=(0.235, 20.0), fontsize=8.8,
                 color=S.ACCENT, fontweight="bold",
                 bbox=dict(fc="white", ec=S.ACCENT, lw=1.0, alpha=0.96),
                 arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    ax2.plot([0.0], [pfa[0]], "o", color=S.MUTED, ms=8, zorder=6)
    ax2.annotate(f"가드밴드 없이 그냥 판정하면\n오합격 {pfa[0]:.1f} %",
                 xy=(0.0, pfa[0]), xytext=(0.055, 34.0), fontsize=8.8,
                 color=S.MUTED, bbox=dict(fc="white", ec=S.MUTED, lw=0.9, alpha=0.96),
                 arrowprops=dict(arrowstyle="->", color=S.MUTED, lw=1.1))
    ax2.set_xlabel("가드밴드 폭 (dB)")
    ax2.set_ylabel("확률 (%)")
    ax2.set_ylim(0, 62)
    ax2.legend(fontsize=8.6, loc="center right", framealpha=0.96)
    S.save(fig, "M16", "guardband")

    return dict(limit=limit, mu=mu, sigma_p=sigma_p, u=u,
                guards=guards, pfa=pfa, pfr=pfr, g_show=g_show,
                pfa0=pfa[0], pfr0=pfr[0], pfa_g=pfa[k], pfr_g=pfr[k])


def smith_grid(ax, r_vals=(0.2, 0.5, 1.0, 2.0, 5.0),
               x_vals=(0.2, 0.5, 1.0, 2.0, 5.0)):
    """진짜 스미스 차트 격자 — 정저항 원과 정리액턴스 호.

    정저항 r: 중심 (r/(1+r), 0), 반지름 1/(1+r)
    정리액턴스 x: 중심 (1, 1/x), 반지름 1/|x|  (단위원 안쪽만 그린다)
    """
    th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(th), np.sin(th), color=S.INK, lw=1.8, zorder=3)
    ax.plot([-1, 1], [0, 0], color=S.GRID, lw=1.0, zorder=1)
    for r in r_vals:
        c, rad = r / (1 + r), 1 / (1 + r)
        ax.plot(c + rad * np.cos(th), rad * np.sin(th),
                color=S.GRID, lw=0.9, zorder=1)
    for x in x_vals:
        for s in (+1, -1):
            c, rad = 1.0, 1.0 / x
            a = c + rad * np.cos(th)
            b = s * rad + rad * np.sin(th)
            keep = a ** 2 + b ** 2 <= 1.0 + 1e-9
            ax.plot(a[keep], b[keep], color=S.GRID, lw=0.9, zorder=1,
                    ls="none" if not keep.any() else "-")


# ══════════════════════════════════════ 정합 튜닝 궤적
def gamma_of(z):
    return (z - Z0) / (z + Z0)


def m16_tuning():
    """오정합된 부하를 병렬 C, 직렬 L 두 번으로 50 Ω 에 붙인다."""
    w = 2 * np.pi * F0
    z_load = 15.0 + 1j * 30.0                 # 튜닝 전 부하
    g0 = gamma_of(z_load)

    # 1단계: 병렬 커패시터로 어드미턴스 원을 따라 이동
    # 2단계: 직렬 인덕터로 임피던스 원을 따라 이동해 50 Ω 으로
    def after_shunt_c(c):
        y = 1.0 / z_load + 1j * w * c
        return 1.0 / y

    def after_series_l(z, l):
        return z + 1j * w * l

    # 50 Ω 에 닿는 (C, L) 을 손으로 푼다.
    #   Re(Z') = G/(G^2+B^2) = Z0  ->  B = ±sqrt(G/Z0 - G^2)
    # 근이 둘인데, **직렬 소자가 인덕터가 되는 쪽**을 골라야 한다.
    # 다른 근을 고르면 직렬 L 이 음수로 나온다 — 존재하지 않는 부품이다.
    y_load = 1.0 / z_load
    g, b0 = y_load.real, y_load.imag
    b_mag = np.sqrt(g / Z0 - g ** 2)
    cands = []
    for b in (+b_mag, -b_mag):
        c = (b - b0) / w
        z = 1.0 / (g + 1j * b)
        l = -z.imag / w                        # 남은 리액턴스를 상쇄
        if c > 0 and l > 0:                    # 둘 다 실재하는 부품이어야 한다
            cands.append((c, l, z))
    assert cands, "이 부하는 병렬C -> 직렬L 로는 정합되지 않는다"
    c_opt, l_opt, z_mid = cands[0]
    z_end = after_series_l(z_mid, l_opt)
    g_end = gamma_of(z_end)

    # 궤적
    path_c = np.array([gamma_of(after_shunt_c(c)) for c in np.linspace(0, c_opt, 200)])
    path_l = np.array([gamma_of(after_series_l(z_mid, l))
                       for l in np.linspace(0, l_opt, 200)])

    fig, ax = S.figure(7.4, 7.4)
    smith_grid(ax)

    ax.plot(path_c.real, path_c.imag, color=S.COLORS[1], lw=2.8,
            label=f"1단계 · 병렬 C = {c_opt*1e12:.2f} pF")
    ax.plot(path_l.real, path_l.imag, color=S.COLORS[2], lw=2.8,
            label=f"2단계 · 직렬 L = {l_opt*1e9:.2f} nH")
    for g, col, name in ((g0, S.ACCENT, "튜닝 전"),
                         (gamma_of(z_mid), S.COLORS[1], "1단계 후"),
                         (g_end, S.COLORS[2], "튜닝 후")):
        ax.plot([g.real], [g.imag], "o", color=col, ms=10, zorder=8)
    ax.annotate(f"튜닝 전\n{z_load.real:.0f} + j{z_load.imag:.0f} Ω\n"
                f"|S11| = {20*np.log10(abs(g0)):.1f} dB",
                # 위로 올리면 제목을 덮는다. 왼쪽 빈 곳으로 뺀다.
                xy=(g0.real, g0.imag), xytext=(-0.72, 0.22),
                fontsize=9, color=S.ACCENT, fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.ACCENT, lw=1.0, alpha=0.96),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.3))
    ax.annotate("튜닝 후\n50 Ω (중심)",
                xy=(g_end.real, g_end.imag), xytext=(0.40, -0.34),
                fontsize=9, color=S.COLORS[2], fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.COLORS[2], lw=1.0, alpha=0.96),
                arrowprops=dict(arrowstyle="->", color=S.COLORS[2], lw=1.3))
    ax.set_aspect("equal")
    ax.set_xlim(-1.12, 1.12)
    ax.set_ylim(-1.26, 1.12)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(fontsize=9, loc="upper left", framealpha=0.96)
    ax.set_title("그림 M16-4  정합 튜닝의 궤적 — 두 번에 중심으로")
    g_mid = gamma_of(z_mid)
    ax.annotate(f"1단계 후\n{z_mid.real:.0f} − j{abs(z_mid.imag):.0f} Ω",
                xy=(g_mid.real, g_mid.imag), xytext=(g_mid.real + 0.03, -0.72),
                fontsize=9, color=S.COLORS[1], fontweight="bold", ha="center",
                bbox=dict(fc="white", ec=S.COLORS[1], lw=1.0, alpha=0.96),
                arrowprops=dict(arrowstyle="->", color=S.COLORS[1], lw=1.3))
    # 회색 격자는 임피던스(정저항·정리액턴스)다. 주황 궤적이 따라가는
    # 정컨덕턴스 원은 이 격자에 그려져 있지 않다 — 학습자가 반드시 걸리는 지점이라 적어 둔다.
    ax.text(0, -1.13, S.txt("회색 격자는 임피던스 — 원이 정저항, 호가 정리액턴스"),
            fontsize=8.6, color=S.MUTED, ha="center")
    ax.text(0, -1.20, S.txt("주황 궤적이 따르는 정컨덕턴스 원은 이 격자에 없다 (좌우 대칭인 어드미턴스 격자)"),
            fontsize=8.6, color=S.MUTED, ha="center")
    S.save(fig, "M16", "tuning")

    return dict(z_load=z_load, g0=g0, c=c_opt, l=l_opt,
                z_mid=z_mid, z_end=z_end, g_end=g_end)


def tuning_via_skrf(z_load, c, l):
    """같은 정합을 scikit-rf 로 조립해 확인한다 — 교차검증용."""
    freq = rf.Frequency.from_f(np.array([F0 / 1e9]), unit="ghz")
    media = rf.media.DefinedGammaZ0(frequency=freq, z0=Z0)
    load = media.load(gamma_of(z_load))
    net = media.inductor(l) ** media.shunt_capacitor(c) ** load
    return complex(net.s[0, 0, 0])


# ══════════════════════════════════════ 바이어스 튜닝
def m16_bias():
    """바이어스 전류를 올리면 이득과 선형성은 좋아지고 전력은 나빠진다."""
    idq = np.linspace(10.0, 200.0, 400)          # mA

    # 이득: 전류에 따라 오르다 포화
    gain = 21.5 * (1.0 - np.exp(-idq / 45.0))
    # OIP3: 전류에 거의 비례하다 포화
    oip3 = 12.0 + 22.0 * (1.0 - np.exp(-idq / 70.0))
    # 소비전력 (5 V 가정)
    pdc = 5.0 * idq / 1000.0                      # W
    # 잡음지수: 너무 낮으면 나쁘고, 너무 높여도 조금 나빠진다
    nf = 1.05 + 6.0 / idq + 0.0018 * idq

    fig, (ax, axn) = S.figure(9.0, 6.6, nrows=2, sharex=True,
                              gridspec_kw=dict(hspace=0.12,
                                               height_ratios=[2.0, 1.0]))
    ax.plot(idq, gain, color=S.COLORS[0], lw=2.6, label="이득 (dB)")
    ax.plot(idq, oip3, color=S.COLORS[1], lw=2.6, ls="--", label="OIP3 (dBm)")
    ax.set_ylabel("이득 (dB) · OIP3 (dBm)")
    ax.set_ylim(0, 38)

    ax2 = ax.twinx()
    ax2.plot(idq, pdc * 1000, color=S.MUTED, lw=2.2, ls=":",
             label="소비전력 (mW)")
    ax2.set_ylabel("소비전력 (mW)")
    ax2.set_ylim(0, 1100)
    ax2.grid(False)

    # 이득이 거의 포화되는 지점 (기울기가 최대의 10 % 아래로)
    slope = np.gradient(gain, idq)
    k_g = int(np.argmax(slope < 0.1 * slope.max()))
    for a in (ax, axn):
        a.axvline(idq[k_g], color=S.ACCENT, ls=":", lw=1.6)
    ax.annotate(f"{idq[k_g]:.0f} mA 를 넘으면\n이득은 거의 안 오르고\n전력만 오른다",
                xy=(idq[k_g], 21.0), xytext=(idq[k_g] + 12, 8.0), fontsize=8.8,
                color=S.ACCENT, fontweight="bold",
                bbox=dict(fc="white", ec=S.ACCENT, lw=1.0, alpha=0.96),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))

    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=8.6, loc="lower right",
              framealpha=0.96)
    ax.set_title("그림 M16-5  바이어스 튜닝 — 무엇을 얻고 무엇을 내주는가")

    # 잡음지수는 축이 달라 아래 칸에 따로 (x10 같은 편법을 쓰지 않는다)
    k_nf = int(np.argmin(nf))
    axn.plot(idq, nf, color=S.COLORS[2], lw=2.6)
    axn.plot([idq[k_nf]], [nf[k_nf]], "o", color=S.COLORS[2], ms=9, zorder=7)
    axn.annotate(f"잡음지수가 가장 좋은 점\n{idq[k_nf]:.0f} mA · {nf[k_nf]:.2f} dB",
                 xy=(idq[k_nf], nf[k_nf]),
                 xytext=(idq[k_nf] + 26, nf[k_nf] + 0.22), fontsize=8.8,
                 color=S.COLORS[2], fontweight="bold",
                 bbox=dict(fc="white", ec=S.COLORS[2], lw=1.0, alpha=0.96),
                 arrowprops=dict(arrowstyle="->", color=S.COLORS[2], lw=1.2))
    axn.set_xlabel("정지 전류 Idq (mA)")
    axn.set_ylabel("잡음지수 (dB)")
    axn.set_ylim(1.15, 1.75)

    S.save(fig, "M16", "bias")

    return dict(idq=idq, gain=gain, oip3=oip3, nf=nf, pdc=pdc,
                i_nf=idq[k_nf], nf_min=nf[k_nf], i_knee=idq[k_g])


# ══════════════════════════════════════ 검산
def selfcheck(gb, tu, bi):
    ok = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  [{'OK ' if cond else 'FAIL'}] {msg}")

    print("\n[자체 검산]")

    # ── 가드밴딩: 해석식과 몬테카를로
    for g in (0.0, 0.27, 0.54):
        a, b, acc = risks_analytic(gb["limit"], g, gb["mu"], gb["sigma_p"], gb["u"])
        ma, mb, macc = risks_monte_carlo(gb["limit"], g, gb["mu"],
                                         gb["sigma_p"], gb["u"])
        chk(abs(a - ma) < 3e-4 and abs(b - mb) < 5e-4,
            f"가드밴드 {g:.2f} dB: 오합격 해석 {100*a:.3f} % vs 몬테카를로 "
            f"{100*ma:.3f} % · 오불합격 {100*b:.3f} vs {100*mb:.3f} %")

    chk(gb["pfa"][0] > gb["pfa"][-1], "가드밴드를 넓히면 오합격이 준다")
    chk(gb["pfr"][0] < gb["pfr"][-1], "가드밴드를 넓히면 오불합격이 는다")
    chk(gb["pfa_g"] < gb["pfa0"] / 3,
        f"확장불확도만큼 두면 오합격이 {gb['pfa0']:.1f} -> {gb['pfa_g']:.2f} %")
    # 가드밴드 0 일 때 두 위험의 크기 관계는 **모집단이 한계선의 어느 쪽에
    # 몰려 있는가**가 정한다. 대칭이 아니다.
    a0, b0, _ = risks_analytic(gb["limit"], 0.0, gb["mu"], gb["sigma_p"], gb["u"])
    chk(b0 > a0,
        f"모집단 평균이 한계선 아래(양품이 많음)면 오불합격이 더 크다 "
        f"(오합격 {100*a0:.2f} % < 오불합격 {100*b0:.2f} %)")
    # 모집단을 한계선 위로 옮기면 관계가 뒤집혀야 한다
    a1, b1, _ = risks_analytic(gb["limit"], 0.0, gb["limit"] + 0.45,
                               gb["sigma_p"], gb["u"])
    chk(a1 > b1,
        f"모집단을 한계선 위로 옮기면 뒤집힌다 "
        f"(오합격 {100*a1:.2f} % > 오불합격 {100*b1:.2f} %)")

    # ── 튜닝
    chk(abs(tu["z_mid"].real - Z0) < 0.05,
        f"1단계 후 실수부가 50 Ω ({tu['z_mid'].real:.3f})")
    chk(abs(tu["z_end"] - Z0) < 0.05,
        f"2단계 후 50 + j0 Ω ({tu['z_end'].real:.2f} + j{tu['z_end'].imag:.3f})")
    rl_before = 20 * np.log10(abs(tu["g0"]))
    rl_after = 20 * np.log10(max(abs(tu["g_end"]), 1e-12))
    # 부호 규약: M02 의 '반사손실(RL)' 은 양수, 여기 |S11| 은 VNA 화면과 같은 음수다.
    chk(rl_after < -60, f"튜닝 후 |S11| {rl_before:.1f} -> {rl_after:.1f} dB")

    g_skrf = tuning_via_skrf(tu["z_load"], tu["c"], tu["l"])
    chk(abs(g_skrf - tu["g_end"]) < 1e-9,
        f"scikit-rf 로 조립한 결과와 일치 (차이 {abs(g_skrf - tu['g_end']):.2e})")

    # ── 바이어스
    chk(bi["gain"][-1] > bi["gain"][0], "전류를 올리면 이득이 오른다")
    chk(bi["oip3"][-1] - bi["oip3"][0] > 10,
        f"OIP3 가 {bi['oip3'][-1]-bi['oip3'][0]:.1f} dB 오른다")
    chk(0 < bi["i_nf"] < 200,
        f"잡음지수에 최적 전류가 있다 ({bi['i_nf']:.0f} mA, {bi['nf_min']:.2f} dB)")
    chk(bi["nf"][0] > bi["nf_min"] and bi["nf"][-1] > bi["nf_min"],
        "그 점을 벗어나면 양쪽 다 나빠진다")
    chk(bi["i_knee"] < 200,
        f"이득 포화 무릎이 {bi['i_knee']:.0f} mA 에 있다")

    print("\n" + ("전부 통과" if all(ok) else "!! 실패 항목 있음"))
    return all(ok)


def main():
    gb = m16_guardband()
    tu = m16_tuning()
    bi = m16_bias()

    print("[본문에 인용할 계산값]")
    print(f"  가드밴딩 예: 한계 {gb['limit']:.1f} dB · DUT 평균 {gb['mu']:.2f} dB"
          f" · 산포 {gb['sigma_p']:.2f} dB · 측정 표준불확도 {gb['u']:.2f} dB")
    print(f"    가드밴드 0     -> 오합격 {gb['pfa0']:.2f} % · 오불합격 {gb['pfr0']:.2f} %")
    print(f"    가드밴드 {gb['g_show']:.2f} dB -> 오합격 {gb['pfa_g']:.2f} %"
          f" · 오불합격 {gb['pfr_g']:.2f} %")
    print(f"  튜닝: {tu['z_load'].real:.0f}+j{tu['z_load'].imag:.0f} Ω"
          f" -> 병렬 C {tu['c']*1e12:.2f} pF -> 직렬 L {tu['l']*1e9:.2f} nH -> 50 Ω")
    print(f"    |S11| {20*np.log10(abs(tu['g0'])):.1f} dB ->"
          f" {20*np.log10(max(abs(tu['g_end']),1e-12)):.1f} dB")
    print(f"  바이어스: 잡음지수 최적 {bi['i_nf']:.0f} mA ({bi['nf_min']:.2f} dB)"
          f" · 이득 포화 무릎 {bi['i_knee']:.0f} mA")
    for i in (20, 60, 100, 160):
        k = int(np.argmin(np.abs(bi["idq"] - i)))
        print(f"    {i:3d} mA -> 이득 {bi['gain'][k]:.1f} dB ·"
              f" OIP3 {bi['oip3'][k]:.1f} dBm · NF {bi['nf'][k]:.2f} dB ·"
              f" {bi['pdc'][k]*1000:.0f} mW")

    return selfcheck(gb, tu, bi)


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
