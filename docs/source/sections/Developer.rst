************
Installation
************

#########################
Testing
#########################
When updating any files within the PolarRoute repository, tests must be run to ensure that the core functionality of the software remains unchanged.

To allow for validation of changes, a suite of regression tests have been provided in the folder `tests/regression_tests/...`. These tests attempt to rebuild existing test cases using the changed code and compares these rebuilt outputs to the reference test files.


## Vessel Performance Modelling
| **Files altered**                | **Tests**                               |
|----------------------------------|-----------------------------------------|
| `abstract_vessel.py`             | `tests/regression_tests/test_vessel.py` |
| `vessel_factory.py`              |                                         |
| `vessel_performance_modeller.py` |                                         |
| `SDA.py`                         |                                         |
| `slocum.py`                      |                                         |
| `abstract_ship.py`               |                                         |
| `abstract_glider.py`             |                                         |
|                                  |                                         |



## Route Planning
| **Files altered**       | **Tests**                                        |
|-------------------------|--------------------------------------------------|
| `crossing.py`           | `tests/regression_tests/test_routes_dijkstra.py` |
| `crossing_smoothing.py` | `tests/regression_tests/test_routes_smoothed.py` |
| `route_planner.py`      |                                                  |
|                         |                                                  |


## Testing files
Some updates to PolarRoute may result in changes to meshes calculated in our tests suite (*such as adding additional attributes to the cellbox object*). These changes will cause the test suite to fail, though the mode of failure should be predictable. 

### Files

`tests/regression_tests/example_meshes/*` 
`tests/regression_tests/example_routes/*` 
