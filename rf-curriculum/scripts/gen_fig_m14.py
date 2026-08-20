"""M14 — 정밀 측정 I: VNA 교정·디임베딩·불확도. 데이터 그림과 자체 검산.

이 모듈의 핵심 주장은 "교정하지 않은 VNA 가 보여주는 것은 DUT 가 아니다" 이다.
그래서 그림도 말로 설명하지 않고 **오차항을 넣은 가짜 VNA 를 만들어**
그것이 무엇을 보여주는지, 교정이 그것을 어떻게 되돌리는지를 계산으로 보인다.

교정 알고리즘은 손으로 한 번, scikit-rf 로 한 번 — 두 번 독립 구현해 맞춰 본다.
"""
import numpy as np
import skrf as rf

import rf_style as S

Z0 = 50.0
F_GHZ = np.linspace(0.05, 6.0, 1191)          # 50 MHz ~ 6 GHz, 5 MHz 간격
FREQ = rf.Frequency.from_f(F_GHZ, unit="ghz")

C = 299792458.0


# ══════════════════════════════════════ 오차항이 있는 '가짜 VNA'
def error_terms(f_ghz):
    """1-포트 오차 3항. 실제 VNA 에서 볼 법한 크기와 주파수 의존성을 준다.

    **교정 전(raw)** 의 값을 쓴다. 케이블과 커넥터를 달고 아무것도 하지 않은
    상태의 VNA 는 이 정도가 보통이다.

    방향성(e00)   : 브리지 누설. 0.06 이면 약 24 dB. 이것이 **측정 바닥**을 만든다
    소스 정합(e11) : 케이블 끝에서 본 50 Ω 으로부터의 어긋남. 0.15 면 약 16 dB
    반사 추적(e10e01): 크기·위상의 주파수 응답. 케이블 지연이 위상을 돌린다
    """
    w = 2 * np.pi * f_ghz
    e00 = (0.060 + 0.020 * f_ghz / 6.0) * np.exp(1j * (0.8 + 1.7 * w))
    e11 = (0.150 + 0.060 * f_ghz / 6.0) * np.exp(1j * (-0.4 - 2.3 * w))
    tracking = (1.0 - 0.03 * f_ghz / 6.0) * np.exp(-1j * 2.6 * w)
    return e00, e11, tracking


def raw_from_true(gamma_true):
    """오차항을 통과시켜 '교정 안 한 VNA 가 표시하는 값' 을 만든다."""
    e00, e11, tr = error_terms(F_GHZ)
    return e00 + tr * gamma_true / (1.0 - e11 * gamma_true)


def correct(gamma_meas, e00, e11, tr):
    """오차항을 알고 있을 때 참값을 복원한다 (1-포트 교정식)."""
    d = gamma_meas - e00
    return d / (tr + e11 * d)


# ══════════════════════════════════════ 교정 표준
def short_std(offset_ps=0.0):
    """단락 표준. 오프셋 지연이 있으면 그만큼 위상이 더 돈다."""
    return -np.exp(-2j * 2 * np.pi * F_GHZ * 1e9 * offset_ps * 1e-12)


def open_std(c0_ff=50.0, offset_ps=0.0):
    """개방 표준. 끝에서 새는 전기력선이 프린지 커패시턴스로 나타난다.

    이상적인 개방이라면 Γ=+1 이지만, 실제로는 이 축전 성분 때문에
    주파수가 오를수록 위상이 음으로 돌아간다. 교정 키트 정의 파일이
    이 값을 적어 두는 이유다.
    """
    y = 1j * 2 * np.pi * F_GHZ * 1e9 * c0_ff * 1e-15 * Z0
    g = (1 - y) / (1 + y)
    return g * np.exp(-2j * 2 * np.pi * F_GHZ * 1e9 * offset_ps * 1e-12)


def load_std(gamma=0.0):
    return np.full_like(F_GHZ, gamma, dtype=complex)


