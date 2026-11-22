"""
OsdagBridge — Engineering Report Chart Generator
================================================
Generates high-resolution Matplotlib figures for:
  1. Section 5.5: Overall Design Check Summary (Utilization Ratios)
  2. Chapter 7: Material Take-off & Quantity Summary (Steel Tonnage, Concrete & Rebar)

All styles and color palettes are driven by styles.py.
"""

from __future__ import annotations
import os
import logging
from typing import Dict, Any, Optional, Tuple, List
import matplotlib.pyplot as plt
import numpy as np

from osdagbridge.core.utils.common import (
    KEY_UTIL_FLEXURE,
    KEY_UTIL_SHEAR,
    KEY_UTIL_INTERACTION,
    KEY_UTIL_LTB,
    KEY_DD_M_ULS_SAG,
    KEY_DD_MU_BOT,
    KEY_DD_M_ULS_HOG,
    KEY_DD_MU_TOP,
    KEY_DD_PUNCH_VED,
    KEY_DD_VRD_C_MPA,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_DD_WK_BOT,
    KEY_DD_WK_TOP,
    KEY_DD_WK_OH,
    KEY_DD_WK_LIMIT,
    KEY_MP_ED_TYPE,
)

from .styles import (
    apply_chart_style,
    COLOR_PASS_HEX,
    COLOR_FAIL_HEX,
    COLOR_THRESHOLD_HEX,
    COLOR_STEEL_GIRDER_HEX,
    COLOR_STEEL_BRACING_HEX,
    COLOR_STEEL_DIAPHRAGM_HEX,
    COLOR_CONCRETE_HEX,
    COLOR_REBAR_HEX,
    COLOR_OSDAG_GREEN_HEX,
    COLOR_SLATE_HEX,
)

logger = logging.getLogger(__name__)


# =============================================================================
# 1. SECTION 5.5 UTILIZATION RATIO BAR CHART
# =============================================================================

def generate_utilization_chart(ur_data: Dict[str, Optional[float]], output_path: str) -> Optional[str]:
    """
    Generate the Section 5.5 Overall Design Check Summary Utilization Ratio chart.

    Parameters
    ----------
    ur_data : Dict[str, Optional[float]]
        Dictionary with keys:
          - "Steel Plate Girders"
          - "Concrete Deck Slab"
          - "Cross Bracing"
          - "End Diaphragms"
        Values are float utilization ratios or None if uncalculated.
    output_path : str
        Target PNG file path.

    Returns
    -------
    Optional[str]
        Path to saved PNG, or None if generation failed.
    """
    try:
        apply_chart_style()
        fig, ax = plt.subplots(figsize=(7.5, 4.2))

        elements = [
            "Steel Plate Girders",
            "Concrete Deck Slab",
            "Cross Bracing",
            "End Diaphragms",
        ]

        raw_values = [ur_data.get(el) for el in elements]
        x_indices = np.arange(len(elements))
        bar_width = 0.52

        # Plot bars with color based on Pass (<= 1.0) vs Fail (> 1.0)
        bars = []
        has_pass = False
        has_fail = False

        max_val = 1.2
        for i, (el, val) in enumerate(zip(elements, raw_values)):
            if val is not None:
                color = COLOR_PASS_HEX if val <= 1.0 else COLOR_FAIL_HEX
                if val <= 1.0:
                    has_pass = True
                else:
                    has_fail = True
                bar = ax.bar(i, val, width=bar_width, color=color, edgecolor="#333333", linewidth=0.8, zorder=3)
                bars.append(bar)
                # Value label on top of bar
                ax.annotate(
                    f"{val:.2f}",
                    xy=(i, val),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=9.5,
                    fontweight="bold",
                    color=color,
                )
                if val > max_val:
                    max_val = val
            else:
                # Missing value representation
                bar = ax.bar(i, 0.05, width=bar_width, color="#D5D8DC", edgecolor="#999999", linestyle=":", linewidth=0.8, zorder=3)
                bars.append(bar)
                ax.annotate(
                    "N/A",
                    xy=(i, 0.06),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    fontstyle="italic",
                    color="#7F8C8D",
                )

        # Horizontal threshold line at UR = 1.0
        threshold_line = ax.axhline(
            y=1.0,
            color=COLOR_THRESHOLD_HEX,
            linestyle="--",
            linewidth=1.6,
            label="Threshold Limit (UR = 1.0)",
            zorder=4,
        )

        ax.set_xticks(x_indices)
        ax.set_xticklabels(elements, fontweight="bold")
        ax.set_ylabel("Utilization Ratio (UR = Demand / Capacity)")
        ax.set_title("Overall Design Check Summary — Component Utilization Ratios", pad=12)
        ax.set_ylim(0, max_val * 1.18)
        ax.yaxis.grid(True, linestyle="--", alpha=0.6, zorder=0)
        ax.set_axisbelow(True)

        # Legend handles
        from matplotlib.patches import Patch
        legend_elements = [threshold_line]
        if has_pass:
            legend_elements.append(Patch(facecolor=COLOR_PASS_HEX, edgecolor="#333333", label="Passing (UR ≤ 1.0)"))
        if has_fail:
            legend_elements.append(Patch(facecolor=COLOR_FAIL_HEX, edgecolor="#333333", label="Failing (UR > 1.0)"))
        
        ax.legend(handles=legend_elements, loc="upper right", framealpha=0.92, facecolor="#FAFAFA")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        logger.info("Generated Section 5.5 utilization chart: %s", output_path)
        return output_path
    except Exception as exc:
        logger.warning("Failed to generate utilization chart: %s", exc)
        plt.close("all")
        return None


