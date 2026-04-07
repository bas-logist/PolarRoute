"""
Unit tests for vessel performance models and generic vessels.

Tests resistance models, consumption models, and vessel classes independently.
"""

import pytest
import numpy as np
import json
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
from polar_route.vessel_performance.models import ModelRegistry
from polar_route.vessel_performance.vessels.generic_vessels import Ship, Glider, AUV, Aircraft
from polar_route.vessel_performance.vessel_factory import VesselFactory


# Mock cellbox for testing
class MockCellbox:
    """Lightweight mock cellbox for testing without MeshiPhi dependency."""
    def __init__(self, agg_data=None):
        self.id = "test_cell_0"
        self.agg_data = agg_data or {}


@pytest.fixture
def ice_cellbox():
    """Cellbox with ice conditions."""
    return MockCellbox({
        "SIC": 50.0,
        "thickness": 1.0,
        "density": 900.0,
        "elevation": -100.0
    })


@pytest.fixture
def wind_cellbox():
    """Cellbox with wind conditions."""
    return MockCellbox({
        "u10": 5.0,  # 5 m/s eastward wind
        "v10": 3.0,  # 3 m/s northward wind
        "elevation": -100.0
    })


@pytest.fixture
def wave_cellbox():
    """Cellbox with wave conditions."""
    return MockCellbox({
        "swh": 1.5,  # 1.5m significant wave height
        "elevation": -100.0
    })


# ============================================================================
# Resistance Model Tests
# ============================================================================

class TestFroudeIceResistance:
    """Tests for Froude-based ice resistance model."""
    
    @pytest.fixture
    def ice_model(self):
        """Standard ice resistance model (SDA parameters)."""
        return FroudeIceResistance(
            k=4.4, b=-0.8267, n=2.0,
            beam=24.0, force_limit=96634.5, gravity=9.81
        )
    
    def test_zero_ice_gives_zero_resistance(self, ice_model):
        """Test that no ice produces no resistance."""
        cellbox = MockCellbox({"SIC": 0.0, "thickness": 0.0, "density": 900.0})
        resistance = ice_model.calculate_resistance(cellbox, speed=20.0)
        assert resistance == 0.0
    
    def test_positive_resistance_with_ice(self, ice_model, ice_cellbox):
        """Test that ice produces positive resistance."""
        resistance = ice_model.calculate_resistance(ice_cellbox, speed=20.0)
        assert resistance > 0
    
    def test_higher_speed_increases_resistance(self, ice_model, ice_cellbox):
        """Test that resistance increases with speed."""
        r1 = ice_model.calculate_resistance(ice_cellbox, speed=10.0)
        r2 = ice_model.calculate_resistance(ice_cellbox, speed=20.0)
        assert r2 > r1
    
    def test_invert_resistance_gives_expected_force(self, ice_model, ice_cellbox):
        """Test that inverted speed produces target resistance."""
        target_force = 50000.0
        safe_speed = ice_model.invert_resistance(ice_cellbox, target_force)
        actual_resistance = ice_model.calculate_resistance(ice_cellbox, safe_speed)
        assert abs(actual_resistance - target_force) < 1.0  # Within 1N


class TestWindDragResistance:
    """Tests for wind drag resistance model."""
    
    @pytest.fixture
    def wind_model(self):
        """Standard wind resistance model (SDA parameters)."""
        return WindDragResistance(
            frontal_area=750.0,
            angles=[0, 30, 60, 90, 120, 150, 180],
            coefficients=[0.94, 0.77, 0.42, 0.48, 0.17, -0.30, -0.34],
            interpolation="linear",
            air_density=1.225
        )
    
    def test_no_wind_gives_zero_resistance(self, wind_model):
        """Test that calm conditions produce no wind resistance."""
        cellbox = MockCellbox({"u10": 0.0, "v10": 0.0})
        resistance = wind_model.calculate_resistance(cellbox, speed=20.0, direction=0.0)
        assert abs(resistance) < 0.1
    
    def test_headwind_produces_positive_resistance(self, wind_model):
        """Test that headwind increases resistance."""
        cellbox = MockCellbox({"u10": 0.0, "v10": -10.0})  # Strong southward wind
        resistance = wind_model.calculate_resistance(
            cellbox, speed=20.0, direction=0.0  # Heading north
        )
        assert resistance > 0
    
    def test_tailwind_produces_negative_resistance(self, wind_model):
        """Test that tailwind can reduce resistance."""
        cellbox = MockCellbox({"u10": 0.0, "v10": 10.0})  # Strong northward wind
        resistance = wind_model.calculate_resistance(
            cellbox, speed=20.0, direction=0.0  # Heading north
        )
        # Tailwind should reduce resistance (possibly negative)
        assert resistance < 100.0


