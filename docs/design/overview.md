# Overview

If you have already read through the [quickstart guide][quick-start], you can skip to [Abstract Interface of "File" & "Datasets"](#abstract-interface-of-file--datasets).

For more information of creating a new [benchmark][benchmarks] and it's defining [benchmark.yaml][benchmarks].

## Introduction

To use the framework you will first have to define a setup:

```py
new_config = {
    # Required
    "formats"               : ["hdf5"],
    "languages"             : ["py"],
    "paths"                 : paths,
    "iterations"            : 2,
    "runs"                  : {"run": {"X": [[1 * 134217728], []]}},
    "parallel"              : False, # can also be "Both"
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

### Abstract Interface of "File" & "Datasets"

Some applications may refer to a `file` encoded in a `format` as a [Dataset](https://datasetsearch.research.google.com/). However these `file-formats` understand themselves as a `file` that can contain one or multiple `datasets` organized in `groups` as is the case with [HDF5](https://www.hdfgroup.org/solutions/hdf5/). The main issue lies in how different `file-formats` differ in their internal representation.

In order to abstract this behavior, the `file` -> `dataset`, which looks a little something like this:

```py
{"name": list( shapes(), chunks(), "datatype")}

{"X": [[512, 512, 512], [32, 32, 32], "f8"], "Y": [[1 * 134217728], [], "f4"]}
```

This will tell each benchmark to create or expect a single `file` with 2 `dataset` called `X` & `Y`. `X` is a 3 dimensional dataset with 512x512x512 datapoint each of type `float8`. This corresponds to the [numpy data types convertion](https://numpy.org/doc/stable/user/basics.types.html). It is your responsibility to ensure the datatype is understood by all formats requested. 

Adding more dataset is as simple, as adding more entries to the dictionary. A [benchmark-developer][benchmarks] needs to ensure, they can handle this simplified structure.

### Benchmark Hashes

Each [benchmark][benchmarks] is hashed to produce a unique result. Defining traits are:

```py
run_config               # i.e. "run": {"X": [[1 * 134217728], []]}
config_par_backend       # either single backend or list of backends found in the benchmark.yaml
par_backend              # the actual requested parallel backend
bm_config["parallel"]    # the option for parallel in benchmark.yaml, could also be "Both" 
parallel                 # if parallelism is actually requested
bm_config["format"]      # the formats the benchmark.yaml is compatible with
format                   # the actual format requested
ranks                    # the number of ranks requested, defaults to 1 for serial runs
var_to_bm                # the variables (datasets) that are benchmark, can also be a single one
collective               # if collective I/O was set or not, specifically for MPI compatibility
nodes                    # the number of nodes the benchmark is run on
spack_manager.target     # Spackmanager specific attributes to differentiate benchmarks 
spack_manager.additional # run in different spack environments
spack_manager.compiler   #
spack_manager.packages   #
spack_manager.language   #
spack_manager.env_name   #
                  
# Reasoning: If source code changes, do not consider the same benchmark even if it 
# might be functionally the same, could still have an effect on performance
source-code         
```

## Stages

The benchmark-framework is currently designed in 3 stages:

1. [Handler](#handler)
2. [Spackmanager](#spackmanager)
3. [Benchmarkmanager](#benchmarkmanager)

### Handler

Once the initial setup is concluded and passed on, the [Handler](handler.md) works by:

1. Loading the config.
2. Setting some basic configuration options.
3. Checking if the framework is run within a [slurm](https://slurm.schedmd.com/) capable environment.
4. Checking if the configured paths exit and can be used, otherwise it will fall-back to sensible defaults.
5. Determine it's capabilities - these are defined by the benchmarks found within the [benchsmarks](https://github.com/leuchthelp/HPFFbench/tree/refactor/benchmarks) directory.
6. Initialize required [Spackmanagers](#spackmanager) - 1 will be create per environment requested.
7. Create [benchmarks][benchmarks] - each benchmark is controlled by a [Benchmarkmanager](#benchmarkmanager){#bm-general}. Benchmarkmanagers are created only if a user-request matches the determined capabilities of the framework. These objects will be created and populated with required metadata, but not executed immediately.  
8. Once a list of all [Benchmarkmanager](#bm-general) objects is gathered and returned to the [Handler](handler.md), the `.run()` method of each [Benchmarkmanager](#bm-general) is evoked. Benchmarkmanager are executed 1 per available core on the system of a [pathos ProcessPool](https://pathos.readthedocs.io/en/latest/pathos.html#pathos.helpers.ProcessPool). The number off cores used can be adjusted by specifying `max processes` in the initial config.
9. Once all [Benchmarkmanagers](#bm-general) finish, with results saved at `path_to_results`, a [pandas DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html) is generated and returned as `JSON`. By setting `only data` to `True` in the initial config, execution of Benchmarks with be skipped, if you have already generated your results and just wish to collect the again into a new DataFrame.

### Spackmanager

A [Spackmanager](spackmanager.md) encapsulated all defining information of a specific spack environment requested by the user. The environment will be create once upon being requested. If you define multiple spack environments but end up runnings benchmarks not `targeted` by that specific environment, it will not be created to save on time and resources.

Be aware creating a spack environment can take a considerable amount of time upon first launch, as the [spack package manager](https://spack.io/) builds all packages from source for this specific system. To reduce the time complexity for subsequent runs existing environments are kept and reused. If you want to delete all environments upon exit set the `delete envs` flag in the initial config.

An example of a spack environment to request, looks a little something like this:

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
            "hdf5": {
                "versions" : ["1.14.6"],
                "variants" : "~cxx~fortran+hl~ipo~java~map+mpi+shared+subfiling~szip+threadsafe+tools",
                },
        "compiler": "gcc@11.4",
        "additional": "pip install zarr==3.0.5",
        "install": True
        },
    },
},
```

The interface simply passes spack flags onto spack and enables a user to define reproducible environments.

This `test-env-1` targets both the `hdf5` and `zarr` formats for both the `python` and `c` programming language. In the environment the `python` package with `version` `3.11.14` will be installed. [fresh](https://spack.readthedocs.io/en/latest/package_fundamentals.html#reusing-installed-dependencies) signals to `spack` to build & install the package without using existing system or spack packages. For all packages within the environment `gcc` with version `11.4` will be used. In addition you can also install `additional` packages. For this functionally only pythons `pip` is supported.

A [Spackmanager](spackmanager.md) then creates an environment within a `environments/` directory. It gathers all packages and their variations and build a install script, installs all requested software and creates an internal memory about which specific spack packages, identified via their respective hashes, are the once installed to that environment. This is done to ensure the right package hashes are parse to the compiler for compiled languages. This is also important, as this list of packages is a defining trait of a [benchmarks hash](#benchmark-hashes).

What a variation of a packages might look like is show with the `hdf5` package. As you can see this packages has a lot of optional attributes that can be enabled or disabled as required. Should you need `hdf5` with `subfiling` support, you would simply add `+subfiling`.

### Benchmarkmanager

The benchmark manager is what ultimately receives all metadata, source-code and alike from what the framework ingests.

With this information it:

1. Sets all configuration options (current time, parallel backend, format, environment, etc.).
2. Converts the requested [file](#abstract-interface-of-file--datasets) to match the arguments structure of each supported language interface.
3. (Optional) A profiler can be requested by setting the `profiler` flag to `True` and supplying a [profile-command][profile-command] in the [benchmark.yaml][benchmarkyaml]{#bm-yaml} with a compatible and installed profiler.
4. Waits until the [Benchmarkmanagers](benchmarkmanager.md){#bm-file} `.run()` method is called.
5. Create a directory under `path_to_tmp` where files are saved temporarily. Additional metadata during a running benchmark will be dumped into the directory if the `show metadata` flag is set in the global configuration. If a profiler is used, additionally creates a new entry in the `path_to_profiling` directory and saves profiling-results.
6. Checks if `create` is specified in [benchmark.yaml](#bm-yaml), the [BenchmarkManager](#bm-file) takes [source-code][create-code] from the [benchmark.yaml](#bm-yaml) to create a matching file. Gets compiled for compiled languages.
7. Once a file has been created, runs the [benchmarking-code][benchmark-code] supplied. Also gets compiled for compiled languages.
8. Once finished it returns it's own unique [benchmark-id][benchmark-id] and a dictionary containing all metadata.

Results are saved to `path_to_results` as `JSON`. The filename is made up for the unique [hash](#benchmark-hashes) and the timestamp of when the benchmark was run.
