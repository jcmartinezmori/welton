from pathlib import Path
import copy
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.config import *


def plot_trip_durations(columns, **kwargs):

    gtfs_dir = kwargs.get('gtfs_dir', GTFS_DIR)
    fig_name = kwargs.get('fig_name', 'fig')

    kappa = kwargs.get('kappa', KAPPA)
    query_start = kwargs.get('query_start', None)
    query_end = kwargs.get('query_end', None)

    y_max = kwargs.get('y_max', 120)

    df = pd.read_csv(Path(f'output/durations/{gtfs_dir}/durations.csv'))

    df['query_time'] = pd.to_datetime(df['query_time'], format='%H:%M:%S')
    if query_start is not None and query_end is not None:
        df = df[df['query_time'].dt.time.between(pd.Timestamp(query_start).time(), pd.Timestamp(query_end).time())]

    cur = df[df['kappa'].isna() & df['delta'].isna()]
    new = df[df['kappa'].eq(kappa)]
    deltas = sorted(new['delta'].unique())

    tops = [top for top, _ in columns]
    bottoms = [bottom for _, bottom in columns]

    fig = make_subplots(
        rows=2,
        cols=len(columns),
        shared_xaxes=True,
        shared_yaxes=True,
        subplot_titles=[
            f'{a} → {b}' for a, b in tops
        ] + [
            f'{a} → {b}' for a, b in bottoms
        ],
        horizontal_spacing=0.02,
        vertical_spacing=0.075,
    )

    delta_traces = {delta: [] for delta in deltas}
    cur_traces = []
    legend_trace_indices = []

    for col, (top, bottom) in enumerate(columns, start=1):

        for row, (origin, destination) in enumerate((top, bottom), start=1):

            new_df = new[(new.origin == origin) & (new.destination == destination)]
            cur_df = cur[(cur.origin == origin) & (cur.destination == destination)].sort_values('query_time')

            for delta in deltas:

                d = new_df[new_df.delta == delta].sort_values('query_time')

                delta_traces[delta].append(len(fig.data))
                fig.add_trace(
                    go.Scatter(
                        x=d['query_time'],
                        y=d['duration'],
                        mode='lines',
                        name='New Service',
                        legendgroup='new',
                        showlegend=False,
                        visible=(delta == deltas[0]),
                        line={'color': 'blue', 'width': 2.5},
                        hovertemplate=(
                            f'{origin} → {destination}<br>'
                            'Trip Duration: %{y:.1f} [min.], '
                            f'δ: {delta} [min.]'
                        ),
                    ),
                    row=row,
                    col=col,
                )

            cur_traces.append(len(fig.data))
            fig.add_trace(
                go.Scatter(
                    x=cur_df['query_time'],
                    y=cur_df['duration'],
                    mode='lines',
                    name="Current Service",
                    legendgroup='current',
                    showlegend=False,
                    line={'color': 'black', 'width': 1.5},
                    hovertemplate=(
                        f'{origin} → {destination}<br>'
                        'Trip Duration: %{y:.1f} [min.]'
                    ),
                ),
                row=row,
                col=col,
            )

    legend_trace_indices.append(len(fig.data))
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode='lines',
            name='New Service',
            line={'color': "blue", 'width': 2.5},
            showlegend=True,
            hoverinfo='skip',
            visible=True
        )
    )

    legend_trace_indices.append(len(fig.data))
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode='lines',
            name='Current Service',
            line={'color': 'black', 'width': 2.5},
            showlegend=True,
            hoverinfo='skip',
            visible=True
        )
    )

    def visible(delta):
        v = [False] * len(fig.data)
        for i in legend_trace_indices:
            v[i] = True
        for i in delta_traces[delta]:
            v[i] = True
        for i in cur_traces:
            v[i] = True
        return v

    for ann in fig.layout.annotations:
        ann.font.size = 18

    fig.update_yaxes(range=[0, y_max])
    fig.update_yaxes(
        title_text="Trip Duration [min.]",
        title_font=dict(size=18),
        tickfont=dict(size=16),
        row=1, col=1
    )
    fig.update_yaxes(
        title_text="Trip Duration [min.]",
        title_font=dict(size=18),
        tickfont=dict(size=16),
        row=2, col=1
    )
    for col in range(1, len(columns) + 1):
        fig.update_xaxes(
            title_text='Query Time',
            title_font=dict(size=18),
            tickfont=dict(size=16),
            row=2, col=col
        )
    fig.update_xaxes(
        tickformat='%H:%M',
        tickangle=45,
        unifiedhovertitle=dict(
            text='Query Time: %{x|%H:%M}'
        )
    )

    fig.update_layout(
        title={
            'text': f'Trip Durations (κ: {kappa})',
            'x': 0.125,
            'xanchor': 'center',
            'y': 0.98,
            'font': {'size': 26}
        },
        margin={
            'l': 80,
            'r': 80,
            't': 180,
            'b': 80
        },
        sliders=[
            {
                'active': 0,
                'x': 0.5,
                'y': 1.1,
                'len': 0.8,
                'xanchor': 'center',
                'yanchor': 'bottom',
                'currentvalue': {
                    'prefix': 'δ: ',
                    'suffix': ' [min.]',
                    'xanchor': 'center',
                    'font': {'size': 20},
                },
                'pad': {'t': 0, 'b': 0},
                'steps': [
                    {
                        'method': 'update',
                        'label': str(delta),
                        'args': [
                            {'visible': visible(delta)},
                        ],
                    }
                    for delta in deltas
                ],
            }
        ],
        legend={
            'orientation': 'h',
            'x': 0,
            'xanchor': 'left',
            'y': 1.2,
            'yanchor': 'bottom',
            'traceorder': 'normal'
        },
        hovermode="x unified",
        height=800,
        width=1600,
    )

    output_dir = Path(f'output/figures/{gtfs_dir}/{fig_name}')
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.write_html(
        output_dir / f'trip_durations_kappa_{kappa}.html',
        include_plotlyjs="cdn",
    )
    for i, delta in enumerate(deltas):
        export_fig = copy.deepcopy(fig)
        vis = visible(delta)
        for trace, is_visible in zip(export_fig.data, vis):
            trace.visible = is_visible

        export_fig.update_layout(
            sliders=[
                {
                    **export_fig.layout.sliders[0].to_plotly_json(),
                    "active": i,
                }
            ]
        )
        export_fig.write_image(
            output_dir / f'trip_durations_kappa_{kappa}_delta_{delta}.pdf'
        )

    return fig


