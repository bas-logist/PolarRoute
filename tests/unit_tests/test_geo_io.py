"""
Unit tests for the GPX files PolarRoute writes (`Route.save`, `write_route_gpx`) and
reads (`gpx_route_import`).
"""

from pathlib import Path

import pytest

from polar_route.route_planner.route import Route
from polar_route.route_planner.segment import Segment
from polar_route.route_planner.waypoint import Waypoint
from polar_route.utils import gpx_route_import

# (longitude, latitude) in decimal degrees, as in GeoJSON. Not symmetric, so swapped or
# reversed coordinates are caught.
COORDS = [(-60.0, -65.0), (-55.0, -62.0), (-50.0, -60.0)]

# GDAL, which reads the GPX files, keeps coordinates to at least 15 significant digits.
GPX_REL_TOL = 1e-12

# A GPX route in the form other tools write it, with a name on every route point.
NAMED_GPX = """<?xml version="1.0"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
<rte>
  <name>test_route</name>
  <rtept lat="-65.0" lon="-60.0"><name>Start</name></rtept>
  <rtept lat="-62.0" lon="-55.0"><name>Middle</name></rtept>
  <rtept lat="-60.0" lon="-50.0"><name>End</name></rtept>
</rte>
</gpx>
"""


def flatten(coords: list[tuple[float, float]] | list[list[float]]) -> list[float]:
    """Flatten coordinate pairs to one list of numbers, which `pytest.approx` can compare."""
    return [x for c in coords for x in c]


def save_route_gpx(path: Path) -> None:
    """Save a `Route` through `COORDS` to `path` as GPX, from waypoint "Bahía Fildes" to "Ålesund"."""
    waypoints = [Waypoint(lat, lon) for lon, lat in COORDS]
    segments = [Segment(a, b) for a, b in zip(waypoints, waypoints[1:])]
    # A new Segment has an infinite travel time; any finite value will do here.
    for seg in segments:
        seg.set_travel_time(1.0)
    route = Route(segments, "Bahía Fildes", "Ålesund", {"path_variables": []})
    route.save(str(path))


def test_route_save_gpx_round_trips(tmp_path: Path) -> None:
    """A GPX file from `Route.save` reads back with the same coordinates and waypoint names."""
    path = tmp_path / "route.gpx"

    save_route_gpx(path)

    feature = gpx_route_import(str(path))["features"][0]
    assert (feature["properties"]["from"], feature["properties"]["to"]) == (
        "Bahía Fildes",
        "Ålesund",
    )
    assert flatten(feature["geometry"]["coordinates"]) == pytest.approx(
        flatten(COORDS), rel=GPX_REL_TOL
    )


def test_gpx_route_import_named_waypoints(tmp_path: Path) -> None:
    """The first and last named route points become the route's from/to properties."""
    path = tmp_path / "named.gpx"
    path.write_text(NAMED_GPX)

    feature = gpx_route_import(str(path))["features"][0]

    assert feature["properties"]["from"] == "Start"
    assert feature["properties"]["to"] == "End"
    assert flatten(feature["geometry"]["coordinates"]) == pytest.approx(
        flatten(COORDS), rel=GPX_REL_TOL
    )
