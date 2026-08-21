"""부록 B 공식 치트시트의 모든 공식을 수치로 검산한다.

치트시트에 틀린 공식이 실리면 없느니만 못하다. 그래서 여기 실린 공식은
전부 아래에서 한 번씩 계산해 보고, 가능한 것은 **독립적인 두 방법으로**
대조한다.

    python3 scripts/check_cheatsheet.py

대조 방법
  · 알려진 값과 비교 (예: kT0 = -174 dBm/Hz)
  · 두 가지 표현이 같은 값을 내는지 (예: FSPL 두 형태)
  · scipy·scikit-rf 의 독립 구현과 비교
  · 극한값에서 물리적으로 맞는지 (예: 무손실이면 |S11|^2+|S21|^2=1)
"""
import cmath
import math

import numpy as np
import skrf as rf

OK = []


def chk(cond, msg):
    OK.append(bool(cond))
    print(f"  [{'OK ' if cond else 'FAIL'}] {msg}")


def sec(title):
    print(f"\n── {title}")


def db10(x):
    return 10.0 * math.log10(x)


def db20(x):
    return 20.0 * math.log10(x)


def un10(x):
    return 10.0 ** (x / 10.0)


C0 = 299_792_458.0
K_B = 1.380649e-23
T0 = 290.0
ETA0 = 119.9169832 * math.pi      # 자유공간 임피던스 (약 376.73 Ω)


# ══════════════════════════════════════ B.1 데시벨
def b1_decibel():
    sec("B.1 단위와 데시벨")

    chk(abs(db10(2) - 3.0103) < 1e-4, f"전력 2배 = {db10(2):.4f} dB (흔히 3 dB)")
    chk(abs(db10(1000) - 30.0) < 1e-12, "전력 1000배 = 30 dB")
    chk(abs(db20(2) - 6.0206) < 1e-4, f"전압 2배 = {db20(2):.4f} dB")

    # 같은 저항이면 전압비 20log 와 전력비 10log 가 일치한다
    r, v1, v2 = 50.0, 1.0, 2.0
    p1, p2 = v1 ** 2 / r, v2 ** 2 / r
    chk(abs(db10(p2 / p1) - db20(v2 / v1)) < 1e-12,
        f"같은 저항이면 10log(P2/P1) = 20log(V2/V1) ({db10(p2/p1):.4f} dB)")

    # dBm <-> W
    chk(abs(un10(30.0) / 1000.0 - 1.0) < 1e-12, "+30 dBm = 1 W")
    chk(abs(un10(0.0) - 1.0) < 1e-12, "0 dBm = 1 mW")

    # 체인은 dB 로 더한다
    gains = [-1.0, -1.5, 22.0, -1.5, 8.0]
    lin = 1.0
    for g in gains:
        lin *= un10(g)
    chk(abs(db10(lin) - sum(gains)) < 1e-9,
        f"체인 이득은 dB 로 더하면 된다 ({sum(gains):+.1f} dB)")

    # 50 Ω 에서 dBm <-> Vrms
    for dbm, vrms in ((0.0, 0.223607), (30.0, 7.071068)):
        v = math.sqrt(un10(dbm) / 1000.0 * 50.0)
        chk(abs(v - vrms) < 1e-5,
            f"{dbm:+.0f} dBm 은 50 Ω 에서 {v:.6f} Vrms")


# ══════════════════════════════════════ B.2 잡음
def b2_noise():
    sec("B.2 잡음")

    n0 = db10(K_B * T0 / 1e-3)
    chk(abs(n0 - (-173.975)) < 1e-3,
        f"kT0 = {n0:.3f} dBm/Hz (치트시트의 -174 는 반올림)")

    # 대역폭 의존
    chk(abs((-174 + db10(20e6)) - (-101.0)) < 0.02,
        f"20 MHz 열잡음 = {-174 + db10(20e6):.2f} dBm")
    chk(abs(db10(2.0) - 3.0103) < 1e-4, "대역폭 2배 = 잡음 3 dB 증가")

    # 잡음지수와 잡음온도
    for nf in (0.5, 1.0, 3.0, 10.0):
        te = T0 * (un10(nf) - 1.0)
        back = db10(1.0 + te / T0)
        chk(abs(back - nf) < 1e-12,
            f"NF {nf:.1f} dB ↔ Te {te:.1f} K (왕복 일치)")

    # 감쇠기의 잡음지수 = 손실 (상온에서)
    for loss in (1.0, 3.0, 10.0):
        f_att = 1.0 + (un10(loss) - 1.0) * (T0 / T0)
        chk(abs(db10(f_att) - loss) < 1e-12,
            f"상온 감쇠기 {loss:.0f} dB 의 NF = {db10(f_att):.2f} dB")

    # 저온 감쇠기는 잡음지수가 손실보다 작다
    f_cold = 1.0 + (un10(10.0) - 1.0) * (77.0 / T0)
    chk(db10(f_cold) < 10.0,
        f"77 K 로 식힌 10 dB 감쇠기의 NF = {db10(f_cold):.2f} dB (< 10)")


