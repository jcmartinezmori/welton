import pandas as pd
import time
import plotly.graph_objects as go
import subprocess
from src.helper import *
from src.config import *
from src.query_otp import *


def get_durations(origin, destination, query_times, **kwargs):

    tau = kwargs.get('tau', None)
    delta = kwargs.get('delta', None)

    origin_coords = QUERY_COORDINATES[origin]
    destination_coords = QUERY_COORDINATES[destination]

    date = kwargs.get('date', DATE)

    durations = []
    for query_time in query_times:
        duration = get_otp_duration(origin_coords, destination_coords, date, query_time) / 60
        durations.append((tau, delta, origin, destination, query_time, duration))

    return durations


if __name__ == '__main__':

    OTP_URL = "http://localhost:8080/otp/gtfs/v1"
    LAYER_SCRIPT = Path("src/layer_gtfs.sh")

    query_times = [
        f'{hour:02d}:{minute:02d}:00'
        for hour in range(15, 15 + 1)
        for minute in range(60)
    ]

    origin_destination_pairs = [
        ('Union Station', '27th & Welton'),
        ('27th & Welton', 'Union Station'),
        ('38th & Blake', '27th & Welton'),
        ('27th & Welton', '38th & Blake'),
        ('DIA', '27th & Welton'),
        ('27th & Welton', 'DIA'),
        ('DIA', '16th & Stout'),
        ('16th & Stout', 'DIA'),
    ]

    taus = [2, 3, 4]
    deltas = [i for i in range(14)]

    data = []

    for tau in taus:
        for delta in deltas:

            print(f"tau: {tau}, delta: {delta}")
            print("     ... Generating OTP")

            generate_otp_gtfs(
                tau=tau,
                delta=delta,
            )

            log_path = Path(
                f"output/otp/otp_{tau}_{delta}.log"
            )
            log_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with log_path.open("w") as otp_log:
                otp_process = subprocess.Popen(
                    ["bash", str(LAYER_SCRIPT)],
                    stdout=otp_log,
                    stderr=subprocess.STDOUT,
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
                        )

                        data.extend(durations)

                        df = pd.DataFrame(
                            data, columns=['tau', 'delta', 'origin', 'destination', 'query_time', 'duration']
                        )
                        df.to_csv(CWD + '/output/durations/durations.csv', index=False)

                finally:
                    print("     ... Stopping OTP")
                    stop_otp(otp_process)