# ══════════════════════════════════════ 1-포트 교정 (손으로 푼 것)
def solve_one_port(meas, std):
    """표준 3개의 (측정값, 참값) 으로 오차 3항을 푼다.

        Γ_meas = e00 + tr·Γ_std / (1 - e11·Γ_std)

    를 e00, e11, Δ = e00·e11 - tr 에 대해 정리하면 선형이 된다.

        Γ_meas = e00 + (e11·Γ_meas - Δ)·Γ_std

    미지수 3개, 식 3개이므로 주파수마다 3x3 을 푼다.
    """
    e00 = np.empty_like(F_GHZ, dtype=complex)
    e11 = np.empty_like(F_GHZ, dtype=complex)
    tr = np.empty_like(F_GHZ, dtype=complex)
    for k in range(len(F_GHZ)):
        A = np.array([[1.0, meas[i][k] * std[i][k], -std[i][k]] for i in range(3)])
        b = np.array([meas[i][k] for i in range(3)])
        x = np.linalg.solve(A, b)
        e00[k], e11[k] = x[0], x[1]
        tr[k] = e00[k] * e11[k] - x[2]
    return e00, e11, tr


def skrf_one_port(meas, std):
    """같은 문제를 scikit-rf 로 푼다 — 교차검증용."""
    def net(g, name):
        n = rf.Network(frequency=FREQ, s=g.reshape(-1, 1, 1), z0=Z0)
        n.name = name
        return n
    cal = rf.calibration.OnePort(
        measured=[net(m, f"m{i}") for i, m in enumerate(meas)],
        ideals=[net(s, f"i{i}") for i, s in enumerate(std)])
    cal.run()
    c = cal.coefs
    return (c["directivity"], c["source match"], c["reflection tracking"])


# ══════════════════════════════════════ 그림 1 — 교정 전/후
def m14_calibration():
    # DUT: 2.4 GHz 부근에서 아주 잘 정합된 부품. 노치를 깊게 만들어야
    # '교정 전에는 이 깊이를 볼 수 없다' 는 것이 그림에 드러난다.
    l_nh, c_pf, r_ohm = 2.2, 2.0, 49.4
    w = 2 * np.pi * F_GHZ * 1e9
    z = r_ohm + 1j * (w * l_nh * 1e-9 - 1.0 / (w * c_pf * 1e-12))
    g_true = (z - Z0) / (z + Z0)

    g_raw = raw_from_true(g_true)
    std = [short_std(), open_std(), load_std()]
    meas = [raw_from_true(s) for s in std]
    e00, e11, tr = solve_one_port(meas, std)
    g_cal = correct(g_raw, e00, e11, tr)

    fig, (ax1, ax2) = S.figure(9.0, 6.4, nrows=2, sharex=True,
                               gridspec_kw=dict(hspace=0.12))
    db = lambda x: 20 * np.log10(np.maximum(np.abs(x), 1e-9))
    ax1.plot(F_GHZ, db(g_true), color=S.INK, lw=2.4, ls="-", label="참값 (DUT 그 자체)")
    ax1.plot(F_GHZ, db(g_raw), color=S.COLORS[1], lw=2.0, ls="--",
             label="교정 안 한 VNA 가 보여주는 것")
    ax1.plot(F_GHZ, db(g_cal), color=S.COLORS[0], lw=1.6, ls=":",
             label="교정 후 (참값과 겹친다)")
    ax1.set_ylabel("|S11| (dB)")
    ax1.set_ylim(-58, 4)
    ax1.legend(fontsize=8.4, loc="lower right", framealpha=0.96)
    ax1.set_title("그림 M14-1  교정이 되돌리는 것 — 같은 DUT, 세 가지 그림")

    ax2.plot(F_GHZ, db(g_raw - g_true), color=S.COLORS[1], lw=2.0, ls="--",
             label="교정 전 오차 크기")
    ax2.plot(F_GHZ, db(g_cal - g_true), color=S.COLORS[0], lw=2.0, ls="-",
             label="교정 후 오차 크기")
    ax2.set_xlabel("주파수 (GHz)")
    ax2.set_ylabel("|오차| (dB)")
    ax2.set_ylim(-320, 10)
    ax2.legend(fontsize=8.4, loc="lower right", framealpha=0.96)
    ax2.text(0.5, -150, S.txt("교정 후 오차는 수치 계산 한계까지 내려간다\n"
                              "(모형 안에서는 완벽하다는 뜻이지, 실제로 그렇다는 뜻이 아니다)"),
             fontsize=8.2, color=S.MUTED, ha="left")
    S.save(fig, "M14", "calibration")

    return dict(g_true=g_true, g_raw=g_raw, g_cal=g_cal,
                terms=(e00, e11, tr), meas=meas, std=std)