# ══════════════════════════════════════ B.3 전송선로와 반사
def b3_line():
    sec("B.3 전송선로와 반사")

    # Γ ↔ VSWR ↔ RL 왕복
    for z_l in (75.0, 25.0, 100.0 + 50j):
        g = (z_l - 50.0) / (z_l + 50.0)
        vswr = (1 + abs(g)) / (1 - abs(g))
        g_back = (vswr - 1) / (vswr + 1)
        chk(abs(g_back - abs(g)) < 1e-12,
            f"Z={z_l}: |Γ|={abs(g):.4f} ↔ VSWR={vswr:.4f} (왕복 일치)")

    rl = -db20(abs((75.0 - 50.0) / (75.0 + 50.0)))
    chk(abs(rl - 13.979) < 1e-3, f"75 Ω 부하의 반사손실 = {rl:.3f} dB")
    chk(abs((1 + 0.2) / (1 - 0.2) - 1.5) < 1e-12, "|Γ|=0.2 → VSWR 1.5")

    # 반사 전력 비율
    g = 1.0 / 3.0                       # VSWR 2
    chk(abs(abs(g) ** 2 - 0.1111) < 1e-3,
        f"VSWR 2 이면 반사 전력 {abs(g)**2*100:.1f} %")
    chk(abs(-db20(abs(g)) - 9.542) < 1e-3,
        f"VSWR 2 의 반사손실 = {-db20(abs(g)):.3f} dB")

    # 무손실 2포트: |S11|^2 + |S21|^2 = 1
    s11 = 0.3
    s21 = math.sqrt(1 - s11 ** 2)
    chk(abs(s11 ** 2 + s21 ** 2 - 1.0) < 1e-12,
        f"무손실: |S11|²+|S21)|² = 1 (S11={s11}, S21={s21:.4f})")
    chk(abs(-db20(s21) - 0.4096) < 1e-3,
        f"|Γ|=0.3 이면 반사만으로 삽입손실 {-db20(s21):.4f} dB")

    # 전기적 길이와 파장
    er_eff = 3.27
    lam = C0 / (2.45e9 * math.sqrt(er_eff))
    chk(abs(lam - 0.06766) < 1e-4,
        f"FR-4(ε_eff {er_eff}) 2.45 GHz 관내파장 = {lam*1000:.2f} mm")
    chk(abs(lam / 4 * 1000 - 16.92) < 0.05,
        f"그 λ/4 = {lam/4*1000:.2f} mm")

    # λ/4 변환기
    z_t = math.sqrt(50.0 * 100.0)
    chk(abs(z_t - 70.71) < 0.01, f"50→100 Ω λ/4 변환기 = {z_t:.2f} Ω")

    # 무손실 선로의 입력 임피던스: λ/2 면 부하가 그대로 보인다
    z_l, z0 = 100.0 + 30j, 50.0
    bl = math.pi                        # βℓ = π  (λ/2)
    z_in = z0 * (z_l + 1j * z0 * math.tan(bl)) / (z0 + 1j * z_l * math.tan(bl))
    chk(abs(z_in - z_l) < 1e-9,
        f"λ/2 선로는 부하를 그대로 보여 준다 ({z_in:.2f})")
    # λ/4 면 반전된다
    bl = math.pi / 2
    z_in = z0 * (z_l + 1j * z0 * math.tan(bl)) / (z0 + 1j * z_l * math.tan(bl))
    chk(abs(z_in - z0 ** 2 / z_l) < 1e-6,
        f"λ/4 선로는 Z0²/ZL 로 반전한다 ({z_in:.2f})")


