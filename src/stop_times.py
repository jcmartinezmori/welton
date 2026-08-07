import itertools as it
import pandas as pd
from pathlib import Path
from src.config import *


def build_new_stop_times(**kwargs):

    gtfs_dir = kwargs.get('gtfs_dir', GTFS_DIR)

    kappa = kwargs.get('kappa', KAPPA)
    delta = kwargs.get('delta', DELTA)

    tau = kwargs.get('tau', TAU)
    route_id = kwargs.get('route_id', ROUTE_ID)

    trips_df = pd.read_csv(Path(f'input/{gtfs_dir}/trips.txt'))
    stop_times_df = pd.read_csv(Path(f'input/{gtfs_dir}/stop_times.txt'))

    new_stop_times_df = stop_times_df.copy()

    route_trips_df = trips_df[trips_df['route_id'] == route_id]
    route_stop_times_df = stop_times_df[stop_times_df['trip_id'].isin(route_trips_df['trip_id'])]

    data = []

    for direction_id, direction_route_trips_df in route_trips_df.groupby('direction_id'):

        direction_route_stop_times_df = route_stop_times_df[
            route_stop_times_df['trip_id'].isin(direction_route_trips_df['trip_id'])
        ]

        for trip_id, trip_direction_route_stop_times_df in direction_route_stop_times_df.groupby('trip_id'):

            trip_direction_route_stop_times_df = trip_direction_route_stop_times_df.sort_values('stop_sequence')

            trip_indices = trip_direction_route_stop_times_df.index

            arrival_times = pd.to_timedelta(new_stop_times_df.loc[trip_indices, 'arrival_time'])
            departure_times = pd.to_timedelta(new_stop_times_df.loc[trip_indices, 'departure_time'])

            anchor_time = min(arrival_times.iloc[0], departure_times.iloc[0])

            arrival_times = (anchor_time + (arrival_times - anchor_time) * kappa).dt.round('s')
            departure_times = (anchor_time + (departure_times - anchor_time) * kappa).dt.round('s')

            delta_time = pd.Timedelta(minutes=delta)
            tau_time = pd.Timedelta(minutes=tau) * kappa

            if direction_id == 1:  # starts in Downing

                row = trip_direction_route_stop_times_df.iloc[0]

                added_stop_time = anchor_time + delta_time

                arrival_time = format_gtfs_time(added_stop_time)
                departure_time = arrival_time

                stop_id = STATION_IDS["38th & Blake"]
                stop_sequence = 1
                stop_headsign = row["stop_headsign"]
                pickup_type = 0
                drop_off_type = 1
                shape_dist_traveled = row["shape_dist_traveled"]
                timepoint = 1

                new_stop_times_df.loc[row.name, "drop_off_type"] = 0
                new_stop_times_df.loc[trip_indices, "stop_sequence"] += 1

                new_stop_times_df.loc[trip_indices, "arrival_time"] = (
                    format_gtfs_times(
                        arrival_times + delta_time + tau_time
                    )
                )
                new_stop_times_df.loc[trip_indices, "departure_time"] = (
                    format_gtfs_times(
                        departure_times + delta_time + tau_time
                    )
                )

            else:  # ends in Downing

                row = trip_direction_route_stop_times_df.iloc[-1]

                added_stop_time = departure_times.iloc[-1] + delta_time + tau_time

                arrival_time = format_gtfs_time(added_stop_time)
                departure_time = arrival_time

                stop_id = STATION_IDS["38th & Blake"]
                stop_sequence = row["stop_sequence"] + 1
                stop_headsign = row["stop_headsign"]
                pickup_type = 1
                drop_off_type = 0
                shape_dist_traveled = row["shape_dist_traveled"]
                timepoint = 1

                new_stop_times_df.loc[row.name, "pickup_type"] = 0

                new_stop_times_df.loc[trip_indices, "arrival_time"] = (
                    format_gtfs_times(arrival_times + delta_time)
                )

                new_stop_times_df.loc[trip_indices, "departure_time"] = (
                    format_gtfs_times(departure_times + delta_time)
                )

            data.append(
                (
                    trip_id,
                    arrival_time,
                    departure_time,
                    stop_id,
                    stop_sequence,
                    stop_headsign,
                    pickup_type,
                    drop_off_type,
                    shape_dist_traveled,
                    timepoint,
                )
            )

    data_df = pd.DataFrame(data, columns=new_stop_times_df.columns)
    new_stop_times_df = pd.concat([new_stop_times_df, data_df], ignore_index=True)
    new_stop_times_df = new_stop_times_df.sort_values(by=['trip_id', 'stop_sequence'])

    output_dir = Path(f'output/stop_times/{gtfs_dir}')
    output_dir.mkdir(parents=True, exist_ok=True)
    new_stop_times_df.to_csv(output_dir / f'{kappa}_{delta}_stop_times.txt', index=False)


def format_gtfs_time(time):

    total_seconds = int(round(time.total_seconds()))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f'{hours:02d}:{minutes:02d}:{seconds:02d}'


def format_gtfs_times(times):
    return times.map(format_gtfs_time)


if __name__ == '__main__':

    kappas = [1, 0.7]
    deltas = [i for i in range(14 + 1)]

    kappa_delta_pairs = [pair for pair in it.product(kappas, deltas)]
    for kappa, delta in kappa_delta_pairs:
        build_new_stop_times(kappa=kappa, delta=delta)
