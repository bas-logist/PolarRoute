"""
Performance benchmark tests for route calculation.

These tests benchmark the wall-clock time of `compute_routes()` and
`compute_smoothed_routes()` against set of existing regression
test fixtures, ranging from small to large meshes.

Run with: `pytest -m benchmark --benchmark-only`
"""

import json

import pytest

from .utils import get_test_data_path, calculate_dijkstra_route, calculate_smoothed_route

DIJKSTRA_BENCHMARK_FILES = {
    "small": "example_routes/dijkstra/time/twin_otter_tt_route_dijkstra.json",
    "medium": "example_routes/dijkstra/fuel/checkerboard.json",
    "large": "example_routes/dijkstra/fuel/gaussian_random_field.json",
}

SMOOTHED_BENCHMARK_FILES = {
    "small": "example_routes/smoothed/time/multi_waypoint_blocked.json",
    "medium": "example_routes/smoothed/fuel/checkerboard.json",
    "large": "example_routes/smoothed/fuel/great_circle_forward.json",
}

BENCHMARK_ROUNDS = {
    "small": 5,
    "medium": 3,
    "large": 1,
}


def _load_route(relative_path):
    with open(get_test_data_path(relative_path), "r") as fp:
        return json.load(fp)


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "size", ["small", "medium", "large"], ids=["small", "medium", "large"]
)
def test_benchmark_dijkstra(benchmark, size):
    """Benchmark `compute_routes()` (Dijkstra) across small/medium/large meshes."""
    route = _load_route(DIJKSTRA_BENCHMARK_FILES[size])
    config = route["config"]["route_info"]

    benchmark.pedantic(
        calculate_dijkstra_route,
        args=(config, route),
        rounds=BENCHMARK_ROUNDS[size],
        iterations=1,
    )


@pytest.mark.benchmark
@pytest.mark.slow
@pytest.mark.parametrize(
    "size", ["small", "medium", "large"], ids=["small", "medium", "large"]
)
def test_benchmark_smoothed(benchmark, size):
    """Benchmark `compute_smoothed_routes()` across small/medium/large meshes."""
    route = _load_route(SMOOTHED_BENCHMARK_FILES[size])
    config = route["config"]["route_info"]

    benchmark.pedantic(
        calculate_smoothed_route,
        args=(config, route),
        rounds=BENCHMARK_ROUNDS[size],
        iterations=1,
    )
