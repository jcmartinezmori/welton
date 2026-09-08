from pathlib import Path
import numpy as np
import pandas as pd


# =====================================================================
# Configuration
# =====================================================================

GTFS_DIRS = [
    "gtfs_2025-08-31_2026-01-03",
    "gtfs_2026-01-04_2026-06-06",
]

QUERY_START = "15:00:00"
QUERY_END = "18:00:00"

KAPPAS = [1, 0.7]

# One delta for each GTFS period
DELTAS = {
    "gtfs_2025-08-31_2026-01-03": 8,
    "gtfs_2026-01-04_2026-06-06": 11,
}

columns = [
    (
        ("27th & Welton", "38th & Blake"),
        ("38th & Blake", "27th & Welton"),
    ),
    (
        ("27th & Welton", "I-25 & Broadway"),
        ("I-25 & Broadway", "27th & Welton"),
    ),
    (
        ("27th & Welton", "Union Station"),
        ("Union Station", "27th & Welton"),
    ),
    (
        ("27th & Welton", "DIA"),
        ("DIA", "27th & Welton"),
    )
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

def load_df(gtfs_dir):

    input_csv = (
        Path("output")
        / "durations"
        / gtfs_dir
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
    """Calculate minimum or maximum trip duration."""

    mask = (
        (df["origin"] == origin)
        & (df["destination"] == destination)
    )

    # Current service
    if kappa is None:
        mask &= df["kappa"].isna()
        mask &= df["delta"].isna()

    # New service
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

def generate_table(gtfs_dir):

    df = load_df(gtfs_dir)

    if gtfs_dir not in DELTAS:
        raise ValueError(
            f"No delta specified for GTFS directory: {gtfs_dir}"
        )

    delta = DELTAS[gtfs_dir]

    lines = []

    # =================================================================
    # Table beginning
    # =================================================================

    lines.append(r"\begin{table}[ht]")
    lines.append(r"\centering")
    lines.append(r"\resizebox{\linewidth}{!}{%")

    # Route | Current Min Max | kappa=1 Min Max | kappa=0.7 Min Max
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
        rf"\multicolumn{{2}}{{c|}}{{$\kappa = 1$, "
        rf"$\delta = {delta}$}} "
        r"& "
        rf"\multicolumn{{2}}{{c}}{{$\kappa = 0.7$, "
        rf"$\delta = {delta}$}} \\"
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

            # Current minimum
            row.append(
                cell(
                    format_current(current_min)
                )
            )

            # Current maximum
            row.append(
                cell(
                    format_current(current_max),
                    right_bar=True,
                )
            )

            # ---------------------------------------------------------
            # New service
            # ---------------------------------------------------------

            for kappa in KAPPAS:

                new_min = get_duration(
                    df,
                    origin,
                    destination,
                    aggregation="min",
                    kappa=kappa,
                    delta=delta,
                )

                new_max = get_duration(
                    df,
                    origin,
                    destination,
                    aggregation="max",
                    kappa=kappa,
                    delta=delta,
                )

                # New minimum
                row.append(
                    cell(
                        format_new(
                            new_min,
                            current_min,
                        )
                    )
                )

                # New maximum
                row.append(
                    cell(
                        format_new(
                            new_max,
                            current_max,
                        ),
                        right_bar=(kappa == 1),
                    )
                )

            lines.append(
                " & ".join(row) + r" \\"
            )

        # Separator between route pairs
        lines.append(r"\hline")

    # =================================================================
    # Table ending
    # =================================================================

    lines.append(r"\end{tabular}%")
    lines.append(r"}")

    lines.append(
        r"\caption{"
        rf"Minimum and maximum trip durations for "
        rf"$\delta = {delta}$. "
        r"Percent differences relative to the corresponding "
        r"current-service statistic are reported in parenthesis."
        r"}"
    )

    safe_gtfs = (
        gtfs_dir
        .replace("-", "_")
        .replace(".", "_")
    )

    lines.append(
        rf"\label{{tab:minmax_{safe_gtfs}}}"
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

    for gtfs_dir in GTFS_DIRS:

        latex = generate_table(gtfs_dir)

        output_file = (
            OUTPUT_DIR
            / f"trip_duration_minmax_{gtfs_dir}.tex"
        )

        output_file.write_text(
            latex + "\n",
            encoding="utf-8",
        )

        print()
        print("=" * 70)
        print(f"GTFS: {gtfs_dir}")
        print(f"Delta: {DELTAS[gtfs_dir]}")
        print(f"Output: {output_file}")
        print("=" * 70)
        print()

        print(latex)
        print()