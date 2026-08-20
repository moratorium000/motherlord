# 부록 A — 축약어 마스터 목록

**문서 번호**: RF-CUR-APX-A
**버전**: v1.0
**대응 규칙**: 설계서 §7 (규칙 P2-a, P2-b)

---

## A.0 이 문서의 쓰임

RF 분야는 축약어가 유난히 많습니다. 게다가 **같은 글자가 분야마다 다른 뜻**을 갖습니다. 예를 들어 `F`는 잡음지수(noise factor)이기도 하고 주파수(frequency)이기도 하며 패럿(farad)이기도 합니다. 초심자가 문서를 읽다 막히는 지점의 상당수는 개념이 어려워서가 아니라 **약어를 몰라서**입니다.

이 문서는 세 가지로 씁니다.

| 상황 | 보는 곳 |
|---|---|
| 영문 약어를 만났는데 뜻을 모를 때 | **§A.2 알파벳순 마스터 목록** |
| 한글 용어는 아는데 영어로 뭐라 하는지 모를 때 | **§A.3 한글 가나다순 색인** |
| 비슷한 약어끼리 헷갈릴 때 | **§A.4 혼동하기 쉬운 짝** ← 초심자에게 가장 유용 |

**"정의 모듈" 칸**은 그 개념이 커리큘럼에서 **처음 정식으로 설명되는 곳**입니다. 뜻만 알아서는 부족하고 제대로 이해하고 싶을 때 그 모듈로 가십시오. (설계서 §6.1 "개념 소유권" 참조)

---

## A.1 표기 규약

본문에서 축약어는 이렇게 씁니다.

```
잡음지수(Noise Figure, NF)     ← 각 모듈에서 처음 등장할 때
NF                             ← 그 모듈 안에서 두 번째부터
```

모듈은 각각 독립적으로 읽힐 수 있어야 하므로, **모듈이 바뀌면 다시 완전 표기**합니다. 같은 문서 안에서 반복되는 것은 낭비지만, 모듈을 건너뛰어 읽는 사람에게는 필요합니다.

한글 번역이 오히려 혼란스러운 경우(스미스 차트, 로드풀 등)에는 원어를 그대로 쓰고 괄호에 설명을 답니다.

---

## A.2 알파벳순 마스터 목록

### 숫자·기호

| 약어 | 영문 원어 | 한글 | 한 줄 뜻 | 정의 모듈 |
|---|---|---|---|---|
| 1 dB CP | 1 dB Compression Point | 1 dB 압축점 | 이득이 선형값보다 1 dB 줄어드는 전력. P1dB와 같은 말 | M08 |
| 2-tone | Two-tone Test | 2톤 시험 | 두 개의 순음을 동시에 넣어 상호변조를 보는 시험 | M15 |
| 3GPP | 3rd Generation Partnership Project | 3세대 파트너십 프로젝트 | 이동통신 규격을 만드는 국제 표준화 단체 | M13 |
| Γ (감마) | Reflection Coefficient | 반사계수 | 들어간 파 대비 되돌아온 파의 비율(복소수) | M02 |
| λ (람다) | Wavelength | 파장 | 한 주기 동안 파가 나아가는 거리 | M00 |

### A

| 약어 | 영문 원어 | 한글 | 한 줄 뜻 | 정의 모듈 |
|---|---|---|---|---|
| ACLR | Adjacent Channel Leakage Ratio | 인접 채널 누설비 | 내 채널 전력 대비 옆 채널로 새는 전력의 비 | M13 |
| ACPR | Adjacent Channel Power Ratio | 인접 채널 전력비 | ACLR과 사실상 같은 뜻. 규격에 따라 용어가 갈림 | M13 |
| ADC | Analog-to-Digital Converter | 아날로그-디지털 변환기 | 아날로그 신호를 숫자로 바꾸는 소자 | M11 |
| ADS | Advanced Design System | (상용 RF 설계 소프트웨어 이름) | Keysight의 회로·시스템 시뮬레이터 | M07 |
| AGC | Automatic Gain Control | 자동 이득 제어 | 입력 세기에 따라 이득을 자동 조절하는 회로 | M11 |
| AM | Amplitude Modulation | 진폭 변조 | 진폭에 정보를 싣는 변조 | M13 |
| AWR | (Microwave Office 계열 도구 이름) | — | Cadence의 RF 설계 소프트웨어 | M07 |

