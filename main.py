import time
#from mpi4py import MPI
import xarray as xr
import numpy as np
import netCDF4

if __name__ == '__main__':

    #Todo read up on hdf5, zarr, netcdf, xarray, mpi, lustre, ceph
    # and check back with dkrz their structure, code conventions, datasets

    # Todo setup test cases proactively to ensure proper comparability and best practice

    #Todo use netcdf dataset for testing (for now) should already bet hdf5
    #dest_hdf = Dataset("data/source.nc", "w", format="NETCDF4")
    #print(dest_hdf.data_model)
    #dest_hdf.close()

    #Todo import netcdf data through hdf5 to zarr (for now)
    #dest_zarr = zarr.open_group('data/example2.zarr', mode='w')
    #zarr.copy_all(dest_hdf, dest_zarr)
    #dest_zarr.tree()

    #Todo conversion to netcdf

    #for hdf5 nothing needs to be done

    #for zarr (wip). netcdf is developing its own implementation
    # but that isn't available yet so I will work on something myself in the meantime





    #Todo setup Lustre and Ceph (need info on that)

    #Todo setup benchmark (prob compression, filesize, access-time, r/w-time) for sequential access

    #Todo setup benchmark for parallel access

    #Todo setup benchmark for random access

    #Todo setup benchmark for parallel with subfileing and async / I/O
    
    print("creating dataset")
    
    start_time = time.time()
    u = np.random.rand(1_000_000, 10, 10, 1)
    v = np.random.rand(1_000_000, 10, 10, 1)
    w = np.random.rand(1_000_000, 10, 10, 1)
    x = np.random.rand(1_000_000, 10, 10, 1)
    y = np.random.rand(1_000_000, 10, 10, 1)
    z = np.random.rand(1_000_000, 10, 10, 1)

    ds = xr.Dataset(data_vars=dict(
                                u=(["1","2","3","4"], u),
                                v=(["1","2","3","4"], v),
                                w=(["1","2","3","4"], w),
                                x=(["1","2","3","4"], x),
                                y=(["1","2","3","4"], y),
                                z=(["1","2","3","4"], z)
                                ))

    ds.to_netcdf('data/test_dataset.nc', mode="w")

    ds.to_netcdf('data/test_dataset.hdf5', mode="w", engine="h5netcdf")

    ds.to_zarr("data/test_dataset.zarr", mode="w")
    
    print("dataset creation finished")
    print("--- %s seconds ---" % (time.time() - start_time))
    
    
    # do stuff with datasets
    print("open .zarr")
    start_time = time.time()
    ds_zarr = xr.open_zarr('data/test_dataset.zarr', consolidated=True)
    print("--- %s seconds ---" % (time.time() - start_time))


    # do stuff with datasets
    print("compute some test")
    start_time = time.time()
    max_var = ds_zarr["x"].max().compute()
    print("--- %s seconds ---" % (time.time() - start_time))
    
    
    # do stuff with datasets
    print("open .nc")
    start_time = time.time()
    ds_netcdf4 = xr.open_dataset(filename_or_obj="data/test_dataset.nc", engine="h5netcdf")
    print("--- %s seconds ---" % (time.time() - start_time))
    
    
    # do stuff with datasets
    print("compute some test")
    start_time = time.time()
    max_var = ds_netcdf4["x"].max().compute()
    print("--- %s seconds ---" % (time.time() - start_time))
    
    print("finished")

