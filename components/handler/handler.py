from dataclasses import dataclass
from func.datastruct import bcolors
from python.benchmarks import BenchmarkManager
from pathlib import Path
from pathos.pools import ProcessPool
import itertools
import yaml
import hashlib


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
        
        self.__hash = None
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
        
        tasks = None
        if parallel == "Both":
            tasks = self._create_benchmark(parallel=False, determined_cap=determined_cap)
            tasks.extend(self._create_benchmark(parallel=True, determined_cap=determined_cap))
        else:
            tasks = self._create_benchmark(parallel=parallel, determined_cap=determined_cap)
         
        pool = ProcessPool(nodes=6).amap(self._run_benchmark, *tasks)
        pool.get()
        
             
    def print_config(self):
        print(self.config)
     
        
    def print_id(self):
        print(self.__hash)
    

    def _load_config(self, path_to_config):
        
        print(bcolors.OKBLUE + "Try loading config.yaml" + bcolors.ENDC)
        try:
            file = open(f"{path_to_config}config.yaml", "r")
            self.config = yaml.safe_load(stream=file)
            self.__hash = hashlib.sha256(str(path_to_config).encode()).hexdigest()
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
            if not Path(path).exists(): raise ValueError(bcolors.FAIL + f"Configured path: {path} for key: {key} does not exist. Please create it." + bcolors.ENDC)
        
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
                                        
                    determined.append((dict(tmp), current))   

        return determined
        

    def _run_benchmark(self, bm: BenchmarkManager):
        bm.run()
    
    
    def _create_benchmark(self, parallel: str | bool, determined_cap: list) -> list:
        requested_cap = self._requested_capabilities(parallel=parallel)
        
        tasks = []
        for requested in [*requested_cap]: 
            requested = dict(requested)
            for determined in determined_cap:
                if requested == determined[0]:
                    print(bcolors.OKGREEN + f"Success" + bcolors.ENDC)
                    tasks.append(self._create_benchmark_manager(requested=requested, bm_config=determined[1]))
               
        return tasks

    
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
        
                                             
    def _create_benchmark_manager(self, requested: dict, bm_config: dict) -> list:
        
        bm = []
        for _, run_config in self.config["runs"].items():
            
            datatype    = "f8"
            parallel    = requested["parallel"]
            par_backend = requested["par_backend"]
            language    = requested["language"]
            format      = requested["format"]
            use_path    = Path(self.config["paths"]["path_to_tmp"] )
            results_path= Path(self.config["paths"]["path_to_results"])
            range       = self.config["range"]
            stepsize    = self.config["stepsize"]
            iterations  = self.config["iterations"]
                    
            print(bcolors.OKBLUE + f"Managing Benchmark with; file-structure: {run_config} parallel: {parallel}, par_backend: {par_backend}, language: {language}, format: {format}, range: {range}, stepsize: {stepsize} and {iterations} iterations. It will be stored in {use_path}" + bcolors.ENDC)
            bm.append(
                BenchmarkManager(
                    handler_id=str(self.__hash), 
                    run_config=run_config, 
                    parallel=parallel, 
                    par_backend=par_backend, 
                    language=language, 
                    format=format, 
                    range=range, 
                    stepsize=stepsize, 
                    iterations=iterations, 
                    use_path=use_path, 
                    results_path=results_path, 
                    bm_config=bm_config)
                )
        return bm

            
    def _check_mpi(self):
        from mpi4py import MPI
    
    
    def _check_dask(self):
        try:
            print("Import Dask (mock)")
        except ImportError:
            raise ImportError(bcolors.FAIL + f"Dask not present, please install Dask." + bcolors.ENDC)