### B

| 약어 | 영문 원어 | 한글 | 한 줄 뜻 | 정의 모듈 |
|---|---|---|---|---|
| BAW | Bulk Acoustic Wave | 체적 탄성파 | 결정 내부를 통과하는 음향파를 쓰는 필터 기술 | M07 |
| BER | Bit Error Rate | 비트 오류율 | 전송한 비트 중 틀린 비트의 비율 | M13 |
| BJT | Bipolar Junction Transistor | 양극성 접합 트랜지스터 | 전류로 제어하는 트랜지스터 | M08 |
| BNC | Bayonet Neill–Concelman | (커넥터 이름) | 돌려 끼우는 방식의 저주파용 동축 커넥터 | M04 |
| BPF | Band Pass Filter | 대역 통과 필터 | 원하는 주파수 대역만 통과시키는 필터 | M07 |
| BW | Bandwidth | 대역폭 | 신호나 회로가 차지하는 주파수 폭 | M01 |

### C

| 약어 | 영문 원어 | 한글 | 한 줄 뜻 | 정의 모듈 |
|---|---|---|---|---|
| CATR | Compact Antenna Test Range | 소형 안테나 시험장 | 반사경으로 원거리장을 만드는 측정 설비 | M10 |
| CCDF | Complementary Cumulative Distribution Function | 상보 누적 분포 함수 | 첨두가 평균보다 얼마나 큰지 확률로 보는 그래프 | M13 |
| CFR | Crest Factor Reduction | 첨두 저감 | 신호의 뾰족한 첨두를 깎아 PAPR을 줄이는 처리 | M13 |
| CP | Compression Point | 압축점 | 이득이 줄어들기 시작하는 지점 | M08 |
| CW | Continuous Wave | 연속파 | 변조 없이 계속 나오는 순수한 사인파 | M05 |

### D

| 약어 | 영문 원어 | 한글 | 한 줄 뜻 | 정의 모듈 |
|---|---|---|---|---|
| DANL | Displayed Average Noise Level | 표시 평균 잡음 레벨 | 스펙트럼 분석기가 아무것도 없을 때 보여 주는 잡음 바닥 | M05 |
| dB | Decibel | 데시벨 | 두 값의 **비율**을 로그로 나타낸 단위 | M01 |
| dBc | Decibel relative to carrier | 반송파 대비 데시벨 | 주 신호 대비 얼마나 작은지 | M01 |
| dBd | Decibel relative to dipole | 다이폴 대비 데시벨 | 반파장 다이폴 안테나 기준 이득 | M10 |
| dBi | Decibel relative to isotropic | 등방성 대비 데시벨 | 모든 방향으로 고르게 쏘는 가상 안테나 기준 이득 | M10 |
| dBm | Decibel-milliwatt | 데시벨밀리와트 | 1 mW를 기준으로 한 **절대 전력** | M01 |
| dBW | Decibel-watt | 데시벨와트 | 1 W를 기준으로 한 절대 전력 | M01 |
| dBμV | Decibel-microvolt | 데시벨마이크로볼트 | 1 μV 기준 전압. EMC 규격에서 자주 쓰임 | M01 |
| DAC | Digital-to-Analog Converter | 디지털-아날로그 변환기 | 숫자를 아날로그 신호로 바꾸는 소자 | M11 |
| DC | Direct Current | 직류 | 시간에 따라 변하지 않는 전류/전압 | M01 |
| DFM | Design for Manufacturability | 제조 용이성 설계 | 실제로 만들 수 있게 설계하는 일 | M17 |
| Df | Dissipation Factor | 손실 탄젠트 | 기판 재료가 에너지를 얼마나 까먹는지 | M02 |
| Dk | Dielectric Constant | 유전율(비유전율) | 기판 재료가 전파 속도를 얼마나 늦추는지 | M02 |
| DPD | Digital Predistortion | 디지털 사전왜곡 | 증폭기 왜곡을 미리 반대로 왜곡시켜 상쇄하는 기법 | M13 |
| DR | Dynamic Range | 동적 범위 | 다룰 수 있는 가장 작은 신호와 큰 신호의 폭 | M12 |
| DUT | Device Under Test | 피시험 소자 | 지금 측정하고 있는 그 물건 | M04 |

