from dataclasses import dataclass, asdict
from dev_utils import bcolors
from benchmarkmanager import BenchmarkManager
from spackmanager import SpackManager
from pathlib import Path
from pathos.pools import _ProcessPool as ProcessPool
from copy import deepcopy
from collections import Counter
import pandas as pd
import numpy as np
import itertools
import yaml
import json
import hashlib
import tqdm
import sys
import os
import logging

@dataclass
class Handler:
    
    """Defines handler to read configuration from yaml file and create matching benchmarks. Also configures the benchmark environments and gathers system information.
    
    Attributes
    ----------
    path_to_config: str
        Path to config.yaml which covers benchmark environments and benchmarks to run.
    
    """
    
    path_to_config: str
    
    
    def __init__(self, path_to_config: str, logger: logging.Logger):
        
        self.logger = logger
        self.__id = ""
        self.config = {}
        self.__benchmarks = []
        
        
        self.__load_config(path_to_config)
        
        
        self.__delete_envs = True
        try:
            self.__delete_envs = self.config["delete envs"]
        except:
            pass
        
        if bool(self.config["runs"]) == False:
            raise ValueError(bcolors.FAIL + "No runs specified, please add some." + bcolors.ENDC)
        
        self.__check_paths()
        
        self.__capabilities = self.__determine_capabilities()
        
        try:
            self.__only_data = self.config["only data"]  # type: ignore
        except:
            self.__only_data = False
            
        try:
            self.__use_spack_env = self.config["use spack env"]  # type: ignore
        except:
            self.__use_spack_env = True
            
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
            self.logger.info(bcolors.WARNING + f"\"parallel\" is unset! Be aware parallel will be automatically set to False as long as it remains unset. You will be unable to run parallelized benchmarks until you set it to True." + bcolors.ENDC)   
        
        
        self.spack_manager = []
        for env_name, spack_env in self.config["spack env"].items():
            self.spack_manager.append(SpackManager(handler_id=self.__id, env_name=env_name, spack_env=spack_env, use_spack_env=self.__use_spack_env, only_data=self.__only_data, logger=self.logger))
        
        
        if parallel == "Both":
            self.__tasks = self.__create_benchmark(parallel=False, determined_cap=self.__capabilities)
            self.__tasks.extend(self.__create_benchmark(parallel=True, determined_cap=self.__capabilities))
        else:
            self.__tasks = self.__create_benchmark(parallel=parallel, determined_cap=self.__capabilities)
        
        
        if self.__only_data == False:
            self.__start()
        else:
            self.logger.info(bcolors.UNDERLINE + f"Just collecting results of matching benchmarks if they exist since \"only_data\" is set to {self.__only_data}." + bcolors.ENDC)
        
        self.__prepare_dataframe()
                      

    def __load_config(self, path_to_config):
        
        self.logger.info(bcolors.OKBLUE + "Try loading config.yaml" + bcolors.ENDC)
        try:
            file = open(f"{path_to_config}/config.yaml", "r")
            self.config = yaml.safe_load(stream=file)
            self.__id = hashlib.sha256(str(path_to_config).encode()).hexdigest()
            self.logger.info(bcolors.OKGREEN + "Success loading config.yaml" + bcolors.ENDC)
            
        except FileNotFoundError as e:
            FileNotFoundError(bcolors.FAIL + f"config.yaml not found, please ensure a valid config exists! Additional details: {e}" + bcolors.ENDC)
        except OSError as e:
            OSError(bcolors.FAIL + f"Path to config.yaml could not found, please check it is valid! Additional details: {e}" + bcolors.ENDC) 
        except yaml.YAMLError as e:
            yaml.YAMLError(bcolors.FAIL + f"Error loading config.yaml! Additional details: {e}" + bcolors.ENDC)
    
    
    def __check_paths(self):
        self.logger.info(bcolors.OKBLUE + "Check configured paths" + bcolors.ENDC)
        for key, path in self.config["paths"].items(): # type: ignore
            if not Path(path).exists(): raise ValueError(bcolors.FAIL + f"Configured path: {path} for key: {key} does not exist. Please create it." + bcolors.ENDC)
        
        self.logger.info(bcolors.OKGREEN + "All paths checked successfully" + bcolors.ENDC)
        
        self.logger.info(bcolors.OKBLUE + "Create benchmarks" + bcolors.ENDC)
    
    
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
                self.logger.info(bcolors.OKGREEN + f"Success" + bcolors.ENDC)
                
                tasks.append(self.__create_benchmark_manager(parallel=parallel, requested=requested, bm_config=determined_cap[str(requested)]))
        
        return tasks


    def __create_benchmark_manager(self, parallel: bool, requested: dict, bm_config: dict) -> list:
        benchmarks = []
        
        for _, run_config in self.config["runs"].items():  # type: ignore
            
            slurm_options= ""
            nodes       = [1]
            collective  = [None]
            ranks       = [1]
            
            if parallel == True:
                try:
                    
                    ranks = self.config["ranks"]  # type: ignore

                    if type(ranks) == int:
                        ranks = [ranks]
                        
                    try: 
                        config_collective = [self.config["collective"]] # type: ignore
                        
                        if config_collective == "Both":
                            collective = [False, True]
                        else:
                            collective = config_collective
                    except:
                        collective = [False]

                except KeyError as e:
                    raise e
                
                
            use_path    = Path(self.config["paths"]["path_to_tmp"] )  # type: ignore
            root_path   = Path(self.config["paths"]["path_to_root"] )  # type: ignore
            results_path= Path(self.config["paths"]["path_to_results"])  # type: ignore
            
            
            # If within a Slurm environment; slurm options need to be supplied as they have to include account for allocation
            if  "SLURM_JOB_ID" in os.environ or self.__only_data == True:
                slurm_options= self.config["slurm options"]  # type: ignore
                
                try:
                    nodes = self.config["nodes"] if type(self.config["nodes"]) == list else [self.config["nodes"]] # type: ignore
                except:
                    pass
            
            
            var_to_bm   = self.config["variable_to_benchmark"]  # type: ignore
            iterations  = self.config["iterations"]  # type: ignore
            
            spack_manager = []
            for manager in self.spack_manager:
                if requested["format"] in manager.target and requested["language"] in manager.language:
                    spack_manager.append(manager)
            
            combinations = itertools.product(nodes, ranks, collective, spack_manager)
            
            for combination in combinations:
                
                node    = combination[0]
                rank    = combination[1]
                state   = combination[2]
                manager = combination[3]
                                
                if manager.initialized == False:
                    manager.initialize_env()
                else:
                    self.logger.info(bcolors.OKGREEN + f"Environment: {manager.env_name} already initialized" + bcolors.ENDC)
                
                bm = BenchmarkManager(
                        handler_id=self.__id, 
                        run_config=run_config,
                        bm_config=bm_config,
                        nodes=node,
                        slurm_options=slurm_options,
                        requested=requested,
                        parallel=parallel, 
                        collective=state,
                        ranks=rank,
                        var_to_bm=var_to_bm,
                        iterations=iterations, 
                        use_path=use_path, 
                        root_path=root_path,
                        results_path=results_path,
                        spack_manager=manager,
                        logger=self.logger,
                        )
                
                self.__benchmarks.append((bm.id, asdict(bm))) # type: ignore
                benchmarks.append(bm)  
        
        return benchmarks


    def __start(self):
        try:
            self.__benchmarks = []
            bm_list = list(itertools.chain.from_iterable(self.__tasks))
            pool = ProcessPool(processes=self.__max_processes)
            for result in tqdm.tqdm(pool.imap_unordered(self.__run_benchmark, bm_list, chunksize=self.__bm_per_processes), total=len(bm_list), unit="benchmarks", colour="green", file=sys.stdout, desc="Benchmarks still to run"):
                self.__benchmarks.append(result)
            
            if self.__delete_envs == True: 
                for manager in self.spack_manager:
                    self.logger.info(f"remove environment: {manager.env_name}")
                    manager.delete()
                self.logger.info("finish removing environments")       
            
        except TypeError as e:     
            raise NameError(bcolors.FAIL + f"No matching benchmark found that fits configuration" + bcolors.ENDC) from e
        

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
                    
                    self.logger.info(f"currently on {path_name}")
                    
                    benchmark = self.__benchmarks[path_name]
                    
                    with open(path, "r") as file:
                        current = json.load(file)
                    
                    location_nodes = Path(f"{root}/{path_name}-nodes.json")
                    with open(location_nodes.absolute(), "r") as file:
                        used_nodes = json.load(file)
                    
                    mean = np.mean(current)
                    std  = np.std(current)
                    rsd  = std / mean
                    
                    error= std / np.sqrt(len(current))
                        
                        
                    for index, value in enumerate(current):
                        
                        count = Counter()
                        string = used_nodes[index]
                        symbol = string[0]
                        string = string.replace(symbol, "")
                        nodes = string.split(",")
                        
                        
                        for i, node in enumerate(nodes):
                            if "-" in node:
                                hold = node.split("-")
                                
                                node = [str(additional) for additional in range(int(hold[0]), int(hold[1])+1)]
                                nodes[i] = node
                                
                            elif type(node) != list:
                                nodes[i] = [node]


                        count.update(list(itertools.chain.from_iterable(nodes)))
                        
                        anomaly = False
                        if value >= mean + mean * rsd:
                            anomaly = True
                            
                        tmp = pd.DataFrame(data={
                                "benchmark"         : benchmark["id"],
                                "run config"        : [benchmark["run_config"]], 
                                "time taken"        : value,
                                "throughput"        : benchmark["total_filesize"] / mean,
                                "engine"            : benchmark["engine"],
                                "var to bm"         : [benchmark["var_to_bm"]],
                                "total filesize"    : benchmark["total_filesize"],
                                "unit"              : benchmark["unit"],
                                "filesize per var"  : [benchmark["filesize_var"]],
                                "filesize per chunk": [benchmark["chunksize_var"]],
                                "parallel"          : benchmark["parallel"],
                                "parallel backend"  : benchmark["par_backend"],
                                "collective"        : benchmark["collective"],
                                "ranks"             : benchmark["ranks"],
                                "language"          : benchmark["language"], 
                                "format"            : str(benchmark["format"]), 
                                "mean time"         : mean,
                                "standard deviation": std,
                                "relative std"      : rsd,
                                "error bar"         : error,
                                "anomaly"           : anomaly,
                                "nodes"             : benchmark["nodes"],
                                "used nodes"        : used_nodes[index],
                                "node count"        : [count],
                                "total node count"  : [Counter()],
                                "total nc match"    : [Counter()],
                                })
                    
                    
                        df = pd.concat([df, tmp], ignore_index=True)
                    
        
        tmp = self.config["paths"]["path_to_results"]  # type: ignore
        
        # there is probably a better method for doing this, will look into it later
        
        total_node_counter = Counter()
        for count in df["node count"]:
            total_node_counter.update(count)

        
        for index, _ in df.iterrows():
            df.at[index, "total node count"] = total_node_counter # type: ignore
            
            for nodes, count in total_node_counter.items():
                if nodes in df.at[index,"node count"]:  # type: ignore
                    df.at[index,"total nc match"][nodes] = count  # type: ignore
            
        self.logger.debug(df)
        df.sort_values(by=["total filesize", "ranks", "engine", "format"], ascending=[True, True, True, False], inplace=True)
        df.to_json(Path(f"{tmp}/results.json"))                                          

        