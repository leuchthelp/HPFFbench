from dataclasses import dataclass
from func.datastruct import bcolors
from python.benchmarks import BenchmarkManager
from pathlib import Path
import uuid
import yaml
import os.path
import asyncio


@dataclass
class Handler:
    
    """Defines handler to read configuration from yaml file and create matching benchmarks. Also configures the benchmark environments and gathers system information.
    
    Attributes
    ----------
    path_to_config: str
        Path to config.yaml which covers benchmark environments and benchmarks to run.
    
    """
    
    path_to_config: None | str
    
    
    def __init__(self, path_to_config: None | str):
        
        self.__uuid = uuid.uuid4
        self.__benchmarks = list 
        
        self._load_config(path_to_config)
        self._check_paths()
        
        determined_cap = self._determine_capabilities()
        requested_cap = self._requested_capabilities()
        
        parallel = False
        try:
            parallel = self.config["parallel"] 
            if parallel != "Both" and type(parallel) is not bool: raise ValueError(bcolors.FAIL + "\"parallel\" can only either be \"True\", \"False\" or \"Both\"" + bcolors.ENDC)
            
        except KeyError:
            print(bcolors.WARNING + f"\"parallel\" is unset! Be aware parallel will be automatically set to False as long as it remains unset. You will be unable to run parallelized benchmarks until you set it to True." + bcolors.ENDC)   
        
        
        #self._create_benchmark(parallel=parallel)
             
             
    def print_config(self):
        print(self.config)
     
        
    def print_uuid(self):
        print(self.__uuid)
    

    def _load_config(self, path_to_config):
        
        print(bcolors.OKBLUE + "Try loading config.yaml" + bcolors.ENDC)
        try:
            file = open(f"{path_to_config}config.yaml", "r")
            self.config = yaml.safe_load(stream=file)
            print(bcolors.OKGREEN + "Success loading config.yaml" + bcolors.ENDC)
        except FileNotFoundError as e:
            print(bcolors.FAIL + f"config.yaml not found, please ensure a valid config exists! Additional details: {e}" + bcolors.ENDC)
        except OSError as e:
            print(bcolors.FAIL + f"Path to config.yaml could not found, please check it is valid! Additional details: {e}" + bcolors.ENDC) 
        except yaml.YAMLError as e:
            print(bcolors.FAIL + f"Error loading config.yaml! Additional details: {e}" + bcolors.ENDC)
    
    
    def _check_paths(self):
        print(bcolors.OKBLUE + "Check configured paths" + bcolors.ENDC)
        for key, path in self.config["paths"].items():
            if not os.path.exists(path): raise ValueError(bcolors.FAIL + f"Configured path: {path} for key: {key} does not exist. Please create it." + bcolors.ENDC)
        
        print(bcolors.OKGREEN + "All paths checked successfully" + bcolors.ENDC)
        
        print(bcolors.OKBLUE + "Create benchmarks" + bcolors.ENDC)
    
    
    def _determine_capabilities(self):
        root = Path(self.config["paths"]["path_to_benchmarks"])
        
        determined = []
        
        for path in root.rglob("*"):
            
            if not path.is_dir():
                s = str(path).replace(f"{str(root)}/", "")
                features = s.rsplit("/", 1)[0].split("/")
                determined.append(features)    
                
        return determined
        
    
    def _requested_capabilities(self):
        requested = []
        
        par_backend = self.config["par_backend"]
        
        
        return requested
    
    
    def _create_benchmark(self, parallel: str | bool):
        
        if parallel == "Both":
            print(f"parallel {parallel} only matters in the future, for now ignore")
            parallel = False
        self._check_supported_languages(parallel=parallel)
    
    
    def _check_supported_par_backend(self):
        try:
            backend = {
                "MPI": self._check_mpi,
                "Dask": self._check_dask,
            }
                               
            par_backend = self.config["par_backend"]                    
            if par_backend not in backend and par_backend != "All": raise ValueError(bcolors.FAIL + f"Parallel backend \"{par_backend}\" selected is not supported. Did you mean \"All\" to run all available backends?" + bcolors.ENDC)  
            
            for imported_backend, import_func in backend.items():
                    
                if par_backend == imported_backend or par_backend == "All":
                    import_func()
                             
        except KeyError:
            raise ValueError(bcolors.FAIL + f"\"parallel\" was set to True but not parallel backend has been configured within the config.yaml. Please select one of the available backends." + bcolors.ENDC)
    
     
    def _check_supported_languages(self, parallel: bool):  
        supported = ["c", "python"]
        
        for language in self.config["languages"]:     
            if language not in supported: raise ValueError(bcolors.FAIL + f"Language: {language} not currently supported. If you want to help extend support please visit ..." + bcolors.ENDC)
            
            print(bcolors.OKBLUE + f"Language: {language} is supported" + bcolors.ENDC)
            self._check_supported_formats(language=language, parallel=parallel)
       
    
    def _check_supported_formats(self, language: str, parallel: bool):   
        supported = ["hdf5", "zarr", "netcdf4"]
        
        for format in self.config["formats"]:         
            if format not in supported: raise ValueError(bcolors.FAIL + f"Format: {format} not currently supported. If you want to help extend support please visit ..." + bcolors.ENDC)
                
            print(bcolors.OKBLUE + f"Format: {format} is supported." + bcolors.ENDC)
            self._create_benchmark_manager(language=language, format=format, parallel=parallel)
        
                                             
    def _create_benchmark_manager(self, language: str, format: str, parallel = False, par_backend = None):
        for _, run in self.config["runs"].items():
            
            range       = self.config["range"]
            stepsize    = self.config["stepsize"]
            iterations  = self.config["iterations"]
                    
            print(bcolors.OKBLUE + f"Managing Benchmark with; file-structure: {run} parallel: {parallel}, par_backend: {par_backend}, language: {language}, format: {format}, range: {range}, stepsize: {stepsize} and {iterations} iterations" + bcolors.ENDC)
            BenchmarkManager(handler_id=str(self.__uuid), run=run, parallel=parallel, par_backend=par_backend, language=language, format=format, range=range, stepsize=stepsize, iterations=iterations)              
            
    
    def _check_mpi(self):
        from mpi4py import MPI
    
    
    def _check_dask(self):
        try:
            print("Import Dask (mock)")
        except ImportError:
            raise ImportError(bcolors.FAIL + f"Dask not present, please install Dask." + bcolors.ENDC)