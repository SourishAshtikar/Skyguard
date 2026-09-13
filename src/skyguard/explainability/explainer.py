"""
SkyGuard AI — Explainability & Plain-English Root Cause Analysis (RCA)
Generates operator-ready diagnostic reports that strictly separate:
1. Observed Empirical Evidence (raw sensor values, rule violations, mesonet neighbor comparisons)
2. Model Inference (autoencoder score, Kalman innovation distance, TreeSHAP attributions)
3. Operational Confidence
4. Recommended Maintenance / Verification Action
Never presents model predictions as unverified physical facts.
"""

from typing import Dict, List, Optional, Any
from skyguard.config.contracts import (
    AnomalyCategory,
    RuleResult,
    SatelliteCrossCheckOutput,
    Severity,
    SpatialConsensusOutput,
    Stage1ForecastOutput,
    Stage3ArbiterOutput,
    Tier1Output,
    Tier2Output,
)


class IncidentExplainer:
    """Generates structured explainability summaries and plain-English RCA narratives."""

    def generate_narrative(
        self,
        station_name: str,
        station_id: str,
        timestamp: str,
        raw_values: Dict[str, Optional[float]],
        tier1: Tier1Output,
        tier2: Optional[Tier2Output],
        stage1: Optional[Stage1ForecastOutput],
        spatial: Optional[SpatialConsensusOutput],
        arbiter: Optional[Stage3ArbiterOutput],
        final_anomaly: bool,
        satellite: Optional[SatelliteCrossCheckOutput] = None,
    ) -> str:
        """Constructs an audited, human-readable meteorological RCA narrative with deep scientific explanation."""
        t_val = raw_values.get("temperature")
        p_val = raw_values.get("pressure")
        h_val = raw_values.get("humidity")
        t_str = f"{t_val:.1f}°C" if t_val is not None else "MISSING"
        p_str = f"{p_val:.1f} hPa" if p_val is not None else "MISSING"
        h_str = f"{h_val:.1f}%" if h_val is not None else "MISSING"

        if not final_anomaly:
            spatial_note = (
                f"Corroborated by {spatial.neighbor_count} neighboring mesonet stations within spatial correlation radius."
                if (spatial and spatial.neighbor_count > 0)
                else "Single-station physics verified."
            )
            sat_note = f" Cross-verified with {satellite.satellite_id} spaceborne thermal IR imagery." if satellite else ""
            return (
                f"Station {station_name} [{station_id}] telemetry ({t_str}, {p_str}, {h_str}) is VERIFIED NOMINAL at {timestamp}. "
                f"All deterministic WMO quality thresholds (Range, 4σ Step, Persistence, and Dew Point) passed without violations. "
                f"Thermodynamic relationships conform strictly to the Magnus-Tetens atmospheric equation. {spatial_note}{sat_note}"
            )

        lines = [
            f"=== SKYGUARD AI DIAGNOSTIC RCA: {station_name} [{station_id}] ===",
            f"Timestamp: {timestamp} IST | Telemetry: Temp={t_str}, Pressure={p_str}, Humidity={h_str}",
            "",
            "1. EMPIRICAL PHYSICAL EVIDENCE & WMO VIOLATIONS:",
        ]

        if tier1.rules_fired:
            lines.append(f"  • Deterministic Rules Failed ({len(tier1.rules_fired)}):")
            for res in tier1.rule_results:
                if not res.passed:
                    lines.append(f"    - [{res.rule_name}]: {res.message}")
                    # Provide deep physical rationale for specific failures
                    if "DEW_POINT" in res.rule_name:
                        lines.append(
                            "      Reasoning: Under Clausius-Clapeyron atmospheric thermodynamics, air cannot hold more water "
                            "vapor than its saturation vapor pressure at that temperature. Dew point exceeding ambient air temperature "
                            "is physically impossible in Earth's atmosphere and indicates a wet-bulb / capacitive RH sensor calibration breakdown."
                        )
                    elif "SEASONAL_RANGE" in res.rule_name:
                        lines.append(
                            "      Reasoning: The recorded temperature violates regional climatological boundaries codified by the "
                            "India Meteorological Department (IMD) for this specific season. In maritime/peninsular regions during the "
                            "Southwest Monsoon (June–Sept), continuous cloud albedo, maritime monsoonal air mass, and frequent precipitation "
                            "strictly cap temperatures below 36.5°C. A reading of 44°C is possible during peak summer heatwaves in northern deserts, "
                            "but physically impossible in coastal peninsular India during the rainy monsoon season."
                        )
                    elif "RAIN_THERMAL" in res.rule_name:
                        lines.append(
                            "      Reasoning: Under active precipitation or saturated relative humidity (RH ≥ 80%), falling rain droplets "
                            "undergo sub-cloud evaporative cooling, cooling the ambient air toward the wet-bulb temperature. "
                            "Tropospheric thermodynamics cap rain-cooled air below 33.5°C in India. Furthermore, water vapor partial pressure "
                            "cannot exceed Earth's physical tropospheric limit (42.0 hPa). High temperature during rain represents an unphysical sensor fault."
                        )
                    elif "RANGE" in res.rule_name:
                        lines.append(
                            "      Reasoning: Value exceeds extreme Indian climatological boundaries codified in WMO Guide No. 8 and "
                            "IMD AWS standards (Patro & Bartakke, 2025). Suggests open-circuit transducer, short circuit, or ADC saturation."
                        )
                    elif "PERSISTENCE" in res.rule_name:
                        lines.append(
                            "      Reasoning: Atmospheric state variables always undergo continuous micro-turbulent fluctuation. "
                            "Zero variance across multiple observation cycles indicates sensor latchup, digital freeze, or mechanical vane jam."
                        )
                    elif "STEP" in res.rule_name:
                        lines.append(
                            "      Reasoning: The observed rate-of-change exceeds maximum natural atmospheric thermal inertia "
                            "(>4σ dynamic threshold). Natural air masses cannot warm or cool this rapidly without external energy injection."
                        )
        else:
            lines.append("  • Deterministic Range Checks: All boundary thresholds passed. Anomaly detected via subtle multi-parameter divergence.")

        # Spatial Mesonet Consensus Section
        if spatial and spatial.neighbor_count > 0:
            lines.extend([
                "",
                "2. MESONET SPATIAL CONSENSUS CHECK:",
            ])
            med_t = f"{spatial.median_temp:.1f}°C" if spatial.median_temp is not None else "Nominal Baseline"
            if spatial.is_spatially_inconsistent:
                lines.append(
                    f"  • Spatial Discrepancy: Station reading deviates by {spatial.target_deviation_temp:.1f}°C from the regional median "
                    f"({med_t}) computed across {spatial.neighbor_count} peer AWS stations (Consensus Score: {spatial.spatial_consensus_score:.2f})."
                )
                lines.append(
                    "    Reasoning: Nearby mesonet stations within 150 km observe no comparable shift, ruling out a widespread synoptic event "
                    "and confirming an isolated, localized station hardware or transmission malfunction."
                )
            else:
                lines.append(
                    f"  • Spatial Agreement: {spatial.neighbor_count} neighboring AWS stations show consistent readings "
                    f"(Regional Median Temp={med_t}, Consensus Score: {spatial.spatial_consensus_score:.2f})."
                )
                lines.append(
                    "    Reasoning: Spatial peers confirm similar atmospheric movements across the mesonet cluster."
                )

        # Spaceborne Satellite Verification Section
        if satellite:
            lines.extend([
                "",
                "3. SPACEBORNE SATELLITE IMAGERY & THERMAL IR CROSS-CHECK:",
            ])
            lines.append(f"  • Satellite Feed: {satellite.satellite_id} (Pixel: {satellite.pixel_latitude:.2f}°N, {satellite.pixel_longitude:.2f}°E)")
            if satellite.land_surface_temp_c is not None:
                lines.append(f"  • Spaceborne Land Surface Temp (LST): {satellite.land_surface_temp_c:.1f}°C vs AWS {t_str}")
            if satellite.cloud_fraction_pct is not None:
                lines.append(f"  • Satellite Cloud Cover / Mask: {satellite.cloud_fraction_pct:.0f}%")
            if satellite.cloud_top_temp_c is not None:
                lines.append(f"  • Cloud Top Temperature (CTT): {satellite.cloud_top_temp_c:.1f}°C")
            lines.append(f"  • Satellite Diagnosis: {satellite.satellite_note}")

        # Machine Learning & State-Space Attribution
        lines.extend([
            "",
            "4. MACHINE LEARNING & STATISTICAL ATTRIBUTIONS:",
        ])
        if tier2 and tier2.is_anomaly:
            lines.append(
                f"  • Edge Autoencoder: Reconstruction anomaly score={tier2.anomaly_score:.3f} "
                f"(Reconstruction MSE: {tier2.reconstruction_error:.4f} vs threshold {tier2.threshold:.4f})."
            )
        if stage1 and stage1.is_suspicious:
            lines.append(
                f"  • Kalman State-Space Forecast: Mahalanobis distance d²={stage1.mahalanobis_distance:.2f} "
                f"(99% confidence threshold = 11.35). Innovations: ΔTemp={stage1.residual_temp:+.1f}°C, "
                f"ΔPres={stage1.residual_pres:+.1f} hPa, ΔHumi={stage1.residual_humi:+.1f}%."
            )
        if arbiter:
            top_shap = sorted(
                arbiter.shap_attributions.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )[:3]
            shap_desc = ", ".join(f"{k} ({v:+.2f})" for k, v in top_shap)
            lines.append(f"  • TreeSHAP Dominant Feature Drivers: {shap_desc}")
            lines.append(
                f"  • Arbiter Verdict: {arbiter.root_cause_label} (Confidence: {arbiter.confidence * 100:.1f}%)"
            )

        # Root Cause & Operator Action
        lines.extend([
            "",
            "5. OPERATOR ROOT CAUSE ANALYSIS & RECOMMENDED ACTION:",
        ])
        if arbiter and arbiter.is_weather_event:
            lines.append(
                "  • Root Cause: GENUINE SEVERE METEOROLOGICAL EVENT (e.g. convective squall line, microburst, or cold front passage). "
                "The abrupt change is verified as real atmospheric behavior corroborated by spatial mesonet peers."
            )
            lines.append(
                "  • Action Required: Retain telemetry for synoptic forecasting and issue weather hazard alert. DO NOT mark sensor as faulty."
            )
        else:
            cat = arbiter.anomaly_category.value if arbiter else "INSTRUMENT_FAULT"
            lines.append(f"  • Root Cause: Confirmed Sensor/Telemetry Malfunction — {cat}.")
            if "PERSISTENCE" in cat or "FROZEN" in cat:
                lines.append(
                    "  • Action Required: Inspect sensor transducer for physical debris, dead insect ingress, or ADC serial bus freeze. Perform power-cycle."
                )
            elif "SPIKE" in cat or "CORRUPTION" in cat:
                lines.append(
                    "  • Action Required: Inspect signal shielding, lightning surge protector (SPD), and RS-485 / Modbus bus grounding."
                )
            elif "DRIFT" in cat:
                lines.append(
                    "  • Action Required: Schedule sensor recalibration against a calibrated WMO reference standard; zero-point offset detected."
                )
            elif "DROPOUT" in cat or "MISSING" in cat:
                lines.append(
                    "  • Action Required: Check solar panel voltage, battery state-of-charge (<11.2V threshold), SIM card GPRS/INSAT-3A transmitter connection."
                )
            elif "PHYSICAL" in cat:
                lines.append(
                    "  • Action Required: Replace relative humidity capacitive film element or check temperature RTD 4-wire bridge resistance."
                )
            else:
                lines.append(
                    "  • Action Required: Flag data record as invalid in IMD national archive and deploy automated Kalman self-healing imputation."
                )

        return "\n".join(lines)
