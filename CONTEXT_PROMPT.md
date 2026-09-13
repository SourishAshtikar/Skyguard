# SkyGuard AI — Project Context Prompt

Use this as the starting brief for any new session, coding agent, or collaborator picking up this project.

---

## Project

**Title:** SkyGuard AI — Intelligent Real-Time Anomaly Detection System for Temperature, Pressure, and Humidity Sensors in Automatic Weather Stations (AWS)

**Problem statement:** Build an AI/ML system that automatically detects abnormal, inconsistent, or faulty readings from AWS sensors (temperature °C, pressure hPa, humidity %) in real time — distinguishing genuine extreme weather events from sensor/data anomalies (spikes, frozen values, calibration drift, communication errors, physically inconsistent readings), while minimizing false alarms and remaining deployable at scale on low-power edge hardware (ESP32).

**Grand Challenge:** Can AI build a self-aware and self-healing weather observation network capable of delivering trustworthy atmospheric data under all environmental conditions?

**Evaluation criteria (competition):** Innovation & Novelty (25%), Detection Accuracy (20%), Real-Time Capability (15%), Explainability (10%), Scalability (10%), Practical Deployability (10%), Visualization/UI (5%), Energy Efficiency (5%). Evaluated on anomaly-injected test data.

**Deliverable:** Fully executable code with example usage + a document explaining various use cases.

---

## Expected Inputs & Outputs

### Inputs

| Parameter            | Unit  | Sensor (IMD AWS)      | Range             | Resolution |
|----------------------|-------|-----------------------|-------------------|------------|
| Air Temperature      | °C    | Pt-100 RTD / BME280   | −40 to +60        | 0.1 °C     |
| Atmospheric Pressure | hPa   | Piezoresistive / BMP  | 500 to 1100       | 0.1 hPa    |
| Relative Humidity    | %     | Capacitive / BME280   | 0 to 100          | 0.1 %      |

### Expected Outputs

| Output                        | Description                                                                 |
|-------------------------------|-----------------------------------------------------------------------------|
| Real-time anomaly alerts      | Flagged instantly at the edge (ESP32) and/or cloud                          |
| Severity & confidence scores  | 0–1 confidence score per reading; severity: Low / Medium / High / Critical  |
| Root-cause classification     | Sensor Fault · Comms Error · Calibration Drift · Genuine Weather Event      |
| Explainability report         | Which rule fired (Tier 1) or SHAP feature-importance vector (Tier 3)        |
| Sensor health status          | Per-sensor degradation tracker; predictive maintenance alerts               |
| Visualization dashboard       | Live stream + anomaly highlights + confidence gauge + SHAP panel            |
| Corrected data estimation     | Optional imputed value when anomaly is confirmed as sensor fault            |

---

## Anomaly Taxonomy (types the system must detect)

| # | Anomaly Type               | Example                                                              | Detection Difficulty |
|---|----------------------------|----------------------------------------------------------------------|----------------------|
| 1 | **Spike / Outlier**        | Temp jumps +20°C in one reading, reverts next reading                | Easy                 |
| 2 | **Frozen / Stuck Sensor**  | Humidity reports exactly 78.3% for 12+ consecutive hours             | Easy–Medium          |
| 3 | **Calibration Drift**      | Pressure reads 3 hPa higher each week vs. neighbors                 | Hard                 |
| 4 | **Communication Dropout**  | NaN / missing values for extended periods, then data resumes         | Easy                 |
| 5 | **Physical Inconsistency** | Dew point > air temperature (thermodynamically impossible)           | Medium               |
| 6 | **Noise / Jitter**         | High-frequency micro-oscillations beyond sensor resolution           | Medium               |
| 7 | **Range Violation**        | Temperature = 65°C (physically impossible in India)                  | Easy                 |
| 8 | **Spatial Inconsistency**  | Station reads 55°C while 3 neighbors within 50 km read 35°C         | Hard                 |
| 9 | **Temporal Pattern Break** | Normal diurnal cycle suddenly absent (flat line during day)          | Hard                 |

---

## Feature Engineering Specification

### A. Raw Sensor Features (3 — direct from AWS sensors)

| # | Feature Name    | Symbol   | Unit | Source      |
|---|-----------------|----------|------|-------------|
| 1 | Air Temperature | `temp`   | °C   | Sensor      |
| 2 | Atm. Pressure   | `pres`   | hPa  | Sensor      |
| 3 | Rel. Humidity    | `humi`   | %    | Sensor      |

