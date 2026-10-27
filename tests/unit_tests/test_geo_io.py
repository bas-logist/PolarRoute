"""
Unit test for the GPX files PolarRoute writes (`Route.save`) and reads (`gpx_route_import`).
"""

from pathlib import Path

from polar_route.route_planner.route import Route
from polar_route.route_planner.segment import Segment
from polar_route.route_planner.waypoint import Waypoint
from polar_route.utils import gpx_route_import

# (longitude, latitude) in decimal degrees, as in GeoJSON. Not symmetric, so swapped or
# reversed coordinates are caught.
COORDS = [(-60.0, -65.0), (-55.0, -62.0), (-50.0, -60.0)]


def test_route_save_gpx_round_trips(tmp_path: Path) -> None:
    """A GPX file from `Route.save` reads back with the same coordinates and waypoint names."""
    path = tmp_path / "route.gpx"
    waypoints = [Waypoint(lat, lon) for lon, lat in COORDS]
    segments = [Segment(a, b) for a, b in zip(waypoints, waypoints[1:])]
    # A new Segment has an infinite travel time; any finite value will do here.
    for seg in segments:
        seg.set_travel_time(1.0)
    Route(segments, "Bahía Fildes", "Ålesund", {"path_variables": []}).save(str(path))

    feature = gpx_route_import(str(path))["features"][0]

    assert (feature["properties"]["from"], feature["properties"]["to"]) == (
        "Bahía Fildes",
        "Ålesund",
    )
    assert [tuple(c) for c in feature["geometry"]["coordinates"]] == COORDS
