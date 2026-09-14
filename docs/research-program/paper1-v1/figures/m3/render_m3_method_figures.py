"""Render SR2FPGA Paper-1 M3 explanatory figures with editable SVG text."""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


OUT = Path(__file__).resolve().parent
FIGURE_WIDTH_MM = 182
FIGURE_WIDTH_IN = FIGURE_WIDTH_MM / 25.4

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    }
)

COLORS = {
    "ink": "#202A35",
    "muted": "#4E5D6C",
    "line": "#6E7F91",
    "light": "#F8F9FA",
    "neutral": "#EDF0F3",
    "blue": "#1F4E79",
    "blue_light": "#EAF2F8",
    "teal": "#2B6F6D",
    "teal_light": "#EEF7F6",
    "purple": "#5B4B8A",
    "purple_light": "#F3F1F8",
    "orange": "#B85C13",
    "orange_light": "#FAEFE5",
    "red": "#B95858",
    "red_light": "#F7DEDE",
    "green": "#548B63",
    "green_light": "#DDEEDF",
}


def setup(width=FIGURE_WIDTH_IN, height=4.5):
    fig, ax = plt.subplots(figsize=(width, height))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()
    return fig, ax


def box(
    ax,
    x,
    y,
    w,
    h,
    text,
    *,
    fc="white",
    ec=None,
    lw=1.0,
    ls="solid",
    fontsize=8.5,
    weight="normal",
    color=None,
    radius=0.003,
    zorder=2,
):
    ec = ec or COLORS["line"]
    color = color or COLORS["ink"]
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.006,rounding_size={radius}",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
        linestyle=ls,
        zorder=zorder,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight=weight,
        color=color,
        linespacing=1.25,
        zorder=zorder + 1,
    )
    return patch


def arrow(
    ax,
    start,
    end,
    *,
    color=None,
    lw=1.15,
    style="-|>",
    connectionstyle="arc3,rad=0",
    ls="solid",
    zorder=3,
):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle=style,
        mutation_scale=9,
        linewidth=lw,
        color=color or COLORS["ink"],
        connectionstyle=connectionstyle,
        linestyle=ls,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def label(ax, x, y, text, *, size=7, color=None, ha="center", weight="normal"):
    ax.text(
        x,
        y,
        text,
        fontsize=size,
        color=color or COLORS["muted"],
        ha=ha,
        va="center",
        fontweight=weight,
    )


def legend(ax, x=0.67, y=0.03):
    box(ax, x, y, 0.13, 0.055, "development\nimplementation", fc=COLORS["blue_light"], ec=COLORS["blue"], fontsize=7.2)
    box(ax, x + 0.145, y, 0.17, 0.055, "official authority\nincomplete", fc="white", ec=COLORS["orange"], ls="dashed", fontsize=7.2)


