#!/usr/bin/env python3
"""
RF 커리큘럼 공용 회로 심볼 생성기
=================================

설계서 §8.3 "심볼 일관성" 규약을 이행한다.
모든 모듈의 회로도는 여기서 생성한 심볼만 사용하여, 18개 모듈에 걸쳐
같은 부품이 항상 같은 모양으로 그려지도록 보장한다.

실행:
    python3 scripts/gen_symbols.py

출력:
    assets/symbols/<name>.svg   개별 심볼
    assets/symbols/CATALOG.md   전체 카탈로그 (문서에서 골라 쓰기용)

설계 규약
---------
* 배경을 흰색으로 명시한다. GitHub 등에서 SVG는 <img>로 렌더되어 페이지의
  다크 모드 색을 상속하지 못하므로, 배경을 비워 두면 어두운 테마에서
  검은 선이 보이지 않는다.
* 선 색은 #1a1a1a 단색, 선 굵기는 STROKE 로 통일한다.
* 라벨 글꼴 크기와 위치도 통일한다.
* 단자(terminal)는 항상 좌우 중앙 높이에 오게 하여 심볼끼리 이어 붙일 때
  선이 어긋나지 않게 한다.
* **심볼 안에는 한글을 넣지 않는다.** SVG의 <text>는 *보는 사람의 컴퓨터에
  설치된 폰트*로 그려지므로, 한글 폰트가 없는 환경에서는 네모 상자(□□□)로
  깨진다. 실제로 초판에서 PLL 심볼의 "합성기"가 그렇게 깨지는 것을 확인했다.
  한글 설명은 심볼 바깥, 즉 마크다운 캡션에 쓴다. 캡션은 검색·복사·번역도
  되므로 접근성 면에서도 낫다.
  (Matplotlib으로 그리는 데이터 플롯은 사정이 다르다. 그쪽은 글자를 벡터
   경로로 변환해 저장하므로 한글을 써도 안전하다. scripts/rf_style.py 참조.)
"""

from pathlib import Path

# ---------------------------------------------------------------- 공통 규약
STROKE = 2.0            # 선 굵기
INK = "#1a1a1a"         # 선 색
ACCENT = "#c0392b"      # 강조(신호 흐름, 주석)
BG = "#ffffff"          # 배경
FONT = "font-family='DejaVu Sans, Helvetica, Arial, sans-serif'"

OUT = Path(__file__).resolve().parent.parent / "assets" / "symbols"