### E

| 약어 | 영문 원어 | 한글 | 한 줄 뜻 | 정의 모듈 |
|---|---|---|---|---|
| ECal | Electronic Calibration | 전자식 교정 | 표준기를 손으로 바꿔 끼우지 않는 자동 교정 모듈 | M14 |
| EIRP | Effective Isotropic Radiated Power | 등가 등방성 복사 전력 | 송신 전력 × 안테나 이득. 규제가 이 값을 제한함 | M10 |
| EMC | Electromagnetic Compatibility | 전자파 적합성 | 남에게 방해 안 하고 남의 방해도 견디는 성질 | M17 |
| EMI | Electromagnetic Interference | 전자파 간섭 | 원치 않는 전자파 방해 | M17 |
| ENOB | Effective Number of Bits | 유효 비트수 | ADC가 실제로 쓸모 있게 쓰는 비트 수 | M11 |
| ENR | Excess Noise Ratio | 초과 잡음비 | 잡음원이 상온보다 얼마나 더 시끄러운지 | M15 |
| ERP | Effective Radiated Power | 유효 복사 전력 | EIRP와 비슷하되 다이폴 기준 (EIRP보다 2.15 dB 작음) | M10 |
| ESD | Electrostatic Discharge | 정전기 방전 | 정전기가 튀어 소자를 죽이는 현상 | M04 |
| ESL | Equivalent Series Inductance | 등가 직렬 인덕턴스 | 커패시터에 딸려 오는 기생 인덕턴스 | M06 |
| ESR | Equivalent Series Resistance | 등가 직렬 저항 | 부품에 딸려 오는 기생 저항 | M06 |
| ETSI | European Telecommunications Standards Institute | 유럽 전기통신 표준화 기구 | 유럽 무선 규격을 만드는 단체 | M13 |
| EVM | Error Vector Magnitude | 오차 벡터 크기 | 받은 신호가 이상적 위치에서 얼마나 벗어났는지 | M13 |

### F

| 약어 | 영문 원어 | 한글 | 한 줄 뜻 | 정의 모듈 |
|---|---|---|---|---|
| F | Noise Factor | 잡음 계수 | 잡음지수의 **선형** 값 (dB 아님). NF = 10 log F | M08 |
| FCC | Federal Communications Commission | 미국 연방통신위원회 | 미국의 무선 규제 기관 | M13 |
| FBAR | Film Bulk Acoustic Resonator | 박막 체적 음향 공진기 | BAW의 대표적 구현 방식 | M07 |
| FDD | Frequency Division Duplex | 주파수 분할 이중통신 | 송신·수신에 다른 주파수를 쓰는 방식 | M11 |
| FET | Field Effect Transistor | 전계효과 트랜지스터 | 전압으로 제어하는 트랜지스터 | M08 |
| FFT | Fast Fourier Transform | 고속 푸리에 변환 | 시간 신호를 주파수 성분으로 바꾸는 계산법 | M05 |
| F_min | Minimum Noise Figure | 최소 잡음지수 | 소자가 낼 수 있는 가장 좋은 잡음지수 | M08 |
| FR1 / FR2 | Frequency Range 1 / 2 | 주파수 범위 1 / 2 | 5G의 저주파 대역(~7 GHz) / 밀리미터파 대역 | M00 |
| FR-4 | Flame Retardant 4 | (기판 재료 등급 이름) | 가장 흔한 유리섬유 기판. RF에서는 손실이 큼 | M17 |
| FSPL | Free Space Path Loss | 자유공간 경로손실 | 아무 방해 없이 거리만으로 생기는 손실 | M10 |

### G

