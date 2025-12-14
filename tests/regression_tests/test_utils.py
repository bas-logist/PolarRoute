"""
Shared utilities for regression tests
"""

import logging
from pathlib import Path
from typing import List, Tuple

# Configure logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

def get_test_data_path(relative_path: str) -> str:
    """Convert relative path to absolute path based on test file location"""
    test_dir = Path(__file__).parent
    return str(test_dir / relative_path.lstrip('./').lstrip('/'))

def discover_test_files(pattern: str) -> List[str]:
    """Discover test files matching a glob pattern"""
    test_dir = Path(__file__).parent
    return [str(p) for p in test_dir.glob(pattern)]

def get_route_test_files(route_type: str) -> List[str]:
    """Get all test route files for a specific route type (dijkstra or smoothed)"""
    pattern = f"example_routes/{route_type}/**/*.json"
    return discover_test_files(pattern)

def get_mesh_test_files() -> Tuple[List[str], List[str]]:
    """Get input and output mesh files for vessel tests"""
    input_pattern = "example_meshes/env_meshes/*.json"
    output_pattern = "example_meshes/vessel_meshes/*.json"
    
    input_meshes = discover_test_files(input_pattern)
    output_meshes = discover_test_files(output_pattern)
    
    # Sort to ensure consistent pairing
    input_meshes.sort()
    output_meshes.sort()
    
    return input_meshes, output_meshes