if __name__ == "__main__":

    gtfs_dirs = ['gtfs_2025-08-31_2026-01-03', 'gtfs_2026-01-04_2026-06-06']
    for gtfs_dir in gtfs_dirs:

        fig_name = 'welton'
        columns = [
            (("27th & Welton", "38th & Blake"), ("38th & Blake", "27th & Welton")),
            (("27th & Welton", "I-25 & Broadway"), ("I-25 & Broadway", "27th & Welton")),
            (("27th & Welton", "Union Station"), ("Union Station", "27th & Welton")),
            (("27th & Welton", "DIA"), ("DIA", "27th & Welton"))
        ]

        plot_trip_durations(
            columns,
            fig_name=fig_name,
            gtfs_dir=gtfs_dir,
            kappa=0.7,
            query_start='15:00:00',
            query_end='18:00:00',
            y_max=77.5
        )
        plot_trip_durations(
            columns,
            fig_name=fig_name,
            gtfs_dir=gtfs_dir,
            kappa=1,
            query_start='15:00:00',
            query_end='18:00:00',
            y_max=77.5
        )

        fig_name = 'dia'
        columns = [
            (("20th & Welton", "DIA"), ("DIA", "20th & Welton")),
            (("16th & Stout", "DIA"), ("DIA", "16th & Stout")),
            (("10th & Osage", "DIA"), ("DIA", "10th & Osage")),
            (("I-25 & Broadway", "DIA"), ("DIA", "I-25 & Broadway")),
        ]

        plot_trip_durations(
            columns,
            fig_name=fig_name,
            gtfs_dir=gtfs_dir,
            kappa=0.7,
            query_start='15:00:00',
            query_end='18:00:00',
            y_max=90
        )
        plot_trip_durations(
            columns,
            fig_name=fig_name,
            gtfs_dir=gtfs_dir,
            kappa=1,
            query_start='15:00:00',
            query_end='18:00:00',
            y_max=120
        )
