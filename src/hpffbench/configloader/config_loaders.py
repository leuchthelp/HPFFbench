import itertools
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, NotRequired, ReadOnly, TypedDict

import yaml

logger = logging.getLogger(__name__)


class ProcessedPath(TypedDict):
    path: ReadOnly[str]
    skip: ReadOnly[bool]


class RunConfig(TypedDict):
    shape: ReadOnly[list[int]]
    chunks: ReadOnly[list[int]]
    datatype: ReadOnly[str]


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
    versions: ReadOnly[list[str]]
    variants: ReadOnly[str]
    fresh: ReadOnly[NotRequired[bool]]


class SpackEnvConfig(TypedDict):
    target: ReadOnly[list[dict[str, str]]]
    language: ReadOnly[list[str]]
    packages: ReadOnly[dict[str, SpackPackageConfig]]
    compiler: ReadOnly[str]
    additional: ReadOnly[str]
    install: ReadOnly[bool]


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
            "additional": env.get("additional", ""),
            "install": env.get("install", False),
        }


class LazyCommand(TypedDict):
    command: ReadOnly[str]
    language: ReadOnly[str]
    compile: ReadOnly[bool]


class RunCommands(TypedDict):
    serial: ReadOnly[str]

    # shitfix until TypedDict PEP728 is fully supported
    MPI: ReadOnly[NotRequired[str]]
    lazy: ReadOnly[NotRequired[LazyCommand]]


class InstrumenterMethods(TypedDict):
    start: ReadOnly[str]
    stop: ReadOnly[NotRequired[str]]


@dataclass
class ProfilerConfigLoader:
    language: str
    package: str
    imports: str
    compile: bool

    install_method: str | None
    compile_command: str | None

    formats: list[str]
    run_commands: RunCommands
    instrumenter: InstrumenterMethods | None
    env_vars: dict[str, str]
    export_method: dict[str, str]

    def __init__(self, path_to_config: Path):

        self.config: dict[str, Any] = {}
        with open(str(path_to_config), "r") as file:
            self.config: dict[str, Any] = yaml.safe_load(stream=file)

        self.language: str = self.config["language"]
        self.package: str = self.config["package"]
        self.formats: list[str] = self.config["formats"]
        self.run_commands: RunCommands = self.config["run_commands"]

        self.export_method: dict[str, str] = {}
        if "export_method" in self.config:
            self.export_method: dict[str, str] = self.config["export_method"]
        else:
            for command in self.run_commands.values():
                if "<profile_path>" not in str(command):
                    raise ValueError(
                        "<profile_path> not found in profiler command, while no alternative way to change the export location of profiler result were given."
                    )

        # Optionals
        self.imports = ""
        if "imports" in self.config:
            self.imports: str = self.config["imports"]

        self.compile = False
        if "compile" in self.config:
            self.compile: bool = self.config["compile"]

        self.compile_command: str | None = None
        if self.compile:
            self.compile_command: str = self.config["compile_command"]

        self.install_method: str | None = None
        if "install_method" in self.config:
            self.install_method: str = self.config["install_method"]

        self.instrumenter: InstrumenterMethods | None = None
        if "instrumenter" in self.config:
            self.instrumenter: InstrumenterMethods = self.config["instrumenter"]

        self.env_vars: dict[str, str] = {}
        if "env_variables" in self.config:
            self.env_vars: dict[str, str] = self.config["env_variables"]


class BenchmarkConfig(TypedDict):
    task: ReadOnly[str]
    format: ReadOnly[str]
    language: ReadOnly[str]
    parallel: ReadOnly[bool]
    par_backend: ReadOnly[str | None]


@dataclass
class BenchmarkConfigLoader:
    task: str
    format: str
    create: str | None
    source: str
    language: str
    extension: str
    compile_command: str | None

    compile: bool

    parallel: list[bool]
    create_commands: RunCommands
    run_commands: RunCommands

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

        self.task: str = self.config["task"]
        self.language: str = self.config["language"]
        self.format: str = self.config["format"]
        self.extension: str = self.config["extension"]
        self.create_commands: RunCommands = self.config["create_command"]
        self.run_commands: RunCommands = self.config["run_command"]
        self.source: str = self.config["source"]

        # Optionals
        self.create = None
        if "create" in self.config:
            self.create: str = self.config["create"]

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


