from func.datastruct import bcolors as color
from func import datastruct as ds
from bm_hdf5 import bench_hdf5, bench_parallel_hdf5
from bm_netcdf4 import bench_netcdf4, bench_parallel_netcdf4
from bm_zarr import bench_zarr, bench_parallel_zarr
import os, shutil, json, argparse

def create_ds(form, selection, parallel=False):
    
    from mpi4py import MPI
    #new.create(path="components/python/data/test_dataset.zarr", shape=(512, 512, 512), chunks=(512, 512, 8), mode="r+", engine="zarr")
    match selection:
        case 1:
            ds_zarr = ds.Datastruct()
            
            if parallel is False or MPI.COMM_WORLD.rank == 0:
                if os.path.exists("components/python/data/datasets/test_dataset.zarr"):
                    shutil.rmtree("components/python/data/datasets/test_dataset.zarr")
                else:
                    print(f"{color.OKCYAN}The file does not exist{color.ENDC}")
            
            print(f"{color.WARNING}Creating zarr{color.ENDC}")
            ds_zarr.create(path="components/python/data/datasets/test_dataset.zarr", form=form, engine="zarr", parallel=parallel)
            
        case 2:
            ds_netcdf4 = ds.Datastruct()
            
            if parallel is False or MPI.COMM_WORLD.rank == 0:
                if os.path.exists("components/python/data/datasets/test_dataset.nc"):
                    os.remove("components/python/data/datasets/test_dataset.nc")
                else:
                    print(f"{color.OKCYAN}The file does not exist{color.ENDC}")
            
            print(f"{color.WARNING}Creating netcdf4{color.ENDC}")
            ds_netcdf4.create(path="components/python/data/datasets/test_dataset.nc", form=form, engine="netcdf4", parallel=parallel)
            
        case 3:
            ds_hdf5 = ds.Datastruct()
            
            if parallel is False or MPI.COMM_WORLD.rank == 0:
                if os.path.exists("components/python/data/datasets/test_dataset.h5"):
                    os.remove("components/python/data/datasets/test_dataset.h5")
                else:
                    print(f"{color.OKCYAN}The file does not exist{color.ENDC}")
            
            print(f"{color.WARNING}Creating hdf5{color.ENDC}")
            ds_hdf5.create(path="components/python/data/datasets/test_dataset.h5", form=form, engine="hdf5", parallel=parallel)


def create(selection, parallel=False):
    with open("components/python/data/tmp/run_config.json") as json_file:
        create_ds(json.load(json_file), selection, parallel=parallel)       
    
 
def main():

    parser = argparse.ArgumentParser(
        prog="Python Dataformat-Benchmark",
        description="run python based benchmark for Zarr, NetCDF4 and HDF5",
    )
    
    parser.add_argument("-c", "--create", type=int, default=-1, help="creates Zarr, NetCDF4 and HDF5 Files using a previously saved run format")
    parser.add_argument("-b", "--benchmark", type=int, default=-1, help="benchmark to run from selection of 1-3")
    parser.add_argument("-i", "--iterations", type=int, default=10, help="number of iterations to run the benchmark for")
    parser.add_argument("-v", "--variable", type=str, default=None, help="variable to read, if none is provided all are read")
    
    args = parser.parse_args()
    
    match args.benchmark:
        case 1:
            bench_zarr(args.iterations, args.variable)
        case 2:
            bench_netcdf4(args.iterations, args.variable)
        case 3:
            bench_hdf5(args.iterations, args.variable)
        case 4:
            bench_parallel_zarr(args.iterations, args.variable)
        case 5:
            bench_parallel_netcdf4(args.iterations, args.variable)
        case 6: 
            bench_parallel_hdf5(args.iterations, args.variable)
        case -1:
            
            if args.create != -1:
                create(args.create, False)
            else:
                print("No benchmark requested, exiting")
   
    
if __name__=="__main__":
    main()