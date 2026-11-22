"""
OsdagBridge — Centralized Report Styling and Formatting System
==============================================================
Acts as the single source of truth for all LaTeX report styling, document
geometry, color palettes, table layout parameters, header/footer configurations,
and Matplotlib chart styles.
"""

from __future__ import annotations
import os
from typing import Dict, Any, List, Optional
import matplotlib as mpl
import matplotlib.pyplot as plt

# =============================================================================
# 1. COLOR DEFINITIONS (LaTeX & Python / Matplotlib)
# =============================================================================

# Brand and Theme Colors
COLOR_OSDAG_GREEN_HEX = "#91B014"
COLOR_OSDAG_GREEN_DARK_HEX = "#6E870D"
COLOR_PRIMARY_DARK_HEX = "#1A3038"
COLOR_SLATE_HEX = "#2C3E50"
COLOR_LIGHT_BG_HEX = "#F4F6F8"
COLOR_BORDER_HEX = "#CCCCCC"
COLOR_TEXT_MAIN_HEX = "#222222"
COLOR_TEXT_MUTED_HEX = "#555555"

# Status Colors
COLOR_PASS_HEX = "#2E7D32"
COLOR_WARN_HEX = "#E65100"
COLOR_FAIL_HEX = "#C62828"
COLOR_THRESHOLD_HEX = "#D32F2F"

# Material Quantity Chart Colors
COLOR_STEEL_GIRDER_HEX = "#2B5B84"
COLOR_STEEL_BRACING_HEX = "#4A90E2"
COLOR_STEEL_DIAPHRAGM_HEX = "#70A1D7"
COLOR_CONCRETE_HEX = "#5C6B73"
COLOR_REBAR_HEX = "#E07A5F"

# LaTeX Color Declarations
LATEX_COLOR_DECLARATIONS = r"""
\definecolor{osdagGreen}{HTML}{91B014}
\definecolor{osdagGreenDark}{HTML}{6E870D}
\definecolor{osdagSlate}{HTML}{2C3E50}
\definecolor{osdagLightGray}{HTML}{F4F6F8}
\definecolor{osdagBorder}{HTML}{D0D0D0}
\definecolor{osdagPass}{HTML}{2E7D32}
\definecolor{osdagWarn}{HTML}{E65100}
\definecolor{osdagFail}{HTML}{C62828}
\definecolor{osdagHeaderBg}{HTML}{E8EFA8}
"""

# =============================================================================
# 2. DOCUMENT GEOMETRY AND PAGE CONFIGURATION
# =============================================================================

# Standard A4 Page Margins & Header/Footer spacing
# Explicit geometry settings prevent tables and text from overlapping footers
GEOMETRY_CONFIG = {
    "paper": "a4paper",
    "top": "25mm",
    "bottom": "30mm",
    "left": "22mm",
    "right": "22mm",
    "headheight": "18pt",
    "headsep": "12pt",
    "footskip": "16mm",
}

LATEX_GEOMETRY_OPTIONS = (
    f"a4paper, "
    f"top={GEOMETRY_CONFIG['top']}, "
    f"bottom={GEOMETRY_CONFIG['bottom']}, "
    f"left={GEOMETRY_CONFIG['left']}, "
    f"right={GEOMETRY_CONFIG['right']}, "
    f"headheight={GEOMETRY_CONFIG['headheight']}, "
    f"headsep={GEOMETRY_CONFIG['headsep']}, "
    f"footskip={GEOMETRY_CONFIG['footskip']}"
)

# =============================================================================
# 3. TABLE STYLING CONSTANTS
# =============================================================================

TABLE_TABCOLSEP = "5pt"          # Column padding
TABLE_ARRAYSTRETCH = "1.15"       # Row height factor
TABLE_EXTRAROWHEIGHT = "1.2pt"    # Extra cell height
TABLE_ARRAYRULEWIDTH = "0.5pt"    # Border thickness
TABLE_LTPRE = "0pt"               # Longtable pre-skip
TABLE_LTPOST = "6pt"              # Longtable post-skip
NEEDSPACE_LINES = "4"             # Baseline skips required before breaking table

LATEX_TABLE_SETUP = f"""
% Table layout and spacing
\\setlength{{\\tabcolsep}}{{{TABLE_TABCOLSEP}}}
\\renewcommand{{\\arraystretch}}{{{TABLE_ARRAYSTRETCH}}}
\\setlength{{\\extrarowheight}}{{{TABLE_EXTRAROWHEIGHT}}}
\\setlength{{\\arrayrulewidth}}{{{TABLE_ARRAYRULEWIDTH}}}
\\setlength{{\\LTpre}}{{{TABLE_LTPRE}}}
\\setlength{{\\LTpost}}{{{TABLE_LTPOST}}}
\\setlength{{\\LTleft}}{{\\fill}}
\\setlength{{\\LTright}}{{\\fill}}
\\BeforeBeginEnvironment{{table}}{{\\needspace{{{NEEDSPACE_LINES}\\baselineskip}}}}
\\BeforeBeginEnvironment{{longtable}}{{\\needspace{{{NEEDSPACE_LINES}\\baselineskip}}}}
"""

# =============================================================================
# 4. HEADER AND FOOTER STYLING
# =============================================================================