# =============================================================================
# 2. CHAPTER 7 MATERIAL QUANTITY BAR CHARTS
# =============================================================================

def generate_material_charts(quantities: Dict[str, Any], output_dir: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Generate Chapter 7 Material Take-Off Bar Charts:
      Chart A: Structural Steel Tonnage Breakdown (Girders, Cross Bracing, End Diaphragms)
      Chart B: Concrete Volume & Reinforcement Steel Weight

    Parameters
    ----------
    quantities : Dict[str, Any]
        Dictionary of calculated quantities from boq_generator.
    output_dir : str
        Directory to save generated chart PNG images.

    Returns
    -------
    Tuple[Optional[str], Optional[str]]
        (path_chart_a, path_chart_b)
    """
    path_a = os.path.join(output_dir, "material_steel_tonnage.png")
    path_b = os.path.join(output_dir, "material_concrete_rebar.png")

    os.makedirs(output_dir, exist_ok=True)
    apply_chart_style()

    # -------------------------------------------------------------------------
    # Chart A: Structural Steel Tonnage
    # -------------------------------------------------------------------------
    res_a = None
    try:
        fig_a, ax_a = plt.subplots(figsize=(6.8, 3.8))

        def _to_float(val):
            try:
                return float(str(val).replace(",", "").strip())
            except (ValueError, TypeError):
                return 0.0

        girders_wt = _to_float(quantities.get("steel_girders_wt_total"))
        cb_top = _to_float(quantities.get("bracing_top_wt_total"))
        cb_bot = _to_float(quantities.get("bracing_bot_wt_total"))
        cb_diag = _to_float(quantities.get("bracing_diag_wt_total"))
        bracing_total = cb_top + cb_bot + cb_diag
        if bracing_total == 0.0:
            bracing_total = _to_float(quantities.get("steel_bracing_wt_total"))
        
        diaphragm_wt = _to_float(quantities.get("steel_diaphragm_wt_total", 0.0))

        steel_items = ["Girders", "Cross Bracing", "End Diaphragms"]
        steel_weights = [girders_wt, bracing_total, diaphragm_wt]
        colors = [COLOR_STEEL_GIRDER_HEX, COLOR_STEEL_BRACING_HEX, COLOR_STEEL_DIAPHRAGM_HEX]

        x_pos = np.arange(len(steel_items))
        bars_a = ax_a.bar(x_pos, steel_weights, width=0.48, color=colors, edgecolor="#2C3E50", linewidth=0.8, zorder=3)

        max_steel = max(steel_weights) if max(steel_weights) > 0 else 10.0
        ax_a.set_ylim(0, max_steel * 1.22)

        for i, val in enumerate(steel_weights):
            txt = f"{val:.2f} MT" if val > 0 else "N.A."
            ax_a.annotate(
                txt,
                xy=(i, val),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9.5,
                fontweight="bold",
                color="#2C3E50",
            )

        ax_a.set_xticks(x_pos)
        ax_a.set_xticklabels(steel_items, fontweight="bold")
        ax_a.set_ylabel("Weight (Metric Tonnes)")
        ax_a.set_title("Structural Steel Tonnage Breakdown (IS 2062)", pad=10)
        ax_a.yaxis.grid(True, linestyle="--", alpha=0.6, zorder=0)
        ax_a.set_axisbelow(True)

        fig_a.savefig(path_a, dpi=300, bbox_inches="tight")
        plt.close(fig_a)
        res_a = path_a
    except Exception as exc:
        logger.warning("Failed to generate steel tonnage chart: %s", exc)
        plt.close("all")

    # -------------------------------------------------------------------------
    # Chart B: Concrete Volume & Reinforcement Steel Weight
    # -------------------------------------------------------------------------
    res_b = None
    try:
        fig_b, ax_b1 = plt.subplots(figsize=(6.8, 3.8))

        concrete_vol = _to_float(quantities.get("concrete_deck_vol_total"))
        rebar_wt = _to_float(quantities.get("rebar_deck_wt_total"))

        labels = ["Concrete Deck Slab\n(Volume)", "Reinforcement Steel\n(Weight)"]
        values = [concrete_vol, rebar_wt]
        units = ["m³", "MT"]
        colors_b = [COLOR_CONCRETE_HEX, COLOR_REBAR_HEX]

        x_b = np.arange(len(labels))
        bars_b = ax_b1.bar(x_b, values, width=0.44, color=colors_b, edgecolor="#2C3E50", linewidth=0.8, zorder=3)

        max_val_b = max(values) if max(values) > 0 else 10.0
        ax_b1.set_ylim(0, max_val_b * 1.22)

        for i, (val, unit) in enumerate(zip(values, units)):
            txt = f"{val:.2f} {unit}" if val > 0 else "N.A."
            ax_b1.annotate(
                txt,
                xy=(i, val),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9.5,
                fontweight="bold",
                color="#2C3E50",
            )

        ax_b1.set_xticks(x_b)
        ax_b1.set_xticklabels(labels, fontweight="bold")
        ax_b1.set_ylabel("Quantity (m³ / MT)")
        ax_b1.set_title("Concrete and Reinforcement Take-Off", pad=10)
        ax_b1.yaxis.grid(True, linestyle="--", alpha=0.6, zorder=0)
        ax_b1.set_axisbelow(True)

        fig_b.savefig(path_b, dpi=300, bbox_inches="tight")
        plt.close(fig_b)
        res_b = path_b
    except Exception as exc:
        logger.warning("Failed to generate concrete/rebar chart: %s", exc)
        plt.close("all")

    return res_a, res_b


# =============================================================================
# 3. ENGINEERING DATA EXTRACTION HELPER
# =============================================================================

def extract_utilization_ratios(bridge) -> Dict[str, Optional[float]]:
    """
    Extract actual utilization ratios for:
      - Steel Plate Girders
      - Concrete Deck Slab
      - Cross Bracing
      - End Diaphragms
    from bridge outputs (ReportDataBridge).
    Never invents or fabricates numbers. Handles missing values explicitly by returning None.
    """
    ur_dict: Dict[str, Optional[float]] = {
        "Steel Plate Girders": None,
        "Concrete Deck Slab": None,
        "Cross Bracing": None,
        "End Diaphragms": None,
    }

    # 1. Steel Plate Girders
    girder_urs = []
    # Check direct summary keys
    for k in (KEY_UTIL_FLEXURE, KEY_UTIL_SHEAR, KEY_UTIL_INTERACTION, KEY_UTIL_LTB):
        v = bridge.output_dict.get(k)
        if v is not None:
            try:
                fv = float(v)
                if fv > 2.0:  # Value was given as percentage (e.g. 74.05%)
                    fv = fv / 100.0
                girder_urs.append(fv)
            except (ValueError, TypeError):
                pass
    
    # Check per_girder / design_checks
    if hasattr(bridge, "design_checks") and bridge.design_checks:
        for chk in bridge.design_checks:
            dcr = getattr(chk, "dcr", None) or (chk.get("dcr") if isinstance(chk, dict) else None)
            if dcr is not None:
                try:
                    girder_urs.append(float(dcr))
                except (ValueError, TypeError):
                    pass
    
    # Check overall_utilization_ratio
    ov_ur = bridge.output_dict.get("overall_utilization_ratio")
    if ov_ur is not None:
        try:
            girder_urs.append(float(ov_ur))
        except (ValueError, TypeError):
            pass

    if girder_urs:
        ur_dict["Steel Plate Girders"] = round(max(girder_urs), 3)

    # 2. Concrete Deck Slab
    deck_urs = []
    dd_res = bridge.output_dict.get("deck_design_results")
    if isinstance(dd_res, dict):
        for k in ("ur_sagging", "ur_hogging", "ur_shear", "ur_punching"):
            val = dd_res.get(k)
            if val is not None:
                try:
                    deck_urs.append(float(val))
                except (ValueError, TypeError):
                    pass
    
    dd_rpt = bridge.output_dict.get("deck_report_values") or {}
    # Sagging flexure
    m_uls_sag = dd_rpt.get(KEY_DD_M_ULS_SAG)
    mu_bot = dd_rpt.get(KEY_DD_MU_BOT)
    if m_uls_sag is not None and mu_bot is not None:
        try:
            if float(mu_bot) > 0:
                deck_urs.append(float(m_uls_sag) / float(mu_bot))
        except (ValueError, TypeError):
            pass
    
    # Hogging flexure
    m_uls_hog = dd_rpt.get(KEY_DD_M_ULS_HOG)
    mu_top = dd_rpt.get(KEY_DD_MU_TOP)
    if m_uls_hog is not None and mu_top is not None:
        try:
            if float(mu_top) > 0:
                deck_urs.append(float(m_uls_hog) / float(mu_top))
        except (ValueError, TypeError):
            pass

    # Punching shear
    ved_p = dd_rpt.get(KEY_DD_PUNCH_VED)
    vrdc_p = dd_rpt.get(KEY_DD_VRD_C_MPA)
    if ved_p is not None and vrdc_p is not None:
        try:
            if float(vrdc_p) > 0:
                deck_urs.append(float(ved_p) / float(vrdc_p))
        except (ValueError, TypeError):
            pass

    # One-way shear
    ved_s = dd_rpt.get(KEY_DD_SHEAR_VED)
    vrdc_s = dd_rpt.get(KEY_DD_SHEAR_VRDC)
    if ved_s is not None and vrdc_s is not None:
        try:
            if float(vrdc_s) > 0:
                deck_urs.append(float(ved_s) / float(vrdc_s))
        except (ValueError, TypeError):
            pass

    # Crack width
    try:
        wk_gov = max(
            float(dd_rpt.get(KEY_DD_WK_BOT, 0.0) or 0.0),
            float(dd_rpt.get(KEY_DD_WK_TOP, 0.0) or 0.0),
            float(dd_rpt.get(KEY_DD_WK_OH, 0.0) or 0.0),
        )
        wk_lim = float(dd_rpt.get(KEY_DD_WK_LIMIT, 0.0) or 0.0)
        if wk_lim > 0 and wk_gov > 0:
            deck_urs.append(wk_gov / wk_lim)
    except (ValueError, TypeError):
        pass

    if deck_urs:
        ur_dict["Concrete Deck Slab"] = round(max(deck_urs), 3)

    # 3. Cross Bracing
    cb_urs = []
    # From bridge getter methods
    if hasattr(bridge, "_cb_pairs"):
        for pair in getattr(bridge, "_cb_pairs", []):
            for member in ("diagonal", "chord"):
                for force_type in ("compression", "tension"):
                    eff = bridge.get_cb_efficiency(pair, member, force_type)
                    if eff:
                        try:
                            cb_urs.append(float(eff))
                        except (ValueError, TypeError):
                            pass
    # From crossbracing_design_results directly
    cb_res = bridge.output_dict.get("crossbracing_design_results")
    if isinstance(cb_res, dict):
        for pair_dict in cb_res.values():
            if isinstance(pair_dict, dict):
                for mem_dict in pair_dict.values():
                    if isinstance(mem_dict, dict):
                        for ft_dict in mem_dict.values():
                            if isinstance(ft_dict, dict) and "efficiency" in ft_dict:
                                try:
                                    cb_urs.append(float(ft_dict["efficiency"]))
                                except (ValueError, TypeError):
                                    pass

    if cb_urs:
        ur_dict["Cross Bracing"] = round(max(cb_urs), 3)

    # 4. End Diaphragms
    ed_urs = []
    ed_res = bridge.output_dict.get("end_diaphragm_design_results")
    if isinstance(ed_res, dict):
        for pair_dict in ed_res.values():
            if isinstance(pair_dict, dict):
                for mem_dict in pair_dict.values():
                    if isinstance(mem_dict, dict):
                        for ft_dict in mem_dict.values():
                            if isinstance(ft_dict, dict) and "efficiency" in ft_dict:
                                try:
                                    ed_urs.append(float(ft_dict["efficiency"]))
                                except (ValueError, TypeError):
                                    pass
    
    # Check if end diaphragm configured as cross bracing
    ed_type = ""
    for _k, _v in bridge.input_dict.items():
        if str(_k).startswith(KEY_MP_ED_TYPE) and _v:
            ed_type = str(_v)
            break
    if not ed_urs and "brac" in ed_type.strip().lower() and cb_urs:
        ed_urs = cb_urs

    if ed_urs:
        ur_dict["End Diaphragms"] = round(max(ed_urs), 3)

    return ur_dict

