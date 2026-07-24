import shutil
import zipfile
from pathlib import Path
import pandas as pd
import time
import plotly.graph_objects as go
import subprocess


def generate_otp_gtfs(**kwargs):

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


def wait_for_otp(
    process: subprocess.Popen,
    timeout: float = 120,
) -> None:
    """Wait until the OTP GraphQL API is ready."""

    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        # Detect OTP crashing during startup.
        return_code = process.poll()

        if return_code is not None:
            raise RuntimeError(
                f"OTP exited during startup with code {return_code}"
            )

        try:
            response = requests.post(
                OTP_URL,
                json={"query": "{ __typename }"},
                timeout=2,
            )

            if response.ok:
                return

        except requests.RequestException:
            pass

        time.sleep(1)

    raise TimeoutError(
        f"OTP did not become ready within {timeout} seconds"
    )


def stop_otp(process: subprocess.Popen) -> None:
    """Stop OTP cleanly, killing it if necessary."""

    if process.poll() is not None:
        return

    process.terminate()

    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()