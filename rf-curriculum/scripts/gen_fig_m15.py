"""M15 — 정밀 측정 II: 잡음지수·선형성·위상잡음·로드풀. 데이터 그림과 자체 검산.

M14 가 "이 숫자를 믿어도 되는가" 였다면 여기는 "그 숫자를 어떻게 얻는가" 다.
그래서 그림도 결과가 아니라 **측정 과정에서 실제로 벌어지는 일**을 그린다.

가능한 곳마다 두 경로로 독립 계산해 맞춰 본다
  · 잡음지수: 잡음인자 경로 vs 잡음온도 경로
  · IM3: 다항식 모형의 계수에서 얻은 IIP3 vs 두 톤을 통과시켜 잰 IIP3
"""
import numpy as np

import rf_style as S

T0 = 290.0
K_B = 1.380649e-23


def db(x):
    return 10 * np.log10(x)


def un(x):
    return 10 ** (x / 10)


# ══════════════════════════════════════ 잡음지수 — Y 계수법
def nf_from_y(y_db, enr_db):
    """Y 계수와 초과잡음비로 잡음지수를 구한다.

        F = ENR / (Y - 1)          (전부 진수)

    Y 는 잡음원을 켰을 때와 껐을 때 출력 잡음 전력의 비다.
    """
    return db(un(enr_db) / (un(y_db) - 1.0))


def nf_via_temperature(y_db, enr_db, t_cold=T0):
    """같은 값을 잡음온도 경로로 구한다 — 교차검증용.

        T_hot = T0(ENR + 1),  Te = (T_hot - Y·T_cold)/(Y - 1),  F = 1 + Te/T0
    """
    y = un(y_db)
    t_hot = T0 * (un(enr_db) + 1.0)
    te = (t_hot - y * t_cold) / (y - 1.0)
    return db(1.0 + te / T0)


def second_stage(nf_meas_db, nf_rx_db, gain_db):
    """2단 보정. 잰 값에서 수신기 몫을 덜어 낸다 (Friis 의 역)."""
    f_meas, f_rx, g = un(nf_meas_db), un(nf_rx_db), un(gain_db)
    return db(f_meas - (f_rx - 1.0) / g)


def m15_noise_figure():
    """Y 계수가 작아질수록 왜 위험해지는가."""
    nf_true = np.linspace(0.3, 12.0, 400)
    fig, (ax1, ax2) = S.figure(9.0, 6.6, nrows=2, sharex=True,
                               gridspec_kw=dict(hspace=0.13))

    for i, enr in enumerate((5.0, 15.0, 21.0)):
        y = db(1.0 + un(enr) / un(nf_true))
        ax1.plot(nf_true, y, color=S.COLORS[i], lw=2.4, label=f"ENR {enr:.0f} dB")
        # 출력 전력을 0.1 dB 틀리게 쟀을 때 NF 가 얼마나 틀리는가.
        # Y 가 작을수록 두 전력이 가까워서 같은 0.1 dB 가 크게 증폭된다.
        err = np.abs(nf_from_y(y + 0.1, enr) - nf_true)
        ax2.plot(nf_true, err, color=S.COLORS[i], lw=2.4,
                 label=f"ENR {enr:.0f} dB")

    ax1.set_ylabel("Y 계수 (dB)")
    ax1.set_title("그림 M15-2  Y 계수법 — 잘 재려면 Y 가 커야 한다")
    ax1.legend(fontsize=8.6, framealpha=0.96)
    ax1.axhspan(0, 1.0, color=S.ACCENT, alpha=0.10)
    ax1.text(6.0, 0.45, S.txt("Y 가 1 dB 아래로 내려가면\n"
                              "두 전력이 거의 같아 잡음에 파묻힌다"),
             fontsize=8.4, color=S.ACCENT, ha="center", fontweight="bold")
    ax1.set_ylim(0, 22)

    ax2.set_xlabel("DUT 의 참 잡음지수 (dB)")
    ax2.set_ylabel("전력을 0.1 dB 틀리게 쟀을 때\nNF 오차 (dB)")
    ax2.legend(fontsize=8.6, loc="upper left", framealpha=0.96)
    ax2.set_ylim(0, 1.2)
    ax2.text(4.2, 0.82, S.txt("Y 가 작을수록 같은 0.1 dB 가 크게 증폭된다.\n"
                              "ENR 21 dB 에서는 어디서나 0.11 dB 로 거의 그대로지만,\n"
                              "ENR 5 dB 로 잡음지수 12 dB 를 재면 0.57 dB 로 커진다."),
             fontsize=8.4, color=S.MUTED, ha="left")
    S.save(fig, "M15", "noise_figure")

    return nf_true


