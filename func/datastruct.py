import netCDF4, zarr, h5py
import numpy as np

class Datastruct:
    
    
    def __init__(self, path=str, shape=(10), chunks=(10), mode=str, engine=str, compression=str, dataset=any):
        self.path = path
        self.mode = mode
        self.shape = shape
        self.chunks = chunks
        self.engine = engine
        self.compression = compression
        self.dataset = dataset
        
    
    def create(self, path, shape, chunks, mode, engine):
        
        if type(mode) == str:
            self.mode = mode
            
        if type(engine) == str:
            self.engine = engine
            
        if engine == "zarr":
            
            if type(path) == str:
                self.path = path
            
            root = zarr.create_group(store=path, zarr_format=3, overwrite=True)
            temperature = root.create_array(name="X", shape=shape, chunks=chunks, dtype="f8")
            humidity = root.create_array(name="Y", shape=shape, chunks=chunks, dtype="f8")
            
            temperature[:, :, :] = np.random.random_sample(shape)
            humidity[:, :, :] = np.random.random_sample(shape)
            
            self.dataset = root
            return self
            
        if engine =="hdf5":
            
            if type(path) == str:
                self.path = path
                
            f = h5py.File("data/test_dataset.h5", "r+")
            root = f.create_group("/")
            temperature = root.create_datset("X", shape=shape,chunks=chunks, dtype="f8")
            humidity = root.create_datset("Y", shape=shape, chunks=chunks, dtype="f8")
            
            temperature[:, :, :] = np.random.random_sample(shape)
            humidity[:, :, :] = np.random.random_sample(shape)
            
            self.dataset = root
            root.close()
            return self
            
        if engine == "netcdf4":
            
            if type(path) == str:
                self.path = path
                
            root = netCDF4.Dataset("data/test_dataset.nc", "r+", format="NETCDF4")
            grp = root.createGroup("/")
            time= root.createDimension("time", 512)
            level = root.createDimension("level", 512)
            lat = root.createDimension("lat", 512)
            
            temperature = root.createVariable("X", "f8", ("time", "level", "lat"), chunksize=chunks)
            humidity = root.createVariable("Y", "f8", ("time", "level", "lat"), chunksize=chunks)
            
            temperature = np.random.random_sample(shape)
            humidity = np.random.random_sample(shape)
                
            self.dataset = root
            root.close()
            return self
        
        
    def open(self, mode):
            
        if self.engine == "zarr":
            
            self.dataset = zarr.open(self.path, mode=mode ,zarr_version=3)
            
        if self.engine =="hdf5":
            
            self.dataset = h5py.File(self.path, mode="r+")
            
        if self.engine == "netcdf4":
                
            self.dataset = netCDF4.Dataset(self.path, mode="r+", format="NETCDF4")
        
    
    def read(self, chunk):
    
        if self.engine == "zarr":
            return self.dataset
        
        if self.engine == "hdf5":
            return 0
            
        if self.engine == "netcdf4":
            return 0