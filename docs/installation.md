# Installation

In this section we will outline the necessary steps for installing the PolarRoute software package. Any installation of PolarRoute will also include [**MeshiPhi**](https://github.com/antarctica/MeshiPhi) - a package designed to
discretise the world from heterogeneous data sources. PolarRoute requires a pre-existing installation of Python 3.9 or higher.

## Installing PolarRoute

PolarRoute is available from PyPI and can be installed by running:

```sh
pip install polar-route
```

For development purposes you can install PolarRoute by downloading the source code from GitHub:

```sh
git clone https://github.com/bas-logist/PolarRoute
cd PolarRoute
pip install -e .
```

Use of `-e` is optional, depending on whether you want to be able to edit the installed copy of the package.

In order to run the test suite you will also need to include the `test` dependencies group:

```sh
pip install --group test
```

## Installing GeoPlot

Plotting functionality for the outputs of PolarRoute is provided by the [**GeoPlot**](https://github.com/antarctica/GeoPlot) package, also developed at BAS.

Geoplot is available from PyPI and can be installed by running: `pip install bas-geoplot`