def m15_nf_pareto():
    """잡음지수 측정 불확도 — 무엇이 지배하는가."""
    items = [
        ("잡음원 ENR 불확도", 0.20),
        ("부정합 (잡음원 ↔ DUT)", 0.15),
        ("2단(수신기) 보정 잔차", 0.08),
        ("측정기 잡음지수 불확도", 0.06),
        ("반복성·표류", 0.04),
        ("이득 측정 오차의 파급", 0.03),
    ]
    names = [n for n, _ in items]
    vals = np.array([v for _, v in items])
    var = vals ** 2
    share = 100 * var / var.sum()

    fig, ax = S.figure(8.8, 4.8)
    y = np.arange(len(items))[::-1]
    ax.barh(y, vals, color=[S.COLORS[0]] + [S.MUTED] * (len(items) - 1),
            height=0.62, edgecolor="white")
    for yi, v, s in zip(y, vals, share):
        ax.text(v + 0.006, yi, f"{v:.2f} dB  ({s:.0f} %)", va="center",
                fontsize=9, color=S.INK)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9.5)
    ax.set_xlabel("표준불확도 (dB)")
    ax.set_xlim(0, 0.30)
    ax.set_title("그림 M15-3  잡음지수 측정의 불확도 — 어디를 고쳐야 하는가")
    total = float(np.sqrt(var.sum()))
    ax.text(0.165, 3.15, S.txt(f"합성 표준불확도 {total:.3f} dB\n"
                              f"확장불확도 (k=2) {2*total:.3f} dB"),
            fontsize=9.2, color=S.ACCENT, fontweight="bold", ha="left",
            bbox=dict(fc="white", ec=S.ACCENT, lw=1.0, alpha=0.96))
    S.save(fig, "M15", "nf_pareto")

    return dict(items=items, total=total, share=dict(zip(names, share)))


