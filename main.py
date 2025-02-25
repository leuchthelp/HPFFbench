import func.datastruct as ds
from func.datastruct import bcolors as color
import os
import pandas as pd
import shutil

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


def bench_variable(setup, df, variable):
    index = 0
    
    for run in setup.values():
        
        shape = run[variable][0]
        chunks = run[variable][1]
        
        size_chunks = calc_chunksize(chunks=chunks)
        
        print(f"{color.WARNING}create Datasets for variable: {variable} with shape: {shape} and chunks: {chunks}, filesize per chunk: {size_chunks[0]} {size_chunks[1]}{color.ENDC}")
        create_ds(form=run)
        
        print(f"{color.OKBLUE}bench zarr with shape: {shape} and chunks: {chunks}, filesize per chunk: {size_chunks[0]} {size_chunks[1]}{color.ENDC}")
        ds_zarr = ds.Datastruct()
        ds_zarr.open(mode="r+", engine="zarr", path="data/datasets/test_dataset.zarr")
        ds_zarr.read("bench_variable", variable=variable, iterations=10)
        
        tmp = pd.DataFrame(data={"time taken": ds_zarr.log, "format": f"{ds_zarr.engine}-{shape}-{chunks}", "run":index, "engine": ds_zarr.engine, "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
        df = pd.concat([df, tmp], ignore_index=True)
        
        print(f"{color.OKBLUE}bench netcdf4 with shape: {shape} and chunks: {chunks}, filesize per chunk:  {size_chunks[0]} {size_chunks[1]}{color.ENDC}")
        ds_netcdf4 = ds.Datastruct()
        ds_netcdf4.open(mode="r+", engine="netcdf4", path="data/datasets/test_dataset.nc")
        ds_netcdf4.read("bench_variable", variable=variable, iterations=10)
        
        tmp = pd.DataFrame(data={"time taken": ds_netcdf4.log, "format": f"{ds_netcdf4.engine}-{shape}-{chunks}", "run":index, "engine": ds_netcdf4.engine, "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
        df= pd.concat([df, tmp], ignore_index=True)
        
        print(f"{color.OKBLUE}bench hdf5 with shape: {shape} and chunks: {chunks}, filesize per chunk: {size_chunks[0]} {size_chunks[1]}{color.ENDC}")
        ds_hdf5 = ds.Datastruct()
        ds_hdf5.open(mode="r+", engine="hdf5", path="data/datasets/test_dataset.h5")
        ds_hdf5.read("bench_variable", variable=variable, iterations=10)

        tmp = pd.DataFrame(data={"time taken": ds_hdf5.log, "format": f"{ds_hdf5.engine}-{shape}-{chunks}", "run":index, "engine": ds_hdf5.engine, "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
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


def bench_subfiling(df):
    
    
    variable = ["X"]
    shape = [134217728]
    chunks = [134217728]
    size_chunks = []
    
    index = 1
    
    for i in range(len(chunks)):    
            tmp = calc_chunksize(chunks=chunks)
            size_chunks.append(tmp)
    
    print(f"{color.OKBLUE}bench zarr for variables: {variable} with shape: {shape} and chunks: {chunks}, filesize per chunk: {size_chunks}{color.ENDC}")
    ds_tmp = ds.Datastruct()
    ds_tmp.engine = "subfiling_hdf5-c"
    ds_tmp.read("bench_subfiling_c", iterations=10) 
    
    tmp = pd.DataFrame(data={"time taken": ds_tmp.log, "format": f"{ds_tmp.engine}-{shape}-{chunks}", "run":index, "engine": ds_tmp.engine})
    df = pd.concat([df, tmp], ignore_index=True) 
    
    
    df.to_json("data/plotting/plotting_bench_subfiling-c.json") 
 
 
def bench_async(df):
    
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
    
    setup = {
            "run01": {"X": ([512, 512, 512], [512, 512, 1]), "Y": ([10, 10], [2, 2])},
            "run02": {"X": ([512, 512, 512], [512, 512, 8]), "Y": ([10, 10], [2, 2])},
            "run03": {"X": ([512, 512, 512], [512, 512, 16]), "Y": ([10, 10], [2, 2])},
            "run04": {"X": ([512, 512, 512], [512, 512, 32]), "Y": ([10, 10], [2, 2])},
            "run05": {"X": ([512, 512, 512], [512, 512, 64]), "Y": ([10, 10], [2, 2])},
            "run06": {"X": ([512, 512, 512], [512, 512, 128]), "Y": ([10, 10], [2, 2])},
            "run07": {"X": ([512, 512, 512], [512, 512, 256]), "Y": ([10, 10], [2, 2])},
            "run08": {"X": ([512, 512, 512], [512, 512, 512]), "Y": ([10, 10], [2, 2])},
            
            #"run11": {"X": ([512, 512, 512], [512, 1, 1])},
            #"run12": {"X": ([512, 512, 512], [512, 8, 8])},
            #"run13": {"X": ([512, 512, 512], [512, 16, 16]), "Y": ([10, 10], [2, 2])},
            #"run14": {"X": ([512, 512, 512], [512, 32, 32]), "Y": ([10, 10], [2, 2])},
            #"run15": {"X": ([512, 512, 512], [512, 64, 64]), "Y": ([10, 10], [2, 2])},
            #"run16": {"X": ([512, 512, 512], [512, 128, 128]), "Y": ([10, 10], [2, 2])},
            #"run17": {"X": ([512, 512, 512], [512, 256, 256]), "Y": ([10, 10], [2, 2])},
            #"run18": {"X": ([512, 512, 512], [512, 512, 512]), "Y": ([10, 10], [2, 2])}, 
            }
    
    #bench_variable(setup, pd.DataFrame(), "X")
    
    #bench_variable(setup, pd.DataFrame(), variable="X")
    #bench_complete(setup, pd.DataFrame())
    
    #create_ds(setup["run01"], parallel=False)
    #create_ds(setup["run01"], parallel=True)
    
    
    

if __name__=="__main__":
    main()