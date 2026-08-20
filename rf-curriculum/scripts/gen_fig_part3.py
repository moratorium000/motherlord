#!/usr/bin/env python3
"""
Part III 전반부 (M06, M07) 데이터 그림 생성기
=============================================

    python3 scripts/gen_fig_part3.py

출력: assets/M06/*.svg, assets/M07/*.svg
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

import rf_style as S


# ══════════════════════════════════════════════════════════ 공통 모델
def z_real_cap(f, c_f, esl_h, esr_ohm):
    """실제 커패시터: ESR + jwL + 1/(jwC) 직렬 모델."""
    w = 2 * np.pi * f
    return esr_ohm + 1j * w * esl_h + 1 / (1j * w * c_f)


def z_real_ind(f, l_h, cp_f, rs_ohm):
    """실제 인덕터: (Rs + jwL) 과 기생 Cp 의 병렬 모델."""
    w = 2 * np.pi * f
    z_l = rs_ohm + 1j * w * l_h
    y = 1 / z_l + 1j * w * cp_f
    return 1 / y


def srf(l_h, c_f):
    return 1 / (2 * np.pi * np.sqrt(l_h * c_f))


# ══════════════════════════════════════════════════════════ M06
def m06_cap_srf():
    """커패시터는 SRF 위에서 인덕터가 된다."""
    fig, ax = S.figure(7.8, 4.6)
    f = np.logspace(6, 10.3, 900)
    esl, esr = 0.5e-9, 0.05                      # 0402 MLCC 대표값

    for c, name in [(100e-9, "100 nF"), (1e-9, "1 nF"),
                    (100e-12, "100 pF"), (10e-12, "10 pF")]:
        z = np.abs(z_real_cap(f, c, esl, esr))
        ax.loglog(f, z, lw=2.0, label=f"{name}")
        f0 = srf(esl, c)
        ax.plot([f0], [esr], "o", color=S.ACCENT, ms=6.5, zorder=8)

    # 10 pF 곡선도 점선이라 헷갈리므로 이상적 곡선은 굵은 회색 파선으로 구분
    z_ideal = 1 / (2 * np.pi * f * 100e-12)
    ax.loglog(f, z_ideal, color=S.MUTED, ls=(0, (6, 3)), lw=2.0, alpha=0.9,
              label="이상적인 100 pF (기생 없음)")

    ax.annotate("빨간 점 = 자기공진주파수(SRF)\n왼쪽은 커패시터, 오른쪽은 인덕터",
                xy=(srf(esl, 1e-9), esr), xytext=(1.6e6, 4.0),
                fontsize=9.2, color=S.ACCENT, fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.95, lw=0.9),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.2))

    ax.set_xlabel("주파수 (Hz)")
    ax.set_ylabel("임피던스 크기 |Z| (Ω)")
    ax.set_title("그림 M06-2  커패시터의 임피던스 (ESL 0.5 nH, ESR 0.05 Ω 가정)")
    ax.set_ylim(1e-2, 1e4)
    ax.legend(fontsize=9, loc="upper right")
    S.plain_log(ax, "y")
    S.hz_ticks(ax, [1e6, 1e7, 1e8, 1e9, 1e10])
    S.save(fig, "M06", "cap_srf")


def m06_ind_srf():
    """인덕터는 SRF 위에서 커패시터가 된다."""
    fig, ax = S.figure(7.6, 4.4)
    f = np.logspace(7, 10.5, 800)
    rs = 0.3

    for l, cp, name in [(100e-9, 0.30e-12, "100 nH"),
                        (10e-9, 0.15e-12, "10 nH"),
                        (2.2e-9, 0.08e-12, "2.2 nH")]:
        z = np.abs(z_real_ind(f, l, cp, rs))
        ax.loglog(f, z, lw=2.0, label=f"{name} (기생 C {cp*1e12:.2f} pF)")
        f0 = srf(l, cp)
        ax.plot([f0], [np.abs(z_real_ind(f0, l, cp, rs))], "o",
                color=S.ACCENT, ms=6.5, zorder=8)

    ax.loglog(f, 2 * np.pi * f * 10e-9, color=S.MUTED, ls=(0, (6, 3)), lw=2.0,
              alpha=0.9, label="이상적인 10 nH")

    ax.set_xlabel("주파수 (Hz)")
    ax.set_ylabel("임피던스 크기 |Z| (Ω)")
    ax.set_title("그림 M06-3  인덕터의 임피던스 — SRF 위에서는 커패시터처럼 행동")
    ax.set_ylim(1e0, 1e5)
    ax.legend(fontsize=8.8, loc="upper left")
    S.plain_log(ax, "y")
    S.hz_ticks(ax, [1e7, 1e8, 1e9, 1e10])
    S.save(fig, "M06", "ind_srf")


def m06_q_bandwidth():
    """Q가 클수록 공진이 날카롭다. BW = f0 / Q."""
    fig, ax = S.figure(7.6, 4.4)
    f0 = 1.0                                       # 정규화 중심 주파수
    f = np.linspace(0.6, 1.4, 1600)

    for q in (5, 20, 100):
        x = f / f0 - f0 / f
        h = 1 / np.sqrt(1 + (q * x) ** 2)          # 2차 공진 응답
        ax.plot(f, 20 * np.log10(h), lw=2.1, label=f"Q = {q}   (BW = f0/{q})")
        # -3 dB 대역폭 표시
        bw = f0 / q
        ax.plot([f0 - bw / 2, f0 + bw / 2], [-3, -3], "o", color=S.ACCENT,
                ms=5.5, zorder=8)

    ax.axhline(-3, color=S.ACCENT, ls="--", lw=1.5)
    ax.annotate("-3 dB 선 — 여기서 잰 폭이 대역폭", xy=(1.30, -3),
                xytext=(1.14, -8.5), fontsize=9, color=S.ACCENT,
                fontweight="bold",
                bbox=dict(fc="white", ec=S.ACCENT, alpha=0.95, lw=0.8),
                arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.1))

    ax.set_xlabel("주파수 (중심 주파수 f0 기준)")
    ax.set_ylabel("응답 (dB)")
    ax.set_title("그림 M06-5  품질계수 Q와 대역폭:  BW = f0 / Q")
    ax.set_ylim(-30, 3)
    ax.legend(fontsize=9.2)
    S.save(fig, "M06", "q_bandwidth")


def m06_decoupling():
    """커패시터를 병렬로 달면 반공진(anti-resonance) 봉우리가 생긴다."""
    fig, ax = S.figure(7.8, 4.6)
    f = np.logspace(6, 9.7, 1200)
    esl, esr = 0.5e-9, 0.05

    caps = [(10e-6, 1.5e-9, 0.02, "10 uF"),
            (100e-9, esl, esr, "100 nF"),
            (1e-9, esl, esr, "1 nF")]
    y_tot = np.zeros_like(f, dtype=complex)
    for c, l_, r_, name in caps:
        z = z_real_cap(f, c, l_, r_)
        ax.loglog(f, np.abs(z), ls="-", lw=1.3, alpha=0.7, label=f"{name} 단독")
        y_tot += 1 / z
    z_tot = 1 / y_tot
    S.emph(ax, f, np.abs(z_tot), label="셋을 병렬로")
    ax.set_xscale("log"); ax.set_yscale("log")

    i = np.argmax(np.abs(z_tot) * (f > 2e7) * (f < 4e8))
    ax.plot([f[i]], [np.abs(z_tot)[i]], "X", color=S.INK, ms=12, zorder=9)
    ax.annotate("반공진(anti-resonance)\n한 커패시터의 인덕턴스와\n"
                "다른 커패시터가 만드는 봉우리\n= 여기서는 오히려 나빠진다",
                xy=(f[i], np.abs(z_tot)[i]), xytext=(1.3e6, 1.2),
                fontsize=8.8, color=S.INK, fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.INK, alpha=0.95, lw=0.9),
                arrowprops=dict(arrowstyle="->", color=S.INK, lw=1.2))

    ax.set_xlabel("주파수 (Hz)")
    ax.set_ylabel("임피던스 크기 |Z| (Ω)")
    ax.set_title("그림 M06-6  디커플링 커패시터를 병렬로 다는 것의 빛과 그림자")
    ax.set_ylim(1e-3, 1e2)
    ax.legend(fontsize=8.8, loc="upper right")
    S.plain_log(ax, "y")
    S.hz_ticks(ax, [1e6, 1e7, 1e8, 1e9])
    S.save(fig, "M06", "decoupling")
    return f[i], np.abs(z_tot)[i]


# ══════════════════════════════════════════════════════════ M07
_PROTOS = {
    "버터워스 (Butterworth)": lambda n: signal.butter(n, 1, analog=True),
    "체비셰프 I형 (리플 0.5 dB)": lambda n: signal.cheby1(n, 0.5, 1, analog=True),
    "타원형 (Elliptic, 0.5/50 dB)": lambda n: signal.ellip(n, 0.5, 50, 1,
                                                           analog=True),
    "베셀 (Bessel)": lambda n: signal.bessel(n, 1, analog=True, norm="mag"),
}


def m07_responses():
    """같은 차수, 다른 응답 — 무엇을 얻고 무엇을 잃는가."""
    fig, axes = plt.subplots(1, 2, figsize=(9.8, 4.3))
    S.setup()
    fig.patch.set_facecolor("white")
    w = np.logspace(-1, 1.2, 900)

    for name, mk in _PROTOS.items():
        b, a = mk(5)
        _, h = signal.freqs(b, a, w)
        axes[0].semilogx(w, 20 * np.log10(np.abs(h)), lw=2.0, label=name)

    axes[0].set_xlabel("정규화 주파수 (차단 주파수 = 1)")
    axes[0].set_ylabel("|S21| (dB)")
    axes[0].set_title("5차 필터 4종 — 전체 응답", fontsize=10.5)
    axes[0].set_ylim(-90, 6)
    axes[0].legend(fontsize=8.2, loc="lower left")
    axes[0].grid(alpha=0.5, which="both")
    S.plain_log(axes[0], "x")

    w2 = np.linspace(0.02, 1.05, 700)
    for name, mk in _PROTOS.items():
        b, a = mk(5)
        _, h = signal.freqs(b, a, w2)
        axes[1].plot(w2, 20 * np.log10(np.abs(h)), lw=2.0)
    axes[1].axhline(-0.5, color=S.ACCENT, ls="--", lw=1.3)
    axes[1].annotate("통과대역 리플 0.5 dB", xy=(0.35, -0.5), xytext=(0.08, -1.4),
                     fontsize=9, color=S.ACCENT, fontweight="bold",
                     arrowprops=dict(arrowstyle="->", color=S.ACCENT, lw=1.1))
    axes[1].set_xlabel("정규화 주파수")
    axes[1].set_ylabel("|S21| (dB)")
    axes[1].set_title("통과대역 확대 — 평탄한가, 물결치는가", fontsize=10.5)
    axes[1].set_ylim(-2.2, 0.4)
    axes[1].grid(alpha=0.5)

    fig.suptitle("그림 M07-1  필터 응답 4종 비교 (같은 5차)", fontweight="bold")
    fig.tight_layout()
    S.save(fig, "M07", "responses")


def m07_group_delay():
    """평탄한 진폭과 평탄한 군지연은 함께 얻을 수 없다."""
    fig, ax = S.figure(7.6, 4.4)
    w = np.linspace(0.02, 2.0, 1400)
    for name, mk in _PROTOS.items():
        b, a = mk(5)
        _, h = signal.freqs(b, a, w)
        ph = np.unwrap(np.angle(h))
        gd = -np.gradient(ph, w)
        ax.plot(w, gd, lw=2.0, label=name)

    ax.axvline(1.0, color=S.MUTED, ls=":", lw=1.2)
    ax.text(1.03, 8.5, "차단 주파수", fontsize=9, color=S.MUTED)
    ax.annotate("베셀은 군지연이 평탄하다\n= 파형이 덜 일그러진다\n"
                "(대신 차단이 완만하다)", xy=(0.45, 2.4), xytext=(0.06, 6.6),
                fontsize=9, color=S.INK, fontweight="bold", ha="left",
                bbox=dict(fc="white", ec=S.INK, alpha=0.95, lw=0.9),
                arrowprops=dict(arrowstyle="->", color=S.INK, lw=1.2))

    ax.set_xlabel("정규화 주파수")
    ax.set_ylabel("군지연 (정규화)")
    ax.set_title("그림 M07-2  같은 필터들의 군지연 — 진폭만 봐서는 모른다")
    ax.set_ylim(0, 11)
    ax.legend(fontsize=8.6, loc="upper right")
    S.save(fig, "M07", "group_delay")


def m07_spec_annotated():
    """필터 데이터시트를 읽는 법 — 그림 위에 용어를 얹는다."""
    fig, ax = S.figure(8.4, 5.0)

    # 2.4 GHz ISM 대역통과 필터를 흉내 낸다.
    # 주의: analog=True 일 때 Wn 과 freqs 의 w 는 모두 rad/s 이다.
    f = np.linspace(2.15e9, 2.75e9, 4000)
    f1, f2 = 2.400e9, 2.4835e9
    il = 1.6                                       # 삽입손실 [dB]
    b, a = signal.cheby1(4, 0.3, [2 * np.pi * f1, 2 * np.pi * f2],
                         btype="band", analog=True)
    _, h = signal.freqs(b, a, 2 * np.pi * f)
    s21 = 20 * np.log10(np.abs(h) + 1e-12) - il
    ax.plot(f / 1e9, s21, color=S.COLORS[0], lw=2.2)

    top = s21.max()
    i3 = np.where(s21 >= top - 3)[0]
    f3lo, f3hi = f[i3[0]], f[i3[-1]]
    i60 = np.where(s21 >= top - 40)[0]
    f40lo, f40hi = f[i60[0]], f[i60[-1]]
    shape = (f40hi - f40lo) / (f3hi - f3lo)

    ax.axvspan(f3lo / 1e9, f3hi / 1e9, color=S.COLORS[2], alpha=0.14)

    def mark(x, y, text, tx, ty, col=S.ACCENT):
        ax.plot([x], [y], "o", color=col, ms=7, zorder=9)
        ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=8.8,
                    color=col, fontweight="bold", zorder=10, ha="center",
                    bbox=dict(fc="white", ec=col, alpha=0.96, lw=0.8),
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.1))

    fc = (f1 + f2) / 2
    mark(fc / 1e9, np.interp(fc, f, s21),
         f"삽입손실 (IL) {il:.1f} dB\n통과대역에서 얼마나 줄어드나",
         2.60, 8)
    mark(f3lo / 1e9, top - 3, f"-3 dB 대역폭\n{(f3hi-f3lo)/1e6:.0f} MHz",
         2.245, -16)
    mark(2.25, np.interp(2.25e9, f, s21), "저지대역 억압\n(rejection)",
         2.26, -46)
    mark(f3hi / 1e9 + 0.012, np.interp(f3hi + 0.012e9, f, s21),
         "스커트(skirt)\n= 얼마나 가파른가", 2.63, -22)

    ax.annotate(f"형상계수(shape factor)\n= -40 dB 폭 / -3 dB 폭\n"
                f"= {(f40hi-f40lo)/1e6:.0f} / {(f3hi-f3lo)/1e6:.0f} = {shape:.2f}\n"
                f"(1에 가까울수록 이상적인 벽)",
                xy=(2.30, -34), fontsize=8.8, color=S.INK, ha="left",
                bbox=dict(fc="white", ec=S.INK, alpha=0.95, lw=0.9))

    ax.set_xlabel("주파수 (GHz)")
    ax.set_ylabel("|S21| (dB)")
    ax.set_title("그림 M07-3  필터 사양서의 용어를 응답 위에 얹으면")
    ax.set_ylim(-75, 16)
    ax.set_xlim(2.15, 2.75)
    S.save(fig, "M07", "spec_annotated")
    return dict(bw3=(f3hi - f3lo) / 1e6, bw40=(f40hi - f40lo) / 1e6,
                shape=shape)


def m07_order():
    """차수를 올리면 가팔라지지만 손실과 크기가 커진다."""
    fig, ax = S.figure(7.6, 4.4)
    w = np.logspace(-0.5, 1.2, 800)
    for n in (3, 5, 7, 9):
        b, a = signal.butter(n, 1, analog=True)
        _, h = signal.freqs(b, a, w)
        # 점근 기울기를 범례에 함께 적는다. 그래프 안에 쓰면 서로 겹친다.
        ax.semilogx(w, 20 * np.log10(np.abs(h)), lw=2.0,
                    label=f"{n}차  —  {20*n} dB/decade = {6*n} dB/옥타브")
    ax.annotate("차수를 올리면 가팔라진다\n대신 소자 수·삽입손실·크기·비용이 커진다",
                xy=(1.35, -12), fontsize=9, color=S.INK, ha="left",
                bbox=dict(fc="white", ec=S.GRID, alpha=0.95))
    ax.set_xlabel("정규화 주파수 (차단 = 1)")
    ax.set_ylabel("|S21| (dB)")
    ax.set_title("그림 M07-4  버터워스 필터의 차수와 롤오프")
    ax.set_ylim(-100, 6)
    ax.legend(fontsize=8.6, loc="lower left")
    ax.grid(alpha=0.5, which="both")
    S.plain_log(ax, "x")
    S.save(fig, "M07", "order")


def m07_tech_map():
    """필터 기술의 적용 영역 — 주파수 범위를 가로 막대로."""
    fig, ax = S.figure(8.4, 4.8)

    # (이름, f_min GHz, f_max GHz, 전력, 전형적 삽입손실, 크기 감각)
    techs = [
        ("캐비티", 0.03, 20.0, "수십~수백 W", "0.5~1.5 dB", "가장 큼"),
        ("마이크로스트립 분포소자", 0.5, 40.0, "수 W", "1~3 dB", "중간"),
        ("LC 집중소자", 0.001, 3.0, "수 W", "1~3 dB", "작음"),
        ("세라믹", 0.3, 6.0, "약 5 W 이하", "1.5~3 dB", "작음"),
        ("BAW / FBAR", 1.0, 20.0, "수 W 이하", "1~2 dB", "가장 작음"),
        ("SAW", 0.03, 2.0, "1 W 이하", "2~4 dB", "가장 작음"),
    ]
    for i, (name, f1, f2, p, il, size) in enumerate(techs):
        y = len(techs) - 1 - i
        col = S.COLORS[i % len(S.COLORS)]
        # ls 를 명시하지 않으면 rcParams 의 선모양 순환이 적용되어
        # 막대가 점선으로 끊겨 보인다 (Part I 정재파 그림에서와 같은 실수).
        ax.plot([f1, f2], [y, y], ls="-", lw=13, color=col, alpha=0.45,
                solid_capstyle="round")
        ax.text(np.sqrt(f1 * f2), y + 0.30, name, ha="center", fontsize=9.2,
                color=col, fontweight="bold")
        ax.text(f2 * 1.35, y, f"{p} · IL {il} · 크기 {size}", va="center",
                ha="left", fontsize=8.4, color="#444")

    ax.set_xscale("log")
    ax.set_xlim(8e-4, 900)
    ax.set_ylim(-0.7, len(techs) - 0.25)
    ax.set_yticks([])
    ax.set_xlabel("동작 주파수 (GHz)")
    ax.set_title("그림 M07-5  필터 기술의 적용 영역 (대략적 경향)")
    S.plain_log(ax, "x")
    ax.grid(axis="x", alpha=0.5, which="both")
    for s in ("left", "right", "top"):
        ax.spines[s].set_visible(False)
    S.save(fig, "M07", "tech_map")


if __name__ == "__main__":
    m06_cap_srf()
    m06_ind_srf()
    m06_q_bandwidth()
    f_ar, z_ar = m06_decoupling()
    m07_responses()
    m07_group_delay()
    spec = m07_spec_annotated()
    m07_order()
    m07_tech_map()

    print("\n[본문에 인용할 계산값]")
    esl = 0.5e-9
    for c, n in [(100e-9, "100 nF"), (10e-9, "10 nF"), (1e-9, "1 nF"),
                 (100e-12, "100 pF"), (10e-12, "10 pF")]:
        print(f"  {n:>7s} (ESL 0.5 nH) → SRF {srf(esl, c)/1e6:8.1f} MHz")
    for l, cp, n in [(100e-9, 0.30e-12, "100 nH"), (10e-9, 0.15e-12, "10 nH"),
                     (2.2e-9, 0.08e-12, "2.2 nH")]:
        print(f"  {n:>7s} (기생 C {cp*1e12:.2f} pF) → SRF {srf(l, cp)/1e9:6.2f} GHz")
    print(f"  필터 사양 예: -3 dB 대역 {spec['bw3']:.1f} MHz, "
          f"-40 dB 대역 {spec['bw40']:.1f} MHz, 형상계수 {spec['shape']:.2f}")
    print(f"  디커플링 반공진: {f_ar/1e6:.1f} MHz 에서 |Z| = {z_ar*1000:.1f} mΩ")
    for q in (5, 20, 100):
        print(f"  Q {q:>3d} → 2.4 GHz 에서 대역폭 {2.4e9/q/1e6:7.1f} MHz")
    print("완료")
