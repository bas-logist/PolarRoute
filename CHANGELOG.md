# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - YYYY-MM-DD

### Added
- Model Registry System: Plugin-based architecture for resistance and consumption models using `@register_model` decorator.
- Generic Vessel Classes: Ship, Glider, AUV, and Aircraft classes replacing hard-coded vessel types.
- Resistance Models: Three pluggable resistance models:
  - `ice_froude`: Froude number-based ice resistance with configurable k/b/n coefficients
  - `wind_drag`: Angle-dependent wind drag with interpolation options (linear/cubic/spline)
  - `wave_kreitner`: Kreitner wave resistance with beam/length/block coefficient parameters
- Consumption Models: Three pluggable consumption models:
  - `polynomial_fuel`: Speed and resistance-based fuel consumption with polynomial coefficients
  - `polynomial_battery`: Speed and depth-based battery consumption for underwater vehicles
  - `constant_consumption`: Fixed-rate consumption for simple vehicles
- Configuration Validation: Comprehensive JSON schema for vessel configurations with detailed parameter documentation including units.
- Documentation: 
  - Vessel configuration gallery with ready-to-use examples (`docs/config/vessel_gallery.md`)
  - Resistance models theory documentation (`docs/methods/resistance_models.md`)
  - Complete model parameters reference (`docs/reference/model_parameters.md`)
- Example Configurations: Updated vessel configs for SDA, SDA_wind, Slocum, and BoatyMcBoatFace using new format.
- Unit Tests: 27 comprehensive tests covering model registry, all resistance/consumption models, generic vessel classes, and factory.

### Changed
- Vessel Configuration Format: `vessel_type` replaced with `vessel_class` + explicit model specifications.
- Configuration Structure: All vessel-specific parameters (beam, force_limit, etc.) now explicitly defined in model params rather than top-level.
- VesselFactory: Simplified factory using VESSEL_CLASSES mapping instead of hard-coded requirements dictionary.
- Physical Constants: Now configurable per-vessel (gravity, air_density, rho_water) with sensible defaults.
- Model Composition: Vessels compose multiple resistance models; total resistance is sum of all active models.

### Removed
- Legacy Vessel Classes (BREAKING): Deleted 12 hard-coded vessel files:
  - `SDA.py`, `SDA_wind.py`, `example_ship.py` (ships)
  - `slocum.py` (gliders)
  - `boatymcboatface.py` (AUVs)
  - `twin_otter.py`, `windracer.py` (aircraft)
  - `abstract_ship.py`, `abstract_glider.py`, `abstract_alr.py`, `abstract_plane.py`, `abstract_uav.py` (abstract classes)
- Configuration Fields (BREAKING): 
  - `vessel_type` (replaced by `vessel_class`)
  - `hull_type` (slender/blunt distinction now encoded in k/b/n coefficients)
  - Top-level `beam`, `force_limit` (now in resistance model params)

### Migration

Quick migration:
1. Change `vessel_type: "SDA"` → `vessel_class: "ship"`
2. Remove `hull_type` field
3. Add `resistance_models` array with model configurations
4. Add `consumption_model` object with model configuration
5. Reference example configs in `examples/vessel_config/` or vessel gallery

## [1.1.9] - YYYY-MM-DD

### Added
- Convert docs from Sphinx to MkDocs (#321).
- Loosen MeshiPhi version strictness in requirements.
- Add Slocum and Boaty McBoatface vessel configs.
- Add module logger, replaces logging.*() calls (#331).
- Enable the running of pytest in the main directory (#260).
- Enable running of tests in parallel using pytest-xdist (#260).
- Add usage section to README.md (#321).
- Add CHANGELOG.md, CONTRIBUTING.md, CITATION.cff, Makefile.
- Linting with ruff.
- Pre-commit hooks which checks linting, along with other formatting issues.
- GitHub Actions test.yml.

### Changed
- Account for SIC values being None, rather than absent in various vessel performance models (#245).
- Parameterise repetitive tests (#260).
- Mark smoothing tests as slow, enable running "not slow" tests (#260).
- Consolidate add tests to dependency group, remove requirements.txt.
- Reduce the amount of duplicate filepaths by adding dynamic discovery of relevant files needed for the tests (#260).

[Unreleased]: https://github.com/bas-amop/PolarRoute/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/bas-amop/PolarRoute/releases/tag/v2.0.0
[1.1.9]: https://github.com/bas-amop/PolarRoute/releases/tag/v1.1.9
