import pandas as pd
import plotly.graph_objects as go
from pathlib import Path


df = pd.read_csv(Path('output/durations/durations.csv'))
df = df.fillna(-1)

for (origin, destination), origin_destination_df in df.groupby(['origin', 'destination']):

    fig = go.Figure()

    for (kappa, delta), delta_df in origin_destination_df.groupby(['kappa', 'delta']):

        delta_df = delta_df.sort_values('query_time')

        fig.add_trace(
            go.Scatter(
                x=delta_df['query_time'],
                y=delta_df['duration'],
                mode="lines",
                name=f"delta: {delta}",
            )
        )

    fig.update_layout(
        title=f'{origin} to {destination}, kappa: {kappa}',
        xaxis_title="Query time",
        yaxis_title="Trip duration (minutes)",
    )

    fig.show()

