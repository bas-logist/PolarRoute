import pytest
import numpy as np
from polar_route.route_planner.crossing import traveltime_in_cell


@pytest.mark.parametrize(
    "bx, by, cx, cy, speed, expected_tt, test_id",
    [
        (30, 15, 2, -4, np.sqrt(65), 5.0, "normal_current"),
        (30, 15, -2, -4, np.sqrt(65), 8.33333, "reverse_current"),
        (30, 15, 2, -4, 5, 15.0, "slow_vessel"),
    ],
)
def test_traveltime_in_cell(bx, by, cx, cy, speed, expected_tt, test_id):
    """Test travel time calculation in cell with various conditions."""
    tt = traveltime_in_cell(bx, by, cx, cy, speed)
    assert tt == pytest.approx(expected_tt, abs=1e-5)