| 약어 | 영문 원어 | 한글 | 한 줄 뜻 | 정의 모듈 |
|---|---|---|---|---|
| GCPW | Grounded Coplanar Waveguide | 접지형 코플래너 도파관 | 신호선 양옆에도 접지를 둔 기판 전송선 | M02 |
| GPIB | General Purpose Interface Bus | 범용 인터페이스 버스 | 옛날부터 쓰던 계측기 연결 규격 | M16 |
| GUM | Guide to the Expression of Uncertainty in Measurement | 측정 불확도 표현 지침 | 불확도를 계산·표기하는 국제 지침 | M14 |

### H – I

| 약어 | 영문 원어 | 한글 | 한 줄 뜻 | 정의 모듈 |
|---|---|---|---|---|
| HPF | High Pass Filter | 고역 통과 필터 | 높은 주파수만 통과시키는 필터 | M07 |
| I/Q | In-phase / Quadrature | 동상 / 직교 | 신호를 90° 어긋난 두 성분으로 나눈 표현 | M11 |
| IF | Intermediate Frequency | 중간주파수 | RF와 기저대역 사이에 두는 중간 단계 주파수 | M09 |
| IIP2 / IIP3 | Input second/third-order Intercept Point | 입력 2차/3차 교차점 | 입력 기준으로 본 선형성 지표 | M08 |
| IL | Insertion Loss | 삽입 손실 | 부품을 끼웠을 때 줄어드는 신호량 | M02 |
| IMD | Intermodulation Distortion | 상호변조 왜곡 | 두 신호가 섞여 새 주파수를 만드는 왜곡 | M08 |
| IM3 | Third-order Intermodulation | 3차 상호변조 | 대역 안에 떨어져 특히 골치 아픈 왜곡 성분 | M08 |
| IRM | Image Reject Mixer | 이미지 제거 믹서 | 이미지 주파수를 구조적으로 없애는 믹서 | M09 |
| ISM | Industrial, Scientific and Medical | 산업·과학·의료 (대역) | 면허 없이 쓸 수 있는 주파수 대역 | M13 |
| ITU | International Telecommunication Union | 국제전기통신연합 | 주파수 국제 배분을 담당하는 UN 기구 | M13 |

### K – L

| 약어 | 영문 원어 | 한글 | 한 줄 뜻 | 정의 모듈 |
|---|---|---|---|---|
| K-factor | Rollett Stability Factor | 롤렛 안정도 계수 | 증폭기가 발진하지 않을 조건을 판정하는 값 | M08 |
| KC | Korea Certification | 국가통합인증마크 | 한국의 제품 인증 제도 | M17 |
| kTB | — | 열잡음 전력 | 온도와 대역폭만으로 정해지는 잡음의 바닥 | M01 |
| LNA | Low Noise Amplifier | 저잡음 증폭기 | 수신단 맨 앞에서 잡음을 최소로 하며 키우는 증폭기 | M08 |
| LO | Local Oscillator | 국부 발진기 | 주파수를 옮기기 위해 믹서에 넣는 자체 신호 | M09 |
| LPF | Low Pass Filter | 저역 통과 필터 | 낮은 주파수만 통과시키는 필터 | M07 |
| LTE | Long Term Evolution | (4세대 이동통신 규격 이름) | 4G 이동통신 표준 | M13 |
| LXI | LAN eXtensions for Instrumentation | 계측기용 LAN 확장 | 이더넷으로 계측기를 연결하는 규격 | M16 |

### M – N

| 약어 | 영문 원어 | 한글 | 한 줄 뜻 | 정의 모듈 |
|---|---|---|---|---|
| MAG | Maximum Available Gain | 최대 가용 이득 | 입출력을 완벽히 정합했을 때 낼 수 있는 최대 이득 | M08 |
| MDS | Minimum Detectable Signal | 최소 검출 신호 | 겨우 알아볼 수 있는 가장 작은 신호 | M12 |
| MMIC | Monolithic Microwave Integrated Circuit | 단일칩 마이크로파 집적회로 | RF 회로를 통째로 집적한 칩 | M08 |
| NF | Noise Figure | 잡음지수 | 소자를 지나며 신호대잡음비가 얼마나 나빠지는지 (dB) | M08 |
| NIST | National Institute of Standards and Technology | 미국 국립표준기술연구소 | 미국의 국가 계량 표준 기관 | M14 |
| NSD | Noise Spectral Density | 잡음 스펙트럼 밀도 | 1 Hz당 잡음 전력 | M11 |
| NTN | Non-Terrestrial Network | 비지상 네트워크 | 위성 등을 이용한 통신망 | M10 |

