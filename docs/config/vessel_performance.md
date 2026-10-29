# Vessel Performance Configuration

The vessel configuration file provides all necessary information about a vessel's characteristics and performance models. This configuration is used by the `VesselPerformanceModeller` class to calculate performance parameters (e.g., speed, fuel consumption) and is required as a command-line argument for the `add_vehicle` entry point.

## Configuration Structure

```json
{
  "vessel_class": "ship",
  "max_speed": 26.5,
  "unit": "km/hr",
  "max_ice_conc": 80,
  "min_depth": 10,
  "num_directions": 8,
  "resistance_models": [
    {
      "type": "ice_resistance",
      "params": {
        "k": 4.4,
        "b": -0.8267,
        "n": 2.0,
        "beam": 24.0,
        "force_limit": 96634.5,
        "gravity": 9.81
      }
    },
    {
      "type": "wind_resistance",
      "params": {
        "frontal_area": 750.0,
        "air_density": 1.225,
        "interpolation": "linear",
        "angles": [0, 30, 60, 90, 120, 150, 180],
        "coefficients": [0.94, 0.77, 0.42, 0.48, 0.17, -0.30, -0.34]
      }
    }
  ],
  "consumption_model": {
    "type": "polynomial_fuel",
    "params": {
      "speed_coeffs": [0.00137247, -0.0029601, 0.25290433],
      "resistance_coeffs": [7.75218178e-11, 6.48113363e-06]
    }
  },
  "max_wave": 3,
  "excluded_zones": ["exclusion_zone"],
  "neighbour_splitting": true
}
```

## Core Parameters

### Required Parameters

* **`vessel_class`** *(string)* - The class of vessel. Must be one of:
  - `"ship"` - Surface vessels (icebreakers, research ships, cargo vessels)
  - `"glider"` - Underwater gliders
  - `"auv"` - Autonomous Underwater Vehicles
  - `"aircraft"` - Aircraft and UAVs

* **`max_speed`** *(float)* - Maximum speed of the vessel in open water conditions.

* **`unit`** *(string)* - Units for speed measurement. Currently only `"km/hr"` is supported.

* **`max_ice_conc`** *(float)* - Maximum sea ice concentration (%) the vessel can navigate through.

* **`min_depth`** *(float)* - Minimum water depth (m) required for vessel operation.

* **`num_directions`** *(int)* - Number of discrete heading directions. Must be `8`, matching the mesh neighbour directions used by the route planner. Default: `8`.

* **`resistance_models`** *(array)* - Array of resistance model configurations. Can be empty `[]` for simple vessels. Each model has:
  - `type` *(string)* - Model identifier (see [Available Models](#available-models))
  - `params` *(object)* - Model-specific parameters (see the [Model Parameters Reference](../reference/model_parameters.md))

* **`consumption_model`** *(object)* - Fuel/battery consumption configuration:
  - `type` *(string)* - Model identifier (see [Available Models](#available-models))
  - `params` *(object)* - Model-specific parameters (see the [Model Parameters Reference](../reference/model_parameters.md))

### Optional Parameters

* **`max_dive_depth`** *(float)* - Gliders only. Operating depth (m) at which battery use is capped, assuming yo-yo dives. Default: `1000`.

* **`max_altitude`** *(float)* - Aircraft only. Cells with elevation (m) above this are marked inaccessible. Replaces the legacy `max_elevation`.

* **`max_wave`** *(float)* - Maximum significant wave height (m) the vessel can operate in.

* **`excluded_zones`** *(array of strings)* - List of mesh cell property names. Cells with `True` values for any listed property are marked inaccessible.

* **`speed_adjustment`** *(object)* - Ships only. Reduces speed per heading according to wind resistance, as in the legacy `SDAWind` vessel. Thresholds are fractions of the `ice_resistance` model's `force_limit`, so an `ice_resistance` model is required. Keys:
  - `wind_threshold_low` *(float, 0-1)* - Headwind resistance below `wind_threshold_low × force_limit` scales speed by `1 - R_wind / force_limit`; at or above it, speed is multiplied by `speed_factor_low`. Default: `0.75`.
  - `speed_factor_low` *(float, 0-1)* - Speed multiplier for strong headwinds. Default: `0.25`.
  - `tailwind_factor` *(float, ≥1)* - Tailwinds (negative wind resistance) scale speed by `1 - R_wind / (tailwind_factor × force_limit)`. Default: `10`.

* **`neighbour_splitting`** *(bool)* - Enable splitting of accessible cells neighboring inaccessible cells. Improves routing accuracy but increases computation time. Default: `true`.

## Available Models

Models are referenced by their `type` string and configured via `params`. A vessel
may combine several resistance models (their forces are summed) and must specify a
single consumption model.

**Resistance models**

- `ice_resistance` – ice resistance from Froude-number scaling
- `wind_resistance` – wind resistance from apparent wind angle and frontal area
- `wave_resistance` – wave resistance from the Kreitner formulation

**Consumption models**

- `polynomial_fuel` – fuel use as a polynomial of speed and resistance
- `polynomial_battery` – battery use as a polynomial of speed and depth
- `constant_consumption` – fixed rate independent of conditions

See the [Model Parameters Reference](../reference/model_parameters.md) for the full
parameter list, units, defaults and worked `params` examples, and
[Resistance Models Theory](../methods/resistance_models.md) for the underlying
equations. Ready-to-use whole-vessel configurations are in the
[Vessel Gallery](vessel_gallery.md).

## See Also

- [Vessel Gallery](vessel_gallery.md) - Ready-to-use configurations for common vessels
- [Resistance Models Theory](../methods/resistance_models.md) - Mathematical background
- [Model Parameters Reference](../reference/model_parameters.md) - Complete parameter listing
