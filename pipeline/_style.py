"""Figure palette and line styles, shared so that checking them cannot run a build.

Colour alone cannot identify fourteen series. The bundled data-visualization guidance
puts the ceiling at eight hues on adjacent pairs and three on all-pairs, and a line
chart whose series cross is an all-pairs problem. So identity here is carried by three
channels at once -- hue, dash pattern, and a direct label at the end of each line --
and `pipeline/check_palette.py` measures what the hue channel contributes rather than
assuming it.

Hues are the validated categorical slots from that guidance, assigned in fixed order.
Assignment follows the entity, never its rank, so filtering the country set never
repaints the survivors.
"""

# Validated categorical slots, light surface, in fixed order.
SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
         "#e87ba4", "#008300", "#4a3aa7", "#e34948"]

# The three benchmarks are visually separated from ASEAN by dash pattern as well as hue,
# so they take the three slots that validate on all pairs.
# BENCH + SEA_MAIN are the nine series that share a line chart, so they need nine
# distinct hues. That is eight validated slots plus one deliberate neutral: Japan, the
# incumbent whose line is flat and high, is the series that reads correctly as recessive
# ink rather than a competing colour.
COLORS = {
    "Japan": "#52514e",          # neutral ink (not a categorical slot, by design)
    "China": "#e34948",          # slot 8 red
    "Korea, Rep.": "#4a3aa7",    # slot 7 violet
    "Singapore": "#2a78d6",      # slot 1 blue
    "Malaysia": "#eb6834",       # slot 2 orange
    "Thailand": "#1baf7a",       # slot 3 aqua
    "Philippines": "#eda100",    # slot 4 yellow
    "Indonesia": "#e87ba4",      # slot 5 magenta
    "Viet Nam": "#008300",       # slot 6 green
    # The five smallest economies never share a colour-identified line chart with the
    # nine above -- they appear in the technology heatmap, where rows are labelled, and
    # in Table 3. Hues here are for completeness, and check_palette.py validates the
    # nine that actually co-occur.
    "Cambodia": "#a04000",
    "Lao PDR": "#7f8c8d",
    "Myanmar": "#af7ac5",
    "Brunei Darussalam": "#45b39d",
    "Timor-Leste": "#909497",
}

# The nine that share a chart, and are therefore the set that must validate together.
PRIMARY = ["China", "Korea, Rep.", "Japan", "Singapore", "Malaysia", "Thailand",
           "Viet Nam", "Philippines", "Indonesia"]

# Second identity channel, and it has to distinguish the benchmarks from each other, not
# only from ASEAN. Korea (violet) and Japan (neutral ink) sit at greyscale distance 1.8 --
# indistinguishable on a mono page, which is how World Patent Information prints by
# default -- so a shared dash pattern left them with no separating channel at all.
DASH = {
    "China": (6, 2),          # long dash
    "Korea, Rep.": (2, 1.6),  # fine dot
    "Japan": (7, 2, 1.5, 2),  # dash-dot
}


def style(country: str) -> dict:
    """Line style for a series: dashed benchmarks, solid ASEAN, distinct within each."""
    d = DASH.get(country)
    return {"color": COLORS.get(country, "#52514e"),
            "linestyle": (0, d) if d else "-",
            "linewidth": 2.2 if d else 1.6}

SHORT = {"Korea, Rep.": "South Korea", "Viet Nam": "Vietnam",
         "Brunei Darussalam": "Brunei", "Lao PDR": "Laos"}

# Elsevier artwork: single column 90 mm, 1.5 column 140 mm, double column 190 mm.
# Figures are sized in inches against those widths and saved at 300 dpi.
MM = 1 / 25.4
COL_1, COL_1_5, COL_2 = 90 * MM, 140 * MM, 190 * MM


def label(country: str) -> str:
    return SHORT.get(country, country)


# --- small-N suppression (plan task 1.4) -------------------------------------------
# A share computed on a handful of publications is noise presented as a measurement.
# Brunei's 2018-2022 green share rests on 32 publications and Cambodia's on 29; a zero
# on either is consistent with anything up to about 11 percent. Below this threshold a
# share is suppressed rather than printed, everywhere it would otherwise appear.
MIN_PUBS = 100
SUPPRESSED = "n<100"
