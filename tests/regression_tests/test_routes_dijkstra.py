import json
import pytest
import time

from polar_route.route_planner.route_planner import RoutePlanner

from .route_test_functions import extract_waypoints
from .route_test_functions import extract_route_info

import logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

# Import test file discovery
from .test_utils import get_route_test_files

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
    route_info = extract_route_info(old_route)
    # Create new json (cast old to dict to create copy to avoid modifying)
    new_route = calculate_dijkstra_route(route_info, dict(old_route))

    return [old_route, new_route]

# Generating new outputs
def calculate_dijkstra_route(config, mesh):
    """
    Calculates the optimised route, with dijkstra but no smoothing

    Args:
        config (dict): the route config
        mesh (dict): the reference mesh (including routes and waypoints)

    Returns:
        new_route (dict): new route output
    """
    start = time.perf_counter()

    # Initial set up
    waypoints   = extract_waypoints(mesh)

    # Calculate dijkstra route
    rp = RoutePlanner(mesh, config)
    routes = rp.compute_routes(waypoints)
    
    # Generate json to compare to old output
    new_route = mesh
    new_route['paths'] = {"type": "FeatureCollection", "features": []}
    new_route['paths']['features'] = [r.to_json() for r in routes]

    end = time.perf_counter()
    LOGGER.info(f'Route calculated in {end - start} seconds')

    return new_route

# Test functions that use the route_pair fixture
from .route_test_functions import (
    test_route_coordinates as _test_route_coordinates,
    test_waypoint_names as _test_waypoint_names,
    test_time as _test_time,
    test_fuel_battery as _test_fuel_battery,
    test_cell_indices as _test_cell_indices,
    test_cases as _test_cases
)

def test_route_coordinates(route_pair):
    """Test route coordinates match between old and new"""
    _test_route_coordinates(route_pair)

def test_waypoint_names(route_pair):
    """Test waypoint names match between old and new"""
    _test_waypoint_names(route_pair)

def test_time(route_pair):
    """Test travel times match between old and new"""
    _test_time(route_pair)

def test_fuel_battery(route_pair):
    """Test fuel/battery consumption matches between old and new"""
    _test_fuel_battery(route_pair)

def test_cell_indices(route_pair):
    """Test cell indices match between old and new"""
    _test_cell_indices(route_pair)

def test_cases(route_pair):
    """Test case information matches between old and new"""
    _test_cases(route_pair)