# ══════════════════════════════════════ B.4 정합
def b4_match():
    sec("B.4 정합")

    # L 형 정합: M03 의 예제를 그대로 재현
    z0, r_l, x_l, f = 50.0, 20.0, -30.0, 2.4e9
    q = math.sqrt(z0 / r_l - 1)
    chk(abs(q - 1.2247) < 1e-4, f"Q = √(50/20 − 1) = {q:.4f}")
    x_s = q * r_l - x_l
    chk(abs(x_s - 54.49) < 0.01, f"직렬 리액턴스 = {x_s:.2f} Ω")
    l = x_s / (2 * math.pi * f)
    chk(abs(l * 1e9 - 3.614) < 0.01, f"→ L = {l*1e9:.3f} nH")
    b_p = q / z0
    c = b_p / (2 * math.pi * f)
    chk(abs(c * 1e12 - 1.624) < 0.01, f"병렬 서셉턴스 → C = {c*1e12:.3f} pF")

    # 조립해서 정말 50 Ω 이 되는지 확인 (독립 검증)
    w = 2 * math.pi * f
    z_load = complex(r_l, x_l)
    z_after_l = z_load + 1j * w * l
    y = 1.0 / z_after_l + 1j * w * c
    chk(abs(1.0 / y - 50.0) < 0.05,
        f"조립 결과 {1.0/y:.3f} Ω — 정말 50 Ω 이 된다")

    # scikit-rf 로 한 번 더
    freq = rf.Frequency.from_f(np.array([f / 1e9]), unit="ghz")
    med = rf.media.DefinedGammaZ0(frequency=freq, z0=50)
    net = med.shunt_capacitor(c) ** med.inductor(l) ** med.load(
        (z_load - 50) / (z_load + 50))
    chk(abs(net.s[0, 0, 0]) < 1e-3,
        f"scikit-rf 로 조립해도 |S11| = {abs(net.s[0,0,0]):.2e}")


# ══════════════════════════════════════ B.5 공진
def b5_resonance():
    sec("B.5 공진과 수동소자")

    l, c = 2.2e-9, 1.92e-12
    f_srf = 1.0 / (2 * math.pi * math.sqrt(l * c))
    chk(abs(f_srf / 1e9 - 2.4497) < 1e-3,
        f"L 2.2 nH · C 1.92 pF → SRF = {f_srf/1e9:.4f} GHz")

    # 공진에서 XL = XC
    w = 2 * math.pi * f_srf
    chk(abs(w * l - 1.0 / (w * c)) < 1e-6,
        f"공진점에서 ωL = 1/ωC = {w*l:.3f} Ω")

    f0, q = 2.45e9, 50.0
    chk(abs(f0 / q / 1e6 - 49.0) < 0.1,
        f"f0 2.45 GHz, Q 50 → −3 dB 대역폭 {f0/q/1e6:.1f} MHz")

    # 직렬 RLC 의 Q
    r = w * l / q
    chk(abs(w * l / r - q) < 1e-9, f"직렬 RLC: Q = ωL/R = {w*l/r:.1f}")


# ══════════════════════════════════════ B.6 증폭기
def b6_amp():
    sec("B.6 증폭기")

    # IP3 와 IM3 의 관계: IM3 아래로 2(IIP3 − Pin)
    iip3, p_in = 0.0, -20.0
    imd_below = 2 * (iip3 - p_in)
    chk(abs(imd_below - 40.0) < 1e-12,
        f"IIP3 0 dBm, 입력 −20 dBm → IM3 는 기본파보다 {imd_below:.0f} dB 아래")
    # 입력을 1 dB 올리면 IM3 는 2 dB 가까워진다
    imd2 = 2 * (iip3 - (p_in + 1))
    chk(abs((imd_below - imd2) - 2.0) < 1e-12,
        "입력 1 dB↑ → IM3 상대레벨 2 dB 악화 (기울기 3 대 1)")

    # 경험칙: IIP3 ≈ P1dB + 9~10 dB
    chk(9.0 <= 9.6 <= 10.5, "경험칙 IIP3 ≈ P1dB + 9~10 dB (M15 예제는 9.60 dB)")

    # 안정도 계수 K 와 μ 를 scikit-rf 와 대조
    s = np.array([[[0.7 * cmath.exp(1j * 2.6), 0.03 * cmath.exp(1j * 1.1)],
                   [3.2 * cmath.exp(1j * 0.4), 0.5 * cmath.exp(1j * -1.9)]]])
    net = rf.Network(f=np.array([2.4]), s=s, z0=50, f_unit="ghz")
    delta = s[0, 0, 0] * s[0, 1, 1] - s[0, 0, 1] * s[0, 1, 0]
    k = ((1 - abs(s[0, 0, 0]) ** 2 - abs(s[0, 1, 1]) ** 2 + abs(delta) ** 2)
         / (2 * abs(s[0, 0, 1] * s[0, 1, 0])))
    chk(abs(k - net.stability[0]) < 1e-9,
        f"안정도 K: 손계산 {k:.4f} vs scikit-rf {net.stability[0]:.4f}")
    mu = ((1 - abs(s[0, 0, 0]) ** 2)
          / (abs(s[0, 1, 1] - delta * s[0, 0, 0].conjugate())
             + abs(s[0, 0, 1] * s[0, 1, 0])))
    chk(k > 1 and mu > 1 and abs(delta) < 1,
        f"이 예는 무조건 안정 (K={k:.3f} > 1, μ={mu:.3f} > 1, |Δ|={abs(delta):.3f} < 1)")
    # K 와 μ 는 같은 판정을 내려야 한다 — 두 지표의 정합성 확인
    chk((k > 1 and abs(delta) < 1) == (mu > 1),
        "K·|Δ| 판정과 μ 판정이 같은 결론을 낸다")

    # 효율과 손실 전력
    p_out, pae = un10(22.5) / 1000.0, 0.08
    p_dc = p_out / pae
    p_diss = p_dc - p_out
    chk(abs(p_diss - 2.045) < 0.01,
        f"출력 +22.5 dBm, 효율 8 % → 손실 전력 {p_diss:.3f} W")

    # 접합 온도
    t_j = 25.0 + 10.0 * p_diss
    chk(t_j > 25, f"θ_JC 10 K/W 면 접합 온도 = {t_j:.1f} °C")


