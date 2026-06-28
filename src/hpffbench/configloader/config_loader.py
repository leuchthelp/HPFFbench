from typing import TypedDict
from pathlib import Path
import itertools
import logging

import yaml

from hpffbench.dev_utils import bcolors


logger = logging.getLogger(__name__)


class ProcessedPath(TypedDict):
    path: str
    skip: bool


class ConfigLoader:
    iterations: int
    slurm_options: str
    only_data: bool
    use_spack_env: bool
    delete_envs: bool

    ranks: list[int]
    nodes: list[int]
    formats: list[str]
    languages: list[str]
    variable_to_benchmark: list[str]

    par_backend: list[str] | str | None

    paths: dict[str, ProcessedPath]

    max_processes: int | None
    parallel: bool | str
    collective: bool | str

    def __init__(self, path_to_config: str | dict):
        if isinstance(path_to_config, dict):
            self.config = path_to_config

        else:
            logger.info(bcolors.OKBLUE + "Try loading config.yaml" + bcolors.ENDC)
            try:
                if ".yaml" or ".yml" not in path_to_config:
                    for file in itertools.chain(
                        Path(path_to_config).glob("*.yaml"),
                        Path(path_to_config).glob("*.yml"),
                    ):
                        path_to_config = str(file)
                        break

                file = open(f"{path_to_config}", "r")
                self.config = yaml.safe_load(stream=file)
                logger.info(
                    bcolors.OKGREEN + "Success loading config.yaml" + bcolors.ENDC
                )

            except FileNotFoundError or IsADirectoryError as e:
                FileNotFoundError(
                    bcolors.FAIL
                    + f"config.yaml not found, please ensure a valid config exists! Additional details: {e}"
                    + bcolors.ENDC
                )
            except OSError as e:
                OSError(
                    bcolors.FAIL
                    + f"Path to config.yaml could not found, please check it is valid! Additional details: {e}"
                    + bcolors.ENDC
                )
            except yaml.YAMLError as e:
                yaml.YAMLError(
                    bcolors.FAIL
                    + f"Error loading config.yaml! Additional details: {e}"
                    + bcolors.ENDC
                )

        self.formats: list[str] = self.config["formats"]
        self.languages: list[str] = self.config["languages"]
        self.iterations: int = self.config["iterations"]
        self.nodes: list[int] = self.config["nodes"]
        self.variable_to_benchmark: list[str] = self.config["variable_to_benchmark"]
        self.slurm_options: str = self.config["slurm_options"]

        if "paths" in self.config:
            paths: dict[str, str | ProcessedPath] = self.config["paths"]

            processed_paths: dict[str, ProcessedPath] = {}
            for key, value in paths.items():
                if isinstance(value, str):
                    processed_paths[key] = {"path": value, "skip": False}
                else:
                    processed_paths[key] = value

            self.paths = processed_paths
        else:
            raise KeyError

        # Optionals
        self.parallel = False
        if "parallel" in self.config:
            parallel: bool | str = self.config["parallel"]

            if parallel != "Both" and type(parallel) is not bool:
                raise ValueError(
                    bcolors.FAIL
                    + '"parallel" can only either be "True", "False" or "Both"'
                    + bcolors.ENDC
                )
            else:
                logger.info(
                    bcolors.WARNING
                    + '"parallel" is unset! Be aware parallel will be automatically set to False as long as it remains unset. You will be unable to run parallelized benchmarks until you set it to True.'
                    + bcolors.ENDC
                )

        self.par_backend = None
        if "par_backend" in self.config:
            self.par_backend: list[str] | str | None = self.config["par_backend"]

        self.collective = False
        if "collective" in self.config:
            self.collective: bool | str = self.config["collective"]

        self.ranks = [1]
        if "ranks" in self.config:
            ranks: list[int] | int = self.config["ranks"]

            if isinstance(ranks, list):
                self.ranks = ranks
            elif isinstance(ranks, int):
                self.ranks = [ranks]

        self.nodes = [1]
        if "nodes" in self.config:
            nodes: list[int] | int = self.config["nodes"]

            if isinstance(nodes, list):
                self.nodes: list[int] = nodes
            elif isinstance(nodes, int):
                self.nodes = [nodes]

        self.max_processes = None
        if "max_processes" in self.config:
            self.max_processes: int | None = self.config["max_processes"]

        self.only_data = False
        if "only_data" in self.config:
            self.only_data: bool = self.config["only_data"]

        self.use_spack_env = True
        if "use_spack_env" in self.config:
            self.use_spack_env: bool = self.config["use_spack_env"]

        self.delete_envs = False
        if "delete_envs" in self.config:
            self.delete_envs: bool = self.config["delete_envs"]

        self.profiler = False
        if "profiler" in self.config:
            self.profiler: bool = self.config["profiler"]

        self.no_caching = False
        if "no_caching" in self.config:
            self.no_caching: bool = self.config["no_caching"]
