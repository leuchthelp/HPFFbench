import netCDF4, zarr, h5py
import numpy as np

class Datastruct:
    
    
    def __init__(self, path=None, shape=(10), chunks=(10), mode=None, engine=None, compression=None, dataset=any):
        self.path = path
        self.shape = shape
        self.chunks = chunks
        self.mode = mode
        self.engine = engine
        self.compression = compression
        self.dataset = dataset
        
    
    def create(self, path, shape, chunks, engine):
            
        if type(engine) == str:
            self.engine = engine
            
        if engine == "zarr":
            
            if type(path) == str:
                self.path = path
            
            root = zarr.create_group(store=path, zarr_format=3, overwrite=True)
            x = root.create_array(name="X", shape=shape, chunks=chunks, dtype="f8")
            y= root.create_array(name="Y", shape=shape, chunks=chunks, dtype="f8")
            
            x[:, :, :] = np.random.random_sample(shape)
            y[:, :, :] = np.random.random_sample(shape)
            
            self.dataset = root
            return self
            
        if engine =="hdf5":
            
            if type(path) == str:
                self.path = path
                
            root = h5py.File(path, "w-")
            x = root.create_dataset("X", shape=shape,chunks=chunks, dtype="f8")
            y = root.create_dataset("Y", shape=shape, chunks=chunks, dtype="f8")
            
            x[:, :, :] = np.random.random_sample(shape)
            y[:, :, :] = np.random.random_sample(shape)
            
            self.dataset = root
            root.close()
            return self
            
        if engine == "netcdf4":
            
            if type(path) == str:
                self.path = path
                
            root = netCDF4.Dataset(path, "w", format="NETCDF4")
            grp = root.createGroup("/")
            u = root.createDimension("u", 512)
            v = root.createDimension("v", 512)
            w = root.createDimension("w", 512)
            
            x = root.createVariable("X", "f8", ("u", "v", "w"), chunksizes=chunks)
            y = root.createVariable("Y", "f8", ("u", "v", "w"), chunksizes=chunks)
            
            x = np.random.random_sample(shape)
            y = np.random.random_sample(shape)
                
            self.dataset = root
            root.close()
            return self
        
        
    def open(self, mode, engine = None | str, path = None | str):
        
        if type(path) == str:
            self.path = path
            
        if type(engine) == str:
            self.engine = engine
        
        if type(mode) == str:
            self.mode = mode
            
        if self.engine == "zarr":
            
            self.dataset = zarr.open(self.path, mode=self.mode ,zarr_version=3)
            
        if self.engine =="hdf5":
            
            self.dataset = h5py.File(self.path, mode=self.mode)
            
        if self.engine == "netcdf4":
                
            self.dataset = netCDF4.Dataset(self.path, mode=self.mode, format="NETCDF4")
        
        return self
        
    
    def read(self, chunk):
    
        if self.engine == "zarr":
            return self.dataset
        
        if self.engine == "hdf5":
            return 0
            
        if self.engine == "netcdf4":
            return 0