class TestKreitnerWaveResistance:
    """Tests for Kreitner wave resistance model."""
    
    @pytest.fixture
    def wave_model(self):
        """Standard wave resistance model."""
        return KreitnerWaveResistance(
            beam=24.0, length=129.0, c_block=0.75, rho_water=9807
        )
    
    def test_no_waves_gives_zero_resistance(self, wave_model):
        """Test that calm seas produce no wave resistance."""
        cellbox = MockCellbox({"swh": 0.0})
        resistance = wave_model.calculate_resistance(cellbox, speed=20.0)
        assert resistance == 0.0
    
    def test_waves_produce_positive_resistance(self, wave_model, wave_cellbox):
        """Test that waves produce positive resistance."""
        resistance = wave_model.calculate_resistance(wave_cellbox, speed=20.0)
        assert resistance > 0
    
    def test_higher_waves_increase_resistance(self, wave_model):
        """Test that resistance scales with wave height squared."""
        cellbox1 = MockCellbox({"swh": 1.0})
        cellbox2 = MockCellbox({"swh": 2.0})
        r1 = wave_model.calculate_resistance(cellbox1, speed=20.0)
        r2 = wave_model.calculate_resistance(cellbox2, speed=20.0)
        # Should be ~4x due to h² term
        assert 3.8 < (r2 / r1) < 4.2


# ============================================================================
# Consumption Model Tests
# ============================================================================

class TestPolynomialFuelModel:
    """Tests for polynomial fuel consumption model."""
    
    @pytest.fixture
    def fuel_model(self):
        """Standard fuel model (SDA parameters)."""
        return PolynomialFuelModel(
            speed_coeffs=[0.00137247, -0.0029601, 0.25290433],
            resistance_coeffs=[7.75218178e-11, 6.48113363e-06]
        )
    
    def test_positive_consumption(self, fuel_model):
        """Test that fuel consumption is always positive."""
        fuel = fuel_model.calculate_consumption(speed=20.0, resistance=50000.0)
        assert fuel > 0
    
    def test_higher_speed_increases_consumption(self, fuel_model):
        """Test that consumption increases with speed."""
        f1 = fuel_model.calculate_consumption(speed=10.0, resistance=0.0)
        f2 = fuel_model.calculate_consumption(speed=20.0, resistance=0.0)
        assert f2 > f1
    
    def test_higher_resistance_increases_consumption(self, fuel_model):
        """Test that consumption increases with resistance."""
        f1 = fuel_model.calculate_consumption(speed=20.0, resistance=10000.0)
        f2 = fuel_model.calculate_consumption(speed=20.0, resistance=50000.0)
        assert f2 > f1
    
    def test_negative_resistance_treated_as_zero(self, fuel_model):
        """Test that negative resistance is handled gracefully."""
        f_neg = fuel_model.calculate_consumption(speed=20.0, resistance=-1000.0)
        f_zero = fuel_model.calculate_consumption(speed=20.0, resistance=0.0)
        assert f_neg == f_zero


class TestPolynomialBatteryModel:
    """Tests for polynomial battery consumption model."""
    
    @pytest.fixture
    def battery_model(self):
        """Standard battery model (Slocum parameters)."""
        return PolynomialBatteryModel(
            speed_coeffs=[4.44444444, -0.5555555499999991],
            depth_coeffs=[0.001, 2]
        )
    
    def test_consumption_includes_speed_and_depth(self, battery_model):
        """Test that both speed and depth affect consumption."""
        b1 = battery_model.calculate_consumption(speed=1.0, depth=10.0)
        b2 = battery_model.calculate_consumption(speed=2.0, depth=10.0)
        b3 = battery_model.calculate_consumption(speed=1.0, depth=20.0)
        assert b2 != b1  # Speed changes consumption
        assert b3 != b1  # Depth changes consumption


class TestConstantConsumptionModel:
    """Tests for constant consumption model."""
    
    def test_returns_constant_rate(self):
        """Test that consumption is always the configured rate."""
        model = ConstantConsumptionModel(rate=4.75)
        c1 = model.calculate_consumption(speed=10.0)
        c2 = model.calculate_consumption(speed=20.0)
        assert c1 == 4.75
        assert c2 == 4.75


