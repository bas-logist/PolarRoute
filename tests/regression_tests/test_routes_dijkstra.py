import json
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
    compare_cases
)

import logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

# Dynamically discover test files
TEST_ROUTES = get_route_test_files('dijkstra')

# Pairing old and new outputs
@pytest.fixture(scope='session', autouse=False, params=TEST_ROUTES)
def route_pair(request):
    """
    Creates a pair of JSON objects, one newly generated, one as old reference
    Args:
        request (fixture): 
            fixture object including list of jsons of optimised routes

    Returns:
        list: [reference json, new json]
    """

    LOGGER.info(f'Test File: {request.param}')

    # Load reference JSON
    with open(request.param, 'r') as fp:
        old_route = json.load(fp)
    route_info = old_route['config']['route_info']
    # Create new json (cast old to dict to create copy to avoid modifying)
    new_route = calculate_dijkstra_route(route_info, dict(old_route))

    return [old_route, new_route]

# Test functions that use the route_pair fixture
def test_route_coordinates(route_pair):
    """Test route coordinates match between old and new"""
    compare_route_coordinates(*route_pair)

def test_waypoint_names(route_pair):
    """Test waypoint names match between old and new"""
    compare_waypoint_names(*route_pair)

def test_time(route_pair):
    """Test travel times match between old and new"""
    compare_time(*route_pair)

def test_fuel_battery(route_pair):
    """Test fuel/battery consumption matches between old and new"""
    path_variables = route_pair[0]['config']['route_info']['path_variables']
    if 'fuel' in path_variables:
        compare_fuel(*route_pair)
    if 'battery' in path_variables:
        compare_battery(*route_pair)

def test_cell_indices(route_pair):
    """Test cell indices match between old and new"""
    compare_cell_indices(*route_pair)

def test_cases(route_pair):
    """Test case information matches between old and new"""
    compare_cases(*route_pair)