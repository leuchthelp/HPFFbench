import func.datastruct as ds
from func.datastruct import bcolors as color
import os
import pandas as pd
import shutil

def create_ds(shape, chunks):
    ds_zarr = ds.Datastruct()
    ds_hdf5 = ds.Datastruct()
    ds_netcdf4 = ds.Datastruct()
    #new.create(path="data/test_dataset.zarr", shape=(512, 512, 512), chunks=(512, 512, 8), mode="r+", engine="zarr")
    
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

    ds_zarr.create(path="data/datasets/test_dataset.zarr", shape=shape, chunks=chunks, engine="zarr")
    ds_hdf5.create(path="data/datasets/test_dataset.h5", shape=shape, chunks=chunks, engine="hdf5")
    ds_netcdf4.create(path="data/datasets/test_dataset.nc", shape=shape, chunks=chunks, engine="netcdf4")
    
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

    return res, size


def main():
    
    setup = {
            "run01":([512, 512, 512], [512, 512, 1]),
            "run02":([512, 512, 512], [512, 512, 8]),
            "run03":([512, 512, 512], [512, 512, 16]),
            "run04":([512, 512, 512], [512, 512, 32]),
            "run05":([512, 512, 512], [512, 512, 64]),
            "run06":([512, 512, 512], [512, 512, 128]),
            "run07":([512, 512, 512], [512, 512, 256]),
            "run08":([512, 512, 512], [512, 512, 512]),
            
            #"run11":([512, 512, 512], [512, 1, 1]),
            #"run12":([512, 512, 512], [512, 8, 8]),
            "run13":([512, 512, 512], [512, 16, 16]),
            "run14":([512, 512, 512], [512, 32, 32]),
            "run15":([512, 512, 512], [512, 64, 64]),
            "run16":([512, 512, 512], [512, 128, 128]),
            "run17":([512, 512, 512], [512, 256, 256]),
            "run18":([512, 512, 512], [512, 512, 512]), 
            }
    
    df_bench = pd.DataFrame()
    index = 0
    
    for run in setup.values():
        size_chunks, unit = calc_chunksize(run[1])
        
        print(f"{color.WARNING}create Datasets with shape:{run[0]} and chunks:{run[1]}, filesize per chunk: {size_chunks} {unit}{color.ENDC}")
        create_ds(shape=run[0], chunks=run[1])
        
        print(f"{color.OKBLUE}bench zarr with shape:{run[0]} and chunks:{run[1]}, filesize per chunk: {size_chunks}{color.ENDC}")
        ds_zarr = ds.Datastruct()
        ds_zarr.open(mode="r+", engine="zarr", path="data/datasets/test_dataset.zarr")
        ds_zarr.read("bench_complete", variable="X", iterations=10)
        
        tmp = pd.DataFrame(data={"time taken": ds_zarr.log, "format": f"{ds_zarr.engine}-{run[0]}-{run[1]}", "run":index, "engine": ds_zarr.engine, "filesize per chunk": size_chunks})
        df_bench = pd.concat([df_bench, tmp], ignore_index=True)
        
        print(f"{color.OKBLUE}bench netcdf4 with shape:{run[0]} and chunks:{run[1]}, filesize per chunk: {size_chunks} {unit}{color.ENDC}")
        ds_netcdf4 = ds.Datastruct()
        ds_netcdf4.open(mode="r+", engine="netcdf4", path="data/datasets/test_dataset.nc")
        ds_netcdf4.read("bench_complete", variable="X", iterations=10)
        
        tmp = pd.DataFrame(data={"time taken": ds_netcdf4.log, "format": f"{ds_netcdf4.engine}-{run[0]}-{run[1]}", "run":index, "engine": ds_netcdf4.engine, "filesize per chunk": size_chunks})
        df_bench = pd.concat([df_bench, tmp], ignore_index=True)
        
        print(f"{color.OKBLUE}bench hdf5 with shape:{run[0]} and chunks:{run[1]}, filesize per chunk: {size_chunks} {unit}{color.ENDC}")
        ds_hdf5 = ds.Datastruct()
        ds_hdf5.open(mode="r+", engine="hdf5", path="data/datasets/test_dataset.h5")
        ds_hdf5.read("bench_complete", variable="X", iterations=10)

        tmp = pd.DataFrame(data={"time taken": ds_hdf5.log, "format": f"{ds_hdf5.engine}-{run[0]}-{run[1]}", "run":index, "engine": ds_hdf5.engine, "filesize per chunk": size_chunks})
        df_bench = pd.concat([df_bench, tmp], ignore_index=True)
        
        index +=1
    
    df_bench.to_json("data/plotting/plotting_bench_complete.json")
    

if __name__=="__main__":
    main()