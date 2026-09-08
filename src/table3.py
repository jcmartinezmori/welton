from pathlib import Path
import numpy as np
import pandas as pd


# =====================================================================
# Configuration
# =====================================================================

GTFS_DIR = "gtfs_2025-08-31_2026-01-03"

QUERY_START = "15:00:00"
QUERY_END = "18:00:00"

KAPPA = 0.7
DELTAS = [8, 2]

columns = [
    (
        ("20th & Welton", "DIA"),
        ("DIA", "20th & Welton"),
    ),
    (
        ("16th & Stout", "DIA"),
        ("DIA", "16th & Stout"),
    ),
    (
        ("10th & Osage", "DIA"),
        ("DIA", "10th & Osage"),
    ),
    (
        ("I-25 & Broadway", "DIA"),
        ("DIA", "I-25 & Broadway"),
    ),
]

OUTPUT_DIR = Path("output/tables")


# =====================================================================
# LaTeX helpers
# =====================================================================

def latex_escape(text):
    """Escape characters with special meaning in LaTeX."""

    text = str(text)

    replacements = {
        "&": r"\&",
        "%": r"\%",
        "#": r"\#",
        "_": r"\_",
        "$": r"\$",
        "{": r"\{",
        "}": r"\}",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def cell(value, right_bar=False):
    """Create a centered LaTeX table cell."""

    if right_bar:
        return rf"\multicolumn{{1}}{{c|}}{{{value}}}"

    return rf"\multicolumn{{1}}{{c}}{{{value}}}"


# =====================================================================
# Load data
# =====================================================================

def load_df():

    input_csv = (
        Path("output")
        / "durations"
        / GTFS_DIR
        / "durations.csv"
    )

    if not input_csv.exists():
        raise FileNotFoundError(
            f"Could not find durations file:\n{input_csv}"
        )

    df = pd.read_csv(input_csv)

    df["query_time"] = pd.to_datetime(
        df["query_time"],
        format="%H:%M:%S",
    )

    start = pd.Timestamp(QUERY_START).time()
    end = pd.Timestamp(QUERY_END).time()

    df = df[
        df["query_time"].dt.time.between(start, end)
    ].copy()

    return df


# =====================================================================
# Calculate duration
# =====================================================================

def get_duration(
    df,
    origin,
    destination,
    aggregation,
    kappa=None,
    delta=None,
):
    """
    Calculate minimum or maximum trip duration.

    Current service:
        kappa=None
        delta=None

    New service:
        kappa and delta are specified.
    """

    mask = (
        (df["origin"] == origin)
        & (df["destination"] == destination)
    )

    # -------------------------------------------------------------
    # Current service
    # -------------------------------------------------------------

    if kappa is None:
        mask &= df["kappa"].isna()
        mask &= df["delta"].isna()

    # -------------------------------------------------------------
    # New service
    # -------------------------------------------------------------

    else:
        mask &= df["kappa"].eq(kappa)
        mask &= df["delta"].eq(delta)

    values = df.loc[mask, "duration"]

    if values.empty:
        return np.nan

    if aggregation == "min":
        return values.min()

    if aggregation == "max":
        return values.max()

    raise ValueError(
        f"Unknown aggregation: {aggregation}"
    )


# =====================================================================
# Formatting
# =====================================================================

def format_current(value):
    """Format a current-service duration."""

    if pd.isna(value):
        return ""

    return f"{value:.2f}"


def format_new(value, current):
    """
    Format a new-service duration and percentage difference
    relative to the corresponding current-service statistic.
    """

    if pd.isna(value):
        return ""

    if pd.isna(current) or current == 0:
        return f"{value:.2f}"

    percent = (value - current) / current * 100

    return f"{value:.2f} ({percent:+.2f}\\%)"


# =====================================================================
# Generate table
# =====================================================================

def generate_table():

    df = load_df()

    lines = []

    # =================================================================
    # Table beginning
    # =================================================================

    lines.append(r"\begin{table}[ht]")
    lines.append(r"\centering")
    lines.append(r"\resizebox{\linewidth}{!}{%")

    # 7 columns:
    #
    # Route
    # Current Min
    # Current Max
    # delta=8 Min
    # delta=8 Max
    # delta=2 Min
    # delta=2 Max
    #
    lines.append(r"\begin{tabular}{l|cc|cc|cc}")

    # =================================================================
    # Header row 1
    # =================================================================

    lines.append(
        r"\multicolumn{1}{c|}{"
        r"\multirow{3}{*}{Origin $\rightarrow$ Destination}"
        r"} "
        r"& "
        r"\multicolumn{6}{c}{Trip Durations [min.]} \\"
    )

    lines.append(r"\cline{2-7}")

    # =================================================================
    # Header row 2
    # =================================================================

    lines.append(
        r"\multicolumn{1}{c|}{} "
        r"& "
        r"\multicolumn{2}{c|}{Current Service} "
        r"& "
        rf"\multicolumn{{2}}{{c|}}{{$\kappa = 0.7$, "
        rf"$\delta = {DELTAS[0]}$}} "
        r"& "
        rf"\multicolumn{{2}}{{c}}{{$\kappa = 0.7$, "
        rf"$\delta = {DELTAS[1]}$}} \\"
    )

    lines.append(r"\cline{2-7}")

    # =================================================================
    # Header row 3
    # =================================================================

    lines.append(
        r"\multicolumn{1}{c|}{} "
        r"& "
        r"\multicolumn{1}{c}{Minimum} "
        r"& "
        r"\multicolumn{1}{c|}{Maximum} "
        r"& "
        r"\multicolumn{1}{c}{Minimum} "
        r"& "
        r"\multicolumn{1}{c|}{Maximum} "
        r"& "
        r"\multicolumn{1}{c}{Minimum} "
        r"& "
        r"\multicolumn{1}{c}{Maximum} \\"
    )

    lines.append(r"\hline")

    # =================================================================
    # Table body
    # =================================================================

    for top, bottom in columns:

        for origin, destination in (top, bottom):

            # ---------------------------------------------------------
            # Current service
            # ---------------------------------------------------------

            current_min = get_duration(
                df,
                origin,
                destination,
                aggregation="min",
            )

            current_max = get_duration(
                df,
                origin,
                destination,
                aggregation="max",
            )

            row = [
                (
                    rf"{latex_escape(origin)} "
                    rf"$\rightarrow$ "
                    rf"{latex_escape(destination)}"
                )
            ]

            # ---------------------------------------------------------
            # Current minimum
            # ---------------------------------------------------------

            row.append(
                cell(
                    format_current(current_min)
                )
            )

            # ---------------------------------------------------------
            # Current maximum
            # ---------------------------------------------------------

            row.append(
                cell(
                    format_current(current_max),
                    right_bar=True,
                )
            )

            # ---------------------------------------------------------
            # New-service scenarios
            # ---------------------------------------------------------

            for delta in DELTAS:

                new_min = get_duration(
                    df,
                    origin,
                    destination,
                    aggregation="min",
                    kappa=KAPPA,
                    delta=delta,
                )

                new_max = get_duration(
                    df,
                    origin,
                    destination,
                    aggregation="max",
                    kappa=KAPPA,
                    delta=delta,
                )

                # Minimum
                row.append(
                    cell(
                        format_new(
                            new_min,
                            current_min,
                        )
                    )
                )

                # Maximum
                row.append(
                    cell(
                        format_new(
                            new_max,
                            current_max,
                        ),
                        right_bar=(delta == DELTAS[0]),
                    )
                )

            lines.append(
                " & ".join(row) + r" \\"
            )

        # Horizontal separator after each route pair
        lines.append(r"\hline")

    # =================================================================
    # Table ending
    # =================================================================

    lines.append(r"\end{tabular}%")
    lines.append(r"}")

    lines.append(
        r"\caption{"
        r"Minimum and maximum trip durations for "
        rf"$\kappa = 0.7$ and $\delta = {DELTAS[0]}$ or "
        rf"$\delta = {DELTAS[1]}$. "
        r"Percent differences relative to the corresponding "
        r"current-service statistic are reported in parenthesis."
        r"}"
    )

    lines.append(
        r"\label{tab:dia_kappa07_delta8_delta2}"
    )

    lines.append(r"\end{table}")

    return "\n".join(lines)


# =====================================================================
# Main
# =====================================================================

if __name__ == "__main__":

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    latex = generate_table()

    output_file = (
        OUTPUT_DIR
        / "trip_duration_dia_kappa07_delta8_delta2.tex"
    )

    output_file.write_text(
        latex + "\n",
        encoding="utf-8",
    )

    print()
    print("=" * 70)
    print(f"GTFS: {GTFS_DIR}")
    print(f"Kappa: {KAPPA}")
    print(f"Deltas: {DELTAS}")
    print(f"Query window: {QUERY_START} - {QUERY_END}")
    print(f"Output: {output_file}")
    print("=" * 70)
    print()

    print(latex)
    print()