
# Quick start

This section will cover how to quickly get HPFFbench up and running.

If you want to learn more about the design of HPFFbench to gain a quick overview, please refer to the [Design](design/overview.md) section.

## Simple run

HPFFbench ships some basic, prebuilt benchmarks to run on any system. They can be found in [benchmarks](../benchmarks). Once the basic configuration has been performed, simply run the script via `python main.py` or similar.

```py
new_config = {
    # Required
    "formats"               : ["hdf5"],
    "languages"             : ["py"],
    "paths"                 : paths,
    "iterations"            : 2,
    "runs"                  : {"run": {"X": [[1 * 134217728], []]}},
    "parallel"              : False,
    "variable_to_benchmark" : ["X"],
    "use spack env"         : True,
    "slurm options"         : slurm_options,
    # Optional
    "use spack env"         : True,
    "spack env"             : spack_envs,
}

Handler(path_to_config=path_to_config)
```

This will tell the framework to find benchmarks with `hdf5` as the format to use with `python` as the language. It will then execute the code it finds and perform whatever function was defined for 2 iterations, before exiting and collecting the results within a [Pandas](https://pandas.pydata.org/) compatible `JSON` file. For this example a file containing a dataset `X` with a size of `1GB` will be created and benchmarked.

IMPORTANT:

Before you can run the benchmark-framework you will need to adjust some basic `slurm_options`. These being `--partition` to tell which partition of your system to run the benchmark on and the `--account` to run them with.

```py
slurm_options = """
#SBATCH --partition=compute
#SBATCH --account=ku0598
"""
```

Optional:

The framework includes a basic [spack](https://spack.io/) interface to manage environments, to run benchmarks in, for you. If you set `use spack env` to `False` your systems default packages will be used without spack managing them.

```py
spack_envs = {
    "test-env-1" : {
        "target"    : ["hdf5", "zarr"],
        "language"  : ["py", "c"],
        "packages"  : {
            "python": {
                "versions" : ["3.11.14"],
                "fresh"    : True
                },
        "compiler": "gcc@11.4",
        "additional": "pip install zarr==3.0.5",
        "install": True
        },
    },
},
```

A spack environment is identified by it's name e.g. `test-env-1` targeting specific formats like `hdf5` or `zarr` for different languages. You will have to make sure all required packages are available and mentioned within the spack environment under `packages`. You can specify a single `compiler` to be used by spack for the all packages within the environment. If you required `additional` python packages you can add them like shown.

IMPORTANT

Setting `install` to `True` will tell the spack interface to perform the installation phase when setting up the environment. This will take a long time, depending on the specific package you want to install and the amount of packages to be installed. Setting `install` to `False` let's the interface assume the package has already been installed within the spack environment and just add the reference to the environment without checking if the package has actually been installed. This behavior might change with future versions of spack.