### O – P

| 약어 | 영문 원어 | 한글 | 한 줄 뜻 | 정의 모듈 |
|---|---|---|---|---|
| OFDM | Orthogonal Frequency Division Multiplexing | 직교 주파수 분할 다중 | 수많은 좁은 반송파에 나눠 싣는 변조 방식 | M13 |
| OIP3 | Output third-order Intercept Point | 출력 3차 교차점 | 출력 기준으로 본 선형성 지표 | M08 |
| OTA | Over-The-Air | 공중 방사 (측정) | 케이블 대신 실제로 전파를 쏴서 하는 측정 | M10 |
| P1dB | 1 dB Compression Point | 1 dB 압축점 | 이득이 1 dB 줄어드는 전력 수준 | M08 |
| PA | Power Amplifier | 전력 증폭기 | 송신단 마지막에서 세게 키우는 증폭기 | M08 |
| PAE | Power Added Efficiency | 전력 부가 효율 | 증폭기가 직류 전력을 RF로 바꾼 효율 | M08 |
| PAPR | Peak-to-Average Power Ratio | 첨두대평균 전력비 | 신호의 첨두가 평균보다 몇 배나 큰지 | M13 |
| PCB | Printed Circuit Board | 인쇄 회로 기판 | 부품을 얹고 배선을 새긴 판 | M17 |
| PDN | Power Distribution Network | 전원 분배망 | 각 부품에 전원을 안정적으로 나눠 주는 회로 | M17 |
| PLL | Phase-Locked Loop | 위상동기루프 | 기준 신호에 위상을 맞춰 원하는 주파수를 만드는 회로 | M09 |
| PTFE | Polytetrafluoroethylene | 폴리테트라플루오로에틸렌 | 손실이 매우 낮은 고급 기판 재료(테프론) | M17 |

### Q – R

| 약어 | 영문 원어 | 한글 | 한 줄 뜻 | 정의 모듈 |
|---|---|---|---|---|
| Q | Quality Factor | 품질 계수 | 공진이 얼마나 날카로운지, 손실이 얼마나 적은지 | M06 |
| QAM | Quadrature Amplitude Modulation | 직교 진폭 변조 | 진폭과 위상을 함께 써서 정보를 싣는 변조 | M13 |
| QPSK | Quadrature Phase Shift Keying | 4위상 편이 변조 | 위상 4개로 2비트씩 싣는 변조 | M13 |
| RBW | Resolution Bandwidth | 분해능 대역폭 | 스펙트럼 분석기가 두 신호를 구별하는 능력 | M05 |
| RED | Radio Equipment Directive | 무선기기 지침 | 유럽의 무선기기 규제 지침 (2014/53/EU) | M17 |
| REFSENS | Reference Sensitivity | 기준 감도 | 3GPP가 정한 최소 수신 감도 요구값 | M13 |
| RF | Radio Frequency | 무선 주파수 | 전파로 쓰이는 주파수 대역 전반 | M00 |
| RL | Return Loss | 반사 손실 | 되돌아온 신호가 원신호보다 몇 dB 작은지 (클수록 좋음) | M02 |
| RMS | Root Mean Square | 제곱평균제곱근 | 변동하는 값의 실효값 | M01 |
| RSS | Root Sum Square | 제곱합근 | 독립적인 오차들을 합치는 방법 | M12 |

### S

