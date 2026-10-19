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
        "path_to_bm_results": "results/general",
        "path_to_results": "results",
        "path_res_profiling": "results/profiling",
    }

    tmp = {
        # "run01": {"X": [[1 * 134217728], [], "f8"], "Y": [[1 * 134217728], [], "f4"]},
        # "run02": {"X": [[1 * 134217728], [], "f8"]},
        # "run03": {"X": [[10 * 134217728], []],},
        # "run03": {"X": [[5 * 134217728], []],},
        # "run04": {"X": [[100 * 134217728], []]},
        "run01": {"X": [[1 * 134217728], []]},
        # "run02": {"X": [[1 * 134217728], [1 * 134217728 // 16]]},  # 64mb
        # "run03": {"X": [[1 * 134217728], [1 * 134217728 // 32]]},  # 32mb
        # "run04": {"X": [[1 * 134217728], [1 * 134217728 // 64]]},  # 16mb
        # "run05": {"X": [[1 * 134217728], [1 * 134217728 // 128]]},  # 8mb
        # "run06": {"X": [[1 * 134217728], [1 * 134217728 // 256]]},  # 4mb
        # "run07": {"X": [[1 * 134217728], [1 * 134217728 // 512]]},  # 2mb
        # "run01-3D": {"X": [[1 * 512, 512, 512], []]},
        # "run02-3D": {"X": [[1 * 512, 512, 512], [1 * 512 // 2, 1 * 512 // 2, 1 * 512 // 2]]},  # 64mb
        # "run03-3D": {"X": [[1 * 512, 512, 512], [1 * 512 // 32]]},  # 32mb
        # "run04-3D": {"X": [[1 * 512, 512, 512], [1 * 512 // 64]]},  # 16mb
        # "run05-3D": {"X": [[1 * 512, 512, 512], [1 * 512 // 128]]},  # 8mb
        # "run06-3D": {"X": [[1 * 512, 512, 512], [1 * 512 // 256]]},  # 4mb
        # "run07-3D": {"X": [[1 * 512, 512, 512], [1 * 512 // 512]]},  # 2mb
        # "run16": {"X": [[10 * 134217728], []]},
        # "run17": {"X": [[10 * 134217728], [1 * 134217728 // 16]]},  # 64mb
        # "run18": {"X": [[10 * 134217728], [1 * 134217728 // 32]]},  # 32mb
        # "run19": {"X": [[10 * 134217728], [1 * 134217728 // 64]]},  # 16mb
        # "run10": {"X": [[10 * 134217728], [1 * 134217728 // 128]]},  # 8mb
        # "run11": {"X": [[10 * 134217728], [1 * 134217728 // 256]]},  # 4mb
        # "run12": {"X": [[10 * 134217728], [1 * 134217728 // 512]]},  # 2mb
        # "run01-3D": {"X": [[10 * 512, 512, 512], []]},
        # "run02-3D": {"X": [[10 * 512, 512, 512], [1 * 512 // 2, 1 * 512 // 2, 1 * 512 // 2]]},
        # "run03-3D": {"X": [[10 * 512, 512, 512], [1 * 512 // 4, 1 * 512 // 4, 1 * 512 // 4]]},
        # "run04-3D": {"X": [[10 * 512, 512, 512], [1 * 512 // 8, 1 * 512 // 8, 1 * 512 // 8]]},
        # "run56": {"X": [[50 * 134217728], []]},
        # "run57": {"X": [[50 * 134217728], [1 * 134217728 // 16]]},  # 64mb
        # "run58": {"X": [[50 * 134217728], [1 * 134217728 // 32]]},  # 32mb
        # "run59": {"X": [[50 * 134217728], [1 * 134217728 // 64]]},  # 16mb
        # "run50": {"X": [[50 * 134217728], [1 * 134217728 // 128]]},  # 8mb
        # "run51": {"X": [[50 * 134217728], [1 * 134217728 // 256]]},  # 4mb
        # "run52": {"X": [[50 * 134217728], [1 * 134217728 // 512]]},  # 2mb
        # "run106": {"X": [[100 * 134217728], []]},
        # "run107": {"X": [[100 * 134217728], [1 * 134217728 // 16]]},  # 64mb
        # "run108": {"X": [[100 * 134217728], [1 * 134217728 // 32]]},  # 32mb
        # "run109": {"X": [[100 * 134217728], [1 * 134217728 // 64]]},  # 16mb
        # "run100": {"X": [[100 * 134217728], [1 * 134217728 // 128]]},  # 8mb
        # "run101": {"X": [[100 * 134217728], [1 * 134217728 // 256]]},  # 4mb
        # "run102": {"X": [[100 * 134217728], [1 * 134217728 // 512]]},  # 2mb
        # "run2501": {"X": [[250 * 134217728], []]},
        # "run2502": {"X": [[250 * 134217728], [1 * 134217728 // 16]]},  # 64mb
        # "run2503": {"X": [[250 * 134217728], [1 * 134217728 // 32]]},  # 32mb
        # "run2504": {"X": [[250 * 134217728], [1 * 134217728 // 64]]},  # 16mb
        # "run2505": {"X": [[250 * 134217728], [1 * 134217728 // 128]]},  # 8mb
        # "run2506": {"X": [[250 * 134217728], [1 * 134217728 // 256]]},  # 4mb
        # "run2507": {"X": [[250 * 134217728], [1 * 134217728 // 512]]},  # 2mb
    }

    slurm_options = """
#SBATCH --partition=compute
#SBATCH --account=ku0598
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
                "spack": {
                    "scorep": {"version": "9.3"},
                    "python": {"version": "3.14.5", "fresh": True},
                    "openmpi": {"version": "5.0.10", "fresh": True},
                    "hdf5": {
                        "version": "1.14.6",
                        "variant": "~cxx~fortran+hl~ipo~java~map+mpi+shared+subfiling~szip+threadsafe+tools",
                    },
                    "argobots": {"version": "main", "fresh": True},
                    "netcdf-c": {
                        "version": "4.10.0",
                        "variant": "build_system=cmake",
                    },
                    "py-mpi4py": {
                        "version": "4.1.1",
                    },
                    "py-h5py": {
                        "version": "3.16.0",
                    },
                    "py-netcdf4": {
                        "version": "1.7.2",
                    },
                },
                "pip": {
                    "zarr": {"version": "3.2.1"},
                    "scorep": {"version": "4.5.1"},
                },
            },
            "compiler": "gcc@15.3.0",
            "install": True,
        },
    }

    xrun_params = {
        "max_number_access": 100,
    }

    new_setup = {
        "tasks": [
            "read",
            "read-random-ND",
            "read-random-ND-ranged",
            "read-random-ND-full-range",
        ],
        "formats": ["hdf5", "netcdf4"],
        "languages": ["py"],
        "paths": paths,
        "iterations": 2,
        "runs": tmp,
        "parallel": "Both",
        "collective": False,
        "par_backend": ["MPI"],
        "ranks": [4],
        "nodes": [1],
        "variable_to_benchmark": ["X"],
        "only_data": False,
        "no_caching": True,
        "use_spack_env": True,
        "max_processes": 1,
        "slurm_options": [slurm_options],
        "spack_env": spack_envs,
        "delete_envs": False,
        "paths_create": True,
        "profiler": False,
        "profilers": ["scorep"],
        "profiler_mode": "manual",
        "xrun_params": xrun_params,
    }

    path_to_config = "src/hpffbench/handler/config.yaml"

    with open(path_to_config, "w") as file:
        yaml.dump(new_setup, file, sort_keys=False)

    Handler(path_to_config=path_to_config, log_lvl=logging.DEBUG)


if __name__ == "__main__":
    main()
