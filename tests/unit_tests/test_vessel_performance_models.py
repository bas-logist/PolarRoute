"""
Unit tests for model-based vessel performance system.

Tests individual resistance models, consumption models, and generic vessel classes.
"""

import pytest
import numpy as np
from polar_route.vessel_performance.models.resistance import (
    FroudeIceResistance,
    WindDragResistance,
    KreitnerWaveResistance
)
from polar_route.vessel_performance.models.consumption import (
    PolynomialFuelModel,
    PolynomialBatteryModel,
    ConstantConsumptionModel
)
from polar_route.vessel_performance.vessels.generic_vessels import Ship, Glider, AUV, Aircraft
from polar_route.vessel_performance.models import ModelRegistry
from meshiphi.mesh_generation.aggregated_cellbox import AggregatedCellBox
from meshiphi.mesh_generation.boundary import Boundary


# Resistance Model Tests

class TestFroudeIceResistance:
    """Test Froude-based ice resistance model."""
    
    @pytest.fixture
    def ice_model(self):
        """Create ice resistance model with SDA slender hull parameters."""
        return FroudeIceResistance(
            k=4.4, b=-0.8267, n=2.0,
            beam=24.0, force_limit=96634.5, gravity=9.81
        )
    
    @pytest.fixture
    def cellbox_with_ice(self):
        """Cellbox with ice conditions."""
        boundary = Boundary([-85, -84.9], [-135, -134.9], ["1970-01-01", "2021-12-31"])
        cellbox = AggregatedCellBox(boundary, {}, "0")
        cellbox.agg_data = {
            "SIC": 50.0,  # 50% ice concentration
            "thickness": 1.0,  # 1m thick ice
            "density": 900.0  # 900 kg/m³
        }
        return cellbox
    
    def test_no_ice_gives_zero_resistance(self, ice_model):
        """Test that no ice returns zero resistance."""
        boundary = Boundary([-85, -84.9], [-135, -134.9], ["1970-01-01", "2021-12-31"])
        cellbox = AggregatedCellBox(boundary, {}, "0")
        cellbox.agg_data = {"SIC": 0.0, "thickness": 0.0, "density": 900.0}
        
        resistance = ice_model.calculate_resistance(cellbox, speed=15.0)
        assert resistance == 0.0
    
    def test_ice_resistance_positive(self, ice_model, cellbox_with_ice):
        """Test that ice resistance is positive."""
        resistance = ice_model.calculate_resistance(cellbox_with_ice, speed=15.0)
        assert resistance > 0.0
    
    def test_ice_resistance_increases_with_speed(self, ice_model, cellbox_with_ice):
        """Test that resistance increases with speed."""
        r1 = ice_model.calculate_resistance(cellbox_with_ice, speed=10.0)
        r2 = ice_model.calculate_resistance(cellbox_with_ice, speed=20.0)
        assert r2 > r1
    
    def test_invert_resistance_returns_valid_speed(self, ice_model, cellbox_with_ice):
        """Test that speed inversion returns reasonable value."""
        max_speed = ice_model.invert_resistance(cellbox_with_ice, force_limit=96634.5)
        assert max_speed > 0.0
        assert max_speed < 100.0  # Reasonable speed limit
        
        # Verify that calculated speed gives resistance near limit
        resistance = ice_model.calculate_resistance(cellbox_with_ice, max_speed)
        assert abs(resistance - 96634.5) / 96634.5 < 0.1  # Within 10%


