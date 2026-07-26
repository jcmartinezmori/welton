import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path


df = pd.read_csv(Path("output/durations/durations.csv"))

# Current service has missing kappa and delta.
current_df = df[
    df["kappa"].isna()
    & df["delta"].isna()
].copy()

# Only plot the new service results for kappa = 1.
new_df = df[
    (df["kappa"] == 1)
    & df["delta"].notna()
].copy()

# Convert NumPy values to ordinary Python values.
deltas = sorted(new_df["delta"].unique().tolist())

if not deltas:
    raise ValueError("No rows were found for kappa = 1.")

# Treat A -> B and B -> A as the same pair.
new_df["pair"] = new_df.apply(
    lambda row: tuple(
        sorted(
            (
                row["origin"],
                row["destination"],
            )
        )
    ),
    axis=1,
)

pairs = sorted(new_df["pair"].unique().tolist())

subplot_titles = []

for location_1, location_2 in pairs:
    subplot_titles.extend(
        [
            f"{location_1} → {location_2}",
            f"{location_2} → {location_1}",
        ]
    )

fig = make_subplots(
    rows=len(pairs),
    cols=2,
    shared_xaxes=True,
    subplot_titles=subplot_titles,
    horizontal_spacing=0.08,
    vertical_spacing=0.10,
)

# Store the indices of blue traces associated with each delta.
delta_trace_indices = {
    delta: []
    for delta in deltas
}

# Store the indices of all black current-service traces.
current_trace_indices = []

new_legend_added = False
current_legend_added = False


for row, (location_1, location_2) in enumerate(
    pairs,
    start=1,
):
    directions = [
        (location_1, location_2),
        (location_2, location_1),
    ]

    pair_new_df = new_df[
        new_df["pair"] == (location_1, location_2)
    ]

    pair_current_df = current_df[
        (
            (current_df["origin"] == location_1)
            & (current_df["destination"] == location_2)
        )
        | (
            (current_df["origin"] == location_2)
            & (current_df["destination"] == location_1)
        )
    ]

    # Use one fixed y-axis range for both directions in this row.
    row_durations = pd.concat(
        [
            pair_new_df["duration"],
            pair_current_df["duration"],
        ]
    ).dropna()

    if row_durations.empty:
        row_y_range = None
    else:
        y_min = row_durations.min()
        y_max = row_durations.max()
        y_padding = max(
            1,
            0.05 * (y_max - y_min),
        )

        row_y_range = [
            y_min - y_padding,
            y_max + y_padding,
        ]

    for col, (origin, destination) in enumerate(
        directions,
        start=1,
    ):
        direction_df = new_df[
            (new_df["origin"] == origin)
            & (new_df["destination"] == destination)
        ]

        direction_current_df = (
            current_df[
                (current_df["origin"] == origin)
                & (current_df["destination"] == destination)
            ]
            .sort_values("query_time")
        )

        # Add one blue trace for each delta.
        for delta in deltas:
            delta_df = (
                direction_df[
                    direction_df["delta"] == delta
                ]
                .sort_values("query_time")
            )

            if delta_df.empty:
                continue

            trace_index = len(fig.data)
            delta_trace_indices[delta].append(trace_index)

            show_new_legend = bool(
                delta == deltas[0]
                and not new_legend_added
            )

            if show_new_legend:
                new_legend_added = True

            fig.add_trace(
                go.Scatter(
                    x=delta_df["query_time"],
                    y=delta_df["duration"],
                    mode="lines",
                    name="New service",
                    legendgroup="new",
                    showlegend=show_new_legend,
                    visible=bool(delta == deltas[0]),
                    line={
                        "color": "blue",
                        "width": 2.5,
                    },
                    hovertemplate=(
                        f"{origin} → {destination}<br>"
                        f"δ: {delta}<br>"
                        "Query time: %{x}<br>"
                        "Duration: %{y:.1f} minutes"
                        "<extra>New service</extra>"
                    ),
                ),
                row=row,
                col=col,
            )

        # Add the black current-service trace.
        current_trace_index = len(fig.data)
        current_trace_indices.append(current_trace_index)

        fig.add_trace(
            go.Scatter(
                x=direction_current_df["query_time"],
                y=direction_current_df["duration"],
                mode="lines",
                name="Current service",
                legendgroup="current",
                showlegend=bool(not current_legend_added),
                visible=True,
                line={
                    "color": "black",
                    "width": 2.5,
                },
                hovertemplate=(
                    f"{origin} → {destination}<br>"
                    "Query time: %{x}<br>"
                    "Duration: %{y:.1f} minutes"
                    "<extra>Current service</extra>"
                ),
            ),
            row=row,
            col=col,
        )

        current_legend_added = True

        if row_y_range is not None:
            fig.update_yaxes(
                range=row_y_range,
                row=row,
                col=col,
            )


def visibility_for_delta(selected_delta):
    visibility = [False] * len(fig.data)

    # Show all blue traces for the selected delta.
    for trace_index in delta_trace_indices[selected_delta]:
        visibility[trace_index] = True

    # Always show all black current-service traces.
    for trace_index in current_trace_indices:
        visibility[trace_index] = True

    return visibility


slider_steps = [
    {
        "method": "update",
        "label": str(delta),
        "args": [
            {
                "visible": visibility_for_delta(delta),
            },
            {
                "title.text": (
                    "Trip durations for κ = 1"
                    f"<br><sup>Selected δ = {delta}</sup>"
                ),
            },
        ],
    }
    for delta in deltas
]

# Add y-axis titles only to the left column.
for row in range(1, len(pairs) + 1):
    fig.update_yaxes(
        title_text="Duration (minutes)",
        row=row,
        col=1,
    )

# Add x-axis titles only to the bottom row.
for col in range(1, 3):
    fig.update_xaxes(
        title_text="Query time",
        row=len(pairs),
        col=col,
    )

fig.update_layout(
    title={
        "text": (
            "Trip durations for κ = 1"
            f"<br><sup>Selected δ = {deltas[0]}</sup>"
        ),
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    sliders=[
        {
            "active": 0,
            "x": 0.08,
            "y": 1.06,
            "len": 0.84,
            "xanchor": "left",
            "yanchor": "bottom",
            "currentvalue": {
                "prefix": "Selected δ: ",
                "xanchor": "center",
                "font": {
                    "size": 16,
                },
            },
            "pad": {
                "t": 10,
                "b": 10,
            },
            "steps": slider_steps,
        }
    ],
    legend={
        "orientation": "h",
        "x": 0.5,
        "xanchor": "center",
        "y": 1.0,
        "yanchor": "bottom",
    },
    hovermode="x unified",
    height=max(
        600,
        300 * len(pairs),
    ),
    width=1200,
    margin={
        "t": 180,
        "b": 80,
        "l": 100,
        "r": 50,
    },
)

fig.show()