| 약어 | 영문 원어 | 한글 | 한 줄 뜻 | 정의 모듈 |
|---|---|---|---|---|
| SA | Spectrum Analyzer | 스펙트럼 분석기 | 신호를 주파수 축에 펼쳐 보여 주는 장비 | M04 |
| SAW | Surface Acoustic Wave | 표면 탄성파 | 결정 표면의 음향파를 쓰는 필터 기술 | M07 |
| SCPI | Standard Commands for Programmable Instruments | 프로그래머블 계측기 표준 명령 | 계측기를 글자 명령으로 제어하는 공통 규격 | M16 |
| SDR | Software Defined Radio | 소프트웨어 정의 무선 | 기능 대부분을 소프트웨어로 처리하는 무선기 | M11 |
| SEM | Spectrum Emission Mask | 스펙트럼 방출 마스크 | 주파수별로 넘으면 안 되는 전력 한계선 | M13 |
| SFDR | Spurious-Free Dynamic Range | 무스퓨리어스 동적 범위 | 가짜 신호에 묻히지 않고 볼 수 있는 범위 | M11 |
| SMA | SubMiniature version A | (커넥터 이름) | RF에서 가장 흔한 소형 나사식 커넥터 | M04 |
| SNR | Signal-to-Noise Ratio | 신호대잡음비 | 신호가 잡음보다 몇 dB 큰지 | M01 |
| SOLR | Short-Open-Load-Reciprocal | (교정 방식 이름) | 스루 표준을 정확히 몰라도 되는 교정법 | M14 |
| SOLT | Short-Open-Load-Thru | (교정 방식 이름) | 표준기 4종으로 하는 가장 흔한 VNA 교정 | M14 |
| SPDT | Single Pole Double Throw | 단극쌍투 | 한 입력을 두 출력 중 하나로 보내는 스위치 | M07 |
| SRF | Self-Resonant Frequency | 자기공진주파수 | 이 위에서는 커패시터가 인덕터처럼 행동하는 경계 | M06 |
| SWR | Standing Wave Ratio | 정재파비 | VSWR과 같은 말 | M02 |

### T – Z

| 약어 | 영문 원어 | 한글 | 한 줄 뜻 | 정의 모듈 |
|---|---|---|---|---|
| TCXO | Temperature Compensated Crystal Oscillator | 온도보상 수정발진기 | 온도가 변해도 주파수가 잘 안 변하는 발진기 | M09 |
| TDD | Time Division Duplex | 시분할 이중통신 | 송신과 수신을 시간으로 나눠 번갈아 하는 방식 | M11 |
| TDR | Time Domain Reflectometry | 시간 영역 반사 측정 | 반사가 **어느 위치**에서 생겼는지 찾는 기법 | M14 |
| TRL | Thru-Reflect-Line | (교정 방식 이름) | 기판 위 측정에 유리한 VNA 교정법 | M14 |
| T₀ | Reference Temperature (290 K) | 기준 온도 | 잡음지수 정의에 쓰는 약속된 온도 | M01 |
| UE | User Equipment | 사용자 단말 | 3GPP 용어로 휴대폰 등 단말기 | M13 |
| VBW | Video Bandwidth | 비디오 대역폭 | 트레이스를 매끄럽게 다듬는 필터 설정 | M05 |
| VCO | Voltage Controlled Oscillator | 전압제어 발진기 | 전압으로 주파수를 바꾸는 발진기 | M09 |
| VISA | Virtual Instrument Software Architecture | 가상 계측기 소프트웨어 구조 | 어떤 연결 방식이든 같은 방법으로 계측기를 다루게 해 주는 계층 | M16 |
| VNA | Vector Network Analyzer | 벡터 회로망 분석기 | S-파라미터를 크기와 위상까지 재는 장비 | M04 |
| VSWR | Voltage Standing Wave Ratio | 전압 정재파비 | 정합이 얼마나 잘 됐는지 나타내는 1 이상의 수 | M02 |
| Z₀ | Characteristic Impedance | 특성 임피던스 | 전송선로가 지닌 고유 임피던스 (보통 50 Ω) | M02 |

---

## A.3 한글 가나다순 색인

