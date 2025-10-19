Written: 17.03.2025

## Setup Project

### Local

This assumes you have admin rights and a refresh installation of `debain-based` Linux and will only cover the steps needed to run both `main.py` and `/c-stuff/a.out` scripts.

This will not cover how to install `ipython` or `juypter` functionally. Using an editor like `VSCode` should already help you and configure all the necessary steps to display the notebook.

Run
```
sudo apt update

sudo apt upgrade
```

and install `spack` required software with
```
sudo apt install bzip2 ca-certificates g++ gcc gfortran git gzip lsb-release patch python3 tar unzip xz-utils zstd
```

After refresh your shell and execute
```
bash dkrz_dev/dkrz_dev_setup.sh
```

from your `/home/user` directory.

`spack` should then be downloaded via `git` and installed. All these steps are also detailed in the `dkrz_dev_setup.sh`.

**WARNING** This process will potentially take multiple hours as `spack` builds all required packages from source.

After `spack` has finished we should add the `spack env` permanently to our shell and load all required modules using `module` which the script installed as `lmod`. In order to do this navigate into your `/home` directory and run:
```
nano .bashrc
```

If a bash configuration was already created by your `OS` it should already be filled otherwise a new `.bashrc` will be created.

Either way we will add the following lines to the **end**:
```
. ~/spack/share/spack/setup-env.sh

. $SPACK_ROOT/share/spack/setup-env.sh

. $(spack location -i lmod)/lmod/lmod/init/bash

module load hdf5 netcdf-c py-mpi4py openmpi python py-pip py-netcdf4 py-h5py py-rich py-numpy git nano gcc

module load hdf5-vol-async/develop
```

You will then have to set a couple environmental variables. For this you need to locate where `spack` installed the packages and more importantly under what `hash`. You will have to do this for `HDF5`, `NetCDF4` and `HDF5-VOL-ASYNC`. They should be under `/home/user/spack/opt/spack/<platform-linux>/<compiler>/`.

You will need the `/lib` e.g. `/home/user/spack/opt/spack/<platform-linux>/<compiler>/lib-hash/lib`

Locate all 3 and fill them into
```
export LD_LIBRARY_PATH=/<first-lib>:<second-lib>:<third-lib>
```

You should add this to the `.bashrc` we edited earlier as well.

You will also have to recompile `benchmarks.c` with these new locations using. TODO add make / cmake
```
gcc benchmarks.c -I<location to openmpi>/include -L<location to openmpi>/lib -Wl,-rpath -Wl,<location to openmpi>/lib -lmpi -I<location to netcdf4>/include -L<location to netcdf4>/lib -lnetcdf -I<location to hdf5>/include -L<location to hdf5>/lib -lhdf5_hl -lhdf5 -I<location to hdf5-vol-async>/include -L<location to hdf5-vol-async>/lib -lasynchdf5
```

After we  add the `spack` environment permanently to our shell navigate into `/dkrz_dev` and from within we now need to setup a python virtual environment `venv` to install packages missing in `spack`.
```
cd /dkrz_dev

python -m venv .venv

source .venv/bin/activate

module load py-pip

pip install -r requirements.txt
```

Once done refresh you shell one final time to be safe and everything should be configured properly.

**IMPORTANT: Do not do this on any kind of Cluster as you will run the script on a login node**

Then just run the `main.py` script and plot the results using the `dev_original.ipynb` notebook (**Installation for notebook functionally not covered**).

  
### Cluster (DKRZ)

Will only cover the steps needed to run both `main.py` and `/c-stuff/a.out` scripts. Setup on `levante.dkrz.de` is slightly different.

This will not cover how to install `ipython` or `juypter` functionally. Using an editor like `VSCode` should already help you and configure all the necessary steps to display the notebook.

First we need to configure out DKRZ user account to allow custom spack package installation.

See https://docs.dkrz.de/doc/levante/code-development/building-with-spack.html

To login into `levante.dkrz.de` please see  https://docs.dkrz.de/doc/levante/access-and-environment.html
```
ssh q012345@levante.dkrz.de
```

When login into `levante.dkrz.de` you should already find yourself in `/home/<letter assigned>/<letter:user_id>` so e.g. `/home/q/q012345`.

From here navigate into the reconfigured `.spack` directory.
```
cd .spack
```

And add 3 `.yaml files`

`config.yaml`
```
config:
  install_tree:
    root: <your-installation-directory>
```