class GlobalConfigLoader:
    iterations: int
    paths_create: bool
    only_data: bool
    use_spack_env: bool
    delete_envs: bool

    ranks: list[int]
    nodes: list[int]
    tasks: list[str]
    formats: list[str]
    languages: list[str]
    slurm_options: list[str]
    variable_to_benchmark: list[str]
    profilers: list[str]
    profiler_mode: Literal["manual", "auto"]

    par_backend: list[str] | None

    paths: dict[str, ProcessedPath]
    runs: dict[str, Run]
    spack_envs: dict[str, SpackEnv]

    max_processes: int | None
    profiler: list[bool]
    parallel: list[bool]
    collective: list[bool | None]
    no_caching: list[bool]

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

            except (FileNotFoundError, IsADirectoryError) as e:
                raise FileNotFoundError(
                    f"config.yaml not found, please ensure a valid config exists! Additional details: {e}"
                )
            except OSError as e:
                raise OSError(
                    f"Path to config.yaml could not found, please check it is valid! Additional details: {e}"
                )
            except yaml.YAMLError as e:
                yaml.YAMLError(f"Error loading config.yaml! Additional details: {e}")

        self.tasks: list[str] = self.config["tasks"]
        self.formats: list[str] = self.config["formats"]
        self.languages: list[str] = self.config["languages"]
        self.iterations: int = self.config["iterations"]
        self.nodes: list[int] = self.config["nodes"]
        self.variable_to_benchmark: list[str] = self.config["variable_to_benchmark"]
        self.slurm_options: list[str] = self.config["slurm_options"]

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
        self.paths_create = False
        if "paths_create" in self.config:
            self.paths_create: bool = self.config["paths_create"]

        self.parallel: list[bool] = [False]
        if "parallel" in self.config:
            config_parallel: bool | str = self.config["parallel"]

            if not isinstance(config_parallel, bool) and config_parallel != "Both":
                raise ValueError(
                    '"parallel" can only either be "True", "False" or "Both"'
                )
            elif not isinstance(config_parallel, bool) and config_parallel == "Both":
                self.parallel: list[bool] = [False, True]
            else:
                self.parallel: list[bool] = [config_parallel]
        else:
            logger.info(
                '"parallel" is unset! Be aware parallel will be set to False as long as it remains unset. You will be unable to run parallelized benchmarks until you set it to True.'
            )

        self.par_backend = None
        if "par_backend" in self.config:
            self.par_backend: list[str] | str | None = self.config["par_backend"]

        self.collective: list[bool | None] = [None]
        if "collective" in self.config:
            collective: bool | str = self.config["collective"]

            if isinstance(collective, str) and collective == "Both":
                self.collective = [False, True]
            elif isinstance(collective, bool):
                self.collective = [collective]

            if True not in self.parallel:
                logger.warning(
                    f"Parallel was set to {self.parallel} but collective was set: {collective}. Will be ignored as long as parallel is not True or for runs which are not parallelized."
                )

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

        self.no_caching = [True]
        if "no_caching" in self.config:
            no_caching: bool | str = self.config["no_caching"]

            if isinstance(no_caching, str) and no_caching == "Both":
                self.no_caching = [False, True]
            elif isinstance(no_caching, bool):
                self.no_caching = [no_caching]

        self.profiler: list[bool] = [False]
        if "profiler" in self.config:
            config_profiler: bool | str = self.config["profiler"]

            if not isinstance(config_profiler, bool) and config_profiler != "Both":
                raise ValueError(
                    '"profiler" can only either be "True", "False" or "Both"'
                )
            elif not isinstance(config_profiler, bool) and config_profiler == "Both":
                self.profiler: list[bool] = [False, True]
            else:
                self.profiler: list[bool] = [config_profiler]
        else:
            logger.info(
                '"profiler" is unset! Be aware profiler will be set to False as long as it remains unset. You will be unable to run profiled benchmarks until you set it to True.'
            )

        self.profilers: list[str] = []
        if "profilers" in self.config:
            self.profilers: list[str] = self.config["profilers"]

        self.profiler_mode: Literal["manual", "auto"] = "auto"
        if "profiler_mode" in self.config:
            self.profiler_mode: Literal["manual", "auto"] = self.config["profiler_mode"]
