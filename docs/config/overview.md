# Configuration Overview

In this section we will outline the standard structure for a configuration file used in 
all portions of the PolarRoute software package.

Each stage of the route-planning process is configured by a separate configuration file. 
The configuration files are written in JSON, and are passed to each stage of the 
route-planning process as command-line arguments or through a Python script.

Example configuration files are provided in the `config` directory of [the repository](https://github.com/bas-amop/PolarRoute/tree/main/examples).

The format of the config used to generate an environmental mesh can be found in the [Configuration - Mesh Construction](https://bas-amop.github.io/MeshiPhi/html/sections/Configuration/Mesh_construction_config.html) section of the [MeshiPhi documentation](https://bas-amop.github.io/MeshiPhi/).

Descriptions of the configuration options for the Vessel Performance Modelling can 
be found in the [Configuration - Vessel Performance Modeller](vessel_performance.md) section of the 
documentation.

Descriptions of the configuration options for Route Planning can be found in the 
[Configuration - Route Planning](route_planning.md) section of the documentation.
