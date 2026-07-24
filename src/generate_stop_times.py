import pandas as pd
from src.config import *


def generate_stop_times(tau, delta, **kwargs):

    route_id = kwargs.get('route_id', ROUTE_ID)
    service_id = kwargs.get('service_id', SERVICE_ID)

    trips_df = pd.read_csv(CWD + '/input/gtfs/trips.txt')
    stop_times_df = pd.read_csv(CWD + '/input/gtfs/stop_times.txt')

    new_stop_times_df = stop_times_df.copy()

    route_trips_df = trips_df[(trips_df['route_id'] == route_id) & (trips_df['service_id'] == service_id)]
    route_stop_times_df = stop_times_df[stop_times_df['trip_id'].isin(route_trips_df['trip_id'])]

    data = []
    for direction_id, direction_route_trips_df in route_trips_df.groupby('direction_id'):
        direction_route_stop_times_df = route_stop_times_df[route_stop_times_df['trip_id'].isin(direction_route_trips_df['trip_id'])]
        for trip_id, trip_direction_route_stop_times_df in direction_route_stop_times_df.groupby('trip_id'):

            if direction_id == 1:  # starts in downing

                row = trip_direction_route_stop_times_df.iloc[0]
                arrival_time = (
                        pd.to_datetime(row['arrival_time'])
                        - pd.Timedelta(minutes=tau)
                        + pd.Timedelta(minutes=delta)
                ).strftime('%H:%M:%S')
                departure_time = arrival_time
                stop_id = STATION_IDS['38th & Blake']
                stop_sequence = 1
                stop_headsign = row['stop_headsign']
                pickup_type = 0
                drop_off_type = 1
                shape_dist_traveled = row['shape_dist_traveled']
                timepoint = 1

                new_stop_times_df.loc[trip_direction_route_stop_times_df.index, 'stop_sequence'] += 1
                new_stop_times_df.loc[row.name, 'pickup_type'] = 0

            else:  # ends in downing

                row = trip_direction_route_stop_times_df.iloc[-1]
                arrival_time = (
                        pd.to_datetime(row['arrival_time'])
                        + pd.Timedelta(minutes=tau)
                        + pd.Timedelta(minutes=delta)
                ).strftime('%H:%M:%S')
                departure_time = arrival_time
                stop_id = STATION_IDS['38th & Blake']
                stop_sequence = row['stop_sequence'] + 1
                stop_headsign = row['stop_headsign']
                pickup_type = 1
                drop_off_type = 0
                shape_dist_traveled = row['shape_dist_traveled']
                timepoint = 1

                new_stop_times_df.loc[row.name, 'pickup_type'] = 0

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
                    timepoint
                )
            )

    data_df = pd.DataFrame(data, columns=new_stop_times_df.columns)
    new_stop_times_df = pd.concat([new_stop_times_df, data_df], ignore_index=True)
    new_stop_times_df = new_stop_times_df.sort_values(by=['trip_id', 'stop_sequence'])
    new_stop_times_df.to_csv(CWD + f'/output/stop_times/{tau}_{delta}_stop_times.txt', index=False)


if __name__ == '__main__':

    taus = [2, 3, 4]
    deltas = [i for i in range(14)]

    for tau in taus:
        for delta in deltas:
            generate_stop_times(tau, delta)
