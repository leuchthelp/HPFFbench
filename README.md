Written: 17.02.2025
## Setup Project

TODO
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
engine = None
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

The predefined format required by `form` is a python dictionary `dict` which specifies the name of the variable `X` to be created, its `shape` and the chunking `chunks` for each dimension. 
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

![[image.png]]
![[image-1.png]]
![[image 1.png]]
![[image-1 1.png]]
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

 The C implementation currently consist off one file called `main.c` located in the `c-stuff` directory. The script features a similar approach to the python implementation simply lacking the `Datastruct` class due to the nature of C. The project wanted to focus on 3 important features currently only available in C, namely `HDF5-VOL-ASYNC`, ``HDF5-VOL-SUBFILING` and `NetCDF-C-NCZarr`. 

Currently available functions:

``` C
void save_to_json(double *arr, char *file_name, char *name, size_t size)
void create_hdf5(bool with_chunking)
void create_hdf5_subfiling(int argc, char **argv)
void create_hdf5_async(int argc, char **argv, bool with_chunking) 
void bench_variable_hdf5()
void bench_variable_nczarr()
void bench_variable_netcdf4()
void bench_variable_subfiling(int argc, char **argv)
void bench_variable_async(int argc, char **argv)
```

``` C
void save_to_json() 
```

Is used to generate a JSON output from a given benchmark so it can be plotted and evaluated later.

`create_` functions similarly to Python are used to create the respective Data formats with the needed functionally as `async` and `subfiling` both need different drivers to be enabled and `subfiling` uses a completely different structure from a regular `HDF5` dataset. 

Similar to Python each `bench_` function sets up and runs a benchmark for some number of `iterations` and exports the time taken for each iteration to complete as a `JSON`. Time is measure using `clock_gettime(CLOCK_MONOTONIC)`.
For more information please visit https://www.man7.org/linux/man-pages/man3/clock_gettime.3.html#top_of_page

``` C
void create_hdf5(bool with_chunking)
```

Creates a regular HDF5 file using the default backend. Additionally chunking can be enabled with `with_chunking`.

``` C
void create_hdf5_subfiling(int argc, char **argv)
```

Create a HDF5 file using `subfiling`. Within this function parameters such as `scripe_size`, `stripe_counter` which represents the amount of subfiles created and `thread_pool_size` which represents the number of MPI ranks or workers, can be changed and adjusted.

For more information on `subfiling` please visit https://github.com/HDFGroup/hdf5doc/blob/master/RFCs/HDF5_Library/VFD_Subfiling/user_guide/HDF5_Subfiling_VFD_User_s_Guide.pdf or the respective `subfiling` section which will provide for information in the future.

``` C
void create_hdf5_async(int argc, char **argv, bool with_chunking) 
```

Create a HDF5 file using `async`. 

For more information `async` please visit https://hdf5-vol-async.readthedocs.io/en/latest/  or the respective `async` section which will provide for information in the future.

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
- serial creation / reading of File using `async` - debugging
- lopping reading `async` so I can benchmark

**working on** 
- integrate c function calls in `Datastruct.py`

#### Problems

##### serial creation / reading of File using `async` - debugging - FIXED (20.02.2025)

When creating or reading a HDF5 file using `async` operation failures occur during the `async-wait` period when waiting for the async calls to finish. The function from HDF5 `H5ESwait` to perform the waiting process is designed to stop waiting and continue once a singular failed is detected.  

This problem is currently under investigation and the process can be followed here https://forum.hdfgroup.org/t/vol-async-debugging-async-operation-failures/13055/8

Sadly the functions provided by HDF to help debug operation failures lack any real examples which HDF has confirmed to be problem. 

Current process is to perform manual debugging to reverse engineer the error handling.

Manual debugging is unsuccessful in determining the root cause further assistance has been requested @ https://forum.hdfgroup.org/t/vol-async-debugging-async-operation-failures/13055/11 

It has been observed that there is some run to run variance where the async operations "magically" run without any failures.

It seems the issue was actually much much stupider than I initially thought. I just assumed `H5ESwait()` would overwrite `num_in_progress` and `op_failed` in either event of `H5ESwait()` executing successfully or unsuccessfully. 

This is not the case. `H5ESwait()` does not set `num_in_progress` or `op_failed` to something like `0` or `False` to indicate no failures have happened, it just leaves them to their default values. As I had not initialized the values, whatever random value was printed and interpreted, causing me to suspect an operation failure. This is also why there sometimes would be `0` failures, when the random value in memory happened to be `0`.

Anyway thanks, I will go cry in a corner now for not having realized this earlier.

##### lopping reading `async` so I can benchmark - FIXED (20.02.2025)

`creation` needs to be done by just one rank similarly to `closing` the event-set as otherwise the other ranks cant access it anymore. Will have to implement waiting for rank `0` for creation and rank `0` waiting for all other ranks for `closing`

## Additional Information

This section provides additional information, knowledge and examples gather during the time working on the project. 

TODO