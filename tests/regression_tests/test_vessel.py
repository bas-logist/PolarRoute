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

@pytest.fixture(scope='session', params=MESH_PAIRS, ids=MESH_IDS)
def mesh_pair(request):
    """Creates pair of meshes: reference and newly generated."""
    input_mesh_file, output_mesh_file = request.param
    LOGGER.info(f'Test File: {output_mesh_file}')
    
    with open(output_mesh_file, 'r') as fp:
        old_mesh = json.load(fp)
    with open(input_mesh_file, 'r') as fp:
        input_mesh = json.load(fp)
    
    # Merge vessel config from reference into input mesh
    config = input_mesh.copy()
    config.setdefault('config', {})['vessel_info'] = old_mesh['config']['vessel_info']
    
    new_mesh = calculate_vessel_mesh(config)
    return [old_mesh, new_mesh]

# Test functions that use the mesh_pair fixture
@pytest.mark.parametrize('compare_func', [
    compare_cellbox_count,
    compare_cellbox_ids,
    compare_cellbox_values,
    compare_cellbox_attributes,
    compare_neighbour_graph_count,
    compare_neighbour_graph_ids,
    compare_neighbour_graph_values
], ids=['cellbox_count', 'cellbox_ids', 'cellbox_values', 'cellbox_attributes',
        'graph_count', 'graph_ids', 'graph_values'])
def test_vessel_mesh(mesh_pair, compare_func):
    """Test vessel mesh property matches between old and new"""
    compare_func(*mesh_pair)