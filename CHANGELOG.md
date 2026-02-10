# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.9] - 2026-02-10

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
- GitHub Actions test.yml with GDAL installation and caching.

### Changed
- Account for SIC values being None, rather than absent in various vessel performance models (#245).
- Parameterise repetitive tests (#260).
- Mark smoothing tests as slow, enable running "not slow" tests (#260).
- Consolidate add tests to dependency group, remove requirements.txt.
- Reduce the amount of duplicate filepaths by adding dynamic discovery of relevant files needed for the tests (#260).

### Fixed
- Fix test failures on Python 3.14 caused by NumPy float64 type comparisons in vessel performance tests.

[Unreleased]: https://github.com/bas-amop/PolarRoute/compare/v1.1.9...HEAD
[1.1.9]: https://github.com/bas-amop/PolarRoute/releases/tag/v1.1.9
