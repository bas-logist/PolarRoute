"""
    Regression testing package to ensure consistent functionality in development
    of the PolarRoute python package.
"""

import json
import pytest
import time

from polar_route import VesselPerformanceModeller

import logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

# Import test file discovery
from .test_utils import get_mesh_test_files

# Dynamically discover test files
INPUT_MESHES, OUTPUT_MESHES = get_mesh_test_files()

@pytest.fixture(scope='session', autouse=False, params=zip(INPUT_MESHES, OUTPUT_MESHES))
def mesh_pair(request):
    """
    Creates a pair of JSON objects, one newly generated, one as old reference
    Args:
        request (fixture):
            fixture object including list of meshes to regenerate

    Returns:
        list: old and new mesh jsons for comparison
    """
    LOGGER.info(f'Test File: {request.param[1]}')

    input_mesh_file = request.param[0]
    output_mesh_file = request.param[1]
    # Open vessel mesh for reference
    with open(output_mesh_file, 'r') as fp:
        old_mesh = json.load(fp)
    # Open env mesh to generate new vessel mesh
    with open(input_mesh_file, 'r') as fp:
        input_mesh = json.load(fp)
    # Extract out vessel config from reference mesh
    vessel_config = old_mesh['config']['vessel_info']
    new_mesh = calculate_vessel_mesh(input_mesh, vessel_config)
    
    return [old_mesh, new_mesh]

def calculate_vessel_mesh(mesh_json, vessel_config):
    """
    Creates a new, pruned and updated mesh from the environmental mesh

    Args:
        mesh_json (json): Environmental mesh to modify with vessel parameters
        vessel_config (json): Vessel information to prune the env mesh with

    Returns:
        json: Newly regenerated mesh
    """
    start = time.perf_counter()

    new_mesh = VesselPerformanceModeller(mesh_json, vessel_config)
    new_mesh.model_accessibility()
    new_mesh.model_performance()

    end = time.perf_counter()

    cellbox_count = len(new_mesh.env_mesh.agg_cellboxes)
    LOGGER.info(f'Vessel simulated against {cellbox_count} cellboxes in {end - start} seconds')

    return new_mesh.to_json()