from components.func.datastruct import bcolors as color
from components.func.dev_utils import calc_chunksize
from components.runners.c.runner_hdf5 import runner_hdf5_c, runner_hdf5_c_parallel, runner_hdf5_c_async, runner_hdf5_c_subfiling
from components.runners.c.runner_netcdf4 import runner_netcdf4_c, runner_netcdf4_c_parallel
from components.runners.python.runner_hdf5 import runner_hdf5, runner_hdf5_parallel
from components.runners.python.runner_netcdf4 import runner_netcdf4, runner_netcdf4_parallel
from components.runners.python.runner_zarr import runner_zarr
import pandas as pd
import os, shutil, subprocess, json


#paths 

path_to_c = "components/c"
path_to_python = "components/python"
path_to_visuals = "components/visualize"

path_c_benchmark = "components/c/benchmarks"
path_py_benchmark = "components/python/benchmarks"

path_c_datasets = "components/c/data/datasets"
path_py_datasets = "components/python/data/datasets"

path_c_tmp = "components/c/data/tmp"
path_py_tmp = "components/python/data/tmp"

path_c_results = "components/c/data/results"
path_py_results = "components/python/data/results"

path_plotting = "components/visualize/plotting"
    

def bench_variable(setup, df, variable, iterations, mpi_ranks):
    index = 0
    
    for run in setup.values():
        
        shape = run[variable][0]
        chunks = run[variable][1]
        
        total_filesize = calc_chunksize(chunks=shape)
        
        size_chunks = [None, None]
        if len(chunks) != 0:
            size_chunks = calc_chunksize(chunks=chunks)
        
        print(f"{color.WARNING}create Datasets for variable: {variable} with shape: {shape} and chunks: {chunks}, total filesize: {total_filesize[0]} {total_filesize[1]}, filesize per chunk: {size_chunks[0]} {size_chunks[1]}{color.ENDC}")
        with open(f"{path_py_tmp}/run_config.json", "w") as f:
            json.dump(run, f)
        
        ## create Zarr, NetCDF4 and HDF5 file sequentially 
        p = subprocess.Popen(f"python {path_py_benchmark}/benchmarks.py -c 1".split())
        p.wait()
        
        p = subprocess.Popen(f"python {path_py_benchmark}/benchmarks.py -c 2".split())
        p.wait()
        
        p = subprocess.Popen(f"python {path_py_benchmark}/benchmarks.py -c 3".split())
        p.wait()
        
        df = runner_zarr(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index)
        
        df = runner_netcdf4(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index)
        
        df = runner_hdf5(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index)
        
        df = runner_netcdf4_parallel(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks)
        
        df = runner_hdf5_parallel(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks)
        
        
        ## delete zarr python file
        if os.path.exists(f"{path_py_datasets}/test_dataset.zarr"):
            shutil.rmtree(f"{path_py_datasets}/test_dataset.zarr")
        
        ## delete hdf5 python file
        if os.path.exists(f"{path_py_datasets}/test_dataset.h5"):
            os.remove(f"{path_py_datasets}/test_dataset.h5")
        
        
        # setup metadata for c-run
        chunks = []
        size_chunks = [None, None]
        total_filesize = calc_chunksize(chunks=shape)
        
        df = runner_netcdf4_c(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index)
        
        df = runner_hdf5_c(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index)
        
        df = runner_netcdf4_c_parallel(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks)
        
        df = runner_hdf5_c_parallel(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks)
        
        df = runner_hdf5_c_async(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks)
        
        df = runner_hdf5_c_subfiling(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks)
        
        index +=1
        df.to_json(f"{path_plotting}/plotting_bench_variable.json")
 
 
def bench_python(setup, df, variable, iterations, mpi_ranks):
    index = 0
    
    for run in setup.values():
        
        shape = run[variable][0]
        chunks = run[variable][1]
        
        total_filesize = calc_chunksize(chunks=shape)
        
        size_chunks = [None, None]
        if len(chunks) != 0:
            size_chunks = calc_chunksize(chunks=chunks)
        
        print(f"{color.WARNING}create Datasets for variable: {variable} with shape: {shape} and chunks: {chunks}, total filesize: {total_filesize[0]} {total_filesize[1]}, filesize per chunk: {size_chunks[0]} {size_chunks[1]}{color.ENDC}")
        with open(f"{path_py_tmp}/run_config.json", "w") as f:
            json.dump(run, f)
        
        ## create Zarr, NetCDF4 and HDF5 file sequentially 
        p = subprocess.Popen(f"python {path_py_benchmark}/benchmarks.py -c 1".split())
        p.wait()
        
        p = subprocess.Popen(f"python {path_py_benchmark}/benchmarks.py -c 2".split())
        p.wait()
        
        p = subprocess.Popen(f"python {path_py_benchmark}/benchmarks.py -c 3".split())
        p.wait()
        
        df = runner_zarr(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index)
        
        df = runner_netcdf4(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index)
        
        df = runner_hdf5(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index)
        
        df = runner_netcdf4_parallel(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks)
        
        df = runner_hdf5_parallel(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks)
        
        
        ## delete zarr python file
        if os.path.exists(f"{path_py_datasets}/test_dataset.zarr"):
            shutil.rmtree(f"{path_py_datasets}/test_dataset.zarr")
        
        ## delete hdf5 python file
        if os.path.exists(f"{path_py_datasets}/test_dataset.h5"):
            os.remove(f"{path_py_datasets}/test_dataset.h5")
        
        index +=1
        df.to_json(f"{path_plotting}/plotting_bench_python.json")   


