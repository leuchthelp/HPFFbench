from dev_utils import calc_size_unit, bcolors
from spackmanager import SpackManager
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import shutil
import yaml
import hashlib
import subprocess
import os
import re
import logging

@dataclass
class BenchmarkManager:
    
    """Defines handler to read configuration from yaml file and create matching benchmarks. Also configures the benchmark environments and gathers system information.
    
    Attributes
    ----------
    handler_id: str
        Unique handler ID to identify the handler assigned to this specific benchmark.
        
    id: str
        Unique ID to identify this specific benchmark with.
        
    run_config: dict
        The run configuration that was requested, contains the basic structure of a file that will be created.
        
    bm_config: dict
        The configuration of the benchmark file with all it's adjacent information like source code, commands and such.
        
    nodes: int
        Number of nodes used with the context of a slurm environment, otherwise always 1.
        
    parallel: bool
        If parallelism is enabled.
        
    par_backend: None | str
        What kind of backend is being used to facilitate parallelism. Will be "None" if parallelism is not requested.
        
    ranks: int
        Represents how many cores are used to execute the benchmark following the MPI terminology. Will always be 1 for serial benchmarks.
        
    collective: None | bool
        If collective MPI I/O is requested, default is "False" for independent I/O. Will be none for serial benchmarks.
        
    langauge: str

    format: str
        Simplified representation of the kind of benchmark that was requested.
        
    engine: str
        Represent the file format following the xarray terminology.
        
    extension: str
        File extension used for the created file.
        
    datatype: list
        Datatypes of each variable / dataset within the file.
        
    var_to_bm: str | list
        Which variable / dataset will be benchmarked from the file. Can either be a single value string or a list of strings.
        
    total_filesize: int
        The total filesize benchmarked calculated from all variables / datasets were requested for benchmarking.
        
    unit: str
        Unit for the total filesize, i.e. MB, GB, etc.
        
    filesize_var: list
        filesize per variable / dataset.
        
    chunksize_var: list
        filesize per variable / dataset chunks.
        
    iterations: int
        total iterations performed. In the context of a slurm environment equal to the number of unique node allocations performed.
        
    internal_i: int
        The benchmark itself can have iterations to be performed as well, this would result in caching of files on the nodes used in the context of a slurm environment.
    """
    
    handler_id      : str
    id              : str
    run_config      : dict
    bm_config       : dict
    nodes           : int
    parallel        : bool
    par_backend     : None | str
    ranks           : int
    collective      : None | bool
    language        : str
    format          : str
    engine          : str
    extension       : str
    datatype        : list
    var_to_bm       : str | list
    total_filesize  : int
    unit            : str
    filesize_var    : list
    chunksize_var   : list
    iterations      : int
    internal_i      : int
    current_time    : str
    
    
    def __init__(self, 
                 handler_id     : str, 
                 run_config     : dict,
                 bm_config      : dict,
                 global_config  : dict,
                 nodes          : int,
                 slurm_options  : str,
                 parallel       : bool,
                 collective     : None | bool, 
                 ranks          : int, 
                 requested      : dict, 
                 spack_manager  : SpackManager,
                 logger         : logging.Logger,
                 paths          : dict,
                 ):
        
        
        # Object config
        self.current_time   = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.logger         = logger
        self.handler_id     = handler_id
        self.bm_config      = bm_config
        self.global_config  = global_config
        self.bash_location  = "slurm-config"
        self.slurm_options  = slurm_options
        self.spack_manager  = spack_manager
        
        # Source code
        try:
            self.create     = bm_config["create"]
        except:
            self.create     = ""
        
        try:
            self.compile    = bm_config["compile"]
            
            self.compile_command = ""
            try:
                self.compile_command = bm_config["compile_command"]
            except:
                raise ValueError("Missing compile command for benchmark requiring compilation")
        except KeyError:
            self.compile    = False
            
            
        self.src            = bm_config["source"]
        
        
        # Benchmark config
        self.run_config     = run_config
        self.nodes          = nodes
        self.parallel       = parallel
        self.par_backend    = requested["par_backend"]
        self.collective     = collective
        self.ranks          = ranks
        self.language       = requested["language"]
        self.format         = requested["format"]
        self.engine         = f"{self.format}-{self.language}-parallel" if self.parallel == True else f"{self.format}-{self.language}"
        self.extension      = bm_config["extension"]
        
        try:
            config_par_backend = self.bm_config["par_backend"]
        except:
            config_par_backend = None
        
        
        datatype    = []
        for _, item in run_config.items():
            if any(isinstance(x, str) for x in item):
                datatype.append(item[-1])
            else:
                datatype.append("f8")
        self.datatype       = datatype
        
        self.var_to_bm      = self.global_config["variable_to_benchmark"]
        self.iterations     = self.global_config["iterations"]
        self.internal_i     = 1
        self.no_caching     = False
        self.local          = False
        
        
        # Assemble ID
        id_str = (str(self.run_config) 
                  + str(config_par_backend) 
                  + str(self.par_backend) 
                  + str(self.bm_config["parallel"]) 
                  + str(self.parallel) 
                  + str(self.bm_config["format"])
                  + str(self.format)
                  + str(self.ranks) 
                  + str(self.var_to_bm)
                  + str(self.collective)
                  + str(self.nodes)
                  + str(self.spack_manager.target)
                  + str(self.spack_manager.additional)
                  + str(self.spack_manager.compiler)
                  + str(self.spack_manager.packages)
                  + str(self.spack_manager.language)
                  + str(self.spack_manager.env_name)
                  
                  # Reasoning: If source code changes, do not consider the same benchmark even if it might be functionally the same, could still have an effect in performance
                  + self.src
                  )
        
        self.id             = hashlib.sha256(id_str.encode()).hexdigest()
        
        self.use_path       = Path(paths["path_to_tmp"])
        self.root_path      = Path(paths["path_to_root"])
        self.results_path   = Path(paths["path_to_results"])
        self.dir_path       = Path(f"{self.use_path}/{str(self.id)}")
        
        
        # Benchmark info 
        self.location       = f"{self.id}.{self.extension}"
        
        filesize_per_var    = [(key, calc_size_unit(item[0])) for key, item in run_config.items() if key in self.var_to_bm] 
        
        total_filesize = 0
        for filesize in filesize_per_var:
            total_filesize += filesize[1][0]
        
        self.total_filesize = total_filesize   # type: ignore
        self.unit           = filesize_per_var[0][1][1] 
        self.filesize_var   = filesize_per_var   
        self.chunksize_var  = [(key, calc_size_unit(item[1])) for key, item in run_config.items() if key in self.var_to_bm] 
        self.show_metdata   = True
        
        
        # Environment config
        self.__checkpoint   = yaml
        self.__profiler     = False
        try:
            self.__profiler = self.global_config["profiler"]
        except:
            pass
        
        if self.__profiler == True:
            self.profiling_path = Path(paths["path_profiling"]) 
        
        self.logger.info(bcolors.OKBLUE +  
                        f"Managing Benchmark with; file-structure: {run_config}, "
                        f"nodes: {self.nodes}, "
                        f"datatype: {self.datatype}, "
                        f"parallel: {self.parallel}, " 
                        f"collective: {self.collective}, "
                        f"ranks: {self.ranks}, "
                        f"par_backend: {self.par_backend}, "
                        f"language: {self.language}, "
                        f"format: {self.format}, " 
                        f"iterations: {self.iterations}, "
                        f"in env: {self.spack_manager.env_name}. "
                        f"It will be stored in {self.use_path}" + bcolors.ENDC
            )   
    
    
    def run(self):
        self.dir_path.mkdir(parents=True)

        try:

            if self.show_metdata:
                with open(f"{self.dir_path}/metadata.yaml", "w") as f:
                    yaml.safe_dump(asdict(self), f)

            
            if self.__profiler == True:
                new_profiler_path = Path(f"{self.profiling_path.absolute()}/{self.id}")
                new_profiler_path.mkdir(parents=True, exist_ok=True)
                self.profiling_path = new_profiler_path
            

            if self.create != None:  
                self.__create_file()


            self.__execute_file()
        
        finally:
            shutil.rmtree(path=self.dir_path)
            pass
            
        return self.id, asdict(self)

 
    def __create_file(self):
        
        # Get create command
        create_commands = self.bm_config["create_command"]
        
        create_command = ""
        language = self.language
        compile = self.compile
        
        # I'm to lazy to reimplement creating the given file in c again, so will just reuse easier python code as files should be identical
        if "lazy" in create_commands:
            try:
                create_command  = create_commands["lazy"][0]
                language        = create_commands["lazy"][1]
                compile         = create_commands["lazy"][2]
            except IndexError as e:
                raise IndentationError(bcolors.FAIL + "Lazy option is not a proper lazy command. A lazy command needs [command, language, compile flag (turn off/on compilation)]." + bcolors.ENDC) from e
        else:    
            try:
                create_command  = create_commands["serial"]
                
                if self.__profiler == True:
                    try:
                        create_command = create_commands["profile"]
                    except:
                        self.logger.warning("Profiler was set to \"True\" on create, but no valid profile command supplied - continuing without profiling")
                    
            except KeyError as e:
                if self.bm_config["parallel"] == True:
                    pass
                else: 
                    raise e
                
            
        # Create the file that contains code to create the given dataset
        create = self.create.replace("#MAIN", self.__replace_main(language))
        
        path_to_create_file = Path(f"{self.dir_path}/create.{language}")
        with open(path_to_create_file, "w") as file:
            file.write(create)
        
        
        create_file = f"create.{language}"
        compiled_file_info = ("", "")
        if compile == True:
            compiled_file_info = self.__compile_file(path=path_to_create_file)
            create_file = f"./{compiled_file_info[0]}"
        
        
        if self.par_backend in create_commands.keys():
            
            create_command = create_commands[self.par_backend]
            
            if self.__profiler == True:

                check_profiling = f"profile-{self.par_backend}"
                if check_profiling in create_commands:
                    create_command = create_commands[check_profiling]
                else:
                    self.logger.warning(f"Profiler was set to \"True\" on create with {self.par_backend}, but no valid profile command supplied - continuing without profiling")
        
        
        if self.par_backend != None:
            create_command = create_command + " -p"
            create_command = create_command.replace(" -n ", f" -n {self.ranks} ", count=1)

            if self.collective == True:
                create_command = create_command + f"-I {self.collective}"


        if self.__profiler == True:
            create_command = create_command.replace("<profile_path>", f"{self.profiling_path.absolute()}/{self.id}-{self.current_time}", count=1)
        

        create_command = create_command.replace("{runnable}", f"{create_file} ", count=1)
        create_command = create_command.replace(" -p", f" -p {self.parallel} ", count=1)
        
        
        if "-c" not in create_command:
            create_command = create_command + " -c 1"
        
            
        if "-l" not in create_command:
            create_command = create_command + " -l"
                
        create_command = create_command.replace(" -l", f" -l {self.location}", count=1)
        
        
        # Transform run config into 4 lists; variables (list(string)), shape (list(list(int))), chunks (list(list(int))) & datatypes (list(string)) 
        flag_variable = "-V"
        if flag_variable not in create_command:
            create_command = create_command + f" {flag_variable}"
        
        variables = ",".join(list(self.run_config.keys()))
        create_command = create_command.replace(f"{flag_variable}", f"{flag_variable} {variables}", count=1)
        
        values = list(self.run_config.values())
        shapes = []
        chunks = []
        datatypes = self.datatype
        for value in values:
            shapes.append(value[0])
            chunks.append(value[1])
            
        
        create_command = self.__append_flag(flag="-S", command=create_command, data=shapes)
        create_command = self.__append_flag(flag="-C", command=create_command, data=chunks)
        create_command = self.__append_flag(flag="-D", command=create_command, data=datatypes)
        

        if  "SLURM_JOB_ID" in os.environ and self.local == False:
            create_command = ["sbatch", self.__assemble_bash(path=self.bash_location, compile_file_info=compiled_file_info), create_command] # type: ignore
        else: 
            create_command = ["bash", self.__assemble_bash(path=self.bash_location, compile_file_info=compiled_file_info), create_command]

        self.logger.debug(f"create command used: {create_command}")
        p = subprocess.run(create_command, capture_output=True, text=True, check=True, cwd=self.dir_path)
        self.logger.error(p.stderr)
        self.logger.info(p.stdout)
    
    
    def __append_flag(self, flag: str, command: str, data: list):
        if flag not in command:
            command = command + f" {flag}"
            
        data_str = ",".join(str(x) for x in data)
        command = command.replace(f"{flag}", f"{flag} {data_str}", count=1)
        
        return command
    

    def __compile_file(self, path: Path):
        
        compile_command = self.compile_command.replace("{runnable}", f"{path.absolute()}")
        
        pattern = r"\<(.*?)\>"
        requested_packages = re.findall(string=compile_command, pattern=pattern)
        
        ld_library_path = "export LD_LIBRARY_PATH="
        for package in requested_packages:
            package_location = self.spack_manager.package_locations[package][1]
            compile_command = compile_command.replace(f"<{package}>", f"-I{package_location}/include -L{package_location}/lib -L{package_location}/lib64", count=1)
            ld_library_path = ld_library_path + f"{package_location}/lib:{package_location}/lib64:"
            
        
        
        compiled_file = f"{path.name}.out"
        compile_command = compile_command + " -Wl,--unresolved-symbols=ignore-in-object-files" + f" -o {compiled_file}"
        
        
        self.logger.debug(f"compile command used: {compile_command}")
        with open(f"{self.dir_path.absolute()}/compile.sh", "w") as file:
            file.write("#!/bin/bash\n")
            file.write(self.spack_manager.load_env())
            file.write(compile_command)
            
        p = subprocess.run(["bash", "compile.sh"], check=True, capture_output=True, cwd=self.dir_path)
        self.logger.error(p.stderr)
        self.logger.debug(p.stdout)
        
        return compiled_file, ld_library_path
  

    def __execute_file(self):
        
        # Get run command to execute the code with
        run_commands = self.bm_config["run_command"]
        
        run_command = ""
        try:
            run_command  = run_commands["serial"]
                
            if self.__profiler == True:
                try:
                    run_command = run_commands["profile"]
                except:
                    self.logger.warning("Profiler was set to \"True\" on run, but no valid profile command supplied - continuing without profiling")
            
        except KeyError as e:
            if self.bm_config["parallel"] == True:
                pass
            else: 
                raise e
        
        
        # Create the executable to run the benchmark on a given file with
        execute = self.src.replace("#MAIN", self.__replace_main(self.language))
        
        path_to_tmp_file = Path(f"{self.dir_path}/execute.{self.language}")
        with open(path_to_tmp_file, "w") as file:
            file.write(execute)
        
        
        tmp_file    = f"execute.{self.language}"
        compiled_file_info = ("", "")
        if self.compile == True:
            compiled_file_info = self.__compile_file(path=path_to_tmp_file)
            tmp_file = f"./{compiled_file_info[0]}"
    
        
        if self.par_backend in run_commands.keys():
            
            run_command = run_commands[self.par_backend]
            
            if self.__profiler == True:

                check_profiling = f"profile-{self.par_backend}"
                if check_profiling in run_commands:
                    run_command = run_commands[check_profiling]
                else:
                    self.logger.warning(f"Profiler was set to \"True\" on run with {self.par_backend}, but no valid profile command supplied - continuing without profiling")
        
        
        if self.par_backend != None:
            run_command = run_command + " -p"
            run_command = run_command.replace(" -n ", f" -n {self.ranks} ", count=1)

            if self.collective == True:
                run_command = run_command + f"-I {self.collective}"

        
        run_command = run_command.replace("{runnable}", f"{tmp_file} ", count=1)
        run_command = run_command.replace(" -i", f" -i {self.internal_i} ", count=1)
        run_command = run_command.replace(" -p", f" -p {self.parallel} ", count=1)
        
        
        if "-b" not in run_command:
            run_command = run_command + "-b 1 "
            
        if "-l" not in run_command:
            run_command = run_command + f"-l {self.location} "
            
        vars_to_bm = ",".join(self.var_to_bm)
        if "-v" not in run_command:
            run_command = run_command + "-v"
            
        run_command = run_command.replace(" -v", f" -v {vars_to_bm} ", count=1)
        

        if self.language == "c":
            
            size = []
            for var in self.var_to_bm:
                size.append(self.run_config[var][0])
            
            run_command = run_command + f"-s {sum([sum(x) for x in size])}"


        if  "SLURM_JOB_ID" in os.environ and self.local is False:
            run_command = ["sbatch", self.__assemble_bash(self.bash_location, compile_file_info=compiled_file_info), run_command] # type: ignore
        else:
            run_command = ["bash", self.__assemble_bash(self.bash_location, compile_file_info=compiled_file_info), run_command]

        self.used_nodes = []
        
        self.logger.debug(f"run command used: {run_command}")
        original_run_command = run_command[2]
        for i in range(self.iterations):
            
            if self.__profiler == True:
                tmp_command     = original_run_command
                tmp_command     = tmp_command.replace("<profile_path>", f"{self.profiling_path.absolute()}/{self.id}-{self.current_time}-{i}", count=1)
                run_command[2]  = tmp_command
                self.logger.debug(f"Run command with profiler {run_command}")
                
                
            if  "SLURM_JOB_ID" in os.environ and self.local == False:
                p = subprocess.run(run_command, capture_output=True, text=True, cwd=self.dir_path, check=True)
                self.logger.error(p.stderr)
                self.logger.info(p.stdout)
            else: 
                p = subprocess.run(run_command, capture_output=True, text=True, cwd=self.dir_path, check=True)   # type: ignore
                self.logger.error(p.stderr)
                self.logger.info(p.stdout)
                #if self.no_caching == True:
                #    new_path = Path(f"{self.dir_path}/{i}")
                #    new_path.mkdir(parents=True)
                #    
                #    current_path = Path()
                #    for path in self.dir_path.rglob(f"*.{self.extension}"):
                #        current_path = path
                #        
                #    new_file_location = shutil.move(current_path.absolute(), f"{new_path.absolute()}/{i}.{self.extension}")  
                #    
                #    #print(f"current location: {self.location} -> new location: {new_file_location}")
                #    
                #    run_command = run_command.replace(f"-l {self.location}", f"-l {new_file_location}")   # type: ignore
                #    #print(f"new run command: {run_command}")
                #    self.location = new_file_location
                
        
    def __replace_main(self, language: str) -> str:  # type: ignore
        
        match language:
            
            ##################################################################################################
            #### Py Part to be injected for #MAIN
            ##################################################################################################
            
            case "py":
                return f"""
import ast
import os
            
def main():

    parser = argparse.ArgumentParser(
        prog="Python Dataformat-Benchmark",
        description="run python based benchmark for Zarr, NetCDF4 and HDF5",
    )
    parser.add_argument("-c", "--create", type=int, default=-1, help="creates Zarr, NetCDF4 and HDF5 Files using a previously saved run format")
    parser.add_argument("-b", "--benchmark", type=int, default=-1, help="benchmark to run")
    parser.add_argument("-v", "--var_to_bm", type=str, default=None, help="var_to_bm to read, if none is provided all are read")
    parser.add_argument("-V", "--variable", type=str, default=None, help="variables to create")
    parser.add_argument("-S", "--shape", type=str, default=None, help="shapes per variable to create")
    parser.add_argument("-C", "--chunk", type=str, default=None, help="chunks per variable to create")
    parser.add_argument("-D", "--datatype", type=str, default=None, help="datatype per variable to create")
    parser.add_argument("-p", "--parallel", type=bool, default=False, help="If to run the benchmark using parallelism of any kind supported")
    parser.add_argument("-i", "--iterations", type=int, default=1, help="number of internal iterations to run the benchmark for. Will cause caching effects")
    parser.add_argument("-l", "--location", type=str, default="", help="Location where file will be create / saved")
    parser.add_argument("-I", "--input_output", type=bool, default=False, help="Set I/O to either use independent (default or False) or collective I/O (True)")
    args = parser.parse_args()
    
    match args.benchmark:
        case 1:
            
            result = bench(iterations=args.iterations, 
                            variable=args.var_to_bm, 
                            parallel=args.parallel, 
                            path=args.location, 
                            collective=args.input_output,
                            )
                    
            from mpi4py import MPI
            import json
            if args.parallel is False or MPI.COMM_WORLD.rank == 0:
                from pathlib import Path
                if Path("{self.results_path.absolute()}/{self.id}-{self.current_time}.json").exists():
                    with open("{self.results_path.absolute()}/{self.id}-{self.current_time}.json", "r") as t:
                        tmp = []
                        tmp.extend(json.load(t))
                        tmp.extend(result)
                        result = tmp

                with open("{self.results_path.absolute()}/{self.id}-{self.current_time}.json", "w") as f:
                    json.dump(result, f)
                
                nodes = []
                for _ in range(args.iterations):
                    tmp = "None"
                    if "SLURM_JOB_NODELIST" in os.environ:
                        tmp = os.environ["SLURM_JOB_NODELIST"]
                    tmp = tmp.replace("[", "")
                    tmp = tmp.replace("]", "")
                    nodes.append(tmp)
                
                if Path("{self.results_path.absolute()}/{self.id}-{self.current_time}-nodes.json").exists():
                    with open("{self.results_path.absolute()}/{self.id}-{self.current_time}-nodes.json", "r") as t:
                        tmp = []
                        tmp.extend(json.load(t))
                        tmp.extend(nodes)
                        nodes = tmp

                with open("{self.results_path.absolute()}/{self.id}-{self.current_time}-nodes.json", "w") as f:
                    json.dump(nodes, f)
                
        case -1:
            variables   = args.variable.split(",")
            shapes      = [ast.literal_eval(e) for e in args.shape.split(",")]
            chunks      = [ast.literal_eval(e) for e in args.chunk.split(",")]
            datatypes   = args.datatype.split(",")
            
            if args.create != -1:
                create(variables=variables, 
                        shapes=shapes, 
                        chunks=chunks, 
                        datatypes=datatypes, 
                        parallel=args.parallel, 
                        path=args.location, 
                        collective=args.input_output
                        )

if __name__=="__main__":
    main()
        """
            
            ##################################################################################################
            #### C Part to be injected for #MAIN
            ##################################################################################################
        
            case "c":
                tmp = """
            
#include <unistd.h>
#include <argp.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

void save_double_list_to_json(double *arr, char *file_name, size_t size)
{
    FILE *fptr;

    fptr = fopen(file_name, "r+");
    
    if (fptr == NULL)
    {
        fptr = fopen(file_name, "w");
        
        if (fptr == NULL)
        {
            fprintf(stderr, "cannot open target file %s\\n", file_name);
            exit(1);
        }
    }
    
    if(fgetc(fptr) != 91){     
        fprintf(fptr, "[");
    } else {
        (void)0;
    }
    
    int ch;
    while ((ch = fgetc(fptr)) != EOF)
    {   
        if (ch == ']')
        {
            fseek(fptr, -1, SEEK_CUR);
            fputc(',',fptr);
            fseek(fptr, 0, SEEK_CUR);
        }
    }

    for (size_t i = 0; i < size; i++)
    {
        fprintf(fptr, "%f", arr[i]);

        if (i != size - 1)
        {
            fprintf(fptr, ",");
        }
    }

    fprintf(fptr, "]");

    fclose(fptr);
}

void removeCharPointer(char *str, char c) {
    char *rS = str;
    char *rD = str;
    for(; *rD != 0; rS++) {
        if(*rS == c && *rS)
            continue;
        *rD = *rS;
        rD++;
        if(!*rS)
            return;
    }
}

void save_string_list_to_json(char **arr, char *file_name, size_t size)
{
    FILE *fptr;

    fptr = fopen(file_name, "r+");
    
    if (fptr == NULL)
    {
        fptr = fopen(file_name, "w");
        
        if (fptr == NULL)
        {
            fprintf(stderr, "cannot open target file %s\\n", file_name);
            exit(1);
        }
    }
    
    if(fgetc(fptr) != 91){     
        fprintf(fptr, "[");
    } else {
        (void)0;
    }
    
    int ch;
    while ((ch = fgetc(fptr)) != EOF)
    {   
        if (ch == ']')
        {
            fseek(fptr, -1, SEEK_CUR);
            fputc(',',fptr);
            fseek(fptr, 0, SEEK_CUR);
        }
    }

    for (size_t i = 0; i < size; i++)
    {   
        char * tmp = arr[i];
        removeCharPointer(tmp, '[');
        removeCharPointer(tmp, ']');
        fprintf(fptr, "\\"%s\\"", tmp);

        if (i != size - 1)
        {
            fprintf(fptr, ",");
        }
    }

    fprintf(fptr, "]");

    fclose(fptr);
}


typedef struct args_t
{
    int create;
    int benchmark;
    char *var_to_bm;
    char *variable;
    hsize_t size;
    char *shape;
    char *chunk;
    char *datatype;
    int parallel;
    int input_output;
    int iterations;
    char *location;
} args_t;

static int parse_opt(int key, char *arg, struct argp_state *state)
{
    args_t *arguments = state->input;

    switch (key)
    {
    case 'c':
        arguments->create = atoi(arg);
        break;
    case 'b':
        arguments->benchmark = atoi(arg);
        break;
    case 'v':
        arguments->var_to_bm = arg;
        break;
    case 'V':
        arguments->variable = arg;
        break;
    case 's':
        arguments->size = strtoull(arg, NULL, 10);
        break;
    case 'S':
        arguments->shape = arg;
        break;
    case 'C':
        arguments->chunk = arg;
        break;
    case 'D':
        arguments->datatype = arg;
        break;
    case 'p':
        arguments->parallel = strtoull(arg, NULL, 10);
        break;
    case 'i':
        arguments->iterations = atoi(arg);
        break;
    case 'I':
        arguments->input_output = atoi(arg);
        break;
    case 'l':
        arguments->location = arg;
        break;
    case ARGP_KEY_ARG:
        return 0;
    default:
        return ARGP_ERR_UNKNOWN;
    }
    return 0;
}

static struct argp_option options[] = {
    {"create file", 'c', "NUM", 0, "If to create a file"},
    {"benchmark",   'b', "NUM", 0, "If to run benchmark"},
    {"var_to_bm",   'v', "c",   0, "Variables within a file to benchmark"},
    {"variable",    'V', "c",   0, "Variables the file should contain"},
    {"size",        's', "NUM", 0, "Specifiy the size of the file to read"},
    {"shape",       'S', "c",   0, "Specifiy the shapes of the file you want to create as list of lists"},
    {"chunk",       'C', "c",   0, "Specifiy the chunksize of the file you want to create as list of lists"},
    {"datatype",    'D', "c",   0, "Data types each variable should have as list"},
    {"parallel",    'p', "NUM", 0, "If to use parallelism or not"},
    {"iterations",  'i', "NUM", 0, "Ammount of iterations the benchmark should run"},
    {"input-output",'I', "NUM", 0, "Set I/O to either use independent (default or False) or collective I/O (True)"},
    {"location",    'l', "c",   0, "Location where file is going to be created / read from"},
    {0}};

hsize_t word_count(char *smth, char delim)
{
    hsize_t count = 1;
    for (hsize_t x = 0; x < strlen(smth); x++)
        if (smth[x] == delim)
            count++;
    return count;
}

int get_chars(char *smth, hsize_t amount, char **buf)
{
    hsize_t i = 0;
    char *token;
    char *rest = smth;

    while ((token = strtok_r(rest, ",", &rest)))
    {
        if (i == amount)
            break;
        buf[i] = calloc(strlen(token), sizeof(char *));
        strcpy(buf[i], token);
        i++;
    }
    return 0;
}

int get_list_contents(char *smth, hsize_t *buf)
{
    hsize_t i = 0;
    char tmp_char[CHAR_MAX] = "";
    bool flag = false;
    for (hsize_t x = 0; x < strlen(smth); x++)
    {
        if (smth[x] != 44) // ASCII ","
        {
            if (smth[x] == 91) // ASCII "["
                flag = true;
            if (smth[x] == 93) // ASCII "]"
                flag = false;

            if (flag == true && smth[x] != 91)
            {
                char tmp = smth[x];
                strncat(tmp_char, &tmp, 1);
            }
        }
        else
        {
            buf[i] = (hsize_t)strtoull(tmp_char, NULL, 10);
            tmp_char[0] = '\\0';
            i++;
        }
    }
    buf[i] = (hsize_t)strtoull(tmp_char, NULL, 10);
    return 0;
}

int get_individual_as_jagged(char *smth, hsize_t size, hsize_t **buf, hsize_t *jagged_size)
{
    char *token;
    char *rest = smth;

    hsize_t current_var = 0;
    while ((token = strtok_r(rest, "-", &rest)))
    {
        if (current_var == size)
            break;
        hsize_t dims = word_count(token, ',');

        buf[current_var] = calloc(dims, sizeof(hsize_t));
        int res = get_list_contents(token, buf[current_var]);
        jagged_size[current_var] = dims;
        current_var++;
    }
    return 0;
}

int main(int argc, char *argv[])
{
    struct argp argp = {options, parse_opt};

    args_t arguments;
    arguments.create = -1;
    arguments.benchmark = -1;
    arguments.var_to_bm = "[]";
    arguments.variable = "[]";
    arguments.size = 134217728;
    arguments.shape = "[]";
    arguments.chunk = "[]";
    arguments.datatype = "[]";
    arguments.parallel = 1;
    arguments.iterations = 1;
    arguments.location = "test.c";

    printf("Parsing: %d, var_to_bm: %s, variables: %s, shapes: %s, chunks: %s, datatypes: %s, parallel: %d, iterations: %d\\n", arguments.benchmark, arguments.var_to_bm, arguments.variable, arguments.shape, arguments.chunk, arguments.datatype, arguments.parallel, arguments.iterations);
    argp_parse(&argp, argc, argv, 0, 0, &arguments);
    
    hsize_t size = arguments.size;

    char *location = arguments.location;
    int iterations = arguments.iterations;
    int res;

    // get variables to benchmark
    hsize_t var_bm_count = word_count(arguments.var_to_bm, ',');

    // get variables
    hsize_t var_count = word_count(arguments.variable, ',');

    // get shapes
    hsize_t **shapes = calloc(var_count, sizeof(hsize_t *));
    hsize_t shapes_size[var_count];

    // get chunks
    hsize_t **chunks = calloc(var_count, sizeof(hsize_t *));
    hsize_t chunks_size[var_count];

    printf("Parsing: %d, parallel: %d, iterations: %d\\n", arguments.benchmark, arguments.parallel, arguments.iterations);

    // arguments parsing for creation of file
    switch (arguments.create)
    {
    case -1:
        break;
    case 1:

        // get variables
        char **variables = calloc(var_count, sizeof(char *));
        res = get_chars(arguments.variable, var_count, variables);


        // get shapes
        res = get_individual_as_jagged(arguments.shape, var_count, shapes, shapes_size);


        // get chunks
        res = get_individual_as_jagged(arguments.chunk, var_count, chunks, chunks_size);


        // get datatypes
        printf("word count: %ld\\n", var_count);
        char **datatypes = calloc(var_count, sizeof(char *));
        res = get_chars(arguments.datatype, var_count, datatypes);


        printf("Creating hdf5 file\\n");
        create(argc, argv, false, variables, shapes, chunks, datatypes, location);

        // Free variables, datatypes, shape and chunks
        for (int i = 0; i < var_count; i++)
        {
            free(variables[i]);
        }
        free(variables);

        for (int i = 0; i < var_count; i++)
        {
            free(datatypes[i]);
        }
        free(datatypes);

        for (int i = 0; i < var_count; i++)
        {
            free(shapes[i]);
        }
        free(shapes);

        for (int i = 0; i < var_count; i++)
        {
            free(chunks[i]);
        }
        free(chunks);
        break;
    case ARGP_KEY_ARG:
        return 0;
    default:
        return ARGP_ERR_UNKNOWN;
    }

    // arguments parsing for benchmarks
    switch (arguments.benchmark)
    {
    case -1:
        printf("No benchmark specified, exiting programm now \\n");
        break;
    case 1:
        // get variables to benchmark
        char **vars_to_bm = calloc(var_bm_count, sizeof(char *));
        res = get_chars(arguments.var_to_bm, var_bm_count, vars_to_bm);

        
        double * result = calloc(iterations, sizeof(double));
        char ** nodes   = calloc(iterations, sizeof(char *));

        printf("Running hdf5 benchmark for %d iterations reading %ld elements\\n", iterations, size);
        bench(argc, argv, size, vars_to_bm, iterations, location, result);

        // Free variables to benchmark
        for (int i = 0; i < var_bm_count; i++)
        {
            free(vars_to_bm[i]);
        }
        free(vars_to_bm);
        
        <result-collection>
        
        free(result);
        free(nodes);
        break;
    case ARGP_KEY_ARG:
        return 0;
    default:
        return ARGP_ERR_UNKNOWN;
    }
    
    //MPI_FINALIZE
    
    return 0;
}
"""    

                case_serial = """               
        save_double_list_to_json(result, "<result-path>.json", iterations);
        
        for(int i = 0; i < iterations; i++){
            if (getenv("SLURM_JOB_NODELIST") != NULL) {
                nodes[i] = getenv("SLURM_JOB_NODELIST");
            } else {
                char str[] = "None";
                nodes[i] = str;
            }
        }
        save_string_list_to_json(nodes, "<nodes-path>.json", iterations);
"""     

                case_mpi = """
        int mpi_rrank;
        MPI_Comm comm = MPI_COMM_WORLD;
        MPI_Comm_rank(comm, &mpi_rrank);

        printf("rank: %d \\n", mpi_rrank);
        if (mpi_rrank == 0)
        {
            save_double_list_to_json(result, "<result-path>.json", iterations);
            
            for(int i = 0; i < iterations; i++){
                
                if (getenv("SLURM_JOB_NODELIST") != NULL) {
                    nodes[i] = getenv("SLURM_JOB_NODELIST");
                } else {
                    char str[] = "None";
                    nodes[i] = str;
                }
            }
            save_string_list_to_json(nodes, "<nodes-path>.json", iterations);
        }
"""               
                if self.parallel == True and self.par_backend == "MPI":
                    tmp = tmp.replace("//MPI_FINALIZE", "MPI_Finalize();", count=1)
                    tmp = tmp.replace("<result-collection>", case_mpi, count=1)
                else:
                    tmp = tmp.replace("<result-collection>", case_serial, count=1)
    
                tmp = tmp.replace("<result-path>", f"{self.results_path.absolute()}/{self.id}-{self.current_time}", count=1)
                tmp = tmp.replace("<nodes-path>", f"{self.results_path.absolute()}/{self.id}-{self.current_time}-nodes", count=1)
                return tmp
           

    def __assemble_bash(self, path: str, compile_file_info: tuple):
        
        
        if  "SLURM_JOB_ID" in os.environ and self.local is False:
            self.slurm_options = self.slurm_options.replace("#SBATCH --nodes=", "#")
            self.slurm_options = self.slurm_options.replace("#SBATCH --job-name=", "#")
            
            if "#SBATCH --wait" not in self.slurm_options:
                self.slurm_options = self.slurm_options + "#SBATCH --wait\n"
            
            self.slurm_options = self.slurm_options + f"#SBATCH --job-name={self.format.replace(' ', '')}-{self.total_filesize}{self.unit}-{str(self.run_config).replace(' ', '')}\n"

            if "#SBATCH --nodes=" not in self.slurm_options:
                self.slurm_options = self.slurm_options + f"#SBATCH --nodes={self.nodes}\n"
        
        else:
            self.slurm_options = ""
            
            
        bash_location = f"{path}.sh"
        with open(Path(f"{self.dir_path}/{bash_location}"), "w") as file:
            file.write(f"""#!/bin/bash

{self.slurm_options}
                       
# Begin of section with executable commands
ls -lh

#sbcast -f "$bin" /tmp/bin
#export $bin="/tmp/bin"

. {self.root_path}/spack/share/spack/setup-env.sh
. $(spack location -i lmod)/lmod/lmod/init/profile

source {self.spack_manager.env_location.absolute()}/.venv/bin/activate

{self.spack_manager.load_env()}

{compile_file_info[1]}

$1

mpi_enabled=$2
w=true

if [ "$mpi_enabled" = "$w" ]; then

    export OMPI_MCA_osc="ucx"
    export OMPI_MCA_pml="ucx"
    export OMPI_MCA_btl="self"
    export UCX_HANDLE_ERRORS="bt"
    export OMPI_MCA_pml_ucx_opal_mem_hooks=1
    
    export OMPI_MCA_io="romio321"          # basic optimisation of I/O
    export UCX_TLS="shm,rc_mlx5,rc_x,self" # for jobs using LESS than 150 nodes
    #export UCX_TLS="shm,dc_mlx5,dc_x,self" # for jobs using MORE than 150 nodes
    export UCX_UNIFIED_MODE="y"            
    
    export OMPI_MCA_coll_tuned_use_dynamic_rules="true"
    export OMPI_MCA_coll_tuned_alltoallv_algorithm=2
    
fi
spack env deactivate                     
"""
)
            
            return bash_location
        