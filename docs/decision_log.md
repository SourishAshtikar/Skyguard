# SkyGuard AI — Architectural Decision Log (ADL)

## DEC-001: Frontend Framework Selection — React + Vite vs Streamlit
- **Date**: 2026-09-11
- **Status**: Accepted (Approved by User)
- **Context**: The project requires an interactive GIS map displaying 545 Indian Automatic Weather Stations with smooth zoom/pan, animated radar pulses for alerts, live time-series streaming without page flickering, and diagnostic side drawers.
- **Decision**: Use React (Vite + Leaflet / React-Leaflet + Tailwind/Vanilla CSS) backed by a Python FastAPI server instead of Streamlit.
- **Consequence**: Superior UI/UX scoring in SIH competition, true real-time WebSockets/SSE streaming capability, and clean API decoupling.

## DEC-002: Built-in TreeSHAP vs External Heavy SHAP C-Extensions
- **Date**: 2026-09-11
- **Status**: Accepted
- **Context**: Python 3.13 requires fast, reliable TreeSHAP calculations (< 5 ms latency) without compiling problematic external C-extensions.
- **Decision**: Utilize XGBoost's native C++ TreeSHAP implementation (`booster.predict(xgb.DMatrix(...), pred_contribs=True)`).
- **Consequence**: Zero compilation overhead, sub-3ms attribution generation, directly supported on all architectures.

## DEC-003: ESP32 Tier 2 Autoencoder Export Format
- **Date**: 2026-09-11
- **Status**: Accepted
- **Context**: Microcontrollers like ESP32 with 320 KB SRAM need compact autoencoder weights without large runtime library overheads.
- **Decision**: Export trained PyTorch weights as both serialized numpy weights and a static C++ header array (`firmware/tier2/model_weights.h`) for zero-dynamic-allocation matrix multiplication on ESP32.
- **Consequence**: Ultra-fast execution (< 4 ms on 240 MHz ESP32) within $< 40$ KB memory footprint.

## DEC-004: Safe Auditable Imputation Principle
- **Date**: 2026-09-11
- **Status**: Accepted
- **Context**: Atmospheric data integrity requires that real observations are never permanently overwritten.
- **Decision**: Imputed values are stored strictly in separate fields (`corrected_telemetry`), only applied when confirmed as an instrument fault with high confidence (> 85%), leaving raw sensor data immutable.
