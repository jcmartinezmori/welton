import pandas as pd
import plotly.graph_objects as go
from pathlib import Path


df = pd.read_csv(Path('output/durations/durations.csv'))

for (origin, destination), origin_destination_df in df.groupby(['origin', 'destination']):

    fig = go.Figure()

    for (tau, delta), group_df in origin_destination_df.groupby(['tau', 'delta']):

        group_df = group_df.sort_values('query_time')

        fig.add_trace(
            go.Scatter(
                x=group_df['query_time'],
                y=group_df['duration'],
                mode="lines",
                name=f"tau={tau}, delta={delta}",
            )
        )

    fig.update_layout(
        title=f'{origin} to {destination}',
        xaxis_title="Query time",
        yaxis_title="Trip duration (minutes)",
    )

    fig.show()