`upstreams.yaml` - to allow access to preinstalled packages on DKRZ
```
upstreams:
  system_installs:
    install_tree: /sw/spack-levante
```
and

`modules.yaml`
```
modules:
  default:
    enable: []
    roots:
      tcl: /your/modules/directory
```

After refresh your shell and execute from your `/home/user` directory.
```
bash dkrz_dev/dkrz_dev_setup.sh
```

`spack` should then be downloaded via `git` and installed. All these steps are also detailed in the `dkrz_dev_setup.sh`.

**WARNING** This process will potentially take multiple hours as `spack` builds all required packages from source.

After `spack` has finished we should add the `spack env` permanently to our shell and load all required modules using `module` which the script installed as `lmod`. In order to do this navigate into your `/home` directory and run:

```
nano .bashrc
```

If a bash configuration was already created by your `OS` it should already be filled otherwise a new `.bashrc` will be created.

Either way we will add the following lines to the **end**:

```
. ~/spack/share/spack/setup-env.sh

. $SPACK_ROOT/share/spack/setup-env.sh

. $(spack location -i lmod)/lmod/lmod/init/bash

module load hdf5 netcdf-c py-mpi4py openmpi python py-netcdf4 py-h5py py-rich py-numpy

module load hdf5-vol-async/develop
```

You will then have to set a couple environmental variables. For this you need to locate where `spack` installed the packages and more importantly under what `hash`. You will have to do this for `HDF5`, `NetCDF4` and `HDF5-VOL-ASYNC`. They should be under `/home/user/spack/opt/spack/<platform-linux>/<compiler>/`.

You will need the `/lib` e.g. `/home/user/spack/opt/spack/<platform-linux>/<compiler>/lib-hash/lib`

Locate all 3 and fill them into

```
export LD_LIBRARY_PATH=/<first-lib>:<second-lib>:<third-lib>
```


You should add this to the `.bashrc` we edited earlier as well.

You will also have to recompile `benchmark.c` with these new locations using. TODO add make / cmake
```
gcc benchmarks.c -I<location to openmpi>/include -L<location to openmpi>/lib -Wl,-rpath -Wl,<location to openmpi>/lib -lmpi -I<location to netcdf4>/include -L<location to netcdf4>/lib -lnetcdf -I<location to hdf5>/include -L<location to hdf5>/lib -lhdf5_hl -lhdf5 -I<location to hdf5-vol-async>/include -L<location to hdf5-vol-async>/lib -lasynchdf5
```

You should add this to the `.bashrc` we edited earlier as well

After we  add the `spack` environment permanently to our shell navigate into `/dkrz_dev` and from within we now need to setup a python virtual environment `venv` to install packages missing in `spack`.
```
cd /dkrz_dev

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt
```

**Important**: make sure the `c-stuff/data/datasets` path exists. This is where datasets created by the `C` part of the benchmark will be saved. If it doesn\`t exist yet, create it.

Once done refresh you shell one final time to be safe and everything should be configured properly.

Then just run the `main.py` script using the provided **IMPORTANT: slurm script** and plot the results using the `dev_original.ipynb` notebook (**Installation for notebook functionally not covered**).

Not using a `slurm script` on DKRZ will cause `main.py` to be executed on a `login-node` with minimal resources and is correct. Please be aware.


## Python Implementation

The python implementation currently consist of 2 major parts; a `main.py` which is the executable script to run the benchmark with and `Datastruct.py` which provides the data structure to handle dynamic creation, opening and reading.

Python was chosen to be a target as most scientific work relating to Zarr, NetCDF4 and HDF5 is done using Python. Sadly not all features that are of interest to this project are currently available in Python.

### Datastruct.py

The Datastruct implementation produces a `Datastruct` class which is a wrapper around common functions tasked with creating, opening and reading in all 3 major Data formats `Zarr`, `NetCDF4`, `HDF5` outline in the projects main goal.

**YOU CREATE ONE `DATASTRUCT` PER SUPPORTED DATAFORMAT.**

Datastruct features 3 main public functions: 
``` python
Datastruct.create(path, form, engine, dtype, parallel)

Datastruct.open(mode, path, engine)