# ══════════════════════════════════════ 그림 2 — TRL 의 대역 제한
def m14_trl_band():
    """TRL 은 THRU 와 LINE 의 위상차가 20°~160° 인 구간에서만 성립한다."""
    fig, ax = S.figure(8.6, 5.0)
    lengths_mm = [10.0, 30.0, 90.0]
    eps_eff = 2.2                       # 흔한 기판 유효 유전율
    v = C / np.sqrt(eps_eff)
    for i, L in enumerate(lengths_mm):
        deg = 360.0 * (F_GHZ * 1e9) * (L * 1e-3) / v
        ax.plot(F_GHZ, deg, color=S.COLORS[i], lw=2.4,
                label=f"라인 길이 {L:.0f} mm")
    ax.axhspan(20, 160, color=S.COLORS[2], alpha=0.12)
    S.limit_line(ax, 20, "20도", side="lower")
    S.limit_line(ax, 160, "160도", side="upper")
    ax.set_xlabel("주파수 (GHz)")
    ax.set_ylabel("THRU 대비 LINE 의 위상차 (도)")
    ax.set_ylim(0, 360)
    ax.set_xlim(0, 6)
    ax.set_title("그림 M14-5  TRL 이 대역 제한을 받는 이유")
    ax.legend(fontsize=8.6, loc="upper left", framealpha=0.96)
    ax.text(3.05, 90, S.txt("이 띠 안에서만 TRL 이 성립한다\n"
                            "라인 하나로는 8:1 대역이 한계"),
            fontsize=8.6, color=S.COLORS[2], ha="center", fontweight="bold")
    S.save(fig, "M14", "trl_band")

    def usable(L):
        deg = 360.0 * (F_GHZ * 1e9) * (L * 1e-3) / v
        ok = (deg >= 20) & (deg <= 160)
        return (F_GHZ[ok][0], F_GHZ[ok][-1]) if ok.any() else (np.nan, np.nan)
    return {L: usable(L) for L in lengths_mm}


# ══════════════════════════════════════ 그림 3 — 시간 영역 변환
def m14_time_domain():
    """주파수 영역 S11 을 시간 영역으로 바꾸면 불연속의 '위치' 가 보인다."""
    # 케이블(지연 1.2 ns) 끝에 커넥터 하나(작은 반사), 그 뒤 부정합 종단
    tau1, tau2 = 1.2e-9, 2.0e-9
    g = (0.06 * np.exp(-2j * 2 * np.pi * F_GHZ * 1e9 * tau1)
         + 0.25 * np.exp(-2j * 2 * np.pi * F_GHZ * 1e9 * tau2))

    n = 8192
    win = np.hanning(len(g))            # 창 없이 변환하면 옆가지가 실제 반사처럼 보인다
    spec = np.zeros(n, dtype=complex)
    spec[:len(g)] = g * win
    t = np.fft.fftfreq(n, d=(F_GHZ[1] - F_GHZ[0]) * 1e9)
    # fft 는 e^(-j...) 를 쓴다. 우리 스펙트럼의 지연도 e^(-j...) 라 그대로
    # 변환하면 봉우리가 음의 시간에 선다. 역변환을 써야 지연이 양이 된다.
    imp = np.fft.ifft(spec)
    order = np.argsort(t)
    t_ns, imp = t[order] * 1e9, np.abs(imp[order])
    imp = imp / imp.max()

    fig, ax = S.figure(8.6, 4.8)
    ax.plot(t_ns, imp, color=S.COLORS[0], lw=2.2)
    ax.set_xlim(0, 5)
    ax.set_xlabel("왕복 시간 (ns)")
    ax.set_ylabel("반사 크기 (최댓값 기준)")
    ax.set_title("그림 M14-9  시간 영역 변환 — 어디서 반사가 오는가")
    for tau, name, col in ((tau1, "커넥터", S.COLORS[1]), (tau2, "종단", S.ACCENT)):
        ax.axvline(tau * 2e9, color=col, ls=":", lw=1.4)
        ax.annotate(f"{name}\n왕복 {tau*2e9:.1f} ns\n= 편도 {tau*1e9:.1f} ns",
                    xy=(tau * 2e9, 0.5), xytext=(tau * 2e9 + 0.35, 0.62 if tau == tau1 else 0.86),
                    fontsize=8.4, color=col, fontweight="bold",
                    bbox=dict(fc="white", ec=col, lw=0.9, alpha=0.96),
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.1))
    S.save(fig, "M14", "time_domain")

    peaks = [t_ns[i] for i in range(1, len(t_ns) - 1)
             if imp[i] > imp[i - 1] and imp[i] > imp[i + 1] and imp[i] > 0.2
             and 0 < t_ns[i] < 5]
    return peaks


