from func.datastruct import bcolors
from dataclasses import dataclass, asdict
from pathlib import Path
import shutil
import yaml
import json
import hashlib
import subprocess
import os

@dataclass
class BenchmarkManager:
    
    """Defines handler to read configuration from yaml file and create matching benchmarks. Also configures the benchmark environments and gathers system information.
    
    Attributes
    ----------
    handler_id: str
        Unique handler ID to identify the handler assigned to this specific benchmark.
    
    """
    
    handler_id  : str
    hash        : str
    run_config  : dict
    parallel    : bool
    par_backend : None | str
    ranks       : None | int
    language    : str
    format      : str
    extension   : str
    range       : list
    stepsize    : int
    datatype    : list
    var_to_bm   : str | list
    iterations  : int
    internal_i  : int
    bm_config   : dict
    
    
    def __init__(self, 
                 handler_id     : str, 
                 run_config     : dict, 
                 parallel       : bool, 
                 par_backend    : None | str, 
                 ranks          : None | int,
                 language       : str, 
                 format         : str, 
                 extension      : str,
                 range          : list, 
                 stepsize       : int, 
                 datatype       : list,
                 var_to_bm      : str | list,
                 iterations     : int, 
                 use_path       : Path, 
                 results_path   : Path, 
                 bm_config      : dict
                 ):
        
        # Object config
        self.handler_id = handler_id
        
        hash_str = str(run_config) + str(bm_config["par_backend"]) + str(par_backend) + str(bm_config["parallel"]) + str(parallel) + str(bm_config["format"]) + str(format)
        self.hash           = hashlib.sha256(hash_str.encode()).hexdigest()
        
        self.use_path       = use_path
        self.results_path   = results_path
        self.dir_path       = Path(f"{self.use_path}/{str(self.hash)}")
        self.bm_config      = bm_config
        
        # Benchmark config
        self.run_config     = run_config
        self.parallel       = parallel
        self.par_backend    = par_backend
        self.ranks          = ranks
        self.language       = language
        self.format         = format
        self.extension      = extension
        self.range          = range
        self.stepsize       = stepsize
        self.datatype       = datatype
        self.var_to_bm      = var_to_bm
        self.iterations     = iterations
        self.internal_i     = 1
        self.no_caching     = True
        self.location       = f"test.{self.extension}"
        
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
        self.__checkpoint   = yaml
        self.__node         = int
        self.__node_info    = yaml
        self.__profiler     = bool
    
    
    def run(self):
        self.dir_path.mkdir(parents=True)
        
        with open(f"{self.dir_path}/run_config.json", "w") as f:
            json.dump(self.run_config, f)
        
        
        if self.create is not None:  
            self.__create_file()
        
        if self.compile is not None:
            self.__compile_file()
        
        self.__execute_file()
        
        shutil.rmtree(path=self.dir_path)
        
        return asdict(self)

 
    def __create_file(self):
        create = self.create.replace("#MAIN", self.__replace_main(self.language)) # type: ignore
        
        path_to_create_file = f"{self.dir_path}/create.{self.language}"
        with open(path_to_create_file, "w") as file:
            file.write(create)
        
        create_file = f"create.{self.language}"
        
        create_commands = self.bm_config["create_command"]
        create_command  = create_commands["serial"]
        
        if self.par_backend in create_commands.keys():
            create_command = create_commands[str(self.par_backend)]
            create_command = create_command +  "-p"
            create_command = create_command.replace("-n ", f"-n {self.ranks} ")

        create_command = create_command.replace("{runnable}", f"{create_file} ")
        create_command = create_command.replace("-p", f"-p {self.parallel} ")
        
        
        if "-c" not in create_command:
            create_command = create_command + "-c 1 "
        
            
        if "-l" not in create_command:
            create_command = create_command + "-l"
                
        create_command = create_command.replace("-l", f"-l {self.location}")
        
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
        run_commands = self.bm_config["run_command"]
        
        run_command  = run_commands["serial"]
        if self.par_backend in run_commands.keys():
            run_command = run_commands[str(self.par_backend)]
            run_command = run_command +  "-p"
            run_command = run_command.replace("-n", f"-n {self.ranks} ")
            
            
        if  "SLURM_JOB_ID"  in os.environ:
            run_command = "sbatch " + run_command
        
        
        tmp = ",".join(self.var_to_bm)    
        run_command = run_command.replace("-v", f"-v {tmp} ")
        run_command = run_command.replace("{runnable}", f"{tmp_file} ")
        run_command = run_command.replace("-i", f"-i {self.internal_i} ")
        run_command = run_command.replace("-p", f"-p {self.parallel} ")
        
        
        if "-b" not in run_command:
            run_command = run_command + "-b 1 "
            
        if "-l" not in run_command:
                run_command = run_command + f"-l {self.location}"
    
    
        for i in range(self.iterations):
            
            p = subprocess.run(run_command.split(), capture_output=True, text=True, cwd=self.dir_path)
            print(p.stderr)
            print(p.stdout)
            
            if "SLURM_JOB_ID" not in os.environ and self.no_caching:
                
                new_path = Path(f"{self.dir_path}/{i}")
                new_path.mkdir(parents=True)
                
                current_path = None
                for path in self.dir_path.rglob(f"*.{self.extension}"):
                    current_path = path
                    
                new_file_location = shutil.move(current_path.absolute(), f"{new_path.absolute()}/{i}.{self.extension}")  # type: ignore
                
                #print(f"current location: {self.location} -> new location: {new_file_location}")
                
                run_command = run_command.replace(f"-l {self.location}", f"-l {new_file_location}")
                #print(f"new run command: {run_command}")
                self.location = new_file_location
                
        
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
    parser.add_argument("-i", "--iterations", type=int, default=1, help="number of internal iterations to run the benchmark for. Will cause caching effects")
    parser.add_argument("-v", "--var_to_bm", type=str, default=None, help="var_to_bm to read, if none is provided all are read")
    parser.add_argument("-p", "--parallel", type=bool, default=False, help="If to run the benchmark using parallelism of any kind supported")
    parser.add_argument("-l", "--location", type=str, default="", help="Location where file will be create / saved")
    args = parser.parse_args()
    
    match args.benchmark:
        case 1:
            bench(iterations=args.iterations, variable=args.var_to_bm, parallel=args.parallel, path=args.location)
        case -1:
            if args.create != -1:
                create(selection=args.create, parallel=args.parallel, path=args.location)

if __name__=="__main__":
    main()
        """
            case "c":
                return ""
     
        
    def __replace_result(self, language):
        
        match language:
            case "py":
                return f"""if parallel is False or MPI.COMM_WORLD.rank == 0:
        with open("{self.results_path.absolute()}/{self.hash}.json", "a") as f:
            json.dump(result, f)
                        """
            case "c":
                return ""