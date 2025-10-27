from components.handler import Handler
from cProfile import Profile
from pstats import SortKey, Stats
import yaml
import os
import logging


#paths
path_to_config = "components/handler/"

paths = {
    "path_to_benchmarks": "components/benchmarks",
    "path_to_tmp"       : "components/tmp",
    "path_to_config"    : "components/handler",
    "path_to_visuals"   : "components/visualize",
    "path_to_root"      : os.path.dirname(os.path.realpath(__file__)),
    "path_to_results"   : "components/results", 
    #"path_profiling"    : "components/profiling",   
}
   
def main():

    tmp = {
            #"run01": {"X": [[1 * 134217728], [], "f8"], "Y": [[1 * 134217728], [], "f4"]},
            #"run02": {"X": [[1 * 134217728], [], "f8"]},
            "run03": {"X": [[1 * 134217728], []],},
            #"run03": {"X": [[5 * 134217728], []],},
        
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
#SBATCH --mem=0
#SBATCH --cpu-freq=High
#SBATCH --distribution=block:cyclic
#SBATCH --time=02:00:00
#SBATCH --exclusive
#SBATCH --output=log/log-%j/log.%j.txt
#SBATCH --error=log/log-%j/log.%j.err
"""
    
    spack_envs = {
        "test-env-1" : {
            "target"    : ["hdf5", {"hdf5": "subfiling"}, "netcdf4", "zarr"],
            "language"  : ["py", "c"],
            "packages"  : {
                "python": {"versions" : ["3.11.14"],
                           "fresh"    : True
                            },
                
                "openmpi": {"versions" : ["5.0.8"],
                            "fresh"    : True
                            },
                
                "hdf5": {"versions" : ["1.14.6"],
                         "variants" : "~cxx~fortran+hl~ipo~java~map+mpi+shared+subfiling~szip+threadsafe+tools",
                         },
                
                "argobots": {"versions" : ["main"],
                             "fresh"    : True
                            },
                
                "netcdf-c": {"versions" : ["4.9.2"],
                             "variants" : "build_system=cmake",
                            },
                
                "py-mpi4py": {"versions" : ["4.0.1"],
                            },
                
                "py-h5py": {"versions" : ["3.14.0"],
                            },
                
                "py-netcdf4": {"versions" : ["1.7.1"],
                            },
            },
            "compiler": "gcc@13",
            "additional": "pip install zarr==3.0.5 py-spy",
            #"install": True
            },
        
        "test-env-async" : {
            "target"    : [{"hdf5": "async"}],
            "language"  : ["c"],
            "packages"  : {
                "python": {"versions" : ["3.11.14"],
                           "fresh"    : True
                            },
                
                "openmpi": {"versions" : ["5.0.8"],
                            },
                
                "hdf5": {"versions" : ["1.14.6"],
                         "variants" : "~cxx~fortran+hl~ipo~java~map+mpi+shared+subfiling~szip+threadsafe+tools",
                         },
                
                "hdf5-vol-async": {"versions" : ["develop"],
                            },
                
                "argobots": {"versions" : ["main"],
                             "fresh"    : True
                            },
                
                "netcdf-c": {"versions" : ["4.9.2"],
                             "variants" : "build_system=cmake",
                            },
                
                "py-mpi4py": {"versions" : ["4.0.1"],
                            },
                
                "py-h5py": {"versions" : ["3.14.0"],
                            },
                
                "py-netcdf4": {"versions" : ["1.7.1"],
                            },
            },
            "compiler": "gcc@13",
            #"install": True
            }
    }
    
    new_setup = {
        #"formats"               : ["hdf5", "netcdf4", "zarr"],
        "formats"               : ["hdf5"],
        "languages"             : ["py"],
        "paths"                 : paths,
        "iterations"            : 1,
        "runs"                  : tmp,
        "parallel"              : False,
        "par_backend"           : "MPI",
        "ranks"                 : [8, 16, 32, 64, 128],
        "nodes"                 : [1],
        "variable_to_benchmark" : ["X"],
        "only data"             : False,
        "use spack env"         : True,
        "max processes"         : 20,
        "slurm options"         : slurm_options,
        "spack env"             : spack_envs,
        "delete envs"           : False,
    }
    
    with open(f"{path_to_config}/config.yaml", "w") as file:
        yaml.dump(new_setup, file, sort_keys=False)

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    
    with Profile() as profile:  
        handler = Handler(path_to_config=path_to_config, logger=logger)
        stats = Stats(profile).strip_dirs()
        #stats.sort_stats(SortKey.CUMULATIVE).print_stats(20)
        #stats.sort_stats(SortKey.CALLS).print_stats(20)
        #stats.sort_stats(SortKey.TIME).print_stats(20)

if __name__=="__main__":
    main()