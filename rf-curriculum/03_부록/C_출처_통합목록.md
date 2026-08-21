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
| 고유 출처 | **166개** |
| 인용한 문서 | 20편 |
| 발행 주체 | 92곳 |

### 등급 분포

| 등급 | 개수 | 비율 |
|---|---|---|
| A | 8 | 4.8 % |
| B | 86 | 51.8 % |
| C | 20 | 12.0 % |
| D | 44 | 26.5 % |
| — (참고 사이트, 교육 구성 참고) | 8 | 4.8 % |

> 📌 **등급 D가 적지 않은 것은 의도된 결과입니다.** RF 실무 지식의 상당 부분이 제조사 블로그와 엔지니어 개인 글에 있습니다. 그래서 D는 **단독으로 쓰지 않고 반드시 교차검증**했습니다 — 각 모듈의 출처 표에 교차검증 건수가 적혀 있습니다.

### 발행 주체 상위

| 발행 주체 | 출처 수 |
|---|---|
| Keysight | 14 |
| rfdh.com (참고 사이트) | 8 |
| Analog Devices | 8 |
| Mini-Circuits | 7 |
| LibreTexts (Steer 교재) | 6 |
| allaboutcircuits.com | 5 |
| Microwaves101 | 5 |
| rfessentials.com | 5 |
| mwrf.com | 4 |
| microwavejournal.com | 4 |
| arXiv | 4 |
| eCFR (미국 연방규정) | 3 |
| coppermountaintech.com | 3 |
| velvetjobs.com | 2 |

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

## C.3 등급 A — 1차 표준·규격 (8개)

*표준화 기구·규제기관의 원문. 가장 신뢰도가 높다*

