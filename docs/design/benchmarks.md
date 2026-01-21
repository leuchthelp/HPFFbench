# Benchmarks

Benchmarks are considered immutable for the benchmark-framework. They represent shareable objects, that can be dropped into the framework environment and picked up as an additional [capability][handler].

## Benchmark ID

Each benchmark gets assigned a unique [hash][benchmark-hashes], which ensure results can be mapped to specific changes later on.

## Benchmark.yaml

This is the heart and soul of the framework. Benchmarks can be added dynamically. All a developer needs to ensure, is a properly formatted `benchmark.yaml` that includes all required information.

RECOMMENDATION, NOT REQUIRED

A Benchmark should be named via: `format`-`language`-`parallelism`*-`feature`.`yaml`

*parallelism: If parallelism is supported, identifiers such as `serial`, `parallel` or `both` are recommended.

### Example yaml

```yml
parallel: configurable
par_backend: MPI
language: py
extension: h5
format: hdf5
    hdf5: async
compile: True
compile_command: gcc {runnable} <openmpi> -lmpi <hdf5> -lhdf5_hl -lhdf5
create_command: 
    serial     : python {runnable}
    MPI        : mpiexec -n python {runnable}
    profile    : py-spy record -o <profile_path>.json -- python {runnable}
    profile-MPI: mpiexec -n py-spy record -o <profile_path>.json -- python {runnable}


create: |
    def create(variables=[], shapes=[], chunks=[], datatypes=[], parallel=False, path=None, collective=False):

    #MAIN


run_command:  
    serial     : python {runnable} -v
    MPI        : mpiexec -n python {runnable} -v
    profile    : py-spy record -o <profile_path>.json -- python {runnable} -v
    profile-MPI: mpiexec -n py-spy record -o <profile_path>.json -- python {runnable} -v


source: | 
    def bench(iterations, variable: None, parallel=False, path=None, collective=False):

        return result
    
    #MAIN
```

The order in which the values are specified does not matter.

1. parallel: either `True`, `False` or `configurable`.
2. par_backend: (Optional) `str`, if requested needs to match in global config.
3. language: `str`, if requested needs to match global config.
4. extension: `str`, file extension of format used.
5. format: either `str` or `dict`, if requested needs to match global config. `dict` if you want to signal a specific feature used.
6. compile: either `True` or `False`, needs to be set for compiled languages.
7. compile_command: `str` that contains compile instructions.
8. create_command: `dict` that has the `par_backend` as its key and a `str` containing execution instructions. Needs to be `serial` as a default.
9. create: `str` containing source code for creating a given file.
10. run_command: `dict` the same as `compile command`.
11. source: `str` containing source code to execute a benchmark on either a prior created file or an existing file. In that case `create` & `create_command` are not needed.

### Compile command

Imagine a compile command as if you'd be doing it manually. You can supply all information you would like. `{runnable}` needs to be includes as this will later be replaced to the file the framework creates internally.

Only when you are using spack environments managed through the benchmark-framework do you need to also supply the `<package>` pattern. These will be replaced internally by the spack package location associated with the environment and must match the exact name you give the package when defining the [environments][spackmanager].

### How does source code need to structure?

Source code has a couple of specifics to remember when writing new benchmarks. This is meant to be a abstract interface, which can be applied to either language. (Improvements are very welcome)

Looking at the `create` function, this will always receive lists of `variables`, `shapes`, `chunks`, `datatypes`, `parallel`, `collective` flags and a `path` as `str`. `path` will be the internal location the file file is temporarily saved at and already includes the `name` the file should have.

This is regardless of language used or benchmark run. A developer should be able to handle arguments, for example ignoring them when not needed like for `parallel` or `collective` if the benchmark is only serialized.

```py
variables = ["X", "Y"]

```

`variables` represents the names of the datasets which need to be created within a file.

```py
shapes = [[512, 512, 512], [1 * 134217728]]
chunks = [[32, 32, 32], []]
datatypes = ["f8", "f4"]
```

`shapes`, `chunks` & `datatypes` are list of lists with their indices mapped to entries in `variables`.

#### The #MAIN directive

This is by far the most important directive as it tells the benchmark-framework to inject a `main` function that matches the languages requested. This enables developers to only have to focus on their end of the code. Everything else will be provided and takes care of for them.

IMPORTANT

There currently does not exist a dynamic interface for additional `mains` for other languages. If you wish to see a specific language be added, please either request it or develop an equal `main` to the existing ones and create a [pull request](https://github.com/leuchthelp/HPFFbench/pulls) for it.

#### Creating a file

##### Create command

If you will need a [create command](#create-command) as seen above. `serial` is the default name given to the dictionary key. Otherwise the additional commands are assumed to be for implementations relying on parallelism and have to match the `par_backend` defined prior. This allows developers to reuse the same exact code for `Both` serialize and parallelized benchmarks, should they differ only by a simple `bool` for example. In that case `parallel` needs to be set to `configurable` and then `Both` can be specified in the global config.

##### Create code

This contains source code for creating a test-file and needs to be formatted properly, otherwise files might execute. Example is already covered in [How does source code need to structure?](#how-does-source-code-need-to-structure)

#### Benchmark a file

##### run command

Exactly the same as [create command](#create-command)

##### Benchmark code

Almost exactly the same as [create code](#create-code). The only major change is the swap from `create` to `bench` for the function name, with slightly different arguments.

As can be seen above a number of `iterations` will be supplied, with again a list of `variables` that are going to be benchmarked within the file as well as the usual `parallel` & `collective` flags. `path` again as [before](#how-does-source-code-need-to-structure) is the file path where the file is located temporarily. If you wish to use an existing file and not have the benchmark create one for you, simply ignore `path`.

### profile command

Profile command behaves similar to [create commands](#create-command) & [run commands](#run-command), you specify which profiler should be used beforehand, the same as if you'd do it manually and then only need to specify the `<profile-path>` pattern for your profilers `output` argument, so the framework can save data in a centralized `path_to_profiling` location.
