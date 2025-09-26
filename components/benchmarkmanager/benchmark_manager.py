from func.dev_utils import calc_size_unit
from spackmanager import SpackManager
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
    
    handler_id      : str
    id              : str
    run_config      : dict
    parallel        : bool
    par_backend     : None | str
    ranks           : None | int
    collective      : bool
    language        : str
    format          : str
    engine          : str
    extension       : str
    range           : list
    stepsize        : int
    datatype        : list
    var_to_bm       : str | list
    total_filesize  : int
    unit            : str
    filesize_var    : list
    chunksize_var   : list
    iterations      : int
    internal_i      : int
    bm_config       : dict
    
    
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
        
        try:
            config_par_backend = bm_config["par_backend"]
        except:
            config_par_backend = None
            
        id_str = str(run_config) + str(config_par_backend) + str(par_backend) + str(bm_config["parallel"]) + str(parallel) + str(bm_config["format"]) + str(format) + str(ranks) + str(var_to_bm)
        self.id           = hashlib.sha256(id_str.encode()).hexdigest()
        
        self.use_path       = use_path
        self.results_path   = results_path
        self.dir_path       = Path(f"{self.use_path}/{str(self.id)}")
        self.bm_config      = bm_config
        self.sbatch_config  = "/work/ku0598/k203191/dkrz_dev/slurm-scripts/run-anything.sh"
        
        
        # Benchmark config
        self.run_config     = run_config
        self.parallel       = parallel
        self.par_backend    = par_backend
        self.ranks          = ranks
        self.collective     = False
        self.language       = language
        self.format         = format
        
        self.engine         = f"{self.format}-{self.language}-parallel" if self.parallel == True else f"{self.format}-{self.language}"
        self.extension      = extension
        self.range          = range
        self.stepsize       = stepsize
        self.datatype       = datatype
        self.var_to_bm      = var_to_bm
        self.iterations     = iterations
        self.internal_i     = 1
        self.no_caching     = False
        self.local          = False
        self.location       = f"{self.id}.{self.extension}"
        
        
        # Benchmark info 
        filesize_per_var    = [(key, calc_size_unit(item[0])) for key, item in run_config.items() if key in self.var_to_bm] 
        
        total_filesize = 0
        for filesize in filesize_per_var:
            total_filesize += filesize[1][0]  # type: ignore
        
        self.total_filesize = total_filesize  # type: ignore
        self.unit           = filesize_per_var[0][1][1]  # type: ignore
        self.filesize_var   = filesize_per_var   
        self.chunksize_var  = [(key, calc_size_unit(item[1])) for key, item in run_config.items() if key in self.var_to_bm] 
        self.show_metdata   = True 
          
        
        # Source code
        try:
            self.create     = bm_config["create"]
        except:
            self.create     = None
        
        try:
            self.compile    = bm_config["compile"]
            try:
                self.compile_command = bm_config["compile_command"]
            except:
                raise ValueError("Missing compile command for benchmark requiring compilation")
        except KeyError:
            self.compile    = False
            
            
        self.src            = bm_config["source"]
        
        
        # Environment config
        self.__checkpoint   = yaml
        self.__node         = int
        self.__node_info    = yaml
        self.__profiler     = bool
    
    
    def run(self):
        self.dir_path.mkdir(parents=True)

        try:
            with open(f"{self.dir_path}/run_config.json", "w") as f:
                json.dump(self.run_config, f)

            self_dict = asdict(self)  

            if self.show_metdata:
                with open(f"{self.dir_path}/metadata.yaml", "w") as f:
                    yaml.safe_dump(self_dict, f)


            if self.create != None:  
                self.__create_file()


            #self.__execute_file()
        
        finally:
            shutil.rmtree(path=self.dir_path)
        
        return self.id, self_dict

 
    def __create_file(self):
        create = self.create.replace("#MAIN", self.__replace_main(self.language)) # type: ignore
        
        path_to_create_file = Path(f"{self.dir_path}/create.{self.language}")
        with open(path_to_create_file, "w") as file:
            file.write(create)
        
        
        create_file = f"create.{self.language}"
        if self.compile == True:
            compiled_file = self.__compile_file(path=path_to_create_file)
            create_file = f"./{compiled_file}"
        
        
        create_commands = self.bm_config["create_command"]
        create_command  = create_commands["serial"]
        
        
        if self.par_backend in create_commands.keys():
            create_command = create_commands[str(self.par_backend)]
            create_command = create_command + "-p"
            create_command = create_command.replace("-n ", f"-n {self.ranks} ")
            
            if self.collective == True:
                create_command = create_command + f"-o {self.collective}"


        create_command = create_command.replace("{runnable}", f"{create_file} ")
        create_command = create_command.replace("-p", f"-p {self.parallel} ")
        
        
        if "-c" not in create_command:
            create_command = create_command + " -c 1"
        
            
        if "-l" not in create_command:
            create_command = create_command + " -l"
                
        create_command = create_command.replace("-l", f"-l {self.location}")
        
        
        # Transform run config into 4 lists; variables (list(string)), shape (list(list(int))), chunks (list(list(int))) & datatypes (list(string)) 
        
        print(list(self.run_config.values()))
        
        flag_variable = "-V"
        if flag_variable not in create_command:
            create_command = create_command + f" {flag_variable}"
        
        variables = ",".join(list(self.run_config.keys()))
        create_command = create_command.replace(f"{flag_variable}", f"{flag_variable} {variables}")
        
        values = list(self.run_config.values())
        shapes = []
        chunks = []
        datatypes = []
        for value in values:
            shapes.append(value[0])
            chunks.append(value[1])
            datatypes.append(value[2])
            
        
        create_command = self.__append_flag(flag="-S", command=create_command, data=shapes)
        create_command = self.__append_flag(flag="-C", command=create_command, data=chunks)
        create_command = self.__append_flag(flag="-D", command=create_command, data=datatypes)
        
        
        if  "SLURM_JOB_ID" in os.environ and self.local == False:
            create_command = ["sbatch", self.sbatch_config, create_command]
        else: 
            create_command = create_command.split()

        print(create_command)
        p = subprocess.run(create_command, capture_output=True, text=True, cwd=self.dir_path)
        print(p.stderr)
        print(p.stdout)
    
    
    def __append_flag(self, flag: str, command: str, data: list):
        if flag not in command:
            command = command + f" {flag}"
            
        data_str = ",".join(str(x) for x in data)
        command = command.replace(f"{flag}", f"{flag} {data_str}")
        
        return command
    

    def __compile_file(self, path: Path):
        
        compile_command = self.compile_command.replace("{runnable}", f"{path.absolute()}")
        
        compiled_file = f"{path.name}.out"
        compile_command = compile_command + " -Wl,--unresolved-symbols=ignore-in-object-files" + f" -o {compiled_file}"
        
        print(compile_command)
        p = subprocess.run(compile_command.split(), capture_output=True, text=True, cwd=self.dir_path, check=True)
        print(p.stderr)
        print(p.stdout)
        
        return compiled_file
  

    def __execute_file(self):
        
        execute = self.src.replace("#MAIN", self.__replace_main(self.language))
        execute = execute.replace("#RESULT", self.__replace_result(self.language))
        
        path_to_tmp_file = Path(f"{self.dir_path}/execute.{self.language}")
        with open(path_to_tmp_file, "w") as file:
            file.write(execute)
        
        
        tmp_file    = f"execute.{self.language}"
        if self.compile == True:
            compiled_file = self.__compile_file(path=path_to_tmp_file)
            tmp_file = f"./{compiled_file}"
        
        
        run_commands = self.bm_config["run_command"]
        run_command  = run_commands["serial"]
        
        if self.par_backend in run_commands.keys():
            run_command = run_commands[str(self.par_backend)]
            run_command = run_command +  "-p"
            run_command = run_command.replace("-n", f"-n {self.ranks} ")
            
            if self.collective == True:
                run_command = run_command + f"-o {self.collective}"

        
        tmp = ",".join(self.var_to_bm)    
        run_command = run_command.replace("-v", f"-v {tmp} ")
        run_command = run_command.replace("{runnable}", f"{tmp_file} ")
        run_command = run_command.replace("-i", f"-i {self.internal_i} ")
        run_command = run_command.replace("-p", f"-p {self.parallel} ")
        
        
        if "-b" not in run_command:
            run_command = run_command + " -b 1"
            
        if "-l" not in run_command:
                run_command = run_command + f" -l {self.location}"


        if  "SLURM_JOB_ID" in os.environ and self.local is False:
            run_command = ["sbatch", self.sbatch_config, run_command]


        for i in range(self.iterations):
            
            if  "SLURM_JOB_ID" in os.environ and self.local == False:
                p = subprocess.run(run_command, capture_output=True, text=True, cwd=self.dir_path)
                print(p.stderr)
                print(p.stdout)
            else: 
                p = subprocess.run(run_command.split(), capture_output=True, text=True, cwd=self.dir_path)  # type: ignore
                print(p.stderr)
                print(p.stdout)

                if self.no_caching == True:
                    new_path = Path(f"{self.dir_path}/{i}")
                    new_path.mkdir(parents=True)
                    
                    current_path = None
                    for path in self.dir_path.rglob(f"*.{self.extension}"):
                        current_path = path
                        
                    new_file_location = shutil.move(current_path.absolute(), f"{new_path.absolute()}/{i}.{self.extension}")  # type: ignore
                    
                    #print(f"current location: {self.location} -> new location: {new_file_location}")
                    
                    run_command = run_command.replace(f"-l {self.location}", f"-l {new_file_location}")  # type: ignore
                    #print(f"new run command: {run_command}")
                    self.location = new_file_location
                
        
    def __replace_main(self, language):
        
        match language:
            
            ##################################################################################################
            #### Py Part to be injected for #MAIN
            ##################################################################################################
            
            case "py":
                return """
def main():

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
    parser.add_argument("-o", "--out_in", type=bool, default=False, help="Set I/O to either use independent (default or False) or collective I/O (True)")
    args = parser.parse_args()
    
    match args.benchmark:
        case 1:
            bench(iterations=args.iterations, variable=args.var_to_bm, parallel=args.parallel, path=args.location, collective=args.out_in)
        case -1:
            if args.create != -1:
                create(selection=args.create, parallel=args.parallel, path=args.location, collective=args.out_in)

if __name__=="__main__":
    main()
        """
            ##################################################################################################
            #### C Part to be injected for #MAIN
            ##################################################################################################
        
            case "c":
                return """
            
#include <unistd.h>
#include <argp.h>
#include <stdio.h>
#include <string.h>
    
typedef struct args_t
{
    int     create;
    int     benchmark;
    char*   var_to_bm;
    char*   variables;
    char*   shapes;
    char*   chunks;
    char*   datatypes;
    hsize_t factor;
    int     iterations;
    char*   location;
} args_t;

static int parse_opt(int key, char *arg, struct argp_state *state)
{
    args_t *arguments = state->input;

    switch (key)
    {
    case 'c':
        arguments->create       = atoi(arg);
        break;
    case 'b':
        arguments->benchmark    = atoi(arg);
        break;
    case 'i':
        arguments->iterations   = atoi(arg);
        break;
    case 'v':
        arguments->var_to_bm    = arg;
        break;
    case 'V':
        char* token;
        char* rest = arg;
        int i = 0;
        char *array[4];
        
        while (token = strtok_r(rest, ",", &rest))
        {
            array[i++] = token;
        }
        
        printf(arg);
            
        
        arguments->variables    = array;
        break;
    case 'S':
        arguments->shapes       = arg;
        break;
    case 'C':
        arguments->chunks       = arg;
        break;
    case 'D':
        arguments->datatypes    = arg;
        break;
    case 'f':
        arguments->factor       = strtoull(arg, NULL, 10);
        break;
    case 'l':
        arguments->location     = arg;
        break;
    case ARGP_KEY_ARG:
        return 0;
    default:
        return ARGP_ERR_UNKNOWN;
    }
    return 0;
}

static struct argp_option options[] = {
    {"create file",     'c', "NUM", 0, "If to create a file"},
    {"benchmark",       'b', "NUM", 0, "If to run benchmark"},
    {"var_to_bm",       'v', "c",   0, "Variables within a file to benchmark"},
    {"variables",       'V', "c",   0, "Variables the file should contain"},
    {"shapes",          'S', "c",   0, "Specifiy the shapes of the file you want to create as list of lists"},
    {"chunks",          'C', "c",   0, "Specifiy the chunksize of the file you want to create as list of lists"},
    {"datatypes",       'D', "c",   0, "Data types each variable should have as list"},
    {"factor",          'f', "NUM", 0, "Factor to multiply shape with to increase / decrease size"},
    {"iterations",      'i', "NUM", 0, "Ammount of iterations the benchmark should run"},
    {"location",        'l', "c",   0, "Location where file is going to be created / read from"},
    {0}};
    
    
int main(int argc, char **argv)
{
    struct argp argp = {options, parse_opt};

    args_t arguments;
    arguments.create    = -1;
    arguments.benchmark = -1;
    hsize_t tmpsize     = 134217728;
    arguments.var_to_bm = "[]";
    arguments.variables = "[]";
    arguments.shapes    = "[]";
    arguments.chunks    = "[]";
    arguments.datatypes = "[]";
    arguments.factor    = 1;
    arguments.iterations= 1;
    arguments.location  = "test.c";

    printf("Parsing: %d, filesize: %lu, var_to_bm: %s, variables: %s, shapes: %s, chunks: %s, datatypes: %s, factor: %lu, iterations: %d --- ", arguments.benchmark, tmpsize, arguments.var_to_bm, arguments.variables, arguments.shapes, arguments.chunks, arguments.datatypes, arguments.factor, arguments.iterations);

    argp_parse(&argp, argc, argv, 0, 0, &arguments);

    hsize_t size    = tmpsize * arguments.factor;
    char* var_to_bm= arguments.var_to_bm;
    char* variables= arguments.variables;
    char* shapes   = arguments.shapes;
    char* chunks   = arguments.chunks;
    char* datatypes= arguments.datatypes;
    char* location  = arguments.location;
    int iterations  = arguments.iterations;
    
    printf("Parsing: %d, filesize: %lu, var_to_bm: %s, variables: %s, shapes: %s, chunks: %s, datatypes: %s, factor: %lu, iterations: %d --- ", arguments.benchmark, size, var_to_bm, variables, shapes, chunks, datatypes, arguments.factor, arguments.iterations);

    // arguments parsing for creation of file
    switch (arguments.create)
    {
    case -1:
        break;
    case 1:
        printf("Creating hdf5 file with a filesize of %lu and chunksize of %s", size, chunks);
        create(false, size, 0, location);
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
        printf("No benchmark specified, exiting programm now");
        break;
    case 1:
        printf("Running hdf5 benchmark with a filesize of %lu for %d iterations", size, iterations);
        bench(size, iterations, location);
        break;
    case ARGP_KEY_ARG:
        return 0;
    default:
        return ARGP_ERR_UNKNOWN;
    }
    return 0;
}
"""
     
        
    def __replace_result(self, language):
        
        match language:
            case "py":
                return f"""from mpi4py import MPI
    if parallel is False or MPI.COMM_WORLD.rank == 0:
        from pathlib import Path
        if Path("{self.results_path.absolute()}/{self.id}.json").exists():
            with open("{self.results_path.absolute()}/{self.id}.json", "r") as t:
                result.extend(json.load(t))    
        
        with open("{self.results_path.absolute()}/{self.id}.json", "w") as f:
            json.dump(result, f)
                        """
            case "c":
                return ""