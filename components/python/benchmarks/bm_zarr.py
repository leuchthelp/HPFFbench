from func import datastruct as ds
import json

def bench_zarr(iterations, variable=None):
    
    if variable == None:
        variable = []
        with open("components/python/data/tmp/run_config.json") as json_file:
            tmp = json.load(json_file) 

            for keys in tmp.keys():
                variable.append(keys)
    
    ds_zarr = ds.Datastruct()
    ds_zarr.open(mode="r+", engine="zarr", path="components/python/data/datasets/test_dataset.zarr")
    ds_zarr.read("bench_complete", variable=variable, iterations=iterations)
    
    with open("components/python/data/results/test-zarr-python.json", "w") as f:
        json.dump(ds_zarr.log, f)
 
    
def bench_parallel_zarr(iterations, variable=None):
    
    from mpi4py import MPI
    
    if variable == None:
        variable = []
        with open("components/python/data/tmp/run_config.json") as json_file:
            tmp = json.load(json_file)

            for keys in tmp.keys():
                variable.append(keys)
 
    ds_zarr = ds.Datastruct()
    ds_zarr.open(mode="r+", engine="zarr", path="components/python/data/datasets/test_dataset.zarr", parallel=True)
    ds_zarr.read("bench_complete_parallel", variable=variable, iterations=iterations)
    
    if MPI.COMM_WORLD.rank == 0:
        with open("components/python/data/results/test-zarr-python-parallel.json", "w") as f:
            json.dump(ds_zarr.log, f)