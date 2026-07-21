import pandas as pd

service_id = 'FR'
route = '109L'
stout_id = 35266  # '16th & Stout Station'
downing_id = 23051  # '30th & Downing Station'
blake_id = 35320  # '38th / Blake Station'

trips_df = pd.read_csv('./input/trips.txt')
stops_df = pd.read_csv('./input/stops.txt')
stop_times_df = pd.read_csv('./input/stop_times.txt')

new_stop_times_df = stop_times_df.copy()

route_trips_df = trips_df[(trips_df['route_id'] == route) & (trips_df['service_id'] == service_id)]
route_stop_times_df = stop_times_df[stop_times_df['trip_id'].isin(route_trips_df['trip_id'])]

downing_stout_time = 2
time_shift = -4

# downing_arvs = []
# downing_dpts = []
# stout_arvs = []
# stout_dpts = []


data = []
for direction_id, direction_route_trips_df in route_trips_df.groupby('direction_id'):
    direction_route_stop_times_df = route_stop_times_df[route_stop_times_df['trip_id'].isin(direction_route_trips_df['trip_id'])]
    for trip_id, trip_direction_route_stop_times_df in direction_route_stop_times_df.groupby('trip_id'):

        if direction_id == 1:  # starts in downing

            row = trip_direction_route_stop_times_df.iloc[0]
            arrival_time = (
                    pd.to_datetime(row['arrival_time'])
                    - pd.Timedelta(minutes=downing_stout_time)
                    + pd.Timedelta(minutes=time_shift)
            ).strftime('%H:%M:%S')
            departure_time = arrival_time
            stop_id = blake_id
            stop_sequence = 1
            stop_headsign = row['stop_headsign']
            pickup_type = 0
            drop_off_type = 1
            shape_dist_traveled = row['shape_dist_traveled']
            timepoint = 1

            new_stop_times_df.loc[trip_direction_route_stop_times_df.index, 'stop_sequence'] += 1
            new_stop_times_df.loc[row.name, 'pickup_type'] = 0

            # downing_arvs.append(arrival_time)
            # downing_dpts.append(departure_time)

        else:  # ends in downing

            row = trip_direction_route_stop_times_df.iloc[-1]
            arrival_time = (
                    pd.to_datetime(row['arrival_time'])
                    + pd.Timedelta(minutes=downing_stout_time)
                    + pd.Timedelta(minutes=time_shift)
            ).strftime('%H:%M:%S')
            departure_time = arrival_time
            stop_id = blake_id
            stop_sequence = row['stop_sequence'] + 1
            stop_headsign = row['stop_headsign']
            pickup_type = 1
            drop_off_type = 0
            shape_dist_traveled = row['shape_dist_traveled']
            timepoint = 1

            new_stop_times_df.loc[row.name, 'pickup_type'] = 0

            # stout_arvs.append(arrival_time)
            # stout_dpts.append(departure_time)

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

        arrival_time = pd.to_datetime(
            new_stop_times_df.loc[trip_direction_route_stop_times_df.index, 'arrival_time'],
            format="%H:%M:%S",
            errors="coerce"
        )
        departure_time = pd.to_datetime(
            new_stop_times_df.loc[trip_direction_route_stop_times_df.index, 'departure_time'],
            format="%H:%M:%S",
            errors="coerce"
        )

        new_stop_times_df.loc[trip_direction_route_stop_times_df.index, 'arrival_time'] = (
                arrival_time + pd.Timedelta(minutes=time_shift)
        ).dt.strftime("%H:%M:%S")
        new_stop_times_df.loc[trip_direction_route_stop_times_df.index, 'departure_time'] = (
                departure_time + pd.Timedelta(minutes=time_shift)
        ).dt.strftime("%H:%M:%S")


new_stop_times_df = new_stop_times_df.sort_values(by=['trip_id', 'stop_sequence'])
new_stop_times_df.to_csv('./output/original/stop_times.txt', index=False)

data_df = pd.DataFrame(data, columns=new_stop_times_df.columns)
new_stop_times_df = pd.concat([new_stop_times_df, data_df], ignore_index=True)
new_stop_times_df = new_stop_times_df.sort_values(by=['trip_id', 'stop_sequence'])
new_stop_times_df.to_csv('./output/counterfactual/stop_times.txt', index=False)
