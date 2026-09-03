r"""Figures for Paper A, the counting-unit methods paper.

Kept in a separate module from the regional paper's figures so the split is mechanical
rather than a matter of memory: everything here belongs to Paper A, everything in
make_figures.py and make_figures_extra.py belongs to Paper B. The two papers do not
share figure files. Outputs land in figures/paper_a/ and Paper A/figures/.
"""
import sys
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import DERIVED, FIG  # noqa: E402
from _countries import COUNTRIES  # noqa: E402
from _style import COL_1, COL_1_5, COL_2  # noqa: E402

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight",
    "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25,
})
OUT = FIG / "paper_a"
OUT.mkdir(parents=True, exist_ok=True)
PAPER_OUT = Path(__file__).resolve().parents[1] / "Paper A" / "figures"
PAPER_OUT.mkdir(parents=True, exist_ok=True)

try:
    from adjustText import adjust_text as _adjust_text
except ImportError:
    _adjust_text = None

EPC_COLOR = "#2a78d6"
NON_EPC_COLOR = "#eb6834"
INK = "#2a2a28"
MUTED = "#9a9a94"


def save(fig, name):
    png = OUT / f"{name}.png"
    pdf = OUT / f"{name}.pdf"
    fig.savefig(png, metadata={"Software": None})
    fig.savefig(pdf, metadata={"CreationDate": None})
    shutil.copy2(png, PAPER_OUT / png.name)
    shutil.copy2(pdf, PAPER_OUT / pdf.name)
    plt.close(fig)
    print(f"saved figures/paper_a/{name}.png|pdf and Paper A/figures/")


def _iso(o):
    return o if o == o else ""


def fig_a0_schematic():
    """Illustrative filing routes and five counting rules. Not an average family."""
    fig, axes = plt.subplots(2, 1, figsize=(COL_2, 6.2),
                             gridspec_kw={"height_ratios": [1.15, 0.95], "hspace": 0.42})
    for ax in axes:
        ax.set_xlim(-0.15, 3.15)
        ax.set_ylim(-1.55, 1.85)
        ax.axis("off")
        ax.grid(False)

    def timeline(ax):
        # Time axis sits above the office boxes so labels cannot collide with the counts.
        ax.plot([0, 2.85], [1.62, 1.62], color=INK, lw=1.1, zorder=1)
        for x, lab in ((0.0, "Priority"), (1.2, "+18 months"), (2.4, "+30 months")):
            ax.plot(x, 1.62, "o", color=INK, ms=4.5, zorder=3)
            ax.text(x, 1.72, lab, ha="center", va="bottom", fontsize=7.5, color=INK)

    def box(ax, x, y, text, color, width=0.72, height=0.36):
        p = FancyBboxPatch((x - width / 2, y - height / 2), width, height,
                           boxstyle="round,pad=0.02,rounding_size=0.04",
                           facecolor=color, edgecolor=INK, linewidth=0.7, zorder=2)
        ax.add_patch(p)
        ax.text(x, y, text, ha="center", va="center", fontsize=7.2, color=INK, zorder=3)

    def counts_row(ax, values, y=-1.12):
        labels = ("office-sum\nincl. **", "office-sum\nexcl. **", "leading\noffice",
                  "all families\n(6a)", "foreign-\noriented (7)")
        xs = np.linspace(0.15, 2.85, 5)
        ax.plot([0.0, 2.85], [y + 0.62, y + 0.62], color="#d0d0cc", lw=0.6, zorder=1)
        for x, lab, val in zip(xs, labels, values):
            ax.text(x, y + 0.38, lab, ha="center", va="bottom", fontsize=6.2, color="#555")
            ax.text(x, y, str(val), ha="center", va="center", fontsize=11,
                    fontweight="bold", color=INK,
                    bbox=dict(boxstyle="round,pad=0.18", facecolor="#f4f4f1",
                              edgecolor="#c8c8c2", linewidth=0.6))

    # Panel A: internationally filed invention
    ax = axes[0]
    ax.set_title("A. International filing route  ·  illustrative, not an average family",
                 loc="left", fontsize=8.5, color=INK, pad=2)
    timeline(ax)
    box(ax, 0.0, 0.72, "Home office", "#d9e8f8")
    box(ax, 1.2, 0.72, "PCT  (**)", "#f7e2c8")
    box(ax, 2.05, 1.18, "Foreign 1", "#e4f0e4")
    box(ax, 2.75, 1.18, "Foreign 2", "#e4f0e4")
    box(ax, 2.05, 0.68, "Foreign 3", "#e4f0e4")
    box(ax, 2.75, 0.68, "EPO\n(regional)", "#e8d9f2")
    ax.annotate("", xy=(1.2, 0.52), xytext=(0.36, 0.52),
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.9))
    ax.annotate("", xy=(2.05, 0.52), xytext=(1.56, 0.52),
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.9))
    counts_row(ax, (6, 5, 1, 1, 1))

    # Panel B: domestic-only invention
    ax = axes[1]
    ax.set_title("B. Domestic-only filing route  ·  illustrative, not an average family",
                 loc="left", fontsize=8.5, color=INK, pad=2)
    timeline(ax)
    box(ax, 0.0, 0.72, "Home office", "#d9e8f8")
    ax.text(1.2, 0.72, "no PCT\npublication", ha="center", va="center",
            fontsize=7, color=MUTED, style="italic")
    ax.text(2.4, 0.72, "no foreign or\nregional publication", ha="center", va="center",
            fontsize=7, color=MUTED, style="italic")
    counts_row(ax, (1, 1, 1, 1, 0))
    save(fig, "figA0_counting_schematic")


