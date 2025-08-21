from dataclasses import dataclass
from func import bcolors
from python.benchmarks import BenchmarkManager
import uuid
import yaml
import os.path

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
        
        self._load_config(path_to_config)
        self._check_paths()
        self._check_supported_languages()
             
             
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
            try:
                assert os.path.exists(path)
            except AssertionError:
                print(bcolors.FAIL + f"Configured path: {path} for key: {key} does not exist. Please create it." + bcolors.ENDC)
        print(bcolors.OKGREEN + "All paths checked successfully" + bcolors.ENDC)
        
        print(bcolors.OKBLUE + "Create benchmarks" + bcolors.ENDC)
    
    
    def _check_supported_languages(self):      
        supported = ["c", "python"]
        
        for language in self.config["languages"]:     
            try:
                assert language in supported
                
                print(bcolors.OKBLUE + f"Language: {language} is supported" + bcolors.ENDC)
                self._check_supported_formats(language=language)
            except AssertionError:
                print(bcolors.FAIL + f"Language: {language} not currently supported. If you want to help extend support please visit ..." + bcolors.ENDC)
    
    
    def _check_supported_formats(self, language: str):     
        supported = ["hdf5", "zarr", "netcdf4"]
        
        for format in self.config["formats"]:         
            try:
                assert format in supported
                
                print(bcolors.OKBLUE + f"Format: {format} is supported." + bcolors.ENDC)
                self._create_benchmark_manager(language=language, format=format)
            except AssertionError:
                print(bcolors.FAIL + f"Format: {format} not currently supported. If you want to help extend support please visit ..." + bcolors.ENDC)
      
    
    def _create_benchmark(self, language: str, format: str):
        self._create_benchmark_manager(language=language, format=format)
  
        
    def _create_benchmark_manager(self, language: str, format: str):
        for _, run in self.config["runs"].items():
            
            parallel    = False
            par_backend = None
            range       = self.config["range"]
            stepsize    = self.config["stepsize"]
            iterations  = self.config["iterations"]
            
            print(bcolors.OKBLUE + f"Managing Benchmark with; file-structure: {run} parallel: {parallel}, par_backend: {par_backend}, language: {language}, format: {format}, range: {range}, stepsize: {stepsize} and {iterations} iterations" + bcolors.ENDC)
            BenchmarkManager(handler_id=str(self.__uuid), run=run, parallel=parallel, par_backend=par_backend, language=language, format=format, range=range, stepsize=stepsize, iterations=iterations)