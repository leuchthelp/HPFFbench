from dataclasses import dataclass, asdict
from func.datastruct import bcolors
from benchmarkmanager import BenchmarkManager
from pathlib import Path
from pathos.pools import _ProcessPool as ProcessPool
from copy import deepcopy
import pandas as pd
import numpy as np
import itertools
import yaml
import json
import hashlib
import random
import tqdm
import sys

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
        
        self.__id = None
        self.config = {}
        self.__benchmarks = []
        
        self.__load_config(path_to_config)
        
        if bool(self.config["runs"]) == False:
            raise ValueError(bcolors.FAIL + "No runs specified, please add some." + bcolors.ENDC)
        
        self.__check_paths()
        
        self.__capabilities = self.__determine_capabilities()
        
        try:
            self.__only_data = self.config["only data"]  # type: ignore
        except:
            self.__only_data = False
            
        try:
            self.__max_processes = self.config["max processes"]  # type: ignore
        except:
            self.__max_processes = None
            
        try:
            self.__bm_per_processes = self.config["bm per process"]  # type: ignore
        except:
            self.__bm_per_processes = 1
        
        parallel = False
        try:
            parallel = self.config["parallel"]  # type: ignore
            if parallel != "Both" and type(parallel) != bool: raise ValueError(bcolors.FAIL + "\"parallel\" can only either be \"True\", \"False\" or \"Both\"" + bcolors.ENDC)
            
        except KeyError:
            print(bcolors.WARNING + f"\"parallel\" is unset! Be aware parallel will be automatically set to False as long as it remains unset. You will be unable to run parallelized benchmarks until you set it to True." + bcolors.ENDC)   
        
        
        if parallel == "Both":
            self.__tasks = self.__create_benchmark(parallel=False, determined_cap=self.__capabilities)
            self.__tasks.extend(self.__create_benchmark(parallel=True, determined_cap=self.__capabilities))
        else:
            self.__tasks = self.__create_benchmark(parallel=parallel, determined_cap=self.__capabilities)
        
        
        if self.__only_data == False:
            self.__start()
        else:
            print(bcolors.UNDERLINE + f"Just collecting results of matching benchmarks if they exist since \"only_data\" is set to {self.__only_data}." + bcolors.ENDC)
        
        #self.__prepare_dataframe()
                      

    def __load_config(self, path_to_config):
        
        print(bcolors.OKBLUE + "Try loading config.yaml" + bcolors.ENDC)
        try:
            file = open(f"{path_to_config}config.yaml", "r")
            self.config = yaml.safe_load(stream=file)
            self.__id = hashlib.sha256(str(path_to_config).encode()).hexdigest()
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
        
        determined = {}
        
        for path in root.rglob("*"): 
            if not path.is_dir():      
                with open(path, "r") as file:
                    current = yaml.safe_load(file)
                    
                    tmp = []
                    additional = []
                    
                    try:
                        tmp.append(("parallel", current["parallel"]))  # type: ignore
                    except KeyError:
                        tmp.append(("parallel", False))
                    
                    try:
                        if current["par_backend"] != None and current["parallel"] == True:  # type: ignore
                            tmp.append(("par_backend", current["par_backend"]))  # type: ignore
                            
                        elif current["parallel"] == "configurable":  # type: ignore
                            
                            if type(current["par_backend"]) == list:  # type: ignore
                                additional = current["par_backend"]  # type: ignore
                            else:
                                additional.append(current["par_backend"])  # type: ignore   
                            raise KeyError
                                    
                        else:
                            raise KeyError
                    except KeyError:
                        tmp.append(("par_backend", None))
                    
                    try:
                        tmp.append(("language", current["language"]))  # type: ignore
                    except yaml.YAMLError as e:
                        raise e
                     
                    try: 
                        tmp.append(("format", current["format"]))  # type: ignore
                    except KeyError as e:
                        raise e
                    
                    hold = dict(tmp)
                    if hold["parallel"] == "configurable":
                        hold["parallel"] = False
                        
                        for backend in additional:
                            extra = deepcopy(hold)
                            extra["parallel"] = True
                            extra["par_backend"] = backend

                            determined[str(extra)] = current
                        
                    determined[str(hold)] = current


        return determined
        
   
    def __requested_capabilities(self, parallel: bool):
        requested   = None
        
        languages    = []
        for langauge in self.config["languages"]:  # type: ignore
            languages.append(("language", langauge))
        
        formats      = []
        for format in self.config["formats"]:  # type: ignore
            formats.append(("format", format))
            
        par_backends = [("par_backend", None)]
        
        if parallel == True:
            par_backends = []
            if type(self.config["par_backend"]) != list:  # type: ignore
                    par_backends.append(("par_backend", self.config["par_backend"]))  # type: ignore
            else:
                for par_backend in self.config["par_backend"]:  # type: ignore
                    par_backends.append(("par_backend", par_backend))
        
        requested = itertools.product(*[[("parallel", parallel)], par_backends, languages, formats])
        return requested   
   
     
    def __create_benchmark(self, parallel: bool, determined_cap: dict) -> list:
        requested_cap = self.__requested_capabilities(parallel=parallel) 
        
        tasks = []
        for requested in [*requested_cap]: 
            requested = dict(requested)
            if str(requested) in determined_cap:
                print(bcolors.OKGREEN + f"Success" + bcolors.ENDC)
                
                tasks.append(self.__create_benchmark_manager(requested=requested, bm_config=determined_cap[str(requested)]))
        
        return tasks


    def __create_benchmark_manager(self, requested: dict, bm_config: dict) -> list:
        benchmarks = []
        
        for _, run_config in self.config["runs"].items():  # type: ignore
            
            parallel    = requested["parallel"]
            
            ranks = [1]
            
            if parallel == True:
                try:
                    ranks = self.config["ranks"]  # type: ignore

                    if type(ranks) == int:
                        ranks = [ranks]

                except KeyError as e:
                    raise e
                
                
            use_path    = Path(self.config["paths"]["path_to_tmp"] )  # type: ignore
            results_path= Path(self.config["paths"]["path_to_results"])  # type: ignore
            
            
            var_to_bm   = self.config["variable_to_benchmark"]  # type: ignore
            iterations  = self.config["iterations"]  # type: ignore
            
    
            for rank in ranks:      
                bm = BenchmarkManager(
                        handler_id=str(self.__id), 
                        run_config=run_config,
                        bm_config=bm_config,
                        requested=requested,
                        parallel=parallel, 
                        ranks=rank,
                        var_to_bm=var_to_bm,
                        iterations=iterations, 
                        use_path=use_path, 
                        results_path=results_path 
                        )
                
                self.__benchmarks.append((bm.id, asdict(bm))) # type: ignore

                benchmarks.append(bm)
            
        return benchmarks


    def __start(self):
        try:
            bm_list = [x for xs in self.__tasks for x in xs]
            pool = ProcessPool(processes=self.__max_processes)
            for _ in tqdm.tqdm(pool.imap_unordered(self.__run_benchmark, bm_list, chunksize=self.__bm_per_processes), total=len(bm_list), unit="benchmarks", colour="green", file=sys.stdout, desc="Benchmarks still to run"):
                pass      
            
        except TypeError:     
            raise NameError(bcolors.FAIL + f"No matching benchmark found that fits configuration" + bcolors.ENDC)
        

    def __run_benchmark(self, benchmarks: BenchmarkManager):
        return benchmarks.run()

    
    def __prepare_dataframe(self):
        root = Path(self.config["paths"]["path_to_results"])  # type: ignore
        df = pd.DataFrame()
        
        self.__benchmarks = dict(self.__benchmarks)
        
        for path in root.rglob("*"):
            if not path.is_dir(): 
                
                path_name = path.name.replace(".json", "")
                if path_name in self.__benchmarks:
                    
                    print(f"currently on {path_name}")
                    
                    benchmarks = self.__benchmarks[path_name]
                    
                    with open(path, "r") as file:
                        current = json.load(file)
                    
                    mean = np.mean(current)
                    std  = np.std(current)
                    rsd  = std / mean
                    
                    error= std / np.sqrt(len(current))
        
                    anomaly = False
                    
                    
                    # demo code, do not use in future
                    node = ""
                    
                    tmp = pd.DataFrame(data={
                            "benchmark"         : benchmarks["id"],
                            "run config"        : str(benchmarks["run_config"]), 
                            "time taken"        : current,
                            "throughput"        : benchmarks["total_filesize"] / mean,
                            "engine"            : benchmarks["engine"],
                            "var to bm"         : str(benchmarks["var_to_bm"]),
                            "total filesize"    : benchmarks["total_filesize"],
                            "unit"              : benchmarks["unit"],
                            "filesize per var"  : str(benchmarks["filesize_var"]),
                            "filesize per chunk": str(benchmarks["chunksize_var"]),
                            "parallel"          : benchmarks["parallel"],
                            "parallel backend"  : benchmarks["par_backend"],
                            "ranks"             : benchmarks["ranks"],
                            "language"          : benchmarks["language"], 
                            "format"            : str(benchmarks["format"]), 
                            "mean time"         : mean,
                            "standard deviation": std,
                            "relative std"      : rsd,
                            "error bar"         : error,
                            "anomaly"           : anomaly,
                            "node"              : node,
                            "node count"        : 0,
                            })
                    
                    for i, rows in tmp.iterrows():
                        if rows["relative std"] > 0.35:
                            tmp.at[i, "anomaly"] = True  # type: ignore
                            tmp.at[i, "node"] = f"l{random.randint(10485, 10490)}"  # type: ignore
                        else:
                            tmp.at[i, "node"] = f"l{random.randint(10420, 10484)}" # type: ignore
                    
                    df = pd.concat([df, tmp], ignore_index=True)
                    
        
        tmp = self.config["paths"]["path_to_results"]  # type: ignore
        
        # there is probably a better method for doing this, will look into it later
        for node, count in df["node"].value_counts().to_dict().items():
            df.loc[df["node"] == node, "node count"] = count
        
        df.sort_values(by=["total filesize", "ranks", "engine", "format"], ascending=[True, True, True, False], inplace=True)
        df.to_json(Path(f"{tmp}/results.json"))                                          

        