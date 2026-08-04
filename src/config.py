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
KAPPA = 1
DELTA = 0

# ---------- OTP ---------- #
DATE = '2026-03-27'
OTP_COORDINATES = {
    '16th & Stout': (39.74607840576559, -104.99292108362069),
    'Union Station': (39.75369692944971, -105.00089845324099),
    '27th & Welton': (39.75524464534553, -104.9772704985722),
    '38th & Blake': (39.77082631327184, -104.97345638692283),
    'DIA': (39.84732834809734, -104.6738677718117),
    'I-25 & Broadway': (39.701573482994874, -104.9899987909828),
    '20th & Welton': (39.7480579332452, -104.98675830009564)
}
OTP_URL = "http://localhost:8080/otp/gtfs/v1"
LAYER_SCRIPT = Path('src/layer_otp.sh')
MAX_TRANSFERS = 2
NUM_ITINERARIES = 1000
SEARCH_WINDOW = 60 * 60
TIME_ZONE = 'America/Denver'
