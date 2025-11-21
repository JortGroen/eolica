# eolica

A Python tool for wind farm simulation and energy output forecasting, built on top of [py_wake](https://github.com/DTUWindEnergy/PyWake), an open-source wind turbine wake simulation framework.

## Overview

Eolica enables comprehensive wind farm analysis including:
- **Wind farm simulation**: Simulate power output of wind farms using wake models (e.g., Bastankhah-Porte-Agel 2014)
- **Energy forecasting**: Forecast energy production based on wind speed and direction time series
- **Visualization**: Generate wind roses, Weibull distributions, turbine power curves, and interactive maps
- **Validation**: Compare simulation results against actual production data

## Installation

### Prerequisites

- Python >=3.12 (3.13 recommended)
- [uv](https://github.com/astral-sh/uv) package manager

### Install uv

If you don't have `uv` installed, you can install it using:

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### Install eolica

Clone the repository and install dependencies:

```bash
git clone https://gitlab-intern.ait.ac.at/duenserm/eolica.git
cd eolica
uv sync
```

This will:
- Create a virtual environment (if needed)
- Install all dependencies from `pyproject.toml` and `uv.lock`
- Install the package in editable mode

### Run with uv

To run scripts using the installed environment:

```bash
uv run python eolica.py
```

Or activate the virtual environment:

```bash
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

## Key Components

- **`EolicaPark`**: Represents a wind farm configuration with turbine locations, types, and site characteristics
- **`EolicaSimulation`**: Performs wake simulations using py_wake models
- **`EolicaDataset`**: Handles input wind data (time series) and production data for validation

## Usage

### Configuration Files

Eolica uses YAML configuration files:

- **Park configuration** (`parks/*.yaml`): Defines turbine locations, types, and site parameters
- **Simulation configuration** (`simulations/*.yaml`): Specifies simulation parameters, input data sources, and model settings

### Basic Workflow

```python
from eolica import EolicaPark, EolicaSimulation, EolicaDataset

# Load wind farm configuration
park = EolicaPark('parks/hollern.yaml')

# Generate visualizations
park.plot_weibull_dists()
park.plot_windrose()
park.plot_turbines_powerCT()

# Create simulation
simulation = EolicaSimulation(park, config_fn='simulations/hollern_2020to2024.yaml')

# Load input dataset
dataset_input = EolicaDataset('simulations/hollern_2020to2024.yaml')

# Run simulation
sim_res = simulation.simulate_wind_timeseries(dataset_input)

# Compare with production data
dataset_prod = EolicaDataset('simulations/hollern_2020to2024.yaml', type='production')
simulation.compare_to_production(dataset_prod)
```

## Docker

Build the Docker image:

```bash
docker build -t my-eolica .
```

Verify the image:

```bash
docker images
```

Run the container:

```bash
docker run my-eolica
```

## Requirements

- Python >=3.12
- Dependencies managed via `uv` (see `pyproject.toml`)

## Author

marc.duenser@ait.ac.at
