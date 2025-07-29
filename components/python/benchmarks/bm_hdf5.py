from func import datastruct as ds
import json

def bench_hdf5(iterations, variable=None):
    
    if variable == None:
        variable = []
        with open("components/python/data/tmp/run_config.json") as json_file:
            tmp = json.load(json_file)  

            for keys in tmp.keys():
                variable.append(keys)  
        
    ds_hdf5 = ds.Datastruct()
    ds_hdf5.open(mode="r+", engine="hdf5", path="components/python/data/datasets/test_dataset.h5")
    ds_hdf5.read("bench_complete", variable=variable, iterations=iterations)
    ds_hdf5.dataset.close()
    
    with open("components/python/data/results/test-hdf5-python.json", "w") as f:
        json.dump(ds_hdf5.log, f)
 
 
def bench_parallel_hdf5(iterations, variable=None):
    
    from mpi4py import MPI
    
    if variable == None:
        variable = []
        with open("components/python/data/tmp/run_config.json") as json_file:
            tmp = json.load(json_file)  

            for keys in tmp.keys():
                variable.append(keys)  
        
    ds_hdf5 = ds.Datastruct()
    ds_hdf5.open(mode="r+", engine="hdf5", path="components/python/data/datasets/test_dataset.h5", parallel=True)
    ds_hdf5.read("bench_complete_parallel", variable=variable, iterations=iterations)
    ds_hdf5.dataset.close()
    
    if MPI.COMM_WORLD.rank == 0:
        with open("components/python/data/results/test-hdf5-python-parallel.json", "w") as f:
            json.dump(ds_hdf5.log, f)