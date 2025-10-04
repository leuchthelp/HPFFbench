from components.handler import Handler
import yaml
from cProfile import Profile
from pstats import SortKey, Stats


#paths
path_to_config = "components/handler/"

paths = {
    "path_to_benchmarks": "components/benchmarks",
    "path_to_tmp"       : "components/tmp",
    "path_to_config"    : "components/handler/",
    "path_to_visuals"   : "components/visualize",
    "path_to_plotting"  : "components/visualize/plotting",
    "path_to_results"   : "components/results",     
}
   
def main():
    
    setup = {    
            #"run06": {"X": ([faktor * 512, 512, 512], [faktor * 512, 512, 128])},
            #"run07": {"X": ([faktor * 512, 512, 512], [faktor * 512, 512, 256])},
            #"run08": {"X": ([faktor * 512, 512, 512], [faktor * 512, 512, 512])},
            
            #"run11": {"X": ([512, 512, 512], [512, 1, 1])},
            #"run12": {"X": ([512, 512, 512], [512, 8, 8])},
            #"run13": {"X": ([512, 512, 512], [512, 16, 16]), "Y": ([10, 10], [2, 2])},
            #"run14": {"X": ([512, 512, 512], [512, 32, 32]), "Y": ([10, 10], [2, 2])},
            #"run15": {"X": ([512, 512, 512], [512, 64, 64]), "Y": ([10, 10], [2, 2])},
            #"run16": {"X": ([512, 512, 512], [512, 128, 128]), "Y": ([10, 10], [2, 2])},
            #"run17": {"X": ([512, 512, 512], [512, 256, 256]), "Y": ([10, 10], [2, 2])},
            #"run18": {"X": ([512, 512, 512], [512, 512, 512]), "Y": ([10, 10], [2, 2])}, 
            }

    tmp = {
            #"run01": {"X": [[1 * 134217728], [], "f8"], "Y": [[1 * 134217728], [], "f4"]},
            #"run02": {"X": [[1 * 134217728], [], "f8"]},
            "run03": {"X": [[1 * 134217728], []],},
            
            #"run04": {"X": [[10 * 134217728], []]},
            #"run05": {"X": [[20 * 134217728], []]},
            #"run06": {"X": [[30 * 134217728], []]},
            #"run07": {"X": [[40 * 134217728], []]},
            #"run08": {"X": [[50 * 134217728], []]},
            #"run09": {"X": [[60 * 134217728], []]},
            #"run10": {"X": [[70 * 134217728], []]},
            #"run11": {"X": [[80 * 134217728], []]},
            #"run12": {"X": [[90 * 134217728], []]},
            #"run13": {"X": [[100 * 134217728], []]},
    }
    
    slurm_options = """
#SBATCH --wait
#SBATCH --partition=compute
#SBATCH --account=ku0598
#SBATCH --constraint="[cell02]"
#SBATCH --nodes=1
#SBATCH --mem=0
#SBATCH --cpu-freq=High
#SBATCH --distribution=block:cyclic
#SBATCH --time=02:00:00
#SBATCH --exclusive
#SBATCH --output=log/log-%j/log.%j.txt
#SBATCH --error=log/log-%j/log.%j.err
    """
    
    new_setup = {
        "formats"               : [{"hdf5": "subfiling"}, {"hdf5": "async"}, "hdf5"],
        "languages"             : ["c"],
        "paths"                 : paths,
        "iterations"            : 2,
        "runs"                  : tmp,
        "parallel"              : "Both",
        "par_backend"           : "MPI",
        "ranks"                 : [2],
        "variable_to_benchmark" : ["X"],
        "only data"             : False,
        "max processes"         : 20,
        "slurm options"         : slurm_options,
    }
    
    with open(f"{path_to_config}config.yaml", "w") as file:
        yaml.dump(new_setup, file)
      
    with Profile() as profile:  
        handler = Handler(path_to_config=path_to_config)
        stats = Stats(profile).strip_dirs()
        #stats.sort_stats(SortKey.CUMULATIVE).print_stats(20)
        #stats.sort_stats(SortKey.CALLS).print_stats(20)
        #stats.sort_stats(SortKey.TIME).print_stats(20)

if __name__=="__main__":
    main()