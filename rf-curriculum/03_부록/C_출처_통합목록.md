# 부록 C — 출처 통합목록

**문서 번호**: RF-CUR-APX-C · **버전**: v1.0
**대응 규칙**: 설계서 §11 (출처 관리·신뢰성 등급·교차검증)
**생성 방법**: 이 문서는 **본문에서 자동 생성**됩니다 — `python3 scripts/gen_appendix_c.py`

---

## C.0 이 문서는 무엇인가

> **본문 전체가 인용한 외부 출처를 한곳에 모은 것입니다.** 어떤 주장이 어디서 왔는지 되짚을 때, 그리고 **링크가 죽었는지 확인할 때** 씁니다.

### 손으로 쓰지 않았습니다

출처 목록을 손으로 옮겨 적으면 본문이 바뀔 때마다 어긋납니다. 그래서 이 문서는 저장소의 모든 마크다운을 훑어 **생성**합니다.

```bash
python3 scripts/gen_appendix_c.py            # 다시 생성
python3 scripts/gen_appendix_c.py --check    # 본문과 어긋났는지 확인
```

> 📌 **본문에 출처를 추가하거나 고쳤다면 이 스크립트를 다시 돌리십시오.** `--check` 는 어긋난 것이 있으면 0이 아닌 값으로 끝나므로 자동화에 걸 수 있습니다.

### 등급의 뜻

| 등급 | 무엇 | 어떻게 쓰나 |
|---|---|---|
| **A** | 1차 표준·규격 | 표준화 기구·규제기관의 원문. 가장 신뢰도가 높다 |
| **B** | 제조사·학술 | 계측기·부품 제조사의 응용노트와 백서, 대학 교재·논문 |
| **C** | 교육 사이트 | 정리가 잘 된 공개 교육 자료. 원문 확인이 필요할 때가 있다 |
| **D** | 블로그·개인 | 유용하지만 단독 근거로 쓰지 않는다. 교차검증 필수 |
| — | 등급 없음 | **사실 근거가 아니라 교육 구성 참고**로 인용한 것 |

> ⚠️ **등급은 신뢰도의 순위이지 정확도의 보증이 아닙니다.** 등급 A라도 개정되고, 등급 D라도 맞을 수 있습니다. **중요한 수치는 등급과 무관하게 원문에서 확인**하십시오.

---

## C.1 한눈에

| | |
|---|---|
| 고유 출처 | **282개** |
| 인용한 문서 | 32편 |
| 발행 주체 | 143곳 |

### 등급 분포

| 등급 | 개수 | 비율 |
|---|---|---|
| A | 21 | 7.4 % |
| B | 173 | 61.3 % |
| C | 36 | 12.8 % |
| D | 44 | 15.6 % |
| — (참고 사이트, 교육 구성 참고) | 8 | 2.8 % |

> 📌 **등급 D가 적지 않은 것은 의도된 결과입니다.** RF 실무 지식의 상당 부분이 제조사 블로그와 엔지니어 개인 글에 있습니다. 그래서 D는 **단독으로 쓰지 않고 반드시 교차검증**했습니다 — 각 모듈의 출처 표에 교차검증 건수가 적혀 있습니다.

### 발행 주체 상위

| 발행 주체 | 출처 수 |
|---|---|
| Keysight | 19 |
| Analog Devices | 11 |
| allaboutcircuits.com | 9 |
| mwrf.com | 9 |
| rfdh.com (참고 사이트) | 8 |
| Mini-Circuits | 8 |
| microwavejournal.com | 8 |
| arXiv | 8 |
| LibreTexts (Steer 교재) | 6 |
| rfessentials.com | 6 |
| researchgate.net | 6 |
| Microwaves101 | 5 |
| scikit-rf | 4 |
| ieeexplore.ieee.org | 4 |

---

## C.2 여러 모듈이 함께 쓴 출처

세 편 이상에서 인용한 것들입니다. **이 커리큘럼의 뼈대를 이루는 자료**입니다.

