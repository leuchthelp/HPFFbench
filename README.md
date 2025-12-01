# HFFBench

## Introduction

HFFBench stands for {H}igh-Performance {F}ile {F}ormat {Bench}mark. (Name is debatable)

It was developed for the   [DKRZ](https://www.dkrz.de/en) to evaluate the performance of different file format used in [High-Performance Computing (HPC)](https://www.nvidia.com/en-us/glossary/high-performance-computing/) like [NetCDF4](https://www.unidata.ucar.edu/software/netcdf), [HDF5](https://www.hdfgroup.org/solutions/hdf5/) & [Zarr](https://zarr.dev/) throughout various language interfaces.

The main goal was to analize performance across different cluster environments, configured with different runtime variables and produce reliable, reproducable results showcasing influences and potential opportunities for optimisation.

This first major contributions aims to be a starting-point for future development and establish a baseline concept for how such a benchmark-framework could potentially look like.

## Examples

## Installation

The projects comes bundles with an intial interface to the [spack](https://spack.io/) packages-manager often used in HPC and is designed to manage requested package version for you. However due to spack quirkiness it is advised so source the spack environment and install packages with dependencies on one another yourself. This is to ensure dependencies are grouped as required. Spack requires `bzip2 ca-certificates g++ gcc gfortran git gzip lsb-release patch python3 tar unzip xz-utils zstd` to be installed. 

The `HFFBench-setup.sh` script should install spack and setup a local python virtual environment `.venv` with neccesary packages for you.

For initial installation simply run `./HFFBench-setup.sh`.

Afterwards `source .venv/bin/activate` as the final step.

Everything else should be taken care of by the benchmark.

### Additional
As mentioned before if you require specific spack packages, which you want to test, to be dependencies of one another it is advised you install these packages yourself as spack can be quirky. 

For this purpose source the `. spack/share/spack/setup-env.sh` script which should have been installed and install the required packages.

## Design

There are two main files showcasing how to use the current benchmark-framework. 

`main.py` and `HFFBench.ipynb` if you like to use `Jupyter Notebooks` and want to script the whole pipeline directly. However not that it is not possible to figure out the `root` directory path from within a notebook run environment, which is why you need to supply a `path_to_root` manually as this is used internal by the benchmark to handle data.

You will see some paths that should be configured to tell the framework where to find potential benchmarks and where to place data once finished. 

### Runs

Next are the different `runs` the framework should perform. A run describes what kind of file will be generate. For example:

```py
"run01": {"X": [[1 * 134217728], [], "f8"],},
``` 

will create a file containing one dataset called `X` with `134217728` random elements each of type `f8` and with no chunks configured. This would equate to a `1` `GB` file.

This allows you to quickly scale the benchmarks by simply increasing the number of elements requested. Adding more datasets is as simple as adding more entries into the dictionary. 

```py
"run02": {"X": [[1 * 134217728], [], "f8"], "Y": [[1 * 134217728], [512], ]},
```

Leaving the `datatype` entry empty will default to `f8` and adding chunking can be done by specifying the number of elements per chunk.

Since the benchmark tries to interface with each respective file formats API, this is the minimum amount of information required to configure a `run`.

### Benchmarks

The benchmark-framework is designed to simply pass required information along the file formats APIs which is the benchmarks `developer` main burden to properly handle.

A `developer` would have to create working `source-code` for `creating` and at a minimum `running` a benchmark. For inspiration please look at `components/benchmarks/`.

A benchmark is descirbed as `.yaml` containing information on the `format`, `language` &  `file-extension` used as well as which type of `parallelism` may be supported.  