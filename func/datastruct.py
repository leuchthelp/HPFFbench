import netCDF4, zarr, h5py
import numpy as np
import func.dev_logging as logger
import multiprocessing as mp
import time
import timeit

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Datastruct:
    
    
    def __init__(self, path=None, shape=(), chunks=(), mode=None, engine=None, compression=None, dataset=any, log=None):
        self.path = path
        self.shape = shape
        self.chunks = chunks
        self.mode = mode
        self.engine = engine
        self.compression = compression
        self.dataset = dataset
        self.log = log
        
    
    def create(self, path, shape, chunks, engine):
            
        if type(engine) == str:
            self.engine = engine
            
        match self.engine:
            case "zarr":
                if type(path) == str:
                    self.path = path
                
                root = zarr.create_group(store=path, zarr_format=3, overwrite=True)
                x = root.create_array(name="X", shape=shape, chunks=chunks, dtype="f8")
                y= root.create_array(name="Y", shape=shape, chunks=chunks, dtype="f8")
                
                x[:, :, :] = np.random.random_sample(shape)
                y[:, :, :] = np.random.random_sample(shape)
                
                self.dataset = root
            
        
            case "hdf5":
                if type(path) == str:
                    self.path = path
                    
                root = h5py.File(path, "w-")
                x = root.create_dataset("X", shape=shape,chunks=chunks, dtype="f8")
                y = root.create_dataset("Y", shape=shape, chunks=chunks, dtype="f8")
                
                x[:, :, :] = np.random.random_sample(shape)
                y[:, :, :] = np.random.random_sample(shape)
                
                self.dataset = root
                root.close()
            
        
            case "netcdf4":
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
            
        match self.engine:
            case "zarr":
                self.dataset = zarr.open(self.path, mode=self.mode ,zarr_version=3)
            case "hdf5":
                self.dataset = h5py.File(self.path, mode=self.mode)
            case "netcdf4":    
                self.dataset = netCDF4.Dataset(self.path, mode=self.mode, format="NETCDF4")
        
        return self

    
    def _read_header(self, variable, iterations):
        
        if type(variable) == str:
            match self.engine:
                case "zarr":
                    print(self.dataset[variable].info_complete())
                
                case "hdf5":
                    print(self.dataset[variable])
                
                case "netcdf4":
                    print(self.dataset.variables[variable])
                        
        else:
            match self.engine:
                case "zarr":
                    print(self.dataset.info_complete())
                        
                case "hdf5":
                    print(self.dataset)
                        
                case "netcdf4":
                    print(self.dataset)
      
                    
    def _read_complete(self, variable, iterations):
        match self.engine:
            case "zarr":
                print(self.dataset[variable])
                
            case "hdf5":
                print(self.dataset[variable])
                
            case "netcdf4":
                print(self.dataset.variables[variable])  
                
    def _bench_complete(self, variable, iterations):
        res = None
        bench = []
         
        match self.engine:
            case "zarr":
                
                for i in range(iterations):
                    start = time.monotonic()
                    res = self.dataset[variable]
                    bench.append(start - time.monotonic())
                
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
                
            case "hdf5":
                
                for i in range(iterations):
                    start = time.monotonic()
                    res = self.dataset[variable]
                    bench.append(start - time.monotonic())
                
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
                
            case "netcdf4":
                
                for i in range(iterations):
                    start = time.monotonic()
                    res = self.dataset[variable]
                    bench.append(start - time.monotonic())
                
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
    
    def _bench_calc_max(self, variable, iterations):
        match self.engine:
            case "zarr":
                self.dataset[variable]
                
            case "hdf5":
                self.dataset[variable]
                
            case "netcdf4":
                self.dataset.variables[variable]
        
    
    def read(self, pattern, variable=None, iterations=None):
        
        patterns = {
            "header": self._read_header,
            "complete": self._read_complete,
            "bench_complete": self._bench_complete
        }
        
        if pattern not in  ("header", "complete"):
            proc = mp.Process(target=logger.run_logging, args=(f'{pattern}_{self.engine}_test.txt',))
            proc.start()
            print(f"pid: {proc.pid}")
            
            # give logger time to start up and get ready
            print(f"{bcolors.WARNING} take some time to set up logger{bcolors.ENDC}")
            time.sleep(3)
              
        
        res = patterns[pattern](variable=variable, iterations=iterations)
        
        if pattern not in  ("header", "complete"):
            proc.kill()
            proc.join()
            proc.close()
            pass
                
        return res