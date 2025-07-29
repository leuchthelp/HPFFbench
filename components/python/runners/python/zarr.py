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

def runner_zarr(df, shape, chunks, variable, iterations, total_filesize, size_chunks, index):
    ## run benchmark on zarr python file
    print(f"{color.OKBLUE}bench zarr with shape: {shape} and chunks: {chunks}, total filesize: {total_filesize[0]} {total_filesize[1]}, filesize per chunk: {size_chunks[0]} {size_chunks[1]}{color.ENDC}")
    
    p = subprocess.Popen(f"python {path_py_benchmark}/benchmarks.py -b 1 -v {variable} -i {iterations}".split())
    p.wait()
    
    times = pd.read_json(f"{path_py_results}/test-zarr-python.json")[0].tolist()
    tmp = pd.DataFrame(data={"time taken": times, "format": f"zarr-python-{shape}-{chunks}", "run":index, "engine": "zarr-python", "total filesize": f"{total_filesize[0]} {total_filesize[1]}", "filesize per chunk": f"{size_chunks[0]} {size_chunks[1]}"})
    df = pd.concat([df, tmp], ignore_index=True)
    
    ## delete zarr python file
    #if os.path.exists(f"{path_py_datasets}/test_dataset.zarr"):
    #    shutil.rmtree(f"{path_py_datasets}/test_dataset.zarr")
        
    return df