def get_fancyhdr_styles(project_name: str, job_number: str, report_date: str, report_version: str = "Rev 0") -> str:
    """Generate fancyhdr styles with clean footer clearance and proper rules."""
    pn = project_name
    jn = job_number
    rd = report_date
    rv = report_version

    return r"""
\fancypagestyle{main}{
  \fancyhf{}
  \fancyhead[L]{\small\textcolor{osdagSlate}{""" + pn + r""" $|$ """ + jn + r"""}}
  \fancyhead[R]{\small\textcolor{osdagSlate}{""" + rd + r""" $|$ """ + rv + r"""}}
  \fancyfoot[L]{\small\textcolor{osdagSlate}{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}}
  \fancyfoot[R]{\small\textcolor{osdagSlate}{Page \thepage\ of \pageref{LastPage}}}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{2pt}}
  \renewcommand{\footrule}{%
    \ifbool{hasSDonPage}{%
      \vspace{-12pt}%
      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{* Software default value}}\hfil}%
      \vspace{2pt}%
    }{%
      \vspace{-4pt}%
    }%
    \color{osdagGreen}\hrule width\headwidth height 1pt \vspace{4pt}%
  }
}

\fancypagestyle{plain}{
  \fancyhf{}
  \fancyhead[L]{\small\textcolor{osdagSlate}{""" + pn + r""" $|$ """ + jn + r"""}}
  \fancyhead[R]{\small\textcolor{osdagSlate}{""" + rd + r""" $|$ """ + rv + r"""}}
  \fancyfoot[L]{\small\textcolor{osdagSlate}{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}}
  \fancyfoot[R]{\small\textcolor{osdagSlate}{Page \thepage\ of \pageref{LastPage}}}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{2pt}}
  \renewcommand{\footrule}{%
    \ifbool{hasSDonPage}{%
      \vspace{-12pt}%
      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{* Software default value}}\hfil}%
      \vspace{2pt}%
    }{%
      \vspace{-4pt}%
    }%
    \color{osdagGreen}\hrule width\headwidth height 1pt \vspace{4pt}%
  }
}

\fancypagestyle{firstpage}{
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \fancyfoot[L]{\small\textcolor{osdagSlate}{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}}
  \fancyfoot[R]{\small\textcolor{osdagSlate}{Page \thepage\ of \pageref{LastPage}}}
  \renewcommand{\footrule}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{4pt}}
}
"""

# =============================================================================
# 5. REUSABLE LONGTABLE BUILDER HELPERS
# =============================================================================

def build_longtable_header(caption: str, col_count: int, header_rows_tex: str, label: str = "") -> str:
    """
    Construct standardized longtable header with repeat logic for multipage tables.
    Includes:
      - \\endfirsthead for the initial page
      - \\endhead for all continued pages with continuation notice
      - \\endfoot with 'Continued on next page...'
      - \\endlastfoot for final closure
    """
    caption_clean = caption.strip()
    if caption_clean.startswith(r"\textbf{") and caption_clean.endswith("}"):
        caption_clean = caption_clean[8:-1].strip()
    
    label_tex = f"\\label{{{label}}}" if label else ""
    return (
        f"\\caption{{\\textbf{{{caption_clean}}}}}{label_tex}\\\\\n"
        f"\\hline\n"
        f"{header_rows_tex}\n"
        f"\\hline\n"
        f"\\endfirsthead\n\n"
        f"\\multicolumn{{{col_count}}}{{c}}{{\\small\\textit{{\\tablename\\ \\thetable\\ -- Continued from previous page}}}} \\\\\n"
        f"\\hline\n"
        f"{header_rows_tex}\n"
        f"\\hline\n"
        f"\\endhead\n\n"
        f"\\hline\n"
        f"\\multicolumn{{{col_count}}}{{r}}{{\\footnotesize\\textit{{Continued on next page\\ldots}}}} \\\\\n"
        f"\\endfoot\n\n"
        f"\\hline\n"
        f"\\endlastfoot\n"
    )

def status_pass_fail(ur_value: Optional[float], pass_text: str = "PASS", fail_text: str = "FAIL") -> str:
    """Format PASS/FAIL text with consistent status coloring."""
    if ur_value is None:
        return "---"
    if ur_value <= 1.0:
        return r"\textcolor{osdagPass}{\textbf{" + pass_text + r"}}"
    return r"\textcolor{osdagFail}{\textbf{" + fail_text + r"}}"

# =============================================================================
# 6. MATPLOTLIB CHART STYLING SYSTEM
# =============================================================================

def apply_chart_style():
    """Apply centralized styling to Matplotlib globally for reports."""
    plt.style.use("default")
    mpl.rcParams["font.family"] = "sans-serif"
    mpl.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"]
    mpl.rcParams["font.size"] = 10
    mpl.rcParams["axes.titlesize"] = 12
    mpl.rcParams["axes.titleweight"] = "bold"
    mpl.rcParams["axes.labelsize"] = 10
    mpl.rcParams["axes.labelweight"] = "bold"
    mpl.rcParams["xtick.labelsize"] = 9
    mpl.rcParams["ytick.labelsize"] = 9
    mpl.rcParams["legend.fontsize"] = 9
    mpl.rcParams["figure.titlesize"] = 13
    mpl.rcParams["axes.edgecolor"] = "#888888"
    mpl.rcParams["axes.linewidth"] = 0.8
    mpl.rcParams["grid.color"] = "#E0E0E0"
    mpl.rcParams["grid.linestyle"] = "--"
    mpl.rcParams["grid.linewidth"] = 0.6
    mpl.rcParams["grid.alpha"] = 0.7
    mpl.rcParams["figure.dpi"] = 300
    mpl.rcParams["savefig.dpi"] = 300
    mpl.rcParams["savefig.bbox"] = "tight"
    mpl.rcParams["savefig.pad_inches"] = 0.08