# ══════════════════════════════════════ 그림 4 — 부정합 불확도
def m14_mismatch():
    """두 부품을 이었을 때, 위상을 모르면 남는 불확도.

        전달되는 전력비의 분모가 |1 - Γs·Γl|^2 인데 위상을 모르므로
        (1 ± |Γs||Γl|)^2 사이 어디든 될 수 있다.
    """
    def unc_db(vswr_s, vswr_l):
        gs = (vswr_s - 1) / (vswr_s + 1)
        gl = (vswr_l - 1) / (vswr_l + 1)
        return 20 * np.log10(1 + gs * gl), 20 * np.log10(1 - gs * gl)

    v = np.linspace(1.0, 3.0, 400)
    fig, ax = S.figure(8.6, 5.0)
    for i, vs in enumerate((1.1, 1.2, 1.5, 2.0)):
        hi, lo = unc_db(vs, v)
        ax.plot(v, hi, color=S.COLORS[i], lw=2.2, label=f"측정기 VSWR {vs}")
        ax.plot(v, lo, color=S.COLORS[i], lw=2.2, ls="--")
    ax.axhline(0, color=S.INK, lw=1.0)
    ax.set_xlabel("DUT 의 VSWR")
    ax.set_ylabel("부정합 불확도 (dB)")
    ax.set_title("그림 M14-10  부정합 불확도 — 위상을 모르기 때문에 남는 폭")
    ax.legend(fontsize=8.4, loc="upper left", framealpha=0.96)
    ax.text(1.05, -1.42, S.txt("실선 = + 쪽 한계, 파선 = - 쪽 한계\n"
                               "두 선 사이가 '알 수 없는 폭' 이다"),
            fontsize=8.4, color=S.MUTED, ha="left")
    S.save(fig, "M14", "mismatch")

    return {(vs, vl): unc_db(vs, vl)
            for vs, vl in ((1.2, 2.0), (1.05, 2.0), (1.2, 1.2))}


