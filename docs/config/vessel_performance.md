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
      "type": "ice_froude",
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
      "type": "wind_drag",
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

* **`num_directions`** *(int)* - Number of discrete heading directions for route planning (typically 8 or 16).

* **`resistance_models`** *(array)* - Array of resistance model configurations. Can be empty `[]` for simple vessels. Each model has:
  - `type` *(string)* - Model identifier (see [Resistance Models](#resistance-models))
  - `params` *(object)* - Model-specific parameters (see [Model Parameters](#model-parameters))

* **`consumption_model`** *(object)* - Fuel/battery consumption configuration:
  - `type` *(string)* - Model identifier (see [Consumption Models](#consumption-models))
  - `params` *(object)* - Model-specific parameters (see [Model Parameters](#model-parameters))

### Optional Parameters

* **`max_depth`** *(float)* - Maximum operating depth (m). Required for gliders and AUVs.

* **`max_wave`** *(float)* - Maximum significant wave height (m) the vessel can operate in.

* **`excluded_zones`** *(array of strings)* - List of mesh cell property names. Cells with `True` values for any listed property are marked inaccessible.

* **`neighbour_splitting`** *(bool)* - Enable splitting of accessible cells neighboring inaccessible cells. Improves routing accuracy but increases computation time. Default: `true`.

## Resistance Models

Resistance models calculate forces opposing vessel motion. Multiple resistance models can be combined - the total resistance is the sum of all configured models.

### Ice Froude Resistance (`ice_froude`)

Models ice resistance using Froude number scaling:

$$ R_{ice} = k \cdot \text{Fr}^n \cdot \rho_{water} \cdot g \cdot beam^b $$

where $\text{Fr} = \frac{v}{\sqrt{g \cdot beam}}$ is the Froude number.

**Parameters:**
- `k` *(float)* - Dimensionless scaling coefficient
- `b` *(float)* - Dimensionless beam exponent (typically negative)
- `n` *(float)* - Dimensionless Froude number exponent
- `beam` *(float)* - Vessel beam/width in meters [m]
- `force_limit` *(float)* - Maximum allowable resistance in Newtons [N]
- `gravity` *(float, optional)* - Gravitational acceleration [m/s²]. Default: 9.81
- `rho_water` *(float, optional)* - Water density factor [N/m³]. Default: 9807

**Example:**
```json
{
  "type": "ice_froude",
  "params": {
    "k": 4.4,
    "b": -0.8267,
    "n": 2.0,
    "beam": 24.0,
    "force_limit": 96634.5
  }
}
```

### Wind Drag Resistance (`wind_drag`)

Models resistance from wind based on apparent wind angle and vessel frontal area.

**Parameters:**
- `frontal_area` *(float)* - Vessel frontal area exposed to wind [m²]
- `air_density` *(float, optional)* - Air density [kg/m³]. Default: 1.225
- `interpolation` *(string, optional)* - Method for interpolating drag coefficients: `"linear"`, `"cubic"`, or `"spline"`. Default: `"linear"`
- `angles` *(array of floats)* - Wind angles in degrees [0-180], where 0° is head wind
- `coefficients` *(array of floats)* - Drag coefficients (dimensionless) corresponding to each angle

**Example:**
```json
{
  "type": "wind_drag",
  "params": {
    "frontal_area": 750.0,
    "interpolation": "linear",
    "angles": [0, 30, 60, 90, 120, 150, 180],
    "coefficients": [0.94, 0.77, 0.42, 0.48, 0.17, -0.30, -0.34]
  }
}
```

### Wave Resistance (`wave_kreitner`)

Models wave resistance using the Kreitner formulation.

**Parameters:**
- `beam` *(float)* - Vessel beam/width [m]
- `length` *(float)* - Vessel length [m]
- `c_block` *(float)* - Block coefficient (dimensionless, typically 0.5-0.9)
- `rho_water` *(float, optional)* - Water density factor [N/m³]. Default: 9807

**Example:**
```json
{
  "type": "wave_kreitner",
  "params": {
    "beam": 24.0,
    "length": 128.0,
    "c_block": 0.7
  }
}
```

## Consumption Models

Consumption models calculate fuel or battery usage based on vessel operating conditions.

### Polynomial Fuel Model (`polynomial_fuel`)

Calculates fuel consumption using polynomial functions of speed and resistance:

$$ C = \sum_{i} a_i \cdot v^i + \sum_{j} b_j \cdot R^j $$

**Parameters:**
- `speed_coeffs` *(array of floats)* - Polynomial coefficients for speed terms [tons/day, tons·hr/day·km, tons·hr²/day·km², ...]
- `resistance_coeffs` *(array of floats)* - Polynomial coefficients for resistance terms [tons/day·N, tons/day·N², ...]

**Example:**
```json
{
  "type": "polynomial_fuel",
  "params": {
    "speed_coeffs": [0.00137247, -0.0029601, 0.25290433],
    "resistance_coeffs": [7.75218178e-11, 6.48113363e-06]
  }
}
```

### Polynomial Battery Model (`polynomial_battery`)

Calculates battery consumption for underwater vehicles using speed and depth polynomials:

$$ C = \sum_{i} a_i \cdot v^i + \sum_{j} b_j \cdot d^j $$

**Parameters:**
- `speed_coeffs` *(array of floats)* - Polynomial coefficients for speed terms [1/day, hr/day·km, hr²/day·km², ...]
- `depth_coeffs` *(array of floats)* - Polynomial coefficients for depth terms [1/day·m, 1/day·m², ...]

**Example:**
```json
{
  "type": "polynomial_battery",
  "params": {
    "speed_coeffs": [0.0, 0.0, 0.0416],
    "depth_coeffs": [0.0, 0.0]
  }
}
```

### Constant Consumption Model (`constant_consumption`)

Simple fixed-rate consumption, independent of operating conditions.

**Parameters:**
- `consumption_rate` *(float)* - Fixed consumption rate per day [tons/day or dimensionless]

**Example:**
```json
{
  "type": "constant_consumption",
  "params": {
    "consumption_rate": 0.01
  }
}
```

## Complete Examples

### Research Icebreaker

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
      "type": "ice_froude",
      "params": {
        "k": 4.4,
        "b": -0.8267,
        "n": 2.0,
        "beam": 24.0,
        "force_limit": 96634.5
      }
    },
    {
      "type": "wind_drag",
      "params": {
        "frontal_area": 750.0,
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
  }
}
```

### Underwater Glider

```json
{
  "vessel_class": "glider",
  "max_speed": 0.8,
  "unit": "km/hr",
  "max_ice_conc": 80,
  "min_depth": 10,
  "max_depth": 200,
  "num_directions": 8,
  "resistance_models": [],
  "consumption_model": {
    "type": "polynomial_battery",
    "params": {
      "speed_coeffs": [0.0, 0.0, 0.0416],
      "depth_coeffs": [0.0, 0.0]
    }
  }
}
```

### Autonomous Underwater Vehicle

```json
{
  "vessel_class": "auv",
  "max_speed": 7.2,
  "unit": "km/hr",
  "max_ice_conc": 100,
  "min_depth": 10,
  "max_depth": 6000,
  "num_directions": 8,
  "resistance_models": [],
  "consumption_model": {
    "type": "constant_consumption",
    "params": {
      "consumption_rate": 0.01
    }
  }
}
```

## See Also

- [Vessel Gallery](vessel_gallery.md) - Ready-to-use configurations for common vessels
- [Resistance Models Theory](../methods/resistance_models.md) - Mathematical background
- [Model Parameters Reference](../reference/model_parameters.md) - Complete parameter listing
