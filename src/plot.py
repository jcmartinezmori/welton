import pandas as pd
import plotly.graph_objects as go
from pathlib import Path


df = pd.read_csv(Path('output/durations/durations.csv'))
current_df = df[(df['kappa'].isna()) & (df['delta'].isna())]
df = df.dropna()

for (origin, destination, kappa), group_df in df.groupby(['origin', 'destination', 'kappa']):

    group_current_df = current_df[(current_df['origin'] == origin) & (current_df['destination'] == destination)]
    group_current_df = group_current_df.sort_values('query_time')

    fig = go.Figure()

    deltas = sorted(group_df["delta"].unique())

    for i, delta in enumerate(deltas):

        delta_df = (
            group_df[group_df["delta"] == delta]
            .sort_values("query_time")
        )

        fig.add_trace(
            go.Scatter(
                x=delta_df["query_time"],
                y=delta_df["duration"],
                mode="lines",
                name=f"delta: {delta}",
                visible=(i == 0),
            )
        )

    fig.add_trace(
        go.Scatter(
            x=group_current_df["query_time"],
            y=group_current_df["duration"],
            mode="lines",
        )
    )

    slider_steps = [
        {
            "method": "update",
            "label": str(delta),
            "args": [
                {"visible": [i == j for i in range(len(deltas))]},
                {
                    "title": (
                        f"{origin} to {destination}, "
                        f"kappa: {kappa}, delta: {delta}"
                    )
                },
            ],
        }
        for j, delta in enumerate(deltas)
    ]

    y_min = group_df["duration"].min()
    y_max = group_current_df["duration"].max()

    fig.update_layout(
        title=(
            f"{origin} to {destination}, "
            f"kappa: {kappa}, delta: {deltas[0]}"
        ),
        xaxis_title="Query time",
        yaxis_title="Trip duration (minutes)",
        yaxis_range=[y_min, y_max],
        sliders=[
            {
                "active": 0,
                "currentvalue": {"prefix": "delta: "},
                "steps": slider_steps,
            }
        ],
        showlegend=False,
    )

    fig.show()