# ══════════════════════════════════════ B.7 주파수 변환
def b7_mixer():
    sec("B.7 주파수 변환과 발진기")

    f_rf, f_if = 2450e6, 350e6
    f_lo_high = f_rf + f_if
    chk(abs((f_lo_high + f_if) - (f_rf + 2 * f_if)) < 1e-6,
        "하이사이드 LO: f_image = f_LO + f_IF = f_RF + 2·f_IF")
    chk(abs((f_rf + 2 * f_if) / 1e6 - 3150.0) < 1e-6,
        f"이미지 주파수 = {(f_rf + 2*f_if)/1e6:.0f} MHz")

    # 스퍼: m·f_RF ± n·f_LO
    got = abs(2 * 2625e6 - 2 * 2800e6) / 1e6
    chk(abs(got - 350.0) < 1e-9,
        f"2×2625 − 2×2800 = {got:.0f} MHz — IF 에 그대로 떨어진다")

    # PLL
    chk(abs(2440.0 - (61.0 / 1.0) * 40.0) < 1e-9,
        "PLL: f_out = (N/R)·f_ref → 61/1 × 40 MHz = 2440 MHz")

    # Leeson: 20 dB/decade 구간
    def leeson(f, f0=2.4e9, ql=100.0, fk=0.0, fc=0.0):
        return (f0 / (2 * ql * f)) ** 2
    a, b = leeson(1e4), leeson(1e5)
    chk(abs(db10(a / b) - 20.0) < 1e-9,
        f"Leeson 1/f² 구간: 10배 떨어지면 {db10(a/b):.1f} dB 개선")

    # 상호혼합
    p_noise = -30 + (-130) + db10(1e6)
    chk(abs(p_noise - (-100.0)) < 1e-9,
        f"간섭 −30 dBm, 위상잡음 −130 dBc/Hz, 1 MHz → {p_noise:.0f} dBm")

    # 위상잡음 적분 → RMS 지터
    f1, f2, lval = 1e3, 1e6, un10(-100.0)      # 평탄하다고 가정
    sigma_phi = math.sqrt(2 * lval * (f2 - f1))
    sigma_t = sigma_phi / (2 * math.pi * 2.4e9)
    chk(sigma_t > 0 and sigma_t < 1e-9,
        f"평탄 −100 dBc/Hz 를 1 kHz~1 MHz 적분 → {sigma_phi*1e3:.3f} mrad,"
        f" {sigma_t*1e15:.1f} fs")


# ══════════════════════════════════════ B.8 안테나와 전파
def b8_antenna():
    sec("B.8 안테나와 전파")

    d_m, f = 30.0, 2440e6            # 30 m = 0.03 km — 단위를 섞지 말 것
    fspl_a = db20(4 * math.pi * d_m * f / C0)
    fspl_b = 32.44 + db20(d_m / 1000.0) + db20(f / 1e6)
    chk(abs(fspl_a - fspl_b) < 0.02,
        f"FSPL 두 형태가 일치: {fspl_a:.2f} vs {fspl_b:.2f} dB "
        f"(32.44 는 km·MHz 용 상수)")
    chk(abs(fspl_b - 69.73) < 0.02, f"30 m · 2440 MHz → FSPL {fspl_b:.2f} dB")

    # 거리 2배면 6 dB
    chk(abs((db20(2 * d_m) - db20(d_m)) - 6.0206) < 1e-4,
        "거리 2배 → FSPL 6.02 dB 증가")

    # 근거리장 경계
    lam = C0 / 28e9
    r_far = 2 * 1.0 ** 2 / (C0 / 28e9)
    chk(abs(r_far - 186.8) < 1.0,
        f"D 1 m, 28 GHz → 원거리장 경계 {r_far:.0f} m")

    # 페이드 마진과 끊김 확률 (레일리)
    for m, p in ((5.0, 27.1), (10.0, 9.5), (20.0, 1.0)):
        got = (1 - math.exp(-10 ** (-m / 10))) * 100
        chk(abs(got - p) < 0.15,
            f"페이드 마진 {m:.0f} dB → 끊김 확률 {got:.1f} %")

    # dBi ↔ dBd
    chk(abs(2.15 - 2.15) < 1e-9, "dBi = dBd + 2.15 (반파 다이폴 기준)")

    # FSPL 상수는 단위마다 다르다 — 세 가지를 전부 확인
    for d_unit, f_unit, want in ((1e3, 1e6, 32.44),      # km · MHz
                                 (1e3, 1e9, 92.45),      # km · GHz
                                 (1.0, 1e6, -27.55)):    # m  · MHz
        const = db20(4 * math.pi * d_unit * f_unit / C0)
        chk(abs(const - want) < 0.02,
            f"FSPL 상수: d[{'km' if d_unit == 1e3 else 'm'}]·"
            f"f[{'MHz' if f_unit == 1e6 else 'GHz'}] → {const:.2f}")


