from func.datastruct import bcolors as color
import pandas as pd
import os, shutil, subprocess, json, time
    

def delete_json(path):
     if os.path.exists(path):
            os.remove(path)
        
    
def show_header(ds_tmp):
    print(f"{color.OKGREEN}check header with format: {ds_tmp.engine}{color.ENDC}")
    ds_tmp.read(pattern="header")
    
    print(f"{color.OKCYAN}check variable header with format: {ds_tmp.engine}{color.ENDC}")
    ds_tmp.read(pattern="header", variable="X")


def calc_chunksize(chunks):
    
    res = 1
    size = "Byte"
    
    for chunksize in chunks:
        res *= chunksize
    
    res *= 8
    if res > 1 * 1024 * 1024:
        res /= 1024
        size="KB"
       
    if res > 1024:
        res /= 1024
        size = "MB"
        
    if res > 1:
        res /= 1024
        size = "GB"

    return (res, size)


def runner_zarr(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index):
    ## run benchmark on zarr python file
    print(f"{color.OKBLUE}bench zarr with shape: {shape} and chunks: {chunks}, total filesize: {total_filesize[0]} {total_filesize[1]}, filesize per chunk: {size_chunks[0]} {size_chunks[1]}{color.ENDC}")
    
    #path  ="data/results/test-zarr-python.json"
    #delete_json(path)
    
    call = f"python benchmarks.py -b 1 -v {variable} -i {iterations}"
    p = subprocess.Popen(["sbatch", "slurm-scripts/run-anything.sh" , call])
    p.wait()
    
    #while not os.path.exists(path):
    #    time.sleep(wait_time)
    
    times = pd.read_json("data/results/test-zarr-python.json")[0].tolist()
    tmp = pd.DataFrame(data={"time taken": times, "format": f"zarr-python-{shape}-{chunks}", "run":index, "engine": "zarr-python", "total filesize": f"{total_filesize[0]} {total_filesize[1]}", "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
    df = pd.concat([df, tmp], ignore_index=True)
    
    ## delete zarr python file
    if os.path.exists("data/datasets/test_dataset.zarr"):
        shutil.rmtree("data/datasets/test_dataset.zarr")
        
    return df


def runner_netcdf4(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index):
    ## run benchmark on netcdf4 python file
    print(f"{color.OKBLUE}bench netcdf4 with shape: {shape} and chunks: {chunks}, total filesize: {total_filesize[0]} {total_filesize[1]}, filesize per chunk:  {size_chunks[0]} {size_chunks[1]}{color.ENDC}")
    
    #path  ="data/results/test-netcdf4-python.json"
    #delete_json(path)
    
    call = f"python benchmarks.py -b 2 -v {variable} -i {iterations}"
    p = subprocess.Popen(["sbatch", "slurm-scripts/run-anything.sh" , call])
    p.wait()
    
    #while not os.path.exists(path):
    #    time.sleep(wait_time)
    
    times = pd.read_json("data/results/test-netcdf4-python.json")[0].tolist()
    tmp = pd.DataFrame(data={"time taken": times, "format": f"netcdf4-python-{shape}-{chunks}", "run":index, "engine": "netcdf4-python", "total filesize": f"{total_filesize[0]} {total_filesize[1]}", "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
    df= pd.concat([df, tmp], ignore_index=True)
    
    ## delete netcdf4 python file - current still need for a later c run of netcdf4
    
    return df


def runner_hdf5(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index):

    ## run benchmark on hdf5 python file
    print(f"{color.OKBLUE}bench hdf5 with shape: {shape} and chunks: {chunks}, total filesize: {total_filesize[0]} {total_filesize[1]}, filesize per chunk: {size_chunks[0]} {size_chunks[1]}{color.ENDC}")
    
    #path  ="data/results/test-hdf5-python.json"
    #delete_json(path)
         
    call = f"python benchmarks.py -b 3 -v {variable} -i {iterations}"
    p = subprocess.Popen(["sbatch", "slurm-scripts/run-anything.sh" , call])
    p.wait()
    
    #while not os.path.exists(path):
    #    time.sleep(wait_time)
    
    times = pd.read_json("data/results/test-hdf5-python.json")[0].tolist()
    tmp = pd.DataFrame(data={"time taken": times, "format": f"hdf5-python-{shape}-{chunks}", "run":index, "engine": "hdf5-python", "total filesize": f"{total_filesize[0]} {total_filesize[1]}", "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
    df = pd.concat([df, tmp], ignore_index=True)
    
     ## delete hdf5 python file
    if os.path.exists("data/datasets/test_dataset.h5"):
        os.remove("data/datasets/test_dataset.h5")
        
    return df


def runner_netcdf4_c(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index):
    # netcd-c
    filesize = shape[0]
    
    ## create netcdf4 C file - current not needed as file created by python benchmark is used
    
    ## run benchmark on netcdf4 C file
    
    #path  ="c-stuff/data/results/test_netcdf4.json"
    #delete_json(path)
    
    call = f"./a.out -b 2 -i {iterations} -s {filesize}"
    p = subprocess.Popen(["sbatch", "../slurm-scripts/run-anything.sh" , call],  cwd="./c-stuff")
    p.wait()
    
    #while not os.path.exists(path):
    #    time.sleep(wait_time)
    
    tmp = pd.read_json("./c-stuff/data/results/test_netcdf4.json")
    df_netcdf4_c = tmp["netcdf4-read"].tolist()
    
    tmp = pd.DataFrame(data={"time taken": df_netcdf4_c, "format": f"netcdf4-c-{filesize}-{size_chunks}", "run":index, "engine": "netcdf4-c", "total filesize": f"{total_filesize[0]} {total_filesize[1]}", "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
    df = pd.concat([df, tmp], ignore_index=True)
    
    ## delete netcdf4 file
    if os.path.exists("data/datasets/test_dataset.nc"):
        os.remove("data/datasets/test_dataset.nc")
        
    return df
 

def runner_hdf5_c(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index):
    # hdf-c
    filesize = shape[0]

    ## create hdf5 C file
    call = f"./a.out -c 1 -s {filesize}"
    p = subprocess.Popen(["sbatch", "../slurm-scripts/run-anything.sh" , call], cwd="./c-stuff")
    p.wait()

    ## run benchmark on hdf5 C file
    
    #path  ="c-stuff/data/results/test_hdf5-c.json"
    #delete_json(path)
    
    call = f"./a.out -b 1 -i {iterations} -s {filesize}"
    p = subprocess.Popen(["sbatch", "../slurm-scripts/run-anything.sh" , call],  cwd="./c-stuff")
    p.wait()
    
    #while not os.path.exists(path):
    #    time.sleep(wait_time)

    tmp= pd.read_json("./c-stuff/data/results/test_hdf5-c.json")
    df_hdf5_c = tmp["hdf5-c-read"].tolist()

    tmp = pd.DataFrame(data={"time taken": df_hdf5_c, "format": f"hdf5-c-{filesize}-{size_chunks}", "run":index, "engine": "hdf5-c", "total filesize": f"{total_filesize[0]} {total_filesize[1]}", "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
    df = pd.concat([df, tmp], ignore_index=True) 

    ## delete hdf5 C file
    if os.path.exists("c-stuff/data/datasets/test_dataset_hdf5-c.h5"):
        os.remove("c-stuff/data/datasets/test_dataset_hdf5-c.h5")
        
    return df
  
    
def runner_hdf5_c_parallel(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks):
    # hdf-c-parallel
    filesize = shape[0]
    
    ## create hdf5 C file parallel 
    call = f"mpiexec -n  {mpi_ranks} ./a.out -c 4 -s {filesize}"
    p = subprocess.Popen(["sbatch", "../slurm-scripts/run-anything.sh" , call], cwd="./c-stuff")
    p.wait()

    
    ## run benchmark on hdf5 C file parallel
    
    #path  ="c-stuff/data/results/test_hdf5-c_parallel.json"
    #delete_json(path)
    
    call = f"mpiexec -n {mpi_ranks} ./a.out -b 4 -i {iterations} -s {filesize}"
    p = subprocess.Popen(["sbatch", "../slurm-scripts/run-anything.sh" , call],  cwd="./c-stuff")
    p.wait()
    
    #while not os.path.exists(path):
    #    time.sleep(wait_time)
    
    tmp= pd.read_json("./c-stuff/data/results/test_hdf5-c_parallel.json")
    df_hdf5_c_parallel = tmp["hdf5-c-read-parallel"].tolist()
    
    tmp = pd.DataFrame(data={"time taken": df_hdf5_c_parallel, "format": f"hdf5-c-parallel{filesize}-{size_chunks}", "run":index, "engine": "hdf5-c-parallel", "total filesize": f"{total_filesize[0]} {total_filesize[1]}", "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
    df = pd.concat([df, tmp], ignore_index=True)
    
    ## delete hdf5 C file parallel
    if os.path.exists("c-stuff/data/datasets/test_dataset_hdf5-c.h5"):
        os.remove("c-stuff/data/datasets/test_dataset_hdf5-c.h5") 
        
    return df
 
    
def runner_hdf5_c_async(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks):
    # hdf5-c-async
    filesize = shape[0]
    
    ## create hdf5-vol-async C file 
    call = f"mpiexec -n  {mpi_ranks} ./a.out -c 5 -s {filesize}"
    p = subprocess.Popen(["sbatch", "../slurm-scripts/run-anything.sh" , call], cwd="./c-stuff")
    p.wait()
    
    ## run benchmark on hdf5-vol-async C file
    
    #path  ="c-stuff/data/results/test_hdf5-c_async.json"
    #delete_json(path)
    
    call = f"mpiexec -n {mpi_ranks} ./a.out -b 5 -i {iterations} -s {filesize}"
    p = subprocess.Popen(["sbatch", "../slurm-scripts/run-anything.sh" , call],  cwd="./c-stuff")
    p.wait()
    
    #while not os.path.exists(path):
    #    time.sleep(wait_time)
    
    tmp = pd.read_json("./c-stuff/data/results/test_hdf5-c_async.json")
    df_hdf5_async = tmp["hdf5-c-async-read"].tolist()
    
    tmp = pd.DataFrame(data={"time taken": df_hdf5_async, "format": f"hdf5-async-{filesize}-{size_chunks}", "run":index, "engine": "hdf5-async", "total filesize": f"{total_filesize[0]} {total_filesize[1]}", "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
    df = pd.concat([df, tmp], ignore_index=True)
    
    ## delete hdf5-vol-async file C parallel
    if os.path.exists("c-stuff/data/datasets/test_dataset_hdf5-c_async.h5"):
        os.remove("c-stuff/data/datasets/test_dataset_hdf5-c_async.h5")
        
    return df
   
    
def runner_hdf5_c_subfiling(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks):
    # hdf5-c-subfiling
    filesize = shape[0]
    
    ## create hdf5-subfiling C file 
    call = f"mpiexec -n  {mpi_ranks} ./a.out -c 6 -s {filesize}"
    p = subprocess.Popen(["sbatch", "../slurm-scripts/run-anything.sh" , call], cwd="./c-stuff")
    p.wait()
    
    ## run benchmark on hdf5-subfiling C file
    
    #path  ="c-stuff/data/results/test_hdf5-c_subfiling.json"
    #delete_json(path)
    
    call = f"mpiexec -n {mpi_ranks} ./a.out -b 6 -i {iterations} -s {filesize}"
    p = subprocess.Popen(["sbatch", "../slurm-scripts/run-anything.sh" , call],  cwd="./c-stuff")
    p.wait()
    
    #while not os.path.exists(path):
    #    time.sleep(wait_time)
    
    tmp = pd.read_json("./c-stuff/data/results/test_hdf5_subfiling.json")
    df_hdf5_subfiling = tmp["hdf5-subfiling-read"].tolist()
    
    tmp = pd.DataFrame(data={"time taken": df_hdf5_subfiling, "format": f"hdf5-subfiling-{filesize}-{size_chunks}", "run":index, "engine": "hdf5-subfiling", "total filesize": f"{total_filesize[0]} {total_filesize[1]}", "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
    df = pd.concat([df, tmp], ignore_index=True)
    
    ## delete hdf5-subfiling C file - current not possible due to the unique structure of subfiling 
    
    return df


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
        
        with open("data/tmp/run_config.json", "w") as f:
            json.dump(run, f)
        
        ## create Zarr, NetCDF4 and HDF5 file sequentially 
        call = "python benchmarks.py -c"
        p = subprocess.Popen(["sbatch", "slurm-scripts/run-anything.sh" , call])
        p.wait()
        
        df = runner_zarr(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index)
        
        df = runner_netcdf4(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index)
        
        df = runner_hdf5(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index)
        
        
        # setup metadata for c-runs
        size_chunks = [None, None]
        total_filesize = calc_chunksize(chunks=shape)
        
        df = runner_netcdf4_c(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index)
        
        df = runner_hdf5_c(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index)
        
        df = runner_hdf5_c_parallel(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks)
        
        df = runner_hdf5_c_async(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks)
        
        df = runner_hdf5_c_subfiling(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index, mpi_ranks)
        
        
        index +=1
        df.to_json("data/plotting/plotting_bench_variable.json")

wait_time = 5
        
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
    
    bench_variable(setup, pd.DataFrame(), variable=variable, iterations=iterations, mpi_ranks=mpi_ranks)
    
    

if __name__=="__main__":
    main()