# ══════════════════════════════════════ 그림 5 — 디임베딩
def m14_deembed():
    """픽스처를 통과해 본 DUT 를, 픽스처 S-파라미터로 되돌린다."""
    # 픽스처 한쪽: 손실 있는 짧은 선로 + 약간의 부정합
    def fixture():
        tau, loss_db_ghz = 45e-12, 0.25
        a = 10 ** (-loss_db_ghz * F_GHZ / 20.0)
        th = 2 * np.pi * F_GHZ * 1e9 * tau
        s21 = a * np.exp(-1j * th)
        s11 = 0.10 * np.exp(-1j * 2 * th)
        s = np.zeros((len(F_GHZ), 2, 2), dtype=complex)
        s[:, 0, 0] = s11
        s[:, 1, 1] = s11
        s[:, 0, 1] = s21
        s[:, 1, 0] = s21
        return rf.Network(frequency=FREQ, s=s, z0=Z0, name="fixture")

    w = 2 * np.pi * F_GHZ * 1e9
    z = 38.0 + 1j * (w * 1.8e-9 - 1.0 / (w * 2.4e-12))
    g = (z - Z0) / (z + Z0)
    s = np.zeros((len(F_GHZ), 2, 2), dtype=complex)
    s[:, 0, 0] = g
    s[:, 1, 1] = g
    s[:, 0, 1] = s[:, 1, 0] = np.sqrt(np.maximum(1 - np.abs(g) ** 2, 0))
    dut = rf.Network(frequency=FREQ, s=s, z0=Z0, name="dut")

    fx = fixture()
    measured = fx ** dut ** fx.flipped()
    recovered = fx.inv ** measured ** fx.flipped().inv

    fig, ax = S.figure(8.8, 5.0)
    db = lambda n: 20 * np.log10(np.maximum(np.abs(n.s[:, 0, 0]), 1e-9))
    ax.plot(F_GHZ, db(dut), color=S.INK, lw=2.4, label="DUT 참값")
    ax.plot(F_GHZ, db(measured), color=S.COLORS[1], lw=2.0, ls="--",
            label="픽스처를 통해 본 값")
    ax.plot(F_GHZ, db(recovered), color=S.COLORS[0], lw=1.6, ls=":",
            label="디임베딩 후")
    ax.set_xlabel("주파수 (GHz)")
    ax.set_ylabel("|S11| (dB)")
    ax.set_title("그림 M14-8  디임베딩 — 픽스처를 걷어 내면 DUT 가 보인다")
    ax.legend(fontsize=8.6, loc="lower right", framealpha=0.96)
    S.save(fig, "M14", "deembed")

    err = np.abs(recovered.s[:, 0, 0] - dut.s[:, 0, 0]).max()
    shift = np.abs(measured.s[:, 0, 0] - dut.s[:, 0, 0]).max()
    kt = int(np.argmin(np.abs(dut.s[:, 0, 0])))
    km = int(np.argmin(np.abs(measured.s[:, 0, 0])))
    notch = (F_GHZ[kt], db(dut)[kt], F_GHZ[km], db(measured)[km])
    return err, shift, dut, measured, recovered, notch


# ══════════════════════════════════════ 검산
def selfcheck(cal, trl, peaks, mm, deem):
    ok = []

    def chk(cond, msg):
        ok.append(cond)
        print(f"  [{'OK ' if cond else 'FAIL'}] {msg}")

    print("\n[자체 검산]")

    # ── 교정
    e00, e11, tr = cal["terms"]
    t00, t11, ttr = error_terms(F_GHZ)
    chk(np.abs(e00 - t00).max() < 1e-12, "손으로 푼 방향성 항이 넣은 값과 일치")
    chk(np.abs(e11 - t11).max() < 1e-12, "손으로 푼 소스 정합 항이 넣은 값과 일치")
    chk(np.abs(tr - ttr).max() < 1e-12, "손으로 푼 반사 추적 항이 넣은 값과 일치")

    s00, s11, str_ = skrf_one_port(cal["meas"], cal["std"])
    d = max(np.abs(s00 - e00).max(), np.abs(s11 - e11).max(),
            np.abs(str_ - tr).max())
    chk(d < 1e-10, f"scikit-rf 의 1-포트 교정과 완전히 일치 (최대차 {d:.2e})")

    chk(np.abs(cal["g_cal"] - cal["g_true"]).max() < 1e-10,
        "교정 후 S11 이 참값을 복원")
    raw_err = np.abs(cal["g_raw"] - cal["g_true"]).max()
    chk(raw_err > 0.05, f"교정 전 오차는 무시할 수 없다 (최대 {raw_err:.3f})")

    # ── 표준
    o = open_std(c0_ff=50.0)
    ph_lo = np.rad2deg(np.angle(o[0]))
    ph_hi = np.rad2deg(np.angle(o[-1]))
    chk(ph_lo > ph_hi and ph_hi < -5 and np.all(np.diff(np.angle(o)) < 0),
        f"개방 표준의 위상이 주파수와 함께 단조롭게 음으로 돈다 "
        f"({ph_lo:.2f}도 -> {ph_hi:.2f}도)")
    chk(np.allclose(np.abs(o), 1.0, atol=1e-9),
        "개방 표준은 무손실이라 크기는 1 을 유지")

    # ── TRL
    lo, hi = trl[30.0]
    chk(abs(hi / lo - 8.0) < 0.1,
        f"라인 하나의 쓸 수 있는 대역은 8:1 ({lo:.2f} ~ {hi:.2f} GHz)")

    # ── 시간 영역
    chk(len(peaks) == 2, f"시간 영역에서 불연속 두 개가 분리된다 ({len(peaks)}개)")
    chk(abs(peaks[0] - 2.4) < 0.15 and abs(peaks[1] - 4.0) < 0.4,
        f"봉우리가 왕복 시간 자리에 선다 ({peaks[0]:.2f}, {peaks[1]:.2f} ns)")

    # ── 부정합 불확도
    hi12, lo12 = mm[(1.2, 2.0)]
    # 손으로: Gs=0.2/2.2=0.0909, Gl=1/3, 곱 0.03030
    #        20log10(1.0303)=+0.2594, 20log10(0.9697)=-0.2673
    chk(abs(hi12 - 0.2594) < 0.001 and abs(lo12 + 0.2673) < 0.001,
        f"측정기 VSWR 1.2 · DUT 2.0 이면 +{hi12:.4f} / {lo12:.4f} dB "
        f"(손계산과 일치)")
    hi05, _ = mm[(1.05, 2.0)]
    chk(hi05 < hi12 / 3,
        f"측정기를 1.05 로 좋게 하면 불확도가 1/3 아래로 ({hi05:.3f} dB)")

    # ── 디임베딩
    err, shift = deem[0], deem[1]
    chk(err < 1e-9, f"디임베딩 후 DUT 참값과 일치 (최대차 {err:.2e})")
    chk(shift > 0.05, f"픽스처가 만드는 왜곡은 크다 (최대 {shift:.3f})")

    print("\n" + ("전부 통과" if all(ok) else "!! 실패 항목 있음"))
    return all(ok)


