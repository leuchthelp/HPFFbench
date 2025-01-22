import func.datastruct as ds

def create_ds():
    ds_zarr = ds.Datastruct()
    ds_hdf5 = ds.Datastruct()
    ds_netcdf4 = ds.Datastruct()
    #new.create(path="data/test_dataset.zarr", shape=(512, 512, 512), chunks=(512, 512, 8), mode="r+", engine="zarr")

    ds_zarr.create(path="data/datasets/test_dataset.zarr", shape=(512, 512, 512), chunks=(512, 512, 8), engine="zarr")
    ds_hdf5.create(path="data/datasets/test_dataset.h5", shape=(512, 512, 512), chunks=(512, 512, 8), engine="hdf5")
    ds_netcdf4.create(path="data/datasets/test_dataset.nc", shape=(512, 512, 512), chunks=(512, 512, 8), engine="netcdf4")


def main():

    ds_zarr = ds.Datastruct()
    ds_zarr.open(mode="r+", engine="zarr", path="data/datasets/test_dataset.zarr")
    print(ds_zarr.dataset)

if __name__=="__main__":
    main()