| 한글 용어 | 약어 / 원어 | 정의 모듈 |
|---|---|---|
| 감쇠기 | Attenuator | M07 |
| 결합기 | Coupler | M07 |
| 경로손실 | Path Loss / FSPL | M10 |
| 교정 | Calibration | M14 |
| 국부 발진기 | LO | M09 |
| 군지연 | Group Delay | M07 |
| 근거리장 / 원거리장 | Near Field / Far Field | M10 |
| 기준 임피던스 | Reference Impedance | M03 |
| 대역폭 | BW | M01 |
| 데시벨 | dB | M01 |
| 동적 범위 | Dynamic Range | M12 |
| 디임베딩 | De-embedding | M14 |
| 로드풀 | Load-pull | M15 |
| 마이크로스트립 | Microstrip | M02 |
| 반사계수 | Γ | M02 |
| 반사 손실 | RL | M02 |
| 방사 패턴 | Radiation Pattern | M10 |
| 백오프 | Back-off | M13 |
| 부정합 불확도 | Mismatch Uncertainty | M14 |
| 분해능 대역폭 | RBW | M05 |
| 삽입 손실 | IL | M02 |
| 상호변조 | IMD | M08 |
| 성상도 | Constellation | M13 |
| 스미스 차트 | Smith Chart | M03 |
| 스퓨리어스 | Spurious | M09 |
| 스택업 | Stack-up | M17 |
| 안정도 | Stability (K-factor) | M08 |
| 압축점 | P1dB | M08 |
| 열잡음 | Thermal Noise / kTB | M01 |
| 오차 벡터 크기 | EVM | M13 |
| 위상잡음 | Phase Noise | M09 |
| 이미지 주파수 | Image Frequency | M09 |
| 잡음지수 | NF | M08 |
| 전송선로 | Transmission Line | M02 |
| 정합 | Matching | M03 |
| 정재파비 | VSWR | M02 |
| 주파수 계획 | Frequency Planning | M09 |
| 중간주파수 | IF | M09 |
| 차단 | Blocking | M12 |
| 첨두대평균 전력비 | PAPR | M13 |
| 캐스케이드 | Cascade | M12 |
| 커넥터 | Connector | M04 |
| 특성 임피던스 | Z₀ | M02 |
| 파장 | λ | M00 |
| 품질 계수 | Q | M06 |
| 필터 | Filter | M07 |
| 하모닉 | Harmonic | M08 |
| 회로망 분석기 | VNA | M04 |
| 효율 | PAE | M08 |

---

## A.4 혼동하기 쉬운 짝 ★

초심자가 실제로 가장 많이 틀리는 지점만 모았습니다. **이 절만 따로 외워도 문서 읽는 속도가 달라집니다.**

### 1. dB vs dBm — 비율이냐 절대값이냐

| | dB | dBm |
|---|---|---|
| 무엇 | **비율** (기준 없음) | **절대 전력** (기준 = 1 mW) |
| 예 | "이 증폭기 이득은 20 dB" | "출력은 +10 dBm" |
| 더하기 | dBm + dB = dBm ✅ | dBm + dBm = **의미 없음** ❌ |

> 외우는 법: **m**이 붙으면 **milliwatt** 기준이 있으니 절대값입니다.

### 2. NF vs F — dB냐 선형이냐

- **F (잡음 계수, noise factor)** = 선형 값. 캐스케이드 계산(Friis 공식)은 **반드시 F로** 합니다.
- **NF (잡음지수, noise figure)** = 10 log₁₀ F, 단위 dB. 데이터시트에 적히는 값.

> 초심자 실수 1순위: **dB 값을 그대로 Friis 공식에 넣기.** 반드시 선형으로 바꾼 뒤 계산하고, 결과를 다시 dB로 되돌립니다.

### 3. IIP3 vs OIP3 — 입력 기준이냐 출력 기준이냐

`OIP3 = IIP3 + 이득(dB)`

수신단 설계에서는 보통 **IIP3**를, 송신단에서는 **OIP3**를 씁니다. 데이터시트에 어느 쪽이 적혀 있는지 확인하지 않으면 이득만큼(보통 10~20 dB) 통째로 틀립니다.

### 4. RBW vs VBW — 분해하느냐 다듬느냐

| | RBW (분해능 대역폭) | VBW (비디오 대역폭) |
|---|---|---|
| 하는 일 | 가까운 두 신호를 **구별** | 트레이스를 **매끄럽게** |
| 잡음 바닥 | 좁히면 **내려감** | 좁혀도 **안 내려감** (변동만 줄어듦) |
| 소인 시간 | 좁히면 **크게 늘어남** | 좁히면 늘어남 |

