import logging
import os

import yaml

from hpffbench.handler import Handler


def main():

    paths = {
        "path_to_benchmarks": "configs/benchmarks",
        "path_to_profilers": "configs/profilers",
        "path_to_tmp": "tmp",
        "path_to_root": os.path.dirname(os.path.realpath(__file__)),
        "path_to_results": "results/general",
        "path_res_profiling": "results/profiling",
    }

    tmp = {
        # "run01": {"X": [[1 * 134217728], [], "f8"], "Y": [[1 * 134217728], [], "f4"]},
        # "run02": {"X": [[1 * 134217728], [], "f8"]},
        # "run03": {"X": [[10 * 134217728], []],},
        # "run03": {"X": [[5 * 134217728], []],},
        # "run04": {"X": [[100 * 134217728], []]},
        "run18": {"X": [[100 * 134217728], [1 * 134217728 // 32]]},  # 32mb
        "run19": {"X": [[100 * 134217728], [1 * 134217728 // 64]]},  # 16mb
        "run20": {"X": [[100 * 134217728], [1 * 134217728 // 128]]},  # 8mb
        "run21": {"X": [[100 * 134217728], [1 * 134217728 // 256]]},  # 4mb
        "run22": {"X": [[100 * 134217728], [1 * 134217728 // 512]]},  # 2mb
        # "run05": {"X": [[20 * 134217728], []]},
        # "run06": {"X": [[30 * 134217728], []]},
        # "run07": {"X": [[40 * 134217728], []]},
        # "run08": {"X": [[50 * 134217728], []]},
        # "run09": {"X": [[60 * 134217728], []]},
        # "run10": {"X": [[70 * 134217728], []]},
        # "run11": {"X": [[80 * 134217728], []]},
        # "run12": {"X": [[90 * 134217728], []]},
        # "run13": {"X": [[100 * 134217728], []]},
    }

    slurm_options = """
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
        "test-env-1": {
            "target": ["hdf5", {"hdf5": "subfiling"}, "netcdf4", "zarr"],
            "language": ["py", "c"],
            "packages": {
                "scorep": {"versions": ["9.3"]},
                "python": {"versions": ["3.14.5"], "fresh": True},
                "openmpi": {"versions": ["5.0.10"], "fresh": True},
                "hdf5": {
                    "versions": ["1.14.6"],
                    "variants": "~cxx~fortran+hl~ipo~java~map+mpi+shared+subfiling~szip+threadsafe+tools",
                },
                "argobots": {"versions": ["main"], "fresh": True},
                "netcdf-c": {
                    "versions": ["4.10.0"],
                    "variants": "build_system=cmake",
                },
                "py-mpi4py": {
                    "versions": ["4.1.1"],
                },
                "py-h5py": {
                    "versions": ["3.16.0"],
                },
                "py-netcdf4": {
                    "versions": ["1.7.2"],
                },
            },
            "compiler": "gcc@15.3.0",
            "additional": "pip install zarr==3.2.1 scorep",
            "install": True,
        },
        "test-env-async": {
            "target": [{"hdf5": "async"}],
            "language": ["c"],
            "packages": {
                "python": {"versions": ["3.14.0"], "fresh": True},
                "openmpi": {
                    "versions": ["5.0.10"],
                },
                "hdf5": {
                    "versions": ["1.14.6"],
                    "variants": "~cxx~fortran+hl~ipo~java~map+mpi+shared+subfiling~szip+threadsafe+tools",
                },
                "hdf5-vol-async": {
                    "versions": ["develop"],
                },
                "argobots": {"versions": ["main"], "fresh": True},
                "netcdf-c": {
                    "versions": ["4.10.0"],
                    "variants": "build_system=cmake",
                },
                "py-mpi4py": {
                    "versions": ["4.1.1"],
                },
                "py-h5py": {
                    "versions": ["3.16.0"],
                },
                "py-netcdf4": {
                    "versions": ["1.7.2"],
                },
            },
            "compiler": "gcc@15.3.0",
            # "install": True
        },
    }

    new_setup = {
        "formats": ["netcdf4", "zarr", "hdf5"],
        "languages": ["py"],
        "paths": paths,
        "iterations": 5,
        "runs": tmp,
        "parallel": True,
        "collective": False,
        "par_backend": ["MPI"],
        "ranks": [16, 32, 64],
        "nodes": [1],
        "variable_to_benchmark": ["X"],
        "only_data": False,
        "no_caching": True,
        "use_spack_env": True,
        "max_processes": 20,
        "slurm_options": slurm_options,
        "spack_env": spack_envs,
        "delete_envs": False,
        "paths_create": True,
        "profiler": True,
        "profilers": ["scorep"],
        "profiler_mode": "manual",
    }

    path_to_config = "src/hpffbench/handler/config.yaml"

    with open(path_to_config, "w") as file:
        yaml.dump(new_setup, file, sort_keys=False)

    Handler(path_to_config=path_to_config, log_lvl=logging.INFO)


if __name__ == "__main__":
    main()