# ══════════════════════════════════════ P1dB 자동 소인
def m15_p1db():
    """이득 압축 소인. 어디서부터 압축인지, 얼마나 촘촘히 재야 하는지."""
    g0_db, oip3_db = 20.0, 32.0
    pin = np.linspace(-30.0, 5.0, 351)

    # 3차 비선형 다항식에서 나오는 압축 (부호가 음이면 이득이 줄어든다)
    a1 = un(g0_db / 2) ** 0.5 * 0 + 10 ** (g0_db / 20)
    # OIP3 로부터 3차 계수를 정한다: IIP3 = OIP3 - G
    iip3_v = 10 ** ((oip3_db - g0_db - 10) / 20)      # dBm -> 전압 (50 ohm)
    a3 = -(4.0 / 3.0) * a1 / (iip3_v ** 2)

    v_in = 10 ** ((pin - 10) / 20)
    v_out = a1 * v_in + 0.75 * a3 * v_in ** 3          # 기본파 성분
    gain = 20 * np.log10(np.maximum(np.abs(v_out) / v_in, 1e-12))
    pout = pin + gain

    k = int(np.argmin(np.abs(gain - (g0_db - 1.0))))
    p1db_in, p1db_out = pin[k], pout[k]

    fig, (ax1, ax2) = S.figure(8.8, 6.2, nrows=2, sharex=True,
                               gridspec_kw=dict(hspace=0.12))
    ax1.plot(pin, pout, color=S.COLORS[0], lw=2.6, label="실제 출력")
    S.reference_line(ax1, pin, pin + g0_db, label="선형 연장선")
    ax1.plot([p1db_in], [p1db_out], "o", color=S.ACCENT, ms=9, zorder=6)
    ax1.annotate(f"입력 P1dB {p1db_in:.1f} dBm\n출력 P1dB {p1db_out:.1f} dBm",
                 xy=(p1db_in, p1db_out), xytext=(p1db_in - 17, p1db_out + 2),
                 fontsize=9, color=S.ACCENT, fontweight="bold",
                 bbox=dict(fc="white", ec=S.ACCENT, lw=1.0, alpha=0.96),
                 arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    ax1.set_ylabel("출력 전력 (dBm)")
    ax1.set_title("그림 M15-4  이득 압축 소인 — P1dB 를 찾는 법")
    ax1.legend(fontsize=8.6, loc="upper left", framealpha=0.96)

    ax2.plot(pin, gain, color=S.COLORS[0], lw=2.6)
    S.limit_line(ax2, g0_db - 1.0, "소신호 이득 - 1 dB", side="lower")
    ax2.axvline(p1db_in, color=S.ACCENT, ls=":", lw=1.4)
    ax2.set_xlabel("입력 전력 (dBm)")
    ax2.set_ylabel("이득 (dB)")
    ax2.set_ylim(g0_db - 4.0, g0_db + 0.6)
    ax2.text(-29, g0_db - 3.4,
             S.txt("압축이 시작되는 구간은 좁다.\n"
                   "1 dB 간격으로 쓸면 P1dB 를 1 dB 놓칠 수 있다\n"
                   "-> 압축 근처에서는 0.2 dB 간격으로"),
             fontsize=8.4, color=S.MUTED, ha="left")
    S.save(fig, "M15", "p1db")

    # 성긴 소인이 얼마나 놓치는가
    coarse = pin[::10]                                # 1 dB 간격
    g_coarse = np.interp(coarse, pin, gain)
    kc = int(np.argmin(np.abs(g_coarse - (g0_db - 1.0))))
    return dict(p1db_in=p1db_in, p1db_out=p1db_out, g0=g0_db,
                coarse_err=abs(coarse[kc] - p1db_in), a1=a1, a3=a3,
                iip3_expected=oip3_db - g0_db)


# ══════════════════════════════════════ 2-tone: 측정계 IM3 대 DUT IM3
def m15_im3():
    """측정계 자신의 IM3 와 DUT 의 IM3 를 어떻게 구분하는가.

    둘 다 톤 전력에 대해 기울기 3 이라 **전력을 바꿔서는 구분되지 않는다.**
    (평행선이라 서로 만나지 않는다.)

    구분하는 방법은 **분석기 앞의 감쇠기를 옮기는 것**이다.
      · DUT 가 만든 IM3 는 이미 만들어진 신호라 감쇠량만큼 그대로 내려간다 (1:1)
      · 분석기가 스스로 만드는 IM3 는 입력이 줄면 세제곱으로 줄어든다 (3:1)
    """
    att = np.linspace(0.0, 30.0, 301)          # 분석기 앞에 넣는 감쇠 (dB)
    p_tone_out = 0.0                            # DUT 출력의 톤 하나 (dBm)
    im3_dut_at_dut = -45.0                      # DUT 가 만든 IM3 (DUT 출력 기준)
    iip3_sa = 15.0                              # 분석기의 IIP3 (입력 기준)

    # 분석기 입력에서 본 두 성분
    im3_from_dut = im3_dut_at_dut - att                     # 1 dB 당 1 dB
    p_in_sa = p_tone_out - att
    im3_from_sa = 3 * p_in_sa - 2 * iip3_sa                 # 1 dB 당 3 dB
    seen = 10 * np.log10(un(im3_from_dut) + un(im3_from_sa))

    fig, ax = S.figure(8.8, 5.4)
    ax.plot(att, im3_from_dut, color=S.COLORS[0], lw=2.6,
            label="DUT 가 만든 IM3 (감쇠 1 dB 당 1 dB)")
    ax.plot(att, im3_from_sa, color=S.COLORS[1], lw=2.4, ls="--",
            label="분석기가 스스로 만드는 IM3 (1 dB 당 3 dB)")
    S.emph(ax, att, seen, color=S.ACCENT)
    ax.plot([], [], color=S.ACCENT, lw=2.6, label="화면에 보이는 값")

    ax.set_xlabel("분석기 앞에 넣은 감쇠 (dB)")
    ax.set_ylabel("분석기 입력에서 본 IM3 (dBm)")
    ax.set_title("그림 M15-6  내 IM3 인가, 분석기의 IM3 인가 — 감쇠기로 가른다")
    ax.legend(fontsize=8.4, loc="upper right", framealpha=0.96)
    ax.set_ylim(-118, -36)

    k = {a: int(np.argmin(np.abs(att - a))) for a in (0, 10, 20, 30)}
    d1 = seen[k[0]] - seen[k[10]]
    d2 = seen[k[10]] - seen[k[20]]
    for a0, a1, d, y in ((0, 10, d1, -74), (10, 20, d2, -95)):
        ax.annotate(f"{a0} -> {a1} dB 감쇠에\n화면 값 {d:.1f} dB 하락",
                    xy=((a0 + a1) / 2, seen[int(np.argmin(np.abs(att - (a0 + a1) / 2)))]),
                    xytext=((a0 + a1) / 2 - 4.5, y), fontsize=8.6,
                    color=S.ACCENT, fontweight="bold",
                    bbox=dict(fc="white", ec=S.ACCENT, lw=1.0, alpha=0.96),
                    arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))
    ax.text(15.5, -108, S.txt("판정: 10 dB 감쇠에 10 dB 내려가면 DUT 것,\n"
                             "30 dB 내려가면 분석기 것이다.\n"
                             "그 사이면 섞여 있다 — 더 감쇠해 DUT 쪽으로 넘어간 뒤 읽는다"),
            fontsize=8.4, color=S.MUTED, ha="left")
    S.save(fig, "M15", "im3")

    # 분석기 몫이 DUT 몫보다 10 dB 아래로 내려가는 감쇠량
    ok = im3_from_dut - im3_from_sa > 10.0
    clean = att[int(np.argmax(ok))] if ok.any() else float("nan")
    return dict(drop_first=d1, drop_second=d2, clean_att=clean,
                im3_true=im3_dut_at_dut, iip3_sa=iip3_sa,
                dut_slope=1.0, sa_slope=3.0)


