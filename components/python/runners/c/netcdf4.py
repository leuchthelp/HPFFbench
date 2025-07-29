from func.datastruct import bcolors as color
import os, subprocess
import pandas as pd

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

def runner_netcdf4_c(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index):
    # netcd-c
    filesize = shape[0]
    
    ## create netcdf4 C file - current not needed as file created by python benchmark is used
    
    ## run benchmark on netcdf4 C file
    p = subprocess.Popen(f"./a.out -b 2 -i {iterations} -s {filesize}".split(), cwd="./components/c")
    p.wait()
    tmp = pd.read_json(f".{path_py_results}/test_netcdf4.json")
    df_netcdf4_c = tmp["netcdf4-read"].tolist()
    
    tmp = pd.DataFrame(data={"time taken": df_netcdf4_c, "format": f"netcdf4-c-[{filesize}]-{chunks}", "run":index, "engine": "netcdf4-c", "total filesize": f"{total_filesize[0]} {total_filesize[1]}", "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
    df = pd.concat([df, tmp], ignore_index=True)
    
    ## delete netcdf4 file
        
    return df


def runner_netcdf4_c_parallel(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks):
    # netcdf4-c-parallel
    filesize = shape[0]
    
    ## create netcdf4 C file parallel 
    
    ## run benchmark on netcdf4 C file parallel
    p = subprocess.Popen(f"mpiexec -n {mpi_ranks} ./a.out -b 7 -i {iterations} -s {filesize}".split(), cwd="./components/c")
    p.wait()
    
    tmp= pd.read_json(f".{path_py_results}/test_netcdf4-c_parallel.json")
    df_netcdf4_c_parallel = tmp["netcdf4-c-read-parallel"].tolist()
    
    tmp = pd.DataFrame(data={"time taken": df_netcdf4_c_parallel, "format": f"netcdf4-c-parallel-[{filesize}]-{chunks}", "run":index, "engine": "netcdf4-c-parallel", "total filesize": f"{total_filesize[0]} {total_filesize[1]}", "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
    df = pd.concat([df, tmp], ignore_index=True)
    
    ## delete netcdf4 C file parallel
    if os.path.exists(f"{path_py_datasets}/test_dataset.nc"):
        os.remove(f"{path_py_datasets}/test_dataset.nc")
        
    return df