### B. Derived Thermodynamic Features (4 — physical consistency signals)

| # | Feature Name                  | Symbol       | Formula / Logic                                                          | Why                                                    |
|---|-------------------------------|--------------|--------------------------------------------------------------------------|--------------------------------------------------------|
| 4 | Dew Point Temperature         | `dew_point`  | `b × [ln(RH/100) + aT/(b+T)] / [a − ln(RH/100) − aT/(b+T)]` (Magnus)  | Core physical consistency anchor: must be ≤ temp       |
| 5 | Dew Point Depression          | `dp_depress` | `temp − dew_point`                                                       | Negative value = impossible = instant anomaly flag     |
| 6 | Vapor Pressure                | `vap_pres`   | `6.1078 × exp(aT/(b+T)) × RH/100`                                      | Links temp, humidity, and pressure physically          |
| 7 | Heat Index / Apparent Temp    | `heat_idx`   | Rothfusz regression (when T > 27°C and RH > 40%)                        | Multivariate consistency cross-check                   |

### C. Temporal / Rate-of-Change Features (12 — detect spikes, drift, frozen sensor)

| #  | Feature Name                   | Symbol            | Window    | Formula                                       | Detects                  |
|----|--------------------------------|-------------------|-----------|-----------------------------------------------|--------------------------|
| 8  | Temp 1-step delta              | `temp_delta_1`    | 1 step    | `T(t) − T(t−1)`                               | Spike                    |
| 9  | Pressure 1-step delta          | `pres_delta_1`    | 1 step    | `P(t) − P(t−1)`                               | Spike                    |
| 10 | Humidity 1-step delta          | `humi_delta_1`    | 1 step    | `H(t) − H(t−1)`                               | Spike                    |
| 11 | Temp rate of change (3h)       | `temp_roc_3h`     | 3 hours   | `[T(t) − T(t−3)] / 3`                         | Drift, rapid changes     |
| 12 | Pressure rate of change (3h)   | `pres_roc_3h`     | 3 hours   | `[P(t) − P(t−3)] / 3`                         | Drift, frontal passages  |
| 13 | Humidity rate of change (3h)   | `humi_roc_3h`     | 3 hours   | `[H(t) − H(t−3)] / 3`                         | Drift, sudden dry/wet    |
| 14 | Temp rolling mean (6h)         | `temp_rmean_6h`   | 6 hours   | `mean(T[t−5:t])`                               | Context baseline         |
| 15 | Temp rolling std (6h)          | `temp_rstd_6h`    | 6 hours   | `std(T[t−5:t])`                                | Jitter / noise detection |
| 16 | Pressure rolling mean (6h)     | `pres_rmean_6h`   | 6 hours   | `mean(P[t−5:t])`                               | Context baseline         |
| 17 | Pressure rolling std (6h)      | `pres_rstd_6h`    | 6 hours   | `std(P[t−5:t])`                                | Jitter / noise detection |
| 18 | Humidity rolling mean (6h)     | `humi_rmean_6h`   | 6 hours   | `mean(H[t−5:t])`                               | Context baseline         |
| 19 | Humidity rolling std (6h)      | `humi_rstd_6h`    | 6 hours   | `std(H[t−5:t])`                                | Jitter / noise detection |

### D. Persistence / Frozen Sensor Features (3 — detect stuck sensors)

| #  | Feature Name                   | Symbol              | Formula                                                                  | Detects              |
|----|--------------------------------|---------------------|--------------------------------------------------------------------------|----------------------|
| 20 | Temp identical-value run length| `temp_persist_len`  | Count of consecutive readings where `|T(t) − T(t−1)| < 0.05`           | Frozen temp sensor   |
| 21 | Pres identical-value run length| `pres_persist_len`  | Count of consecutive readings where `|P(t) − P(t−1)| < 0.05`           | Frozen pres sensor   |
| 22 | Humi identical-value run length| `humi_persist_len`  | Count of consecutive readings where `|H(t) − H(t−1)| < 0.05`           | Frozen humi sensor   |

### E. Temporal Context Features (4 — encode time-of-day and season)

| #  | Feature Name       | Symbol       | Formula                                              | Why                                         |
|----|--------------------|--------------|------------------------------------------------------|---------------------------------------------|
| 23 | Hour sin           | `hour_sin`   | `sin(2π × hour / 24)`                               | Diurnal cycle encoding (continuous)         |
| 24 | Hour cos           | `hour_cos`   | `cos(2π × hour / 24)`                               | Diurnal cycle encoding (continuous)         |
| 25 | Day-of-year sin    | `doy_sin`    | `sin(2π × day_of_year / 365.25)`                    | Seasonal cycle encoding (monsoon/winter)    |
| 26 | Day-of-year cos    | `doy_cos`    | `cos(2π × day_of_year / 365.25)`                    | Seasonal cycle encoding (monsoon/winter)    |

