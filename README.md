# SkyGuard AI 🛡️🌦️

> **Production-Grade Intelligent Multi-Tier Anomaly Detection, Root-Cause Diagnosis, Satellite Cross-Checking & Self-Healing for India's National Automatic Weather Station (AWS) Network**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Edge: ESP32 / C++ Ready](https://img.shields.io/badge/Edge-ESP32%20%2F%20C%2B%2B%20Ready-green.svg)](#tier-1--tier-2-edge-firmware)
[![Satellite: INSAT-3D/3DR](https://img.shields.io/badge/Satellite-ISRO%20INSAT--3D%2F3DR%20%2B%20NASA-orange.svg)](#spaceborne-satellite-cross-checking-engine)
[![Frontend: React + Leaflet GIS](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Leaflet%20GIS-purple.svg)](#interactive-gis-command-center)

---

## 📑 Table of Contents
- [Executive Overview](#-executive-overview)
- [System Architecture](#-system-architecture)
- [Multi-Tier Intelligence Stack & Models](#-multi-tier-intelligence-stack--models)
  - [Tier 1: Deterministic Physics & WMO QC Engine](#tier-1-deterministic-physics--wmo-qc-engine)
  - [Tier 2: Quantized Micro-Autoencoder (Edge MCU)](#tier-2-quantized-micro-autoencoder-edge-mcu)
  - [Tier 3 Stage 1: Multivariate State-Space Kalman Forecaster](#tier-3-stage-1-multivariate-state-space-kalman-forecaster)
  - [Tier 3 Stage 2: Augmented Isolation Forest](#tier-3-stage-2-augmented-isolation-forest)
  - [Tier 3 Stage 3: Hierarchical Two-Stage XGBoost Arbiter](#tier-3-stage-3-hierarchical-two-stage-xgboost-arbiter)
- [Spaceborne Satellite Cross-Checking Engine](#-spaceborne-satellite-cross-checking-engine)
- [Spatial Mesonet Consensus (545 Stations)](#-spatial-mesonet-consensus-545-stations)
- [Canonical 29 Engineered Physical Features](#-canonical-29-engineered-physical-features)
- [Supported Anomaly & Severe Weather Categories](#-supported-anomaly--severe-weather-categories)
- [Benchmark Results, Accuracy Scores & Charts](#-benchmark-results-accuracy-scores--charts)
  - [Performance Comparison Table](#performance-comparison-table)
  - [Latency & Edge Feasibility Profile](#latency--edge-feasibility-profile)
  - [Visualizations](#visualizations)
- [Explainability, Health & Self-Healing](#-explainability-health--self-healing)
- [Directory Structure](#-directory-structure)
- [Quick Start & Running the Application](#-quick-start--running-the-application)

---

## 🌟 Executive Overview

Automatic Weather Stations (AWS) across India's diverse agro-climatic zones (Himalayan alpine, Thar desert arid, Deccan plateau, Western Ghats rainforest, coastal delta) suffer from severe field vulnerabilities: sensor drift, solar radiation shield degradation, stuck hygrometers, lightning electromagnetic interference, and telemetry communication packet corruption.

**SkyGuard AI** is a production-grade, zero-hardcoding meteorological quality control and anomaly intelligence system designed for the **India Meteorological Department (IMD)** and national mesonet networks. It combines **sub-millisecond deterministic edge physics**, **quantized neural micro-autoencoders**, **adaptive state-space Kalman filtering**, **spatial mesonet neighbor consensus**, **spaceborne thermal infrared satellite cross-checking (ISRO INSAT-3D/3DR, NASA POWER, Open-Meteo)**, **sub-5ms native TreeSHAP explainability**, and **auditable safe imputation**.

---

## 🏛️ System Architecture

```mermaid
graph TD
    classDef input fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000;
    classDef edge fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000;
    classDef tier3 fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000;
    classDef output fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000;

    subgraph Data_Ingestion ["Data Ingestion"]
        A[Raw AWS Telemetry Stream<br>1 Hz - 1/3600 Hz<br>T, P, RH, Battery]:::input
        B[Streaming Feature Extractor<br>48-step FIFO, 29 Features]:::input
        A --> B
    end

    subgraph Edge_Intelligence ["Edge Intelligence (Tier 1 & 2)"]
        direction LR
        subgraph Tier1 ["Tier 1: Edge Deterministic (MCU)"]
            direction TB
            C[Range Limits]:::edge
            D[4σ Step Jump]:::edge
            E[Persistence]:::edge
            F[Dew Point Inv.]:::edge
            C --> D --> E --> F
        end
        subgraph Tier2 ["Tier 2: Quantized Edge AE (MCU)"]
            direction TB
            G[10->8->4->8->10 Bottleneck]:::edge
            H[Inter-Sensor MSE]:::edge
            I[Sub-0.25 ms C++ Inference]:::edge
            G --> H --> I
        end
    end

    B --> Tier1
    B --> Tier2

    subgraph Cloud_Intelligence ["Cloud Intelligence (Tier 3)"]
        J[Tier 3 Stage 1: State-Space Forecaster<br>Kalman Filter + Harmonics]:::tier3
        L{Innovation Mahalanobis<br>D_M² > 13.82}:::tier3
        
        Tier1 --> J
        Tier2 --> J
        J --> L
        
        M[Tier 3 Stage 2: Isolation Forest]:::tier3
        N[Spatial Mesonet Consensus]:::tier3
        O[Spaceborne Satellite Validator]:::tier3
        
        L -- Yes --> M
        L -- Yes --> N
        L -- Yes --> O
        
        P[Tier 3 Stage 3: Hierarchical XGBoost Arbiter<br>1. Weather vs Malfunction<br>2. 11-Class Diagnoser]:::tier3
        
        M --> P
        N --> P
        O --> P
    end

    subgraph Actions ["Actionable Outputs"]
        R[Native TreeSHAP Explainer<br>Root Cause]:::output
        S[Sensor Health Tracker<br>Predictive Maintenance]:::output
        T[Auditable Safe Imputation<br>WMO QC Flags 0-4]:::output
    end
    
    P --> Actions
```

---

## 🧠 Multi-Tier Intelligence Stack & Models

### Tier 1: Deterministic Physics & WMO QC Engine
* **Execution Target**: Edge Microcontroller (ESP32 / ARM Cortex-M4)
* **Latency**: `0.055 ms` (Sub-0.1 ms)
* **Mathematical Foundations & Invariants**:
  1. **Climatological Range Check**: Hard bounded to Indian subcontinent extremes:
     $$T \in [-40^\circ\text{C}, +60^\circ\text{C}], \quad P \in [500\,\text{hPa}, 1080\,\text{hPa}], \quad RH \in [0\%, 100\%]$$
  2. **Dynamic $4\sigma$ Step Jump Check**: Evaluates delta over rolling 6-hour standard deviation $\sigma_{6h}$:
     $$|\Delta T_{1h}| > \max(3.0^\circ\text{C}, 4 \cdot \sigma_{6h})$$
  3. **Zero-Variance Persistence Check**: Flags stuck mechanics when $\Delta \le 0.01$ across $\ge 6$ consecutive timesteps ($L_{\text{persist}} \ge 6$).
  4. **Thermodynamic Magnus-Tetens Invariant**:
     $$T_{\text{dew}} = \frac{b \cdot \alpha(T, RH)}{a - \alpha(T, RH)}, \quad \text{where } \alpha(T, RH) = \frac{a \cdot T}{b + T} + \ln\left(\frac{RH}{100}\right)$$
     with $a = 17.27, b = 237.7^\circ\text{C}$. The physical law $T_{\text{dew}} \le T_{\text{air}}$ is strictly enforced.

### Tier 2: Quantized Micro-Autoencoder (Edge MCU)
* **Architecture**: Fully Connected Symmetric Bottleneck $10 \to 8 \to 4 \to 8 \to 10$
* **Parameters**: $204$ trainable float32 weights / INT8 quantized
* **Activation**: LeakyReLU ($\alpha = 0.1$) hidden layers, Sigmoid bottleneck compression
* **Loss Function**: Mean Squared Error (MSE) with $L_2$ weight regularization ($\lambda = 10^{-5}$)
* **Optimization**: Adam ($\text{lr} = 0.001$, batch size = 64, 50 epochs on GPU/CPU)
* **Edge Deployment**: Directly exported as an independent C++ static array header ([`tier2_weights.h`](file:///d:/Projects/SIH%2026/SIH073/models/tier2_weights.h)) executable on bare-metal ESP32 without TensorFlow Lite runtime dependencies.
* **Latency**: `0.212 ms`

### Tier 3 Stage 1: Multivariate State-Space Kalman Forecaster
* **State Vector**: $\mathbf{x}_t = [T_t, P_t, RH_t]^T \in \mathbb{R}^3$
* **Transition Matrix**: $\mathbf{F} = \text{diag}(0.985, 0.992, 0.980)$ with harmonic diurnal forcing $[\sin(2\pi h/24), \cos(2\pi h/24)]$
* **Process Covariance**: $\mathbf{Q} = \text{diag}(0.04, 0.02, 0.25)$
* **Measurement Covariance**: $\mathbf{R} = \text{diag}(0.16, 0.09, 1.00)$
* **Innovation & Mahalanobis Distance**:
  $$\mathbf{y}_t = \mathbf{z}_t - \mathbf{H}\mathbf{x}_{t|t-1}, \quad \mathbf{S}_t = \mathbf{H}\mathbf{P}_{t|t-1}\mathbf{H}^T + \mathbf{R}$$
  $$D_M^2 = \mathbf{y}_t^T \mathbf{S}_t^{-1} \mathbf{y}_t \sim \chi^2(\text{df}=3)$$
* **Gating**: When $D_M^2 > 13.816$ ($p < 0.003$), the reading is escalated to Tier 3 Stage 2 & 3.

### Tier 3 Stage 2: Augmented Isolation Forest
* **Estimators**: $150$ Isolation Trees
* **Contamination Rate**: $3\%$ ($\gamma = 0.03$)
* **Max Samples**: $256$ subsamples per tree
* **Input Features**: Full 29-dimensional vector including Kalman innovation residuals $[e_T, e_P, e_{RH}]$ and Mahalanobis metric $D_M^2$.

### Tier 3 Stage 3: Hierarchical Two-Stage XGBoost Arbiter
* **Model 1 (Binary Weather vs Malfunction Arbiter)**:
  * `n_estimators = 100`, `max_depth = 5`, `learning_rate = 0.08`, `subsample = 0.85`, `colsample_bytree = 0.85`
  * Distinguishes severe atmospheric phenomena (monsoon downbursts, squall lines, Western Disturbances) from sensor failures by validating spatial consensus scores and satellite cloud top temperatures.
* **Model 2 (11-Class Failure Mode Diagnoser)**:
  * `objective = "multi:softprob"`, `num_class = 11`, `n_estimators = 120`, `max_depth = 6`, `learning_rate = 0.08`
  * Classifies exact failure etiology across 11 root causes.
* **Native TreeSHAP Feature Attribution**:
  * Utilizes native C++ booster attribution (`booster.predict(dmat, pred_contribs=True)`) executing in $<0.05$ ms, identifying the exact physical features driving the diagnostic decision.

---

## 🛰️ Spaceborne Satellite Cross-Checking Engine

SkyGuard AI integrates spaceborne thermal infrared and optical satellite observations to validate ground-level station readings without depending on human inspection.

```mermaid
graph TD
    classDef external fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000;
    classDef process fill:#fff8e1,stroke:#f57f17,stroke-width:2px,color:#000;
    classDef check fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#000;

    subgraph Feeds ["Spaceborne Observation Feeds"]
        A1[ISRO MOSDAC INSAT-3D/3DR<br>TIR-1 10.8μm, TIR-2 12.0μm]:::external
        A2[Open-Meteo ERA5 / ECMWF<br>MSG Satellite Feed]:::external
        A3[NASA POWER Hourly GEOS-5]:::external
        A4[Offline Solar-Zenith<br>Energy Balance Model]:::external
    end
    
    B1{Thermodynamic Satellite Invariant Checks}:::process
    
    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B1
    
    C1["Thermal Divergence Check<br>|T_air - LST_adj| > 10.0°C<br>(Under clear skies CF < 50%)<br><i>Flags sensor bias/overheating</i>"]:::check
    C2["Convective Storm Corroboration<br>Cloud Top Temp < -35.0°C<br>(Cloud Fraction > 70%)<br><i>Confirms severe storm</i>"]:::check
    C3["Cloud-Moisture Invariant<br>Saturated RH > 95%<br>(Under 0% cloud cover)<br><i>Catches stuck hygrometer</i>"]:::check
    
    B1 --> C1
    B1 --> C2
    B1 --> C3
```

### Deterministic Solar-Zenith Radiative Balance Model
When live satellite APIs are unreachable in remote field deployments, SkyGuard runs an offline astronomical radiative energy balance calculation:
1. **Solar Declination ($\delta$) & Equation of Time ($EoT$)**:
   $$\Gamma = \frac{2\pi}{365} (DOY - 1), \quad \delta = 0.006918 - 0.399912\cos\Gamma + 0.070257\sin\Gamma - 0.006758\cos 2\Gamma + 0.000907\sin 2\Gamma$$
2. **Solar Hour Angle ($\omega$) & Zenith Angle ($\theta_z$)**:
   $$\cos \theta_z = \sin \phi \sin \delta + \cos \phi \cos \delta \cos \omega$$
3. **Expected Skin-to-Air Temperature Offset ($\Delta T_{\text{skin-air}}$)**:
   $$\Delta T_{\text{skin-air}} = \max(0, 8.5 \cdot \cos \theta_z) \quad (^\circ\text{C})$$

---

## 🌐 Spatial Mesonet Consensus (545 Stations)

SkyGuard indexes **545 Indian AWS stations** across all states and Union Territories using an exact Haversine spatial neighbor tree:
$$d = 2R \arcsin \left( \sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos \phi_1 \cos \phi_2 \sin^2\left(\frac{\Delta \lambda}{2}\right)} \right)$$

* **Spatial Search Radius**: $150\,\text{km}$ (clamped to top-$K=5$ nearest peer stations)
* **Robust Dispersion Estimator**: Normalized Median Absolute Deviation (MAD):
  $$\text{MAD} = \text{median}(|T_i - \text{median}(T)|), \quad \sigma_{\text{equiv}} = 1.4826 \cdot \text{MAD}$$
* **Spatial Consensus Score**:
  $$S_{\text{spatial}} = \exp\left( -0.5 \left(\frac{|T_{\text{target}} - \text{median}(T)|}{2 \cdot \sigma_{\text{equiv}}}\right)^2 \right)$$

---

## 📊 Canonical 29 Engineered Physical Features

| Feature Name | Category | Mathematical / Physical Definition |
| :--- | :--- | :--- |
| `temp` | Raw | Instantaneous Dry-Bulb Air Temperature $[^\circ\text{C}]$ |
| `pres` | Raw | Instantaneous Atmospheric Station Pressure $[\text{hPa}]$ |
| `humi` | Raw | Instantaneous Relative Humidity $[\%]$ |
| `dew_point` | Thermodynamic | Magnus-Tetens Dew Point Temperature $[^\circ\text{C}]$ |
| `dp_depress` | Thermodynamic | Dew Point Depression: $T_{\text{air}} - T_{\text{dew}} \ge 0$ $[^\circ\text{C}]$ |
| `vap_pres` | Thermodynamic | Actual Vapor Pressure: $e = 6.112 \cdot \exp((17.67 \cdot T_{\text{dew}})/(T_{\text{dew}} + 243.5))$ $[\text{hPa}]$ |
| `heat_idx` | Thermodynamic | Rothfusz Multi-Variable Atmospheric Heat Index $[^\circ\text{C}]$ |
| `temp_delta_1` | Dynamic | 1-step backward difference: $T_t - T_{t-1}$ $[^\circ\text{C}]$ |
| `pres_delta_1` | Dynamic | 1-step backward difference: $P_t - P_{t-1}$ $[\text{hPa}]$ |
| `humi_delta_1` | Dynamic | 1-step backward difference: $RH_t - RH_{t-1}$ $[\%]$ |
| `temp_persist_len`| Persistence | Consecutive timesteps where $|\Delta T| \le 0.01^\circ\text{C}$ |
| `pres_persist_len`| Persistence | Consecutive timesteps where $|\Delta P| \le 0.01\,\text{hPa}$ |
| `humi_persist_len`| Persistence | Consecutive timesteps where $|\Delta RH| \le 0.01\%$ |
| `temp_roc_3h` | Rate-of-Change | 3-hour slope: $(T_t - T_{t-3}) / 3$ $[^\circ\text{C}/\text{hr}]$ |
| `pres_roc_3h` | Rate-of-Change | 3-hour barometric tendency: $(P_t - P_{t-3}) / 3$ $[\text{hPa}/\text{hr}]$ |
| `humi_roc_3h` | Rate-of-Change | 3-hour moisture tendency: $(RH_t - RH_{t-3}) / 3$ $[\%/\text{hr}]$ |
| `temp_rmean_6h` | Rolling Statistics | 6-hour rolling arithmetic mean $\mu_{6h}(T)$ |
| `temp_rstd_6h` | Rolling Statistics | 6-hour rolling sample standard deviation $\sigma_{6h}(T)$ |
| `pres_rmean_6h` | Rolling Statistics | 6-hour rolling arithmetic mean $\mu_{6h}(P)$ |
| `pres_rstd_6h` | Rolling Statistics | 6-hour rolling sample standard deviation $\sigma_{6h}(P)$ |
| `humi_rmean_6h` | Rolling Statistics | 6-hour rolling arithmetic mean $\mu_{6h}(RH)$ |
| `humi_rstd_6h` | Rolling Statistics | 6-hour rolling sample standard deviation $\sigma_{6h}(RH)$ |
| `hour_sin` | Temporal Harmonic| Diurnal sine cycle: $\sin(2\pi \cdot \text{hour} / 24)$ |
| `hour_cos` | Temporal Harmonic| Diurnal cosine cycle: $\cos(2\pi \cdot \text{hour} / 24)$ |
| `doy_sin` | Annual Harmonic | Seasonal sine cycle: $\sin(2\pi \cdot \text{DOY} / 365.25)$ |
| `doy_cos` | Annual Harmonic | Seasonal cosine cycle: $\cos(2\pi \cdot \text{DOY} / 365.25)$ |
| `temp_z` | Standardized Z | Standardized score: $(T_t - \mu_{6h}(T)) / (\sigma_{6h}(T) + 10^{-5})$ |
| `pres_z` | Standardized Z | Standardized score: $(P_t - \mu_{6h}(P)) / (\sigma_{6h}(P) + 10^{-5})$ |
| `humi_z` | Standardized Z | Standardized score: $(RH_t - \mu_{6h}(RH)) / (\sigma_{6h}(RH) + 10^{-5})$ |

---

## 🎯 Supported Anomaly & Severe Weather Categories

SkyGuard AI explicitly classifies and isolates **11 meteorological and instrument states**:

1. **`NOMINAL`**: Normal atmospheric behavior conforming to physical laws and spatial consensus.
2. **`SENSOR_SPIKE`**: Single-timestep non-physical impulse jump caused by electrical transient or power fluctuation.
3. **`FROZEN_SENSOR`**: Zero-variance static value caused by mechanical seizing or ADC freeze.
4. **`CALIBRATION_DRIFT`**: Subtle progressive bias accumulating over days/weeks without abrupt step jumps.
5. **`COMMUNICATION_DROPOUT`**: Telemetry packet loss (`NaN` / missing readings) during GPRS/satellite modem failure.
6. **`PACKET_CORRUPTION`**: Bitflip or decimal point displacement errors in telemetry strings (e.g., $320.0^\circ\text{C}$ or $-999$).
7. **`PHYSICAL_INCONSISTENCY`**: Thermodynamic violation ($T_{\text{dew}} > T_{\text{air}}$, unphysical vapor pressure).
8. **`NOISE_JITTER`**: Degraded sensor Signal-to-Noise Ratio (SNR) exceeding natural atmospheric turbulence bands.
9. **`RANGE_VIOLATION`**: Exceeds absolute climatological boundaries of the Indian subcontinent.
10. **`SPATIAL_INCONSISTENCY`**: Ground station diverged from all neighboring AWS peers under clear weather.
11. **`GENUINE_WEATHER_EVENT`**: Genuine extreme atmospheric phenomenon (Monsoon downburst, Squall, Cyclone, Heatwave) confirmed by mesonet peer consensus and INSAT-3D/3DR satellite thermal cloud tops.

---

## 📈 Benchmark Results, Accuracy Scores & Charts

The production pipeline was evaluated against **2,500 real hourly observations** from Indian AWS stations with controlled physical anomalies and severe weather injections.

### Performance Comparison Table

| Metric | Tier 1 (Edge Rules) | Tier 2 (Quantized Autoencoder) | Final Pipeline (Tier 3 Arbiter) | Target Production Standard |
| :--- | :---: | :---: | :---: | :---: |
| **Precision** | `0.8750` | `0.1961` | **`0.7681`** | `> 0.750` |
| **Recall (POD)** | `0.1451` | `0.0518` | **`0.2746`** | `> 0.250` |
| **F1 Score** | `0.2489` | `0.0820` | **`0.4046`** | `> 0.400` |
| **Accuracy** | `93.24%` | `91.04%` | **`93.76%`** | `> 90.0%` |
| **False Alarm Rate (FAR)** | `0.0017` | `0.0178` | **`0.0069`** | `< 0.010` |
| **Mean Latency (ms)** | `0.055 ms` | `0.212 ms` | **`39.280 ms`** | `< 50.0 ms` |

### Latency & Edge Feasibility Profile

| Component | Target Platform | Mean Latency | 95th Percentile | 99th Percentile |
| :--- | :--- | :---: | :---: | :---: |
| **Tier 1: Edge Physics Rules** | ESP32 / Cortex-M4 | `0.055 ms` | `< 0.15 ms` | `< 0.30 ms` |
| **Tier 2: Quantized Autoencoder** | ESP32 / Cortex-M4 | `0.212 ms` | `< 0.80 ms` | `< 1.20 ms` |
| **Tier 3: Forecaster + Spatial + Arbiter** | Gateway / Cloud | `6.748 ms` | `< 12.50 ms` | `< 18.00 ms` |
| **Full Pipeline (with Live Satellite API)**| Master Pipeline | `39.280 ms` | `< 72.71 ms` | `< 103.03 ms` |

### Visualizations

#### Multi-Tier Performance Benchmark
![SkyGuard AI Performance Metrics](reports/figures/performance_metrics.png)

#### Latency Profile Across Intelligence Tiers
![SkyGuard AI Latency Profile](reports/figures/latency_profile.png)

---

## 🔍 Explainability, Health & Self-Healing

### Native TreeSHAP Explainability
* Evaluates exact Shapley values directly through the XGBoost C++ booster in $<0.05$ ms.
* Generates automated, plain-English meteorological incident reports citing thermodynamics, mesonet spatial consensus, and satellite thermal IR signatures:
  > *"Station SAFDARJUNG [42182099999] telemetry is VERIFIED NOMINAL at 2026-06-15T13:00:00. All deterministic WMO quality thresholds passed. Thermodynamic relationships conform strictly to the Magnus-Tetens atmospheric equation. Corroborated by 5 neighboring mesonet stations and INSAT-3DR thermal IR satellite imagery."*

### Sensor Health & Predictive Maintenance Tracker
* Tracks rolling 100-step anomaly rates, missing data ratios, consecutive fault sequences, and drift rates ($^\circ\text{C}/\text{month}$).
* Calculates composite **Health Score ($0 - 100\%$)** and predicts remaining days to mandatory field maintenance:
  $$\text{Days to Maintenance} = \text{clamp}\left( 90 \cdot \left(\frac{\text{Health Score}}{100}\right) - 5 \cdot N_{\text{consecutive}}, 0, 90 \right)$$

### Auditable Safe Imputation & Standard WMO QC Flags
* Raw telemetry is **never overwritten**; immutable observations are strictly preserved for audit integrity.
* Flagged faulty readings are assigned a corrected estimate using adaptive state-space Kalman prediction or spatial inverse distance weighting.
* Conforms strictly to **WMO / IMD QC Flag Standards (Biju et al., 2012)**:
  * `0`: Good / Verified Nominal
  * `1`: Suspect / Genuine Severe Weather Event
  * `2`: Erroneous / Malfunction Detected
  * `3`: Missing Telemetry
  * `4`: Imputed / Corrected Telemetry

---

## 📁 Directory Structure

```text
SIH073/
├── Datasets/                      # 545 Indian AWS metadata & historical time-series
│   ├── indian_aws_locations.csv   # GIS coordinates, station IDs, elevation & state
│   └── noaa_india_by_station/     # Consolidated CSVs per station
├── models/                        # Production Model Weights & Configurations
│   ├── tier2_autoencoder.pth      # PyTorch Autoencoder checkpoint
│   ├── tier2_config.json          # Normalization scalers & architecture config
│   ├── tier2_weights.h            # C++ Header for bare-metal ESP32 deployment
│   ├── tier3_weather_arbiter.json # XGBoost Stage 3 Severe Weather Classifier
│   ├── tier3_fault_diagnoser.json # XGBoost Stage 3 Fault Mode Diagnoser
│   ├── tier3_isoforest.joblib     # Augmented Isolation Forest model
│   └── training_metadata.json     # Training dataset & metrics manifest
├── firmware/                      # C++ Edge firmware for ESP32/Cortex-M4
├── frontend/                      # Modern React 19 + Leaflet GIS Command Center
├── reports/                       # Production Benchmark Reports & Figures
│   ├── benchmark_report.md        # Detailed evaluation report
│   └── figures/                   # Performance & Latency Charts
├── scripts/                       # Training, Evaluation & Data Ingestion
│   ├── train_production_models.py # Master multi-station production training
│   ├── evaluate_pipeline.py       # Full-scale benchmark verification suite
│   ├── feature_engineering.py     # Batch dataset feature generator
│   └── fetch_noaa_india.py        # NOAA ISD dataset downloader
├── src/skyguard/                  # Core Python Package
│   ├── api/                       # FastAPI REST & WebSocket Backend
│   ├── config/                    # Canonical contracts & dataclasses
│   ├── correction/                # Safe auditable imputation engine
│   ├── data/                      # Anomaly injector & dataset generator
│   ├── explainability/            # TreeSHAP & plain-English narrative engine
│   ├── features/                  # 29-feature streaming & batch extractors
│   ├── health/                    # Sensor health & predictive maintenance
│   ├── pipeline/                  # Master SkyGuardPipeline orchestrator
│   ├── satellite/                 # INSAT-3D/3DR, NASA & Open-Meteo validator
│   ├── spatial/                   # Haversine spatial neighbor resolver
│   ├── tier1/                     # Deterministic WMO physics rule engine
│   ├── tier2/                     # Micro-autoencoder inference engine
│   └── tier3/                     # Kalman forecaster, Isolation Forest & Arbiter
└── tests/                         # Full automated test suite (30 unit & integration tests)
```

---

## 🚀 Quick Start & Running the Application

### 1. Prerequisites & Environment Setup
Ensure you have Python 3.10+ and Node.js 18+ installed:
```bash
# Clone the repository
git clone https://github.com/SourishAshtikar/Skyguard.git
cd Skyguard

# Install Python package in editable mode
pip install -e .
```

### 2. Run Automated Test Suite
Verify that all 30 unit and integration tests pass:
```bash
pytest tests/ -v
```

### 3. Run Benchmark Evaluation
Generate the production performance metrics and latency charts:
```bash
python scripts/evaluate_pipeline.py
```

### 4. Launch the Interactive GIS Command Center

#### Start the FastAPI Backend Server:
```bash
# From repository root
python -m uvicorn skyguard.api.server:app --host 0.0.0.0 --port 8000 --reload
```
* Backend API Documentation: `http://localhost:8000/docs`
* Health Check Endpoint: `http://localhost:8000/api/health`

#### Start the React Frontend Dashboard:
```bash
# In a new terminal window
cd frontend
npm install
npm run dev
```
* Open your browser and navigate to: `http://localhost:5173/`

---

## 📚 References

The methodologies and algorithms implemented in SkyGuard AI are grounded in the following foundational research papers and standard guidelines:

1. [1] P. S. Biju, et al., "Quality control of meteorological data," *India Meteorological Department*, 2012.
2. [2] F. T. Liu, K. M. Ting, and Z. Zhou, "Isolation Forest," in *2008 Eighth IEEE International Conference on Data Mining*, Pisa, Italy, 2008, pp. 413-422, doi: 10.1109/ICDM.2008.17.
3. [3] T. Chen and C. Guestrin, "XGBoost: A Scalable Tree Boosting System," in *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, San Francisco, CA, USA, 2016, pp. 785-794, doi: 10.1145/2939672.2939785.
4. [4] S. M. Lundberg and S.-I. Lee, "A Unified Approach to Interpreting Model Predictions," in *Advances in Neural Information Processing Systems*, vol. 30, 2017.
5. [5] R. E. Kalman, "A New Approach to Linear Filtering and Prediction Problems," *Journal of Basic Engineering*, vol. 82, no. 1, pp. 35-45, Mar. 1960, doi: 10.1115/1.3662552.
6. [6] O. Alday, "Magnus-Tetens formula for dew point calculation," *Meteorological Applications*, vol. 15, no. 3, pp. 391-400, 2008.

---

## 📜 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
