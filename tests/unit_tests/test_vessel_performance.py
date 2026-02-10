import pytest
import numpy as np
from polar_route.vessel_performance.vessels.SDA import (
    SDA,
    wind_resistance,
    wind_mag_dir,
    c_wind,
    calc_wind,
    fuel_eq,
)
from meshiphi.mesh_generation.aggregated_cellbox import AggregatedCellBox
from meshiphi.mesh_generation.boundary import Boundary


@pytest.fixture
def sda_vessel():
    """Fixture providing SDA vessel instance."""
    config = {
        "vessel_type": "SDA",
        "max_speed": 26.5,
        "unit": "km/hr",
        "beam": 24.0,
        "hull_type": "slender",
        "force_limit": 96634.5,
        "max_ice_conc": 80,
        "min_depth": -10,
    }
    return SDA(config)


@pytest.fixture
def base_cellbox():
    """Fixture providing base cellbox instance."""
    boundary = Boundary([-85, -84.9], [-135, -134.9], ["1970-01-01", "2021-12-31"])
    return AggregatedCellBox(boundary, {}, "0")


def test_land(sda_vessel, base_cellbox):
    """Test land detection returns False for navigable depth."""
    base_cellbox.agg_data = {"elevation": -100.0}
    assert not sda_vessel.land(base_cellbox)


def test_extreme_ice(sda_vessel, base_cellbox):
    """Test extreme ice detection for 100% concentration."""
    base_cellbox.agg_data = {"SIC": 100.0}
    assert sda_vessel.extreme_ice(base_cellbox)


@pytest.mark.parametrize(
    "agg_data, expected",
    [
        # Open water case
        (
            {"speed": 26.5, "SIC": 0.0, "thickness": 0.0, "density": 0.0},
            {
                "speed": [26.5] * 8,
                "SIC": 0.0,
                "thickness": 0.0,
                "density": 0.0,
                "ice resistance": 0.0,
            },
        ),
        # Ice case
        (
            {"speed": 26.5, "SIC": 60.0, "thickness": 1.0, "density": 980.0},
            {
                "speed": [7.842665122593933] * 8,
                "SIC": 60.0,
                "thickness": 1.0,
                "density": 980.0,
                "ice resistance": 96634.5,
            },
        ),
    ],
    ids=["open_water", "ice"],
)
def test_model_speed(sda_vessel, base_cellbox, agg_data, expected):
    """Test speed modeling in open water and ice conditions."""
    base_cellbox.agg_data = agg_data
    result = sda_vessel.model_speed(base_cellbox).agg_data
    assert result == expected


@pytest.mark.parametrize(
    "agg_data, expected",
    [
        # Open water
        (
            {
                "speed": [26.5] * 8,
                "SIC": 0.0,
                "thickness": 0.0,
                "density": 0.0,
                "ice resistance": 0.0,
            },
            {
                "speed": [26.5] * 8,
                "SIC": 0.0,
                "thickness": 0.0,
                "density": 0.0,
                "ice resistance": 0.0,
                "resistance": [0.0] * 8,
            },
        ),
        # Ice
        (
            {
                "speed": [7.842665122593933] * 8,
                "SIC": 60.0,
                "thickness": 1.0,
                "density": 980.0,
                "ice resistance": 96634.5,
            },
            {
                "speed": [7.842665122593933] * 8,
                "SIC": 60.0,
                "thickness": 1.0,
                "density": 980.0,
                "ice resistance": 96634.5,
                "resistance": [96634.5] * 8,
            },
        ),
    ],
    ids=["open_water", "ice"],
)
def test_model_resistance(sda_vessel, base_cellbox, agg_data, expected):
    """Test resistance modeling in open water and ice conditions."""
    base_cellbox.agg_data = agg_data
    result = sda_vessel.model_resistance(base_cellbox).agg_data
    assert result == expected


