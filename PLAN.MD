# SkyGuard AI — Complete Multi-Agent Execution Plan

## Summary

Build SkyGuard AI as a reproducible, testable pipeline for detecting AWS sensor anomalies across three tiers:

1. ESP32 Tier 1: deterministic quality-control rules.
2. ESP32 Tier 2: compact quantized autoencoder.
3. Cloud Tier 3: forecasting, anomaly scoring, root-cause diagnosis, explainability, spatial validation, health prediction, dashboard, and deployment interfaces.

The implementation should proceed sequentially through validated milestones. Each AI agent must produce code, tests, documentation, sample outputs, and a handoff report before the next agent begins.

The project source of truth is:

`D:\Projects\SIH 26\SIH073\CONTEXT_PROMPT.md`

The NOAA station data is already available under:

`D:\Projects\SIH 26\SIH073\Datasets\`

The current repository contains data-acquisition scripts and an initial feature-engineering script, but no complete test suite, anomaly injector, model pipeline, ESP32 firmware, dashboard, or deployment package.

## Agent Operating Rules

Every implementation agent must:

- Read `CONTEXT_PROMPT.md` before working.
- Inspect existing files before creating replacements.
- Preserve existing datasets and scripts.
- Work in small, independently testable modules.
- Add unit tests for every public function.
- Add one runnable example for every major component.
- Record assumptions and unresolved issues in `docs/decision_log.md`.
- Run the relevant tests before handoff.
- Never silently change column names, units, thresholds, labels, or model contracts.
- Return a handoff report containing:
  - Files added or changed.
  - Commands used.
  - Tests run and results.
  - Known limitations.
  - Exact next-agent instructions.

Use a central configuration file so thresholds and model parameters are not hard-coded across modules.

## Phase 0 — Repository and Data Contract

### Agent 0: Project Auditor

Inspect the existing project and create:

- `README.md`
- `docs/architecture.md`
- `docs/data_dictionary.md`
- `docs/decision_log.md`
- `requirements.txt` or `pyproject.toml`
- `tests/`
- `configs/default.yaml`

Define the canonical input schema:

```text
timestamp
station_id
station_name
latitude
longitude
temperature
pressure
humidity
```

Define the canonical output schema:

```text
timestamp
station_id
raw values
engineered features
tier1 status
tier1 rules fired
tier2 score
tier2 status
tier3 score
anomaly type
root cause
severity
confidence
corrected values
explanation
sensor health
```

Add schema validation for:

- Required columns.
- Numeric types.
- Timestamp parsing.
- Valid unit conventions.
- Duplicate timestamps.
- Missing values.
- Station metadata consistency.

### Gate

Do not begin model development until one sample station file can be loaded, validated, and summarized by a single command.

## Phase 1 — Feature Engineering

### Agent 1: Feature Pipeline

Complete and harden the existing `scripts/feature_engineering.py`.

Implement all 29 specified features:

- Raw sensor features.
- Dew point, vapor pressure, dew-point depression, and heat index.
- One-step changes.
- Time-aware three-hour rate of change.
- Six-hour rolling statistics.
- Persistence lengths.
- Cyclical hour and day-of-year features.
- Rolling 24-hour z-scores.

Required corrections:

- Use actual timestamp spacing rather than assuming every row is exactly one hour.
- Handle irregular NOAA observations safely.
- Preserve missing readings as missing where appropriate.
- Prevent invalid mathematical operations.
- Define minimum-history behavior explicitly.
- Ensure batch and streaming implementations produce equivalent results.
- Avoid data leakage from future observations.
- Use consistent population/sample standard deviation settings.
- Add station/timezone handling.

Create:

- `src/skyguard/features/batch.py`
- `src/skyguard/features/streaming.py`
- `src/skyguard/features/thermodynamics.py`
- `tests/test_features.py`

### Tests

Validate:

- Magnus dew-point calculations.
- Vapor pressure.
- Heat-index activation conditions.
- Rolling values.
- Persistence reset behavior.
- Missing data.
- Irregular timestamps.
- Batch/streaming equivalence.
- Exactly 29 engineered features.

### Gate

Generate a featured sample dataset for at least three stations and verify that all expected columns exist with no unexpected infinity values.

## Phase 2 — Synthetic Anomaly Dataset

### Agent 2: Anomaly Injector

Create a deterministic anomaly-injection framework using real NOAA baseline data.

Implement anomaly classes:

- Spike/outlier.
- Frozen sensor.
- Calibration drift.
- Communication dropout.
- Packet corruption.
- Physical inconsistency.
- Noise/jitter.
- Range violation.
- Spatial inconsistency.
- Temporal pattern break.

Each injected record must include:

```text
is_anomaly
anomaly_type
affected_sensor
injection_id
injection_start
injection_end
ground_truth_root_cause
```

Requirements:

- Preserve the original clean values.
- Support configurable random seeds.
- Support anomaly severity.
- Prevent impossible accidental labels.
- Generate train, validation, and test splits chronologically.
- Keep stations separated where required.
- Prevent the same anomaly episode appearing across splits.

Create:

- `src/skyguard/data/anomaly_injector.py`
- `src/skyguard/data/dataset_builder.py`
- `configs/anomalies.yaml`
- `tests/test_anomaly_injector.py`

### Metrics

Implement reusable evaluation functions for:

- Precision.
- Recall/POD.
- F1.
- False alarm rate.
- Specificity.
- Detection delay.
- Per-anomaly-type performance.
- Per-sensor performance.
- Calibration error for confidence scores.

### Gate

Produce a versioned synthetic dataset and a report proving that every required anomaly type is represented and correctly labeled.

## Phase 3 — Tier 1 Rule Engine

### Agent 3: Deterministic QC Engine

Implement the explainable rule engine first in Python.

Rules:

- Physical range.
- Step/rate-of-change.
- Rolling sigma.
- Persistence.
- Dew-point consistency.
- Cross-parameter consistency.
- Missing/dropout.
- Resolution/noise checks.

Each rule must return:

```text
rule_name
passed
severity
message
evidence
```

Create a deterministic aggregate decision:

```text
PASS
SUSPECT
FAIL
```

Create:

- `src/skyguard/tier1/rules.py`
- `src/skyguard/tier1/engine.py`
- `tests/test_tier1.py`
- `examples/run_tier1.py`

### ESP32 Port

After Python behavior is frozen:

- Port only the required state and rules to C++.
- Provide Arduino/PlatformIO project files.
- Avoid dynamic allocation.
- Add serial test mode.
- Feed identical fixtures to Python and C++.
- Compare outputs exactly or within documented floating-point tolerance.

Create:

- `firmware/tier1/`
- `firmware/tier1/test_vectors/`
- `tests/test_python_cpp_parity.py`

### Gate

The Python and C++ engines must agree on all golden test vectors.

## Phase 4 — Tier 2 Edge Autoencoder

### Agent 4: Compact ML Model

Train the specified autoencoder using normal-only data:

```text
10 → 8 → 4 → 8 → 10
```

Input features:

- Temperature.
- Pressure.
- Humidity.
- Dew point.
- Dew-point depression.
- Vapor pressure.
- Heat index.
- Temperature z-score.
- Pressure z-score.
- Humidity z-score.

Requirements:

- Fit scalers only on training data.
- Train on clean/normal windows.
- Select threshold using validation data.
- Report reconstruction-error distributions.
- Export floating-point model.
- Quantize to int8.
- Export TensorFlow Lite model.
- Verify TFLite output against Python output.
- Measure model size and inference latency.

Create:

- `src/skyguard/tier2/train_autoencoder.py`
- `src/skyguard/tier2/inference.py`
- `src/skyguard/tier2/export_tflite.py`
- `models/tier2/`
- `tests/test_tier2.py`

### ESP32 Validation

Create a minimal TFLite Micro integration:

- Fixed-size tensor arena.
- No heap allocation during inference.
- Serial input/output protocol.
- Memory and latency report.
- Golden-vector parity test.

### Gate

The edge model must meet the documented SRAM, flash, and latency targets or clearly report the measured deviation.

## Phase 5 — Tier 3 Forecasting and Sequential Detection

### Agent 5: Forecasting Layer

Implement the Stage 1 multivariate forecasting layer.

Required behavior:

- Jointly model temperature, pressure, and humidity.
- Include cyclical time features.
- Support recursive one-step inference.
- Return prediction, covariance, residual, and Mahalanobis distance.
- Handle missing telemetry without naïve forward-filling.
- Provide a cold-start fallback.

Create an interface independent of the selected library:

```python
forecast = forecaster.update(reading)
```

Return:

```text
prediction
covariance
residual
mahalanobis_distance
stage1_status
```

Use a fallback implementation if VARMAX is unstable or unavailable, but preserve the same interface.

### Agent 6: Isolation Forest Layer

Run Isolation Forest only for Stage 1 suspicious readings.

Inputs:

- All 29 engineered features.
- Forecast residuals.
- Mahalanobis distance.

Requirements:

- Fit only on clean training data.
- Persist model and preprocessing.
- Handle missing features safely.
- Return normalized anomaly score.
- Support batch and streaming inference.

### Agent 7: Root-Cause Arbiter

Implement the two-stage XGBoost decision layer:

1. Genuine weather event versus malfunction.
2. Fault classification:
   - Spike.
   - Frozen sensor.
   - Calibration drift.
   - Communication dropout.
   - Packet corruption.

Use:

- Tier 1 outputs.
- Tier 2 score.
- Tier 3 forecast residuals.
- Spatial consensus.
- Thermodynamic features.
- Temporal features.

If labeled real-world data is insufficient, use synthetic labels and clearly mark the limitation.

### Gate

The complete cloud pipeline must process one reading and return one stable output object with anomaly status, severity, confidence, root cause, and explanation.

## Phase 6 — Spatial Consistency

### Agent 8: Neighbor Resolver

Implement:

- Station metadata loading.
- Haversine distance.
- Nearest-neighbor lookup.
- Configurable radius.
- Minimum neighbor count.
- Missing-neighbor fallback.
- Temporal alignment/tolerance.
- Neighbor consensus features.

Do not use future observations relative to the target timestamp.

Output:

```text
neighbor_count
neighbor_ids
distance_km
neighbor_median
neighbor_mad
target_deviation
spatial_consensus
```

Use spatial evidence only when enough valid neighbors exist.

### Gate

Test known station coordinates and validate spatial anomaly scenarios from the synthetic dataset.

## Phase 7 — Explainability and Sensor Health

### Agent 9: Explainability

Implement:

- Tier 1 rule explanations.
- Forecast confidence bands.
- Isolation Forest evidence summary.
- TreeSHAP explanations for XGBoost.
- Plain-language RCA generation.
- Stable explanation schema.

Every explanation must distinguish:

- Observed evidence.
- Model inference.
- Confidence.
- Missing evidence.

Never present a model prediction as a confirmed physical fact.

### Agent 10: Sensor Health

Track per-station and per-sensor:

- Rolling anomaly rate.
- Recent severity distribution.
- Consecutive failures.
- Missing-data ratio.
- Drift indicators.
- Last healthy timestamp.
- Maintenance risk score.

Return:

```text
health_status
health_score
risk_factors
recommended_action
```

### Gate

For every anomaly, the system must explain why it fired and show the sensor-health impact.

## Phase 8 — End-to-End Pipeline API

### Agent 11: Pipeline Integrator

Create a single orchestration layer:

```python
result = pipeline.process(reading, context)
```

The pipeline order must be:

1. Validate input.
2. Compute streaming features.
3. Run Tier 1 rules.
4. Run Tier 2 model if configured.
5. Run Stage 1 forecast.
6. Run Stage 2 Isolation Forest only when required.
7. Run spatial validation.
8. Run root-cause arbiter.
9. Compute severity and confidence.
10. Generate explanation.
11. Update sensor health.
12. Optionally estimate corrected value.
13. Emit structured result.

Support:

- Offline batch mode.
- Single-reading streaming mode.
- Replay mode.
- Disabled-model fallback.
- Model version reporting.
- Configuration version reporting.

### Gate

Replay a complete anomaly-injected stream and generate a machine-readable result for every reading.

## Phase 9 — Correction and Imputation

### Agent 12: Safe Correction Layer

Only provide corrected values when:

- The reading is classified as a sensor/data fault.
- Confidence exceeds a configured threshold.
- A valid replacement estimate exists.
- The correction is auditable.

Possible methods:

- Forecast estimate.
- Neighbor median.
- Interpolation for short communication gaps.
- Last-known value only for explicitly approved cases.

Never overwrite raw data. Store:

```text
raw_value
corrected_value
correction_applied
correction_method
correction_confidence
```

### Gate

Test that genuine extreme weather events are not automatically corrected as faults.

## Phase 10 — Dashboard and Demonstration

### Agent 13: Streamlit Dashboard

Create a dashboard with:

- Station selector.
- Time-range selector.
- Live/replay mode.
- Temperature, pressure, humidity charts.
- Anomaly markers.
- Severity indicator.
- Confidence gauge.
- Root-cause panel.
- Tier-by-tier decision trace.
- SHAP feature panel.
- Neighbor comparison.
- Sensor-health history.
- Corrected-versus-raw view.

The dashboard must work without a live ESP32 by using replay data.

Create:

- `app/dashboard.py`
- `examples/demo_replay.py`
- `docs/dashboard.md`

### Gate

A reviewer must be able to start the dashboard with one documented command and inspect at least one complete anomaly episode.

## Phase 11 — Communication and ESP32 Integration

### Agent 14: Device Gateway

Implement a transport-neutral message contract first.

Recommended payload:

```json
{
  "station_id": "string",
  "device_id": "string",
  "timestamp": "ISO-8601",
  "sequence": 0,
  "temperature": 0.0,
  "pressure": 0.0,
  "humidity": 0.0,
  "battery_voltage": 0.0,
  "firmware_version": "string"
}
```

Support a local simulator before real communication.

Add:

- Sequence-number validation.
- Duplicate detection.
- Timestamp validation.
- Payload checksum or integrity field.
- Retry behavior.
- Offline buffering.
- Backpressure handling.
- Connection-loss simulation.

Implement one real transport first, preferably HTTP or MQTT, and keep WiFi/LoRa/GSM adapters behind the same interface.

### Gate

Demonstrate sensor simulator → gateway → pipeline → dashboard flow.

## Phase 12 — Evaluation, Packaging, and Documentation

### Agent 15: Benchmark and Report

Run experiments for:

- Clean data.
- Each anomaly type.
- Mixed anomalies.
- Missing data.
- Different stations.
- Different climate zones.
- Cold start.
- No-neighbor situations.
- Genuine extreme-weather-like events.

Report:

- Precision, recall, F1, POD, FAR.
- Detection delay.
- False alarms per station-day.
- Root-cause accuracy.
- Confidence calibration.
- Tier 1 latency.
- Tier 2 latency.
- Tier 3 latency.
- Memory footprint.
- Model sizes.
- Dashboard throughput.

Create:

- `reports/benchmark_report.md`
- `reports/results.json`
- `reports/figures/`
- `docs/use_cases.md`
- `docs/deployment.md`
- `docs/limitations.md`

### Agent 16: Release Auditor

Verify:

- Fresh environment installation.
- Dataset path configuration.
- Reproducible model training.
- End-to-end replay.
- Dashboard launch.
- ESP32 build.
- Python/C++ parity.
- No raw data overwrite.
- No secrets committed.
- Documentation accuracy.
- All tests passing.

Create a final release checklist and package the demo.

## Recommended Repository Layout

```text
SIH073/
├── CONTEXT_PROMPT.md
├── README.md
├── pyproject.toml
├── configs/
├── datasets/
├── docs/
├── examples/
├── firmware/
│   └── tier1/
├── models/
├── notebooks/
├── reports/
├── scripts/
├── src/
│   └── skyguard/
│       ├── config/
│       ├── data/
│       ├── features/
│       ├── tier1/
│       ├── tier2/
│       ├── tier3/
│       ├── spatial/
│       ├── health/
│       ├── explainability/
│       ├── correction/
│       ├── pipeline/
│       └── evaluation/
├── tests/
└── app/
```

## Final Acceptance Criteria

The project is complete only when all of the following are true:

- A clean installation can run the demo.
- Historical NOAA data can be transformed into 29 engineered features.
- All required anomaly types can be injected with ground truth.
- Tier 1 produces explainable decisions.
- Python Tier 1 and ESP32 C++ outputs agree.
- Tier 2 has an exported quantized model and measured resource usage.
- Tier 3 performs sequential detection and root-cause classification.
- Spatial validation works with missing-neighbor fallbacks.
- Every alert contains severity, confidence, cause, and explanation.
- Sensor health is tracked over time.
- Dashboard displays a complete replay.
- Raw data remains immutable.
- Benchmark results are reproducible.
- Limitations and unsupported claims are documented.

## Assumptions and Defaults

- The SIH073 project at `D:\Projects\SIH 26\SIH073` is the target repository.
- The referenced `exp-4_ins.py` file was not found inside that project and is not treated as a project dependency unless separately supplied.
- The NOAA station CSV schema shown in the repository is authoritative.
- Python is used for research, orchestration, and cloud inference.
- C++/PlatformIO is used for ESP32 deployment.
- Synthetic anomaly data is acceptable for initial supervised training, but all results must identify where real labeled data is unavailable.
- Raw observations are never modified.
- Any model that cannot meet the stated edge constraints must be replaced, simplified, or explicitly marked as non-deployable.
