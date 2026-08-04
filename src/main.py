import itertools as it

import pandas as pd
import time
import plotly.graph_objects as go
import subprocess
from src.helper import *
from src.config import *


def get_durations(origin, destination, query_times, **kwargs):

    kappa = kwargs.get('kappa', None)
    delta = kwargs.get('delta', None)
    date = kwargs.get('date', DATE)

    print(f"    origin: {origin}, destination: {destination}")

    origin_coords = OTP_COORDINATES[origin]
    destination_coords = OTP_COORDINATES[destination]

    durations = []
    for query_time in query_times:

        itinerary = get_itinerary(origin_coords, destination_coords, date, query_time)

        duration = itinerary['duration']

        transit_legs = [leg for leg in itinerary['legs'] if leg['transitLeg']]
        if "1:109L" in [leg["route"]["gtfsId"] for leg in transit_legs]:
            marker = 1
        else:
            marker = 0

        durations.append((kappa, delta, origin, destination, query_time, duration, marker))

        print(f'        query_time: {query_time}, duration: {duration}')

    return durations


if __name__ == '__main__':

    query_times = [
        f'{hour:02d}:{minute:02d}:00'
        for hour in range(15, 18 + 1)
        for minute in range(59 + 1)
    ]

    origin_destination_pairs = [
        ('27th & Welton', 'Union Station'),
        ('Union Station', '27th & Welton'),
        ('27th & Welton', '38th & Blake'),
        ('38th & Blake', '27th & Welton'),
        ('27th & Welton', 'DIA'),
        ('DIA', '27th & Welton'),
        ('20th & Welton', 'DIA'),
        ('DIA', '20th & Welton'),
        ('16th & Stout', 'DIA'),
        ('DIA', '16th & Stout'),
        ('I-25 & Broadway', 'DIA'),
        ('DIA', 'I-25 & Broadway'),
    ]

    kappas = [1, 0.7]
    deltas = [i for i in range(14 + 1)]

    kappa_delta_pairs = [pair for pair in it.product(kappas, deltas)]
    kappa_delta_pairs.append((None, None))

    data = []

    for kappa, delta in kappa_delta_pairs:

        print(f"kappa: {kappa}, delta: {delta}")
        print("     ... Generating OTP")

        edit_otp_gtfs(kappa=kappa, delta=delta)

        log_path = Path(f'output/otp/log/otp_{kappa}_{delta}.log')
        log_path.parent.mkdir(parents=True, exist_ok=True)

        with log_path.open('w') as otp_log:

            otp_process = subprocess.Popen(
                ['bash', str(LAYER_SCRIPT)],
                stdout=otp_log,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )

            try:

                print("     ... Waiting for OTP")
                wait_for_otp(otp_process)

                print("     ... Querying OTP")
                for origin, destination in origin_destination_pairs:

                    durations = get_durations(
                        origin,
                        destination,
                        query_times,
                        kappa=kappa,
                        delta=delta
                    )

                    data.extend(durations)

                    df = pd.DataFrame(
                        data, columns=['kappa', 'delta', 'origin', 'destination', 'query_time', 'duration', 'marker']
                    )
                    df.to_csv(Path('output/durations/durations.csv'), index=False)

            finally:
                print("     ... Stopping OTP")
                stop_otp(otp_process)