# ══════════════════════════════════════ 위상잡음 3측정법
def m15_phase_noise():
    """세 방법의 바닥이 어디에 있고, 상호상관이 얼마나 내려가는가."""
    f = np.logspace(2, 7, 400)

    def leeson(f0=1e9, q=60.0, nf_db=8.0, ps_dbm=5.0, fc=3e4):
        nf, ps = un(nf_db), un(ps_dbm) / 1000.0
        fl = f0 / (2 * q)
        return db((nf * K_B * T0 / ps) * (1 + (fl / f) ** 2) * (1 + fc / f))

    dut = leeson()
    sa_floor = -95 - 25 * np.log10(f / 1e2) / np.log10(1e5)   # 대략적인 SA 바닥
    sa_floor = np.maximum(sa_floor, -152.0)
    pd_floor = np.full_like(f, -165.0)
    pd_floor = np.minimum(-120 - 15 * np.log10(f / 1e2), pd_floor) * 0 + \
        np.maximum(-120 - 12 * np.log10(f / 1e2), -168.0)
    xc_floor = pd_floor - 20.0                     # 상호상관 10000회 = 5log(N)

    fig, ax = S.figure(8.8, 5.4)
    ax.plot(f, dut, color=S.INK, lw=2.8, label="DUT 의 진짜 위상잡음")
    ax.plot(f, sa_floor, color=S.COLORS[1], lw=2.2, ls="--",
            label="① 직접 스펙트럼법의 바닥")
    ax.plot(f, pd_floor, color=S.COLORS[0], lw=2.2, ls="-.",
            label="② 위상검출기법의 바닥")
    ax.plot(f, xc_floor, color=S.COLORS[2], lw=2.2, ls=":",
            label="③ 상호상관법의 바닥 (1만 회)")
    ax.set_xscale("log")
    S.hz_ticks(ax, [1e2, 1e3, 1e4, 1e5, 1e6, 1e7])
    ax.set_xlabel("반송파로부터의 오프셋")
    ax.set_ylabel("위상잡음 L(f) (dBc/Hz)")
    ax.set_title("그림 M15-8  위상잡음 측정 3종 — 바닥이 다르다")
    ax.legend(fontsize=8.2, loc="upper right", framealpha=0.96)
    ax.set_ylim(-190, -58)
    ax.annotate("바닥이 DUT 보다 위면\n재고 있는 것은 측정기다",
                xy=(3e2, -99), xytext=(1.1e3, -183), fontsize=8.6,
                color=S.ACCENT, fontweight="bold",
                bbox=dict(fc="white", ec=S.ACCENT, lw=0.9, alpha=0.96),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.1))
    S.save(fig, "M15", "phase_noise")

    return dict(f=f, dut=dut, sa=sa_floor, pd=pd_floor, xc=xc_floor)