Datastruct.read(pattern, variable, iterations, logging)
```

A Datastruct object saves and sets information about itself such as:
``` python
path = None
shape = []
chunks = []
mode = None
ngine = None
compression = None
dataset = any
log = None
parallel = False
```

  
```python
.create()
```

is tasked with dynamically creating a Data format specified by `engine` with a matching name and path specified with `path` using a predefined format with `form` and data-type `dtype`. The default mode for Data format creation is to be handled serially.

Data format creation using parallel features can be enabled with the Boolean `parallel` (not currently implemented).

It then exposes the underlying Data format via `Datastruct.dataset`.
```python
 {variable: (shape, chunks)}
 
 Example:
  {"X": ([512, 512, 512], [512, 512, 1])}
```

The predefined format required by `form` is a python dictionary `dict` which specifies the name of the variable `X` to be created, its `shape` and the chunking `chunks` for each dimension.  To specify no custom chunking and rely on the standard configuration for `chunking` by each Format simply leave `chunks` empty.
```python
 {variable: (shape, chunks)}
 
 Example:
  {"X": ([512, 512, 512], [])}
```

An arbitrary number of dimensions with arbitrary shaping and chunking within the standard specification of each Data format is supported.

Each created file will have the following structure:
```
Group: /
  Variable 1: (shape, chunks),
  Variable 2: (shape, chunks),
  ...
  Variable n: (shape, chunks)
```

Other more complicated configurations are not supported for creation via `.create()`.
```python
.open()
```

Can open any file that is either Zarr, NetCDF4 or HDF5 specified by `engine` in either mode `mode` supported by the respective Data formats.
```python
.read()
```

**(`logging` is currently unused. Its meant to initialize an additional logger in the future to provide for metrics than just `time`.)**

Can read any file that is either Zarr, NetCDF4 or HDF5. `.read()` uses it's own knowledge of what file has been opened with which engine and mode, so the user does not have to provide that information again.

The user has to specify a `variable` to read from and the number of `iterations` to perform.

Additionally the user needs to provide one of the currently available patterns via `pattern` which maps it to private predefined functions simulating different behaviour.
```
"header"
"variable"
"bench_variable"
"bench_complete"
```

 `"header"`: simply returns the header information (`iterations` will be ignored)

 `"variable"`: returns the variable read loaded into memory (`iterations` will be ignored)

Now onto patterns carrying the `bench_` naming convention. These patterns are designed to run internal benchmarking and exposing the results of these benchmarks via `Datastruct.log`. The current implementation generates a list of `len(iterations)` filled with time measurements of how long it took to perform a specific action.

Time is measured using `python: time.monotonic()`:
```
Return the value (in fractional seconds) of a monotonic clock, i.e. a clock that cannot go backwards. The clock is not affected by system clock updates. The reference point of the returned value is undefined, so that only the difference between the results of two calls is valid.
```

For more information please visit https://docs.python.org/3.11/library/time.html#time.monotonic

 `"bench_variable`: Reads an entire variable of the Data format into memory.

 `"bench_complete"`: Reads the entire Data format into memory including an arbitrary number of variables (be prepared to have sufficient RAM available)

### main.py

This is the executable script which handles setting up the Data formats to benchmark, performing the benchmarks via `Datastruct`and the exporting the results using `JSON` which can then be reimported into `pandas` for example for plotting and performance analysis. The `JSON` features the name for the `bench_` used and adds the prefix `plotting_`. For the `bench_` functions one needs to provide a `pandas.DataFrame()` as they are used to gather all relevant information and create the output `JSON`.

Currently `main.py` provides:
``` python
create_ds(form, parallel) #create Data formats for Zarr, NetCDF4, HDF5
show_header(ds_tmp) #show header for all 3
calc_chunksize(chunks) #returns chunksize with matching unit
bench_variable(setup, df, variable) #run benchmark for all 3 and export JSON
bench_complte(setup, df, variable) #run benchmark for all 3 and export JSON
```

To run a benchmark you first have to define a dictionary called `setup`, which defines the Dataset to created and evaluate for Zarr, NetCDF4, HDF5 as an individual run.

