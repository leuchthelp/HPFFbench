from func.datastruct import bcolors
from dataclasses import dataclass
from pathlib import Path
import shutil
import yaml
import hashlib
import subprocess

@dataclass
class BenchmarkManager:
    
    """Defines handler to read configuration from yaml file and create matching benchmarks. Also configures the benchmark environments and gathers system information.
    
    Attributes
    ----------
    handler_id: str
        Unique handler ID to identify the handler assigned to this specific benchmark.
    
    """
    
    handler_id  : str
    run_config  : dict
    parallel    : bool
    par_backend : None | str
    language    : str
    range       : list
    stepsize    : int
    iterations  : int
    bm_config   : dict
    
    
    def __init__(self, handler_id: str, run_config: dict, parallel: bool, par_backend: None | str, language: str, format: str, range: list, stepsize: int, iterations: int, use_path: Path, results_path: Path, bm_config: dict):
        
        # Object config
        self.handler_id = handler_id
        
        hash_str = str(run_config) + str(bm_config)
        self.hash           = hashlib.sha256(hash_str.encode()).hexdigest()
        
        self.use_path       = use_path
        self.results_path   = results_path
        self.dir_path       = Path(f"{self.use_path}/{str(self.hash)}")
        self.bm_config      = bm_config
        
        # Benchmark config
        self.run_config     = run_config
        self.parallel       = parallel
        self.par_backend    = par_backend
        self.language       = language
        self.format         = format
        self.range          = range
        self.stepsize       = stepsize
        self.variable       = "X"
        self.iterations     = iterations
        
        # Source code
        try:
            self.create     = bm_config["create"]
        except:
            self.create     = None
        
        try:
            self.compile    = bm_config["compile"]
        except:
            self.compile    = None
            
        self.src            = bm_config["source"]
        
        # Environment config
        self.__checkpoint    = yaml
        self.__node          = int
        self.__node_info     = yaml
        self.__profiler      = bool
    
    
    def run(self):
        self.dir_path.mkdir(parents=True)
        
        with open(f"{self.dir_path}/run_config.yaml", "w") as f:
            yaml.safe_dump(self.run_config, f)
        
        
        if self.create is not None:    
            self.__create_file()
        
        if self.compile is not None:
            self.__compile_file()
        self.__execute_file()
        
        shutil.rmtree(path=self.dir_path)
        
        return self

 
    def __create_file(self):
        create = self.create.replace("#MAIN", self.__replace_main(self.language))
        
        path_to_create_file = f"{self.dir_path}/create.{self.language}"
        with open(path_to_create_file, "w") as file:
            file.write(create)
        
        create_file = f"create.{self.language}"
        create_command = self.bm_config["create_command"]
        create_command = create_command.replace("{runnable}", f"{create_file}")
        
        p = subprocess.run(create_command.split(), capture_output=True, text=True, cwd=self.dir_path)
        print(p.stderr)
        print(p.stdout)
        

    def __compile_file(self):
        pass
  

    def __execute_file(self):
        
        execute = self.src.replace("#MAIN", self.__replace_main(self.language))
        execute = execute.replace("#RESULT", self.__replace_result(self.language))
        
        path_to_tmp_file = f"{self.dir_path}/execute.{self.language}"
        with open(path_to_tmp_file, "w") as file:
            file.write(execute)
        
        tmp_file    = f"execute.{self.language}"
        run_command = self.bm_config["run_command"]
        run_command = run_command.replace("{runnable}", f"{tmp_file}")
        run_command = run_command.replace("{variable}", f"{self.variable}")
        run_command = run_command.replace("{iterations}", f"{self.iterations}")
        
        p = subprocess.run(run_command.split(), capture_output=True, text=True, cwd=self.dir_path)
        print(p.stderr)
        print(p.stdout)
    
        
    def __replace_main(self, language):
        
        match language:
            case "py":
                return """def main():

    parser = argparse.ArgumentParser(
        prog="Python Dataformat-Benchmark",
        description="run python based benchmark for Zarr, NetCDF4 and HDF5",
    )
    parser.add_argument("-c", "--create", type=int, default=-1, help="creates Zarr, NetCDF4 and HDF5 Files using a previously saved run format")
    parser.add_argument("-b", "--benchmark", type=int, default=-1, help="benchmark to run")
    parser.add_argument("-i", "--iterations", type=int, default=10, help="number of iterations to run the benchmark for")
    parser.add_argument("-v", "--variable", type=str, default=None, help="variable to read, if none is provided all are read")
    parser.add_argument("-p", "--path", type=str, default=None, help="Path to file to use for benchmark")
    args = parser.parse_args()
    match args.benchmark:
        case 1:
            bench(args.iterations, args.variable)
        case -1:
            if args.create != -1:
                create(args.create, False)

if __name__=="__main__":
    main()
        """
            case "c":
                return ""
     
        
    def __replace_result(self, language):
        
        match language:
            case "py":
                return f"""with open("{self.results_path.absolute()}/{self.hash}.yaml", "w") as f:
        yaml.dump(result, f)
                        """
            case "c":
                return ""