def xcorr_gain_db(n):
    """상호상관 N 회의 바닥 개선량. 문헌의 5·log10(N) 을 그대로 쓴다."""
    return 5.0 * np.log10(n)


# ══════════════════════════════════════ 로드풀
def m15_loadpull():
    """부하 임피던스를 옮겨 가며 출력과 효율을 재면 등고선이 나온다.

    핵심 결론: **최대 출력점과 최대 효율점은 같은 자리가 아니다.**
    """
    n = 241
    gr = np.linspace(-0.85, 0.85, n)
    gi = np.linspace(-0.85, 0.85, n)
    GR, GI = np.meshgrid(gr, gi)
    G = GR + 1j * GI
    inside = np.abs(G) <= 0.85

    # 출력이 최대가 되는 부하와 효율이 최대가 되는 부하를 서로 다르게 둔다
    g_pmax = 0.45 * np.exp(1j * np.deg2rad(155.0))
    g_emax = 0.62 * np.exp(1j * np.deg2rad(120.0))

    pout = 41.0 - 32.0 * np.abs(G - g_pmax) ** 2
    pae = 62.0 - 150.0 * np.abs(G - g_emax) ** 2

    pout = np.where(inside, pout, np.nan)
    pae = np.where(inside, pae, np.nan)

    fig, ax = S.figure(7.6, 7.2)
    th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(0.9 * np.cos(th), 0.9 * np.sin(th), color=S.INK, lw=1.6)
    for r in (0.3, 0.6):
        ax.plot(r * np.cos(th), r * np.sin(th), color=S.GRID, lw=0.9)
    ax.plot([-0.9, 0.9], [0, 0], color=S.GRID, lw=0.9)
    ax.plot([0, 0], [-0.9, 0.9], color=S.GRID, lw=0.9)

    c1 = ax.contour(GR, GI, pout, levels=[38, 40],
                    colors=S.COLORS[0], linewidths=2.2)
    ax.clabel(c1, fmt="%.0f dBm", fontsize=8.5, inline=True)
    c2 = ax.contour(GR, GI, pae, levels=[45, 57],
                    colors=S.COLORS[2], linewidths=2.2, linestyles="--")
    ax.clabel(c2, fmt="%.0f %%", fontsize=8.5, inline=True)

    for g, col, name in ((g_pmax, S.COLORS[0], "최대 출력"),
                         (g_emax, S.COLORS[2], "최대 효율")):
        ax.plot([g.real], [g.imag], "o", color=col, ms=10, zorder=8)
        dx, dy = (-0.30, -0.42) if name == "최대 출력" else (0.46, 0.26)
        ax.annotate(name, xy=(g.real, g.imag),
                    xytext=(g.real + dx, g.imag + dy), fontsize=10,
                    color=col, fontweight="bold", ha="center",
                    bbox=dict(fc="white", ec=col, lw=1.0, alpha=0.95),
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.3))

    ax.set_aspect("equal")
    ax.set_xlim(-0.98, 0.98)
    ax.set_ylim(-1.12, 0.98)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("그림 M15-9  로드풀 등고선 — 출력과 효율은 다른 곳에서 최대가 된다")
    ax.text(0, -1.05, S.txt("부하쪽 반사계수 평면. 실선이 출력, 파선이 효율"),
            fontsize=9, color=S.MUTED, ha="center")
    S.save(fig, "M15", "loadpull")

    sep = np.abs(g_pmax - g_emax)
    pout_at_emax = 41.0 - 32.0 * np.abs(g_emax - g_pmax) ** 2
    pae_at_pmax = 62.0 - 150.0 * np.abs(g_pmax - g_emax) ** 2
    return dict(g_pmax=g_pmax, g_emax=g_emax, sep=sep,
                pmax=41.0, emax=62.0,
                pout_at_emax=pout_at_emax, pae_at_pmax=pae_at_pmax)


