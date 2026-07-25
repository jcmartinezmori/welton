from pathlib import Path

# ---------- GTFS ---------- #
ROUTE_ID = '109L'
SERVICE_ID = 'FR'
STATION_IDS = {
    '16th & Stout': 35266,
    '38th & Blake': 35320,
    '30th & Downing': 23051

}
TAU = 4

# ---------- OTP ---------- #
DATE = '2026-03-27'
OTP_COORDINATES = {
    '16th & Stout': (39.746080362466564, -104.99292078083685),
    'Union Station': (39.752972760202766, -104.99992340468313),
    '27th & Welton': (39.75522805291108, -104.97725395645433),
    '38th & Blake': (39.7708433185342, -104.97337379540957),
    'DIA': (39.84732834809734, -104.6738677718117)
}
OTP_URL = "http://localhost:8080/otp/gtfs/v1"
LAYER_SCRIPT = Path('src/layer_otp.sh')
MAX_TRANSFERS = 2
NUM_ITINERARIES = 1000
SEARCH_WINDOW = 60 * 60
TIME_ZONE = 'America/Denver'