Example:
```python
setup = {

"run01": {"X": ([512, 512, 512], [512, 512, 1]), "Y": ([10, 10], [2, 2])},

"run02": {"X": ([512, 512, 512], [512, 512, 8]), "Y": ([10, 10], [2, 2])},

"run03": {"X": ([512, 512, 512], [512, 512, 16]), "Y": ([10, 10], [2, 2])},

"run04": {"X": ([512, 512, 512], [512, 512, 32]), "Y": ([10, 10], [2, 2])}, 

"run05": {"X": ([512, 512, 512], [512, 512, 64]), "Y": ([10, 10], [2, 2])},

"run06": {"X": ([512, 512, 512], [512, 512, 128]), "Y": ([10, 10], [2, 2])},

"run07": {"X": ([512, 512, 512], [512, 512, 256]), "Y": ([10, 10], [2, 2])},

"run08": {"X": ([512, 512, 512], [512, 512, 512]), "Y": ([10, 10], [2, 2])},

}
```

Both predefined `bench_` functions run both `python` and `C` scripts. The `C` part is launched as a subprocess. (**Note**: Chunking is currently not supported for the `C` script and `bench_` should reflect that.)

After the benchmark has finished you can plot the results using the `dev_original.ipynb` notebook provided.

### Zarr v3.0.1

**supported**
- serial creation / open / read of File
- parallel creation of File using MPI via `mpi4py`  

**working on**
- parallel reading / writing of File  
#### Problems

##### parallel reading / writing of File:

Zarr currently does not have official support for MPI based parallelisation and is `Coming soon`

https://zarr.readthedocs.io/en/v3.0.1/user-guide/performance.html#parallel-computing-and-synchronization

Previously parallel access for Zarr in v2.18.4 was handle with `multiprocessing` or `threading` ensuring each `Writer` only accesses on singular subfile created by Zarr.

https://zarr.readthedocs.io/en/v2.18.4/tutorial.html#parallel-computing-and-synchronization


### NetCDF4 v4.9.2 py: netCDF4 v1.7.1.post2

**supported**
- serial creation / open / read of File
- parallel creation of File using MPI via `mpi4py` **WARNING: currently takes up to 5 minutes**

**working on**
- parallel reading / writing of File

#### Problems

##### parallel reading / writing of File

yet unknown, in debugging


### HDF5 v1.14.5 py: h5py v3.12.1

**supported**
- serial creation / open / read of File
- parallel creation of File using MPI via `mpi4py` **WARNING: currently takes up to 5 minutes**

**working on**
- parallel reading / writing of File

#### Problems

##### parallel reading / writing of File

yet unknown, in debugging

  

