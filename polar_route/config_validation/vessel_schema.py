"""
Vessel configuration schema for model-based vessel performance system.

This schema validates vessel configuration files that specify vessel class,
resistance models, consumption models, and physical parameters with units.
"""

from polar_route.vessel_performance.models import ModelRegistry

# Get registered model types for validation
def _get_registered_models():
    """Get list of registered model types for schema validation."""
    try:
        return ModelRegistry.get_registered_models()
    except Exception:
        # If models not yet registered, return empty list
        # (will be populated after imports complete)
        return []

# Resistance model parameter schemas with unit documentation
_resistance_model_schemas = {
    "ice_froude": {
        "type": "object",
        "required": ["k", "b", "n", "beam", "force_limit"],
        "properties": {
            "k": {
                "type": "number",
                "description": "Hull coefficient [dimensionless]"
            },
            "b": {
                "type": "number",
                "description": "Froude number exponent [dimensionless]"
            },
            "n": {
                "type": "number",
                "description": "Ice concentration exponent [dimensionless]"
            },
            "beam": {
                "type": "number",
                "minimum": 0,
                "description": "Vessel beam width [m]"
            },
            "force_limit": {
                "type": "number",
                "minimum": 0,
                "description": "Maximum allowable resistance force [N]"
            },
            "gravity": {
                "type": "number",
                "minimum": 0,
                "default": 9.81,
                "description": "Gravitational acceleration [m/s²]"
            }
        }
    },
    "wind_drag": {
        "type": "object",
        "required": ["frontal_area", "angles", "coefficients"],
        "properties": {
            "frontal_area": {
                "type": "number",
                "minimum": 0,
                "description": "Vessel frontal area exposed to wind [m²]"
            },
            "angles": {
                "type": "array",
                "items": {"type": "number"},
                "description": "Wind angle breakpoints [degrees], e.g., [0, 30, 60, 90, 120, 150, 180]"
            },
            "coefficients": {
                "type": "array",
                "items": {"type": "number"},
                "description": "Drag coefficients at each angle [dimensionless]"
            },
            "interpolation": {
                "type": "string",
                "enum": ["linear", "cubic", "spline"],
                "default": "linear",
                "description": "Interpolation method between angle breakpoints"
            },
            "air_density": {
                "type": "number",
                "minimum": 0,
                "default": 1.225,
                "description": "Air density [kg/m³]"
            }
        }
    },
    "wave_kreitner": {
        "type": "object",
        "required": ["beam", "length"],
        "properties": {
            "beam": {
                "type": "number",
                "minimum": 0,
                "description": "Vessel beam width [m]"
            },
            "length": {
                "type": "number",
                "minimum": 0,
                "description": "Vessel length [m]"
            },
            "c_block": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "default": 0.75,
                "description": "Block coefficient (ratio of underwater volume to cuboid) [dimensionless]"
            },
            "rho_water": {
                "type": "number",
                "minimum": 0,
                "default": 9807,
                "description": "Specific weight of water [N/m³], default 9807 for freshwater at 4°C"
            }
        }
    }
}

