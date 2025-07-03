import json
import pytest
import pandas as pd
import os

from io import StringIO
from jsonschema.exceptions import ValidationError

from polar_route.config_validation.config_validator import (
    validate_vessel_config,
    validate_route_config,
    validate_waypoints,
)

waypoints_columns = ["Name", "Lat", "Long", "Source", "Destination"]

EXAMPLES_DIR = os.path.join("examples")


def load_json_example(path):
    """Helper to load a JSON example or skip test if file missing."""
    if not os.path.exists(path):
        pytest.skip(f"Example file not found: {path}")
    with open(path) as fp:
        return json.load(fp)


def load_csv_example(path):
    """Helper to load a CSV example or skip test if file missing."""
    if not os.path.exists(path):
        pytest.skip(f"Example CSV file not found: {path}")
    return pd.read_csv(path)


# Vessel config tests
def test_validate_vessel_config_file():
    """Test that vessel config example file validates successfully."""
    path = os.path.join(EXAMPLES_DIR, "vessel_config", "SDA.config.json")
    vessel_config = load_json_example(path)
    validate_vessel_config(vessel_config)


@pytest.mark.parametrize(
    "invalid_config, match_str",
    [
        ({"vessel_type": "SDA", "unit": "km/hr"}, "max_speed"),
        (
            {"vessel_type": "SDA", "unit": "km/hr", "max_speed": "fast"},
            "max_speed",
        ),
    ],
)
def test_validate_vessel_config_invalid(invalid_config, match_str):
    """Test ValidationError raised for missing or invalid max_speed."""
    with pytest.raises(ValidationError, match=match_str):
        validate_vessel_config(invalid_config)


def test_validate_vessel_config_not_dict():
    """Test TypeError is raised when vessel config is not a dict."""
    with pytest.raises(TypeError):
        validate_vessel_config(["this", "is", "a", "list"])


def test_validate_vessel_config_extra_keys():
    """Test that vessel config with extra keys passes as expected."""
    base_config = {
        "vessel_type": "SDA",
        "max_speed": 20,
        "unit": "km/hr",
    }
    config_with_extra = base_config.copy()
    config_with_extra["additional_field"] = "some value"

    validate_vessel_config(config_with_extra)


def test_validate_vessel_config_empty_dict():
    """Test ValidationError raised on empty vessel config dict."""
    with pytest.raises(ValidationError):
        validate_vessel_config({})


@pytest.mark.parametrize(
    "invalid_config, match_str",
    [
        ({"vessel_type": None, "max_speed": 26.5, "unit": "km/hr"}, "vessel_type"),
        ({"vessel_type": "SDA", "max_speed": None, "unit": "km/hr"}, "max_speed"),
        ({"vessel_type": "SDA", "max_speed": 26.5, "unit": None}, "unit"),
    ],
)
def test_validate_vessel_config_null_fields(invalid_config, match_str):
    """Test ValidationError for null required fields in vessel config."""
    with pytest.raises(ValidationError, match=match_str):
        validate_vessel_config(invalid_config)


# Route config tests
def test_validate_route_config_file():
    """Test that route config example file validates successfully."""
    path = os.path.join(EXAMPLES_DIR, "route_config", "all_options.config.json")
    route_config = load_json_example(path)
    validate_route_config(route_config)


@pytest.mark.parametrize(
    "invalid_config, match_str",
    [
        (
            {"objective_function": "fuel_use"},
            "path_variables",
        ),
        (
            {
                "objective_function": "fuel_use",
                "path_variables": ["lat", "lon"],
                "vector_names": ["current_u", "current_v"],
                "time_unit": "weeks",
            },
            "weeks",
        ),
        (
            {
                "objective_function": "fuel_use",
                "path_variables": "lat,lon",
                "vector_names": ["current_u", "current_v"],
            },
            "path_variables",
        ),
    ],
)
def test_validate_route_config_invalid(invalid_config, match_str):
    """Test ValidationError raised for various route config validation errors."""
    with pytest.raises(ValidationError, match=match_str):
        validate_route_config(invalid_config)


def test_validate_route_config_not_dict():
    """Test TypeError is raised when route config is not a dict."""
    with pytest.raises(TypeError):
        validate_route_config(["this", "is", "a", "list"])


# Waypoints validation tests
def test_validate_waypoints_file():
    """Test that example waypoints CSV validates successfully."""
    path = os.path.join(EXAMPLES_DIR, "waypoints_example.csv")
    df = load_csv_example(path)
    validate_waypoints(df)


@pytest.mark.parametrize(
    "csv_content, error_match",
    [
        (
            """
Index,Name,Lat,Source
0,WP1,60.0,X
""",
            "Expected the following columns",
        ),
        (
            """
Index,Name,Lat,Long,Source,Destination
0,WP1,60.0,-45.0,,X
""",
            "No source waypoint defined!",
        ),
        (
            """
Index,Name,Lat,Long,Source,Destination
0,WP1,60.0,-45.0,X,
""",
            "No destination waypoint defined!",
        ),
        (
            """
Index,Name,Lat,Long,Source,Destination
0,WP1,sixty,-45.0,X,
1,WP2,61.0,not_a_number,,X
""",
            'Non-numeric value in "Lat" column',
        ),
    ],
)
def test_validate_waypoints_invalid(csv_content, error_match):
    """Test AssertionError raised for various waypoint validation errors."""
    df = pd.read_csv(StringIO(csv_content))
    with pytest.raises(AssertionError, match=error_match):
        validate_waypoints(df)


def test_validate_waypoints_not_csv():
    """Test TypeError raised when waypoints input is not a DataFrame."""
    with pytest.raises(TypeError):
        validate_waypoints(["this", "is", "a", "list"])