class TestWindDragResistance:
    """Test wind drag resistance model."""
    
    @pytest.fixture
    def wind_model(self):
        """Create wind resistance model with SDA parameters."""
        return WindDragResistance(
            frontal_area=750.0,
            angles=[0, 30, 60, 90, 120, 150, 180],
            coefficients=[0.94, 0.77, 0.42, 0.48, 0.17, -0.30, -0.34],
            interpolation="linear",
            air_density=1.225
        )
    
    @pytest.fixture
    def cellbox_with_wind(self):
        """Cellbox with wind conditions."""
        boundary = Boundary([-85, -84.9], [-135, -134.9], ["1970-01-01", "2021-12-31"])
        cellbox = AggregatedCellBox(boundary, {}, "0")
        cellbox.agg_data = {
            "u10": 10.0,  # 10 m/s eastward wind
            "v10": 0.0,   # No northward component
            "speed": [15.0] * 8
        }
        return cellbox
    
    def test_no_wind_gives_zero_resistance(self, wind_model):
        """Test that no wind returns zero resistance."""
        boundary = Boundary([-85, -84.9], [-135, -134.9], ["1970-01-01", "2021-12-31"])
        cellbox = AggregatedCellBox(boundary, {}, "0")
        cellbox.agg_data = {"u10": 0.0, "v10": 0.0, "speed": [15.0] * 8}
        
        resistance = wind_model.calculate_resistance(cellbox, speed=15.0, direction=0.0)
        # Should be near zero (small numerical differences possible)
        assert abs(resistance) < 10.0
    
    def test_headwind_gives_positive_resistance(self, wind_model, cellbox_with_wind):
        """Test that headwind creates positive resistance."""
        # Travel eastward (π/2) into eastward wind
        resistance = wind_model.calculate_resistance(
            cellbox_with_wind, speed=15.0, direction=np.pi/2
        )
        assert resistance > 0.0
    
    def test_tailwind_gives_negative_resistance(self, wind_model, cellbox_with_wind):
        """Test that tailwind creates negative resistance (boost)."""
        # Travel westward (3π/2) with eastward wind at back
        resistance = wind_model.calculate_resistance(
            cellbox_with_wind, speed=15.0, direction=3*np.pi/2
        )
        assert resistance < 0.0


class TestWaveResistance:
    """Test Kreitner wave resistance model."""
    
    @pytest.fixture
    def wave_model(self):
        """Create wave resistance model."""
        return KreitnerWaveResistance(
            beam=24.0, length=129.0, c_block=0.75, rho_water=9807
        )
    
    def test_no_waves_gives_zero_resistance(self, wave_model):
        """Test that no waves returns zero resistance."""
        boundary = Boundary([-85, -84.9], [-135, -134.9], ["1970-01-01", "2021-12-31"])
        cellbox = AggregatedCellBox(boundary, {}, "0")
        cellbox.agg_data = {"swh": 0.0}
        
        resistance = wave_model.calculate_resistance(cellbox, speed=15.0)
        assert resistance == 0.0
    
    def test_wave_resistance_positive(self, wave_model):
        """Test that waves create positive resistance."""
        boundary = Boundary([-85, -84.9], [-135, -134.9], ["1970-01-01", "2021-12-31"])
        cellbox = AggregatedCellBox(boundary, {}, "0")
        cellbox.agg_data = {"swh": 1.5}  # 1.5m waves
        
        resistance = wave_model.calculate_resistance(cellbox, speed=15.0)
        assert resistance > 0.0
    
    def test_wave_resistance_increases_with_height(self, wave_model):
        """Test that resistance increases with wave height."""
        boundary = Boundary([-85, -84.9], [-135, -134.9], ["1970-01-01", "2021-12-31"])
        cellbox = AggregatedCellBox(boundary, {}, "0")
        
        cellbox.agg_data = {"swh": 1.0}
        r1 = wave_model.calculate_resistance(cellbox, speed=15.0)
        
        cellbox.agg_data = {"swh": 2.0}
        r2 = wave_model.calculate_resistance(cellbox, speed=15.0)
        
        assert r2 > r1


# Consumption Model Tests