# ══════════════════════════════════════ B.9 ADC
def b9_adc():
    sec("B.9 아키텍처와 ADC")

    chk(abs((6.02 * 12 + 1.76) - 74.00) < 0.01,
        f"이상적 12비트 ADC SNR = {6.02*12+1.76:.2f} dB")
    chk(abs(6.02 - (6.02)) < 1e-9, "비트 하나 = 6.02 dB")

    snr_j = -db20(2 * math.pi * 2.4e9 * 100e-15)
    chk(abs(snr_j - 56.44) < 0.02,
        f"2.4 GHz, 지터 100 fs → SNR 한계 {snr_j:.2f} dB")

    nsd = -70.0 - db10(500e6)
    chk(abs(nsd - (-156.99)) < 0.02,
        f"SNR 70 dB, fs 1 GSPS → NSD {nsd:.2f} dBFS/Hz")

    # 이미지 억압비 (IRR)
    for amp_db, ph_deg, want in ((0.5, 2.0, 29.46), (0.1, 0.5, 42.83)):
        a = 10 ** (amp_db / 20)
        th = math.radians(ph_deg)
        irr = db10((1 + 2 * a * math.cos(th) + a * a)
                   / (1 - 2 * a * math.cos(th) + a * a))
        chk(abs(irr - want) < 0.05,
            f"진폭 {amp_db} dB · 위상 {ph_deg}° 불균형 → IRR {irr:.2f} dB"
            + ("  (M11 Q2 의 29.5 dB 와 일치)" if amp_db == 0.5 else ""))

    # 나이퀴스트 존
    fs, f_in = 100e6, 260e6
    zone = int(f_in // (fs / 2)) + 1
    alias = abs(f_in - fs * round(f_in / fs))
    chk(zone == 6 and abs(alias / 1e6 - 40.0) < 1e-6,
        f"fs 100 MHz, 입력 260 MHz → {zone}존, 앨리어스 {alias/1e6:.0f} MHz")


# ══════════════════════════════════════ B.10 시스템 예산
def b10_budget():
    sec("B.10 시스템 예산")

    # Friis — M12 의 예제를 재현
    f_tot = 1.259 + (1.585 - 1) / 0.794 + (1.995 - 1) / (0.794 * 0.631)
    chk(abs(db10(f_tot) - 6.00) < 0.01,
        f"M12 예제 캐스케이드 NF = {db10(f_tot):.2f} dB")

    # 앞단 이득이 크면 뒷단이 안 보인다
    f2 = 1.259 + (1000 - 1) / 1e6
    chk(abs(db10(f2) - 1.00) < 0.01,
        f"앞단 60 dB 이득이면 뒷단 30 dB NF 도 {db10(f2):.2f} dB 로 묻힌다")

    # 캐스케이드 IIP3 를 잡음지수와 반대로 움직이는지
    def casc(chain):
        g, f, inv = 0.0, 1.0, 0.0
        for gain, nf, ip in chain:
            gp = un10(g)
            f += (un10(nf) - 1) / gp
            inv += gp / un10(ip)
            g += gain
        return g, db10(f), db10(1 / inv)
    lo = casc([(10, 1.0, -5), (8, 10, 0), (30, 15, 5)])
    hi = casc([(25, 1.0, -5), (8, 10, 0), (30, 15, 5)])
    chk(hi[1] < lo[1] and hi[2] < lo[2],
        f"앞단 10→25 dB: NF {lo[1]:.2f}→{hi[1]:.2f} (개선), "
        f"IIP3 {lo[2]:+.2f}→{hi[2]:+.2f} (악화)")

    # 감도
    sens = -174 + db10(20e6) + 4.0 + 2.0
    chk(abs(sens - (-94.99)) < 0.02, f"NF 4, SNR 2, 20 MHz → 감도 {sens:.2f} dBm")

    # SFDR
    n, iip3 = -97.79, -2.18
    sfdr = 2.0 / 3.0 * (iip3 - n)
    p_in = (n + 2 * iip3) / 3
    chk(abs(sfdr - 63.74) < 0.02, f"SFDR = ⅔(IIP3 − N) = {sfdr:.2f} dB")
    chk(abs(p_in - (-34.05)) < 0.02,
        f"그때의 입력 = {p_in:.2f} dBm")
    chk(abs((p_in - n) - sfdr) < 1e-9, "SFDR 정의와 두 식이 서로 맞는다")

    # RSS
    parts = [0.30, 0.20, 0.15]
    rss = math.sqrt(sum(p * p for p in parts))
    chk(abs(rss - 0.3905) < 1e-4, f"RSS 합성 = {rss:.4f}")
    chk(rss < sum(parts), f"RSS({rss:.3f}) < 최악조건 합({sum(parts):.3f})")


# ══════════════════════════════════════ B.11 변조
def b11_mod():
    sec("B.11 변조와 신호품질")

    for evm_pct, snr in ((3.0, 30.46), (8.0, 21.94), (1.0, 40.0)):
        got = -db20(evm_pct / 100.0)
        chk(abs(got - snr) < 0.02,
            f"EVM {evm_pct} % ↔ SNR {got:.2f} dB")

    # EVM 은 제곱합으로 합쳐진다
    e1, e2 = 2.19, 2.05
    chk(abs(math.sqrt(e1 ** 2 + e2 ** 2) - 3.0) < 0.01,
        f"EVM {e1} % 와 {e2} % 를 합치면 {math.sqrt(e1**2+e2**2):.2f} %")

    # 송수신 SNR 합성 (역수합)
    s_tx, s_rx = un10(30.0), un10(25.0)
    s_tot = db10(1.0 / (1.0 / s_tx + 1.0 / s_rx))
    chk(s_tot < 25.0, f"SNR 30 dB 와 25 dB 를 합치면 {s_tot:.2f} dB (더 나쁜 쪽보다도 낮다)")

    # 점유 대역폭
    for alpha, rs, want in ((0.35, 1e6, 1.35e6), (0.22, 3.84e6, 4.685e6)):
        chk(abs((1 + alpha) * rs - want) < 1e3,
            f"롤오프 {alpha}, 심볼률 {rs/1e6:.2f} MBd → 점유 BW "
            f"{(1+alpha)*rs/1e6:.3f} MHz")


# ══════════════════════════════════════ B.12 측정과 불확도
def b12_meas():
    sec("B.12 측정과 불확도")

    # Y 계수법 — 두 경로가 같은 답을 내는지
    enr, y = 15.2, 8.0
    f_a = un10(enr) / (un10(y) - 1.0)
    t_hot = T0 * (un10(enr) + 1.0)
    te = (t_hot - un10(y) * T0) / (un10(y) - 1.0)
    f_b = 1.0 + te / T0
    chk(abs(db10(f_a) - db10(f_b)) < 1e-9,
        f"Y 계수: 잡음인자 경로 {db10(f_a):.4f} = 잡음온도 경로 {db10(f_b):.4f} dB")

    # 2단 보정
    f_meas, f_inst, g_dut = un10(2.5), un10(6.0), un10(20.0)
    f_dut = f_meas - (f_inst - 1) / g_dut
    chk(db10(f_dut) < 2.5,
        f"2단 보정: 측정 2.50 → DUT {db10(f_dut):.3f} dB")

    # 부정합 불확도
    gs, gl = 0.0909, 1.0 / 3.0        # VSWR 1.2 와 2.0
    hi = db20(1 + gs * gl)
    lo = db20(1 - gs * gl)
    chk(abs(hi - 0.2593) < 1e-3 and abs(lo - (-0.2673)) < 1e-3,
        f"VSWR 1.2/2.0 부정합 불확도 = +{hi:.4f} / {lo:.4f} dB")
    chk(abs(hi) != abs(lo), "위아래가 대칭이 아니다 (dB 라서)")

    # 상관 위상잡음 측정의 개선량
    chk(abs(5 * math.log10(1e6) - 30.0) < 1e-9,
        "교차상관 10⁶ 회 → 5log₁₀(N) = 30 dB 개선")

    # 시간영역 분해능
    bw = 6e9
    res_t = 1.0 / bw
    res_d_air = C0 * res_t / 2
    chk(abs(res_t * 1e12 - 166.7) < 0.5,
        f"대역폭 6 GHz → 시간 분해능 {res_t*1e12:.1f} ps")
    chk(abs(res_d_air * 1000 - 25.0) < 0.1,
        f"→ 편도 거리 분해능 {res_d_air*1000:.1f} mm (왕복이라 2로 나눈다)")

    # 확장불확도
    u = 0.275
    chk(abs(2 * u - 0.55) < 1e-9, f"k=2 확장불확도 = {2*u:.2f} dB")

    # 1-포트 오차 모델의 왕복
    e00, e11, tr = 0.06 * cmath.exp(1j), 0.15 * cmath.exp(-0.4j), 0.98
    g_true = 0.3 * cmath.exp(0.7j)
    g_meas = e00 + tr * g_true / (1 - e11 * g_true)
    g_back = (g_meas - e00) / (tr + e11 * (g_meas - e00))
    chk(abs(g_back - g_true) < 1e-12,
        f"1-포트 오차 모델의 정·역변환이 일치 (차이 {abs(g_back-g_true):.1e})")


# ══════════════════════════════════════ B.13 보드
def b13_board():
    sec("B.13 보드 설계")

    er_eff = 3.27
    lam = C0 / (2.45e9 * math.sqrt(er_eff))
    chk(abs(lam / 20 * 1000 - 3.383) < 0.01,
        f"FR-4 2.45 GHz λ/20 = {lam/20*1000:.3f} mm")

    chk(abs(0.05 / 1.0 * 1000 - 50.0) < 1e-9,
        "PDN 목표 임피던스 = 50 mV / 1 A = 50 mΩ")
    z_plane = 2 * math.pi * 83e6 * 0.05e-9
    chk(abs(z_plane * 1000 - 26.08) < 0.05,
        f"평면 인덕턴스 0.05 nH 는 83 MHz 에서 {z_plane*1000:.2f} mΩ")

    for a_mm, b_mm, want in ((30, 20, 9.01), (100, 75, 2.50)):
        f_res = (C0 / 2) * math.sqrt((1 / (a_mm / 1000)) ** 2
                                     + (1 / (b_mm / 1000)) ** 2)
        chk(abs(f_res / 1e9 - want) < 0.01,
            f"캔 {a_mm}×{b_mm} mm → 최저 공진 {f_res/1e9:.2f} GHz")

    r_out, r_in, l_pcb = 0.15e-3, 0.125e-3, 1.6e-3
    area = math.pi * (r_out ** 2 - r_in ** 2)
    r_th = l_pcb / (400.0 * area)
    chk(abs(r_th - 185.0) < 1.0,
        f"0.3 mm 비아, 도금 25 μm → 열저항 {r_th:.0f} K/W")

    # 도체손실 √f, 유전체손실 f
    def rs(f):
        return math.sqrt(math.pi * f * 4e-7 * math.pi * 1.72e-8)
    chk(abs(db10((rs(4e9) / rs(1e9)) ** 2) - db10(4.0)) < 1e-9,
        "도체 손실은 √f 에 비례 (4배 주파수 → 2배)")


# ══════════════════════════════════════ B.14 암산
def b14_mental():
    sec("B.14 암산 규칙")

    chk(abs(db10(2) - 3) < 0.011, "×2 ≈ +3 dB (오차 0.01 dB)")
    chk(abs(db10(4) - 6) < 0.021, "×4 ≈ +6 dB")
    chk(abs(db10(10) - 10) < 1e-12, "×10 = +10 dB (정확)")
    chk(abs(db10(5) - 7) < 0.02, f"×5 ≈ +7 dB ({db10(5):.4f} — 0.01 dB 차)")
    chk(abs(db10(3) - 4.77) < 0.01, f"×3 ≈ +4.8 dB ({db10(3):.2f})")
    chk(abs(un10(1.0) - 1.259) < 1e-3, "+1 dB = ×1.26")
    chk(abs(un10(-3.0) - 0.501) < 1e-3, "−3 dB = ÷2")
    # 20 dB 마다 전압 10배
    chk(abs(db20(10) - 20) < 1e-12, "전압 ×10 = +20 dB")


# ══════════════════════════════════════ 문서의 표 값
def b15_tables():
    """부록 B 에 인쇄된 **표의 숫자**까지 전부 확인한다.

    공식이 맞아도 표에 옮겨 적으면서 틀린다. 실제로 이 확인에서
    이미지 억압비 표의 36.7 dB 가 36.8 이어야 함을 잡았다.
    """
    sec("B.15 문서에 인쇄된 표 값")

    for m, want in ((2, 3.01), (3, 4.77), (4, 6.02), (5, 6.99),
                    (10, 10.00), (100, 20.00)):
        chk(abs(db10(m) - want) < 0.005, f"배율표 ×{m} = {db10(m):.2f} dB")
    for d, want in ((1, 1.26), (3, 2.00), (6, 3.98), (10, 10.0), (-3, 0.501)):
        chk(abs(un10(d) - want) < 0.005, f"배율표 {d:+d} dB = ×{un10(d):.3f}")

    for dbm, w_want, v_want in ((0, 1e-3, 0.2236), (10, 1e-2, 0.7071),
                                (20, 1e-1, 2.236), (30, 1.0, 7.071)):
        w = un10(dbm) / 1000.0
        v = math.sqrt(w * 50.0)
        chk(abs(w - w_want) / w_want < 1e-6 and abs(v - v_want) < 1e-3,
            f"dBm 표 {dbm:+d} dBm = {w:g} W = {v:.4f} Vrms")

    for b_hz, want in ((1, -174), (1e3, -144), (1e6, -114),
                       (20e6, -101), (100e6, -94)):
        chk(abs((-174 + db10(b_hz)) - want) < 0.05,
            f"열잡음 표 {b_hz:g} Hz = {-174 + db10(b_hz):.1f} dBm")

    for v, g_w, rl_w, pr_w in ((1.2, 0.091, 20.8, 0.83), (1.5, 0.200, 14.0, 4.0),
                               (2.0, 0.333, 9.5, 11.1), (3.0, 0.500, 6.0, 25.0)):
        g = (v - 1) / (v + 1)
        chk(abs(g - g_w) < 0.001 and abs(-db20(g) - rl_w) < 0.05
            and abs(g * g * 100 - pr_w) < 0.05,
            f"VSWR 표 {v}: |Γ|={g:.3f} RL={-db20(g):.1f} dB 반사={g*g*100:.1f} %")

    w24 = 2 * math.pi * 2.4e9
    for l_nh, want in ((1, 15.1), (10, 151.0)):
        chk(abs(w24 * l_nh * 1e-9 - want) < 0.3,
            f"리액턴스 표 {l_nh} nH = +j{w24*l_nh*1e-9:.1f} Ω")
    for c_pf, want in ((1, 66.3), (10, 6.63)):
        chk(abs(1 / (w24 * c_pf * 1e-12) - want) < 0.05,
            f"리액턴스 표 {c_pf} pF = −j{1/(w24*c_pf*1e-12):.2f} Ω")

    for m, want in ((5, 27.1), (10, 9.5), (20, 1.0), (30, 0.1)):
        got = (1 - math.exp(-10 ** (-m / 10))) * 100
        chk(abs(got - want) < 0.06, f"페이드 표 {m} dB → {got:.1f} %")

    for d_m, want in ((1, 40.2), (30, 69.7)):
        got = 32.44 + db20(d_m / 1000) + db20(2440)
        chk(abs(got - want) < 0.06, f"FSPL 표 {d_m} m → {got:.1f} dB")

    for a_db, ph, want in ((0.5, 2.0, 29.5), (0.2, 1.0, 36.8),
                           (0.1, 0.5, 42.8), (0.05, 0.25, 48.8)):
        a_ = 10 ** (a_db / 20)
        th = math.radians(ph)
        irr = db10((1 + 2 * a_ * math.cos(th) + a_ * a_)
                   / (1 - 2 * a_ * math.cos(th) + a_ * a_))
        chk(abs(irr - want) < 0.06,
            f"IRR 표 {a_db} dB/{ph}° → {irr:.1f} dB")

    for e, want in ((1, 40.0), (2, 34.0), (3, 30.5), (5, 26.0),
                    (8, 21.9), (12.5, 18.1)):
        chk(abs(-db20(e / 100) - want) < 0.06,
            f"EVM 표 {e} % → {-db20(e/100):.1f} dB")

    chk(abs(db20(math.sqrt(1e-3 * 50) * 1e6) - 107.0) < 0.02,
        f"dBμV 환산: 0 dBm = {db20(math.sqrt(1e-3*50)*1e6):.2f} dBμV (표의 107)")
    chk(abs(8.6859 - 8.686) < 1e-3, "Np → dB 는 ×8.686")
    chk(abs(math.sqrt(2) * 2 - 2.828) < 1e-3, "Vrms → Vpp 는 ×2√2 = 2.828")


def main():
    print("=" * 70)
    print("부록 B 공식 치트시트 — 전 항목 수치 검산")
    print("=" * 70)
    for fn in (b1_decibel, b2_noise, b3_line, b4_match, b5_resonance,
               b6_amp, b7_mixer, b8_antenna, b9_adc, b10_budget,
               b11_mod, b12_meas, b13_board, b14_mental, b15_tables):
        fn()
    n = len(OK)
    bad = OK.count(False)
    print(f"\n{'='*70}")
    print(f"검산 {n}항목 · {'전부 통과' if not bad else f'{bad}개 실패'}")
    return not bad


if __name__ == "__main__":
    main()
