import func.datastruct as ds
from func.datastruct import bcolors as color

def create_ds():
    ds_zarr = ds.Datastruct()
    ds_hdf5 = ds.Datastruct()
    ds_netcdf4 = ds.Datastruct()
    #new.create(path="data/test_dataset.zarr", shape=(512, 512, 512), chunks=(512, 512, 8), mode="r+", engine="zarr")

    ds_zarr.create(path="data/datasets/test_dataset.zarr", shape=(512, 512, 512), chunks=(512, 512, 8), engine="zarr")
    ds_hdf5.create(path="data/datasets/test_dataset.h5", shape=(512, 512, 512), chunks=(512, 512, 8), engine="hdf5")
    ds_netcdf4.create(path="data/datasets/test_dataset.nc", shape=(512, 512, 512), chunks=(512, 512, 8), engine="netcdf4")
    
def show_header(ds_tmp):
    print(f"{color.OKGREEN}check header with format: {ds_tmp.engine}{color.ENDC}")
    ds_tmp.read(pattern="header")
    
    print(f"{color.OKCYAN}check variable header with format: {ds_tmp.engine}{color.ENDC}")
    ds_tmp.read(pattern="header", variable="X")


def main():
    
    #create_ds()
    
    ds_zarr = ds.Datastruct()
    ds_zarr.open(mode="r+", engine="zarr", path="data/datasets/test_dataset.zarr")
    
    ds_hdf5 = ds.Datastruct()
    ds_hdf5.open(mode="r+", engine="hdf5", path="data/datasets/test_dataset.h5")
    
    ds_netcdf4 = ds.Datastruct()
    ds_netcdf4.open(mode="r+", engine="netcdf4", path="data/datasets/test_dataset.nc")

    #show_header(ds_zarr)
    #show_header(ds_hdf5)
    #show_header(ds_netcdf4)
    
    print(ds_zarr.read("complete", variable="X").shape)
    print(ds_hdf5.read("complete", variable="X").shape)
    print(ds_netcdf4.read("complete", variable="X").shape)
    
    #ds_zarr.read("bench_complete", variable="X", iterations=10)
    #ds_hdf5.read("bench_complete", variable="X", iterations=10)
    #ds_netcdf4.read("bench_complete", variable="X", iterations=10)
    
    

if __name__=="__main__":
    main()