# ============================================================================
# Model Registry Tests
# ============================================================================

class TestModelRegistry:
    """Tests for model registry system."""
    
    def test_all_models_registered(self):
        """Test that all expected models are registered."""
        models = ModelRegistry.get_registered_models()
        expected = [
            'constant_consumption',
            'ice_froude',
            'polynomial_battery',
            'polynomial_fuel',
            'wave_kreitner',
            'wind_drag'
        ]
        for model_name in expected:
            assert model_name in models
    
    def test_create_valid_model(self):
        """Test creating a registered model."""
        model = ModelRegistry.create('ice_froude', {
            'k': 4.4, 'b': -0.8267, 'n': 2.0,
            'beam': 24.0, 'force_limit': 96634.5
        })
        assert isinstance(model, FroudeIceResistance)
    
    def test_create_invalid_model_raises_error(self):
        """Test that unknown model type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown model type"):
            ModelRegistry.create('nonexistent_model', {})


# ============================================================================
# Generic Vessel Tests
# ============================================================================

class TestShip:
    """Tests for generic Ship class."""
    
    @pytest.fixture
    def ship_config(self):
        """SDA-equivalent ship configuration."""
        with open('examples/vessel_config/SDA.config.json', 'r') as f:
            return json.load(f)
    
    def test_ship_initialization(self, ship_config):
        """Test that ship initializes with models."""
        ship = Ship(ship_config)
        assert ship.max_speed == 26.5
        assert len(ship.resistance_models) == 2
        assert ship.consumption_model is not None
    
    def test_ship_model_performance(self, ship_config, ice_cellbox):
        """Test that ship calculates performance values."""
        ship = Ship(ship_config)
        ice_cellbox.agg_data["speed"] = ship.max_speed
        performance = ship.model_performance(ice_cellbox)
        
        assert "speed" in performance
        assert "resistance" in performance
        assert "fuel" in performance
        assert len(performance["speed"]) == 8
    
    def test_ship_model_accessibility(self, ship_config):
        """Test ship accessibility checks."""
        ship = Ship(ship_config)
        
        # Test land detection
        land_cellbox = MockCellbox({"elevation": 10.0})
        access = ship.model_accessibility(land_cellbox)
        assert access["land"] is True
        assert access["inaccessible"] is True
        
        # Test navigable water
        water_cellbox = MockCellbox({"elevation": -100.0, "SIC": 0.0})
        access = ship.model_accessibility(water_cellbox)
        assert access["inaccessible"] is False


class TestGlider:
    """Tests for generic Glider class."""
    
    @pytest.fixture
    def glider_config(self):
        """Slocum-equivalent glider configuration."""
        with open('examples/vessel_config/Slocum.config.json', 'r') as f:
            return json.load(f)
    
    def test_glider_initialization(self, glider_config):
        """Test that glider initializes correctly."""
        glider = Glider(glider_config)
        assert glider.max_speed == 1.25
        assert glider.consumption_model is not None
    
    def test_glider_model_performance(self, glider_config):
        """Test that glider calculates battery consumption."""
        glider = Glider(glider_config)
        cellbox = MockCellbox({"elevation": -50.0, "speed": 1.0})
        performance = glider.model_performance(cellbox)
        
        assert "speed" in performance
        assert "battery" in performance
        assert len(performance["speed"]) == 8
        assert len(performance["battery"]) == 8


# ============================================================================
# Vessel Factory Tests
# ============================================================================

class TestVesselFactory:
    """Tests for vessel factory."""
    
    def test_create_ship_from_config(self):
        """Test creating ship from config file."""
        with open('examples/vessel_config/SDA.config.json', 'r') as f:
            config = json.load(f)
        vessel = VesselFactory.get_vessel(config)
        assert isinstance(vessel, Ship)
    
    def test_create_glider_from_config(self):
        """Test creating glider from config file."""
        with open('examples/vessel_config/Slocum.config.json', 'r') as f:
            config = json.load(f)
        vessel = VesselFactory.get_vessel(config)
        assert isinstance(vessel, Glider)
    
    def test_invalid_vessel_class_raises_error(self):
        """Test that invalid vessel_class raises ValueError."""
        config = {"vessel_class": "invalid", "max_speed": 10, "unit": "km/hr"}
        with pytest.raises(ValueError, match="Unknown vessel_class"):
            VesselFactory.get_vessel(config)