# ══════════════════════════════════════ 검산
def selfcheck(nf_pareto, p1, im3, pn, lp):
    ok = []

    def chk(cond, msg):
        ok.append(bool(cond))
        print(f"  [{'OK ' if cond else 'FAIL'}] {msg}")

    print("\n[자체 검산]")

    # ── Y 계수: 두 경로가 같은 답을 주는가
    for y, enr in ((10.0, 15.0), (3.0, 15.0), (1.5, 5.0), (6.0, 21.0)):
        a, b = nf_from_y(y, enr), nf_via_temperature(y, enr)
        chk(abs(a - b) < 1e-9,
            f"Y={y} dB · ENR={enr} dB -> NF {a:.4f} dB "
            f"(잡음인자 경로와 잡음온도 경로 일치)")

    # 손계산 대조: ENR 15 dB, Y 10 dB
    #   F = 31.623 / (10 - 1) = 3.5137 -> 5.4585 dB
    chk(abs(nf_from_y(10.0, 15.0) - 5.4585) < 1e-3,
        f"손계산과 일치 (ENR 15 · Y 10 -> {nf_from_y(10.0, 15.0):.4f} dB)")

    # ── 2단 보정
    #   측정 3.0 dB, 수신기 8 dB, DUT 이득 20 dB
    corrected = second_stage(3.0, 8.0, 20.0)
    chk(corrected < 3.0, f"2단 보정은 값을 낮춘다 (3.00 -> {corrected:.3f} dB)")
    #   역으로 Friis 로 다시 합치면 원래 값이 나와야 한다
    recomposed = db(un(corrected) + (un(8.0) - 1.0) / un(20.0))
    chk(abs(recomposed - 3.0) < 1e-9,
        f"보정을 Friis 로 되돌리면 측정값 복원 ({recomposed:.6f} dB)")
    #   이득이 크면 보정이 작아진다
    chk(abs(second_stage(3.0, 8.0, 40.0) - 3.0) < 0.02,
        "DUT 이득이 40 dB 면 2단 보정이 0.02 dB 아래")

    # ── 불확도
    chk(abs(nf_pareto["share"]["잡음원 ENR 불확도"] - 100 *
            0.20 ** 2 / sum(v ** 2 for _, v in nf_pareto["items"])) < 1e-9,
        f"ENR 이 분산의 {nf_pareto['share']['잡음원 ENR 불확도']:.0f} % 를 차지")
    chk(nf_pareto["share"]["잡음원 ENR 불확도"] > 50,
        "ENR 하나가 절반을 넘는다")

    # ── P1dB
    chk(abs(p1["p1db_out"] - (p1["p1db_in"] + p1["g0"] - 1.0)) < 0.02,
        f"출력 P1dB = 입력 P1dB + (이득 - 1) ({p1['p1db_out']:.2f} dBm)")
    #   3차 다항식에서 P1dB 는 IIP3 보다 약 9.6 dB 아래
    gap = p1["iip3_expected"] - p1["p1db_in"]
    chk(abs(gap - 9.64) < 0.35,
        f"입력 P1dB 가 IIP3 보다 {gap:.2f} dB 아래 (이론 9.64 dB)")
    chk(p1["coarse_err"] > 0.3,
        f"1 dB 간격 소인은 P1dB 를 {p1['coarse_err']:.1f} dB 놓친다")

    # ── IM3
    chk(abs(im3["sa_slope"] / im3["dut_slope"] - 3.0) < 1e-9,
        "감쇠에 대해 DUT 몫은 1:1, 분석기 몫은 3:1 로 내려간다")
    chk(im3["drop_first"] > im3["drop_second"],
        f"처음 10 dB 에서는 {im3['drop_first']:.1f} dB, 다음 10 dB 에서는 "
        f"{im3['drop_second']:.1f} dB — 분석기 몫이 먼저 사라진다")
    chk(abs(im3["drop_second"] - 10.0) < 2.0,
        f"DUT 쪽으로 넘어가면 감쇠와 1:1 이 된다 ({im3['drop_second']:.1f} dB)")
    chk(im3["clean_att"] > 0,
        f"감쇠를 {im3['clean_att']:.0f} dB 넣으면 분석기 몫이 10 dB 아래로 밀린다")

    # ── 위상잡음
    chk(abs(xcorr_gain_db(10) - 5.0) < 1e-9, "상호상관 10회 -> 5 dB 개선")
    chk(abs(xcorr_gain_db(10000) - 20.0) < 1e-9, "상호상관 1만회 -> 20 dB 개선")
    chk(np.all(pn["xc"] <= pn["pd"] + 1e-9), "상호상관 바닥이 위상검출기보다 낮다")
    near = pn["f"] < 1e3
    chk(np.all(pn["sa"][near] > pn["pd"][near]),
        "가까운 오프셋에서 직접 스펙트럼법의 바닥이 가장 높다")

    # ── 로드풀
    chk(lp["sep"] > 0.15,
        f"최대 출력점과 최대 효율점이 떨어져 있다 (|ΔΓ| = {lp['sep']:.3f})")
    chk(lp["pout_at_emax"] < lp["pmax"] and lp["pae_at_pmax"] < lp["emax"],
        f"한쪽을 고르면 다른 쪽을 잃는다 "
        f"(효율점에서 출력 {lp['pout_at_emax']:.1f} dBm, "
        f"출력점에서 효율 {lp['pae_at_pmax']:.1f} %)")

    print("\n" + ("전부 통과" if all(ok) else "!! 실패 항목 있음"))
    return all(ok)


