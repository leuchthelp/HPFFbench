import netCDF4, zarr, h5py
import numpy as np
import func.dev_logging as logger
import multiprocessing as mp
import time
import timeit
from mpi4py import MPI

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
    
    
    def __init__(self, path=None, shape=[], chunks=[], mode=None, engine=None, compression=None, dataset=any, log=None, parallel=False):
        self.path = path
        self.shape = shape
        self.chunks = chunks
        self.mode = mode
        self.engine = engine
        self.compression = compression
        self.dataset = dataset
        self.log = log
        
    
    def create(self, path, form, engine, dtype="f8", parallel=False):
            
        if type(engine) == str:
            self.engine = engine
            
        if parallel == True:
            self.parallel = parallel
            
            
        match self.engine:
            case "zarr":
                if type(path) == str:
                    self.path = path
                
                root = zarr.create_group(store=path, zarr_format=3, overwrite=True)
                
                for variable, element in form.items():
                    shape = element[0]
                    chunks = element[1]
                    
                    x = root.create_array(name=variable, shape=shape, chunks=chunks, dtype=dtype)
                    x[:] = np.random.random_sample(shape)
                
                self.dataset = root
            
        
            case "hdf5":
                if type(path) == str:
                    self.path = path
                
                match parallel:
                    case True:
                        root = h5py.File(path, "w-", driver="mpio")
                    case False:
                        root = h5py.File(path, "w-")

                for variable, element in form.items():
                    shape = element[0]
                    chunks = element[1]
                    
                    x = root.create_dataset(variable, shape=shape,chunks=tuple(chunks), dtype=dtype)
                    x[:] = np.random.random_sample(shape)
                
                self.dataset = root
                root.close()
            
        
            case "netcdf4":
                if type(path) == str:
                    self.path = path
                    
                root = netCDF4.Dataset(path, "w", format="NETCDF4", parallel=parallel)
                root.createGroup("/")
                
                used = 0
                
                for variable, element in form.items():
                    shape = element[0]
                    chunks = element[1]
                    dimensions = []
                    
                    for size in shape:
                        root.createDimension(f"{used}", size)
                        dimensions.append(f"{used}")
                        used += 1
                    
                    x = root.createVariable(variable, dtype, dimensions, chunksizes=chunks)
                    x[:] = np.random.random_sample(shape)
                    
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
      
                    
    def _read_variable(self, variable, iterations):
        match self.engine:
            case "zarr":
                return self.dataset[variable][:]
                
            case "hdf5":
                return self.dataset[variable][:]
                
            case "netcdf4":
                return self.dataset.variables[variable][:] 
 
                
    def _bench_variable(self, variable, iterations):
        bench = []
         
        match self.engine:
            case "zarr":
                
                for i in range(iterations):
                    print(f"i: {i} for variable: {variable}")
                    start = time.monotonic()
                    self.dataset[variable][:]
                    bench.append(time.monotonic() - start)
                
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
                
            case "hdf5":
                
                for i in range(iterations):
                    print(f"i: {i} for variable: {variable}")
                    #arr = np.zeros((512, 512, 512))
                    start = time.monotonic()
                    #rself.dataset[variable].read_direct(arr)
                    self.dataset[variable][:]
                    bench.append(time.monotonic() - start)
                
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
                
            case "netcdf4":
                
                for i in range(iterations):
                    print(f"i: {i} for variable: {variable}")
                    start = time.monotonic()
                    self.dataset[variable][:]
                    bench.append(time.monotonic() - start)
                
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
 
  
    def _bench_complete(self, variable, iterations):
        bench = []
         
        match self.engine:
            case "zarr":
                
                for i in range(iterations):
                    print(f"i: {i} for variable: {variable}")
                    start = time.monotonic()
                    
                    for var in variable:
                        self.dataset[var][:]
                    
                    bench.append(time.monotonic() - start)
                
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
                
            case "hdf5":
                
                for i in range(iterations):
                    print(f"i: {i} for variable: {variable}")
                    #arr = np.zeros((512, 512, 512))
                    start = time.monotonic()
                    
                    for var in variable:
                        #self.dataset[variable].read_direct(arr)
                        self.dataset[var][:]
                        
                    bench.append(time.monotonic() - start)
                
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
                
            case "netcdf4":
                
                for i in range(iterations):
                    print(f"i: {i} for variable: {variable}")
                    start = time.monotonic()
                    
                    for var in variable:
                        self.dataset[var][:]
                    
                    bench.append(time.monotonic() - start)
                
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
 
 
    def _bench_sinus(self, variable, iterations):
        pass
   
    
    def _bench_calc_max(self, variable, iterations):
        match self.engine:
            case "zarr":
                self.dataset[variable]
                
            case "hdf5":
                self.dataset[variable]
                
            case "netcdf4":
                self.dataset.variables[variable]
        
    
    def read(self, pattern, variable=None, iterations=None, logging=False):
        
        patterns = {
            "header": self._read_header,
            "complete": self._read_variable,
            "bench_variable": self._bench_variable,
            "bench_complete": self._bench_complete,
        }
        
        if logging:
            proc = mp.Process(target=logger.run_logging, args=(f'{pattern}_{self.engine}_test.txt',))
            proc.start()
            print(f"pid: {proc.pid}")
            
            # give logger time to start up and get ready
            print(f"{bcolors.WARNING} take some time to set up logger{bcolors.ENDC}")
            time.sleep(3)
              
        
        res = patterns[pattern](variable=variable, iterations=iterations)
        
        if logging:
            proc.kill()
            proc.join()
            proc.close()
            pass
                
        return res