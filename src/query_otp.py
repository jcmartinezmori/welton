import requests
from datetime import datetime
from zoneinfo import ZoneInfo


def get_duration(
    from_coords,
    to_coords,
    date,
    time,
    otp_url="http://localhost:8080/otp/gtfs/v1",
    max_transfers=2,
    max_walk_distance=1000,
    num_itineraries=50,
    timezone="America/Denver",
):
    """
    Return elapsed time in seconds from the requested query time
    until arrival.

    Coordinates must be (latitude, longitude).
    """

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
        otp_url,
        json={
            "query": query,
            "variables": variables,
        },
        timeout=30,
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

    return (arrival_datetime - query_datetime).total_seconds()