def fig_a1(d):
    d_x = d.dropna(subset=["domestic_share"]).copy()
    fig, ax = plt.subplots(figsize=(COL_2, 4.6))
    # Identity curve, clipped to the data y-range so the scatter stays readable.
    xx = np.linspace(max(d_x.domestic_share.min() * 0.6, 0.25), 99.5, 400)
    yy = 100.0 / xx
    ax.plot(xx, yy, color="#52514e", lw=1.05, ls=(0, (4, 2.5)), zorder=1, label="D = 1/H")

    epc = d_x["is_epc"].astype(bool)
    home = d_x["home_is_origin_leader"].astype(bool)
    groups = (
        (epc & home, EPC_COLOR, "o", True, "EPC, home is origin-level leader"),
        (epc & ~home, EPC_COLOR, "^", False, "EPC, home is not the leader"),
        (~epc & home, NON_EPC_COLOR, "o", True, "non-EPC, home is origin-level leader"),
        (~epc & ~home, NON_EPC_COLOR, "^", False, "non-EPC, home is not the leader"),
    )
    for mask, color, marker, filled, _lab in groups:
        sub = d_x.loc[mask]
        if sub.empty:
            continue
        ax.scatter(sub.domestic_share, sub.duplication_factor, s=38,
                   marker=marker,
                   facecolors=color if filled else "none",
                   edgecolors=color, linewidths=0.9, alpha=0.9, zorder=3, label=_lab)

    ax.set_xlim(-2, 102)
    ax.set_ylim(0.85, 5.15)
    ax.set_xlabel("Publications filed at the applicant's own office (%)")
    ax.set_ylabel("Duplication factor (office-sum ÷ cell-wise leading office)")

    texts = []
    offsets = {"CH": (6, 8), "CN": (-28, 8), "SG": (8, -12), "SA": (8, 10)}
    for code in ("CH", "CN", "SG", "SA"):
        if code not in d_x.index:
            continue
        t = ax.annotate(code, (d_x.domestic_share[code], d_x.duplication_factor[code]),
                        xytext=offsets[code], textcoords="offset points", fontsize=8,
                        color=INK, zorder=4)
        texts.append(t)
    if _adjust_text is not None and texts:
        _adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.5))

    # Gap at low H: identity at Singapore vs observed D ceiling.
    d_ceil = float(d.duplication_factor.max())
    sg_id = float(d.loc["SG", "identity"])
    ax.annotate(
        f"1/H = {sg_id:.2f} at SG\nobserved D ceiling {d_ceil:.2f}",
        xy=(float(d.loc["SG", "domestic_share"]), float(d.loc["SG", "duplication_factor"])),
        xytext=(18, 1.15), textcoords="data", fontsize=7.2, color=INK,
        arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.8),
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#d0d0cc", lw=0.5),
        zorder=5,
    )
    # Label the identity curve where it is on-scale.
    ax.text(42, 100 / 42 + 0.18, "D = 1/H", fontsize=7.5, color="#52514e", rotation=-32)

    handles = [
        Line2D([0], [0], color="#52514e", lw=1.05, ls=(0, (4, 2.5)), label="D = 1/H"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=EPC_COLOR,
               markeredgecolor=EPC_COLOR, ms=7, label="EPC, home is origin-level leader"),
        Line2D([0], [0], marker="^", color="none", markerfacecolor="none",
               markeredgecolor=EPC_COLOR, ms=7, label="EPC, home is not the leader"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=NON_EPC_COLOR,
               markeredgecolor=NON_EPC_COLOR, ms=7, label="non-EPC, home is origin-level leader"),
        Line2D([0], [0], marker="^", color="none", markerfacecolor="none",
               markeredgecolor=NON_EPC_COLOR, ms=7, label="non-EPC, home is not the leader"),
    ]
    ax.legend(handles=handles, frameon=False, fontsize=6.6, loc="upper right")
    fig.tight_layout()
    save(fig, "figA1_duplication_vs_domestic")


