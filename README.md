# SkyGuard AI 🛡️🌦️

> **Intelligent Real-Time Anomaly Detection, Root-Cause Diagnosis & Self-Healing for India's Automatic Weather Stations (AWS)**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Edge: ESP32](https://img.shields.io/badge/Edge-ESP32%20Ready-green.svg)](#tier-1--tier-2-edge-firmware)
[![React + GIS](https://img.shields.io/badge/Frontend-React%20%2B%20GIS-purple.svg)](#interactive-gis-command-center)

---

## Overview

SkyGuard AI protects national meteorological networks from sensor and transmission failures by deploying a 3-tier intelligence pipeline:

1. **Tier 1 (Edge ESP32, $<0.2$ ms)**: Deterministic WMO QC rules (Range, 4-sigma step, persistence, dew-point consistency).
2. **Tier 2 (Edge ESP32, $<3.5$ ms)**: Ultra-compact $10 \to 8 \to 4 \to 8 \to 10$ quantized autoencoder for multivariate edge anomaly scoring.
3. **Tier 3 (Cloud / Gateway, $<25$ ms)**:
   - **Stage 1**: Multivariate State-Space Kalman Forecaster with diurnal cycle regressors.
   - **Stage 2**: Augmented Isolation Forest evaluating all 29 thermodynamic and physical features.
   - **Stage 3**: Hierarchical Two-Tier XGBoost Arbiter separating **Genuine Extreme Weather Events** from **Instrument Malfunctions**.
   - **Spatial Verification**: Haversine neighbor consensus across 545 Indian AWS stations.
   - **Explainability**: Sub-5ms native TreeSHAP waterfall and automated plain-English Root Cause Analysis (RCA).
   - **Self-Healing**: Auditable safe imputation preserving immutable raw observations.

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -e .
```

### 2. Run Automated Test Suite
```bash
pytest tests/ -v
```

### 3. Launch React + GIS Command Center
```bash
# Terminal 1: Start FastAPI Backend
python -m skyguard.api.server

# Terminal 2: Start React Frontend
cd frontend
npm install
npm run dev
```

---

## Directory Structure

```text
SIH073/
├── configs/               # System and anomaly scenario configurations
├── Datasets/              # 545 Indian AWS stations & historical hourly datasets
├── docs/                  # Architecture, data dictionary, and decision logs
├── firmware/              # ESP32 Tier 1 & Tier 2 C++ firmware
├── frontend/              # Modern React + GIS Command Center
├── src/skyguard/
│   ├── config/            # Canonical dataclasses and contracts
│   ├── features/          # 29 thermodynamic & streaming feature extractors
│   ├── data/              # 10-class synthetic anomaly injector & dataset builder
│   ├── tier1/             # Deterministic WMO QC rule engine
│   ├── tier2/             # Compact autoencoder & weight exporter
│   ├── tier3/             # Kalman forecaster, Isolation Forest & XGBoost Arbiter
│   ├── spatial/           # Haversine neighbor consensus resolver
│   ├── explainability/    # Native TreeSHAP & plain-English RCA
│   ├── health/            # Sensor health & predictive maintenance tracker
│   ├── correction/        # Auditable safe imputation layer
│   ├── pipeline/          # Master end-to-end orchestrator
│   └── api/               # FastAPI REST/WebSocket server
└── tests/                 # Unit and integration test suites
```