### F. Z-Score Normalized Features (3 — for ML model input)

| #  | Feature Name     | Symbol       | Formula                              | Why                                      |
|----|------------------|--------------|--------------------------------------|------------------------------------------|
| 27 | Temp z-score     | `temp_z`     | `(T − μ_T) / σ_T` (rolling 24h)     | Scale-invariant input for autoencoder    |
| 28 | Pressure z-score | `pres_z`     | `(P − μ_P) / σ_P` (rolling 24h)     | Scale-invariant input for autoencoder    |
| 29 | Humidity z-score | `humi_z`     | `(H − μ_H) / σ_H` (rolling 24h)     | Scale-invariant input for autoencoder    |

### Feature Summary

| Category                        | Feature Count | Hardware Target  |
|---------------------------------|---------------|------------------|
| A. Raw sensor                   | 3             | ESP32 + Cloud    |
| B. Derived thermodynamic        | 4             | ESP32 + Cloud    |
| C. Temporal / rate-of-change    | 12            | ESP32 + Cloud    |
| D. Persistence / frozen sensor  | 3             | ESP32 + Cloud    |
| E. Temporal context (cyclical)  | 4             | ESP32 + Cloud    |
| F. Z-score normalized           | 3             | ESP32 + Cloud    |
| **Total engineered features**   | **29**        |                  |

> **ESP32 Tier 2 autoencoder input**: Features 1–7 (raw + thermodynamic) + 27–29 (z-scores) = **10 features** (fits comfortably in ESP32 SRAM).  
> **Cloud Tier 3 ensemble input**: All 29 features + spatial neighbor deltas (if available).

---

## Architecture (tiered — NOT everything on one device)

### Tier 1 — ESP32 (always-on, real-time, zero ML, ~0ms latency)
- **Rule-based WMO-style QC checks** — inherently explainable (reports exactly which rule fired):
  - **Range check**: flags values outside physically possible bounds (e.g., temp > 55°C or < −40°C for India)
  - **Step check (4σ rule)**: flags jump > 4× rolling standard deviation between consecutive readings
  - **Persistence check**: flags sensor stuck at identical value for > 6 consecutive readings
  - **Dew-point consistency**: flags when dew_point > temp (thermodynamically impossible)
  - **Cross-parameter consistency**: flags simultaneous extreme temp + extreme humidity + abnormal pressure (multi-sensor failure signature)
- **Output**: binary flag per reading (PASS / FAIL) + rule name + severity level

### Tier 2 — ESP32 (lightweight ML, ~5ms latency)
- **Quantized dense autoencoder** (int8, TensorFlow Lite Micro)
  - Architecture: 10 → 8 → 4 → 8 → 10 (bottleneck = 4, total params ~200)
  - Input: 10 features (raw + thermodynamic + z-scores)
  - Trained offline on normal data only (unsupervised)
  - **Reconstruction error** above adaptive threshold = multivariate anomaly flag
  - Fits within ESP32's ~320 KB SRAM / 4 MB flash
- **Output**: anomaly_score (0.0–1.0), is_anomaly flag

### Tier 3 — Cloud/gateway (Sequential Filter Pipeline + Root-Cause Intelligence)
- **Architecture Flow**:
  1. **Stage 1 — Multivariate VARMAX State-Space Forecaster**:
     - Jointly models $[T, P, H]$ and cross-correlations with diurnal cyclical exogenous regressors (`hour_sin/cos`, `doy_sin/cos`).
     - Fast 1-step recursive Kalman filter update (< 2 ms).
     - Scaled across India using **6–8 Climatic Zone Master Models** (Köppen/IMD zones) with station elevation/latitude offsets.
     - Naturally handles telemetry communication dropouts via Kalman state covariance propagation without ad-hoc imputation.
     - Evaluates innovation Mahalanobis distance $d^2 = (y_t - \hat{y}_t)^T \Sigma_t^{-1} (y_t - \hat{y}_t) \sim \chi^2_3$. If within nominal bounds, reading passes with zero extra compute.
  2. **Stage 2 — Augmented Isolation Forest**:
     - Invoked only for suspicious readings flagged by Stage 1 ($d^2 > \chi^2_{3, 0.99}$).
     - Evaluates the 29 engineered features + VARMAX residuals ($e_{\text{temp}}, e_{\text{pres}}, e_{\text{humi}}$) + Mahalanobis distance.
     - Detects non-linear thermodynamic violations and multi-sensor correlated failures.
  3. **Stage 3 — Hierarchical Two-Tier XGBoost Arbiter**:
     - **Model 1 (Weather vs Malfunction Validator)**: Evaluates whether a sudden shift is a Genuine Extreme Weather Event (thunderstorm squall, cloudburst, heatwave) or an instrument fault using Haversine consensus across 3 nearest neighbor AWS stations + thermodynamic invariants.
     - **Model 2 (Failure Mode Diagnoser)**: If confirmed as an instrument fault, classifies root cause:
       - → Sensor Spike
       - → Stuck / Frozen Sensor
       - → Calibration Drift
       - → Communication Dropout / Packet Corruption
