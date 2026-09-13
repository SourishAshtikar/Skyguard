# SkyGuard AI — Data Dictionary & Canonical Schema

## Canonical Raw Inputs

| Column | Type | Unit | Description | Valid Range |
| :--- | :--- | :--- | :--- | :--- |
| `timestamp` | ISO-8601 String / Datetime | UTC / Local | Observation timestamp | Chronological |
| `station_id` | String | Identifier | WMO / NOAA station ID (e.g. 42182099999) | 11 digits |
| `station_name` | String | Text | Official station name (e.g. SAFDARJUNG) | Text |
| `latitude` | Float | Decimal Degrees | Station latitude | $8.0^\circ\text{N} - 37.0^\circ\text{N}$ |
| `longitude` | Float | Decimal Degrees | Station longitude | $68.0^\circ\text{E} - 97.5^\circ\text{E}$ |
| `temperature`| Float | °C | Air dry-bulb temperature | $-40.0^\circ\text{C} - +55.0^\circ\text{C}$ |
| `pressure` | Float | hPa | Atmospheric surface pressure | $500.0 - 1080.0\text{ hPa}$ |
| `humidity` | Float | % | Relative humidity | $0.0\% - 100.0\%$ |

---

## The 29 Engineered Features

| # | Feature Name | Symbol | Unit | Category | Mathematical Basis |
|---|---|---|---|---|---|
| 1 | Air Temperature | `temp` | °C | Raw | Direct sensor reading |
| 2 | Atmospheric Pressure | `pres` | hPa | Raw | Direct sensor reading |
| 3 | Relative Humidity | `humi` | % | Raw | Direct sensor reading |
| 4 | Dew Point Temperature | `dew_point` | °C | Thermodynamic | Magnus-Tetens: $b \frac{\ln(RH/100) + \frac{aT}{b+T}}{a - \ln(RH/100) - \frac{aT}{b+T}}$ |
| 5 | Dew Point Depression | `dp_depress` | °C | Thermodynamic | $T - T_{\text{dew}}$ (Negative = Physical Invariant Violation) |
| 6 | Vapor Pressure | `vap_pres` | hPa | Thermodynamic | $e_s(T) \times (RH / 100)$ where $e_s(T) = 6.1078 \exp\left(\frac{aT}{b+T}\right)$ |
| 7 | Heat Index | `heat_idx` | °C | Thermodynamic | Rothfusz multi-variate regression polynomial |
| 8 | Temperature 1-Step Delta | `temp_delta_1` | °C | Temporal | $T_t - T_{t-1}$ |
| 9 | Pressure 1-Step Delta | `pres_delta_1` | hPa | Temporal | $P_t - P_{t-1}$ |
| 10 | Humidity 1-Step Delta | `humi_delta_1` | % | Temporal | $H_t - H_{t-1}$ |
| 11 | Temperature Rate of Change (3h) | `temp_roc_3h` | °C/h | Temporal | $(T_t - T_{t-3}) / 3$ |
| 12 | Pressure Rate of Change (3h) | `pres_roc_3h` | hPa/h | Temporal | $(P_t - P_{t-3}) / 3$ |
| 13 | Humidity Rate of Change (3h) | `humi_roc_3h` | %/h | Temporal | $(H_t - H_{t-3}) / 3$ |
| 14 | Temperature Rolling Mean (6h) | `temp_rmean_6h` | °C | Statistical | 6-step rolling window mean |
| 15 | Temperature Rolling Std (6h) | `temp_rstd_6h` | °C | Statistical | 6-step rolling window sample std |
| 16 | Pressure Rolling Mean (6h) | `pres_rmean_6h` | hPa | Statistical | 6-step rolling window mean |
| 17 | Pressure Rolling Std (6h) | `pres_rstd_6h` | hPa | Statistical | 6-step rolling window sample std |
| 18 | Humidity Rolling Mean (6h) | `humi_rmean_6h` | % | Statistical | 6-step rolling window mean |
| 19 | Humidity Rolling Std (6h) | `humi_rstd_6h` | % | Statistical | 6-step rolling window sample std |
| 20 | Temperature Persistence Run | `temp_persist_len` | Count | Stuck Sensor | Consecutive readings with $\|\Delta T\| < 0.05$ |
| 21 | Pressure Persistence Run | `pres_persist_len` | Count | Stuck Sensor | Consecutive readings with $\|\Delta P\| < 0.05$ |
| 22 | Humidity Persistence Run | `humi_persist_len` | Count | Stuck Sensor | Consecutive readings with $\|\Delta H\| < 0.05$ |
| 23 | Hour Sin | `hour_sin` | Continuous | Cyclical | $\sin(2\pi \cdot \text{hour} / 24)$ |
| 24 | Hour Cos | `hour_cos` | Continuous | Cyclical | $\cos(2\pi \cdot \text{hour} / 24)$ |
| 25 | Day of Year Sin | `doy_sin` | Continuous | Cyclical | $\sin(2\pi \cdot \text{DOY} / 365.25)$ |
| 26 | Day of Year Cos | `doy_cos` | Continuous | Cyclical | $\cos(2\pi \cdot \text{DOY} / 365.25)$ |
| 27 | Temperature 24h Z-Score | `temp_z` | Normal | Normalized | $(T - \mu_{24}) / (\sigma_{24} + \epsilon)$ |
| 28 | Pressure 24h Z-Score | `pres_z` | Normal | Normalized | $(P - \mu_{24}) / (\sigma_{24} + \epsilon)$ |
| 29 | Humidity 24h Z-Score | `humi_z` | Normal | Normalized | $(H - \mu_{24}) / (\sigma_{24} + \epsilon)$ |