def bench_c(setup, df, variable, iterations, mpi_ranks):
    index = 0
    
    for run in setup.values():
        
        shape = run[variable][0]
        chunks = run[variable][1]
        
        total_filesize = calc_chunksize(chunks=shape)
        
        chunks = []
        size_chunks = [None, None]
        if len(chunks) != 0:
            size_chunks = calc_chunksize(chunks=chunks)
        
        print(f"{color.WARNING}create Datasets for variable: {variable} with shape: {shape} and chunks: {chunks}, total filesize: {total_filesize[0]} {total_filesize[1]}, filesize per chunk: {size_chunks[0]} {size_chunks[1]}{color.ENDC}")
        with open(f"{path_py_tmp}/run_config.json", "w") as f:
            json.dump(run, f)
        
        ## create Zarr, NetCDF4 and HDF5 file sequentially 
        p = subprocess.Popen(f"python {path_to_python}/benchmarks.py -c 2".split())
        p.wait()
        
        # setup metadata for c-run
        size_chunks = [None, None]
        total_filesize = calc_chunksize(chunks=shape)
        
        df = runner_netcdf4_c(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index)
        
        df = runner_hdf5_c(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index)
        
        df = runner_netcdf4_c_parallel(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks)
        
        df = runner_hdf5_c_parallel(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks)
        
        df = runner_hdf5_c_async(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks)
        
        df = runner_hdf5_c_subfiling(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks)
        
        index +=1
        df.to_json(f"{path_plotting}/plotting_bench_c.json")

   
def main():
    
    iterations = 5
    variable = "X"
    mpi_ranks = 4
    
    setup = {
            "run01": {"X": ([1 * 134217728], [])},
            "run02": {"X": ([2 * 134217728], [])},
            "run03": {"X": ([3 * 134217728], [])},
            #"run04": {"X": ([4 * 134217728], [])},
            #"run05": {"X": ([5 * 134217728], [])},
            #"run06": {"X": ([6 * 134217728], [])},
            #"run07": {"X": ([7 * 134217728], [])},
            #"run08": {"X": ([8 * 134217728], [])},
            #"run09": {"X": ([9 * 134217728], [])},
            #"run10": {"X": ([10 * 134217728], [])},
            #"run11": {"X": ([20 * 134217728], [])},
            #"run12": {"X": ([30 * 134217728], [])},
            #"run13": {"X": ([40 * 134217728], [])},
            #"run14": {"X": ([50 * 134217728], [])},
            #"run15": {"X": ([60 * 134217728], [])},
            #"run16": {"X": ([70 * 134217728], [])},
            #"run17": {"X": ([80 * 134217728], [])},
            #"run18": {"X": ([90 * 134217728], [])},
            #"run19": {"X": ([100 * 134217728], [])},
            
            
            #"run06": {"X": ([faktor * 512, 512, 512], [faktor * 512, 512, 128])},
            #"run07": {"X": ([faktor * 512, 512, 512], [faktor * 512, 512, 256])},
            #"run08": {"X": ([faktor * 512, 512, 512], [faktor * 512, 512, 512])},
            
            #"run11": {"X": ([512, 512, 512], [512, 1, 1])},
            #"run12": {"X": ([512, 512, 512], [512, 8, 8])},
            #"run13": {"X": ([512, 512, 512], [512, 16, 16]), "Y": ([10, 10], [2, 2])},
            #"run14": {"X": ([512, 512, 512], [512, 32, 32]), "Y": ([10, 10], [2, 2])},
            #"run15": {"X": ([512, 512, 512], [512, 64, 64]), "Y": ([10, 10], [2, 2])},
            #"run16": {"X": ([512, 512, 512], [512, 128, 128]), "Y": ([10, 10], [2, 2])},
            #"run17": {"X": ([512, 512, 512], [512, 256, 256]), "Y": ([10, 10], [2, 2])},
            #"run18": {"X": ([512, 512, 512], [512, 512, 512]), "Y": ([10, 10], [2, 2])}, 
            }
    
    #bench_variable(setup, pd.DataFrame(), variable=variable, iterations=iterations, mpi_ranks=mpi_ranks)
    bench_python(setup, pd.DataFrame(), variable=variable, iterations=iterations, mpi_ranks=mpi_ranks)
    #bench_c(setup, pd.DataFrame(), variable=variable, iterations=iterations, mpi_ranks=mpi_ranks)
    
    

if __name__=="__main__":
    main()