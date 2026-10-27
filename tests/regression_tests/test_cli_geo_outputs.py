"""
End-to-end tests of the CLI entry points that read or write KML/GPX files.
"""

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
import pytest

from polar_route.cli import (
    calculate_route_cli,
    extract_routes_cli,
    optimise_routes_cli,
)

EXAMPLE_ROUTE = (
    Path(__file__).parent
    / "example_routes"
    / "smoothed"
    / "time"
    / "twin_otter_tt_route.json"
)

# A KML file written from a GeoDataFrame with no CRS makes GeoPandas emit this warning.
pytestmark = pytest.mark.filterwarnings("error:'crs' was not provided:UserWarning")

# GDAL writes KML coordinates with 15 significant digits, and calculate_route sums costs
# in a different order from the optimiser; both differ by at most ~1e-14 on this route.
GEO_FILE_REL_TOL = 1e-12

# Paths of the (config, mesh, waypoints) files the CLI entry points take.
CliInputs = tuple[Path, Path, Path]


def run_cli(
    monkeypatch: pytest.MonkeyPatch, entry_point: Callable[[], None], *args: object
) -> None:
    """Call a CLI entry point as if run from the shell with `args` as its arguments."""
    monkeypatch.setattr(sys, "argv", [entry_point.__name__, *map(str, args)])
    entry_point()


@pytest.fixture
def cli_inputs(tmp_path: Path) -> CliInputs:
    """Writes the config, mesh and waypoints files the CLI expects."""
    with open(EXAMPLE_ROUTE) as fp:
        example = json.load(fp)

    config = tmp_path / "config.json"
    config.write_text(json.dumps(example["config"]["route_info"]))

    mesh_json = {k: v for k, v in example.items() if k != "paths"}
    mesh = tmp_path / "mesh.json"
    mesh.write_text(json.dumps(mesh_json))

    waypoints = tmp_path / "waypoints.csv"
    pd.DataFrame(example["waypoints"]).to_csv(waypoints, index=False)

    return config, mesh, waypoints


@pytest.fixture
def optimised_routes(
    cli_inputs: CliInputs, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Output of optimise_routes, with KML and GPX route files requested."""
    config, mesh, waypoints = cli_inputs
    output = tmp_path / "optimised" / "out.route.json"
    output.parent.mkdir()
    run_cli(
        monkeypatch,
        optimise_routes_cli,
        config,
        mesh,
        waypoints,
        "-o",
        output,
        "--path_kml",
        "--path_gpx",
    )
    return output


def optimised_paths(optimised_routes: Path) -> list[dict[str, Any]]:
    """Return the route features stored under `paths` in an `optimise_routes` output file."""
    with open(optimised_routes) as fp:
        paths: list[dict[str, Any]] = json.load(fp)["paths"]["features"]
    return paths


def assert_matches_route(gdf: gpd.GeoDataFrame, route: dict[str, Any]) -> None:
    """Assert the first geometry in `gdf` has the same coordinates as the route feature."""
    expected = [x for c in route["geometry"]["coordinates"] for x in c]
    actual = [x for c in gdf.geometry.iloc[0].coords for x in c]
    assert actual == pytest.approx(expected, rel=GEO_FILE_REL_TOL)


def test_optimise_routes_writes_kml_and_gpx(
    cli_inputs: CliInputs,
    optimised_routes: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`optimise_routes` writes KML and GPX files holding the route, and `calculate_route`
    costs the GPX file, with its waypoint names, the same as the optimiser did."""
    out_dir = optimised_routes.parent
    gpx_route = out_dir / "out.route_SourceDestination.gpx"
    [route] = optimised_paths(optimised_routes)

    assert_matches_route(
        gpd.read_file(out_dir / "out.route_SourceDestination.kml"), route
    )
    assert_matches_route(gpd.read_file(gpx_route, layer="routes"), route)

    _, mesh, _ = cli_inputs
    output = tmp_path / "calculated.json"
    run_cli(monkeypatch, calculate_route_cli, mesh, gpx_route, "-o", output)
    with open(output) as fp:
        calculated = json.load(fp)["features"][0]["properties"]
    for key in ("from", "to"):
        assert calculated[key] == route["properties"][key]
    for key in ("traveltime", "fuel", "distance"):
        assert calculated[key] == pytest.approx(
            route["properties"][key], rel=GEO_FILE_REL_TOL
        ), key


# One case per output writer and per input branch of `extract_routes_cli`.
@pytest.mark.parametrize(
    ("extension", "source"), [("kml", "mesh_output"), ("gpx", "route_collection")]
)
def test_extract_routes_writes_kml_and_gpx(
    optimised_routes: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    extension: str,
    source: str,
) -> None:
    """`extract_routes` writes KML or GPX from a full mesh output or a bare route file."""
    [route] = optimised_paths(optimised_routes)
    route_input = optimised_routes
    if source == "route_collection":
        route_input = tmp_path / "routes.json"
        route_input.write_text(
            json.dumps({"type": "FeatureCollection", "features": [route]})
        )
    output = tmp_path / "extracted" / f"route.{extension}"
    output.parent.mkdir()

    run_cli(monkeypatch, extract_routes_cli, route_input, "-o", output)

    extracted = output.parent / f"route_SourceDestination.{extension}"
    layer = "routes" if extension == "gpx" else None
    assert_matches_route(gpd.read_file(extracted, layer=layer), route)