@pytest.mark.parametrize(
    "agg_data, expected_fuel",
    [
        # Open water
        (
            {
                "speed": [26.5] * 8,
                "SIC": 0.0,
                "thickness": 0.0,
                "density": 0.0,
                "ice resistance": 0.0,
                "resistance": [0.0] * 8,
            },
            [27.3186897] * 8,
        ),
        # Ice
        (
            {
                "speed": [7.842665122593933] * 8,
                "SIC": 60.0,
                "thickness": 1.0,
                "density": 980.0,
                "ice resistance": 96634.5,
                "resistance": [96634.5] * 8,
            },
            [39.94376930737089] * 8,
        ),
    ],
    ids=["open_water", "ice"],
)
def test_model_fuel(sda_vessel, base_cellbox, agg_data, expected_fuel):
    """Test fuel modeling in open water and ice conditions."""
    base_cellbox.agg_data = agg_data
    result = sda_vessel.model_fuel(base_cellbox).agg_data
    assert result["fuel"] == expected_fuel


@pytest.mark.parametrize(
    "speed, sic, thickness, density, expected",
    [
        (0.0, 0.0, 0.0, 0.0, 0.0),
        (5.56, 60.0, 1.0, 980.0, 64543.75549708632),
    ],
    ids=["zero", "positive"],
)
def test_ice_resistance(
    sda_vessel, base_cellbox, speed, sic, thickness, density, expected
):
    """Test ice resistance calculation."""
    base_cellbox.agg_data = {
        "speed": speed,
        "SIC": sic,
        "thickness": thickness,
        "density": density,
    }
    result = sda_vessel.ice_resistance(base_cellbox)
    assert result == pytest.approx(expected, abs=1e-5)


@pytest.mark.parametrize(
    "speed, sic, thickness, density, expected",
    [
        (26.5, 0.0, 0.0, 0.0, 26.5),
        (26.5, 60.0, 1.0, 980.0, 7.842665122593933),
    ],
    ids=["zero_resistance", "positive_resistance"],
)
def test_invert_resistance(
    sda_vessel, base_cellbox, speed, sic, thickness, density, expected
):
    """Test resistance inversion to calculate achievable speed."""
    base_cellbox.agg_data = {
        "speed": speed,
        "SIC": sic,
        "thickness": thickness,
        "density": density,
    }
    result = sda_vessel.invert_resistance(base_cellbox)
    assert result == pytest.approx(expected, abs=1e-5)


@pytest.mark.parametrize(
    "speed, resistance, expected",
    [
        (0.0, 0.0, 6.06970392),  # Hotel load
        (26.5, 0.0, 27.3186897),  # Open water
        (5.56, 64543.76, 24.48333122037351),  # Ice breaking
    ],
    ids=["hotel", "open_water", "ice_breaking"],
)
def test_fuel_eq(speed, resistance, expected):
    """Test fuel equation calculation."""
    result = fuel_eq(speed, resistance)
    assert result == pytest.approx(expected, abs=1e-5)


@pytest.mark.parametrize(
    "angle, expected", [(0.0, 0.94), (np.pi / 4.0, 0.595)], ids=["zero", "interpolated"]
)
def test_wind_coeff(angle, expected):
    """Test wind coefficient calculation."""
    assert c_wind(angle) == expected


@pytest.mark.parametrize(
    "v_vessel, v_wind, wind_dir, expected",
    [
        (0.0, 0.0, 0.0, 0.0),
        (10.0, 10.0, 0.0, 0.0),  # Equal opposite
        (10.0, 20.0, 0.0, 129543.75),
        (10.0, 20.0, np.pi, -105656.25),
    ],
    ids=["zero", "equal_opposite", "positive", "negative"],
)
def test_wind_resistance(v_vessel, v_wind, wind_dir, expected):
    """Test wind resistance calculation."""
    result = wind_resistance(v_vessel, v_wind, wind_dir)
    assert result == pytest.approx(expected, abs=1e-5)


@pytest.mark.parametrize(
    "speed, u10, v10, expected",
    [
        ([0.0] * 8, 0.0, 0.0, (0.0, 0.0)),
        ([10.0] * 8, 0.0, 10.0, (7.22222, np.pi)),
        ([10.0] * 8, 10.0, 0.0, (10.378634, 1.299849)),
    ],
    ids=["zero", "north", "east"],
)
def test_wind_mag_dir(base_cellbox, speed, u10, v10, expected):
    """Test wind magnitude and direction calculation."""
    base_cellbox.agg_data = {"speed": speed, "u10": u10, "v10": v10}
    result = wind_mag_dir(base_cellbox, 0.0)
    assert result[0] == pytest.approx(expected[0], abs=1e-5)
    assert result[1] == pytest.approx(expected[1], abs=1e-5)


