from pathlib import Path
import numpy as np
import pandas as pd

INPUT_CSV = Path("output/durations/durations.csv")

QUERY_START = "15:00:00"
QUERY_END = "18:00:00"

KAPPAS = [1, 0.7]
DELTAS = [3, 5, 11]

columns = [
    (("27th & Welton", "38th & Blake"), ("38th & Blake", "27th & Welton")),
    (("27th & Welton", "Union Station"), ("Union Station", "27th & Welton")),
    (("27th & Welton", "DIA"), ("DIA", "27th & Welton")),
    (("20th & Welton", "DIA"), ("DIA", "20th & Welton")),
    (("16th & Stout", "DIA"), ("DIA", "16th & Stout")),
]


def latex_escape(s):
    return s.replace("&", r"\&")


def wrap(value, right_bar=False):
    """Center a cell, optionally keeping a vertical rule on its right."""
    spec = "c|" if right_bar else "c"
    return rf"\multicolumn{{1}}{{{spec}}}{{{value}}}"


def load_df():
    df = pd.read_csv(INPUT_CSV)

    df["query_time"] = pd.to_datetime(df["query_time"], format="%H:%M:%S")

    start = pd.Timestamp(QUERY_START).time()
    end = pd.Timestamp(QUERY_END).time()
    df = df[df["query_time"].dt.time.between(start, end)]

    return df


def min_duration(df, origin, destination, kappa=None, delta=None):
    mask = (
        (df["origin"] == origin)
        & (df["destination"] == destination)
    )

    if kappa is None:
        mask &= df["kappa"].isna()
        mask &= df["delta"].isna()
    else:
        mask &= df["kappa"].eq(kappa)
        mask &= df["delta"].eq(delta)

    vals = df.loc[mask, "duration"]

    if vals.empty:
        return np.nan

    return vals.min()


def fmt_current(x):
    if pd.isna(x):
        return ""
    return f"{x:.2f}"


def fmt_new(new, current):
    if pd.isna(new):
        return ""

    pct = (new - current) / current * 100

    return f"{new:.2f} ({pct:+.2f}\\%)"


df = load_df()
df["duration"] = df["duration"].round(2)

print(r"\begin{table}[ht]")
print(r"\centering")
print(r"\resizebox{\linewidth}{!}{%")
print(r"\begin{tabular}{l|lllllll}")

print(
    r"\multicolumn{1}{c|}{\multirow{3}{*}{Origin $\rightarrow$ Destination}} "
    r"& \multicolumn{7}{c}{Minimum Trip Duration {[}min.{]}} \\"
)
print(r"\cline{2-8}")
print(
    r"\multicolumn{1}{c|}{} "
    r"& \multicolumn{1}{c|}{\multirow{2}{*}{\begin{tabular}[c]{@{}c@{}}Current Service\\ (No Track Extension)\end{tabular}}} "
    r"& \multicolumn{3}{c|}{$\kappa = 1$} "
    r"& \multicolumn{3}{c}{$\kappa = 0.7$} \\"
)
print(r"\multicolumn{1}{c|}{} & \multicolumn{1}{c|}{} & \multicolumn{1}{c}{$\delta = 3$} & $\delta = 5$ & \multicolumn{1}{l|}{$\delta = 11$} & \multicolumn{1}{c}{$\delta = 3$} & \multicolumn{1}{c}{$\delta = 5$} & \multicolumn{1}{c}{$\delta = 11$} \\ \hline")

for top, bottom in columns:

    for origin, destination in (top, bottom):

        current = min_duration(df, origin, destination)

        row = [
            rf"{latex_escape(origin)} $\rightarrow$ {latex_escape(destination)}",
            wrap(fmt_current(current), right_bar=True),
        ]

        for kappa in KAPPAS:
            for delta in DELTAS:

                new = min_duration(
                    df,
                    origin,
                    destination,
                    kappa=kappa,
                    delta=delta,
                )

                row.append(
                    wrap(
                        fmt_new(new, current),
                        right_bar=(kappa == 1 and delta == 11),
                    )
                )

        print(" & ".join(row) + r" \\")

    print(r"\hline")

print(r"\end{tabular}%")
print(r"}")
print(r"\caption{}")
print(r"\label{tab:summary}")
print(r"\end{table}")