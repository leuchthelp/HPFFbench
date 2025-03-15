import func.datastruct as ds
from func.datastruct import bcolors as color
import os
import pandas as pd
import shutil
import subprocess

from mpi4py import MPI

def create_ds(form, parallel=False):
    ds_zarr = ds.Datastruct()
    ds_hdf5 = ds.Datastruct()
    ds_netcdf4 = ds.Datastruct()
    #new.create(path="data/test_dataset.zarr", shape=(512, 512, 512), chunks=(512, 512, 8), mode="r+", engine="zarr")
    
    if parallel is False or MPI.COMM_WORLD.rank == 0:
        if os.path.exists("data/datasets/test_dataset.zarr"):
            shutil.rmtree("data/datasets/test_dataset.zarr")
        else:
            print(f"{color.WARNING}The file does not exist{color.ENDC}")
            
        if os.path.exists("data/datasets/test_dataset.nc"):
            os.remove("data/datasets/test_dataset.nc")
        else:
            print(f"{color.WARNING}The file does not exist{color.ENDC}")
            
        if os.path.exists("data/datasets/test_dataset.h5"):
            os.remove("data/datasets/test_dataset.h5")
        else:
            print(f"{color.WARNING}The file does not exist{color.ENDC}")

    print(f"{color.WARNING}Creating zarr{color.ENDC}")
    ds_zarr.create(path="data/datasets/test_dataset.zarr", form=form, engine="zarr", parallel=parallel)
    print(f"{color.WARNING}Creating hdf5{color.ENDC}")
    ds_hdf5.create(path="data/datasets/test_dataset.h5", form=form, engine="hdf5", parallel=parallel)
    print(f"{color.WARNING}Creating netcdf4{color.ENDC}")
    ds_netcdf4.create(path="data/datasets/test_dataset.nc", form=form, engine="netcdf4", parallel=parallel)
    
    
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

    return (res, size)