> 잡음 바닥을 낮추려면 **RBW**를 좁혀야 합니다. VBW를 아무리 좁혀도 바닥은 그대로입니다.

### 5. VSWR vs 반사 손실 vs Γ — 같은 것의 세 얼굴

셋은 **같은 정보를 다르게 표현한 것**입니다.

| VSWR | 반사 손실 (dB) | 반사되는 전력 |
|---|---|---|
| 1.0 | ∞ | 0 % (완벽) |
| 1.5 | 14.0 | 4 % |
| 2.0 | 9.5 | 11 % |
| 3.0 | 6.0 | 25 % |

> **반사 손실은 클수록 좋습니다** (많이 "손실"되어 안 돌아옴). 부호를 −9.5 dB로 쓰는 곳도 있어 헷갈리므로, 문서마다 부호 규약을 확인하십시오.

### 6. EIRP vs ERP — 기준 안테나가 다르다

`EIRP(dBm) = ERP(dBm) + 2.15 dB`

EIRP는 등방성 안테나 기준, ERP는 반파장 다이폴 기준입니다. 규제 문서가 어느 쪽으로 한계를 정했는지 확인하지 않으면 2.15 dB만큼 틀립니다.

### 7. ACLR vs SEM vs 스퓨리어스 — 셋 다 "새는 것"이지만 다르다

| | 무엇을 보는가 | 측정 방식 |
|---|---|---|
| **ACLR** | 바로 옆 **채널**로 새는 전력 | 채널 대역폭만큼 적분해 비율로 |
| **SEM** | 내 채널 주변의 **주파수별 한계선** | 마스크 위로 넘는지 판정 |
| **스퓨리어스** | **멀리 떨어진** 곳에 튀어나온 가짜 신호 | 넓은 대역을 훑어서 절대값으로 |

### 8. SAW vs BAW — 어디를 지나가느냐

- **SAW**: 결정 **표면**을 타고 감. 대략 1.5 GHz까지 유리하고 만들기 쉬움.
- **BAW/FBAR**: 결정 **속**을 통과. 더 높은 주파수에서 삽입 손실이 낮고 차단 특성이 가파름.

### 9. S11 vs Γ — 거의 같지만 완전히 같지는 않다

S11은 **다른 포트가 모두 기준 임피던스로 종단된 상태**에서 잰 반사계수입니다. 2포트 소자의 출력에 다른 것이 붙어 있으면 실제 입력 반사계수 Γ_in은 S11과 달라집니다.

### 10. 3 dB의 두 얼굴

- **전력**이 3 dB 줄면 → **절반** (50 %)
- **전압**이 3 dB 줄면 → 약 0.707배

같은 3 dB인데 배율이 다른 이유는 전력이 전압의 제곱에 비례하기 때문입니다. 그래서 전력은 10 log, 전압은 20 log를 씁니다. (→ M01 §2)

---

## A.5 유지 관리 규칙

1. 모듈 본문을 집필할 때 **새 축약어가 나오면 즉시 이 문서에 추가**합니다.
2. "정의 모듈" 칸은 설계서 §6.1 **개념 소유권 매트릭스와 항상 일치**해야 합니다. 불일치는 구조 결함입니다.
3. §A.4는 **집필 중 실제로 헷갈린 것**만 추가합니다. 예상만으로 늘리면 목록이 길어져 쓸모가 떨어집니다.

---

## 변경 이력

| 버전 | 일자 | 내용 |
|---|---|---|
| v1.0 | 2026-08-20 | 최초 작성. 약 180개 항목, 혼동 짝 10종 |
| — | 2026-08-20 | **검토 3회 완료.** 1차(사실): VSWR↔반사손실↔반사전력 환산표, EIRP−ERP=2.15 dB, OIP3=IIP3+이득을 계산으로 재검증 → 전부 일치. 2차(교육): §A.4 "혼동하기 쉬운 짝"을 초심자 실수 빈도순으로 재배열. 3차(구조): 설계서 §6.1 개념 소유권과 대조 → **삽입손실(IL)의 정의 모듈이 M07로 잘못 기재된 것을 M02로 정정** |