class TestPolynomialFuelModel:
    """Test polynomial fuel consumption model."""
    
    @pytest.fixture
    def fuel_model(self):
        """Create fuel model with SDA parameters."""
        return PolynomialFuelModel(
            speed_coeffs=[0.00137247, -0.0029601, 0.25290433],
            resistance_coeffs=[7.75218178e-11, 6.48113363e-06]
        )
    
    def test_fuel_consumption_positive(self, fuel_model):
        """Test that fuel consumption is positive."""
        fuel = fuel_model.calculate_consumption(speed=15.0, resistance=50000.0)
        assert fuel > 0.0
    
    def test_fuel_increases_with_speed(self, fuel_model):
        """Test that fuel increases with speed."""
        f1 = fuel_model.calculate_consumption(speed=10.0, resistance=50000.0)
        f2 = fuel_model.calculate_consumption(speed=20.0, resistance=50000.0)
        assert f2 > f1
    
    def test_fuel_increases_with_resistance(self, fuel_model):
        """Test that fuel increases with resistance."""
        f1 = fuel_model.calculate_consumption(speed=15.0, resistance=10000.0)
        f2 = fuel_model.calculate_consumption(speed=15.0, resistance=90000.0)
        assert f2 > f1
    
    def test_negative_resistance_treated_as_zero(self, fuel_model):
        """Test that negative resistance is clamped to zero."""
        f1 = fuel_model.calculate_consumption(speed=15.0, resistance=0.0)
        f2 = fuel_model.calculate_consumption(speed=15.0, resistance=-5000.0)
        assert f1 == f2


class TestPolynomialBatteryModel:
    """Test polynomial battery consumption model."""
    
    @pytest.fixture
    def battery_model(self):
        """Create battery model with Slocum parameters."""
        return PolynomialBatteryModel(
            speed_coeffs=[4.44444444, -0.5555555499999991],
            depth_coeffs=[0.001, 2]
        )
    
    def test_battery_consumption_positive(self, battery_model):
        """Test that battery consumption is positive."""
        battery = battery_model.calculate_consumption(speed=1.0, depth=50.0)
        assert battery > 0.0
    
    def test_battery_increases_with_depth(self, battery_model):
        """Test that battery consumption increases with depth."""
        b1 = battery_model.calculate_consumption(speed=1.0, depth=10.0)
        b2 = battery_model.calculate_consumption(speed=1.0, depth=100.0)
        assert b2 > b1


class TestConstantConsumptionModel:
    """Test constant consumption model."""
    
    def test_constant_consumption(self):
        """Test that consumption is constant."""
        model = ConstantConsumptionModel(rate=4.75)
        
        c1 = model.calculate_consumption(speed=1.0)
        c2 = model.calculate_consumption(speed=10.0, resistance=10000.0)
        
        assert c1 == 4.75
        assert c2 == 4.75
        assert c1 == c2


# Model Registry Tests