- **Explainability**:
  - Closed-form dynamic confidence bands ($\pm 3\sigma$) from Stage 1 VARMAX.
  - Native **TreeSHAP** feature-importance waterfall on XGBoost decisions (< 5 ms).
  - Automated plain-English Root Cause Analysis (RCA) narrative for operators.
- **Spatial consistency check**: 3 nearest neighboring AWS stations via Haversine distance lookup from `indian_aws_locations.csv`.
- **Sensor health predictor**: tracks rolling anomaly rate per sensor type, predicts maintenance window.

### Explicit model-to-hardware split

| Model / Component                                        | Hardware | Latency   | Memory     |
|----------------------------------------------------------|----------|-----------|------------|
| Rule engine (range/step/persistence/dew-pt)              | ESP32    | < 1 ms    | < 2 KB     |
| Quantized dense autoencoder (TFLite Micro)               | ESP32    | < 5 ms    | < 50 KB    |
| Stage 1: Multivariate VARMAX State-Space Forecaster      | Cloud    | < 5 ms    | ~4 MB      |
| Stage 2: Augmented Isolation Forest                      | Cloud    | < 15 ms   | ~2 MB      |
| Stage 3: Hierarchical XGBoost (Validator + Diagnoser)    | Cloud    | < 5 ms    | ~5 MB      |
| TreeSHAP Explainer (Native fast tree traversal)          | Cloud    | < 10 ms   | ~10 MB     |
| Spatial consistency checker (Haversine neighbor lookup)  | Cloud    | < 10 ms   | ~1 MB      |
| Sensor health predictor                                  | Cloud    | < 5 ms    | ~1 MB      |
| **Total Cloud Tier 3 Latency**                           | **Cloud**| **< 50 ms**| **~23 MB** |

---

## Datasets

### Acquired ✅

1. **NOAA ISD Global Hourly — India (Primary Real Baseline)**
   - Source: NOAA NCEI via AWS S3 (`s3://noaa-isd-pds`)
   - **543 consolidated station files** (350 active AWS + 153 synoptic + 39 historical)
   - **13,166 station-year datasets** spanning 1942–2025
   - Parameters: timestamp, station_id, station_name, latitude, longitude, temperature (°C), pressure (hPa), humidity (%)
   - Location: `Datasets/noaa_india_by_station/` (one CSV per station, full history)
   - Station metadata: `Datasets/indian_aws_locations.csv` (545 Indian stations with lat/lon/elevation/dates)

2. **Multi-station spatial cluster data** — concurrent timestamps across geographically neighboring stations available in the consolidated dataset for spatial consistency checks

### To Be Generated 🔨

3. **Synthetic anomaly-labeled dataset**: inject spikes, frozen segments, drift, dropout/NaN, physical inconsistencies onto real baseline series → ground-truth labels for computing Accuracy / POD / FAR / F1
4. **ESP32 validation data**: small self-collected capture from real BME280/BME680 sensor rig to confirm on-device behavior matches Python prototype

### Reference Data 📚

5. **AWS sensor spec reference** (from IMD papers): Ranalkar et al. Table 1 (sensor accuracy/range/resolution), Patro & Bartakke Table II (WMO range-check limits) and Table IV/V (real-world QC pass-rate benchmarks — e.g., their system got ~99.6% temp / ~82% humidity consistency pass rates)

---

## Key reference papers (uploaded, already reviewed)

