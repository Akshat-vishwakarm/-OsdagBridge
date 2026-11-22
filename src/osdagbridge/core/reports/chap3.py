# =============================================================================
# Chapter 3: Loads and Load Combinations
# Refactored for FOSSEE screening requirements:
#   - Separate Vehicle Live Loads and Footway Loads tables
#   - Dynamic vehicle selection from input parameters
#   - Inclusion of Centrifugal Force per IRC 6 Cl. 212
#   - Repeated table headers across page breaks (LongTable endfirsthead/endhead)
#   - Centralized styling integration
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_CB_LOAD,
    KEY_FOOTPATH,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE
)

from osdagbridge.core.reports.report_utils import _tex, _render_value
from osdagbridge.core.reports.styles import build_longtable_header


def ch3_loads(input_dict: dict) -> str:
    # -------------------------------------------------------------------------
    # 1. Dynamic Live Load Vehicle Mapping
    # -------------------------------------------------------------------------
    vehicles = []
    if input_dict.get(KEY_LL_IRC_CLASS_A):
        vehicles.append("IRC Class A")
    if input_dict.get(KEY_LL_IRC_70R_WHEELED):
        vehicles.append("IRC Class 70R (Wheeled)")
    if input_dict.get(KEY_LL_IRC_70R_TRACKED):
        vehicles.append("IRC Class 70R (Tracked)")
    if input_dict.get(KEY_LL_IRC_AA_WHEELED):
        vehicles.append("IRC Class AA (Wheeled)")
    if input_dict.get(KEY_LL_IRC_AA_TRACKED):
        vehicles.append("IRC Class AA (Tracked)")
    if input_dict.get(KEY_LL_IRC_CLASS_SV):
        vehicles.append("IRC Class SV (Special Vehicle)")
    if input_dict.get(KEY_LL_IRC_70R_BOGIE):
        vehicles.append("IRC Class 70R (Bogie)")
    if input_dict.get(KEY_LL_IRC_CLASS_FATIGUE):
        vehicles.append("IRC Class Fatigue Vehicle")

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            if isinstance(c, dict) and c.get('name'):
                vehicles.append(f"Custom: {c['name']}")
            elif isinstance(c, str):
                vehicles.append(f"Custom: {c}")

    vehicles_str = ", ".join(vehicles) if vehicles else "None Specified"

    # -------------------------------------------------------------------------
    # 2. Impact Factor Calculation (IRC 6 Cl. 208)
    # -------------------------------------------------------------------------
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
    span = input_dict.get(KEY_SPAN)
    impact_factor_str = "N/A"
    if span not in (None, ""):
        try:
            span_m = float(span)
            factors = []
            if input_dict.get(KEY_LL_IRC_CLASS_A):
                im_a = IRC6_2017.cl_208_2_impact_factor(span_m)
                factors.append(f"Class A: {1.0 + im_a:.3f} (fraction = {im_a:.3f})")
            is_wheeled_heavy = (
                input_dict.get(KEY_LL_IRC_70R_WHEELED) or
                input_dict.get(KEY_LL_IRC_AA_WHEELED) or
                input_dict.get(KEY_LL_IRC_70R_BOGIE)
            )
            is_tracked_heavy = (
                input_dict.get(KEY_LL_IRC_70R_TRACKED) or
                input_dict.get(KEY_LL_IRC_AA_TRACKED)
            )
            if is_wheeled_heavy or is_tracked_heavy:
                im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
                factors.append(f"Class AA / 70R: {1.0 + im_aa:.3f} (fraction = {im_aa:.3f})")

            if factors:
                impact_factor_str = ", ".join(factors)
        except Exception:
            impact_factor_str = "N/A"

    # -------------------------------------------------------------------------
    # 3. Braking Force (IRC 6 Cl. 211.2)
    # -------------------------------------------------------------------------
    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    braking_force_str = "N/A"
    if lanes not in (None, ""):
        try:
            lanes_int = int(lanes)
            braking_force_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
            braking_force_kN = braking_force_t * 9.81
            braking_force_str = f"{braking_force_kN:.2f} kN ({braking_force_t:.2f} tonnes)"
        except Exception:
            braking_force_str = "N/A"

    # -------------------------------------------------------------------------
    # 4. Centrifugal Force (IRC 6 Cl. 212)
    # -------------------------------------------------------------------------
    # For straight bridges (standard I-girder configuration), radius R = infinity, force = 0.
    centrifugal_force_str = "Nil / Not Applicable (Straight Alignment per IRC 6 Cl. 212)"

    # -------------------------------------------------------------------------
    # 5. Footway / Pedestrian Loading (IRC 6 Cl. 206.1 & IRC 5 Cl. 104.3.6)
    # -------------------------------------------------------------------------
    fp_mode = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "As per IRC 6")
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    footpath_prov = input_dict.get(KEY_FOOTPATH, "None")
    footpath_width = input_dict.get(KEY_TS_FOOTPATH_WIDTH, "0.0")

    if str(fp_mode).strip().lower() in ("as per irc 6", "as per irc6", "automatic"):
        try:
            fp_str = f"{IRC6_2017.cl_206_1_footway_load():.3f} kN/m² (IRC 6 Cl. 206.1 code default)"
        except Exception:
            fp_str = "4.905 kN/m² (500 kg/m² per IRC 6 Cl. 206.1)"
    elif fp_value not in (None, ""):
        fp_str = f"{fp_value} kN/m² (User Defined)"
    else:
        fp_str = "4.905 kN/m² (IRC 6 Cl. 206.1)"

    # -------------------------------------------------------------------------
    # 6. Wind & Seismic Parameters
    # -------------------------------------------------------------------------
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get('wind_speed')
            _h = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
            _ter = {
                "Plain Terrain": "plain",
                "Terrain with Obstructions": "obstructed",
            }.get(str(input_dict.get(KEY_WL_TERRAIN_TYPE, "")).strip(), "plain")
            _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))
            if not vz_val:
                vz_val = _res.get("Vz")
            if not pz_val:
                pz_val = _res.get("Pz")
        except Exception:
            pass
    vz_str = f"{float(vz_val):.2f} m/s" if vz_val not in (None, "") else "N/A"
    pz_str = f"{float(pz_val):.2f} N/m²" if pz_val not in (None, "") else "N/A"

    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res = IRC6_2017.cl_218_5_1(
                zone=f"Zone {_z}",
                soil_type=_st,
                dead_load_kN=_dead,
                live_load_kN=_live,
                period_T=float(_tp) if _tp else None,
                damping_percent=float(_damp)
            )
            if not sl_zone_factor:
                sl_zone_factor = _res.get("Z")
            if not sl_spectral:
                sl_spectral = _res.get("Sa_g_adjusted")
            if not sl_ah:
                sl_ah = _res.get("Ah")
            if not sl_av:
                sl_av = round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # 7. Temperature Load
    # -------------------------------------------------------------------------
    tl_temp_min = tl_temp_max = tl_rise = tl_fall = "N/A"
    try:
        _tmax = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get('shade_temp_max')
        _tmin = input_dict.get(KEY_TL_LOWEST_MIN_TEMP) or input_dict.get('shade_temp_min')
        if _tmax and _tmin:
            _res = IRC6_2017.cl_215_2_effective_bridge_temperature(
                float(_tmax), float(_tmin), 'metallic', False
            )
            _bt_min = _res.get('T_min', 0)
            _bt_max = _res.get('T_max', 0)
            _mean = (_bt_max + _bt_min) / 2.0
            tl_temp_min = f"{_bt_min:.2f}"
            tl_temp_max = f"{_bt_max:.2f}"
            tl_rise = f"{_bt_max - _mean:.2f}"
            tl_fall = f"{_mean - _bt_min:.2f}"
    except Exception:
        pass

    # -------------------------------------------------------------------------
    # 8. Load Combinations
    # -------------------------------------------------------------------------
    _LOAD_LABEL_MAP = {
        'dead_load': 'DL',
        'surfacing': 'SIDL',
        'live_load': 'LL',
        'wind_load': 'WL',
        'thermal_load': 'TL',
        'vehicle_collision': 'VC',
        'barge_impact': 'BI',
        'floating_bodies': 'FB',
        'seismic': 'EQ',
    }

    def _fmt_factors(factors):
        parts = []
        for load, val in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):
                add = val.get('adding')
                rel = val.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '--'
                rel_s = f"{rel:.2f}" if rel is not None else '--'
                parts.append(f"{label}({add_s}/{rel_s})")
            else:
                if val is None:
                    continue
                parts.append(f"{label}({val:.2f})")
        return ' + '.join(parts)

    uls_combos = IRC6_2017.uls_load_combinations()
    sls_combos = IRC6_2017.sls_load_combinations()
    lc_rows = []
    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(f"ULS-{i:02d} & {cases} \\\\[6pt]\n\\hline")
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(f"SLS-{i:02d} & {cases} \\\\[6pt]\n\\hline")

    lc_rows_str = "\n".join(lc_rows)

    # -------------------------------------------------------------------------
    # LongTable Header Definitions with Repeated Headers across pages
    # -------------------------------------------------------------------------
    param_hdr = r"\textbf{Parameter} & \textbf{Value} \\"

    hdr_31 = build_longtable_header("Dead Load --- Self Weight", 2, param_hdr, "tab:dl-self-weight")
    hdr_32 = build_longtable_header("Dead Load for Surfacing (DW / SIDL)", 2, param_hdr, "tab:dl-surfacing")
    hdr_33 = build_longtable_header("Vehicle Live Loads (LL) --- per IRC 6", 2, param_hdr, "tab:vehicle-live-load")
    hdr_34 = build_longtable_header("Footway Live Loads --- per IRC 6 & IRC 5", 2, param_hdr, "tab:footway-load")
    hdr_35 = build_longtable_header("Wind Load (WL) --- per IRC 6", 2, param_hdr, "tab:wind-load")
    hdr_36 = build_longtable_header("Earthquake Load (EL) --- per IRC 6", 2, param_hdr, "tab:earthquake-load")
    hdr_37 = build_longtable_header("Temperature Load (TL) --- per IRC 6", 2, param_hdr, "tab:temperature-load")
    hdr_38 = build_longtable_header("Load Combinations (ULS and SLS) --- IRC 6 Table B.1 to B.4", 2, r"\textbf{Combination ID} & \textbf{Load Cases and Partial Safety Factors} \\", "tab:load-combos")

    return r"""
\chapter{Loads and Load Combinations}
\label{ch:loads-combinations}

This section summarizes all permanent and transient loads applied to the bridge and the governing load combinations evaluated for analysis and design per IRC 6:2017.

\vspace{1em}
\begin{longtable}{|L{6.0cm}|p{9.5cm}|}
""" + hdr_31 + r"""
\textnormal{Steel Self-Weight Applied} & """ + (_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, r' kN/m\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Concrete Deck Weight} & """ + (_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, r' kN/m\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Self-Weight Factor} & """ + (_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{6.0cm}|p{9.5cm}|}
""" + hdr_32 + r"""
\textnormal{Wearing Course Material} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" \\[6pt]
\hline
\textnormal{Wearing Course Thickness} & """ + (_render_value(input_dict, KEY_WC_THICKNESS, ' mm')) + r""" \\[6pt]
\hline
\textnormal{Additional SIDL (Crash Barrier)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" kN/m per barrier \\[6pt]
\hline
\textnormal{Railing Load} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" kN/m\sdstar{} \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{6.0cm}|p{9.5cm}|}
""" + hdr_33 + r"""
\textnormal{Selected Live Load Vehicle Class} & \textbf{""" + _tex(vehicles_str) + r"""} \\[6pt]
\hline
\textnormal{Impact Factor ($1.0 + i$)} & """ + _tex(impact_factor_str) + r""" \\[6pt]
\hline
\textnormal{Braking Load ($F_b$)} & """ + _tex(braking_force_str) + r""" \\[6pt]
\hline
\textnormal{Centrifugal Force ($F_{cf}$)} & """ + _tex(centrifugal_force_str) + r""" \\[6pt]
\hline
\textnormal{Number of Traffic Lanes} & """ + (_render_value(input_dict, KEY_WC_LD_LANE_TABLE_COUNT)) + r""" (per IRC 5 Cl. 104.3.1) \\[6pt]
\hline
\textnormal{Carriageway Width} & """ + (_render_value(input_dict, KEY_CARRIAGEWAY_WIDTH, ' m')) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{6.0cm}|p{9.5cm}|}
""" + hdr_34 + r"""
\textnormal{Footway Provision} & """ + _tex(footpath_prov) + r""" \\[6pt]
\hline
\textnormal{Footpath Width} & """ + _tex(footpath_width) + r""" m (IRC 5 Cl. 104.3.6 min: 1.5 m) \\[6pt]
\hline
\textnormal{Footway Loading Calculation Mode} & """ + _tex(fp_mode) + r""" \\[6pt]
\hline
\textnormal{Footway Live Load Intensity} & """ + _tex(fp_str) + r""" \\[6pt]
\hline
\textnormal{Railing Load on Footway} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE, ' kN/m')) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{6.0cm}|p{9.5cm}|}
""" + hdr_35 + r"""
\textnormal{Basic Wind Speed, $V_b$} & """ + (_render_value(input_dict, 'wind_speed', ' m/s')) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Terrain Type} & """ + (_render_value(input_dict, KEY_WL_TERRAIN_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Average Exposed Height, $H$} & """ + (_render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m')) + r""" \\[6pt]
\hline
\textnormal{Hourly Mean Wind Speed, $V_z$} & """ + (_render_value(input_dict, KEY_WL_HOURLY_MEAN_WIND, ' m/s')) + r""" \\[6pt]
\hline
\textnormal{Hourly Wind Pressure, $P_z$} & """ + (_render_value(input_dict, KEY_WL_HOURLY_WIND_PRESSURE, r' N/m\textsuperscript{2}')) + r""" \\[6pt]
\hline
\textnormal{Transverse Wind Force} & """ + (_render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\textnormal{Longitudinal Wind Force} & """ + (_render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\textnormal{Vertical Wind Force} & """ + (_render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{6.0cm}|p{9.5cm}|}
""" + hdr_36 + r"""
\textnormal{Seismic Zone} & """ + (_render_value(input_dict, 'seismic_zone')) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Zone Factor, $Z$} & """ + (_render_value(input_dict, KEY_SL_ZONE_FACTOR)) + r""" \\[6pt]
\hline
\textnormal{Importance Factor, $I$} & """ + (_render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR)) + r""" \\[6pt]
\hline
\textnormal{Type of Soil} & """ + (_render_value(input_dict, KEY_SL_SOIL_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Average Response Acceleration, $S_a/g$} & """ + (_render_value(input_dict, KEY_SL_SPECTRAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Coefficient, $A_h$} & """ + (_render_value(input_dict, KEY_SL_HORIZONTAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Vertical Seismic Coefficient, $A_v$} & """ + (_render_value(input_dict, KEY_SL_VERTICAL_COEFF)) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{6.0cm}|p{9.5cm}|}
""" + hdr_37 + r"""
\textnormal{Maximum Shade Temperature} & """ + (_render_value(input_dict, 'shade_temp_max')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Minimum Shade Temperature} & """ + (_render_value(input_dict, 'shade_temp_min')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Effective Bridge Temp. Range} & """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN)) + r""" to """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX)) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Temperature Rise / Fall for Design} & +""" + (_render_value(input_dict, KEY_TL_TEMP_RISE)) + r""" $^\circ$C / \textminus{}""" + (_render_value(input_dict, KEY_TL_TEMP_FALL)) + r""" $^\circ$C \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|C{3.8cm}|p{11.7cm}|}
""" + hdr_38 + r"""
""" + lc_rows_str + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""
