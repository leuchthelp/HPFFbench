# HPFFbench

## Introduction

HPFFbench stands for {H}igh-{P}erformance {F}ile {F}ormat {bench}mark. (Name is debatable)

It was developed for the   [DKRZ](https://www.dkrz.de/en) to evaluate the performance of different file format used in [High-Performance Computing (HPC)](https://www.nvidia.com/en-us/glossary/high-performance-computing/) like [NetCDF4](https://www.unidata.ucar.edu/software/netcdf), [HDF5](https://www.hdfgroup.org/solutions/hdf5/) & [Zarr](https://zarr.dev/) throughout various language-interfaces.

The main goal was to analyze performance across different cluster environments running [slurm](https://slurm.schedmd.com/overview.html), configured with different runtime variables and produce reliable, reproducible results showcasing influences and potential opportunities for optimization. It launches each phase, i.e. `creating` a file & `executing` some function of that file for testing, as a separate, new `node-allocation` within a `slurm` cluster to potentially reduce caching effects by only using fresh nodes for benchmarking.

This first major contribution aims to be a starting-point for future development and establish a baseline concept for how such a benchmark-framework could potentially look like.

| Languages     | Supported    |
| ------------- | ------------- |
| Python | &check; |
| C | &check; |
| Rust | planned |

## Examples

![Alt text](newplot.png)

## Installation

The project comes bundled with an initial interface to the [spack](https://spack.io/) package manager often used in HPC and is designed to manage requested package versions for you. However due to spacks quirkiness it is advised to source the spack environment and install packages yourself. This is to ensure dependencies are grouped as required. Spack requires `bzip2 ca-certificates g++ gcc gfortran git gzip lsb-release patch python3 tar unzip xz-utils zstd` to be installed.

The `HPFFbench-setup.sh` script should install spack and setup a local python virtual environment `.venv` with necessary packages for you.

For initial installation simply run `./HPFFbench-setup.sh`.

Afterwards `source .venv/bin/activate` as the final step.

Everything else should be taken care of by the framework.

### Additional

If you require specific spack packages to be dependencies of one another it is advised you install these packages yourself as spack can be quirky.

For this purpose source the `. spack/share/spack/setup-env.sh` script which should have been installed and install the required packages.

## Design

There are two main files showcasing how to use the current benchmark-framework.

`main.py` and `HPFFbench.ipynb` if you like to use `Jupyter Notebooks` and want to script the whole pipeline directly. However, it is not possible to figure out the `root` directory path from within a notebook run environment, which is why you need to supply a `path_to_root` manually as this is used internally by the framework to handle data.

You will see additional paths that should be configured to tell the framework where to find potential benchmarks and where to place data once finished.

### Benchmark Framework Configuration

Shown below are some of the most common parameters required for the framework to function as intended:

```py
new_setup = {
    #"formats"               : ["hdf5", "netcdf4", "zarr"],
    "formats"               : ["hdf5", {"hdf5": "subfiling"}, {"hdf5": "async"}],
    "languages"             : ["py", "c"],
    "paths"                 : paths,
    "iterations"            : 10,
    "runs"                  : runs,
    "parallel"              : True,
    "par_backend"           : ["MPI", "Additional"],
    "ranks"                 : [8, 16, 32, 64, 128],
    "nodes"                 : [1, 2, 4, 8, 100],
    "variable_to_benchmark" : ["X"],
    #"variable_to_benchmark" : ["X", "My-Dataset2", "My-Dataset3"],
    "only data"             : False,
    "use spack env"         : True,
    "max processes"         : 20, #Number of benchmarks to run in parallel
    "slurm options"         : slurm_options,
    "spack env"             : spack_envs,
    "delete envs"           : False,
}
```

Most of these should be self-explanatory. Please refer to the [documentation]() for more detail.

The finished config is then passed to a `Handler` object which handles the associated information and runs any benchmarks found within the `/benchmarks` directory that matches any of the requested information.

Potential `benchmarks` are identified by `format`, `language`, `parallel` & the associated `par_backend`.

Once finished a `.json` file is created, containing all the collected results and a bunch of additional data as a [pandas Dataframe](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html).

### Runs

Next are the different `runs` the framework should perform. A run describes what kind of file will be generate. For example:

```py
"run01": {"X": [[1 * 134217728], [], "f8"],},
```

will create a file containing one dataset called `X` with `134217728` random elements each of type `f8` and with no chunks configured. This would equate to a `1` `GB` file.

This allows you to quickly scale the benchmarks by simply increasing the number of elements requested. Adding more datasets is as simple as adding more entries into the dictionary.

```py
"run02": {"X": [[1 * 134217728], [], "f8"], "Y": [[10 * 134217728], [512], ]},
```

Leaving the `datatype` entry empty will default to `f8` and adding chunking can be done by specifying the number of elements per chunk.

Since the benchmark tries to interface with each respective file formats API, this is the minimum amount of information required to configure a `run`.

### Benchmarks

The benchmark-framework is designed to simply pass required information along to the file formats APIs which is the benchmarks `developer` main burden to properly handle. Individual benchmarks are identified by their `format` attribute. A format can be either just a `string` or a `dictionary` which describes a specific feature that is being used. Example:

```yaml
format: hdf5

or

format: 
    hdf5: subfiling
```

A `developer` would have to create working `source-code` for `creating` and at a minimum `running` a benchmark. For inspiration please look at `components/benchmarks/`.

A benchmark is described as `.yaml` containing information on the `format`, `language` &  `file-extension` used as well as which type of `parallelism` may be supported.

#### Creating a file

To create a file based on the information supplied by the framework a `developer` would need to supply two `yaml` attributes, those being `create_command` and `create`. Creating a file in a separate step can help to reduce caching effects. There is nothing stopping you from combining both the `running` and `creating` step into one.

`create` is the source-code required to create a given file. It is up to the developer to ensure their code can handle any inputs supplied. Within `create` they will also have to supply a `#MAIN` directive similar to a `pragma` in `C`. This will inject a pre-made `main` which calls the code and collects potential results. This is based on the `language` attribute to identify the requested programming language. Please refer to the support matrix for information on the languages currently supported by `HPFFbench`.

`create_command` is a list of commands that are used to execute your code. A single `serial` command is the minimum amount of commands required.

#### Benchmarking a file

Benchmarking a file will effectively be the same as creating a file. A `developer` will still need to supply both a list of `run_command`'s and `source`-code that will be executed. The `#MAIN` directive will be replaced with the same code as in `create`.

### Spack Environments

The benchmark-framework is designed to handle different spack packages for you with [spack environments](https://spack-tutorial.readthedocs.io/en/latest/tutorial_environments.html)

For this purpose you will need to define and pass your required environments.

This is done as a `dictionary` which includes the name of the `env` to create as a key and another `dict` as the value which includes the benchmarks to `target` for that environment. For example:

```py
"env-1" : {
    "target" : ["hdf5", {"hdf5": "subfiling"}, "netcdf4", "zarr"],
}
```

will tell the framework to use `env-1` for all `hdf5`, `hdf5` using the `subfiling` feature, `netcdf4` & `zarr` benchmarks it can find. If you want to target the same benchmarks with multiple environments, you will simply have to add that benchmark to the `target`-list.

The same mechanism works for describing which `language`s to use the environment for:

```py
"language"  : ["py", "c"],
```

Next will be the packages to add to the environment. This corresponds to the `spack install` syntax and will simply pass through all requested information straight to spack. *This is done to allow multiple versions of the same package within a single environment; however handling this functionally is currently undefined.*

```py
"packages": {
    "python": {"versions" : ["3.11.14"],
               "fresh"    : True
            },
    
    "openmpi": {"versions" : ["5.0.8"],
                "fresh"    : True
                "variants" : "build_system=cmake",
            },
}
```

If you want to ensure a specific compiler is used, simply add:

```py
"compiler": "gcc@13",
```

and if you have any additional packages, like for example python packages, add:

```py
"additional": "pip install zarr==3.0.5 py-spy",
```

WARNING:
Additionally if you want to have the framework install the spack packages for you, you can add `"install": True`. However this will drastically increase the initial start-up time as you will have to run the entire `spack install` process, which builds all required packages from source. Similarly spack can be quite quirky and might not install all packages the exact way you envisioned. For example `netcdf4` depends on `hdf5`. If you want your `netcdf4` install to use the exact version of `hdf5` installed just before, you can request that, however the spack concretizer might not fully respect your wishes and you could end up with two different version of `hdf5` being installed, one that `netcdf4` depends on and another that you have specifically requested. This could lead to unintended behavior when running a given benchmark. So it is advised to forego `"install": True` and handle initial installing of packages manually for now.

### Slurm Options

You can simply pass necessary slurm options like so:

```py
slurm_options = """
#SBATCH --partition=compute
#SBATCH --account=
#SBATCH --constraint="[cell02]"
#SBATCH --mem=0
#SBATCH --cpu-freq=High
#SBATCH --distribution=block:cyclic
#SBATCH --time=02:00:00
#SBATCH --exclusive
#SBATCH --output=log/log-%j/log.%j.txt
#SBATCH --error=log/log-%j/log.%j.err
"""
```

Both `--account` and `--partition` are required as with any `sbatch` script. The rest is up to you.