- Ranalkar et al., "Network of Automatic Weather Stations: Pseudo random burst sequence type" (Mausam 2012) — AWS hardware architecture, sensor specs, telemetry design
- Biju et al., "An indigenous state-of-the-art Digital Automatic Recording System (DARS)" (Mausam 2012) — data logger design, power budget (42 AH battery, 3+ months no solar)
- Patro & Bartakke, "Quality Control (QC) and Quality Assurance (QA) Procedures for Meteorological Data from AWS" (ICORT 2025) — the WMO QC methodology this project's Tier 1 rule engine directly implements, with published benchmark pass rates

---

## Implementation plan (phased)

| Phase | Task                                                    | Status       |
|-------|---------------------------------------------------------|--------------|
| 0     | Data collection — NOAA ISD India + station locations    | ✅ Complete   |
| 0.1   | Consolidate yearly files → single CSV per station       | ✅ Complete   |
| 1     | Feature engineering pipeline (29 features)              | 🔨 Next      |
| 2     | Synthetic anomaly injector with ground-truth labels     | 🔨 Next      |
| 3     | Tier 1 rule engine — Python prototype, then C++ port    | ⬜ Pending   |
| 4     | Tier 2 ESP32 autoencoder — train, quantize, TFLite Micro| ⬜ Pending   |
| 5     | Tier 3 cloud pipeline — VARMAX + IsoForest + XGBoost    | ⬜ Pending   |
| 6     | Explainability — TreeSHAP + confidence bands + RCA      | ⬜ Pending   |
| 7     | Spatial consistency checker                             | ⬜ Pending   |
| 8     | Sensor health predictor                                 | ⬜ Pending   |
| 9     | Communication — ESP32 → gateway (WiFi/LoRa/GSM)        | ⬜ Pending   |
| 10    | Dashboard — Streamlit/Dash, live stream + SHAP panel    | ⬜ Pending   |
| 11    | Correction/imputation + final report + use-case doc     | ⬜ Pending   |

---

## Progress so far / current files

### Project structure
```
SIH073/
├── CONTEXT_PROMPT.md                          ← This file
├── Datasets/
│   ├── indian_aws_locations.csv               ← 545 Indian station metadata (lat/lon/elev/dates)
│   ├── isd-history.csv                        ← Full NOAA global station inventory
│   ├── noaa_india_by_station/                 ← 543 consolidated station CSVs (one file per station, full history)
│   │   ├── 42182099999_SAFDARJUNG.csv         ← Delhi (1944–2025, ~180K records)
│   │   ├── 43003099999_CHHATRAPATI_SHIVAJI_MAHARAJ_INTL.csv  ← Mumbai (1944–2025, ~489K records)
│   │   ├── 43279099999_CHENNAI_INTL.csv       ← Chennai (1944–2025, ~470K records)
│   │   ├── ... (543 total station files)
│   │   └──
│   ├── noaa_india_hourly_processed/           ← 13,166 yearly station-year CSVs (raw processed)
│   └── noaa_india_hourly_combined.csv         ← Sample combined multi-station dataset
├── scripts/
│   ├── fetch_noaa_india.py                    ← NOAA data collector (AWS S3 + NCEI fallback)
│   └── consolidate_by_station.py              ← Merges yearly CSVs into single per-station files
```

### Scripts

- `scripts/fetch_noaa_india.py` — Downloads NOAA ISD station inventory, filters for India (CTRY=='IN'), downloads full historical hourly weather data from AWS S3 (`s3://noaa-isd-pds`), parses ISD fixed-width format, decodes TMP/DEW/SLP, calculates Relative Humidity via Magnus-Tetens formula, outputs clean CSVs. Multi-threaded (16 workers).
- `scripts/consolidate_by_station.py` — Merges all yearly CSV files per station into a single consolidated historical CSV, sorted chronologically and deduplicated.

## Next steps (not yet built)

- Feature engineering pipeline (29 features as specified above)
- Synthetic anomaly injector (spike/frozen/drift/dropout/inconsistency) with ground-truth labels
- Tier 1 rule engine (Python prototype first, then C++ port for ESP32)
- Tier 2 quantized autoencoder (train → TFLite Converter → TFLite Micro)
- Tier 3 cloud ensemble notebook (Isolation Forest + LSTM autoencoder + root-cause classifier)
- SHAP explainability wrapper
- Spatial consistency checker (Haversine nearest-neighbor lookup)
- Sensor health predictor (rolling anomaly rate tracker)
- Streamlit dashboard (live stream + anomaly highlights + confidence gauge + SHAP panel)
- ESP32 firmware port (Arduino/PlatformIO)
- Use-case documentation