# Consumption model parameter schemas with unit documentation
_consumption_model_schemas = {
    "polynomial_fuel": {
        "type": "object",
        "required": ["speed_coeffs", "resistance_coeffs"],
        "properties": {
            "speed_coeffs": {
                "type": "array",
                "items": {"type": "number"},
                "minItems": 3,
                "maxItems": 3,
                "description": "Speed polynomial coefficients [c_s2, c_s1, c_s0] where fuel includes c_s2*v² + c_s1*v + c_s0. Units: [tons/day per (km/h)², tons/day per km/h, tons/day]"
            },
            "resistance_coeffs": {
                "type": "array",
                "items": {"type": "number"},
                "minItems": 2,
                "maxItems": 2,
                "description": "Resistance polynomial coefficients [c_r2, c_r1] where fuel includes c_r2*R² + c_r1*R. Units: [tons/day per N², tons/day per N]"
            }
        }
    },
    "polynomial_battery": {
        "type": "object",
        "required": ["speed_coeffs", "depth_coeffs"],
        "properties": {
            "speed_coeffs": {
                "type": "array",
                "items": {"type": "number"},
                "description": "Speed polynomial coefficients [c_n, ..., c_1, c_0] (numpy poly1d format). Units: [Ah/day per (km/h)^n] or [W per (km/h)^n]"
            },
            "depth_coeffs": {
                "type": "array",
                "items": {"type": "number"},
                "description": "Depth polynomial coefficients [c_n, ..., c_1, c_0] (numpy poly1d format). Units: [Ah/day per m^n] or [W per m^n]"
            }
        }
    },
    "constant_consumption": {
        "type": "object",
        "required": ["rate"],
        "properties": {
            "rate": {
                "type": "number",
                "minimum": 0,
                "description": "Fixed consumption rate. Units: [tons/day] for fuel, [Ah/day] or [W] for battery"
            }
        }
    }
}

vessel_schema = {
    "type": "object",
    "required": ["vessel_class", "max_speed", "unit", "consumption_model"],
    "additionalProperties": False,
    "properties": {
        "vessel_class": {
            "type": "string",
            "enum": ["ship", "glider", "auv", "aircraft"],
            "description": "Type of vessel: ship (surface), glider/auv (underwater), aircraft (airborne)"
        },
        "max_speed": {
            "type": "number",
            "minimum": 0,
            "description": "Maximum vessel speed [km/h]"
        },
        "unit": {
            "type": "string",
            "description": "Speed unit (should be 'km/hr')"
        },
        "max_ice_conc": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "description": "Maximum ice concentration accessible [%]"
        },
        "min_depth": {
            "type": "number",
            "minimum": 0,
            "description": "Minimum water depth required [m]"
        },
        "max_wave": {
            "type": "number",
            "minimum": 0,
            "description": "Maximum wave height accessible [m]"
        },
        "num_directions": {
            "type": "integer",
            "minimum": 4,
            "default": 8,
            "description": "Number of compass directions to model (e.g., 4, 8, 16, 32). More directions increase computational cost."
        },
        "resistance_models": {
            "type": "array",
            "description": "List of resistance models to apply (forces sum linearly)",
            "items": {
                "type": "object",
                "required": ["type", "params"],
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "Registered resistance model name (e.g., 'ice_froude', 'wind_drag', 'wave_kreitner')"
                    },
                    "params": {
                        "type": "object",
                        "description": "Model-specific parameters with units (see model documentation)"
                    }
                }
            }
        },
        "consumption_model": {
            "type": "object",
            "required": ["type", "params"],
            "description": "Fuel or battery consumption model",
            "properties": {
                "type": {
                    "type": "string",
                    "description": "Registered consumption model name (e.g., 'polynomial_fuel', 'polynomial_battery', 'constant_consumption')"
                },
                "params": {
                    "type": "object",
                    "description": "Model-specific parameters with units (see model documentation)"
                }
            }
        },
        "speed_adjustment": {
            "type": "object",
            "description": "Optional wind-based speed adjustment thresholds (for SDA_wind-style behaviour)",
            "properties": {
                "wind_threshold_low": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Lower wind resistance threshold as fraction of force_limit [dimensionless]"
                },
                "wind_threshold_high": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Upper wind resistance threshold as fraction of force_limit [dimensionless]"
                },
                "speed_factor_low": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Speed reduction factor for high wind resistance [dimensionless]"
                },
                "tailwind_factor": {
                    "type": "number",
                    "minimum": 1,
                    "description": "Multiplier for tailwind speed boost calculation [dimensionless]"
                }
            }
        },
        "excluded_zones": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of zone names to exclude from routing"
        },
        "neighbour_splitting": {
            "type": "boolean",
            "description": "Enable splitting of cell neighbours"
        }
    }
}