@pytest.mark.parametrize(
    "speed, u10, v10, expected",
    [
        # Zero wind
        (
            [0.0] * 8,
            0.0,
            0.0,
            {
                "speed": [0.0] * 8,
                "u10": 0.0,
                "v10": 0.0,
                "wind resistance": [0] * 8,
                "relative wind speed": [0] * 8,
                "relative wind angle": [0] * 8,
            },
        ),
        # Northerly wind
        (
            [10.0] * 8,
            0.0,
            10.0,
            {
                "speed": [10.0] * 8,
                "u10": 0.0,
                "v10": 10.0,
                "wind resistance": [
                    1389.4514464984172,
                    18883.168370819058,
                    44192.363791332944,
                    67170.852525,
                    44192.36379133295,
                    18883.168370819058,
                    1389.45144649843,
                    -11478.704021299203,
                ],
                "relative wind speed": [
                    8.272382984093076,
                    10.378634868247365,
                    12.124347537962088,
                    12.77778,
                    12.124347537962088,
                    10.378634868247365,
                    8.272382984093076,
                    7.22222,
                ],
                "relative wind angle": [
                    2.11646579563727,
                    1.299849270152763,
                    0.6226774988830187,
                    0.0,
                    0.6226774988830185,
                    1.2998492701527629,
                    2.1164657956372697,
                    3.141592653589793,
                ],
            },
        ),
        # Easterly wind
        (
            [10.0] * 8,
            10.0,
            0.0,
            {
                "speed": [10.0] * 8,
                "u10": 10.0,
                "v10": 0.0,
                "wind resistance": [
                    1389.45144649843,
                    -11478.704021299203,
                    1389.4514464984172,
                    18883.168370819058,
                    44192.363791332944,
                    67170.852525,
                    44192.363791332944,
                    18883.168370819058,
                ],
                "relative wind speed": [
                    8.272382984093076,
                    7.22222,
                    8.272382984093076,
                    10.378634868247365,
                    12.124347537962088,
                    12.77778,
                    12.124347537962088,
                    10.378634868247365,
                ],
                "relative wind angle": [
                    2.1164657956372697,
                    3.141592653589793,
                    2.11646579563727,
                    1.299849270152763,
                    0.6226774988830187,
                    0.0,
                    0.6226774988830187,
                    1.2998492701527629,
                ],
            },
        ),
    ],
    ids=["zero", "north", "east"],
)
def test_calc_wind(base_cellbox, speed, u10, v10, expected):
    """Test complete wind calculation with different wind directions."""
    base_cellbox.agg_data = {"speed": speed, "u10": u10, "v10": v10}
    result = calc_wind(base_cellbox).agg_data
    assert result == expected


def test_model_resistance_ice_wind_north(sda_vessel, base_cellbox):
    """Test combined ice and wind resistance modeling."""
    base_cellbox.agg_data = {
        "speed": [7.842665122593933] * 8,
        "SIC": 60.0,
        "thickness": 1.0,
        "density": 980.0,
        "ice resistance": 96634.5,
        "u10": 0.0,
        "v10": 10.0,
    }
    result = sda_vessel.model_resistance(base_cellbox).agg_data
    expected = {
        "speed": [7.842665122593933] * 8,
        "SIC": 60.0,
        "thickness": 1.0,
        "density": 980.0,
        "ice resistance": 96634.5,
        "u10": 0.0,
        "v10": 10.0,
        "wind resistance": [
            1234.4775504276085,
            19864.391781102568,
            40525.12205230855,
            61995.4919027709,
            40525.1220523086,
            19864.391781102568,
            1234.4775504276222,
            -11604.216485701227,
        ],
        "relative wind speed": [
            8.598664182949458,
            10.234546822417895,
            11.64280342483676,
            12.178519832423898,
            11.642803424836762,
            10.234546822417895,
            8.598664182949458,
            7.8214801675761025,
        ],
        "relative wind angle": [
            2.176072621553403,
            1.356295795185576,
            0.652700196811307,
            0.0,
            0.6527001968113064,
            1.3562957951855759,
            2.1760726215534025,
            3.141592653589793,
        ],
        "resistance": [
            97868.9775504276,
            116498.89178110257,
            137159.62205230855,
            158629.99190277088,
            137159.6220523086,
            116498.89178110257,
            97868.97755042762,
            85030.28351429878,
        ],
    }
    assert result == expected