def save(fig, stem):
    fig.savefig(OUT / f"{stem}.svg", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.tiff", dpi=600, bbox_inches="tight")
    plt.close(fig)


def figure2_overview():
    fig, ax = setup(FIGURE_WIDTH_IN, 4.3)

    # Independent requirement-boundary lane.
    label(ax, 0.03, 0.94, "Independent RQ0 audit", ha="left", size=8.5, weight="bold", color=COLORS["purple"])
    box(ax, 0.03, 0.81, 0.13, 0.085, "Requirement\nfacts", fc="white", ec=COLORS["purple"], weight="bold")
    arrow(ax, (0.16, 0.852), (0.20, 0.852), color=COLORS["purple"])
    box(ax, 0.20, 0.80, 0.19, 0.105, "Requirement envelope\nand disposition", fc="white", ec=COLORS["purple"], weight="bold")
    arrow(ax, (0.39, 0.852), (0.43, 0.852), color=COLORS["purple"])
    box(ax, 0.43, 0.81, 0.14, 0.085, "needs clarification\nor capability gap", fc="white", ec=COLORS["red"], fontsize=7.8)
    arrow(ax, (0.295, 0.80), (0.295, 0.72), color=COLORS["green"], connectionstyle="arc3,rad=0")
    label(ax, 0.312, 0.758, "ready", size=7.5, color=COLORS["green"], ha="left", weight="bold")

    # Ready-only main lane.
    label(ax, 0.03, 0.68, "Ready-only VPP population", ha="left", size=8.5, weight="bold", color=COLORS["blue"])
    box(ax, 0.03, 0.51, 0.15, 0.12, "Frozen public facts\nproject contract\nplatform profile", fc="white", ec=COLORS["blue"], fontsize=8.0, weight="bold")
    arrow(ax, (0.18, 0.57), (0.22, 0.57), color=COLORS["blue"])
    box(ax, 0.22, 0.49, 0.17, 0.16, "Matched M0-M5\nmethod ladder\nS_D / S_H / S_P", fc=COLORS["blue_light"], ec=COLORS["blue"], fontsize=7.7, weight="bold")
    arrow(ax, (0.39, 0.57), (0.43, 0.57), color=COLORS["blue"])
    box(ax, 0.43, 0.515, 0.15, 0.11, "Candidate project\npackage", fc="white", ec=COLORS["line"], fontsize=8.0, weight="bold")
    arrow(ax, (0.58, 0.57), (0.62, 0.57), color=COLORS["teal"])
    box(ax, 0.62, 0.495, 0.16, 0.15, "Public evaluation\nbounded repair\n(M1 / M5)", fc=COLORS["teal_light"], ec=COLORS["teal"], fontsize=7.7, weight="bold")
    arrow(ax, (0.78, 0.57), (0.82, 0.57), color=COLORS["ink"])
    box(ax, 0.82, 0.515, 0.15, 0.11, "Terminal select\nand seal", fc="white", ec=COLORS["ink"], fontsize=8.0, weight="bold")

    # Hidden lane and evidence.
    arrow(ax, (0.895, 0.515), (0.895, 0.40), color=COLORS["purple"])
    box(ax, 0.79, 0.27, 0.18, 0.12, "One-shot hidden final\nprivate store", fc=COLORS["purple_light"], ec=COLORS["purple"], fontsize=8.0, weight="bold")
    label(ax, 0.885, 0.235, "opaque ref / sanitized status only", size=7.0, color=COLORS["purple"])

    box(ax, 0.03, 0.27, 0.17, 0.12, "Public L0-L3\nand bounded RQ4 L4", fc=COLORS["teal_light"], ec=COLORS["teal"], fontsize=7.7, weight="bold")
    arrow(ax, (0.20, 0.33), (0.24, 0.33), color=COLORS["ink"])
    box(ax, 0.24, 0.25, 0.47, 0.16, "Immutable evidence plane\nartifacts and provenance\nfailure/missingness - three cost views - reducers", fc="white", ec=COLORS["line"], fontsize=7.7, weight="bold")
    arrow(ax, (0.79, 0.33), (0.71, 0.33), color=COLORS["purple"])
    arrow(ax, (0.70, 0.495), (0.61, 0.41), color=COLORS["teal"], connectionstyle="arc3,rad=0.08")

    # Explicit no-return boundary.
    label(ax, 0.765, 0.44, "no hidden feedback", size=7.0, color=COLORS["red"], weight="bold")

    box(ax, 0.03, 0.08, 0.94, 0.085, "Official execution locked: G3 acceptance and G4b authorization incomplete", fc="white", ec=COLORS["orange"], ls="dashed", fontsize=8.0, weight="bold", color=COLORS["orange"])
    legend(ax, 0.65, 0.84)
    save(fig, "figure2_sr2fpga_overview")


def method_card(ax, y, method, label_text, fill, edge):
    box(ax, 0.38, y, 0.28, 0.078, f"{method}  {label_text}", fc=fill, ec=edge, fontsize=8.0, weight="bold")


def figure3_matched_design():
    fig, ax = setup(FIGURE_WIDTH_IN, 4.55)

    label(ax, 0.055, 0.94, "Shared block preparation", ha="left", size=8.5, weight="bold", color=COLORS["blue"])
    box(ax, 0.04, 0.68, 0.20, 0.10, "S_D\nDirect initial project", fc=COLORS["blue_light"], ec=COLORS["blue"], weight="bold")
    box(ax, 0.04, 0.50, 0.20, 0.10, "S_H\nFrozen generated HIS", fc=COLORS["purple_light"], ec=COLORS["purple"], fontsize=7.2, weight="bold")
    box(ax, 0.04, 0.32, 0.20, 0.10, "S_P\nSkeleton-derived project", fc=COLORS["teal_light"], ec=COLORS["teal"], fontsize=7.1, weight="bold")
    arrow(ax, (0.14, 0.50), (0.14, 0.42), color=COLORS["teal"])

    label(ax, 0.38, 0.94, "Method condition", ha="left", size=8.5, weight="bold")
    ys = [0.77, 0.68, 0.56, 0.47, 0.35, 0.26]
    method_card(ax, ys[0], "M0", "Direct", COLORS["neutral"], COLORS["line"])
    method_card(ax, ys[1], "M1", "Direct + public repair", COLORS["teal_light"], COLORS["teal"])
    method_card(ax, ys[2], "M2", "untyped -> free project", COLORS["neutral"], COLORS["line"])
    method_card(ax, ys[3], "M3", "HIS -> free project", COLORS["purple_light"], COLORS["purple"])
    method_card(ax, ys[4], "M4", "HIS -> skeleton -> behavior", COLORS["blue_light"], COLORS["blue"])
    method_card(ax, ys[5], "M5", "M4 + public repair", COLORS["teal_light"], COLORS["teal"])

    # Shared artifact arrows.
    arrow(ax, (0.24, 0.73), (0.38, ys[0] + 0.036), color=COLORS["blue"])
    arrow(ax, (0.24, 0.73), (0.38, ys[1] + 0.036), color=COLORS["blue"], connectionstyle="arc3,rad=-0.15")
    arrow(ax, (0.24, 0.55), (0.38, ys[3] + 0.036), color=COLORS["purple"])
    arrow(ax, (0.24, 0.55), (0.38, ys[4] + 0.036), color=COLORS["purple"], connectionstyle="arc3,rad=0.10")
    arrow(ax, (0.24, 0.55), (0.38, ys[5] + 0.036), color=COLORS["purple"], connectionstyle="arc3,rad=0.17")
    arrow(ax, (0.24, 0.37), (0.38, ys[4] + 0.036), color=COLORS["teal"])
    arrow(ax, (0.24, 0.37), (0.38, ys[5] + 0.036), color=COLORS["teal"], connectionstyle="arc3,rad=0.12")

    # Contrast cards.
    label(ax, 0.72, 0.94, "Frozen inferential role", ha="left", size=8.5, weight="bold")
    box(ax, 0.72, 0.68, 0.24, 0.12, "RQ1 primary Holm family\nM4 - M3\nM4 - M0", fc=COLORS["blue_light"], ec=COLORS["blue"], fontsize=7.3, weight="bold")
    box(ax, 0.72, 0.51, 0.24, 0.105, "Mandatory secondary\nM3 - M2", fc=COLORS["neutral"], ec=COLORS["line"], fontsize=7.3, weight="bold")
    box(ax, 0.72, 0.31, 0.24, 0.135, "RQ2 Holm family\nM5 - M4\nR_HIS - R_generic", fc=COLORS["teal_light"], ec=COLORS["teal"], fontsize=8.0, weight="bold")

    # The primary card names both contrasts directly; extra crossing arrows are omitted.
    arrow(ax, (0.66, ys[2] + 0.036), (0.72, 0.56), color=COLORS["line"])
    arrow(ax, (0.66, ys[5] + 0.036), (0.72, 0.38), color=COLORS["teal"])

    box(ax, 0.04, 0.10, 0.92, 0.085, "Cost views: actual campaign | standalone end-to-end | post-checkpoint incremental", fc="white", ec=COLORS["line"], fontsize=8.0, weight="bold")
    label(ax, 0.50, 0.05, "Claim activation additionally requires v1.7 Holm, interval, minimum-effect and validity gates.", size=7.5, color=COLORS["muted"])
    save(fig, "figure3_matched_treatment_design")


def figure4_authority():
    fig, ax = setup(FIGURE_WIDTH_IN, 4.4)

    # Zones.
    ax.add_patch(Rectangle((0.025, 0.17), 0.30, 0.79, facecolor="#FAFBFC", edgecolor=COLORS["blue"], linewidth=1.2))
    ax.add_patch(Rectangle((0.35, 0.17), 0.30, 0.79, facecolor="#FAFCFC", edgecolor=COLORS["teal"], linewidth=1.2))
    ax.add_patch(Rectangle((0.675, 0.17), 0.30, 0.79, facecolor="#FCFBFD", edgecolor=COLORS["purple"], linewidth=1.2))
    label(ax, 0.175, 0.91, "Candidate / method side", size=8.5, weight="bold", color=COLORS["blue"])
    label(ax, 0.50, 0.91, "Public evaluator authority", size=8.5, weight="bold", color=COLORS["teal"])
    label(ax, 0.825, 0.91, "Hidden evaluator authority", size=8.5, weight="bold", color=COLORS["purple"])

    box(ax, 0.055, 0.66, 0.24, 0.085, "Generated attempt\nproject package", fc=COLORS["blue_light"], ec=COLORS["blue"], weight="bold")
    box(ax, 0.055, 0.49, 0.24, 0.095, "Bounded repair\nM1 / M5 only", fc=COLORS["teal_light"], ec=COLORS["teal"], weight="bold")
    box(ax, 0.055, 0.30, 0.24, 0.105, "Declared terminal\nselection and seal", fc=COLORS["neutral"], ec=COLORS["ink"], weight="bold")

    box(ax, 0.38, 0.66, 0.24, 0.085, "Sealed public-evaluation\ncandidate", fc=COLORS["teal_light"], ec=COLORS["teal"], weight="bold")
    box(ax, 0.38, 0.49, 0.24, 0.095, "Authoritative public outcome\nand sanitized diagnosis", fc=COLORS["teal_light"], ec=COLORS["teal"], fontsize=7.0, weight="bold")
    box(ax, 0.38, 0.30, 0.24, 0.105, "Exact terminal public rerun\ncontent/hash bound", fc=COLORS["neutral"], ec=COLORS["ink"], fontsize=7.0, weight="bold")

    box(ax, 0.705, 0.66, 0.24, 0.085, "Private commitment\nand hidden cases", fc=COLORS["purple_light"], ec=COLORS["purple"], weight="bold")
    box(ax, 0.705, 0.49, 0.24, 0.095, "Consume-once hidden\nexecution", fc=COLORS["purple_light"], ec=COLORS["purple"], weight="bold")
    box(ax, 0.705, 0.30, 0.24, 0.105, "Private raw record\nopaque outcome ref", fc=COLORS["purple_light"], ec=COLORS["purple"], weight="bold")

    # Flow arrows.
    arrow(ax, (0.295, 0.702), (0.38, 0.702), color=COLORS["teal"])
    arrow(ax, (0.50, 0.66), (0.50, 0.585), color=COLORS["teal"])
    arrow(ax, (0.38, 0.537), (0.295, 0.537), color=COLORS["teal"])
    label(ax, 0.338, 0.555, "public only", size=6.1, color=COLORS["teal"])
    arrow(ax, (0.175, 0.49), (0.175, 0.405), color=COLORS["ink"])
    arrow(ax, (0.295, 0.352), (0.38, 0.352), color=COLORS["ink"])
    arrow(ax, (0.62, 0.352), (0.705, 0.537), color=COLORS["purple"], connectionstyle="arc3,rad=-0.15")
    arrow(ax, (0.825, 0.66), (0.825, 0.585), color=COLORS["purple"])
    arrow(ax, (0.825, 0.49), (0.825, 0.405), color=COLORS["purple"])

    # One-way boundary and reducers.
    arrow(ax, (0.705, 0.352), (0.64, 0.23), color=COLORS["purple"], connectionstyle="arc3,rad=0.12")
    box(ax, 0.37, 0.19, 0.26, 0.07, "Reducer-only sanitized\npass / fail / not_run", fc=COLORS["light"], ec=COLORS["line"], fontsize=6.9, weight="bold")
    arrow(ax, (0.37, 0.225), (0.30, 0.225), color=COLORS["line"])
    box(ax, 0.055, 0.19, 0.24, 0.07, "Episode outcome + cost +\nfailure/missingness ledger", fc=COLORS["light"], ec=COLORS["line"], fontsize=6.7, weight="bold")

    # Red no-return marker.
    arrow(ax, (0.70, 0.44), (0.63, 0.44), color=COLORS["red"], style="-[", ls="dashed")
    label(ax, 0.665, 0.465, "no hidden feedback", size=7.2, color=COLORS["red"], weight="bold")

    box(ax, 0.36, 0.045, 0.60, 0.075, "Official hidden/VPP producer and G4b gate remain incomplete", fc="white", ec=COLORS["orange"], ls="dashed", fontsize=7.7, weight="bold", color=COLORS["orange"])
    label(ax, 0.17, 0.082, "solid: development implementation", size=7.2, ha="center")
    save(fig, "figure4_evaluator_authority")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    figure2_overview()
    figure3_matched_design()
    figure4_authority()


if __name__ == "__main__":
    main()
