from func import datastruct as ds
import json

def bench_netcdf4(iterations, variable=None):
    
    if variable == None:
        variable = []
        with open("components/python/data/tmp/run_config.json") as json_file:
            tmp = json.load(json_file)

            for keys in tmp.keys():
                variable.append(keys)
 
    ds_netcdf4 = ds.Datastruct()
    ds_netcdf4.open(mode="r+", engine="netcdf4", path="components/python/data/datasets/test_dataset.nc")
    ds_netcdf4.read("bench_complete", variable=variable, iterations=iterations)
    ds_netcdf4.dataset.close()
    
    with open("components/python/data/results/test-netcdf4-python.json", "w") as f:
        json.dump(ds_netcdf4.log, f)


def bench_parallel_netcdf4(iterations, variable=None):
    
    from mpi4py import MPI
    
    if variable == None:
        variable = []
        with open("components/python/data/tmp/run_config.json") as json_file:
            tmp = json.load(json_file)

            for keys in tmp.keys():
                variable.append(keys)
 
    ds_netcdf4 = ds.Datastruct()
    ds_netcdf4.open(mode="r+", engine="netcdf4", path="components/python/data/datasets/test_dataset.nc", parallel=True)
    ds_netcdf4.read("bench_complete_parallel", variable=variable, iterations=iterations)
    ds_netcdf4.dataset.close()
    
    if MPI.COMM_WORLD.rank == 0:
        with open("components/python/data/results/test-netcdf4-python-parallel.json", "w") as f:
            json.dump(ds_netcdf4.log, f)