## C Implementation

 The C implementation currently consist off one file called `benchmarks.c` located in the `c-stuff` directory. The script features a similar approach to the python implementation simply lacking the `Datastruct` class due to the nature of C. The project wanted to focus on 3 important features currently only available in C, namely `HDF5-VOL-ASYNC`, ``HDF5-VOL-SUBFILING` and `NetCDF-C-NCZarr`.

Currently available functions:
``` C
void save_to_json(double *arr, char *file_name, char *name, size_t size)
void create_hdf5(bool with_chunking, int size)
void create_hdf5_parallel(int argc, char **argv, bool with_chunking, int size)
void create_hdf5_async(int argc, char **argv, bool with_chunking, int size)
void create_hdf5_subfiling(int argc, char **argv, int size)
void bench_variable_hdf5(int size, int iteration)
void bench_variable_hdf5_parallel(int argc, char **argv, int size, int iteration)
void bench_variable_netcdf4(int size, int iteration)
void bench_variable_nczarr(int size, int iteration)
void bench_variable_async(int argc, char **argv, int size, int iteration)
void bench_variable_subfiling(int argc, char **argv, int size, int iteration)
```

  
``` C
void save_to_json()
```

Is used to generate a JSON output from a given benchmark so it can be plotted and evaluated later.

`create_` functions similarly to Python are used to create the respective Data formats with the needed functionally as `async` and `subfiling` both need different drivers to be enabled and `subfiling` uses a completely different structure from a regular `HDF5` dataset.

Similar to Python each `bench_` function sets up and runs a benchmark for some number of `iterations` and exports the time taken for each iteration to complete as a `JSON`. Time is measure using `clock_gettime(CLOCK_MONOTONIC)`.

For more information please visit https://www.man7.org/linux/man-pages/man3/clock_gettime.3.html#top_of_page
``` C
void create_hdf5(bool with_chunking, int size)
```

Creates a regular HDF5 file using the default backend. Additionally chunking can be enabled with `with_chunking`. `_parallel` provides the same functionally using `MPI-I/O` drivers.
``` C
void create_hdf5_subfiling(int argc, char **argv, int size)
```

Create a HDF5 file using `subfiling`. Within this function parameters such as `scripe_size`, `stripe_counter` which represents the amount of subfiles created and `thread_pool_size` which represents the number of MPI ranks or workers, can be changed and adjusted.

For more information on `subfiling` please visit https://github.com/HDFGroup/hdf5doc/blob/master/RFCs/HDF5_Library/VFD_Subfiling/user_guide/HDF5_Subfiling_VFD_User_s_Guide.pdf or the respective `subfiling` section which will provide for information in the future.
``` C
void create_hdf5_async(int argc, char **argv, bool with_chunking, int size)
```

Create a HDF5 file using `async`.

For more information `async` please visit https://hdf5-vol-async.readthedocs.io/en/latest/  or the respective `async` section which will provide for information in the future.

All the relevant `bench_` functions internally call their respective `create_` functions and the loop `reading` the created file back for `iterations` amount of times.

To use `a.out` compiled from `benchmarks.c` you call it with `./a.out` and pass some arguments to it.
```
./a.out -b 2 -i {iterations} -s {filesize} -f {faktor}
```

`-f` can be used to make it easier to scale the total file size.

For benchmarks requiring `MPI` i.e. `hdf5-parallel`, `async` or `subfiling`
```
mpiexec -n {num processes} ./a.out -b 2 -i {iterations} -s {filesize} -f {faktor}
```

This used `argp_parse` internally so if you require additional info simply parse

```
./a.out --help
```

### Zarr v2 C: NetCDF4 v4.9.2

As Zarr does not have a native C-Implementation and probably never will NetCDF has taken up the torch to create their own Implementation following the Zarr specification in C called NCZarr which is supposed to be cross-compatible with Zarr.

**supported**
- serial reading of File

**working on**

#### Problems

##### serial reading of File - FIXED (20.02.2025)

Zarr file is created using Python using Zarr v3.0.1. In this version for some reason a field `Filters` is being set to an empty `tuple`. When no filters are provided it is supposed to be set to `None`. An issue for a potential bug has been created with the zarr-developers.

You can follow the issue here: https://github.com/zarr-developers/zarr-python/issues/2842

Fix for now would be to set `Filters` to some arbitrary matching filter but has still to be implemented and tested

Bug has been fix and was backported https://github.com/zarr-developers/zarr-python/issues/2842 (20.02.2025)

### NetCDF4 v4.9.2

**supported**
- serial reading of File

**working on**
- integrate c function calls in `Datastruct.py`

#### Problems

### HDF5 v1.14.5

**supported**
- serial reading of File
- serial creation / reading of File using `subfiling`

**working on**
- scaling HDF5 with `subfiling` to better evaluated use-case
- integrate c function calls in `Datastruct.py`

#### Problems

### HDF5-VOL-ASYNC v1.7

**supported**
- lopping reading `async` so I can benchmark
- serial creation / reading of File using `async`

**working on**
- integrate c function calls in `Datastruct.py`

#### Problems
##### serial creation / reading of File using `async` - debugging - FIXED (20.02.2025)

When creating or reading a HDF5 file using `async` operation failures occur during the `async-wait` period when waiting for the async calls to finish. The function from HDF5 `H5ESwait` to perform the waiting process is designed to stop waiting and continue once a singular failed is detected.  

This problem is currently under investigation and the process can be followed here https://forum.hdfgroup.org/t/vol-async-debugging-async-operation-failures/13055/8

Sadly the functions provided by HDF to help debug operation failures lack any real examples which HDF has confirmed to be problem.

Current process is to perform manual debugging to reverse engineer the error handling.

Manual debugging is unsuccessful in determining the root cause further assistance has been requested @ https://forum.hdfgroup.org/t/vol-async-debugging-async-operation-failures/13055/11

Anyway thanks, I will go cry in a corner now for not having realized this earlier.

##### lopping reading `async` so I can benchmark - FIXED (20.02.2025)

`creation` needs to be done by just one rank similarly to `closing` the event-set as otherwise the other ranks cant access it anymore. Will have to implement waiting for rank `0` for creation and rank `0` waiting for all other ranks for `closing`

##### serial creation / reading of File using `async` - debugging SOMEWHAT FIXED (11.03.2025)

On the menu again as there seems to be some run to run variance in it. I sadly have no clue why, working with async has been quite stressful as it seems I have been the first to work with it and have questions about it in the last 5 year when looking at the forum. https://forum.hdfgroup.org/t/how-exactly-is-async-i-o-available-in-hdf5/13089/7

Error can observed at seemingly random iterations. There might be runs that pass without issue or there are runs that fail in the first couple iterations. It is seemingly caused by `H5ESwait()` checking which events in the event set need to waited on causing it to access an area outside of mem. But then there can also me tens of rounds not exhibiting this error at all.

This can also lead to a deadlock caused by `[ASYNC VOL ERROR] get_n_running_task_in_queue_obj with ABT_mutex_lock`
```
Wait for async answer
[leucht:49896] *** Process received signal ***
[leucht:49896] Signal: Segmentation fault (11)
[leucht:49896] Signal code: Address not mapped (1)
[leucht:49896] Failing at address: 0x1d0
[leucht:49896] [ 0] /lib/x86_64-linux-gnu/libc.so.6(+0x42520)[0x7efd5486b520]
[leucht:49896] [ 1] /home/dev/spack/opt/spack/linux-ubuntu22.04-x86_64_v4/gcc-11.4.0/hdf5-vol-async-1.7-vbevlbxizecl24eswhgtycejo4lbfvft/lib/libh5async.so(get_n_running_task_in_queue_obj+0x118)[0x7efd537c8758]
[leucht:49896] [ 2] /home/dev/spack/opt/spack/linux-ubuntu22.04-x86_64_v4/gcc-11.4.0/hdf5-vol-async-1.7-vbevlbxizecl24eswhgtycejo4lbfvft/lib/libh5async.so(+0x2306a)[0x7efd537e206a]
[leucht:49896] [ 3] /home/dev/spack/opt/spack/linux-ubuntu22.04-x86_64_v4/gcc-11.4.0/hdf5-1.14.5-5tlcfqadprf4tpamuxv4tvn67bcastlj/lib/libhdf5.so.310(H5VL_request_wait+0x40)[0x7efd54db41b0]
[leucht:49896] [ 4] /home/dev/spack/opt/spack/linux-ubuntu22.04-x86_64_v4/gcc-11.4.0/hdf5-1.14.5-5tlcfqadprf4tpamuxv4tvn67bcastlj/lib/libhdf5.so.310(+0x12ac9f)[0x7efd54b82c9f]
[leucht:49896] [ 5] /home/dev/spack/opt/spack/linux-ubuntu22.04-x86_64_v4/gcc-11.4.0/hdf5-1.14.5-5tlcfqadprf4tpamuxv4tvn67bcastlj/lib/libhdf5.so.310(H5ES__list_iterate+0x31)[0x7efd54b83b41]
[leucht:49896] [ 6] /home/dev/spack/opt/spack/linux-ubuntu22.04-x86_64_v4/gcc-11.4.0/hdf5-1.14.5-5tlcfqadprf4tpamuxv4tvn67bcastlj/lib/libhdf5.so.310(H5ES__wait+0x54)[0x7efd54b83904]
[leucht:49896] [ 7] /home/dev/spack/opt/spack/linux-ubuntu22.04-x86_64_v4/gcc-11.4.0/hdf5-1.14.5-5tlcfqadprf4tpamuxv4tvn67bcastlj/lib/libhdf5.so.310(H5ESwait+0xc9)[0x7efd54b815a9]
[leucht:49896] [ 8] ./a.out(+0x508f)[0x55b54ea8a08f]
[leucht:49896] [ 9] ./a.out(+0x5ad7)[0x55b54ea8aad7]
[leucht:49896] [10] /lib/x86_64-linux-gnu/libc.so.6(+0x29d90)[0x7efd54852d90]
[leucht:49896] [11] /lib/x86_64-linux-gnu/libc.so.6(__libc_start_main+0x80)[0x7efd54852e40]
[leucht:49896] [12] ./a.out(+0x28c5)[0x55b54ea878c5]
[leucht:49896] *** End of error message ***
--------------------------------------------------------------------------
prterun noticed that process rank 0 with PID 49896 on node leucht exited on
signal 11 (Segmentation fault).
--------------------------------------------------------------------------
```

Issue might be related to `hdf5-vol-async version 1.7`. Unclear if it can be reproduced using `develop` version but causes significant performance regression.

This issue was somewhat fixed with updating to and unreleases version of the spack packages `develop` but with significant cost to performance hence the call to `somewhat fixed`.

## Additional Information

This section provides additional information, knowledge and examples gather during the time working on the project.

TODO