def main():
    m15_noise_figure()
    par = m15_nf_pareto()
    p1 = m15_p1db()
    im3 = m15_im3()
    pn = m15_phase_noise()
    lp = m15_loadpull()

    print("[본문에 인용할 계산값]")
    print(f"  Y 계수법: ENR 15 dB · Y 10 dB -> NF {nf_from_y(10.0, 15.0):.2f} dB")
    print(f"    같은 ENR 에서 Y 가 3 dB 면 NF {nf_from_y(3.0, 15.0):.2f} dB")
    print("  전력을 0.1 dB 틀리게 쟀을 때의 NF 오차")
    for enr in (5.0, 15.0, 21.0):
        for nf in (6.0, 12.0):
            y = db(1 + un(enr) / un(nf))
            print(f"    ENR {enr:4.0f} dB · 참 NF {nf:4.1f} dB (Y {y:5.2f} dB)"
                  f" -> {abs(nf_from_y(y + 0.1, enr) - nf):.3f} dB")
    print(f"  2단 보정: 측정 3.00 dB · 수신기 8 dB · 이득 20 dB"
          f" -> {second_stage(3.0, 8.0, 20.0):.2f} dB")
    print(f"    이득이 10 dB 뿐이면 -> {second_stage(3.0, 8.0, 10.0):.2f} dB")
    print(f"  NF 불확도: 합성 {par['total']:.3f} dB · 확장(k=2) {2*par['total']:.3f} dB")
    for k, v in par["share"].items():
        print(f"    {k:24s} {v:5.1f} %")
    print(f"  P1dB: 입력 {p1['p1db_in']:.1f} dBm · 출력 {p1['p1db_out']:.1f} dBm"
          f" (IIP3 보다 {p1['iip3_expected']-p1['p1db_in']:.2f} dB 아래)")
    print(f"    1 dB 간격으로 쓸면 {p1['coarse_err']:.1f} dB 놓친다")
    print(f"  IM3: 감쇠 0->10 dB 에 {im3['drop_first']:.1f} dB,"
          f" 10->20 dB 에 {im3['drop_second']:.1f} dB 하락"
          f" (DUT 만이면 10, 분석기만이면 30)")
    print(f"    분석기 몫을 10 dB 아래로 밀려면 감쇠 {im3['clean_att']:.0f} dB")
    print(f"  상호상관: 100회 {xcorr_gain_db(100):.0f} dB ·"
          f" 1만회 {xcorr_gain_db(10000):.0f} dB 개선")
    print(f"  로드풀: 최대출력 {lp['pmax']:.0f} dBm / 최대효율 {lp['emax']:.0f} %")
    print(f"    효율점에서 출력 {lp['pout_at_emax']:.1f} dBm"
          f" ({lp['pmax']-lp['pout_at_emax']:.1f} dB 손해)")
    print(f"    출력점에서 효율 {lp['pae_at_pmax']:.1f} %"
          f" ({lp['emax']-lp['pae_at_pmax']:.1f} %p 손해)")

    return selfcheck(par, p1, im3, pn, lp)


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
