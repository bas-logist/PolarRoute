"""
    Regression testing package to ensure consistent functionality in development
    of the PolarRoute python package.
"""

import json
import pytest
from pathlib import Path

import logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

# Import test utilities
from .utils import (
    get_mesh_test_files,
    compare_cellbox_count,
    compare_cellbox_ids,
    compare_cellbox_values,
    compare_cellbox_attributes,
    compare_neighbour_graph_count,
    compare_neighbour_graph_ids,
    compare_neighbour_graph_values,
    calculate_vessel_mesh
)

# Dynamically discover test files
INPUT_MESHES, OUTPUT_MESHES = get_mesh_test_files()

# Create descriptive IDs from mesh file names
def make_mesh_id(mesh_pair):
    """Create descriptive test ID from mesh file paths"""
    input_mesh, output_mesh = mesh_pair
    output_name = Path(output_mesh).stem
    return output_name

MESH_PAIRS = list(zip(INPUT_MESHES, OUTPUT_MESHES))
MESH_IDS = [make_mesh_id(pair) for pair in MESH_PAIRS]

@pytest.fixture(scope='session', autouse=False, params=MESH_PAIRS, ids=MESH_IDS)
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
    
    # Merge vessel config with input mesh config
    config = input_mesh.copy()
    if 'config' not in config:
        config['config'] = {}
    config['config']['vessel_info'] = vessel_config
    
    new_mesh = calculate_vessel_mesh(config)
    
    return [old_mesh, new_mesh]

# Test functions that use the mesh_pair fixture
def test_vessel_mesh_cellbox_count(mesh_pair):
    """Test mesh cellbox count matches between old and new"""
    compare_cellbox_count(*mesh_pair)

def test_vessel_mesh_cellbox_ids(mesh_pair):
    """Test mesh cellbox IDs match between old and new"""
    compare_cellbox_ids(*mesh_pair)

def test_vessel_mesh_cellbox_values(mesh_pair):
    """Test mesh cellbox values match between old and new"""
    compare_cellbox_values(*mesh_pair)

def test_vessel_mesh_cellbox_attributes(mesh_pair):
    """Test mesh cellbox attributes match between old and new"""
    compare_cellbox_attributes(*mesh_pair)

def test_vessel_mesh_neighbour_graph_count(mesh_pair):
    """Test mesh neighbour graph count matches between old and new"""
    compare_neighbour_graph_count(*mesh_pair)

def test_vessel_mesh_neighbour_graph_ids(mesh_pair):
    """Test mesh neighbour graph IDs match between old and new"""
    compare_neighbour_graph_ids(*mesh_pair)

def test_vessel_mesh_neighbour_graph_values(mesh_pair):
    """Test mesh neighbour graph values match between old and new"""
    compare_neighbour_graph_values(*mesh_pair)