from dataclasses import dataclass
from func.datastruct import bcolors
from python.benchmarks import BenchmarkManager
from pathlib import Path
import itertools
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
        
        parallel = False
        try:
            parallel = self.config["parallel"] 
            if parallel != "Both" and type(parallel) is not bool: raise ValueError(bcolors.FAIL + "\"parallel\" can only either be \"True\", \"False\" or \"Both\"" + bcolors.ENDC)
            
        except KeyError:
            print(bcolors.WARNING + f"\"parallel\" is unset! Be aware parallel will be automatically set to False as long as it remains unset. You will be unable to run parallelized benchmarks until you set it to True." + bcolors.ENDC)   
        

        if parallel == "Both":
            self._compare_capabilities(parallel=False, determined_cap=determined_cap)
            self._compare_capabilities(parallel=True, determined_cap=determined_cap)
        else:
            self._compare_capabilities(parallel=parallel, determined_cap=determined_cap)
             
             
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
                with open(path, "r") as file:
                    current = yaml.safe_load(file)
                    
                    tmp = []
                    
                    try:
                        tmp.append(("parallel", current["parallel"]))
                    except KeyError:
                        tmp.append(("parallel", False))
                        
                    try:
                        tmp.append(("par_backend", current["par_backend"]))
                    except KeyError:
                        tmp.append(("par_backend", None))
                    
                    try:
                        tmp.append(("language", current["language"]))
                    except yaml.YAMLError as e:
                        raise e
                     
                    try: 
                        tmp.append(("format", current["format"]))
                    except KeyError as e:
                        raise e
                    
                    try:
                        src = current["source"]
                    except KeyError as e:
                        raise e
                                        
                    determined.append((dict(tmp), src))   

        return determined
        
    
    def _compare_capabilities(self, parallel: str | bool, determined_cap: list):
        requested_cap = self._requested_capabilities(parallel=parallel)
        
        for requested in [*requested_cap]: 
            #print(f"requested: {dict(requested)}")
            #print(f"determined: {determined_cap}")
            requested = dict(requested)
            for determined in determined_cap:
                if requested == determined[0]:
                    print(bcolors.OKGREEN + f"Success" + bcolors.ENDC)
                    self._create_benchmark_manager(requested=requested, src=determined[1])
    
    
    def _requested_capabilities(self, parallel: bool):
        requested   = None
        
        languages    = []
        for langauge in self.config["languages"]:
            languages.append(("language", langauge))
        
        formats      = []
        for format in self.config["formats"]:
            formats.append(("format", format))
            
        par_backends = [("par_backend", None)]
        
        if parallel is True:
            par_backends = []
            if type(self.config["par_backend"]) is not list:
                    par_backends.append(("par_backend", self.config["par_backend"]))
            else:
                for par_backend in self.config["par_backend"]:
                    par_backends.append(("par_backend", par_backend))
        
        requested = itertools.product(*[[("parallel", parallel)], par_backends, languages, formats])

        return requested
        
                                             
    def _create_benchmark_manager(self, requested: dict, src: str):
        for _, run in self.config["runs"].items():
            
            parallel    = requested["parallel"]
            par_backend = requested["par_backend"]
            language    = requested["language"]
            format      = requested["format"]
            range       = self.config["range"]
            stepsize    = self.config["stepsize"]
            iterations  = self.config["iterations"]
                    
            print(bcolors.OKBLUE + f"Managing Benchmark with; file-structure: {run} parallel: {parallel}, par_backend: {par_backend}, language: {language}, format: {format}, range: {range}, stepsize: {stepsize} and {iterations} iterations" + bcolors.ENDC)
            BenchmarkManager(handler_id=str(self.__uuid), run=run, parallel=parallel, par_backend=par_backend, language=language, format=format, range=range, stepsize=stepsize, iterations=iterations, src=src)              
            
    
    def _check_mpi(self):
        from mpi4py import MPI
    
    
    def _check_dask(self):
        try:
            print("Import Dask (mock)")
        except ImportError:
            raise ImportError(bcolors.FAIL + f"Dask not present, please install Dask." + bcolors.ENDC)