| 출처 | 발행 주체 | 쓴 모듈 |
|---|---|---|
| [3GPP TS 38.101-1 (ATIS 사본, Rel-16)](https://atisorg.s3.amazonaws.com/archive/3gpp-documents/Rel16/ATIS.3GPP.38.101-1.V1640.pdf) | atisorg.s3.amazonaws.com | M00 · M13 |
| [eCFR 47 CFR Part 15](https://ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15) | eCFR (미국 연방규정) | M13 |
| [eCFR — 47 CFR Part 15 Subpart B (비의도적 방사체)](https://ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15/subpart-B) | eCFR (미국 연방규정) | M17 |
| [eCFR — 47 CFR Part 15 Subpart C (의도적 방사체)](https://ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15/subpart-C) | eCFR (미국 연방규정) | M17 |
| [ETSI TS 138 101-5](https://etsi.org/deliver/etsi_ts/138100_138199/13810105/17.05.00_60/ts_13810105v170500p.pdf) | ETSI | M13 |
| [EURAMET Calibration Guide No. 12 — Guidelines on the Evaluation of Vector ](https://euramet.org/Media/news/I-CAL-GUI-012_Calibration_Guide_No._12.web.pdf) | EURAMET | M04 · M14 · M16 |
| [MIL-STD-348](https://everyspec.com/MIL-STD/MIL-STD-0300-0499/download.php?spec=MIL-STD-348B_CHG-1.054027.pdf) | MIL-STD | M04 · 부록 D |
| [NIST — Metrological Traceability](https://nist.gov/metrology/metrological-traceability) | nist.gov | M14 |

---

## C.4 등급 B — 제조사·학술 (86개)

*계측기·부품 제조사의 응용노트와 백서, 대학 교재·논문*

| 출처 | 발행 주체 | 쓴 모듈 |
|---|---|---|
| [Rohde & Schwarz — Understanding Phase Noise Fundamentals (백서)](https://allaboutcircuits.com/uploads/articles/RnS-Understanding-phase-noise-fundamentals_wp.pdf) | allaboutcircuits.com | M09 |
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
| [Knowles — RF Filter Terminology and Specifications](https://blog.knowlescapacitors.com/blog/filter-terminology-and-specifications) | blog.knowlescapacitors.com | M07 |
| [Mini-Circuits — Applying Proper Torque to Microwave Connectors](https://blog.minicircuits.com/applying-proper-torque-to-microwave-connectors) | Mini-Circuits | M04 · 부록 D |
| [Mini-Circuits — Making Good RF Connections](https://blog.minicircuits.com/making-good-rf-connections-best-practices-and-the-role-of-anti-torque-connectors) | Mini-Circuits | M04 |
| [Mini-Circuits 블로그 — 같은 내용](https://blog.minicircuits.com/improve-two-tone-third-order-intermodulation-testing) | Mini-Circuits | M15 |
| [Rohde & Schwarz 백서 — Understanding EVM (Denisowski)](https://cdn.rohde-schwarz.com.cn/pws/dl_downloads/premiumdownloads/premium_dl_pdm_downloads/3683_8038_52/Understanding-EVM_wp_en_3683-8038-52_v0100.pdf) | cdn.rohde-schwarz.com.cn | M13 |
| [Copper Mountain — VNA Error Terms and Calibration Kits (webinar)](https://coppermountaintech.com/wp-content/uploads/2023/07/VNA-Calibration-Kits-Error-Terms-and-Calculation-CMT-Webinar-Slides.pdf) | coppermountaintech.com | M14 |
| [Copper Mountain — TRL Calibration](https://coppermountaintech.com/trl-calibration) | coppermountaintech.com | M14 |
| [Copper Mountain — Eliminating Fixture Effects from Embedded Measurements](https://coppermountaintech.com/eliminating-fixture-effects-from-embedded-measurements) | coppermountaintech.com | M14 |
| [Anritsu 백서 — OTA Testing in 5G NR](https://dl.cdn-anritsu.com/en-gb/test-measurement/files/5G-OTA-testing-V1.pdf) | dl.cdn-anritsu.com | M00 · M10 |
| [Keysight KB — EVM 과 SNR 의 관계 (64-QAM)](https://docs.keysight.com/kkbopen/what-is-the-relationship-between-the-error-vector-magnitude-and-the-signal-to-noise-ratio-for-a-64-qam-signal-589738547.html) | Keysight | M13 |
| [Keysight KB — Automate Keysight Instruments Using Python](https://docs.keysight.com/kkbopen/getting-started-automate-keysight-instruments-using-python-3-9-845872587.html) | Keysight | M16 |
| [TI — mmWave Hardware Design Guide](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/1023/2526.mmWave_5F00_hw_5F00_design_5F00_guide_5F00_rev_5F00_9.pdf) | e2e.ti.com | M02 · M17 |
| [Keysight/IEEE EMC — Fixture De-embedding Techniques and Tools using VNA](https://emcsociety.org/wp-content/uploads/2023/03/20230316-IEEE-EMC_-VNA-De-embeding_Keysight.pdf) | emcsociety.org | M14 |
| [Steer, Microwave and RF Design I — Radio Systems (LibreTexts, 무료 공개)](https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_I_-_Radio_Systems_(Steer)) | LibreTexts (Steer 교재) | M00 · M01 · M10 · M12 |
| [Steer, Microwave and RF Design II — Transmission Lines](https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_II_-_Transmission_Lines_(Steer)) | LibreTexts (Steer 교재) | M02 · M06 |
| [Steer, Microwave and RF Design III — Networks](https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_III_-_Networks_(Steer)) | LibreTexts (Steer 교재) | M03 |
| [Steer, Microwave and RF Design IV — Modules](https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_IV:_Modules_(Steer)) | LibreTexts (Steer 교재) | M06 · M07 |
| [Steer, Microwave and RF Design V — Amplifiers and Oscillators, §2.6 Amplif](https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_V:_Amplifiers_and_Oscillators_(Steer)/02:_Linear_Amplifiers/2.06:_Amplifier_Stability) | LibreTexts (Steer 교재) | M08 |
| [Steer, Microwave and RF Design V, §2.4 Amplifier Efficiency](https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_V:_Amplifiers_and_Oscillators_(Steer)/02:_Linear_Amplifiers/2.04:_Amplifier_Efficiency) | LibreTexts (Steer 교재) | M08 |
| [Qucs-RFlayout — openEMS 연동 튜토리얼](https://github.com/thomaslepoix/Qucs-RFlayout/blob/master/doc/tutorials/openems.md) | github.com | M07 · M17 |
| [Keysight 89600 VSA Help — EVM 정의](https://helpfiles.keysight.com/csg/89600B/Webhelp/Subsystems/digdemod/content/digdemod_symtblerrdata_evm.htm) | Keysight | M13 |
| [Keysight — TRL and LRM Calibration](https://helpfiles.keysight.com/csg/N1930xB/VNACalAndMeas/TRL_and_LRM_Calibration.htm) | Keysight | M14 |
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
| [KiCad 공식 사이트](https://kicad.org) | kicad.org | M17 |
| [NC State University Libraries 프로젝트 페이지](https://lib.ncsu.edu/projects/microwave-and-rf-design-open-textbook) | lib.ncsu.edu | M00 |
| [Marki Microwave — Mixer Basics Primer](https://markimicrowave.com/assets/c2c4688b-15c7-4421-a703-254cb238f9fb/Mixer_Basics_Primer.pdf) | markimicrowave.com | M09 |
| [MathWorks — What Is a Link Budget?](https://mathworks.com/discovery/link-budget.html) | mathworks.com | M10 |
| [Maury Microwave — Noise By the Numbers](https://maurymw.com/wp-content/uploads/Noise_By_the_Numbers_web2.pdf) | maurymw.com | M01 |
| [Maury Microwave — Practical Guide to Load Pull Measurements](https://maurymw.com/looking-for-a-practical-guide-to-load-pull-measurements-download-our-ebook) | maurymw.com | M15 |
| [Microwave Journal — Calculating Mismatch Uncertainty](https://microwavejournal.com/articles/6166-calculating-mismatch-uncertainty) | microwavejournal.com | M14 |
| [Microwave Journal — Cross Correlation in Phase Noise Analysis](https://microwavejournal.com/articles/10616-cross-correlation-in-phase-noise-analysis) | microwavejournal.com | M15 |
| [Microwaves101 — Microstrip](https://microwaves101.com/encyclopedias/microstrip) | Microwaves101 | M02 |
| [Microwaves101 — S-parameters](https://microwaves101.com/encyclopedias/s-parameters) | Microwaves101 | M03 |
| [Microwaves101 — 백과사전](https://microwaves101.com/encyclopedias) | Microwaves101 | M06 |
| [Microwaves101 — Noise Figure](https://microwaves101.com/encyclopedias/noise-figure) | Microwaves101 | M08 |
| [Microwaves101 — Noise Parameters](https://microwaves101.com/encyclopedias/noise-parameters) | Microwaves101 | M08 |
| [Mini-Circuits AN00-008 — Improve Two-Tone, Third-Order Intermodulation Tes](https://minicircuits.com/app/AN00-008.pdf) | Mini-Circuits | M07 · M08 · M15 |
| [Mini-Circuits AN00-009 — Understanding Mixers: Terms Defined and Measuring](https://minicircuits.com/app/AN00-009.pdf) | Mini-Circuits | M09 |
| [Mini-Circuits AN00-010 — How to Select a Mixer](https://minicircuits.com/app/AN00-010.pdf) | Mini-Circuits | M09 |
| [TRQ 시리즈 4/8 in-lb 렌치](https://minicircuits.com/WebStore/Wrenches.html) | Mini-Circuits | 부록 D |
| [Copper Mountain — What is the 12-Term VNA Calibration Model?](https://mwrf.com/technologies/test-measurement/article/21277729/copper-mountain-technologies-what-is-the-12-term-vna-calibration-model) | mwrf.com | M14 |
| [Rohde & Schwarz / Microwaves & RF — Understanding Phase-Noise Measurement ](https://mwrf.com/technologies/test-measurement/article/21268395/rohde-schwarz-understanding-phase-noise-measurement-techniques) | mwrf.com | M15 |
| [Narda-MITEQ — Q&A about Image Rejection Mixers](https://nardamiteq.com/docs/Q&A%20IRM%20254-257.PDF) | nardamiteq.com | M09 |
| [NXP AN1997 — LNA design for CDMA front end](https://nxp.com/docs/en/application-note/LNA97.pdf) | nxp.com | M03 · M08 |
| [openEMS 공식 사이트](https://openems.de) | openems.de | M17 |
| [HMC E157 Lecture 13: Stability](https://pages.hmc.edu/mspencer/e157/fa23/slides/13.pdf) | pages.hmc.edu | M08 |
| [HUBER+SUHNER SMA 카탈로그: 권장 0.45 N·m ≈ 4.0 in-lb](https://pdf.directindustry.com/pdf/huber-suhner/series-sma-coaxial-connectors/30583-293489.html) | pdf.directindustry.com | M04 · 부록 D |
| [PyVISA — SCPI Commands](https://pyvisa.org/docs/scpi-commands-python) | pyvisa.org | M16 |
| [PyVISA — Communicating with your instrument](https://pyvisa.readthedocs.io/en/latest/introduction/communication.html) | pyvisa.readthedocs.io | M16 |
| [Qorvo — BAW vs. SAW RF Filters](https://qorvo.com/design-hub/blog/baw-vs-saw-rf-filters) | qorvo.com | M07 |
| [Understanding Noise Figure (기술노트)](https://qsl.net/va3iul/Noise/Understanding%20Noise%20Figure.pdf) | qsl.net | M01 |
| [RF Filter Technologies For Dummies, Qorvo Special Edition](https://rfmw.com/data/qorvo_rf_filter_technologies.pdf) | rfmw.com | M07 |
| [Rohde & Schwarz — Amplifier characterization using load pull](https://rohde-schwarz.com/us/applications/amplifier-characterization-using-load-pull_56279-922304.html) | rohde-schwarz.com | M15 |
| [Campbell Scientific AN 3RF-F — The Link Budget and Fade Margin](https://s.campbellsci.com/documents/us/technical-papers/link-budget.pdf) | s.campbellsci.com | M10 |
| [R&S GFM313 — 5G New Radio Conducted Base Station Transmitter Tests](https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/dl_application/application_notes/gfm313/GFM313_3e_5G_NR_BaseStation_Tx_Tests.pdf) | scdn.rohde-schwarz.com | M13 · M15 |
| [Rohde & Schwarz 1MA178 — The Y Factor Technique for Noise Figure Measureme](https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/dl_application/application_notes/1ma178/1MA178_5e_NoiseFigure.pdf) | scdn.rohde-schwarz.com | M15 |
| [ScienceDirect — Stability Factor overview](https://sciencedirect.com/topics/engineering/stability-factor) | sciencedirect.com | M08 |
| [scikit-rf 문서 — Introduction](https://scikit-rf.readthedocs.io/en/latest/tutorials/Introduction.html) | scikit-rf | M03 |
| [scikit-rf 문서](https://scikit-rf.readthedocs.io/en/latest/tutorials/Networks.html) | scikit-rf | M03 · M14 |
| [Siglent — Spectrum Analyzer Basics: Bandwidth](https://siglenteu.com/application-note/spectrum-analyzer-basics-bandwidth) | siglenteu.com | M05 |
| [SiTime AN10062 — Phase Noise Measurement Guide for Oscillators](https://sitime.com/support/resource-library/application-notes/an10062-phase-noise-measurement-guide-oscillators) | sitime.com | M09 |
| [Tektronix — Noise Figure: Overview of Noise Measurement Methods](https://tek.com/en/documents/whitepaper/noise-figure-overview-noise-measurement-methods) | tek.com | M15 |
| [Tektronix — Decision Rule Guide](https://tek.com/en/documents/service/tektronix-decision-rule-guide) | tek.com | M16 |
| [TI SNAA329 — 12-GHz Direct Conversion Receiver With LMX8410L I/Q Demodulat](https://ti.com/lit/pdf/snaa329) | ti.com | M11 |
| [Times Microwave Systems — Connector Torque Requirements](https://timesmicrowave.com/connector-torque-requirements) | timesmicrowave.com | M04 · 부록 D |

---

## C.5 등급 C — 교육 사이트 (20개)

*정리가 잘 된 공개 교육 자료. 원문 확인이 필요할 때가 있다*

| 출처 | 발행 주체 | 쓴 모듈 |
|---|---|---|
| [A Review of Broadband Doherty Power Amplifier Design (arXiv 1908.07755)](https://arxiv.org/pdf/1908.07755) | arXiv | M08 |
| [Rubiola — The Leeson effect (arXiv physics/0502143)](https://arxiv.org/pdf/physics/0502143) | arXiv | M09 |
| [arXiv 2508.16735 — S-Band Image-Rejecting Dual-Conversion Superheterodyne ](https://arxiv.org/pdf/2508.16735) | arXiv | M09 |
| [arXiv 2407.09944 — 5G FR2 mmWave Antenna Array OTA Measurements Using a CA](https://arxiv.org/pdf/2407.09944) | arXiv | M10 |
| [UIUC ECE329 Lecture 37 — Smith Chart and Impedance Matching](https://courses.grainger.illinois.edu/ece329/sp2021/Lecture_notes/329lect37-L39.pdf) | courses.grainger.illinois.edu | M03 |
| [IEEE TMTT — A Combined Approach to DPD and CFR](https://ieeexplore.ieee.org/document/6353232) | ieeexplore.ieee.org | M13 |
| [ISOBudgets — Guard Banding: How to Take Uncertainty Into Account](https://isobudgets.com/guard-banding-how-to-take-uncertainty-into-account) | isobudgets.com | M16 |
| [ISOBudgets — Statements of Conformity and Decision Rules for ISO 17025](https://isobudgets.com/statements-of-conformity-and-decision-rules) | isobudgets.com | M16 |
| [IJMQE — Importance and Estimation of Mismatch Uncertainty for RF Parameter](https://metrology-journal.org/articles/ijmqe/pdf/2012/01/ijmqe120005.pdf) | metrology-journal.org | M14 |
| [Kikkert, RF Electronics Ch.8 — Amplifiers: Stability, Noise and Gain](https://mwl.diet.uniroma1.it/people/pisa/SISTEMI_RF/MATERIALE%20INTEGRATIVO/Kikkert_RF_Electronics_Course/11-RF_Electronics_Kikkert_Ch8_AmplifierStabilityNoise.pdf) | mwl.diet.uniroma1.it | M03 · M08 |
| [W5LUA, Stability & LNAs (Microwave Update)](https://ntms.org/files/MUD2011/MUD_W5LUA_LNAs_Web.pdf) | ntms.org | M08 |
| [Gary Breed — There's Nothing Magic About 50 Ohms](https://ptacts.uspto.gov/ptacts/public-informations/petitions/1556705/download-documents?artifactId=zZcqPwdS9RS22BDkL4Gc28WNLtSHEbJT-SOD11KzDToEyYTpMFI3XDU) | ptacts.uspto.gov | M02 |
| [B. Razavi, Design Considerations for Direct-Conversion Receivers](https://ptacts.uspto.gov/ptacts/public-informations/petitions/1463055/download-documents?artifactId=qRj6sOyeSMWSL2I1rrtmY-0NtOx5e04SNC3XR5V19X5mqBfXSEuTaT4) | ptacts.uspto.gov | M11 |
| [Chalmers 학위논문 — Design and Realization of a 6 GHz Doherty PA from Load-pul](https://publications.lib.chalmers.se/records/fulltext/225989/225989.pdf) | publications.lib.chalmers.se | M08 |
| [VA3IUL — LNA Design](https://qsl.net/va3iul/LNA%20Design/LNA_design.htm) | qsl.net | M08 |
| [Watkins-Johnson Tech Note — Image-Reject and Single-Sideband Mixers](https://rfcafe.com/references/articles/wj-tech-notes/image-reject-ssb-mixers-v12-3.pdf) | rfcafe.com | M09 |
| [Ricketts Lab — Double Balanced Mixer Theory](https://rickettslab.org/bits2waves/design/mixer-discrete/double-balanced-mixer) | rickettslab.org | M09 |
| [SATRA — Uncertainty, ISO/IEC 17025:2017 and decisions made on conformity](https://satra.com/spotlight/article.php?id=546) | satra.com | M16 |
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
| v1.0 | 2026-08-21 | 최초 생성. 고유 출처 166개, 등급 A 8 · B 86 · C 20 · D 44. `gen_appendix_c.py` 로 본문에서 자동 생성 |