def fig_a2(d):
    """Family count versus two bulk-file stand-ins. The MARE comparison, not D vs pubs/families."""
    fam = pd.read_csv(DERIVED / "wipo_families_long.csv")
    fam = fam[fam.year.between(2018, 2022)].groupby("origin")["families"].sum()
    both = d.join(fam.rename("families"), how="inner")
    both = both[both.families > 0].copy()

    fig, ax = plt.subplots(figsize=(COL_1_5, 4.2))
    lo = min(both.families.min(), both.lower.min()) * 0.55
    hi = max(both.families.max(), both.upper.max()) * 1.8
    grid = np.array([lo, hi])
    ax.plot(grid, grid, color=MUTED, lw=1.0, ls=(0, (4, 3)), zorder=1, label="1:1")
    for _, r in both.iterrows():
        ax.plot([r.families, r.families], [r.lower, r.upper],
                color=MUTED, lw=0.8, alpha=0.55, zorder=2)
    ax.scatter(both.families, both.lower, s=58, color=EPC_COLOR, marker="o",
               edgecolor=INK, linewidth=0.5, zorder=3, label="Cell-wise leading office")
    ax.scatter(both.families, both.upper, s=58, color=NON_EPC_COLOR, marker="s",
               edgecolor=INK, linewidth=0.5, zorder=3, label="Office-sum")
    for o, r in both.iterrows():
        ax.annotate(COUNTRIES.get(o, o), (r.families, r.lower),
                    xytext=(5, -9), textcoords="offset points", fontsize=6.4, color=INK)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("WIPO patent families (indicator 6a, 2018–2022)")
    ax.set_ylabel("Bulk-file count")
    ax.legend(frameon=False, fontsize=7.4, loc="upper left")
    fig.tight_layout()
    save(fig, "figA2_proxy_validation")


def fig_a3_kept_on_disk():
    # Do not revive in any manuscript list. Left on disk because an earlier draft
    # generated it; regenerating keeps the files from going stale if someone deletes them.
    fig, ax = plt.subplots(figsize=(COL_1_5 * 0.62, 3.3))
    bars = {"Schmoch field 24": 11, "WIPO green\ninventory (GTIS)": 157}
    ax.bar(list(bars), list(bars.values()), color=["#eb6834", "#1baf7a"], width=0.5)
    for i, v in enumerate(bars.values()):
        ax.annotate(str(v), (i, v), xytext=(0, 4), textcoords="offset points",
                    ha="center", fontsize=9)
    ax.set_ylabel("IPC subclasses named")
    fig.tight_layout()
    save(fig, "figA3_green_definitions")


