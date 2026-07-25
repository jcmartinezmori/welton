import shutil
import zipfile
from pathlib import Path
import pandas as pd
import time
import plotly.graph_objects as go
import subprocess
import requests
import os
import signal
from src.config import *
from datetime import datetime
from zoneinfo import ZoneInfo


def edit_otp_gtfs(**kwargs):

    tau = kwargs.get('tau', None)
    delta = kwargs.get('delta', None)

    input_gtfs_dir = Path('input/gtfs')
    otp_dir = Path('output/otp')
    output_gtfs_dir = otp_dir / 'gtfs'
    zip_path = otp_dir / 'gtfs.zip'

    otp_dir.mkdir(parents=True, exist_ok=True)

    if output_gtfs_dir.exists():
        shutil.rmtree(output_gtfs_dir)

    shutil.copytree(input_gtfs_dir, output_gtfs_dir)
    if tau is not None and delta is not None:
        shutil.copy(Path(f'output/stop_times/{tau}_{delta}_stop_times.txt'), output_gtfs_dir / 'stop_times.txt')

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in output_gtfs_dir.rglob("*"):
            if file.is_file():
                zf.write(
                    file,
                    arcname=file.relative_to(output_gtfs_dir),
                )


def wait_for_otp(process: subprocess.Popen, timeout: float = 120) -> None:

    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:

        return_code = process.poll()

        if return_code is not None:

            raise RuntimeError(
                f'OTP exited during startup with code {return_code}'
            )

        try:

            response = requests.post(
                OTP_URL,
                json={'query': '{ __typename }'},
                timeout=2,
            )

            if response.ok:
                return

        except requests.RequestException:
            pass

        time.sleep(1)

    raise TimeoutError(
        f'OTP did not become ready within {timeout} seconds'
    )


def stop_otp(process: subprocess.Popen) -> None:

    if process.poll() is not None:
        return

    process_group_id = os.getpgid(process.pid)

    os.killpg(
        process_group_id,
        signal.SIGTERM,
    )

    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(
            process_group_id,
            signal.SIGKILL,
        )
        process.wait()


def get_duration(
        from_coords, to_coords, date, time,
        max_transfers=2, max_walk_distance=1000, num_itineraries=50, timezone="America/Denver"
):

    from_lat, from_lon = from_coords
    to_lat, to_lon = to_coords

    query = """
    query Route(
      $fromPlace: String!
      $toPlace: String!
      $date: String!
      $time: String!
      $maxTransfers: Int!
      $numItineraries: Int!
    ) {
      plan(
        fromPlace: $fromPlace
        toPlace: $toPlace
        date: $date
        time: $time
        transportModes: [
          { mode: WALK }
          { mode: TRANSIT }
        ]
        maxTransfers: $maxTransfers
        numItineraries: $numItineraries
      ) {
        routingErrors {
          code
          description
        }
        itineraries {
          start
          end
          duration
          waitingTime
          walkDistance
          numberOfTransfers
        }
      }
    }
    """

    variables = {
        "fromPlace": f"{from_lat},{from_lon}",
        "toPlace": f"{to_lat},{to_lon}",
        "date": date,
        "time": time,
        "maxTransfers": max_transfers,
        "numItineraries": num_itineraries,
    }

    response = requests.post(
        OTP_URL,
        json={
            "query": query,
            "variables": variables,
        },
        timeout=120,
    )
    response.raise_for_status()

    result = response.json()

    if result.get("errors"):
        raise RuntimeError(f"OTP GraphQL error: {result['errors']}")

    plan = result.get("data", {}).get("plan")

    if not plan:
        return None

    if plan.get("routingErrors"):
        raise RuntimeError(
            f"OTP routing error: {plan['routingErrors']}"
        )

    itineraries = plan.get("itineraries") or []

    valid_itineraries = [
        itinerary
        for itinerary in itineraries
        if itinerary.get("end") is not None
        and itinerary.get("walkDistance") is not None
        and itinerary.get("numberOfTransfers") is not None
        and itinerary["walkDistance"] <= max_walk_distance
        and itinerary["numberOfTransfers"] <= max_transfers
    ]

    if not valid_itineraries:
        return None

    # Pick the itinerary that arrives earliest.
    best_itinerary = min(
        valid_itineraries,
        key=lambda itinerary: datetime.fromisoformat(
            itinerary["end"].replace("Z", "+00:00")
        ),
    )

    query_datetime = datetime.strptime(
        f"{date} {time}",
        "%Y-%m-%d %H:%M:%S",
    ).replace(
        tzinfo=ZoneInfo(timezone)
    )

    arrival_datetime = datetime.fromisoformat(
        best_itinerary["end"].replace("Z", "+00:00")
    )

    return (arrival_datetime - query_datetime).total_seconds() / 60
