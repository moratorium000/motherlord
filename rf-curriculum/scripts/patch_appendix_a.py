#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""부록 A 에 빠져 있던 축약어를 채운다.

17단계 정합성 검토에서 `scripts/check_abbr.py` 가 본문에는 쓰이는데 부록 A
마스터 목록에는 없는 축약어를 찾아냈다. 지침 2("축약어는 반드시 뜻을
병기")를 지키려면 독자가 어떤 축약어를 만나든 찾아볼 한 곳이 있어야 한다.

각 항목의 "정의 모듈" 칸은 그 축약어가 처음 쓰이는 문서를 실제로 검색해
정했다. 이 스크립트는 알파벳 구간을 찾아 가나다순 자리에 행을 끼워 넣는다.
이미 있는 약어는 건너뛰므로 여러 번 돌려도 안전하다.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "03_부록" / "A_축약어_마스터목록.md"

# (구간 제목, 약어, 영문 원어, 한글, 한 줄 뜻, 정의 모듈)
ROWS: list[tuple[str, str, str, str, str, str]] = [
    ("A", "ABCD", "ABCD Parameters", "ABCD 파라미터",
     "2포트를 전압·전류로 기술하는 행렬. 종속 연결이 곱셈이 된다", "M03"),
    ("A", "AWGN", "Additive White Gaussian Noise", "가산 백색 가우스 잡음",
     "모든 주파수에 고르게 퍼진 이론적 잡음 모형. 링크 해석의 기본 가정", "M13"),

    ("B", "BPSK", "Binary Phase Shift Keying", "2진 위상 편이 변조",
     "위상 두 개(0°, 180°)만 쓰는 가장 단순한 디지털 변조", "M13"),

    ("C", "C0G", "Class 1 Ceramic Dielectric (= NP0)", "C0G 유전체",
     "온도·전압에 거의 변하지 않는 세라믹 커패시터 등급. RF 정합용", "M06"),
    ("C", "CATV", "Cable Television", "케이블 텔레비전",
     "동축 케이블 방송망. 50 Ω이 아니라 75 Ω 계를 쓴다", "M02"),
    ("C", "CMOS", "Complementary Metal-Oxide-Semiconductor",
     "상보형 금속 산화막 반도체",
     "디지털·아날로그를 한 칩에 넣는 대표 반도체 공정", "M09"),
    ("C", "CST", "CST Studio Suite", "(상용 전자기 해석 소프트웨어 이름)",
     "3차원 전자기장 시뮬레이터. 안테나·구조물 해석에 쓴다", "부록 D"),
    ("C", "CTIA", "Cellular Telecommunications and Internet Association",
     "(미국 이동통신 산업 협회)",
     "단말 무선 성능(OTA) 시험 규격을 만드는 단체", "M10"),

    ("D", "DIN", "Deutsches Institut für Normung", "독일 표준화 기구",
     "7/16 DIN 커넥터처럼 규격 이름 앞에 붙는다", "M04"),
    ("D", "DRO", "Dielectric Resonator Oscillator", "유전체 공진 발진기",
     "유전체 공진기로 주파수를 정하는 발진기. 위상잡음이 낮다", "M09"),
    ("D", "DSP", "Digital Signal Processing", "디지털 신호 처리",
     "표본으로 바꾼 신호를 계산으로 거르고 복조하는 단계", "M11"),

    ("E", "EHF", "Extremely High Frequency", "초고주파 (30~300 GHz)",
     "ITU 대역 구분의 하나. 밀리미터파 영역", "M00"),
    ("E", "EM", "Electromagnetic", "전자기",
     "EM 시뮬레이션 = 맥스웰 방정식을 직접 푸는 구조 해석", "M17"),
    ("E", "ET", "Envelope Tracking", "포락선 추종",
     "신호 세기에 맞춰 전력 증폭기 전원을 실시간으로 낮춰 효율을 올리는 기법",
     "M08"),

    ("F", "FDTD", "Finite-Difference Time-Domain", "시간영역 유한차분법",
     "전자기장을 시간 격자로 푸는 수치 해석 방법", "M17"),
    ("F", "FM", "Frequency Modulation", "주파수 변조",
     "정보를 주파수 변화에 싣는 아날로그 변조. 라디오 방송에 쓴다", "M00"),

    ("G", "GND", "Ground", "접지",
     "회로도·보드에서 기준 전위. RF 에서는 '기준면'이자 '귀환 경로'", "M17"),

    ("H – I", "HFSS", "High Frequency Structure Simulator",
     "(상용 전자기 해석 소프트웨어 이름)",
     "Ansys의 3차원 전자기장 시뮬레이터", "부록 D"),
    ("H – I", "HPBW", "Half-Power Beamwidth", "반전력 빔폭",
     "방사 패턴에서 최대값보다 3 dB 낮아지는 두 각도 사이의 폭", "M10"),
    ("H – I", "HVLP", "Hyper Very Low Profile (copper foil)",
     "초저조도 동박",
     "표면이 아주 매끄러운 동박. 고주파 도체 손실을 줄인다", "M17"),
    ("H – I", "IC", "Integrated Circuit", "집적 회로",
     "여러 소자를 한 칩에 넣은 부품", "M02"),
    ("H – I", "IFBW", "IF Bandwidth", "중간주파 대역폭",
     "VNA 수신부의 필터 폭. 좁힐수록 잡음은 줄고 측정은 느려진다", "M05"),
    ("H – I", "IM2 / IM5", "2nd / 5th-order Intermodulation",
     "2차 · 5차 상호변조",
     "IM3 말고도 생기는 상호변조 성분. 차수마다 나타나는 위치가 다르다",
     "M08"),
    ("H – I", "IP2 / IP3", "2nd / 3rd-order Intercept Point",
     "2차 · 3차 교차점",
     "입력 기준이면 IIP2·IIP3, 출력 기준이면 OIP2·OIP3", "M08"),
    ("H – I", "IRR", "Image Rejection Ratio", "이미지 억압비",
     "원하는 신호 대비 이미지 성분이 얼마나 작은가 (dB)", "M11"),

    ("J – L", "LAN", "Local Area Network", "근거리 통신망",
     "장비 자동화에서 LXI 장비를 잇는 이더넷 연결", "M16"),
    ("J – L", "LC", "Inductor-Capacitor", "인덕터-커패시터",
     "L 과 C 만으로 만든 회로. LC 정합, LC 필터", "M02"),
    ("J – L", "LDO", "Low-Dropout Regulator", "저전압강하 레귤레이터",
     "입출력 전압 차가 작아도 동작하는 선형 전원. 잡음이 낮다", "M16"),
    ("J – L", "LEO", "Low Earth Orbit", "저궤도",
     "고도 수백 km 위성 궤도. 링크 버짓 예제에 쓴다", "M10"),
    ("J – L", "LISN", "Line Impedance Stabilization Network",
     "선로 임피던스 안정화 회로망",
     "전도 방사 시험에서 전원선 임피던스를 규격값으로 고정하는 장치", "M17"),
    ("J – L", "LOS", "Line of Sight", "가시선",
     "송수신 사이에 가로막는 것이 없는 경로", "M10"),
    ("J – L", "LTCC", "Low Temperature Co-fired Ceramic",
     "저온 동시소성 세라믹",
     "세라믹 층을 겹쳐 구운 소형 필터·정합 부품 공정", "캡스톤"),

    ("M – N", "MCU", "Microcontroller Unit", "마이크로컨트롤러",
     "보드를 제어하는 작은 프로세서. 클록 하모닉의 발생원이기도 하다", "M17"),
    ("M – N", "MIMO", "Multiple-Input Multiple-Output", "다중 입출력",
     "안테나를 여러 개 써서 같은 대역에 여러 신호를 동시에 보내는 방식",
     "M10"),
    ("M – N", "MSPS", "Mega-Samples Per Second", "초당 백만 표본",
     "ADC·DAC 의 표본화 속도 단위", "M11"),
    ("M – N", "NR", "New Radio", "뉴 라디오 (5G 무선 규격)",
     "3GPP 가 정한 5G 무선접속 규격. FR1·FR2 대역을 쓴다", "M11"),

    ("O – P", "OCXO", "Oven-Controlled Crystal Oscillator",
     "항온조 수정 발진기",
     "수정을 항온조에 넣어 온도 변화를 없앤 기준 발진기. 가장 안정", "M09"),
    ("O – P", "OSL", "Open-Short-Load", "개방-단락-부하",
     "1포트 VNA 교정에 쓰는 표준 세 개. SOL 과 같은 말", "M10"),
    ("O – P", "PER", "Packet Error Rate", "패킷 오류율",
     "받은 패킷 중 복구에 실패한 비율. 규격의 감도 판정 기준", "M12"),
    ("O – P", "PSD", "Power Spectral Density", "전력 스펙트럼 밀도",
     "주파수 1 Hz 당 전력. 단위는 보통 dBm/Hz", "M13"),

    ("Q – R", "RC", "Resistor-Capacitor", "저항-커패시터",
     "R 과 C 로 만든 회로. 증폭기 저주파 안정화에 쓴다", "M08"),
    ("Q – R", "RLC", "Resistor-Inductor-Capacitor", "저항-인덕터-커패시터",
     "공진 회로의 기본 3소자 모형", "M16"),
    ("Q – R", "RO4000 / RO4350B", "Rogers RO4000 Series",
     "(고주파 기판 재료 이름)",
     "FR-4 보다 손실이 낮고 Dk 산포가 작은 기판. RO4350B 는 Dk 3.66", "M02"),
    ("Q – R", "RRC", "Root Raised Cosine", "제곱근 상승 코사인",
     "송수신에 나눠 거는 대역 제한 필터. 심볼 간 간섭을 없앤다", "M15"),
    ("Q – R", "RTF", "Reverse Treated Foil", "역처리 동박",
     "거친 면을 바깥으로 돌린 동박. 조도와 접착력의 절충", "M17"),
    ("Q – R", "RTL-SDR", "Realtek RTL2832U-based SDR",
     "(저가 소프트웨어 정의 무선 수신기)",
     "TV 튜너 칩을 쓴 2만 원대 수신기. T0 등급 실습 장비", "M11"),
    ("Q – R", "RX / TX", "Receive / Transmit", "수신 / 송신",
     "블록도에서 수신 경로와 송신 경로를 가리키는 표시", "M00"),

    ("S", "SHF", "Super High Frequency", "초고주파 (3~30 GHz)",
     "ITU 대역 구분의 하나. Wi-Fi·위성이 여기 든다", "M00"),
    ("S", "SHORT · OPEN · LOAD · THRU · LINE · REFLECT",
     "(calibration standard names)",
     "단락 · 개방 · 부하 · 관통 · 선로 · 반사 표준",
     "VNA 교정에 쓰는 기준 소자들의 이름. SOLT 는 앞 네 개, "
     "TRL 은 관통·반사·선로를 쓴다", "M14"),
    ("S", "SNDR", "Signal-to-Noise and Distortion Ratio",
     "신호 대 잡음·왜곡비",
     "잡음뿐 아니라 하모닉까지 포함해 계산한 SNR. ENOB 의 근거", "M11"),
    ("S", "SOL", "Short-Open-Load", "단락-개방-부하",
     "1포트 교정 표준 세 개. OSL 과 같은 말", "M14"),

    ("T – Z", "TEM", "Transverse Electromagnetic", "횡전자기파",
     "전기장·자기장이 모두 진행 방향에 수직인 모드. 동축선의 기본 모드",
     "M02"),
    ("T – Z", "TNC", "Threaded Neill-Concelman", "(나사식 커넥터 계열)",
     "BNC 를 나사식으로 바꾼 커넥터. 진동에 강하다", "M04"),
    ("T – Z", "TS", "Technical Specification", "기술 규격서",
     "3GPP 문서 종류. TS 는 규격, TR 은 기술 보고서", "M13"),
    ("T – Z", "UHF", "Ultra High Frequency", "극초단파 (300 MHz~3 GHz)",
     "ITU 대역 구분의 하나. 셀룰러 저대역이 여기 든다", "M00"),
    ("T – Z", "USB", "Universal Serial Bus", "범용 직렬 버스",
     "장비 제어·데이터 내보내기에 쓰는 연결. VISA 가 지원한다", "M03"),
    ("T – Z", "V_DD", "Drain Supply Voltage", "드레인 공급 전압",
     "전계효과 트랜지스터의 드레인에 거는 직류 전원", "M08"),
    ("T – Z", "VGA", "Variable Gain Amplifier", "가변 이득 증폭기",
     "제어 전압으로 이득을 바꾸는 증폭기. AGC 의 실행부", "캡스톤"),
    ("T – Z", "VHF", "Very High Frequency", "초단파 (30~300 MHz)",
     "ITU 대역 구분의 하나. FM 방송이 여기 든다", "M00"),
    ("T – Z", "VLP", "Very Low Profile (copper foil)", "저조도 동박",
     "표면 거칠기를 낮춘 동박. HVLP 보다는 거칠다", "M17"),
    ("T – Z", "VRM", "Voltage Regulator Module", "전압 조정 모듈",
     "보드에 전원을 공급하는 스위칭 레귤레이터. PDN 의 출발점", "M17"),
    ("T – Z", "X7R / Y5V", "Class 2 Ceramic Dielectric",
     "X7R · Y5V 유전체",
     "용량은 크지만 온도·직류 전압에 따라 값이 크게 변하는 등급. "
     "RF 정합에는 쓰지 않는다", "M06"),
    ("T – Z", "XO", "Crystal Oscillator", "수정 발진기",
     "온도 보상이 없는 기본 수정 발진기. TCXO·OCXO 의 출발점", "M09"),

    # ── 심화 과정(B01–B12) 설계서에서 새로 쓰이는 축약어 ──────────────
    # "정의 모듈" 은 아직 집필 전인 심화 모듈을 가리킨다. 앞을 가리키는
    # 참조지만, 설계서를 읽는 사람에게는 지금 필요한 값이다.
    ("A", "AFR", "Automatic Fixture Removal", "자동 픽스처 제거",
     "2x-Thru 쿠폰으로 픽스처를 반으로 갈라 빼내는 표준화된 방법", "심화 B03"),
    ("A", "ATE", "Automatic Test Equipment", "자동 시험 장비",
     "양산 라인에서 초 단위로 걸러 내는 시험기. 벤치와 목적이 다르다", "심화 B12"),

    ("C", "CMYK", "Cyan-Magenta-Yellow-Key(black)", "인쇄 4원색",
     "인쇄용 색 지정 방식. 화면의 RGB 와 다르다", "인쇄"),

    ("D", "DDJ", "Data-Dependent Jitter", "데이터 의존 지터",
     "앞선 비트 패턴 때문에 생기는 지터. 결정성 지터의 한 갈래", "심화 B02"),
    ("D", "DJ", "Deterministic Jitter", "결정성 지터",
     "크기가 한정된 지터. 무작위 지터와 달리 최대값이 있다", "심화 B02"),

    ("F", "FA", "Failure Analysis", "실패 분석",
     "떨어진 물건이 왜 떨어졌는지 파고 들어가는 절차", "심화 B12"),

    ("G", "GRR / Gage R&R", "Gage Repeatability and Reproducibility",
     "게이지 반복성·재현성",
     "측정 시스템 자체가 만드는 산포. %GRR 10 % 미만이면 양호", "심화 B11"),

    ("H – I", "HALT", "Highly Accelerated Life Test", "고가속 수명 시험",
     "규격보다 가혹한 조건으로 약한 곳을 빨리 드러내는 시험", "심화 B08"),

    ("M – N", "MSA", "Measurement System Analysis", "측정 시스템 분석",
     "측정값의 산포 중 측정계 몫이 얼마인지 가려내는 방법론", "심화 B11"),
    ("M – N", "NPR", "Noise Power Ratio", "잡음 전력비",
     "광대역 신호에 노치를 파고, 비선형이 그 노치를 얼마나 메우는지 보는 시험",
     "심화 B04"),
    ("M – N", "ndc", "number of distinct categories", "구별 범주 수",
     "측정계가 나눌 수 있는 등급의 수. 5 이상이어야 쓸 만하다", "심화 B11"),

    ("O – P", "PJ", "Periodic Jitter", "주기성 지터",
     "전원·클럭 같은 주기적 원인이 만드는 지터", "심화 B02"),
    ("O – P", "PM", "Phase Modulation", "위상 변조",
     "위상잡음 측정에서 AM(진폭) 성분과 갈라 보는 쪽", "심화 B06"),

    ("Q – R", "RJ", "Random Jitter", "무작위 지터",
     "가우스 분포라 최대값이 없다. 오류율을 낮출수록 커진다", "심화 B02"),
    ("Q – R", "Rn", "Equivalent Noise Resistance", "등가 잡음저항",
     "소스 임피던스가 최적점에서 벗어날 때 NF 가 얼마나 빨리 나빠지는가",
     "심화 B05"),

    ("S", "SOA", "Safe Operating Area", "안전 동작 영역",
     "전압·전류·시간의 조합 중 부품이 견디는 범위", "심화 B08"),

    ("T – Z", "TIS", "Total Isotropic Sensitivity", "총등방감도",
     "모든 방향에서 받은 감도를 구면 평균한 값. 측정에 오래 걸린다", "심화 B09"),
    ("T – Z", "TRP", "Total Radiated Power", "총방사전력",
     "모든 방향으로 나간 전력을 구면 적분한 값", "심화 B09"),
    # ── B01·B02 (심화 1~2단계) 에서 새로 쓰이는 축약어 ────────────────
    ("D", "DCD", "Duty Cycle Distortion", "듀티비 왜곡",
     "1 과 0 의 폭이 달라 생기는 결정성 지터", "심화 B02"),

    ("G", "GS/s", "Giga-Samples per second", "초당 십억 표본",
     "오실로스코프의 표본화 속도 단위. 대역폭과는 다른 사양이다", "심화 B02"),

    ("H – I", "ISI", "Inter-Symbol Interference", "부호 간 간섭",
     "채널 대역이 좁아 앞 심볼이 다음 심볼에 남는 현상", "M13"),

    ("S", "SPI", "Serial Peripheral Interface", "직렬 주변장치 인터페이스",
     "RF 모듈의 레지스터를 읽고 쓰는 데 흔히 쓰는 4선 버스", "심화 B02"),

    ("T – Z", "TJ", "Total Jitter", "총 지터",
     "DJ + 2·Q(BER)·RJ. 오류율을 정해야 값이 정해진다", "심화 B02"),
    ("T – Z", "UI", "Unit Interval", "단위 구간",
     "한 비트가 차지하는 시간. 10 Gb/s 면 100 ps", "심화 B02"),
    # ── B03 (다포트·차동과 픽스처) ────────────────────────────────────
    ("M – N", "NZC", "Non-impedance-Corrected", "임피던스 보정 없음",
     "IEEE 370 의 2x-Thru 디임베딩 중 임피던스 프로파일을 살리지 않는 쪽",
     "심화 B03"),

    ("T – Z", "ZC", "Impedance-Corrected", "임피던스 보정",
     "IEEE 370 의 2x-Thru 디임베딩 중 임피던스 프로파일까지 살리는 쪽",
     "심화 B03"),
    # B04 (심화 4단계) 에서 새로 들어온 것
    ("Q – R", "QB", "Quiescent Bias", "정지 바이어스점",
     "펄스 측정에서 펄스와 펄스 사이에 소자가 머무는 동작점. 트랩·온도 상태를 정한다",
     "B04"),

    ("T – Z", "VSA", "Vector Signal Analyzer", "벡터 신호 분석기",
     "신호의 크기와 위상을 함께 캡처해 성상도·EVM·AM-PM 을 뽑는 분석기", "B04"),
    ("T – Z", "VSG", "Vector Signal Generator", "벡터 신호 발생기",
     "규격 변조 파형을 만들어 내보내는 신호원. 대신호 시험의 입력을 담당한다",
     "B04"),

    # B05 · B06 (심화 5단계) 에서 새로 들어온 것
    ("A", "ADEV", "Allan Deviation", "앨런 편차",
     "평균 시간 τ 에 따른 주파수 안정도. 표준편차와 달리 표류가 섞여도 수렴한다",
     "B06"),

    ("Q – R", "PSRR", "Power Supply Rejection Ratio", "전원 잡음 제거비",
     "전원의 리플이 출력으로 얼마나 덜 새는가. 나쁘면 전원 주파수가 스퍼로 선다",
     "B06"),

    # B07 · B08 (심화 6단계) 에서 새로 들어온 것
    ("C", "CISPR", "Comité International Spécial des Perturbations Radioélectriques",
     "국제 무선장해 특별위원회",
     "전자파 장해 시험 규격을 만드는 국제 기구. CISPR 11·22·32 등", "M17"),

    ("H – I", "HEMT", "High Electron Mobility Transistor",
     "고전자이동도 트랜지스터",
     "이종접합으로 전자 이동도를 높인 소자. GaN·GaAs RF 전력소자의 주류", "M08"),

    ("S", "SE", "Shielding Effectiveness", "차폐 효과",
     "차폐가 있을 때와 없을 때의 전계 비. 구멍의 길이가 사실상 이것을 정한다",
     "B07"),
    ("S", "SSC", "Spread Spectrum Clocking", "스프레드 스펙트럼 클럭",
     "클럭 주파수를 조금씩 흔들어 하모닉 봉우리를 퍼뜨리는 기법. "
     "총 에너지는 그대로다", "B07"),

    # B09 · B10 (심화 7단계) 에서 새로 들어온 것
    ("B", "BLE", "Bluetooth Low Energy", "저전력 블루투스",
     "2.4 GHz 근거리 무선 규격. 디센스 시험에서 흔한 공존 상대다", "B10"),

    ("D", "DDR", "Double Data Rate (SDRAM)", "양단 구동 메모리 인터페이스",
     "클럭의 오르내림 양쪽에서 데이터를 실어 나르는 메모리 버스. "
     "하모닉이 넓게 퍼져 디센스의 단골 발생원이다", "B10"),

    ("E", "EIS", "Effective Isotropic Sensitivity", "유효 등방 감도",
     "한 방향에서 규격 오류율을 겨우 맞추는 입사 전력. TIS 는 이것의 구면 평균",
     "B09"),

    ("G", "GNSS", "Global Navigation Satellite System", "전 지구 위성 항법 시스템",
     "GPS·갈릴레오·베이더우를 아우르는 이름. 수신 전력이 낮아 디센스에 가장 약하다",
     "B10"),

    ("H – I", "IM", "Intermodulation", "상호변조",
     "둘 이상의 신호가 비선형을 지나며 m·f1 ± n·f2 자리에 만드는 새 성분", "M08"),

    ("J – L", "JTAG", "Joint Test Action Group", "(경계 주사 디버그 인터페이스)",
     "칩·보드를 디버그하는 직렬 인터페이스. 켜 두면 그 자체가 간섭원이 된다",
     "B10"),

    ("M – N", "MIPI", "Mobile Industry Processor Interface",
     "모바일 산업 프로세서 인터페이스",
     "카메라·디스플레이를 잇는 고속 직렬 규격. 하모닉이 수신 대역을 자주 친다",
     "B10"),

    ("Q – R", "RSSI", "Received Signal Strength Indicator", "수신 신호 세기 표시",
     "수신기가 스스로 보고하는 입력 세기. 감도 판정의 보조 지표", "B09"),

]


def sort_key(abbr: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", abbr).upper()


def main() -> int:
    text = PATH.read_text(encoding="utf-8")

    existing = set()
    for m in re.finditer(r"^\|\s*([^|]+?)\s*\|", text, re.M):
        for tok in re.split(r"[/·]", m.group(1)):
            existing.add(sort_key(tok))

    added = 0
    for sec, abbr, eng, kor, gloss, mod in ROWS:
        if sort_key(abbr.split("/")[0].split("·")[0]) in existing:
            print(f"  건너뜀(이미 있음): {abbr}")
            continue
        row = f"| {abbr} | {eng} | {kor} | {gloss} | {mod} |"

        # 구간의 끝은 다음 ### 또는 다음 ## 이다. `###` 만 보면 마지막 구간
        # (T – Z)이 다음 절(## A.3)을 통째로 삼켜, 행이 엉뚱한 표에 붙는다.
        m = re.search(rf"^### {re.escape(sec)}\s*$(.*?)(?=^#{{2,3}} |\Z)",
                      text, re.M | re.S)
        if not m:
            print(f"[중단] 구간 '### {sec}' 를 찾지 못함")
            return 1
        block = m.group(1)

        rows = [(mm.start(), mm.group(0), sort_key(mm.group(1)))
                for mm in re.finditer(r"^\|\s*([^|]+?)\s*\|[^\n]*$",
                                      block, re.M)
                if not mm.group(1).startswith("-")
                and mm.group(1).strip() != "약어"]
        if not rows:
            print(f"[중단] '### {sec}' 안에 표가 없음")
            return 1

        key = sort_key(abbr)
        after = None
        for start, line, k in rows:
            if k < key:
                after = (start, line)
        if after is None:
            insert_at = m.start(1) + rows[0][0]
        else:
            insert_at = m.start(1) + after[0] + len(after[1]) + 1

        text = text[:insert_at] + row + "\n" + text[insert_at:]
        existing.add(key)
        added += 1

    PATH.write_text(text, encoding="utf-8")
    print(f"\n{added}개 항목 추가")
    return 0


if __name__ == "__main__":
    sys.exit(main())
