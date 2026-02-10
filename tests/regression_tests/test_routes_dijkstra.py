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
@pytest.fixture(scope='session', params=TEST_ROUTES)
def route_pair(request):
    """Creates pair of routes: reference JSON and newly generated."""
    LOGGER.info(f'Test File: {request.param}')
    
    with open(request.param, 'r') as fp:
        old_route = json.load(fp)
    
    new_route = calculate_dijkstra_route(old_route['config']['route_info'], dict(old_route))
    return [old_route, new_route]

# Test functions that use the route_pair fixture
@pytest.mark.parametrize('compare_func', [
    compare_route_coordinates,
    compare_waypoint_names,
    compare_time,
    compare_cell_indices,
    compare_cases
], ids=['coordinates', 'waypoint_names', 'time', 'cell_indices', 'cases'])
def test_route_property(route_pair, compare_func):
    """Test route property matches between old and new"""
    compare_func(*route_pair)

def test_fuel_battery(route_pair):
    """Test fuel/battery consumption matches between old and new"""
    path_variables = route_pair[0]['config']['route_info']['path_variables']
    if 'fuel' in path_variables:
        compare_fuel(*route_pair)
    if 'battery' in path_variables:
        compare_battery(*route_pair)