def bench_variable(setup, df, variable, iterations, mpi_ranks):
    index = 0
    
    for run in setup.values():
        
        shape = run[variable][0]
        chunks = run[variable][1]
        
        if len(chunks) != 0:
            size_chunks = calc_chunksize(chunks=chunks)
        else:
            size_chunks = calc_chunksize(chunks=shape)
        
        print(f"{color.WARNING}create Datasets for variable: {variable} with shape: {shape} and chunks: {chunks}, filesize per chunk: {size_chunks[0]} {size_chunks[1]}{color.ENDC}")
        create_ds(form=run)
        
        print(f"{color.OKBLUE}bench zarr with shape: {shape} and chunks: {chunks}, filesize per chunk: {size_chunks[0]} {size_chunks[1]}{color.ENDC}")
        ds_zarr = ds.Datastruct()
        ds_zarr.open(mode="r+", engine="zarr", path="data/datasets/test_dataset.zarr")
        ds_zarr.read("bench_variable", variable=variable, iterations=iterations)
        
        tmp = pd.DataFrame(data={"time taken": ds_zarr.log, "format": f"{ds_zarr.engine}-{shape}-{chunks}", "run":index, "engine": ds_zarr.engine, "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
        df = pd.concat([df, tmp], ignore_index=True)
        
        print(f"{color.OKBLUE}bench netcdf4 with shape: {shape} and chunks: {chunks}, filesize per chunk:  {size_chunks[0]} {size_chunks[1]}{color.ENDC}")
        ds_netcdf4 = ds.Datastruct()
        ds_netcdf4.open(mode="r+", engine="netcdf4", path="data/datasets/test_dataset.nc")
        ds_netcdf4.read("bench_variable", variable=variable, iterations=iterations)
        ds_netcdf4.dataset.close()
        
        tmp = pd.DataFrame(data={"time taken": ds_netcdf4.log, "format": f"{ds_netcdf4.engine}-{shape}-{chunks}", "run":index, "engine": ds_netcdf4.engine, "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
        df= pd.concat([df, tmp], ignore_index=True)
        
        print(f"{color.OKBLUE}bench hdf5 with shape: {shape} and chunks: {chunks}, filesize per chunk: {size_chunks[0]} {size_chunks[1]}{color.ENDC}")
        ds_hdf5 = ds.Datastruct()
        ds_hdf5.open(mode="r+", engine="hdf5", path="data/datasets/test_dataset.h5")
        ds_hdf5.read("bench_variable", variable=variable, iterations=iterations)
        ds_hdf5.dataset.close()

        tmp = pd.DataFrame(data={"time taken": ds_hdf5.log, "format": f"{ds_hdf5.engine}-{shape}-{chunks}", "run":index, "engine": ds_hdf5.engine, "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
        df = pd.concat([df, tmp], ignore_index=True)
        
        filesize = shape[0]
        c_chunks = []
        c_filesize = calc_chunksize(chunks=shape)
        
        
        # netcd-c
        p = subprocess.Popen(f"./a.out -b 2 -i {iterations} -s {filesize}".split(), cwd="./c-stuff")
        p.wait()
        tmp = pd.read_json("./c-stuff/test_netcdf4.json")
        df_netcdf4_c = tmp["netcdf4-read"].tolist()

        tmp = pd.DataFrame(data={"time taken": df_netcdf4_c, "format": f"netcdf4-c-{filesize}-{filesize}", "run":index, "engine": "netcdf4-c", "filesize per chunk": f"{c_filesize[0]} {c_filesize[1]}"})
        df = pd.concat([df, tmp], ignore_index=True)  

        # hdf-c
        p = subprocess.Popen(f"./a.out -b 1 -i {iterations} -s {filesize}".split(), cwd="./c-stuff")
        p.wait()
        
        tmp= pd.read_json("./c-stuff/test_hdf5-c.json")
        df_hdf5_c = tmp["hdf5-c-read"].tolist()
        
        tmp = pd.DataFrame(data={"time taken": df_hdf5_c, "format": f"hdf5-c-{filesize}-{c_chunks}", "run":index, "engine": "hdf5-c", "filesize per chunk": f"{c_filesize[0]} {c_filesize[1]}"})
        df = pd.concat([df, tmp], ignore_index=True) 

        # hdf-c-parallel
        p = subprocess.Popen(f"mpiexec -n {mpi_ranks} ./a.out -b 4 -i {iterations} -s {filesize}".split(), cwd="./c-stuff")
        p.wait()
        
        tmp= pd.read_json("./c-stuff/test_hdf5-c_parallel.json")
        df_hdf5_c_parallel = tmp["hdf5-c-read-parallel"].tolist()

        tmp = pd.DataFrame(data={"time taken": df_hdf5_c_parallel, "format": f"hdf5-c-parallel{filesize}-{c_chunks}", "run":index, "engine": "hdf5-c-parallel", "filesize per chunk": f"{c_filesize[0]} {c_filesize[1]}"})
        df = pd.concat([df, tmp], ignore_index=True) 

        # hdf5-c-async
        p = subprocess.Popen(f"mpiexec -n {mpi_ranks} ./a.out -b 5 -i {iterations} -s {filesize}".split(), cwd="./c-stuff")
        p.wait()
        
        tmp = pd.read_json("./c-stuff/test_hdf5-c_async.json")
        df_hdf5_async = tmp["hdf5-c-async-read"].tolist()

        tmp = pd.DataFrame(data={"time taken": df_hdf5_async, "format": f"hdf5-async-{filesize}-{c_chunks}", "run":index, "engine": "hdf5-async", "filesize per chunk": f"{c_filesize[0]} {c_filesize[1]}"})
        df = pd.concat([df, tmp], ignore_index=True)

        # hdf5-c-subfiling
        p = subprocess.Popen(f"mpiexec -n {mpi_ranks} ./a.out -b 6 -i {iterations} -s {filesize}".split(), cwd="./c-stuff")
        p.wait()

        tmp = pd.read_json("./c-stuff/test_hdf5_subfiling.json")
        df_hdf5_subfiling = tmp["hdf5-subfiling-read"].tolist()

        tmp = pd.DataFrame(data={"time taken": df_hdf5_subfiling, "format": f"hdf5-subfiling-{filesize}-{c_chunks}", "run":index, "engine": "hdf5-subfiling", "filesize per chunk": f"{c_filesize[0]} {c_filesize[1]}"})
        df = pd.concat([df, tmp], ignore_index=True) 
        
        index +=1
        df.to_json("data/plotting/plotting_bench_variable.json")
    

def bench_complete(setup, df):
    index = 0
    
    for run in setup.values():
        
        variable = []
        shape = []
        chunks = []
        size_chunks = []
                
        for key in run.keys():
            variable.append(key)
            shape.append(run[key][0])
            chunks.append(run[key][1])
            
        for i in range(len(chunks)):    
            tmp = calc_chunksize(chunks=chunks[i])
            size_chunks.append(tmp)
            
    
        print(f"{color.WARNING}create Datasets for variables: {variable} with shape: {shape} and chunks: {chunks}, filesize per chunk: {size_chunks}{color.ENDC}")
        create_ds(form=run)
        
        print(f"{color.OKBLUE}bench zarr for variables: {variable} with shape: {shape} and chunks: {chunks}, filesize per chunk: {size_chunks}{color.ENDC}")
        ds_zarr = ds.Datastruct()
        ds_zarr.open(mode="r+", engine="zarr", path="data/datasets/test_dataset.zarr")
        ds_zarr.read("bench_complete", variable=variable, iterations=10)
        
        tmp = pd.DataFrame(data={"time taken": ds_zarr.log, "format": f"{ds_zarr.engine}-{shape}-{chunks}", "run":index, "engine": ds_zarr.engine})
        df = pd.concat([df, tmp], ignore_index=True)
        
        print(f"{color.OKBLUE}bench netcdf4 for variables: {variable} with shape: {shape} and chunks: {chunks}, filesize per chunk: {size_chunks}{color.ENDC}")
        ds_netcdf4 = ds.Datastruct()
        ds_netcdf4.open(mode="r+", engine="netcdf4", path="data/datasets/test_dataset.nc")
        ds_netcdf4.read("bench_complete", variable=variable, iterations=10)
        
        tmp = pd.DataFrame(data={"time taken": ds_netcdf4.log, "format": f"{ds_netcdf4.engine}-{shape}-{chunks}", "run":index, "engine": ds_netcdf4.engine})
        df= pd.concat([df, tmp], ignore_index=True)
        
        
        print(f"{color.OKBLUE}bench hdf5 for variables: {variable} with shape: {shape} and chunks: {chunks}, filesize per chunk: {size_chunks}{color.ENDC}")
        ds_hdf5 = ds.Datastruct()
        ds_hdf5.open(mode="r+", engine="hdf5", path="data/datasets/test_dataset.h5")
        ds_hdf5.read("bench_complete", variable=variable, iterations=10)

        tmp = pd.DataFrame(data={"time taken": ds_hdf5.log, "format": f"{ds_hdf5.engine}-{shape}-{chunks}", "run":index, "engine": ds_hdf5.engine})
        df = pd.concat([df, tmp], ignore_index=True)
        
        index +=1
    
    
    df.to_json("data/plotting/plotting_bench_complete.json")
    
    variable = ["X"]
    shape = [134217728]
    chunks = [134217728]
    size_chunks = []
    
    index = 1
    
    for i in range(len(chunks)):    
            tmp = calc_chunksize(chunks=chunks[i])
            size_chunks.append(tmp)
    
    print(f"{color.OKBLUE}bench zarr for variables: {variable} with shape: {shape} and chunks: {chunks}, filesize per chunk: {size_chunks}{color.ENDC}")
    ds_tmp = ds.Datastruct()
    ds_tmp.engine = "async_hdf5-c"
    ds_tmp.read("bench_async_c", iterations=10) 
    
    tmp = pd.DataFrame(data={"time taken": ds_tmp.log, "format": f"{ds_tmp.engine}-{shape}-{chunks}", "run":index, "engine": ds_tmp.engine})
    df = pd.concat([df, tmp], ignore_index=True) 
    
    
    df.to_json("data/plotting/plotting_bench_async-c.json") 
 
        
def main():
    
    iterations = 10
    variable = "X"
    mpi_ranks = 4
    
    setup = {
            "run01": {"X": ([1 * 134217728], [])},
            "run02": {"X": ([2 * 134217728], [])},
            "run03": {"X": ([3 * 134217728], [])},
            "run04": {"X": ([4 * 134217728], [])},
            "run05": {"X": ([5 * 134217728], [])},
            "run06": {"X": ([6 * 134217728], [])},
            "run07": {"X": ([7 * 134217728], [])},
            "run08": {"X": ([8 * 134217728], [])},
            "run09": {"X": ([9 * 134217728], [])},
            "run10": {"X": ([10 * 134217728], [])},
            "run11": {"X": ([20 * 134217728], [])},
            "run12": {"X": ([30 * 134217728], [])},
            "run13": {"X": ([40 * 134217728], [])},
            "run14": {"X": ([50 * 134217728], [])},
            "run15": {"X": ([60 * 134217728], [])},
            "run16": {"X": ([70 * 134217728], [])},
            "run17": {"X": ([80 * 134217728], [])},
            "run18": {"X": ([90 * 134217728], [])},
            "run19": {"X": ([100 * 134217728], [])},
            
            
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