def fig_a4():
    fam_ts = pd.read_csv(DERIVED / "wipo_families_long.csv")
    fam_ts = fam_ts[fam_ts.year.between(2000, 2022)]
    piv_all = fam_ts.pivot_table(index="year", columns="country", values="families")
    piv_fo = fam_ts.pivot_table(index="year", columns="country", values="foreign_oriented")
    ratio_all = (piv_all["China"] / piv_all["Singapore"]).replace([float("inf")], pd.NA)
    ratio_fo = (piv_fo["China"] / piv_fo["Singapore"]).replace([float("inf")], pd.NA)

    fig, ax = plt.subplots(figsize=(COL_1_5, 3.6))
    ax.plot(ratio_all.index, ratio_all, color="#e34948", lw=1.8, label="All families")
    ax.plot(ratio_fo.index, ratio_fo, color="#2a78d6", lw=1.8, ls=(0, (5, 2)),
            label="Foreign-oriented families only")
    ax.set_yscale("log")
    ax.set_ylabel("China / Singapore")
    ax.set_xlabel("Earliest filing year")
    ax.legend(frameon=False, fontsize=8)

    # Annotate the 2019 dip only if it is a local minimum in the plotted series.
    year = 2019
    if (year in ratio_all.index and (year - 1) in ratio_all.index
            and (year + 1) in ratio_all.index
            and ratio_all.loc[year] < ratio_all.loc[year - 1]
            and ratio_all.loc[year] < ratio_all.loc[year + 1]):
        ax.annotate("2019", xy=(year, float(ratio_all.loc[year])),
                    xytext=(year - 4.5, float(ratio_all.loc[year]) * 0.55),
                    fontsize=7.5, color=INK,
                    arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.8))
    fig.tight_layout()
    save(fig, "figA4_china_singapore_ratio")


def fig_a5():
    ranks = pd.read_csv(DERIVED / "counting_ranks_all68.csv", index_col=0)
    top = ranks.sort_values("sum_excl_star", ascending=False).head(25)
    cols = ["rank_sum_incl_star", "rank_sum_excl_star", "rank_cellwise_leading"]
    headers = ("Office-sum\nincluding **", "Office-sum\nexcluding **",
               "Cell-wise\nleading office")
    x = np.array([0.0, 1.0, 2.0])
    delta = top["abs_rank_change_1_to_3"].astype(float)
    dmax = max(float(delta.max()), 1.0)

    fig, ax = plt.subplots(figsize=(COL_2, 7.4))
    ax.grid(False)
    ax.set_xlim(-0.35, 2.35)
    ymin, ymax = 0.5, float(top[cols].max().max()) + 0.6
    ax.set_ylim(ymax, ymin)  # rank 1 at the top
    for xi, lab in zip(x, headers):
        ax.axvline(xi, color="#e6e6e2", lw=0.8, zorder=0)
        ax.text(xi, ymin - 0.15, lab, ha="center", va="bottom", fontsize=7.4, color=INK)

    cmap = plt.colormaps["YlOrRd"]
    for iso, r in top.iterrows():
        ys = [float(r[c]) for c in cols]
        t = float(r["abs_rank_change_1_to_3"]) / dmax
        color = cmap(0.25 + 0.75 * t)
        ax.plot(x, ys, color=color, lw=1.35, solid_capstyle="round", zorder=2)
        ax.scatter(x, ys, s=18, color=color, edgecolor=INK, linewidth=0.35, zorder=3)
        ax.text(x[0] - 0.06, ys[0], iso, ha="right", va="center", fontsize=6.4, color=INK)
        ax.text(x[2] + 0.06, ys[2], iso, ha="left", va="center", fontsize=6.4, color=INK)

    ax.set_xticks(x)
    ax.set_xticklabels([])
    ax.set_ylabel("Rank among 68 economies (1 = largest)")
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, dmax))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.035, pad=0.08)
    cbar.set_label("|rank change| between column 1 and column 3", fontsize=7.5)
    cbar.ax.tick_params(labelsize=7)
    fig.tight_layout()
    save(fig, "figA5_rank_instability")


def main():
    d = pd.read_csv(DERIVED / "counting_generality.csv", index_col=0)
    fig_a0_schematic()
    fig_a1(d)
    fig_a2(d)
    fig_a3_kept_on_disk()
    fig_a4()
    fig_a5()
    return 0


if __name__ == "__main__":
    sys.exit(main())