class TestModelRegistry:
    """Test model registration and creation."""
    
    def test_registered_models_exist(self):
        """Test that expected models are registered."""
        registered = ModelRegistry.get_registered_models()
        
        expected_models = [
            "ice_froude", "wind_drag", "wave_kreitner",
            "polynomial_fuel", "polynomial_battery", "constant_consumption"
        ]
        
        for model in expected_models:
            assert model in registered
    
    def test_create_ice_model(self):
        """Test creating ice model via registry."""
        model = ModelRegistry.create("ice_froude", {
            "k": 4.4, "b": -0.8267, "n": 2.0,
            "beam": 24.0, "force_limit": 96634.5
        })
        assert isinstance(model, FroudeIceResistance)
    
    def test_create_unknown_model_raises_error(self):
        """Test that unknown model name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown model type"):
            ModelRegistry.create("nonexistent_model", {})


# Generic Vessel Tests

class TestShip:
    """Test generic Ship vessel class."""
    
    @pytest.fixture
    def ship_config(self):
        """Configuration for SDA-like ship."""
        return {
            "vessel_class": "ship",
            "max_speed": 26.5,
            "unit": "km/hr",
            "max_ice_conc": 80,
            "min_depth": 10,
            "num_directions": 8,
            "resistance_models": [
                {
                    "type": "ice_froude",
                    "params": {
                        "k": 4.4, "b": -0.8267, "n": 2.0,
                        "beam": 24.0, "force_limit": 96634.5, "gravity": 9.81
                    }
                }
            ],
            "consumption_model": {
                "type": "polynomial_fuel",
                "params": {
                    "speed_coeffs": [0.00137247, -0.0029601, 0.25290433],
                    "resistance_coeffs": [7.75218178e-11, 6.48113363e-06]
                }
            }
        }
    
    @pytest.fixture
    def ship(self, ship_config):
        """Create ship instance."""
        return Ship(ship_config)
    
    def test_ship_initialization(self, ship):
        """Test that ship initializes correctly."""
        assert ship.max_speed == 26.5
        assert ship.num_directions == 8
        assert len(ship.resistance_models) == 1
    
    def test_ship_model_performance_returns_correct_keys(self, ship):
        """Test that model_performance returns expected keys."""
        boundary = Boundary([-85, -84.9], [-135, -134.9], ["1970-01-01", "2021-12-31"])
        cellbox = AggregatedCellBox(boundary, {}, "0")
        cellbox.agg_data = {
            "SIC": 30.0,
            "thickness": 0.5,
            "density": 900.0,
            "speed": 26.5
        }
        
        performance = ship.model_performance(cellbox)
        
        assert "speed" in performance
        assert "resistance" in performance
        assert "fuel" in performance
        assert len(performance["speed"]) == 8
        assert len(performance["resistance"]) == 8
        assert len(performance["fuel"]) == 8
    
    def test_ship_accessibility_land(self, ship):
        """Test that ship detects land correctly."""
        boundary = Boundary([-85, -84.9], [-135, -134.9], ["1970-01-01", "2021-12-31"])
        cellbox = AggregatedCellBox(boundary, {}, "0")
        cellbox.agg_data = {"elevation": 10.0}  # Above sea level
        
        access = ship.model_accessibility(cellbox)
        
        assert access["land"] is True
        assert access["inaccessible"] is True
    
    def test_ship_accessibility_extreme_ice(self, ship):
        """Test that ship detects extreme ice."""
        boundary = Boundary([-85, -84.9], [-135, -134.9], ["1970-01-01", "2021-12-31"])
        cellbox = AggregatedCellBox(boundary, {}, "0")
        cellbox.agg_data = {"elevation": -100.0, "SIC": 90.0}
        
        access = ship.model_accessibility(cellbox)
        
        assert access["ext_ice"] is True
        assert access["inaccessible"] is True


class TestGlider:
    """Test generic Glider vessel class."""
    
    @pytest.fixture
    def glider_config(self):
        """Configuration for Slocum-like glider."""
        return {
            "vessel_class": "glider",
            "max_speed": 1.25,
            "unit": "km/hr",
            "max_ice_conc": 10,
            "min_depth": 10,
            "num_directions": 8,
            "consumption_model": {
                "type": "polynomial_battery",
                "params": {
                    "speed_coeffs": [4.44444444, -0.5555555499999991],
                    "depth_coeffs": [0.001, 2]
                }
            }
        }
    
    @pytest.fixture
    def glider(self, glider_config):
        """Create glider instance."""
        return Glider(glider_config)
    
    def test_glider_model_performance_returns_battery(self, glider):
        """Test that glider returns battery consumption."""
        boundary = Boundary([-85, -84.9], [-135, -134.9], ["1970-01-01", "2021-12-31"])
        cellbox = AggregatedCellBox(boundary, {}, "0")
        cellbox.agg_data = {"elevation": -50.0, "speed": 1.25}
        
        performance = glider.model_performance(cellbox)
        
        assert "speed" in performance
        assert "battery" in performance
        assert len(performance["battery"]) == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
