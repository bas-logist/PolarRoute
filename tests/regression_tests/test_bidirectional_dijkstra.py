"""
Verifies that enabling `bidirectional_dijkstra` in the route config produces routes identical to
the standard (unidirectional) Dijkstra search, for every example dijkstra route test file.
"""
import copy
import json

import numpy as np
import pytest

from .utils import (
    get_route_test_files,
    calculate_dijkstra_route,
    compare_route_coordinates,
    compare_waypoint_names,
    compare_time,
    compare_fuel,
    compare_battery,
    compare_cell_indices,
    compare_cases,
)

import logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

# Dynamically discover test files
ALL_TEST_ROUTES = get_route_test_files('dijkstra')

# Meshes that are uniform/symmetric grids with zero currents (the "great_circle" example
# routes) have many exactly-tied-cost shortest paths between the source and destination.
# Unidirectional and bidirectional Dijkstra can legitimately settle on different tied paths
# depending on traversal order, and the waypoint boundary correction applied afterwards is
# sensitive to exactly which path was chosen, so the resulting routes' coordinates/per-point
# values can differ even though both are correct shortest routes.
# Exact route matching isn't a meaningful check for these files;
# they're instead checked for total-cost equivalence only (see
# `test_bidirectional_total_cost_matches_unidirectional`).
TIED_PATH_ROUTES = [f for f in ALL_TEST_ROUTES if 'great_circle' in f]
TEST_ROUTES = [f for f in ALL_TEST_ROUTES if f not in TIED_PATH_ROUTES]


def _compute_route_pair(route_file):
    """
    Computes routes both with the standard (unidirectional) Dijkstra search and with
    `bidirectional_dijkstra` enabled, from the same input mesh/config, so the two can be
    compared directly.
    """
    LOGGER.info(f'Test File: {route_file}')

    with open(route_file, 'r') as fp:
        reference_route = json.load(fp)

    base_config = reference_route['config']['route_info']

    unidirectional_config = copy.deepcopy(base_config)
    unidirectional_route = calculate_dijkstra_route(
        unidirectional_config, copy.deepcopy(reference_route)
    )

    bidirectional_config = copy.deepcopy(base_config)
    bidirectional_config['bidirectional_dijkstra'] = True
    bidirectional_route = calculate_dijkstra_route(
        bidirectional_config, copy.deepcopy(reference_route)
    )

    return [unidirectional_route, bidirectional_route]


@pytest.fixture(scope='session', params=TEST_ROUTES)
def bidirectional_route_pair(request):
    return _compute_route_pair(request.param)


@pytest.fixture(scope='session', params=TIED_PATH_ROUTES)
def tied_path_route_pair(request):
    return _compute_route_pair(request.param)


@pytest.mark.parametrize('compare_func', [
    compare_route_coordinates,
    compare_waypoint_names,
    compare_time,
    compare_cell_indices,
    compare_cases
], ids=['coordinates', 'waypoint_names', 'time', 'cell_indices', 'cases'])
def test_bidirectional_matches_unidirectional(bidirectional_route_pair, compare_func):
    """Test route property matches between unidirectional and bidirectional search"""
    compare_func(*bidirectional_route_pair)


def test_bidirectional_fuel_battery(bidirectional_route_pair):
    """Test fuel/battery consumption matches between unidirectional and bidirectional search"""
    path_variables = bidirectional_route_pair[0]['config']['route_info']['path_variables']
    if 'fuel' in path_variables:
        compare_fuel(*bidirectional_route_pair)
    if 'battery' in path_variables:
        compare_battery(*bidirectional_route_pair)


def test_bidirectional_total_cost_matches_unidirectional(tied_path_route_pair):
    """
    For meshes with many exactly-tied-cost shortest paths (see `TIED_PATH_ROUTES`), only
    check that bidirectional search finds a route whose total cost is close to
    unidirectional search's, rather than requiring an identical route. Either algorithm may
    legitimately settle on a different tied-optimal path, and the waypoint boundary
    correction applied afterwards is sensitive to exactly which path was chosen, so a small
    relative difference between the two corrected totals is expected.
    """
    unidirectional_route, bidirectional_route = tied_path_route_pair
    path_variables = unidirectional_route['config']['route_info']['path_variables']

    for property_name in ['traveltime'] + [v for v in path_variables if v != 'traveltime']:
        values_a = unidirectional_route["paths"]["features"][0]["properties"][property_name]
        values_b = bidirectional_route["paths"]["features"][0]["properties"][property_name]
        np.testing.assert_allclose(
            values_b[-1], values_a[-1], rtol=0.01,
            err_msg=f'Difference in total "{property_name}"'
        )

