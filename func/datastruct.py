import netCDF4, zarr, h5py
import numpy as np

class Datastruct:
    
    
    def __init__(self, path=str, shape=(), chunks=(), mode=str, engine=str, compression=str, dataset=any):
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
            temperature = root.create_array(name="temperature", shape=shape, chunks=chunks, dtype="float64")
            humidity = root.create_array(name="humidity", shape=shape, chunks=chunks, dtype="float64")
            
            temperature[:, :, :] = np.random.random_sample((512, 512, 512))
            humidity[:, :, :] = np.random.random_sample((512, 512, 512))
            
            self.dataset = root
            
        if engine =="hdf5":
            
            if type(path) == str:
                self.path = path
                
            
            
            return print("not implemented")
            
        if engine == "netcdf4":
            
            if type(path) == str:
                self.path = path
                
            return print("not implemented")
        
        
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