def svg(name, w, h, body, title):
    """SVG 문서 한 개를 문자열로 만든다."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img" aria-label="{title}">\n'
        f'  <title>{title}</title>\n'
        f'  <rect x="0" y="0" width="{w}" height="{h}" fill="{BG}"/>\n'
        f'  <g fill="none" stroke="{INK}" stroke-width="{STROKE}" '
        f'stroke-linecap="round" stroke-linejoin="round">\n{body}\n  </g>\n'
        f'</svg>\n'
    )


def line(x1, y1, x2, y2, **kw):
    extra = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return f'    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"{extra}/>'


def path(d, **kw):
    extra = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return f'    <path d="{d}"{extra}/>'


def rect(x, y, w, h, **kw):
    extra = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return f'    <rect x="{x}" y="{y}" width="{w}" height="{h}"{extra}/>'


def circle(cx, cy, r, **kw):
    extra = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return f'    <circle cx="{cx}" cy="{cy}" r="{r}"{extra}/>'


def text(x, y, s, size=11, anchor="middle", color=INK, weight="normal"):
    return (
        f'    <text x="{x}" y="{y}" {FONT} font-size="{size}" '
        f'text-anchor="{anchor}" fill="{color}" font-weight="{weight}" '
        f'stroke="none">{s}</text>'
    )


def leads(x1, x2, y, cx1, cx2):
    """좌우 리드선. (x1..cx1) 과 (cx2..x2)"""
    return [line(x1, y, cx1, y), line(cx2, y, x2, y)]


# ---------------------------------------------------------------- 심볼 정의
SYMBOLS = {}


def sym(name, title, group, w=110, h=60):
    """심볼 등록용 데코레이터."""
    def deco(fn):
        SYMBOLS[name] = dict(title=title, group=group, w=w, h=h, fn=fn)
        return fn
    return deco


# ---- 수동 소자 -------------------------------------------------------------
@sym("resistor", "저항 (Resistor)", "수동 소자")
def _resistor(w, h):
    y = h / 2
    b = [*leads(4, w - 4, y, 30, 80)]
    b.append(rect(30, y - 11, 50, 22))
    return b


@sym("capacitor", "커패시터 (Capacitor)", "수동 소자")
def _capacitor(w, h):
    y = h / 2
    b = [*leads(4, w - 4, y, 48, 62)]
    b += [line(48, y - 16, 48, y + 16), line(62, y - 16, 62, y + 16)]
    return b


@sym("inductor", "인덕터 (Inductor)", "수동 소자")
def _inductor(w, h):
    y = h / 2
    b = [*leads(4, w - 4, y, 30, 80)]
    d = f"M 30 {y}"
    for i in range(5):
        x0 = 30 + i * 10
        d += f" A 5 5 0 0 1 {x0 + 10} {y}"
    b.append(path(d))
    return b


@sym("ground", "접지 (Ground)", "수동 소자", w=70, h=56)
def _ground(w, h):
    cx = w / 2
    b = [line(cx, 6, cx, 26)]
    b += [line(cx - 18, 26, cx + 18, 26),
          line(cx - 11, 34, cx + 11, 34),
          line(cx - 4, 42, cx + 4, 42)]
    return b


@sym("termination_50", "50 Ω 종단기 (50 Ω Termination)", "수동 소자", w=100, h=76)
def _term(w, h):
    y = 26
    b = [line(4, y, 40, y), rect(40, y - 11, 34, 22)]
    b += [line(57, y + 11, 57, 44)]
    b += [line(57 - 14, 44, 57 + 14, 44),
          line(57 - 9, 50, 57 + 9, 50),
          line(57 - 4, 56, 57 + 4, 56)]
    b.append(text(57, 20, "50 Ω", size=10))
    return b


@sym("transmission_line", "전송선로 (Transmission Line)", "수동 소자", w=130, h=64)
def _tline(w, h):
    y = h / 2
    # 동축 전송선로: 바깥 도체 두 줄 + 안쪽 도체 한 줄
    b = [line(4, y, 26, y), line(w - 26, y, w - 4, y)]
    b += [line(26, y - 10, w - 26, y - 10), line(26, y + 10, w - 26, y + 10)]
    b += [line(26, y - 10, 26, y + 10), line(w - 26, y - 10, w - 26, y + 10)]
    b += [line(26, y, w - 26, y, stroke_width=1.2)]
    b.append(text(w / 2, y - 16, "Z₀, ℓ", size=10))
    return b


# ---- 신호원 ---------------------------------------------------------------
@sym("ac_source", "교류 신호원 (AC Source)", "신호원", w=100, h=76)
def _ac(w, h):
    cx, cy = w / 2, 34
    b = [circle(cx, cy, 18), line(4, cy, cx - 18, cy)]
    b.append(path(f"M {cx-10} {cy} q 5 -9 10 0 q 5 9 10 0"))
    b += [line(cx, cy + 18, cx, 56)]
    b += [line(cx - 12, 56, cx + 12, 56),
          line(cx - 7, 62, cx + 7, 62),
          line(cx - 3, 68, cx + 3, 68)]
    return b


@sym("signal_generator", "신호 발생기 (Signal Generator)", "계측 장비", w=140, h=80)
def _siggen(w, h):
    b = [rect(6, 10, w - 40, 58, rx=4)]
    b.append(rect(16, 20, 52, 26, rx=2))
    b.append(path("M 22 33 q 6 -10 12 0 q 6 10 12 0", stroke_width=1.6))
    b += [circle(84, 33, 7), circle(84, 56, 7)]
    b.append(text(38, 60, "SIG GEN", size=9))
    b += [line(w - 34, 39, w - 4, 39), circle(w - 34, 39, 4, fill=BG)]
    return b


# ---- 능동 소자 -------------------------------------------------------------
def _tri_amp(w, h, label, sub=None):
    y = h / 2
    b = [line(4, y, 28, y), line(w - 4, y, w - 24, y)]
    b.append(path(f"M 28 {y-22} L {w-24} {y} L 28 {y+22} Z"))
    b.append(text(28 + (w - 52) / 3, y + 4, label, size=12, weight="bold"))
    if sub:
        b.append(text(w / 2, h - 4, sub, size=9))
    return b


@sym("amplifier", "증폭기 (Amplifier)", "능동 소자", w=120, h=64)
def _amp(w, h):
    return _tri_amp(w, h, "")


@sym("lna", "저잡음 증폭기 (Low Noise Amplifier, LNA)", "능동 소자", w=126, h=72)
def _lna(w, h):
    return _tri_amp(w, h, "LNA")


@sym("pa", "전력 증폭기 (Power Amplifier, PA)", "능동 소자", w=126, h=72)
def _pa(w, h):
    return _tri_amp(w, h, "PA")


@sym("transistor_fet", "전계효과 트랜지스터 (FET)", "능동 소자", w=110, h=90)
def _fet(w, h):
    gx, cx = 18, 52
    b = [line(4, 45, gx, 45), line(gx, 45, cx - 8, 45)]
    b.append(line(cx - 8, 22, cx - 8, 68))          # 게이트 전극
    b.append(line(cx, 22, cx, 38))                  # 드레인 채널
    b.append(line(cx, 52, cx, 68))                  # 소스 채널
    b += [line(cx, 30, w - 20, 30), line(w - 20, 30, w - 20, 8)]
    b += [line(cx, 60, w - 20, 60), line(w - 20, 60, w - 20, 82)]
    b.append(text(w - 8, 12, "D", size=10))
    b.append(text(w - 8, 86, "S", size=10))
    b.append(text(8, 38, "G", size=10))
    return b


@sym("diode", "다이오드 (Diode)", "능동 소자")
def _diode(w, h):
    y = h / 2
    b = [*leads(4, w - 4, y, 42, 68)]
    b.append(path(f"M 42 {y-14} L 68 {y} L 42 {y+14} Z", fill=INK))
    b.append(line(68, y - 14, 68, y + 14))
    return b


# ---- RF 블록 ---------------------------------------------------------------
@sym("mixer", "믹서 (Mixer)", "RF 블록", w=130, h=110)
def _mixer(w, h):
    cx, cy, r = 62, 50, 24
    b = [circle(cx, cy, r)]
    k = r * 0.707
    b += [line(cx - k, cy - k, cx + k, cy + k), line(cx - k, cy + k, cx + k, cy - k)]
    b += [line(4, cy, cx - r, cy), line(cx + r, cy, w - 4, cy)]
    b += [line(cx, cy + r, cx, h - 18)]
    b.append(text(20, cy - 8, "RF", size=10))
    b.append(text(w - 18, cy - 8, "IF", size=10))
    b.append(text(cx + 16, h - 6, "LO", size=10))
    return b


def _filter_box(w, h, curve):
    y = h / 2
    b = [line(4, y, 26, y), line(w - 26, y, w - 4, y)]
    b.append(rect(26, y - 22, w - 52, 44, rx=3))
    b.append(path(curve, stroke_width=1.8))
    return b


@sym("filter_lpf", "저역 통과 필터 (Low Pass Filter, LPF)", "RF 블록", w=120, h=70)
def _lpf(w, h):
    return _filter_box(w, h, "M 38 26 L 62 26 Q 72 26 74 44 L 82 44")


@sym("filter_hpf", "고역 통과 필터 (High Pass Filter, HPF)", "RF 블록", w=120, h=70)
def _hpf(w, h):
    return _filter_box(w, h, "M 38 44 L 46 44 Q 54 44 58 26 L 82 26")


@sym("filter_bpf", "대역 통과 필터 (Band Pass Filter, BPF)", "RF 블록", w=120, h=70)
def _bpf(w, h):
    return _filter_box(w, h, "M 38 44 L 46 44 Q 52 44 56 26 L 64 26 Q 70 26 74 44 L 82 44")


@sym("attenuator", "감쇠기 (Attenuator)", "RF 블록", w=120, h=66)
def _atten(w, h):
    y = h / 2
    b = [line(4, y, 30, y), line(w - 30, y, w - 4, y)]
    b.append(rect(30, y - 18, w - 60, 36, rx=3))
    b.append(text(w / 2, y + 5, "ATT", size=11))
    return b


@sym("switch_spdt", "단극쌍투 스위치 (SPDT Switch)", "RF 블록", w=120, h=90)
def _spdt(w, h):
    b = [line(4, 45, 40, 45), circle(42, 45, 3.5, fill=INK)]
    b.append(line(44, 44, 82, 22))
    b += [circle(86, 20, 3.5, fill=INK), circle(86, 70, 3.5, fill=INK)]
    b += [line(88, 20, w - 4, 20), line(88, 70, w - 4, 70)]
    return b


@sym("circulator", "서큘레이터 (Circulator)", "RF 블록", w=120, h=118)
def _circ(w, h):
    cx, cy, r = 58, 52, 28
    b = [circle(cx, cy, r)]
    b.append(path(f"M {cx-13} {cy+8} A 15 15 0 1 1 {cx+13} {cy+8}",
                  stroke_width=1.6, marker_end="none"))
    b.append(path(f"M {cx+9} {cy+3} L {cx+13} {cy+9} L {cx+17} {cy+1}",
                  stroke_width=1.6))
    b += [line(4, cy, cx - r, cy), line(cx + r, cy, w - 4, cy),
          line(cx, cy + r, cx, h - 16)]
    b.append(text(14, cy - 8, "1", size=10))
    b.append(text(w - 14, cy - 8, "2", size=10))
    b.append(text(cx + 12, h - 4, "3", size=10))
    return b


@sym("isolator", "아이솔레이터 (Isolator)", "RF 블록", w=124, h=70)
def _iso(w, h):
    y = h / 2
    b = [line(4, y, 30, y), line(w - 30, y, w - 4, y)]
    b.append(rect(30, y - 20, w - 60, 40, rx=3))
    b.append(path(f"M {w/2-14} {y} L {w/2+10} {y}", stroke_width=1.8))
    b.append(path(f"M {w/2+2} {y-6} L {w/2+10} {y} L {w/2+2} {y+6}", stroke_width=1.8))
    return b


@sym("coupler", "방향성 결합기 (Directional Coupler)", "RF 블록", w=150, h=100)
def _coupler(w, h):
    b = [line(10, 30, w - 10, 30), line(10, 66, w - 10, 66)]
    b.append(line(46, 30, 46, 66, stroke_dasharray="4 3", stroke_width=1.4))
    b.append(line(104, 30, 104, 66, stroke_dasharray="4 3", stroke_width=1.4))
    b.append(text(16, 22, "IN", size=9, anchor="start"))
    b.append(text(w - 16, 22, "OUT", size=9, anchor="end"))
    b.append(text(16, 84, "ISO", size=9, anchor="start"))
    b.append(text(w - 16, 84, "CPL", size=9, anchor="end"))
    return b


@sym("power_divider", "전력 분배기 (Power Divider)", "RF 블록", w=140, h=110)
def _divider(w, h):
    b = [line(4, 55, 34, 55), rect(34, 24, 46, 62, rx=4)]
    b += [line(80, 40, w - 4, 40), line(80, 70, w - 4, 70)]
    b.append(text(57, 59, "÷", size=16))
    return b


@sym("oscillator", "발진기 (Oscillator)", "RF 블록", w=110, h=76)
def _osc(w, h):
    cx, cy = 40, 38
    b = [circle(cx, cy, 22)]
    b.append(path(f"M {cx-12} {cy} q 6 -11 12 0 q 6 11 12 0", stroke_width=1.6))
    b.append(line(cx + 22, cy, w - 4, cy))
    b.append(text(cx, h - 4, "OSC", size=9))
    return b


@sym("pll", "위상동기루프 (Phase-Locked Loop, PLL)", "RF 블록", w=150, h=80)
def _pll(w, h):
    b = [rect(20, 14, w - 40, 52, rx=4)]
    b += [line(4, 40, 20, 40), line(w - 20, 40, w - 4, 40)]
    # 한글 금지 규약(모듈 도크스트링 참조) — "합성기"는 마크다운 캡션에 쓴다.
    b.append(text(w / 2, 45, "PLL", size=13, weight="bold"))
    return b


@sym("adc", "아날로그-디지털 변환기 (ADC)", "RF 블록", w=140, h=80)
def _adc(w, h):
    b = [path("M 24 14 L 116 14 L 100 66 L 24 66 Z")]
    b += [line(4, 40, 24, 40)]
    b += [line(116 - 12, 40, w - 4, 40)]
    b.append(text(66, 45, "ADC", size=12, weight="bold"))
    return b


@sym("dac", "디지털-아날로그 변환기 (DAC)", "RF 블록", w=140, h=80)
def _dac(w, h):
    b = [path("M 24 14 L 116 14 L 100 66 L 24 66 Z")]
    b += [line(4, 40, 24, 40), line(104, 40, w - 4, 40)]
    b.append(text(66, 45, "DAC", size=12, weight="bold"))
    return b


@sym("antenna", "안테나 (Antenna)", "RF 블록", w=100, h=90)
def _antenna(w, h):
    cx = w / 2
    b = [line(cx, 82, cx, 46)]
    b += [line(cx, 46, cx - 24, 12), line(cx, 46, cx + 24, 12)]
    b.append(path(f"M {cx-13} {32} A 18 18 0 0 0 {cx+13} {32}", stroke_width=1.3))
    return b


@sym("connector_sma", "SMA 커넥터 (SMA Connector)", "기타", w=110, h=64)
def _sma(w, h):
    y = h / 2
    b = [line(4, y, 34, y)]
    b.append(rect(34, y - 16, 30, 32))
    b.append(path(f"M 64 {y-10} L 88 {y-10} M 64 {y+10} L 88 {y+10}"))
    b.append(line(64, y, w - 4, y))
    for x in range(68, 88, 6):
        b.append(line(x, y - 10, x, y + 10, stroke_width=1))
    return b


# ---- 계측 장비 -------------------------------------------------------------
def _instrument(w, h, label, screen):
    b = [rect(6, 8, w - 12, h - 16, rx=5)]
    b.append(rect(16, 18, w - 62, h - 44, rx=2))
    b += screen
    b.append(circle(w - 28, 26, 7))
    b.append(circle(w - 28, h - 30, 7))
    b.append(text((w - 46) / 2 + 16, h - 14, label, size=9))
    return b


@sym("vna", "벡터 회로망 분석기 (VNA)", "계측 장비", w=160, h=100)
def _vna(w, h):
    screen = [path("M 24 52 Q 44 52 54 30 Q 64 52 84 52", stroke_width=1.5,
                   stroke=ACCENT)]
    b = _instrument(w, h, "VNA", screen)
    b += [circle(28, h - 6, 5, fill=BG), circle(64, h - 6, 5, fill=BG)]
    b.append(text(28, h - 2, "1", size=8))
    b.append(text(64, h - 2, "2", size=8))
    return b


@sym("spectrum_analyzer", "스펙트럼 분석기 (Spectrum Analyzer, SA)", "계측 장비",
     w=160, h=100)
def _sa(w, h):
    screen = [line(24, 56, 100, 56, stroke_width=1.2),
              line(40, 56, 40, 26, stroke_width=1.5, stroke=ACCENT),
              line(58, 56, 58, 40, stroke_width=1.5, stroke=ACCENT),
              line(76, 56, 76, 48, stroke_width=1.5, stroke=ACCENT)]
    b = _instrument(w, h, "SPECTRUM ANALYZER", screen)
    b.append(circle(40, h - 6, 5, fill=BG))
    return b


@sym("power_meter", "전력계 (Power Meter)", "계측 장비", w=150, h=94)
def _pm(w, h):
    screen = [text(56, 46, "-12.3", size=15), text(56, 60, "dBm", size=9)]
    b = _instrument(w, h, "POWER METER", screen)
    b.append(circle(40, h - 6, 5, fill=BG))
    return b


@sym("noise_source", "잡음원 (Noise Source)", "계측 장비", w=136, h=70)
def _ns(w, h):
    y = h / 2
    b = [rect(14, y - 22, 84, 44, rx=4)]
    b.append(path("M 24 42 L 30 28 L 36 46 L 42 26 L 48 44 L 54 30 L 60 42",
                  stroke_width=1.4, stroke=ACCENT))
    b.append(text(80, y + 4, "ENR", size=9))
    b.append(line(98, y, w - 4, y))
    return b


@sym("dut", "피시험 소자 (Device Under Test, DUT)", "기타", w=140, h=76)
def _dut(w, h):
    y = h / 2
    b = [line(4, y, 28, y), line(w - 28, y, w - 4, y)]
    b.append(rect(28, y - 24, w - 56, 48, rx=4, stroke_dasharray="6 4"))
    b.append(text(w / 2, y + 5, "DUT", size=13, weight="bold"))
    return b


# ---------------------------------------------------------------- 생성 실행
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    groups = {}
    for name, meta in SYMBOLS.items():
        w, h = meta["w"], meta["h"]
        body = "\n".join(meta["fn"](w, h))
        (OUT / f"{name}.svg").write_text(svg(name, w, h, body, meta["title"]),
                                         encoding="utf-8")
        groups.setdefault(meta["group"], []).append((name, meta["title"]))

    lines = [
        "# 공용 회로 심볼 카탈로그",
        "",
        "> 이 파일은 `scripts/gen_symbols.py`가 자동 생성합니다. **직접 편집하지 마십시오.**",
        "> 심볼을 추가·수정하려면 생성기를 고치고 다시 실행하십시오.",
        "",
        "설계서 §8.3의 **심볼 일관성 규약**에 따라, 커리큘럼 전 모듈의 회로도는",
        "여기 있는 심볼만 사용합니다. 같은 부품이 모듈마다 다른 모양으로 그려지면",
        "초심자는 그것을 다른 부품으로 오해하기 때문입니다.",
        "",
        "## 사용법",
        "",
        "```markdown",
        "![저항](../assets/symbols/resistor.svg)",
        "```",
        "",
        f"현재 심볼 수: **{len(SYMBOLS)}개**",
        "",
    ]
    for g in ["수동 소자", "신호원", "능동 소자", "RF 블록", "계측 장비", "기타"]:
        if g not in groups:
            continue
        lines += [f"## {g}", "", "| 심볼 | 이름 | 파일 |", "|---|---|---|"]
        for name, title in sorted(groups[g]):
            lines.append(f"| ![{title}](./{name}.svg) | {title} | `{name}.svg` |")
        lines.append("")

    (OUT / "CATALOG.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"생성 완료: {len(SYMBOLS)}개 심볼 → {OUT}")
    for g, items in groups.items():
        print(f"  {g}: {len(items)}개")


if __name__ == "__main__":
    main()
