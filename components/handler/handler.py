from dataclasses import dataclass
from func.datastruct import bcolors
from python.benchmarks import BenchmarkManager
from pathlib import Path
from pathos.pools import ProcessPool
import pandas as pd
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
        
        self.__load_config(path_to_config)
        self.__check_paths()
        
        determined_cap = self.__determine_capabilities()
        
        parallel = False
        try:
            parallel = self.config["parallel"] # type: ignore
            if parallel != "Both" and type(parallel) is not bool: raise ValueError(bcolors.FAIL + "\"parallel\" can only either be \"True\", \"False\" or \"Both\"" + bcolors.ENDC)
            
        except KeyError:
            print(bcolors.WARNING + f"\"parallel\" is unset! Be aware parallel will be automatically set to False as long as it remains unset. You will be unable to run parallelized benchmarks until you set it to True." + bcolors.ENDC)   
        
        
        if parallel == "Both":
            self.__tasks = self.__create_benchmark(parallel=False, determined_cap=determined_cap)
            self.__tasks.extend(self.__create_benchmark(parallel=True, determined_cap=determined_cap))
        else:
            self.__tasks = self.__create_benchmark(parallel=parallel, determined_cap=determined_cap)
         

        self.__start()
                      

    def __load_config(self, path_to_config):
        
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
    
    
    def __check_paths(self):
        print(bcolors.OKBLUE + "Check configured paths" + bcolors.ENDC)
        for key, path in self.config["paths"].items(): # type: ignore
            if not Path(path).exists(): raise ValueError(bcolors.FAIL + f"Configured path: {path} for key: {key} does not exist. Please create it." + bcolors.ENDC)
        
        print(bcolors.OKGREEN + "All paths checked successfully" + bcolors.ENDC)
        
        print(bcolors.OKBLUE + "Create benchmarks" + bcolors.ENDC)
    
    
    def __determine_capabilities(self):
        root = Path(self.config["paths"]["path_to_benchmarks"])  # type: ignore
        
        determined = []
        
        for path in root.rglob("*"): 
            if not path.is_dir():      
                with open(path, "r") as file:
                    current = yaml.safe_load(file)
                    
                    tmp = []
                    
                    try:
                        tmp.append(("parallel", current["parallel"]))  # type: ignore
                    except KeyError:
                        tmp.append(("parallel", False))
                    
                    try:
                        if current["par_backend"] is not None:  # type: ignore
                            tmp.append(("par_backend", current["par_backend"]))  # type: ignore
                        else:
                            raise KeyError
                    except KeyError:
                        tmp.append(("par_backend", "base"))
                    
                    try:
                        tmp.append(("language", current["language"]))  # type: ignore
                    except yaml.YAMLError as e:
                        raise e
                     
                    try: 
                        tmp.append(("format", current["format"]))  # type: ignore
                    except KeyError as e:
                        raise e
                                        
                    determined.append((dict(tmp), current))   

        return determined
        
   
    def __requested_capabilities(self, parallel: bool):
        requested   = None
        
        languages    = []
        for langauge in self.config["languages"]:  # type: ignore
            languages.append(("language", langauge))
        
        formats      = []
        for format in self.config["formats"]:  # type: ignore
            formats.append(("format", format))
            
        par_backends = [("par_backend", "base")]
        
        if parallel is True:
            par_backends = []
            if type(self.config["par_backend"]) is not list:  # type: ignore
                    par_backends.append(("par_backend", self.config["par_backend"]))  # type: ignore
            else:
                for par_backend in self.config["par_backend"]:  # type: ignore
                    par_backends.append(("par_backend", par_backend))
        
        requested = itertools.product(*[[("parallel", parallel)], par_backends, languages, formats])
        return requested   
   
     
    def __create_benchmark(self, parallel: bool, determined_cap: list) -> list:
        requested_cap = self.__requested_capabilities(parallel=parallel) 
        
        tasks = []
        for requested in [*requested_cap]: 
            requested = dict(requested)
            for determined in determined_cap:
                if requested == determined[0]:
                    print(bcolors.OKGREEN + f"Success" + bcolors.ENDC)
                    tasks.append(self.__create_benchmark_manager(requested=requested, bm_config=determined[1]))
               
        return tasks


    def __create_benchmark_manager(self, requested: dict, bm_config: dict) -> list:
        
        bm = []
        for _, run_config in self.config["runs"].items():  # type: ignore
            
            parallel    = requested["parallel"]
            par_backend = requested["par_backend"]
            language    = requested["language"]
            format      = requested["format"]
            use_path    = Path(self.config["paths"]["path_to_tmp"] )  # type: ignore
            results_path= Path(self.config["paths"]["path_to_results"])  # type: ignore
            range       = self.config["range"]  # type: ignore
            stepsize    = self.config["stepsize"]  # type: ignore
            
            datatype    = []
            for _, item in run_config.items():
                if any(isinstance(x, str) for x in item):
                    datatype.append(item[-1])
                else:
                    datatype.append("f8")
            
            var_to_bm   = self.config["variable_to_benchmark"]  # type: ignore
            iterations  = self.config["iterations"]  # type: ignore
                    
            print(bcolors.OKBLUE + f"Managing Benchmark with; file-structure: {run_config}, datatype: {datatype}, parallel: {parallel}, par_backend: {par_backend}, language: {language}, format: {format}, range: {range}, stepsize: {stepsize} and {iterations} iterations. It will be stored in {use_path}" + bcolors.ENDC)
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
                    datatype=datatype,
                    var_to_bm=var_to_bm,
                    iterations=iterations, 
                    use_path=use_path, 
                    results_path=results_path, 
                    bm_config=bm_config)
                )
        return bm


    def __start(self):
        self.__benchmarks = ProcessPool().amap(self.__run_benchmark, *self.__tasks).get()  
        self.__prepare_dataframe()
        

    def __run_benchmark(self, bm: BenchmarkManager):
        return bm.run()

    
    def __prepare_dataframe(self):
        root = Path(self.config["paths"]["path_to_results"]) # type: ignore
        df = pd.DataFrame()
        
        for path in root.rglob("*"):
            if not path.is_dir():
                for index in range(len(self.__benchmarks)):
                    
                    bm = self.__benchmarks[index]
                    
                    if bm["hash"] == path.name.replace(".yaml", ""):
                        
                        with open(path, "r") as file:
                            current = yaml.safe_load(file)
                        
                        tmp = pd.DataFrame(data={
                                "run"       : index, 
                                "benchmark" : bm["hash"],
                                "run_config": str(bm["run_config"]), 
                                "time taken": current,
                                "parallel"  : bm["parallel"],
                                "language"  : bm["language"], 
                                "format"    : str(bm["bm_config"]["format"]), 
                                })
                        
                        df = pd.concat([df, tmp], ignore_index=True)
    
                          
        tmp = self.config["paths"]["path_to_results"] # type: ignore  
        df.to_json(Path(f"{tmp}/results.json"))                                          

        