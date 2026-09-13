# SkyGuard AI — System Architecture

SkyGuard AI is a multi-tier intelligent anomaly detection, root-cause diagnosis, and self-healing system designed for India's national network of Automatic Weather Stations (AWS).

```mermaid
flowchart TD
    subgraph Edge ["Tier 1 & Tier 2: Edge Hardware (ESP32)"]
        S[AWS Sensors: Pt-100 / BMP / BME280] --> T1[Tier 1: Deterministic QC Rules<br/>Range, Step 4-sigma, Persistence, Dew-point]
        T1 -->|PASS / SUSPECT| T2[Tier 2: Compact ML Autoencoder<br/>10-8-4-8-10 Int8 Quantized]
        T1 -->|Instant FAIL Alert| OUT_E[Edge Alert Packet]
        T2 -->|Score & Anomaly Flag| OUT_E
    end

    OUT_E -->|Telemetry Gateway| CLOUD

    subgraph Cloud ["Tier 3: Cloud Intelligence & Self-Healing"]
        CLOUD[Ingestion & Streaming Feature Pipeline<br/>29 Physical & Thermodynamic Features]
        CLOUD --> S1[Stage 1: State-Space Forecaster<br/>Multivariate Kalman + Diurnal Regressors]
        S1 -->|Mahalanobis Distance d² > χ²₃| S2[Stage 2: Augmented Isolation Forest]
        S1 -->|Nominal Residuals| PASS_C[Pass-through]
        S2 -->|Suspicious Feature Vector| S3[Stage 3: Hierarchical XGBoost Arbiter]
        
        SPATIAL[Spatial Consensus Engine<br/>Haversine Nearest Neighbors across 545 AWS] --> S3
        
        S3 --> M1[Model 1: Weather Event vs Malfunction]
        M1 -->|Genuine Weather Event| WE_FLAG[Severe Weather Alert: Cyclone/Squall/Heatwave]
        M1 -->|Instrument Fault| M2[Model 2: Root Cause Diagnoser<br/>Spike / Stuck / Drift / Comms Error]
        
        M2 --> EXPL[TreeSHAP & Plain-English RCA Explainer]
        M2 --> HEALTH[Sensor Health & Predictive Maintenance Tracker]
        M2 --> IMPUTE[Auditable Safe Correction Layer]
    end

    EXPL --> DASH[React + GIS Command Center Dashboard]
    HEALTH --> DASH
    IMPUTE --> DASH
    WE_FLAG --> DASH
```

## Latency & Hardware Specifications

| Tier | Component | Target Hardware | Latency Budget | Memory Footprint |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Deterministic WMO QC Engine | ESP32 Microcontroller | $< 0.2$ ms | $< 2$ KB SRAM |
| **Tier 2** | Compact Dense Autoencoder | ESP32 Microcontroller | $< 3.5$ ms | $< 40$ KB Flash/SRAM |
| **Tier 3** | Stage 1 Kalman Forecaster | Cloud / Gateway Server | $< 2.0$ ms | $\sim 4$ MB |
| **Tier 3** | Stage 2 Isolation Forest | Cloud / Gateway Server | $< 8.0$ ms | $\sim 2$ MB |
| **Tier 3** | Spatial Consensus Resolver | Cloud / Gateway Server | $< 5.0$ ms | $\sim 1$ MB |
| **Tier 3** | Stage 3 Hierarchical XGBoost | Cloud / Gateway Server | $< 3.0$ ms | $\sim 5$ MB |
| **Tier 3** | TreeSHAP Attributions | Cloud / Gateway Server | $< 4.0$ ms | $\sim 8$ MB |
| **Tier 3** | Sensor Health & Imputation | Cloud / Gateway Server | $< 1.0$ ms | $< 1$ MB |
| **Total** | **Full End-to-End Cloud Latency**| | **$< 25$ ms** | **$< 25$ MB** |
