import netCDF4, zarr, h5py, time
import numpy as np

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
        self.parallel = parallel
        
    
    def create(self, path, form, engine, dtype="f8", parallel=False):
        from mpi4py import MPI

        if type(engine) == str:
            self.engine = engine
            
        self.parallel = parallel            
            
        match self.engine:
            case "zarr":
                if type(path) == str:
                    self.path = path
                
                if MPI.COMM_WORLD.rank == 0 or parallel == False:
                    root = zarr.create_group(store=path, zarr_format=3, overwrite=True)

                    for variable, element in form.items():
                        shape = element[0]
                        chunks = element[1]
                        
                        if len(chunks) != 0:
                            x = root.create_array(name=variable, shape=shape, chunks=chunks, dtype=dtype)
                        else: 
                            x = root.create_array(name=variable, shape=shape, dtype=dtype)
                        
                        x[:] = np.random.random_sample(shape)

                    self.dataset = root
                    print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
            
        
            case "hdf5":
                if type(path) == str:
                    self.path = path
                
                match parallel:
                    case True:
                        print(f"{bcolors.WARNING}Creating hdf5 file{bcolors.ENDC}")
                        root = h5py.File(path, "w-", driver="mpio", comm=MPI.COMM_WORLD)
                    case False:
                        root = h5py.File(path, "w-")

                for variable, element in form.items():      
                    shape = element[0]
                    chunks = element[1]
                    
                    if len(chunks) != 0: 
                        x = root.create_dataset(variable, shape=shape, chunks=tuple(chunks), dtype=dtype)
                    else:
                        x = root.create_dataset(variable, shape=shape, dtype=dtype)
                    
                    if MPI.COMM_WORLD.rank == 0 or parallel == False:
                        x[:] = np.random.random_sample(shape)
                    
                self.dataset = root
                root.close()
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
            
        
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
                    
                    if len(chunks) != 0: 
                        x = root.createVariable(variable, dtype, dimensions, chunksizes=chunks)
                    else: 
                        x = root.createVariable(variable, dtype, dimensions)
                    
                    if MPI.COMM_WORLD.rank == 0 or parallel == False:
                        x[:] = np.random.random_sample(shape)
                    
                self.dataset = root
                root.close()
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
                
        return self
        
        
    def open(self, mode, engine = None | str, path = None | str, parallel=False):
        from mpi4py import MPI
        
        self.parallel = parallel
        
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
                
                if self.parallel: 
                    self.dataset = h5py.File(self.path, mode=self.mode, driver="mpio", comm=MPI.COMM_WORLD)
                else:
                    self.dataset = h5py.File(self.path, mode=self.mode)                  
                    
            case "netcdf4":    
                self.dataset = netCDF4.Dataset(self.path, mode=self.mode, format="NETCDF4", parallel=self.parallel)

                               
        return self

    
    def __read_header(self, variable, iterations):
        
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
      
                    
    def __read_variable(self, variable, iterations):
        match self.engine:
            case "zarr":
                return self.dataset[variable][:]
                
            case "hdf5":
                return self.dataset[variable][:]
                
            case "netcdf4":
                return self.dataset.variables[variable][:] 
 
                
    def __bench_variable(self, variable, iterations):
        bench = []
        
        match self.engine:
            case "zarr":
                
                size = {self.dataset[variable].shape[0]}
                
                for i in range(iterations):
                    print(f"i: {i} for variable: {variable} for engine: {self.engine}, size: {size}")
                    start = time.monotonic()
                    self.dataset[variable][:]
                    bench.append(time.monotonic() - start)
                
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
                
            case "hdf5":
                
                size = {self.dataset[variable].shape[0]}
                
                for i in range(iterations):
                    print(f"i: {i} for variable: {variable} for engine: {self.engine}, size: {size}")
                    start = time.monotonic()
                    self.dataset[variable][:]
                    bench.append(time.monotonic() - start)
                
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
                
            case "netcdf4":
                
                size = {self.dataset[variable].shape[0]}
                
                for i in range(iterations):
                    print(f"i: {i} for variable: {variable} for engine: {self.engine}, size: {size}")
                    start = time.monotonic()
                    self.dataset[variable][:]
                    bench.append(time.monotonic() - start)
                
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
 
 
    def __bench_variable_parallel(self, variable, iterations):
        from mpi4py import MPI
        
        bench = []
        
        rank = MPI.COMM_WORLD.rank
        rsize = MPI.COMM_WORLD.size
        
        match self.engine:
            case "zarr":
                
                for i in range(iterations):
                    size = {self.dataset[variable].shape[0]}
                    print(f"i: {i} for variable: {variable} for engine: {self.engine}, rank: {rank}, size: {size}")
                    
                    if rank == 0:
                        start = time.monotonic()
                    
                    total_size = self.dataset[variable].shape[0]
                    size = int(total_size / rsize)
                    
                    rstart = rank * size
                    rend = rstart + size
                    self.dataset[variable][rstart:rend:]
                    
                    if rank == 0: 
                        bench.append(time.monotonic() - start)
                    MPI.COMM_WORLD.Barrier()
                
                self.log = bench
                
                MPI.COMM_WORLD.Barrier()
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
                
            case "hdf5":
                
                for i in range(iterations):
                    size = {self.dataset[variable].shape[0]}
                    print(f"i: {i} for variable: {variable} for engine: {self.engine}, rank: {rank}, size: {size}")
                    
                    if rank == 0:
                        start = time.monotonic()
                    
                           
                    total_size = self.dataset[variable].shape[0]
                    size = int(total_size / rsize)
                    
                    rstart = rank * size
                    rend = rstart + size
                    
                    self.dataset[variable][rstart:rend:]
                    
                    if rank == 0:
                        bench.append(time.monotonic() - start)
                    MPI.COMM_WORLD.Barrier()
                
                if rank == 0:
                    self.log = bench
                    
                MPI.COMM_WORLD.Barrier()
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
                
            case "netcdf4":
                
                for i in range(iterations):
                    size = {self.dataset[variable].shape[0]}
                    print(f"i: {i} for variable: {variable} for engine: {self.engine}, rank: {rank}, size: {size}")
                    
                    if rank == 0:
                        start = time.monotonic()
                    
                    self.dataset[variable].set_collective(True)
                    
                    total_size = self.dataset[variable].shape[0]
                    size = int(total_size / rsize)
                    
                    rstart = rank * size
                    rend = rstart + size
                    
                    self.dataset[variable][rstart:rend:]
                    
                    if rank == 0:
                        bench.append(time.monotonic() - start)
                        
                    MPI.COMM_WORLD.Barrier()
                
                if rank == 0:
                    self.log = bench
                    
                MPI.COMM_WORLD.Barrier()
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
  
  
    def __bench_complete(self, variable, iterations):
        bench = []
         
        match self.engine:
            case "zarr":
                size = {self.dataset[variable].shape[0]}
                
                for i in range(iterations):
                    print(f"i: {i} for variable: {variable} for engine: {self.engine}, , size: {size}")
                    start = time.monotonic()
                    
                    for var in variable:
                        self.dataset[var][:]
                    
                    bench.append(time.monotonic() - start)
                
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
                
            case "hdf5":
                size = {self.dataset[variable].shape[0]}
                
                for i in range(iterations):
                    print(f"i: {i} for variable: {variable} for engine: {self.engine}, , size: {size}")
                    start = time.monotonic()
                    
                    for var in variable:
                        #self.dataset[variable].read_direct(arr)
                        self.dataset[var][:]
                        
                    bench.append(time.monotonic() - start)
                
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
                
            case "netcdf4":
                size = {self.dataset[variable].shape[0]}
                
                for i in range(iterations):
                    print(f"i: {i} for variable: {variable} for engine: {self.engine}, , size: {size}")
                    start = time.monotonic()
                    
                    for var in variable:
                        self.dataset[var][:]
                    
                    bench.append(time.monotonic() - start)
                
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
 
 
    def __bench_complete_parallel(self, variable, iterations):
        from mpi4py import MPI
        
        bench = []
        rank = MPI.COMM_WORLD.rank
        rsize = MPI.COMM_WORLD.size
         
        match self.engine:
            case "zarr":
                
                for i in range(iterations):
                    if rank == rank:
                        size = {self.dataset[variable].shape[0]}
                    print(f"i: {i} for variable: {variable} for engine: {self.engine}, rank: {rank}, size: {size}")
                    
                    if rank == 0:
                        start = time.monotonic()
                    
                    for var in variable:
                        
                        total_size = self.dataset[var].shape[0]
                        size = int(total_size / rsize)
                        
                        rstart = rank * size
                        rend = rstart + size
                        self.dataset[var][rstart:rend:]
                        
                    if rank == 0: 
                        bench.append(time.monotonic() - start)
                        
                    MPI.COMM_WORLD.Barrier()
                
                self.log = bench
                
                MPI.COMM_WORLD.Barrier()
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
                
            case "hdf5":
                
                for i in range(iterations):
                    size = {self.dataset[variable].shape[0]}
                    print(f"i: {i} for variable: {variable} for engine: {self.engine}, rank: {rank}, size: {size}")
                    
                    if rank == 0:
                        start = time.monotonic()
                    
                    for var in variable:
                        
                        total_size = self.dataset[var].shape[0]
                        size = int(total_size / rsize)
                    
                        rstart = rank * size
                        rend = rstart + size
                    
                        self.dataset[var][rstart:rend:]
                    
                    if rank == 0: 
                        bench.append(time.monotonic() - start)
                        
                    MPI.COMM_WORLD.Barrier()
                
                if rank == 0:
                    self.log = bench
                    
                MPI.COMM_WORLD.Barrier()
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
                
            case "netcdf4":
                
                for i in range(iterations):
                    size = {self.dataset[variable].shape[0]}
                    print(f"i: {i} for variable: {variable} for engine: {self.engine}, rank: {rank}, size: {size}")
                    
                    if rank == 0:
                        start = time.monotonic()
                    
                    for var in variable:
                        
                        total_size = self.dataset[var].shape[0]
                        size = int(total_size / rsize)
                    
                        rstart = rank * size
                        rend = rstart + size
                    
                        self.dataset[var][rstart:rend:]
                    
                    if rank == 0:
                        bench.append(time.monotonic() - start)
                        
                    MPI.COMM_WORLD.Barrier()
                
                if rank == 0:
                    self.log = bench
                    
                MPI.COMM_WORLD.Barrier()
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")
 
 
    def __bench_sinus(self, variable, iterations):
        pass
   
    
    def __bench_calc_max(self, variable, iterations):
        match self.engine:
            case "zarr":
                self.dataset[variable]
                
            case "hdf5":
                self.dataset[variable]
                
            case "netcdf4":
                self.dataset.variables[variable]
        
      
    def read(self, pattern, variable=None, iterations=None, logging=False):
        
        patterns = {
            "header": self.__read_header,
            "variable": self.__read_variable,
            "bench_variable": self.__bench_variable,
            "bench_complete": self.__bench_complete,
            "bench_variable_parallel": self.__bench_variable_parallel,
            "bench_complete_parallel": self.__bench_complete_parallel,
        }
                
        return patterns[pattern](variable=variable, iterations=iterations)