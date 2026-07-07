from typing import TypedDict, NotRequired, Any
from dataclasses import dataclass
from pathlib import Path
import itertools
import logging

import yaml

logger = logging.getLogger(__name__)


class ProcessedPath(TypedDict):
    path: str
    skip: bool


class RunConfig(TypedDict):
    shape: list[int]
    chunks: list[int]
    datatype: str


@dataclass
class Run:
    def __init__(self, run: dict[str, list]):

        self.variables: dict[str, RunConfig] = {}
        for var, setup in run.items():
            shape: list[int] = setup[0]

            chunks: list[int] = setup[1] if len(setup) > 1 else []
            if len(chunks) > len(shape):
                raise ValueError(
                    "Cannot provide more chunks dimensions than there are dims"
                )

            self.variables[var] = {
                "shape": shape,
                "chunks": chunks,
                "datatype": setup[2] if len(setup) > 2 else "f8",
            }


class SpackPackageConfig(TypedDict):
    versions: list[str]
    variants: str
    fresh: NotRequired[bool]


class SpackEnvConfig(TypedDict):
    target: list[dict[str, str]]
    language: list[str]
    packages: dict[str, SpackPackageConfig]
    compiler: str
    additional: str
    install: bool


class SpackEnv:
    def __init__(self, env: dict):
        packages: dict[str, SpackPackageConfig] = {}
        if "packages" in env:
            found: dict[str, dict] = env["packages"]

            for key, package in found.items():
                fresh = False
                if "fresh" in package:
                    fresh = package["fresh"]
                    if not isinstance(fresh, bool):
                        raise ValueError

                variants = ""
                if "variants" in package:
                    variants = package["variants"]
                    if not isinstance(variants, str):
                        raise ValueError

                packages[key] = {
                    "versions": package["versions"],
                    "variants": variants,
                    "fresh": fresh,
                }
        else:
            raise KeyError

        self.config: SpackEnvConfig = {
            "target": env["target"],
            "language": env["language"],
            "compiler": env["compiler"],
            "packages": packages,
            "additional": env["additional"] if "additional" in env else "",
            "install": env["install"] if "install" in env else False,
        }


class BenchmarkConfig(TypedDict):
    format: str
    language: str
    parallel: bool
    par_backend: str | None


@dataclass
class BenchmarkConfigLoader:
    format: str
    create: str
    source: str
    language: str
    extension: str
    compile_command: str | None

    compile: bool

    parallel: list[bool]
    create_commands: dict[str, str]
    run_commands: dict[str, str]

    par_backend: list[str] | None

    def __init__(self, path_to_config: Path):

        self.config: dict[str, Any] = {}
        with open(str(path_to_config), "r") as file:
            self.config: dict[str, Any] = yaml.safe_load(stream=file)

        parallel: bool | str = self.config["parallel"]
        if isinstance(parallel, str) and parallel.lower() == "configurable":
            self.parallel = [False, True]
        elif isinstance(parallel, bool):
            self.parallel = [parallel]

        self.language: str = self.config["language"]
        self.format: str = self.config["format"]
        self.extension: str = self.config["extension"]
        self.create_commands: dict[str, str] = self.config["create_command"]
        self.create: str = self.config["create"]
        self.run_commands: dict[str, str] = self.config["run_command"]
        self.source: str = self.config["source"]

        # Optionals

        if "par_backend" in self.config:
            par_backend: list[str] | str = self.config["par_backend"]

            if isinstance(par_backend, str):
                self.par_backend = [par_backend]
            elif isinstance(par_backend, list):
                self.par_backend = par_backend
        else:
            self.par_backend = None

        self.compile = False
        if "compile" in self.config:
            self.compile: bool = self.config["compile"]

        self.compile_command = None
        if self.compile:
            self.compile_command: str = self.config["compile_command"]


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

    par_backend: list[str] | None

    paths: dict[str, ProcessedPath]
    runs: dict[str, Run]
    spack_envs: dict[str, SpackEnv]

    max_processes: int | None
    parallel: bool | str
    collective: bool | str

    def __init__(self, path_to_config: str | dict):
        if isinstance(path_to_config, dict):
            self.config = path_to_config

        else:
            logger.info("Try loading config.yaml")
            try:
                if not any(sub in path_to_config for sub in [".yaml", ".yml"]):
                    for file in itertools.chain(
                        Path(path_to_config).glob("*.yaml"),
                        Path(path_to_config).glob("*.yml"),
                    ):
                        path_to_config = str(file)
                        break

                with open(f"{path_to_config}", "r") as file:
                    self.config = yaml.safe_load(stream=file)
                    logger.info("Success loading config.yaml")

            except FileNotFoundError or IsADirectoryError as e:
                FileNotFoundError(
                    f"config.yaml not found, please ensure a valid config exists! Additional details: {e}"
                )
            except OSError as e:
                OSError(
                    f"Path to config.yaml could not found, please check it is valid! Additional details: {e}"
                )
            except yaml.YAMLError as e:
                yaml.YAMLError(f"Error loading config.yaml! Additional details: {e}")

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

        if "runs" in self.config:
            runs: dict[str, dict[str, list]] = self.config["runs"]

            if not self.config["runs"]:
                raise ValueError("No runs specified, please add some.")

            processed_runs: dict[str, Run] = {}
            for key, run in runs.items():
                processed_runs[key] = Run(run)
            self.runs = processed_runs
        else:
            raise KeyError("No runs specified, please add some.")

        self.use_spack_env = True
        if "use_spack_env" in self.config:
            self.use_spack_env: bool = self.config["use_spack_env"]

        if self.use_spack_env:
            if "spack_env" in self.config:
                envs: dict[str, dict[str, dict]] = self.config["spack_env"]

                processed_envs: dict[str, SpackEnv] = {}
                for key, env in envs.items():
                    processed_envs[key] = SpackEnv(env)
                self.spack_envs = processed_envs
            else:
                raise KeyError
        else:
            self.spack_envs: dict[str, SpackEnv] = {}

        # Optionals
        self.parallel = False
        if "parallel" in self.config:
            parallel: bool | str = self.config["parallel"]

            if parallel != "Both" and type(parallel) is not bool:
                raise ValueError(
                    '"parallel" can only either be "True", "False" or "Both"'
                )

            self.parallel = parallel
        else:
            logger.info(
                '"parallel" is unset! Be aware parallel will be automatically set to False as long as it remains unset. You will be unable to run parallelized benchmarks until you set it to True.'
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

        self.delete_envs = False
        if "delete_envs" in self.config:
            self.delete_envs: bool = self.config["delete_envs"]

        self.profiler = False
        if "profiler" in self.config:
            self.profiler: bool = self.config["profiler"]

        self.no_caching = False
        if "no_caching" in self.config:
            self.no_caching: bool = self.config["no_caching"]