def main():
    cal = m14_calibration()
    trl = m14_trl_band()
    peaks = m14_time_domain()
    mm = m14_mismatch()
    deem = m14_deembed()

    print("[본문에 인용할 계산값]")
    e00, e11, tr = cal["terms"]
    print(f"  넣은 오차항 크기: 방향성 {np.abs(e00).min():.4f}~{np.abs(e00).max():.4f}"
          f" · 소스정합 {np.abs(e11).min():.3f}~{np.abs(e11).max():.3f}")
    k = int(np.argmin(np.abs(cal["g_true"])))
    d = lambda x: 20 * np.log10(np.abs(x))
    print(f"  DUT 의 진짜 노치: {F_GHZ[k]:.2f} GHz 에서 {d(cal['g_true'][k]):.1f} dB")
    print(f"    교정 전 같은 주파수에서 읽히는 값: {d(cal['g_raw'][k]):.1f} dB"
          f" (노치를 {d(cal['g_raw'][k]) - d(cal['g_true'][k]):.1f} dB 만큼 못 본다)")
    kk = int(np.argmin(np.abs(cal["g_raw"])))
    print(f"    교정 전 곡선의 가장 깊은 자리: {F_GHZ[kk]:.2f} GHz 에서"
          f" {d(cal['g_raw'][kk]):.1f} dB — 실제로는 없는 가짜 노치")
    for L, (a, b) in trl.items():
        print(f"  TRL 라인 {L:.0f} mm -> {a:.2f} ~ {b:.2f} GHz ({b/a:.1f}:1)")
    print(f"  시간영역 봉우리(왕복 ns): {[round(p,2) for p in peaks]}")
    for k, (hi, lo) in mm.items():
        print(f"  부정합 불확도 측정기 VSWR {k[0]} · DUT {k[1]} -> +{hi:.3f} / {lo:.3f} dB")
    print(f"  픽스처가 만드는 |S11| 왜곡 최대 {deem[1]:.3f}")
    ft, dt, fm, dm = deem[5]
    print(f"  DUT 진짜 노치 {ft:.2f} GHz / {dt:.1f} dB"
          f" -> 픽스처 너머로는 {fm:.2f} GHz / {dm:.1f} dB 로 보인다")
    print(f"    (주파수가 {fm-ft:+.2f} GHz 옮겨 가고, {dt-dm:.1f} dB 만큼"
          f" 실제보다 좋아 보인다)")

    return selfcheck(cal, trl, peaks, mm, deem)


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
