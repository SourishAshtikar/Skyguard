"""
SkyGuard AI — Thermodynamic Calculations
Physical formulas for atmospheric parameters based on WMO standards:
- Magnus-Tetens dew point calculation
- Dew point depression (physical consistency check)
- Atmospheric vapor pressure
- Rothfusz regression heat index
"""

import numpy as np
from typing import Union

# Magnus-Tetens coefficients (Sonntag 1990 / WMO standard)
MAGNUS_A = 17.625
MAGNUS_B = 243.04  # °C


def compute_dew_point(
    temp: Union[float, np.ndarray], humi: Union[float, np.ndarray]
) -> Union[float, np.ndarray]:
    """Computes dew point temperature (°C) via Magnus-Tetens formula.
    Clamps humidity to [0.01, 100.0]% to avoid log(0) singularity.
    Valid for temperatures from -40°C to +55°C.
    """
    is_scalar = np.isscalar(temp)
    t = np.asarray(temp, dtype=float)
    rh = np.asarray(humi, dtype=float)
    rh_clamped = np.clip(rh, 0.01, 100.0)

    alpha = np.log(rh_clamped / 100.0) + (MAGNUS_A * t) / (MAGNUS_B + t)
    denom = MAGNUS_A - alpha
    # Prevent division by zero if alpha approaches MAGNUS_A
    denom = np.where(np.abs(denom) < 1e-7, 1e-7, denom)
    dew_point = (MAGNUS_B * alpha) / denom

    return float(dew_point) if is_scalar else dew_point


def compute_vapor_pressure(
    temp: Union[float, np.ndarray], humi: Union[float, np.ndarray]
) -> Union[float, np.ndarray]:
    """Computes actual atmospheric water vapor pressure e (hPa).
    e = e_s(T) * (RH / 100) where e_s is saturation vapor pressure.
    """
    is_scalar = np.isscalar(temp)
    t = np.asarray(temp, dtype=float)
    rh = np.asarray(humi, dtype=float)
    rh_clamped = np.clip(rh, 0.0, 100.0)

    es = 6.1078 * np.exp((MAGNUS_A * t) / (MAGNUS_B + t))
    vp = es * (rh_clamped / 100.0)

    return float(vp) if is_scalar else vp


def compute_heat_index(
    temp: Union[float, np.ndarray], humi: Union[float, np.ndarray]
) -> Union[float, np.ndarray]:
    """Computes Heat Index / Apparent Temperature (°C) using the Rothfusz regression.
    Heat index is physiologically defined for temperatures >= 20°C (68°F).
    For lower temperatures, heat index defaults directly to dry-bulb air temperature.
    """
    is_scalar = np.isscalar(temp)
    t = np.asarray(temp, dtype=float)
    rh = np.asarray(humi, dtype=float)
    rh_clamped = np.clip(rh, 0.0, 100.0)

    # Convert Celsius to Fahrenheit
    tf = t * 9.0 / 5.0 + 32.0

    # Steadman simple approximation
    hi_simple = 0.5 * (tf + 61.0 + ((tf - 68.0) * 1.2) + (rh_clamped * 0.094))

    # Full Rothfusz polynomial
    hi_full = (
        -42.379
        + 2.04901523 * tf
        + 10.14333127 * rh_clamped
        - 0.22475541 * tf * rh_clamped
        - 0.00683783 * (tf**2)
        - 0.05481717 * (rh_clamped**2)
        + 0.00122874 * (tf**2) * rh_clamped
        + 0.00085282 * tf * (rh_clamped**2)
        - 0.00000199 * (tf**2) * (rh_clamped**2)
    )

    # Low humidity adjustment
    adj1_mask = (rh_clamped < 13.0) & (tf >= 80.0) & (tf <= 112.0)
    adj1 = np.where(
        adj1_mask,
        ((13.0 - rh_clamped) / 4.0)
        * np.sqrt(np.maximum(0.0, (17.0 - np.abs(tf - 95.0)) / 17.0)),
        0.0,
    )

    # High humidity adjustment
    adj2_mask = (rh_clamped > 85.0) & (tf >= 80.0) & (tf <= 87.0)
    adj2 = np.where(
        adj2_mask,
        ((rh_clamped - 85.0) / 10.0) * ((87.0 - tf) / 5.0),
        0.0,
    )

    hi_adjusted = hi_full - adj1 + adj2
    hi_f = np.where(hi_simple >= 80.0, hi_adjusted, hi_simple)
    hi_c = (hi_f - 32.0) * 5.0 / 9.0

    # Only apply heat index when air temperature >= 20.0°C
    result = np.where(t >= 20.0, hi_c, t)
    return float(result) if is_scalar else result
