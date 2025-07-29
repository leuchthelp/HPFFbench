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


def runner_hdf5_c(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index):
    # hdf-c
    filesize = shape[0]

    ## create hdf5 C file
    p = subprocess.Popen(f"./a.out -c 1 -s {filesize}".split(), cwd="./components/c")
    p.wait()

    ## run benchmark on hdf5 C file
    p = subprocess.Popen(f"./a.out -b 1 -i {iterations} -s {filesize}".split(), cwd="./components/c")
    p.wait()

    tmp= pd.read_json(f".{path_py_results}/test_hdf5-c.json")
    df_hdf5_c = tmp["hdf5-c-read"].tolist()

    tmp = pd.DataFrame(data={"time taken": df_hdf5_c, "format": f"hdf5-c-[{filesize}]-{chunks}", "run":index, "engine": "hdf5-c", "total filesize": f"{total_filesize[0]} {total_filesize[1]}", "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
    df = pd.concat([df, tmp], ignore_index=True) 

    ## delete hdf5 C file
    if os.path.exists(f"{path_c_datasets}/test_dataset_hdf5-c.h5"):
        os.remove(f"{path_c_datasets}/test_dataset_hdf5-c.h5")
        
    return df
  
    
def runner_hdf5_c_parallel(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks):
    # hdf-c-parallel
    filesize = shape[0]
    
    ## create hdf5 C file parallel 
    p = subprocess.Popen(f"mpiexec -n  {mpi_ranks} ./a.out -c 4 -s {filesize}".split(), cwd="./components/c")
    p.wait()
    
    ## run benchmark on hdf5 C file parallel
    p = subprocess.Popen(f"mpiexec -n {mpi_ranks} ./a.out -b 4 -i {iterations} -s {filesize}".split(), cwd="./components/c")
    p.wait()
    
    tmp= pd.read_json(f".{path_py_results}/test_hdf5-c_parallel.json")
    df_hdf5_c_parallel = tmp["hdf5-c-read-parallel"].tolist()
    
    tmp = pd.DataFrame(data={"time taken": df_hdf5_c_parallel, "format": f"hdf5-c-parallel-[{filesize}]-{chunks}", "run":index, "engine": "hdf5-c-parallel", "total filesize": f"{total_filesize[0]} {total_filesize[1]}", "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
    df = pd.concat([df, tmp], ignore_index=True)
    
    ## delete hdf5 C file parallel
    if os.path.exists(f"{path_c_datasets}/test_dataset_hdf5-c.h5"):
        os.remove(f"{path_c_datasets}/test_dataset_hdf5-c.h5") 
        
    return df
 
    
def runner_hdf5_c_async(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks):
    # hdf5-c-async
    filesize = shape[0]
    
    ## create hdf5-vol-async C file 
    p = subprocess.Popen(f"mpiexec -n  {mpi_ranks} ./a.out -c 5 -s {filesize}".split(), cwd="./components/c")
    p.wait()
    
    ## run benchmark on hdf5-vol-async C file
    p = subprocess.Popen(f"mpiexec -n {mpi_ranks} ./a.out -b 5 -i {iterations} -s {filesize}".split(), cwd="./components/c")
    p.wait()
    
    tmp = pd.read_json(f".{path_py_results}/test_hdf5-c_async.json")
    df_hdf5_async = tmp["hdf5-c-async-read"].tolist()
    
    tmp = pd.DataFrame(data={"time taken": df_hdf5_async, "format": f"hdf5-async-[{filesize}]-{chunks}", "run":index, "engine": "hdf5-async", "total filesize": f"{total_filesize[0]} {total_filesize[1]}", "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
    df = pd.concat([df, tmp], ignore_index=True)
    
    ## delete hdf5-vol-async file C parallel
    if os.path.exists(f"{path_c_datasets}/test_dataset_hdf5-c_async.h5"):
        os.remove(f"{path_c_datasets}/test_dataset_hdf5-c_async.h5")
        
    return df
   
    
def runner_hdf5_c_subfiling(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks):
    # hdf5-c-subfiling
    filesize = shape[0]
    
    ## create hdf5-subfiling C file 
    p = subprocess.Popen(f"mpiexec -n  {mpi_ranks} ./a.out -c 6 -s {filesize}".split(), cwd="./components/c")
    p.wait()
    
    ## run benchmark on hdf5-subfiling C file
    p = subprocess.Popen(f"mpiexec -n {mpi_ranks} ./a.out -b 6 -i {iterations} -s {filesize}".split(), cwd="./components/c")
    p.wait()
    
    tmp = pd.read_json(f".{path_py_results}/test_hdf5_subfiling.json")
    df_hdf5_subfiling = tmp["hdf5-subfiling-read"].tolist()
    
    tmp = pd.DataFrame(data={"time taken": df_hdf5_subfiling, "format": f"hdf5-subfiling-[{filesize}]-{chunks}", "run":index, "engine": "hdf5-subfiling", "total filesize": f"{total_filesize[0]} {total_filesize[1]}", "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
    df = pd.concat([df, tmp], ignore_index=True)
    
    ## delete hdf5-subfiling C file - current not possible due to the unique structure of subfiling 
    
    return df