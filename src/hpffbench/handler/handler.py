from typing import cast
from collections import Counter
from pathlib import Path
import subprocess
import itertools
import logging
import hashlib
import json
import os

from rich.traceback import install as install_rich_traceback
from rich.logging import RichHandler
from rich.console import Console
from rich.progress import (
    TimeRemainingColumn,
    MofNCompleteColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TextColumn,
    BarColumn,
    Progress,
)

from pathos.pools import ProcessPool
import pandas as pd
import numpy as np


from hpffbench.configloader import (
    BenchmarkConfig,
    GlobalConfigLoader,
    BenchmarkConfigLoader,
    ProfilerConfigLoader,
)
from hpffbench.benchmarkmanager import BenchmarkManager
from hpffbench.spackmanager import SpackManager


logger = logging.getLogger(__name__)

error_console = Console(stderr=True)
install_rich_traceback(console=error_console)


class Handler:
    """Defines handler to read configuration from yaml file and create matching benchmarks. Also configures the benchmark environments and gathers system information.

    Parameters
    ----------
    path_to_config: str
        Path to config.yaml which covers benchmark environments and benchmarks to run.


    Attributes
    ----------
    path_to_config: str
        Path to config.yaml which covers benchmark environments and benchmarks to run.

    """

    path_to_config: str

    def __init__(self, path_to_config: str | dict, log_lvl: int | str | None = None):

        logging.basicConfig(
            level=log_lvl if log_lvl is not None else logging.INFO,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler()],
        )

        self.__load_config(path_to_config)
        self.__benchmarks: list[tuple[str, BenchmarkManager]] = []
        self.__id = hashlib.sha256(str(path_to_config).encode()).hexdigest()
        self.__delete_envs = self.config.delete_envs

        logger.debug("Check if spack is available")

        spack_path = Path("spack")
        if not spack_path or "HPFF_SPACK_ROOT" not in os.environ:
            try:
                p = subprocess.run(
                    ["bash", "helpers/HPFFbench-setup.sh"],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                logger.info(p.stdout)
                if not spack_path.exists():
                    raise RuntimeError(
                        "Spack root could not be inferred, something must have gone wrong."
                    )

                os.environ["HPFF_SPACK_ROOT"] = str(spack_path.absolute())

            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Spack could not be installed for reasons: {e}")

        self.slurm_avail = False
        try:
            logger.debug("Check if slurm is available")
            p = subprocess.run("sinfo", check=True, capture_output=True, text=True)
            logger.debug(p.stdout)
            logger.error(p.stderr)
            self.slurm_avail = True
        except FileNotFoundError:
            pass

        self.__check_paths()
        self.__capabilities = self.__determine_capabilities()

        self.__only_data = self.config.only_data
        self.__use_spack_env = self.config.use_spack_env
        self.__max_processes = self.config.max_processes
        parallel = self.config.parallel

        self.spack_manager: list[SpackManager] = []
        for env_name, spack_env in self.config.spack_envs.items():
            self.spack_manager.append(
                SpackManager(
                    handler_id=self.__id,
                    env_name=env_name,
                    spack_env=spack_env,
                    use_spack_env=self.__use_spack_env,
                    only_data=self.__only_data,
                    paths=self.config.paths,
                )
            )

        if isinstance(parallel, str) and parallel == "Both":
            self.__tasks = self.__create_benchmark(
                parallel=False, determined_cap=self.__capabilities
            )
            self.__tasks.extend(
                self.__create_benchmark(
                    parallel=True, determined_cap=self.__capabilities
                )
            )
        elif isinstance(parallel, bool):
            self.__tasks = self.__create_benchmark(
                parallel=parallel, determined_cap=self.__capabilities
            )

        if not self.__tasks:
            raise RuntimeError("no matching benchmark configs found")

        if not self.__only_data:
            self.start()
        else:
            logger.warning(
                f'Just collecting results of matching benchmarks if they exist since "only_data" is set to {self.__only_data}.'
            )

        self.__prepare_dataframe()

    def __load_config(self, path_to_config: str | dict):
        """
        Tries to find and load a requested configuration file.

        Parameters
        ----------
        path_to_config: str | dict

        Raises
        ------
        FileNotFoundError
            If `config.yaml` cannot be found.
        OSError
            If Path to `config.yaml` cannot be found.
        YAMLError
            If there is an error with the `config.yaml`

        """
        self.config = GlobalConfigLoader(path_to_config)

    def __check_paths(self):
        """
        Checks if all user requested paths exist. Should also define a couple of defaults to fall back to, currently does not.
        """
        logger.info("Check configured paths")
        for key, path in self.config.paths.items():
            if not path["skip"]:
                if not Path(path["path"]).exists():
                    if self.config.paths_create:
                        logger.warning(
                            f'Creating {path} as "paths_create" was set to {self.config.paths_create}'
                        )
                        Path(path["path"]).mkdir(parents=True)
                    else:
                        raise ValueError(
                            f"Configured path: {path} for key: {key} does not exist. Please create it."
                        )
            else:
                logger.warning(f"{path} was skipped, proceed with caution")

        logger.info("All paths checked successfully")

        logger.info("Create benchmarks")

    def __determine_capabilities(self) -> dict[str, BenchmarkConfigLoader]:
        """
        Gather supplied benchmarks at `path_to_benchmarks` and figure out which types of benchmark exist & are potentially runnable within the current environment at runtime.

        Returns
        -------

        dict
            Contains all capabilities the benchmark-framework has at runtime.
        """
        """
        Gather supplied benchmarks at `path_to_benchmarks` and figure out which types of benchmark exist & are potentially runnable within the current environment at runtime.
        
        Returns
        -------
        
        dict
            Contains all capabilities the benchmark-framework has at runtime.
        """
        root = Path(self.config.paths["path_to_benchmarks"]["path"])

        determined: dict[str, BenchmarkConfigLoader] = {}

        for path in root.rglob("*"):
            if not path.is_dir():
                current = BenchmarkConfigLoader(path)

                for entry in current.parallel:
                    if not entry or not isinstance(current.par_backend, list):
                        benchmark_config: BenchmarkConfig = {
                            "format": current.format,
                            "language": current.language,
                            "parallel": entry,
                            "par_backend": None,
                        }
                        determined[str(benchmark_config)] = current
                    else:
                        for backend in current.par_backend:
                            benchmark_config: BenchmarkConfig = {
                                "format": current.format,
                                "language": current.language,
                                "parallel": entry,
                                "par_backend": backend,
                            }
                            determined[str(benchmark_config)] = current

        return determined

    def __requested_capabilities(self, parallel: bool) -> list[BenchmarkConfig]:
        """
        Figures out which benchmarks the user has requested. For this purpose it assembles
        a list of requested benchmarks with attributes in order of `(parallel, par_backends, languages, formats)`.

        Parameters
        ----------

        parallel: bool
            If the requested capabilities require parallelism to be enabled. Some metadata has to be handles for this to work properly which is skipped otherwise.

        Returns
        -------

        list
            Contains all requested benchmarks by the user.
        """
        languages: list[tuple[str, str]] = []
        for language in self.config.languages:
            languages.append(("language", language))

        formats: list[tuple[str, str]] = []
        for format in self.config.formats:
            formats.append(("format", format))

        par_backends: list[tuple[str, str | None]] = [("par_backend", None)]
        if parallel:
            par_backends.clear()
            if not isinstance(self.config.par_backend, list):
                par_backends.append(("par_backend", self.config.par_backend))
            else:
                for par_backend in self.config.par_backend:
                    par_backends.append(("par_backend", par_backend))

        combinations = itertools.product(*[
            formats,
            languages,
            [("parallel", parallel)],
            par_backends,
        ])

        tmp: list[BenchmarkConfig] = []
        for combination in combinations:
            tmp.append(cast(BenchmarkConfig, dict(combination)))

        return tmp

    def __create_benchmark(
        self, parallel: bool, determined_cap: dict[str, BenchmarkConfigLoader]
    ) -> list[list[BenchmarkManager]]:
        """
        Gather tasks to be performed and pass required metadata to configure a single benchmark to be run.
        Gather the user requested capabilities and compares them to the determined capabilities. If they match
        create a new BenchmarkManager object. This is the initial check to skip unnecessary comparisons.

        Parameters
        ----------
        parallel: bool
            If parallelism is going to be used.
        determined_cap: dict
            The previously determined capabilities of the benchmark-framework at runtime.

        Returns
        -------
        list
            List of tasks that will be run in bulk. These tasks are `BenchmarkManager` objects.
        """
        requested_cap = self.__requested_capabilities(parallel=parallel)

        tasks: list[list[BenchmarkManager]] = []
        for requested in requested_cap:
            logger.debug(f"requested: {str(requested)}")
            logger.debug(f"available: {determined_cap.keys()}")
            if str(requested) in determined_cap.keys():
                logger.info("Success")

                tasks.append(
                    self.__create_benchmark_manager(
                        parallel=parallel,
                        requested=requested,
                        bm_config=determined_cap[str(requested)],
                    )
                )

        return tasks

    def __create_benchmark_manager(
        self,
        parallel: bool,
        requested: BenchmarkConfig,
        bm_config: BenchmarkConfigLoader,
    ):
        """
        Gather up additional metadata to create a BenchmarkManager object.

        Within this step assembled all combinations of `(nodes, ranks, collective, spack_managers)` requested by the user and create
        necessary amount of Managers.

        Parameters
        ----------
        parallel: bool
            If parallelism is going to be used.
        requested: dict
            What was requested by the user as a dictionary.
        bm_config:
            The benchmark configuration defined within a benchmarks `.yaml` as a dictionary.

        Returns
        -------
        list
            List of BenchmarkManager objects.
        """
        benchmarks: list[BenchmarkManager] = []

        for _, run_config in self.config.runs.items():
            nodes = self.config.nodes
            slurm_options = ""
            config_ranks: list[int] = [1]
            config_collective: list[bool | None] = [None]
            config_no_caching: list[bool] = self.config.no_caching

            if parallel:
                config_ranks = self.config.ranks
                config_collective = self.config.collective

            # If within a Slurm environment; slurm options need to be supplied as they have to include account for allocation
            if self.slurm_avail or self.__only_data:
                slurm_options = self.config.slurm_options

            spack_manager: list[SpackManager] = []
            for manager in self.spack_manager:
                if (
                    requested["format"] in manager.target
                    and requested["language"] in manager.language
                ):
                    spack_manager.append(manager)

            profilers: list[ProfilerConfigLoader | None] = [None]
            if self.config.profiler:
                profilers.clear()
                for profiler in self.config.profilers:
                    where_paths = Path(self.config.paths["path_to_profilers"]["path"])
                    config_paths = itertools.chain(
                        Path(where_paths).glob("*.yaml"),
                        Path(where_paths).glob("*.yml"),
                    )
                    for profiler_path in config_paths:
                        profiler_loaded = ProfilerConfigLoader(profiler_path)

                        if profiler == profiler_loaded.package:
                            profilers.append(profiler_loaded)

            combinations = itertools.product(
                nodes,
                config_ranks,
                config_collective,
                spack_manager,
                config_no_caching,
                profilers,
            )

            for combination in combinations:
                node = combination[0]
                ranks = combination[1]
                collective = combination[2]
                manager = combination[3]
                no_caching = combination[4]
                profiler_config = combination[5]

                if not manager.initialized:
                    manager.initialize_env()
                else:
                    logger.info(f"Environment: {manager.env_name} already initialized")

                bm = BenchmarkManager(
                    handler_id=self.__id,
                    run_config=run_config,
                    bm_config=bm_config,
                    global_config=self.config,
                    slurm_avail=self.slurm_avail,
                    slurm_options=slurm_options,
                    requested=requested,
                    nodes=node,
                    parallel=parallel,
                    collective=collective,
                    ranks=ranks,
                    spack_manager=manager,
                    no_caching=no_caching,
                    profiler=self.config.profiler,
                    profiler_config=profiler_config,
                )

                self.__benchmarks.append((bm.id, bm))
                benchmarks.append(bm)

        return benchmarks

    def start(self):
        """
        Start running the benchmark by called each BenchmarkManagers `.run()` method on each item found within the list of tasks.
        This is done as a pool of Processes using the `pathos` module to `pickle` entire BenchmarkManager objects via `dill`. The ProcessPool
        performs benchmarks in non-blocking unordered batches of jobs. Specifying `max processes` in the global configuration file controls how
        many processes are being used.

        If `delete envs` is set to `True` will also delete every environment.

        Raises
        ------

        TypeError
            If any error happens within BenchmarkManager, that isn't caught otherwise. Currently refers to "no matching benchmark found" however catches more
            errors than intended. Needs to be changed.
        """
        self.__benchmarks.clear()
        bm_list = list(itertools.chain.from_iterable(self.__tasks))
        pool = ProcessPool(processes=self.__max_processes)

        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            TimeElapsedColumn(),
        )
        task = progress.add_task("[cyan]Benchmarks still to run", total=len(bm_list))

        with progress:
            for result in pool.uimap(self.__run_benchmark, bm_list):
                self.__benchmarks.append(result)
                progress.update(task, advance=1)

        if self.__delete_envs:
            for manager in self.spack_manager:
                logger.info(f"remove environment: {manager.env_name}")
                manager.delete()
            logger.info("finish removing environments")

    def __run_benchmark(self, benchmark: BenchmarkManager):
        return benchmark.run()

    def __prepare_dataframe(self):
        """
        Gathers up all generated results, data and metadata and assembles a pandas Dataframe object. Finally exports the results as JSON.
        Also performs some basic pre-analysis on the data to generate some additional, helpful metrics.
        """
        root = Path(self.config.paths["path_to_results"]["path"])
        df = pd.DataFrame()

        benchmarks = dict(self.__benchmarks)

        for path in root.rglob("*"):
            if not path.is_dir():
                path_name = ""
                path_date = ""
                if "nodes" not in path.name:
                    tmp = path.name.replace(".json", "").split("-")
                    path_name = tmp[0]

                    if len(tmp) > 1:
                        path_date = "-" + tmp[1]

                if path_name in benchmarks.keys():
                    logger.debug(f"full path {path}")
                    logger.debug(f"date of file @ {path_date}")
                    logger.info(f"currently on {path_name}")

                    benchmark = benchmarks[path_name]

                    with open(path, "r") as file:
                        current: list[float] = json.load(file)

                    location_nodes = Path(
                        f"{root.absolute()}/{path_name}{path_date}-nodes.json"
                    )
                    with open(location_nodes.absolute(), "r") as file:
                        used_nodes: list[str] = json.load(file)

                    mean = np.mean(current)
                    std = np.std(current)
                    rsd = std / mean

                    error = std / float(np.sqrt(len(current)))

                    for index, value in enumerate(current):
                        count = Counter()
                        string = used_nodes[index]
                        symbol = string[0]
                        string = string.replace(symbol, "")
                        str_nodes = string.split(",")
                        final_nodes: list[list[str]] = []

                        for node in str_nodes:
                            if "-" in node:
                                hold = node.split("-")

                                node = [
                                    symbol + str(additional)
                                    for additional in range(
                                        int(hold[0]), int(hold[1]) + 1
                                    )
                                ]
                                final_nodes.append(node)

                            elif not isinstance(node, list):
                                final_nodes.append([symbol + node])

                        count.update(list(itertools.chain.from_iterable(final_nodes)))

                        profiling = None
                        try:
                            profile_path = Path(
                                self.config.paths["path_profiling"]["path"]
                            )
                            location_profiling = Path(
                                f"{profile_path.absolute()}/{path_name}/{path_name}{path_date}-{index}.json"
                            )

                            with open(location_profiling.absolute(), "r") as file:
                                profiling = json.load(file)

                            logger.debug(
                                f"loads {location_profiling} for iteration {index}"
                            )
                        except KeyError:
                            pass

                        anomaly = False

                        clusters = []
                        eps = 0.12
                        points_sorted = sorted(current)
                        curr_point = points_sorted[0]
                        curr_cluster = [curr_point]

                        for point in points_sorted[1:]:
                            if point <= curr_point + curr_point * eps:
                                curr_cluster.append(point)
                            else:
                                clusters.append(curr_cluster)
                                curr_cluster = [point]
                            curr_point = point

                        clusters.append(curr_cluster)

                        if value not in clusters[0]:
                            anomaly = True

                        logger.debug(
                            f"clusters: {clusters}, value: {value}, anomaly: {anomaly}"
                        )

                        tmp = pd.DataFrame(
                            data={
                                "benchmark": benchmark.id,
                                "date run": path_date,
                                "run config": [benchmark.run_config],
                                "time taken": value,
                                "throughput": benchmark.total_filesize / mean,
                                "engine": benchmark.engine,
                                "var to bm": [benchmark.var_to_bm],
                                "total filesize": benchmark.total_filesize,
                                "unit": benchmark.unit,
                                "filesize per var": [benchmark.filesize_var],
                                "filesize per chunk": [benchmark.chunksize_var],
                                "no caching": benchmark.no_caching,
                                "parallel": benchmark.parallel,
                                "parallel backend": benchmark.par_backend,
                                "collective": benchmark.collective,
                                "ranks": benchmark.ranks,
                                "language": benchmark.language,
                                "format": str(benchmark.format),
                                "mean time": mean,
                                "standard deviation": std,
                                "relative std": rsd,
                                "error bar": error,
                                "anomaly": anomaly,
                                "nodes": benchmark.nodes,
                                "used nodes": used_nodes[index],
                                "node count": [count],
                                "total node count": [Counter()],
                                "total nc match": [Counter()],
                                "profiling": [profiling],
                            }
                        )

                        df: pd.DataFrame = pd.concat([df, tmp], ignore_index=True)

        res_path: str = self.config.paths["path_to_results"]["path"]

        # there is probably a better method for doing this, will look into it later

        total_node_counter: Counter[str] = Counter()
        for count in df["node count"]:
            total_node_counter.update(count)

        for index, _ in df.iterrows():
            df.at[index, "total node count"] = total_node_counter

            for nodes, count in total_node_counter.items():
                if nodes in df.at[index, "node count"]:
                    df.at[index, "total nc match"][nodes] = count

        logger.debug(df)
        df.sort_values(
            by=["total filesize", "ranks", "engine", "format"],
            ascending=[True, True, True, False],
            inplace=True,
            ignore_index=True,
        )
        df.to_json(Path(f"{res_path}/results.json"))