| 등급 | 출처 | 쓴 모듈 |
|---|---|---|
| B | [Steer, Microwave and RF Design I — Radio Systems (LibreTexts, 무료 공개)](https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_I_-_Radio_Systems_(Steer)) | M00 · M01 · M10 · M12 |
| - | [rfdh — RF 트랜시버 시스템의 이해](https://rfdh.com/bas_rf.htm) | M00 · M01 · M06 · M11 |
| B | [Keysight AN 57-1 / 5952-8255 — Fundamentals of RF and Microwave Noise ](https://keysight.com/us/en/assets/7018-06808/application-notes/5952-8255.pdf) | M01 · M08 · M12 |
| B | [Keysight AN 5965-7709 — Applying Error Correction to VNA Measurements](https://keysight.com/us/en/assets/7018-06761/application-notes/5965-7709.pdf) | M04 · M05 · M14 |
| A | [EURAMET Calibration Guide No. 12 — Guidelines on the Evaluation of Vec](https://euramet.org/Media/news/I-CAL-GUI-012_Calibration_Guide_No._12.web.pdf) | M04 · M14 · M16 |
| B | [Mini-Circuits AN00-008 — Improve Two-Tone, Third-Order Intermodulation](https://minicircuits.com/app/AN00-008.pdf) | M07 · M08 · M15 |

---

## C.3 등급 A — 1차 표준·규격 (21개)

*표준화 기구·규제기관의 원문. 가장 신뢰도가 높다*

| 출처 | 발행 주체 | 쓴 모듈 |
|---|---|---|
| [CTIA OTA 시험계획서 Rev 3.4.1](https://api.ctia.org/docs/default-source/default-document-library/ctia_ota_test_plan_rev_3_4_1.pdf) | api.ctia.org | B09 |
| [CTIA OTA 시험계획서 Rev 3.3.2](https://api.ctia.org/docs/default-source/default-document-library/ctia_ota_test_plan_rev-3-3-2.pdf) | api.ctia.org | B09 |
| [3GPP TS 38.101-1 (ATIS 사본, Rel-16)](https://atisorg.s3.amazonaws.com/archive/3gpp-documents/Rel16/ATIS.3GPP.38.101-1.V1640.pdf) | atisorg.s3.amazonaws.com | M00 · M13 |
| [CTIA 01.20 — 무선 기기 OTA 성능 시험 방법](https://ctiacertification.org/wp-content/uploads/2021/02/CTIA-01.20-Test-Methodology-SISO-Anechoic-Chamber-V4.0.0.pdf) | ctiacertification.org | B09 |
| [eCFR 47 CFR Part 15](https://ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15) | eCFR (미국 연방규정) | M13 |
| [eCFR — 47 CFR Part 15 Subpart B (비의도적 방사체)](https://ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15/subpart-B) | eCFR (미국 연방규정) | M17 |
| [eCFR — 47 CFR Part 15 Subpart C (의도적 방사체)](https://ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15/subpart-C) | eCFR (미국 연방규정) | M17 |
| [IEEE Std 370-2020](https://elecenghub.com/NewSamples/IEEE/149366437/IEEE-370-2020-2.pdf) | elecenghub.com | B03 |
| [ETSI TS 138 101-5](https://etsi.org/deliver/etsi_ts/138100_138199/13810105/17.05.00_60/ts_13810105v170500p.pdf) | ETSI | M13 |
| [EURAMET Calibration Guide No. 12 — Guidelines on the Evaluation of Vector ](https://euramet.org/Media/news/I-CAL-GUI-012_Calibration_Guide_No._12.web.pdf) | EURAMET | M04 · M14 · M16 |
| [MIL-STD-348](https://everyspec.com/MIL-STD/MIL-STD-0300-0499/download.php?spec=MIL-STD-348B_CHG-1.054027.pdf) | MIL-STD | M04 · 부록 D |
| [IEEE Xplore — 2x-Thru 오차 한계 분석](https://ieeexplore.ieee.org/document/8077927) | ieeexplore.ieee.org | B03 |
| [IEEE — 간접 학습 구조 기반 메모리 다항식 전왜곡기](https://ieeexplore.ieee.org/document/1188221) | ieeexplore.ieee.org | B04 |
| [IEEE — 파고율 저감을 위한 다중톤 생성 알고리즘](https://ieeexplore.ieee.org/document/9301549) | ieeexplore.ieee.org | B04 |
| [NCSLI — 오수락 위험 관리를 위한 가드밴딩 방법](https://ncsli.org/mpage/MJ_V15_A2) | ncsli.org | B12 |
| [NIST — Metrological Traceability](https://nist.gov/metrology/metrological-traceability) | nist.gov | M14 |
| [NIST — 극저온 분배기로 붕괴 효과를 줄인 위상잡음 측정](https://nist.gov/publications/phase-noise-measurements-cryogenic-power-splitter-minimize-cross-spectral-collapse) | nist.gov | B06 |
| [Sandia — 가드밴딩 평가 보고서](https://osti.gov/servlets/purl/1855029) | osti.gov | B12 |
| [ISO/TR 14253-6:2012 — 합격·불합격 판정 규칙](https://standards.iteh.ai/catalog/standards/iso/b6e458d4-a2a6-4869-b07a-d5f3b9ca26dd/iso-tr-14253-6-2012) | standards.iteh.ai | B12 |
| [NIST — 분배기 반상관 열잡음에 의한 교차 스펙트럼 붕괴](https://tf.boulder.nist.gov/general/pdf/2844.pdf) | tf.boulder.nist.gov | B06 |
| [NIST — 교차 스펙트럼 측정에서의 분배기 열잡음 상관](https://tf.nist.gov/general/pdf/2853.pdf) | tf.nist.gov | B06 |

---

## C.4 등급 B — 제조사·학술 (173개)

*계측기·부품 제조사의 응용노트와 백서, 대학 교재·논문*

| 출처 | 발행 주체 | 쓴 모듈 |
|---|---|---|
| [Rohde & Schwarz — Understanding Phase Noise Fundamentals (백서)](https://allaboutcircuits.com/uploads/articles/RnS-Understanding-phase-noise-fundamentals_wp.pdf) | allaboutcircuits.com | M09 |
| [AllPCB — 전도·방사 시험에서의 전류 프로브](https://allpcb.com/allelectrohub/current-probe-use-in-conducted-and-radiated-testing) | allpcb.com | B07 |
| [Altium 문서 — Adding Via Stitching and Via Shielding](https://altium.com/documentation/altium-designer/pcb/via-stitching-via-shielding) | altium.com | M17 |
| [AMD/Xilinx WP489 — An Adaptable Direct RF Sampling Solution](https://amd.com/content/dam/amd/en/documents/solutions/direct-rf-sampling-solution-white-paper.pdf) | amd.com | M11 |
| [AMD — Understanding Key Parameters for RF-Sampling Data Converters](https://amd.com/content/dam/amd/en/documents/solutions/zynq-ultrascale-plus-rfsocs-white-paper.pdf) | amd.com | M11 |
| [Analog Devices — PCB Layout Guidelines for RF and Mixed-Signal](https://analog.com/en/resources/technical-articles/pcbs-layout-guidelines-for-rf--mixedsignal.html) | Analog Devices | M06 · M17 |
| [Analog Devices — Low-Noise Amplifier Stability: Concept to Practical Consi](https://analog.com/en/resources/technical-articles/lownoise-amplifier-stability-concept-to-practical-considerations-part-2.html) | Analog Devices | M08 |
| [Analog Devices — Power Added Efficiency (PAE)](https://analog.com/en/resources/glossary/power-added-efficiency-pae.html) | Analog Devices | M08 |
| [Analog Devices — Understanding Image Rejection and Its Impact on Desired S](https://analog.com/en/resources/analog-dialogue/articles/mirror-mirror-on-the-wall-understanding-image-rejection-and-its-impact-on-desired-signals.html) | Analog Devices | M09 |
| [Analog Devices — Mixer 2×2 Spurious Response and IP2 Relationship](https://analog.com/en/resources/technical-articles/mixer-2x2-spurious-response-and-ip2-relationship.html) | Analog Devices | M09 |
| [Analog Devices — System Noise-Figure Analysis for Modern Radio Receivers](https://analog.com/en/resources/technical-articles/system-noisefigure-analysis-for-modern-radio-receivers.html) | Analog Devices | M12 |
| [Analog Devices — RF Signal Chain Discourse: Properties and Performance Met](https://analog.com/en/resources/analog-dialogue/articles/rf-signal-chain-discourse.html) | Analog Devices | M12 |
| [Analog Devices — Cascaded Performance: Integrated vs Passive Mixers](https://analog.com/en/resources/technical-articles/cascaded-performance-when-comparing-integrated-rf-frequencyrnmixers.html) | Analog Devices | M12 |
| [Analog Devices MT-008 — 발진기 위상잡음을 시간 지터로](https://analog.com/media/en/training-seminars/tutorials/mt-008.pdf) | Analog Devices | B06 |
| [Analog Devices AN-1067 — 위상잡음과 지터의 전력 스펙트럼 밀도](https://analog.com/en/resources/app-notes/an-1067.html) | Analog Devices | B06 |
| [Analog Devices AN-2064 — 수신기 디센스 회피 알고리즘](https://analog.com/en/app-notes/an-2064.html) | Analog Devices | B10 |
| [Analyse-it — 방법 비교에 쓸 회귀 고르기](https://analyse-it.com/learn/choosing-a-regression-for-method-comparison) | analyse-it.com | B11 |
| [arXiv — 뉴먼 위상에 관한 추측](https://arxiv.org/pdf/2509.11278) | arXiv | B04 |
| [arXiv — 열잡음 한계 발진기의 교차 스펙트럼 측정](https://arxiv.org/pdf/1512.06160) | arXiv | B06 |
| [arXiv — 실리콘 나노공진기의 주파수 요동](https://arxiv.org/pdf/1506.08135) | arXiv | B06 |
| [arXiv — Bland-Altman 그림의 유용성과 추론](https://arxiv.org/pdf/2108.12937) | arXiv | B11 |
| [Keysight — 오실로스코프 프로브 사양 이해 (AN 1124)](https://assets.testequity.com/te1/Documents/pdf/keysight/Keysight_Understanding-Oscilloscope-Probe-Specifications_App_Note_1124.pdf) | assets.testequity.com | B02 |
| [R&S — NPR 신호 생성과 측정 (1MA29)](https://av.it.pt/medidas/data/Manuais%20&%20Tutoriais/28%20-%20Spectrum%20Analyser%2040GHz/CD/application%20notes/1MA29/1MA29_4E.pdf) | av.it.pt | B04 |
| [Knowles — RF Filter Terminology and Specifications](https://blog.knowlescapacitors.com/blog/filter-terminology-and-specifications) | blog.knowlescapacitors.com | M07 |
| [Mini-Circuits — Applying Proper Torque to Microwave Connectors](https://blog.minicircuits.com/applying-proper-torque-to-microwave-connectors) | Mini-Circuits | M04 · 부록 D |
| [Mini-Circuits — Making Good RF Connections](https://blog.minicircuits.com/making-good-rf-connections-best-practices-and-the-role-of-anti-torque-connectors) | Mini-Circuits | M04 |
| [Mini-Circuits 블로그 — 같은 내용](https://blog.minicircuits.com/improve-two-tone-third-order-intermodulation-testing) | Mini-Circuits | M15 |
| [SAS — 서로 다른 측정법을 비교하는 데밍 회귀](https://blogs.sas.com/content/iml/2019/01/07/deming-regression-sas.html) | blogs.sas.com | B11 |
| [Rohde & Schwarz 백서 — Understanding EVM (Denisowski)](https://cdn.rohde-schwarz.com.cn/pws/dl_downloads/premiumdownloads/premium_dl_pdm_downloads/3683_8038_52/Understanding-EVM_wp_en_3683-8038-52_v0100.pdf) | cdn.rohde-schwarz.com.cn | M13 |
| [R&S — 픽스처 특성화와 디임베딩](https://cdn.rohde-schwarz.com.cn/pws/dl_downloads/dl_application/application_notes/1sl367/1SL367_0e_Test_Fixture_Characterization_and_De-embedding.pdf) | cdn.rohde-schwarz.com.cn | B03 |
| [R&S 1EF110 — 매우 높은 잡음지수의 측정](https://cdn.rohde-schwarz.com.cn/pws/dl_downloads/dl_application/application_notes/1ef110/1EF110_1e_FSWK30_ENR.pdf) | cdn.rohde-schwarz.com.cn | B05 |
| [Teledyne LeCroy — 지터 계산 방법의 이해](https://cdn.teledynelecroy.com/files/whitepapers/understanding_sdaiii_jitter_calculation_methods.pdf) | cdn.teledynelecroy.com | B02 |
| [Copper Mountain — VNA Error Terms and Calibration Kits (webinar)](https://coppermountaintech.com/wp-content/uploads/2023/07/VNA-Calibration-Kits-Error-Terms-and-Calculation-CMT-Webinar-Slides.pdf) | coppermountaintech.com | M14 |
| [Copper Mountain — TRL Calibration](https://coppermountaintech.com/trl-calibration) | coppermountaintech.com | M14 |
| [Copper Mountain — Eliminating Fixture Effects from Embedded Measurements](https://coppermountaintech.com/eliminating-fixture-effects-from-embedded-measurements) | coppermountaintech.com | M14 |
| [CRAN valytics — 방법 비교를 위한 데밍 회귀](https://cran.r-project.org/web/packages/valytics/vignettes/deming-regression.html) | cran.r-project.org | B11 |
| [CS MANTECH — 반도체 대량 시험의 여러 측면](https://csmantech.org/wp-content/acfrcwduploads/field_5e8cddf5ddd10/post_4597/011.3.pdf) | csmantech.org | B12 |
| [Anritsu 백서 — OTA Testing in 5G NR](https://dl.cdn-anritsu.com/en-gb/test-measurement/files/5G-OTA-testing-V1.pdf) | dl.cdn-anritsu.com | M00 · M10 |
| [Keysight KB — EVM 과 SNR 의 관계 (64-QAM)](https://docs.keysight.com/kkbopen/what-is-the-relationship-between-the-error-vector-magnitude-and-the-signal-to-noise-ratio-for-a-64-qam-signal-589738547.html) | Keysight | M13 |
| [Keysight KB — Automate Keysight Instruments Using Python](https://docs.keysight.com/kkbopen/getting-started-automate-keysight-instruments-using-python-3-9-845872587.html) | Keysight | M16 |
| [Keysight — 정확한 프로빙을 위한 절차](https://docs.keysight.com/kkbopen/quick-steps-to-accurate-oscilloscope-probing-589314568.html) | Keysight | B02 |
| [Sensors — 5G 스마트워치 OTA 측정 격자 최적화](https://doi.org/10.3390/s25103185) | doi.org | B09 |
| [NI — DPD 와 동적 전원 아래에서의 PA 시험](https://download.ni.com/evaluation/coretest/RFIC%20White%20Paper%20Series_Part%202.pdf) | download.ni.com | B04 |
| [NI — 잡음지수 측정](https://download.ni.com/evaluation/rf/VSA_Noise_Figure_Measurements.pdf) | download.ni.com | B05 |
| [TI — mmWave Hardware Design Guide](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/1023/2526.mmWave_5F00_hw_5F00_design_5F00_guide_5F00_rev_5F00_9.pdf) | e2e.ti.com | M02 · M17 |
| [EDN — 오실로스코프 프로브의 이해와 최적화](https://edn.com/oscilloscope-probes-understand-and-optimize) | edn.com | B02 |
| [EDN — 다중 사이트 시험의 과제](https://edn.com/the-challenge-of-multisite-test) | edn.com | B12 |
| [Electronic Design — 동시 시험 효율 탐구](https://electronicdesign.com/21201909) | electronicdesign.com | B12 |
| [Elite — CISPR 11 시험 입문](https://elitetest.com/blog/emc-emi-testing/introduction-to-cispr-11-emc-testing) | elitetest.com | B07 |
| [Keysight/IEEE EMC — Fixture De-embedding Techniques and Tools using VNA](https://emcsociety.org/wp-content/uploads/2023/03/20230316-IEEE-EMC_-VNA-De-embeding_Keysight.pdf) | emcsociety.org | M14 |
| [Steer, Microwave and RF Design I — Radio Systems (LibreTexts, 무료 공개)](https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_I_-_Radio_Systems_(Steer)) | LibreTexts (Steer 교재) | M00 · M01 · M10 · M12 |
| [Steer, Microwave and RF Design II — Transmission Lines](https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_II_-_Transmission_Lines_(Steer)) | LibreTexts (Steer 교재) | M02 · M06 |
| [Steer, Microwave and RF Design III — Networks](https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_III_-_Networks_(Steer)) | LibreTexts (Steer 교재) | M03 |
| [Steer, Microwave and RF Design IV — Modules](https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_IV:_Modules_(Steer)) | LibreTexts (Steer 교재) | M06 · M07 |
| [Steer, Microwave and RF Design V — Amplifiers and Oscillators, §2.6 Amplif](https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_V:_Amplifiers_and_Oscillators_(Steer)/02:_Linear_Amplifiers/2.06:_Amplifier_Stability) | LibreTexts (Steer 교재) | M08 |
| [Steer, Microwave and RF Design V, §2.4 Amplifier Efficiency](https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_V:_Amplifiers_and_Oscillators_(Steer)/02:_Linear_Amplifiers/2.04:_Amplifier_Efficiency) | LibreTexts (Steer 교재) | M08 |
| [Focus Microwaves — 펄스 IV 로 본 트랩 동역학](https://focus-microwaves.com/wp-content/uploads/2025/05/PIV-distortion-characterization-V01.pdf) | focus-microwaves.com | B04 |
| [Focus Microwaves — Active Load Pull](https://focus-microwaves.com/applications/active-load-pull) | focus-microwaves.com | B04 |
| [Qucs-RFlayout — openEMS 연동 튜토리얼](https://github.com/thomaslepoix/Qucs-RFlayout/blob/master/doc/tutorials/openems.md) | github.com | M07 · M17 |
| [Keysight 89600 VSA Help — EVM 정의](https://helpfiles.keysight.com/csg/89600B/Webhelp/Subsystems/digdemod/content/digdemod_symtblerrdata_evm.htm) | Keysight | M13 |
| [Keysight — TRL and LRM Calibration](https://helpfiles.keysight.com/csg/N1930xB/VNACalAndMeas/TRL_and_LRM_Calibration.htm) | Keysight | M14 |
| [Keysight — NPR 측정 튜토리얼](https://helpfiles.keysight.com/csg/e5080b/Tutorials/Noise_Power_Ratio_(NPR)_Measurement.htm) | Keysight | B04 |
| [High Frequency Electronics — 잡음지수 불확도의 통계적 접근](https://highfrequencyelectronics.com/index.php?option=com_content&view=article&id=1309:noise-figure-measurement-uncertainty-a-statistical-approach&catid=131&Itemid=189) | highfrequencyelectronics.com | B05 |
| [Univ. of Cincinnati — Noise Figure Circles](https://homepages.uc.edu/~ferendam/Courses/EE_611/Amplifier/NFC.html) | homepages.uc.edu | B05 |
| [US10393786 — 무작위 조정 측정점 기반 OTA 시험](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10393786) | image-ppubs.uspto.gov | B09 |
| [In Compliance — 근접장 프로브로 방사를 해석하기](https://incompliancemag.com/emc-bench-notes-interpreting-emissions-using-a-near-field-probe) | incompliancemag.com | B07 |
| [In Compliance — 케이블의 차동·공통모드 전류 측정](https://incompliancemag.com/measuring-differential-and-common-mode-current-radiation-from-cables) | incompliancemag.com | B07 |
| [In Compliance — 변조가 얽힌 경우의 클럭 듀티 조정을 통한 디센스 완화](https://incompliancemag.com/clock-duty-cycle-tuning-for-desense-mitigation-in-modulation%E2%80%91involved-cases) | incompliancemag.com | B10 |
| [Interference Technology — 1/3/5/10/30 m 방사 측정](https://interferencetechnology.com/emc-radiated-emission-measurements-1351030-meters) | interferencetechnology.com | B07 |
| [Interference Technology — 플랫폼 간섭의 측정과 완화](https://interferencetechnology.com/platform-interference-measurement-mitigation) | interferencetechnology.com | B10 |
| [Keysight AN 57-1 / 5952-8255 — Fundamentals of RF and Microwave Noise Figu](https://keysight.com/us/en/assets/7018-06808/application-notes/5952-8255.pdf) | Keysight | M01 · M08 · M12 |
| [Keysight Application Note 150 — Spectrum Analysis Basics](https://keysight.com/us/en/assets/7018-06714/application-notes/5952-0292.pdf) | Keysight | M04 · M05 |
| [Keysight AN 5965-7709 — Applying Error Correction to VNA Measurements](https://keysight.com/us/en/assets/7018-06761/application-notes/5965-7709.pdf) | Keysight | M04 · M05 · M14 |
| [Keysight blog — Spectrum Analysis Basics Part 3: Detector Types](https://keysight.com/blogs/en/tech/rfmw/2020/07/31/spectrum-analysis-basics-part-3-detector-types) | Keysight | M05 |
| [Keysight — How To Use A Spectrum Analyzer](https://keysight.com/used/us/en/knowledge/guides/how-to-use-a-spectrum-analyzer) | Keysight | M05 |
| [Keysight AN 5991-2069 — Phase Noise Measurement Methods and Techniques](https://keysight.com/us/en/assets/7018-03875/application-notes/5991-2069.pdf) | Keysight | M09 |
| [Keysight AN 5989-4840 — Specifying Calibration Standards and Kits](https://keysight.com/us/en/assets/7018-01375/application-notes/5989-4840.pdf) | Keysight | M14 |
| [Keysight AN 5952-3706 — Noise Figure Measurement Accuracy: The Y-Factor Me](https://keysight.com/us/en/assets/7018-06829/application-notes/5952-3706.pdf) | Keysight | M15 |
| [Keysight — How to Perform Cross-Correlation Phase Noise Measurements](https://keysight.com/us/en/use-cases/perform-cross-correlation-phase-noise-measurements.html) | Keysight | M15 |
| [Keysight 백서 5992-4268 — Instrument Automation with Python](https://keysight.com/us/en/assets/7018-06894/white-papers/5992-4268.pdf) | Keysight | M16 |
| [Keysight — 이중 디랙 모델, RJ/DJ, Q-scale](https://keysight.com/us/en/assets/7018-01309/white-papers/5989-3206.pdf) | Keysight | B02 |
| [Keysight — 변조 신호로 PA 시험하기](https://keysight.com/us/en/use-cases/test-power-amplifiers-with-modulated-signals.html) | Keysight | B04 |
| [Keysight N7614B — PA CFR·DPD·ET 시험](https://keysight.com/us/en/assets/7018-04503/technical-overviews/5991-4959.pdf) | Keysight | B04 |
| [KiCad 공식 사이트](https://kicad.org) | kicad.org | M17 |
| [LBA Group — RF 간섭 탐색과 상호변조 연구](https://lbagroup.com/services/rf-interference-finders-intermodulation-studies-expert-remediation) | lbagroup.com | B10 |
| [LearnEMC — 케이블 공통모드 EMI 계산기](https://learnemc.com/ext/calculators/mremc/cmode.php) | learnemc.com | B07 |
| [NC State University Libraries 프로젝트 페이지](https://lib.ncsu.edu/projects/microwave-and-rf-design-open-textbook) | lib.ncsu.edu | M00 |
| [Marki Microwave — Mixer Basics Primer](https://markimicrowave.com/assets/c2c4688b-15c7-4421-a703-254cb238f9fb/Mixer_Basics_Primer.pdf) | markimicrowave.com | M09 |
| [Marki Microwave — 위상잡음-지터 계산기](https://markimicrowave.com/technical-resources/tools/phase-noise-jitter-calculator) | markimicrowave.com | B06 |
| [MathWorks — What Is a Link Budget?](https://mathworks.com/discovery/link-budget.html) | mathworks.com | M10 |
| [MathWorks — IEEE P370 활용](https://mathworks.com/help/rf/ug/applications-of-ieee-370.html) | mathworks.com | B03 |
| [MathWorks — ieee370QualityCheckFrequencyDomain](https://mathworks.com/help/rf/ref/ieee370qualitycheckfrequencydomain.html) | mathworks.com | B03 |
| [Maury Microwave — Noise By the Numbers](https://maurymw.com/wp-content/uploads/Noise_By_the_Numbers_web2.pdf) | maurymw.com | M01 |
| [Maury Microwave — Practical Guide to Load Pull Measurements](https://maurymw.com/looking-for-a-practical-guide-to-load-pull-measurements-download-our-ebook) | maurymw.com | M15 |
| [Maury Microwave — 펄스 IV 측정 시스템](https://maurymw.com/wp-content/uploads/ims-2025-demo-pulsed-iv-measurement-system-traps-thermal-effects.pdf) | maurymw.com | B04 |
| [Microwave Journal — Calculating Mismatch Uncertainty](https://microwavejournal.com/articles/6166-calculating-mismatch-uncertainty) | microwavejournal.com | M14 |
| [Microwave Journal — Cross Correlation in Phase Noise Analysis](https://microwavejournal.com/articles/10616-cross-correlation-in-phase-noise-analysis) | microwavejournal.com | M15 |
| [Microwave Journal — 펄스 IV·펄스 S-파라미터](https://microwavejournal.com/articles/17337-pulsed-iv-pulsed-s-parameters-and-compact-transistor-models) | microwavejournal.com | B04 |
| [Microwave Journal — 로드풀 시스템의 장단점](https://microwavejournal.com/blogs/10-tek-talk/post/17056-load-pull-system-pros-and-cons) | microwavejournal.com | B04 |
| [Microwave Journal — 잡음 파라미터 측정의 이해](https://microwavejournal.com/articles/7506-understanding-noise-parameter-measurement) | microwavejournal.com | B05 |
| [Microwave Journal — 위상잡음·지터·단기 안정도의 상호관계](https://microwavejournal.com/articles/39449-the-trinity-of-inaccuracy-phase-noise-jitter-and-short-term-stability-what-everyone-should-know-about-their-measurement-and-interrelationships?page=3) | microwavejournal.com | B06 |
| [Microwaves101 — Microstrip](https://microwaves101.com/encyclopedias/microstrip) | Microwaves101 | M02 |
| [Microwaves101 — S-parameters](https://microwaves101.com/encyclopedias/s-parameters) | Microwaves101 | M03 |
| [Microwaves101 — 백과사전](https://microwaves101.com/encyclopedias) | Microwaves101 | M06 |
| [Microwaves101 — Noise Figure](https://microwaves101.com/encyclopedias/noise-figure) | Microwaves101 | M08 |
| [Microwaves101 — Noise Parameters](https://microwaves101.com/encyclopedias/noise-parameters) | Microwaves101 | M08 |
| [Mini-Circuits AN00-008 — Improve Two-Tone, Third-Order Intermodulation Tes](https://minicircuits.com/app/AN00-008.pdf) | Mini-Circuits | M07 · M08 · M15 |
| [Mini-Circuits AN00-009 — Understanding Mixers: Terms Defined and Measuring](https://minicircuits.com/app/AN00-009.pdf) | Mini-Circuits | M09 |
| [Mini-Circuits AN00-010 — How to Select a Mixer](https://minicircuits.com/app/AN00-010.pdf) | Mini-Circuits | M09 |
| [TRQ 시리즈 4/8 in-lb 렌치](https://minicircuits.com/WebStore/Wrenches.html) | Mini-Circuits | 부록 D |
| [Mini-Circuits AN60-040 — 잡음 파라미터 측정의 이해](https://minicircuits.com/appdoc/AN60-040.html) | Mini-Circuits | B05 |
| [Copper Mountain — What is the 12-Term VNA Calibration Model?](https://mwrf.com/technologies/test-measurement/article/21277729/copper-mountain-technologies-what-is-the-12-term-vna-calibration-model) | mwrf.com | M14 |
| [Rohde & Schwarz / Microwaves & RF — Understanding Phase-Noise Measurement ](https://mwrf.com/technologies/test-measurement/article/21268395/rohde-schwarz-understanding-phase-noise-measurement-techniques) | mwrf.com | M15 |
| [Microwaves & RF — 펄스 I-V 로 RF 소자 특성화](https://mwrf.com/test-and-measurement/use-pulse-i-v-testing-characterize-rf-devices) | mwrf.com | B04 |
| [Microwaves & RF — 로드풀 방식 비교](https://mwrf.com/technologies/test-measurement/article/21146075/pasternack-enterprises-comparing-load-pull-testing-methods) | mwrf.com | B04 |
| [Microwaves & RF — 로드풀 방식의 평가](https://mwrf.com/active-components/appraising-different-load-pull-approaches) | mwrf.com | B04 |
| [Microwaves & RF — 임피던스 튜닝 101](https://mwrf.com/technologies/test-measurement/article/21845996/impedance-tuning-101) | mwrf.com | B04 |
| [Microwaves & RF — GaN HEMT 의 올바른 바이어스 시퀀싱](https://mwrf.com/analog-semiconductors/apply-proper-bias-sequencing-gan-hemts) | mwrf.com | B08 |
| [Narda-MITEQ — Q&A about Image Rejection Mixers](https://nardamiteq.com/docs/Q&A%20IRM%20254-257.PDF) | nardamiteq.com | M09 |
| [NXP AN1997 — LNA design for CDMA front end](https://nxp.com/docs/en/application-note/LNA97.pdf) | nxp.com | M03 · M08 |
| [2× Thru 디임베딩의 난점](https://ojs.wiserpub.com/index.php/JEEE/article/download/6598/3214) | ojs.wiserpub.com | B03 |
| [openEMS 공식 사이트](https://openems.de) | openems.de | M17 |
| [HMC E157 Lecture 13: Stability](https://pages.hmc.edu/mspencer/e157/fa23/slides/13.pdf) | pages.hmc.edu | M08 |
| [CN107817391B — TIS 고속 측정법](https://patents.google.com/patent/CN107817391B/en) | patents.google.com | B09 |
| [HUBER+SUHNER SMA 카탈로그: 권장 0.45 N·m ≈ 4.0 in-lb](https://pdf.directindustry.com/pdf/huber-suhner/series-sma-coaxial-connectors/30583-293489.html) | pdf.directindustry.com | M04 · 부록 D |
| [PyVISA — SCPI Commands](https://pyvisa.org/docs/scpi-commands-python) | pyvisa.org | M16 |
| [PyVISA — Communicating with your instrument](https://pyvisa.readthedocs.io/en/latest/introduction/communication.html) | pyvisa.readthedocs.io | M16 |
| [Qorvo — BAW vs. SAW RF Filters](https://qorvo.com/design-hub/blog/baw-vs-saw-rf-filters) | qorvo.com | M07 |
| [Understanding Noise Figure (기술노트)](https://qsl.net/va3iul/Noise/Understanding%20Noise%20Figure.pdf) | qsl.net | M01 |
| [Quality Magazine — 측정 시스템 분석](https://qualitymag.com/articles/97565-measurement-systems-analysis) | qualitymag.com | B01 |
| [Radioengineering — 복소 다중톤의 파고율 최적화](https://radioeng.cz/fulltexts/2023/23_02_0264_0272.pdf) | radioeng.cz | B04 |
| [IEEE — 마이크로파 증폭기의 2-tone IMD 비대칭](https://researchgate.net/publication/3860521_Two-tone_IMD_asymmetry_in_microwave_amplifiers) | researchgate.net | B04 |
| [기저대역 임피던스가 FET 상호변조에 미치는 영향](https://researchgate.net/publication/3130167_Effect_of_baseband_impedance_on_FET_intermodulation) | researchgate.net | B04 |
| [Simplifying and Interpreting Two-Tone Measurements](https://researchgate.net/publication/3130670_Simplifying_and_Interpreting_Two-Tone_Measurements) | researchgate.net | B04 |
| [New Trends for Nonlinear Measurement of High-Power RF Transistors](https://researchgate.net/publication/241638509_New_Trends_for_the_Nonlinear_Measurement_and_Modeling_of_High-Power_RF_Transistors_and_Amplifiers_With_Memory_Effects) | researchgate.net | B04 |
| [Adaptive DPD Based on Memory Polynomial and ILA](https://researchgate.net/publication/351830085_Adaptive_Digital_Predistortion_of_RF_Power_Amplifiers_Based_on_Memory_Polynomial_Model_and_Indirect_Learning_Architecture) | researchgate.net | B04 |
| [IEEE — 펄스·CW 용 GaN HEMT 바이어스 시퀀스 회로 설계](https://researchgate.net/publication/261397813_Design_and_implementation_of_bias_sequence_circuits_for_GaN_HEMT_amplifiers_both_pulsed_and_CW_applications) | researchgate.net | B08 |
| [Cadence — 드레인 효율과 PAE](https://resources.pcb.cadence.com/blog/2019-drain-efficiency-vs-power-added-efficiency-pae-and-the-efficiency-assessment-of-rf-devices) | resources.pcb.cadence.com | B08 |
| [RF Filter Technologies For Dummies, Qorvo Special Edition](https://rfmw.com/data/qorvo_rf_filter_technologies.pdf) | rfmw.com | M07 |
| [Qorvo/TriQuint — GaN on SiC HEMT 바이어싱](https://rfmw.com/data/triquint_biasing_gan_on_sic_hemt_devices.pdf) | rfmw.com | B08 |
| [Rohde & Schwarz — Amplifier characterization using load pull](https://rohde-schwarz.com/us/applications/amplifier-characterization-using-load-pull_56279-922304.html) | rohde-schwarz.com | M15 |
| [R&S — 근접장 프로브 고르는 법](https://rohde-schwarz.com/us/products/test-and-measurement/essentials-test-equipment/rs-essentials-digital-oscilloscopes/how-to-choose-a-near-field-probe_256877.html) | rohde-schwarz.com | B07 |
| [R&S — 오실로스코프로 EMI 디버그하기](https://rohde-schwarz.com/us/products/test-and-measurement/essentials-test-equipment/rs-essentials-digital-oscilloscopes/understanding-emi-debugging_254516.html) | rohde-schwarz.com | B07 |
| [R&S — 오실로스코프용 EMC 근접장 프로브](https://rohde-schwarz.com/us/products/test-and-measurement/oscilloscope-probes/emc-near-field-probes-for-oscilloscopes_63493-73798.html) | rohde-schwarz.com | B07 |
| [Campbell Scientific AN 3RF-F — The Link Budget and Fade Margin](https://s.campbellsci.com/documents/us/technical-papers/link-budget.pdf) | s.campbellsci.com | M10 |
| [R&S GFM313 — 5G New Radio Conducted Base Station Transmitter Tests](https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/dl_application/application_notes/gfm313/GFM313_3e_5G_NR_BaseStation_Tx_Tests.pdf) | scdn.rohde-schwarz.com | M13 · M15 |
| [Rohde & Schwarz 1MA178 — The Y Factor Technique for Noise Figure Measureme](https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/dl_application/application_notes/1ma178/1MA178_5e_NoiseFigure.pdf) | scdn.rohde-schwarz.com | B05 · M15 |
| [ScienceDirect — Stability Factor overview](https://sciencedirect.com/topics/engineering/stability-factor) | sciencedirect.com | M08 |
| [ScienceDirect — 진폭 구간별 2-tone 동적 특성](https://sciencedirect.com/science/article/pii/S026322411630094X) | sciencedirect.com | B04 |
| [ScienceDirect — Power Added Efficiency 개요](https://sciencedirect.com/topics/engineering/power-added-efficiency) | sciencedirect.com | B08 |
| [scikit-rf 문서 — Introduction](https://scikit-rf.readthedocs.io/en/latest/tutorials/Introduction.html) | scikit-rf | M03 |
| [scikit-rf 문서](https://scikit-rf.readthedocs.io/en/latest/tutorials/Networks.html) | scikit-rf | M03 · M14 |
| [scikit-rf — IEEEP370 디임베딩 문서](https://scikit-rf.readthedocs.io/en/latest/examples/networktheory/IEEEP370%20Deembedding.html) | scikit-rf | B03 |
| [scikit-rf — LNA 예제](https://scikit-rf.readthedocs.io/en/latest/examples/networktheory/LNA%20Example.html) | scikit-rf | B05 |
| [Richardson RFPD — GaN HEMT 바이어스 시퀀싱과 온도 보상](https://shop.richardsonrfpd.com/docs/rfpd/gan_hemt_bias_seqnc.pdf) | shop.richardsonrfpd.com | B08 |
| [Nitronex/Richardson — GaN Essentials 바이어싱 응용 노트](https://shop.richardsonrfpd.com/docs/rfpd/Nitronex_GaN_Biasing_App%20Note.pdf) | shop.richardsonrfpd.com | B08 |
| [Siglent — Spectrum Analyzer Basics: Bandwidth](https://siglenteu.com/application-note/spectrum-analyzer-basics-bandwidth) | siglenteu.com | M05 |
| [Siglent — 근접장·전류 프로브를 쓴 EMC 문제 해결](https://siglentna.com/application-note/electromagnetic-compliance-troubleshooting-near-field-current-probes) | siglentna.com | B07 |
| [Signal Integrity Journal — IEEE P370 표준 소개](https://signalintegrityjournal.com/articles/1169-ieee-p370-a-ffixture-ddesign-and-ddata-qquality-mmetric-sstandard-for-iinterconnects-up-to-50-ghz) | signalintegrityjournal.com | B03 |
| [Signal Integrity Journal — P370 실무 적용](https://signalintegrityjournal.com/articles/1185-practical-application-of-the-ieee-p370-standard-for-measurement-of-interconnects-up-to-50-ghz) | signalintegrityjournal.com | B03 |
| [Signal Integrity Journal — 자기생성 간섭 특성화의 3단계 절차](https://signalintegrityjournal.com/blogs/17-practical-emc/post/3281-a-three-step-process-for-characterizing-self-generated-interference-for-wireless-or-iot-products) | signalintegrityjournal.com | B10 |
| [Signal Integrity Journal — 무선·IoT 제품의 EMI 특성화와 디버그](https://signalintegrityjournal.com/articles/1335-characterizing-debugging-emi-issues-for-wireless-and-iot-products) | signalintegrityjournal.com | B10 |
| [SIMCO — 4:1 교정비의 역사와 의미](https://simco.com/blog/4-1-calibration-ratio) | simco.com | B12 |
| [SiTime AN10062 — Phase Noise Measurement Guide for Oscillators](https://sitime.com/support/resource-library/application-notes/an10062-phase-noise-measurement-guide-oscillators) | sitime.com | M09 |
| [Tektronix — Noise Figure: Overview of Noise Measurement Methods](https://tek.com/en/documents/whitepaper/noise-figure-overview-noise-measurement-methods) | tek.com | M15 |
| [Tektronix — Decision Rule Guide](https://tek.com/en/documents/service/tektronix-decision-rule-guide) | tek.com | M16 |
| [Teledyne LeCroy — 수동 프로브 접지 리드의 영향](https://teledynelecroy.com/oscilloscope/blog/the-effects-of-passive-probe-ground-leads) | teledynelecroy.com | B02 |
| [TI SNAA329 — 12-GHz Direct Conversion Receiver With LMX8410L I/Q Demodulat](https://ti.com/lit/pdf/snaa329) | ti.com | M11 |
| [Times Microwave Systems — Connector Torque Requirements](https://timesmicrowave.com/connector-torque-requirements) | timesmicrowave.com | M04 · 부록 D |
| [Toyotech — IoT 무선 기기의 OTA 측정: 과제와 해법](https://toyotechus.com/wp-content/uploads/OTA-Measurement-for-IoT-Wireless-Device-Performance-Evaluation-Challenges-and-Solutions.pdf) | toyotechus.com | B09 |
| [UCSB ECE145A — 저잡음 증폭기 설계](https://web.ece.ucsb.edu/~long/ece145a/LNAdesign.pdf) | web.ece.ucsb.edu | B05 |
| [WRC — CTIA/Verizon 인증 OTA 시험소](https://wrc-nc.org/our-services/ctia-verizon-authorized-ota-testing-lab) | wrc-nc.org | B09 |
| [Advantest — 다중 사이트 효율과 처리량](https://www3.advantest.com/documents/11348/d05328f9-2d91-4372-9a13-8344373c03b4) | www3.advantest.com | B12 |

---

## C.5 등급 C — 교육 사이트 (36개)

*정리가 잘 된 공개 교육 자료. 원문 확인이 필요할 때가 있다*

| 출처 | 발행 주체 | 쓴 모듈 |
|---|---|---|
| [All About Circuits — PA 메모리 효과 입문](https://allaboutcircuits.com/technical-articles/introduction-to-the-memory-effect-in-rf-power-amplifiers) | allaboutcircuits.com | B04 |
| [All About Circuits — 단방향 LNA 설계](https://allaboutcircuits.com/technical-articles/learn-about-designing-unilateral-low-noise-amplifiers) | allaboutcircuits.com | B05 |
| [All About Circuits — Y 계수법의 잡음원 불확도와 픽스처 손실](https://allaboutcircuits.com/technical-articles/noise-figure-measurement-using-the-y-factor-method-noise-source-uncertainty-and-fixturing-losses) | allaboutcircuits.com | B05 |
| [All About Circuits — Y 계수법 살펴보기](https://allaboutcircuits.com/technical-articles/explore-the-y-factor-method-for-noise-figure-measurement) | allaboutcircuits.com | B05 |
| [QualityEngineer.ai — %GRR·NDC 합격 기준](https://app.qualityengineer.ai/blog/gauge-rr-acceptance-criteria) | app.qualityengineer.ai | B11 |
| [A Review of Broadband Doherty Power Amplifier Design (arXiv 1908.07755)](https://arxiv.org/pdf/1908.07755) | arXiv | M08 |
| [Rubiola — The Leeson effect (arXiv physics/0502143)](https://arxiv.org/pdf/physics/0502143) | arXiv | M09 |
| [arXiv 2508.16735 — S-Band Image-Rejecting Dual-Conversion Superheterodyne ](https://arxiv.org/pdf/2508.16735) | arXiv | M09 |
| [arXiv 2407.09944 — 5G FR2 mmWave Antenna Array OTA Measurements Using a CA](https://arxiv.org/pdf/2407.09944) | arXiv | M10 |
| [CalibrationOS — Gage R&R 절차와 합격 기준 (AIAG MSA)](https://calibrationos.com/learn/gage-rr-study-procedure) | calibrationos.com | B01 · B11 |
| [element14 — 프로브 부하 어림법](https://community.element14.com/technologies/test-and-measurement/b/blog/posts/oscilloscope-probe-loading-rule-of-thumbs) | community.element14.com | B02 |
| [UIUC ECE329 Lecture 37 — Smith Chart and Impedance Matching](https://courses.grainger.illinois.edu/ece329/sp2021/Lecture_notes/329lect37-L39.pdf) | courses.grainger.illinois.edu | M03 |
| [Wikipedia — Modified Allan variance](https://en.wikipedia.org/wiki/Modified_Allan_variance) | en.wikipedia.org | B06 |
| [Wikipedia — Common mode current](https://en.wikipedia.org/wiki/Common_mode_current) | en.wikipedia.org | B07 |
| [HWE Design — RF 디센스](https://hwe.design/system-testing/system-coexistence/rf-desense) | hwe.design | B10 |
| [IEEE TMTT — A Combined Approach to DPD and CFR](https://ieeexplore.ieee.org/document/6353232) | ieeexplore.ieee.org | M13 |
| [ISOBudgets — Guard Banding: How to Take Uncertainty Into Account](https://isobudgets.com/guard-banding-how-to-take-uncertainty-into-account) | isobudgets.com | B12 · M16 |
| [ISOBudgets — Statements of Conformity and Decision Rules for ISO 17025](https://isobudgets.com/statements-of-conformity-and-decision-rules) | isobudgets.com | M16 |
| [IJMQE — Importance and Estimation of Mismatch Uncertainty for RF Parameter](https://metrology-journal.org/articles/ijmqe/pdf/2012/01/ijmqe120005.pdf) | metrology-journal.org | M14 |
| [Kikkert, RF Electronics Ch.8 — Amplifiers: Stability, Noise and Gain](https://mwl.diet.uniroma1.it/people/pisa/SISTEMI_RF/MATERIALE%20INTEGRATIVO/Kikkert_RF_Electronics_Course/11-RF_Electronics_Kikkert_Ch8_AmplifierStabilityNoise.pdf) | mwl.diet.uniroma1.it | M03 · M08 |
| [W5LUA, Stability & LNAs (Microwave Update)](https://ntms.org/files/MUD2011/MUD_W5LUA_LNAs_Web.pdf) | ntms.org | M08 |
| [Gary Breed — There's Nothing Magic About 50 Ohms](https://ptacts.uspto.gov/ptacts/public-informations/petitions/1556705/download-documents?artifactId=zZcqPwdS9RS22BDkL4Gc28WNLtSHEbJT-SOD11KzDToEyYTpMFI3XDU) | ptacts.uspto.gov | M02 |
| [B. Razavi, Design Considerations for Direct-Conversion Receivers](https://ptacts.uspto.gov/ptacts/public-informations/petitions/1463055/download-documents?artifactId=qRj6sOyeSMWSL2I1rrtmY-0NtOx5e04SNC3XR5V19X5mqBfXSEuTaT4) | ptacts.uspto.gov | M11 |
| [Chalmers 학위논문 — Design and Realization of a 6 GHz Doherty PA from Load-pul](https://publications.lib.chalmers.se/records/fulltext/225989/225989.pdf) | publications.lib.chalmers.se | M08 |
| [VA3IUL — LNA Design](https://qsl.net/va3iul/LNA%20Design/LNA_design.htm) | qsl.net | M08 |
| [Rahsoft — RF 시스템의 PAE](https://rahsoft.com/2024/02/29/power-added-efficiency-pae-in-rf-systems) | rahsoft.com | B08 |
| [Dj 가 DDj 보다 작을 수 있는 이유](https://redeweb.com/en/articulos/instrumentacion/entendiendo-el-calculo-del-jitter-por-que-dj-puede-ser-menor-que-ddj-o-pj) | redeweb.com | B02 |
| [Watkins-Johnson Tech Note — Image-Reject and Single-Sideband Mixers](https://rfcafe.com/references/articles/wj-tech-notes/image-reject-ssb-mixers-v12-3.pdf) | rfcafe.com | M09 |
| [RF Essentials — 신호 대역폭과 메모리 효과](https://rfessentials.com/rf-knowledge-base/how-does-the-signal-bandwidth-affect-the-memory-effects-in-a-power-amplifier) | rfessentials.com | B04 |
| [RF Wireless World — NPR 측정의 장단점](https://rfwireless-world.com/test-and-measurement/Advantages-and-Disadvantages-of-NPR-Measurement.html) | rfwireless-world.com | B04 |
| [RF Wireless World — PAE 계산기](https://rfwireless-world.com/calculators/rf-amplifier-pae-calculator) | rfwireless-world.com | B08 |
| [Ricketts Lab — Double Balanced Mixer Theory](https://rickettslab.org/bits2waves/design/mixer-discrete/double-balanced-mixer) | rickettslab.org | M09 |
| [SATRA — Uncertainty, ISO/IEC 17025:2017 and decisions made on conformity](https://satra.com/spotlight/article.php?id=546) | satra.com | M16 |
| [SigmaDesk — Gage R&R / MSA 연구 해설](https://sigmadesk.app/blog/msa-gage-rr) | sigmadesk.app | B11 |
| [Signal Hound — Phase Noise Measurement: A Complete Guide](https://signalhound.com/rf-measurement-fundamentals/phase-noise-measurement) | signalhound.com | M15 |
| [USPAS — Impedance Matching and Smith Charts (Staples, LBNL)](https://uspas.fnal.gov/materials/08UCSC/mml13_matching+smith_chart.pdf) | uspas.fnal.gov | M03 |

---

## C.6 등급 D — 블로그·개인 (44개)

*유용하지만 단독 근거로 쓰지 않는다. 교차검증 필수*

| 출처 | 발행 주체 | 쓴 모듈 |
|---|---|---|
| [All About Circuits — Understanding the RF Noise Figure Specification](https://allaboutcircuits.com/technical-articles/understanding-the-noise-figure-specification) | allaboutcircuits.com | M01 |
| [All About Circuits — RF Amplifier Stability Factors and Stabilization Tech](https://allaboutcircuits.com/technical-articles/rf-amplifier-stability-tests-and-stabilization-techniques) | allaboutcircuits.com | M08 |
| [All About Circuits — A Guide to Calculating IM3 and IP3 for Nonlinear RF C](https://allaboutcircuits.com/technical-articles/a-guide-to-calculating-im3-and-ip3-for-nonlinear-rf-circuits) | allaboutcircuits.com | M08 |
| [All About Circuits — Understanding the 12-Term Error Model and SOLT](https://allaboutcircuits.com/technical-articles/understanding-the-12-term-error-model-and-solt-calibration-method-for-vna-measurements) | allaboutcircuits.com | M14 |
| [Antenna Test Lab — Return Loss and VSWR Explained](https://antennatestlab.com/antenna-education-tutorials/return-loss-vswr-explained) | antennatestlab.com | M02 · M10 |
| [AtlasPCB — RF Via Stitching and Ground Plane Isolation](https://atlaspcb.com/blog/rf-via-stitching-ground-plane-isolation) | atlaspcb.com | M17 |
| [C&E — ETSI EN 301 489 시험 개요](https://celectronics.com/International-Compliance/ETSI-EN-301-489-Testing) | celectronics.com | M17 · 캡스톤 |
| [Centric RF Torque Specifications](https://centricrf.com/torque-specifications) | centricrf.com | 부록 D |
| [Cross Technologies — P1dB vs. OIP3 Relationship](https://crosstechnologies.com/technical/P1dB%20vs%20OIP3%20Relationship.pdf) | crosstechnologies.com | M08 |
| [Data Alliance — SMA/RP-SMA 토크 등급](https://data-alliance.net/blog/torque-ratings-of-sma-and-rpsma-antenna-cable-connectors-adapters) | data-alliance.net | 부록 D |
| [EDN — Via spacing on high-performance PCBs](https://edn.com/via-spacing-on-high-performance-pcbs) | edn.com | M17 |
| [EECL RF Cascade Calculator](https://eecl.co.uk/rf-cascade-calculator) | eecl.co.uk | M12 |
| [Electronic Design — Understanding Error Vector Magnitude](https://electronicdesign.com/engineering-essentials/understanding-error-vector-magnitude) | electronicdesign.com | M13 |
| [Electronics Notes — 50Ω vs 75Ω Coax](https://electronics-notes.com/articles/antennas-propagation/rf-feeders-transmission-lines/50ohm-vs-75ohm-coax-cable-reasons-advantages-disadvantages.php) | electronics-notes.com | M02 |
| [Electronics Notes — Double Balanced Mixer](https://electronics-notes.com/articles/radio/rf-mixer/double-balanced-mixer.php) | electronics-notes.com | M09 |
| [Gough's Tech Zone — SCPI Automation with PyVISA](https://goughlui.com/2021/03/28/tutorial-introduction-to-scpi-automation-of-test-equipment-with-pyvisa) | goughlui.com | M16 |
| [Intertek — ETSI EN 300 328 V2.2.2](https://intertek.com/ict/etsi-en-300-328) | intertek.com | M17 · 캡스톤 |
| [Lockheed Martin RF Systems Engineer](https://lockheedmartinjobs.com/job/huntsville/rf-systems-engineer/694/78970220048) | lockheedmartinjobs.com | M00 |
| [Microwave Journal — Open Source EM Simulation Software](https://microwavejournal.com/articles/44778-open-source-em-simulation-software-curated-by-katerina-galitskaya) | microwavejournal.com | M07 |
| [Microwave Journal — Connector Torque Requirements](https://microwavejournal.com/articles/1064-connector-torque-requirements) | microwavejournal.com | 부록 D |
| [Microwaves & RF — Narrowing Choices For RF/MW Filters](https://mwrf.com/technologies/components/article/21843442/narrowing-choices-for-rf-mw-filters) | mwrf.com | M07 |
| [Microwaves & RF — Increasing SFDR in Software-Defined Radios](https://mwrf.com/technologies/embedded/systems/article/21162308/precision-receivers-increasing-sfdr-in-software-defined-radios) | mwrf.com | M11 |
| [NuWaves — Choosing the Best RF Filter](https://nuwaves.com/choose-best-rf-filter) | nuwaves.com | M07 |
| [Sierra Circuits — RF PCB Via Design Challenges](https://protoexpress.com/blog/rf-pcb-via-design-challenges-with-layout-solutions) | protoexpress.com | M17 |
| [R&L Electronics](https://randl.com/index.php?main_page=product_info&products_id=75145) | randl.com | 부록 D |
| [Renhotec — Ultimate Guide to SMA/3.5/2.92/2.4/1.85/1 mm](https://renhotecrf.com/products/rf-connector-cable/the-ultimate-guide-to-sma-3-5mm-2-92mm-2-4mm-1-85mm-1mm-connectors-demystifying-differences-and-compatibility.html) | renhotecrf.com | M04 |
| [Altium — The Mysterious 50 Ohm Impedance](https://resources.altium.com/p/mysterious-50-ohm-impedance-where-it-came-and-why-we-use-it) | resources.altium.com | M02 |
| [Altium — RF PCB Design Guidelines for Digital Engineers](https://resources.altium.com/p/digital-engineers-guide-rf-pcb-layout-and-routing) | resources.altium.com | M17 |
| [Cadence — Quarter-Wave Transformers: Theory and Equations](https://resources.system-analysis.cadence.com/blog/msa2023-quarter-wave-transformer-theory-and-equations) | resources.system-analysis.cadence.com | M03 |
| [NanoVNA 입문 가이드](https://rfcharge.com/blogs/industry-technology-insights/nanovna-complete-beginner-guide) | rfcharge.com | M05 |
| [LenoRF 토크 가이드](https://rfcnn.com/blog/rf-connector-torque-guide-sma-n-3-5mm-2-92mm-4-3-10) | rfcnn.com | 부록 D |
| [RF Com — Mating 3.5mm, 2.92mm, SMA, 2.4mm and 1.85mm Connectors](https://rfcom.co.uk/mating-3-5mm-2-92mm-sma-2-4mm-and-1-85mm-connectors-a-comprehensive-guide) | rfcom.co.uk | M04 |
| [RF Essentials — Noise Matching](https://rfessentials.com/resources/rf-glossary/noise-matching) | rfessentials.com | M08 |
| [RF Essentials — TRL vs SOLT](https://rfessentials.com/rf-knowledge-base/what-is-the-difference-between-a-trl-calibration-and-a-solt-calibration-and-when) | rfessentials.com | M14 |
| [RF Essentials — Port Extension](https://rfessentials.com/rf-knowledge-base/what-is-the-port-extension-feature-on-a-vna-and-when-should-i-use-it) | rfessentials.com | M14 |
| [RF Essentials — Two-Tone IP3 Measurement Setup](https://rfessentials.com/rf-knowledge-base/what-is-the-correct-setup-for-measuring-two-tone-intermodulation-distortion-and-) | rfessentials.com | M15 |
| [RF Essentials — RF PCB Layout: Grounding, Via Fencing, Trace Geometry](https://rfessentials.com/industry-news/rf-design/rf-pcb-layout-grounding) | rfessentials.com | M17 |
| [rftools.io Cascaded NF Calculator](https://rftools.io/calculators/rf/noise-figure-cascade) | rftools.io | M12 |
| [tinySA 소개](https://rtl-sdr.com/the-49-tinysa-spectrum-analyzer) | rtl-sdr.com | M05 · 부록 D |
| [S3 Semi 비교](https://s3semi.com/tinysa-vs-nanovna-how-to-pick-the-right-analyzer-for-your-rf-projects) | s3semi.com | 부록 D |
| [Velvet Jobs — RF Systems Engineer](https://velvetjobs.com/job-descriptions/rf-systems-engineer) | velvetjobs.com | M00 · M16 |
| [Velvet Jobs RF Engineer](https://velvetjobs.com/job-descriptions/rf-engineer) | velvetjobs.com | M00 |
| [Vikram Sekar — Why 50 Ohms Became the RF Standard](https://viksnewsletter.com/p/why-50-ohms-became-the-rf-standard) | viksnewsletter.com | M02 |
| [Vinstronics 비교](https://vinstronics.com/difference-1-85mm-2-4mm-2-92mm-3-5mm-sma-connector) | vinstronics.com | M04 |

---

## C.7 참고 사이트 — 등급 없음 (8개)

> **지침 1의 참고 사이트입니다.** 사실의 근거가 아니라 **무엇을 어떤 순서로 가르칠지**를 참고했습니다. 그래서 등급을 매기지 않았습니다.

| 출처 | 쓴 모듈 |
|---|---|
| [rfdh — RF 트랜시버 시스템의 이해](https://rfdh.com/bas_rf.htm) | M00 · M01 · M06 · M11 |
| [rfdh.com — 50옴을 쓰는 이유는?](https://rfdh.com/bas_rf/begin/50ohm.htm) | M02 |
| [rfdh — Intermodulation의 정체](https://rfdh.com/bas_rf/begin/im.htm) | M08 |
| [rfdh — 믹서](https://rfdh.com/bas_rf/begin/mixer.php3) | M09 |
| [rfdh — 발진기](https://rfdh.com/bas_rf/begin/osc.htm) | M09 |
| [초보만세](https://rfdh.com/bas_rf/beginer.htm) | M00 |
| [rfdh.com — S파라미터](https://rfdh.com/bas_rf/s.htm) | M03 |
| [rfdh.com — RFDB MicroStrip](https://rfdh.com/rfdb/msline.htm) | M02 |

---

## C.8 문서마다 등급이 갈린 출처

없습니다. 같은 출처에는 모든 문서가 같은 등급을 매겼습니다.

---

## C.9 모듈별 색인

| 문서 | 출처 수 | 등급 구성 |
|---|---|---|
| B01 | 2 | B 1 · C 1 |
| B02 | 8 | B 6 · C 2 |
| B03 | 9 | A 2 · B 7 |
| B04 | 27 | A 2 · B 22 · C 3 |
| B05 | 12 | B 9 · C 3 |
| B06 | 10 | A 3 · B 6 · C 1 |
| B07 | 11 | B 10 · C 1 |
| B08 | 9 | B 7 · C 2 |
| B09 | 8 | A 3 · B 5 |
| B10 | 7 | B 6 · C 1 |
| B11 | 7 | B 4 · C 3 |
| B12 | 9 | A 3 · B 5 · C 1 |
| M00 | 9 | - 2 · A 1 · B 3 · D 3 |
| M01 | 6 | - 1 · B 4 · D 1 |
| M02 | 10 | - 2 · B 3 · C 1 · D 4 |
| M03 | 10 | - 1 · B 5 · C 3 · D 1 |
| M04 | 11 | A 2 · B 6 · D 3 |
| M05 | 7 | B 5 · D 2 |
| M06 | 5 | - 1 · B 4 |
| M07 | 9 | B 6 · D 3 |
| M08 | 21 | - 1 · B 11 · C 5 · D 4 |
| M09 | 16 | - 2 · B 9 · C 4 · D 1 |
| M10 | 6 | B 4 · C 1 · D 1 |
| M11 | 6 | - 1 · B 3 · C 1 · D 1 |
| M12 | 7 | B 5 · D 2 |
| M13 | 9 | A 3 · B 4 · C 1 · D 1 |
| M14 | 16 | A 2 · B 10 · C 1 · D 3 |
| M15 | 13 | B 11 · C 1 · D 1 |
| M16 | 11 | A 1 · B 5 · C 3 · D 2 |
| M17 | 15 | A 2 · B 6 · D 7 |
| 부록 D | 12 | A 1 · B 4 · D 7 |
| 캡스톤 | 2 | D 2 |

> 📌 **각 문서의 §S(출처) 절에 그 문서만의 목록과 교차검증 건수가 있습니다.** 여기는 전체를 훑기 위한 색인입니다.

---

## C.10 확인 안내와 한계

> ⚠️ **URL을 직접 열어 확인하지 못했습니다.**
>
> 이 커리큘럼은 조직 네트워크 정책상 **외부 웹사이트 직접 접속이 차단된 환경**에서 작성되었습니다. 모든 사실은 검색 결과의 서지 정보와 요약을 **독립 출처 2곳 이상으로 교차 대조**해 썼지만, **원문을 열어 확인하지는 못했습니다.**
>
> 따라서 다음을 독자가 확인해 주셔야 합니다.
>
> | 확인할 것 | 왜 |
> |---|---|
> | 링크가 살아 있는가 | 제조사 응용노트는 개편 때 주소가 자주 바뀐다 |
> | 인용한 수치가 원문에 있는가 | 요약을 대조했을 뿐이다 |
> | 규격의 개정 여부 | 조항 번호와 한계값은 개정된다 |
> | 가격·재고 정보 | 시점에 따라 크게 변한다 (부록 D) |

> 📌 **이 한계를 감추지 않는 것이 이 커리큘럼의 방침입니다.** 각 모듈의 출처 절에도 같은 안내가 붙어 있습니다. 배경은 [M00.S](../01_모듈/M00_RF시스템엔지니어링이란.md#m00s-출처)에 있습니다.

### 링크 확인 도구

접속이 되는 환경이라면 아래로 한 번에 확인할 수 있습니다.

```bash
# 이 문서의 모든 링크에 HEAD 요청을 보내 죽은 링크를 찾는다
grep -o 'https\?://[^)]*' 03_부록/C_출처_통합목록.md | sort -u | \
  while read u; do
    code=$(curl -s -o /dev/null -w "%{http_code}" -L --max-time 15 "$u")
    [ "$code" = "200" ] || echo "$code  $u"
  done
```

---

## 변경 이력

| 버전 | 일자 | 내용 |
|---|---|---|
| v1.0 | 2026-08-21 | 최초 생성. 고유 출처 282개, 등급 A 21 · B 173 · C 36 · D 44. `gen_appendix_c.py` 로 본문에서 자동 생성 |
