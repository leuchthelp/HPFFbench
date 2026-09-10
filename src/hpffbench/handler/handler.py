import hashlib
import itertools
import json
import logging
import os
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import numpy as np
import xarray as xr
from pathos.pools import ProcessPool
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.traceback import install as install_rich_traceback

from hpffbench.benchmarkmanager import BenchmarkManager
from hpffbench.configloader import (
    BenchmarkConfig,
    BenchmarkConfigLoader,
    GlobalConfigLoader,
    ProfilerConfigLoader,
)
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
        profiler = self.config.profiler

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

        self.__tasks: list[list[BenchmarkManager]] = []
        combinations = itertools.product(parallel, profiler)
        for combination in combinations:
            self.__tasks.extend(
                self.__create_benchmark(
                    parallel=combination[0],
                    profiler=combination[1],
                    determined_cap=self.__capabilities,
                )
            )

        logger.debug(self.__tasks)
        if not self.__tasks:
            raise RuntimeError("no matching benchmark configs found")

        if not self.__only_data:
            self.start()
        else:
            logger.warning(
                f'Just collecting results of matching benchmarks if they exist since "only_data" is set to {self.__only_data}.'
            )

        self.__build_datatree()

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
                            "task": current.task,
                            "format": current.format,
                            "language": current.language,
                            "parallel": entry,
                            "par_backend": None,
                        }
                        determined[str(benchmark_config)] = current
                    else:
                        for backend in current.par_backend:
                            benchmark_config: BenchmarkConfig = {
                                "task": current.task,
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
        tasks: list[tuple[str, str]] = []
        for task in self.config.tasks:
            tasks.append(("task", task))

        formats: list[tuple[str, str]] = []
        for format in self.config.formats:
            formats.append(("format", format))

        languages: list[tuple[str, str]] = []
        for language in self.config.languages:
            languages.append(("language", language))

        par_backends: list[tuple[str, str | None]] = [("par_backend", None)]
        if parallel:
            par_backends.clear()
            if not isinstance(self.config.par_backend, list):
                par_backends.append(("par_backend", self.config.par_backend))
            else:
                for par_backend in self.config.par_backend:
                    par_backends.append(("par_backend", par_backend))

        combinations = itertools.product(
            *[
                tasks,
                formats,
                languages,
                [("parallel", parallel)],
                par_backends,
            ]
        )

        tmp: list[BenchmarkConfig] = []
        for combination in combinations:
            tmp.append(cast(BenchmarkConfig, dict(combination)))

        return tmp

    def __create_benchmark(
        self,
        parallel: bool,
        profiler: bool,
        determined_cap: dict[str, BenchmarkConfigLoader],
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
            logger.debug(f"requested: {requested!s}")
            logger.debug(f"available: {determined_cap.keys()}")
            if str(requested) in determined_cap:
                logger.info("Success")

                tasks.append(
                    self.__create_benchmark_manager(
                        parallel=parallel,
                        profiler=profiler,
                        requested=requested,
                        bm_config=determined_cap[str(requested)],
                    )
                )

        return tasks

    def __create_benchmark_manager(
        self,
        parallel: bool,
        profiler: bool,
        requested: BenchmarkConfig,
        bm_config: BenchmarkConfigLoader,
    ) -> list[BenchmarkManager]:
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
        for run_config in self.config.runs.values():
            nodes = self.config.nodes
            slurm_options = [""]
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
            if profiler:
                profilers.clear()
                for req_profiler in self.config.profilers:
                    where_paths = Path(self.config.paths["path_to_profilers"]["path"])
                    config_paths = itertools.chain(
                        Path(where_paths).glob("*.yaml"),
                        Path(where_paths).glob("*.yml"),
                    )
                    for profiler_path in config_paths:
                        profiler_loaded = ProfilerConfigLoader(profiler_path)

                        if req_profiler == profiler_loaded.package:
                            profilers.append(profiler_loaded)

            combinations = itertools.product(
                nodes,
                config_ranks,
                config_collective,
                spack_manager,
                config_no_caching,
                profilers,
                slurm_options,
            )

            for combination in combinations:
                node = combination[0]
                ranks = combination[1]
                collective = combination[2]
                manager = combination[3]
                no_caching = combination[4]
                profiler_config = combination[5]
                slurm_option = combination[6]

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
                    slurm_options=slurm_option,
                    requested=requested,
                    nodes=node,
                    parallel=parallel,
                    collective=collective,
                    ranks=ranks,
                    spack_manager=manager,
                    no_caching=no_caching,
                    profiler=profiler,
                    profiler_config=profiler_config,
                )

                self.__benchmarks.append((bm.id, bm))
                benchmarks.append(bm)

        if not benchmarks:
            raise ValueError("Not benchmarks have been created, something is wrong.")

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

    def __calc_anomaly_prob(
        self, measures: list[float]
    ) -> tuple[list[float], list[bool]]:
        clusters = []
        eps = 0.12
        points_sorted = sorted(measures)
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

        anomaly_prob: list[float] = []
        anomaly_class: list[bool] = []

        # Very naive approach, need something better
        for value in measures:
            if value not in clusters[0]:
                idx = 0
                for i, elem in enumerate(clusters[1:]):
                    if value in elem:
                        idx = i

                prob = idx / len(clusters)

                anomaly_prob.append(prob)
                anomaly_class.append(True)
            else:
                anomaly_prob.append(0.0)
                anomaly_class.append(False)

        return anomaly_prob, anomaly_class

    def __build_overview_array(
        self, res_path: Path, benchmark: BenchmarkManager
    ) -> xr.DataArray:
        with open(res_path, "r") as file:
            initial: list[str] = json.load(file)

        used_nodes: list[str] = []
        ranks: list[int] = []
        measures: list[float] = []
        for entry in initial:
            split = entry.split("-")
            rank = int(split[0])
            node = split[1]
            value = float(split[2])

            ranks.append(rank)
            used_nodes.append(node)
            measures.append(value)

        count_per_rank = Counter(ranks)

        ranks = list(count_per_rank.keys())
        _, iter_amount = count_per_rank.popitem()
        iterations: list[int] = list(range(iter_amount))

        time_mean = np.mean(measures)
        time_std = np.std(measures)
        time_rsd = time_std / time_mean
        time_error = time_std / float(np.sqrt(len(measures)))

        throughputs = [benchmark.total_filesize / time for time in measures]
        throughput_mean = np.mean(throughputs)
        throughput_std = np.std(throughputs)
        throughput_rsd = throughput_std / throughput_mean
        throughput_err = throughput_std / float(np.sqrt(len(throughputs)))

        anomaly_prob, anomaly_class = self.__calc_anomaly_prob(measures=measures)
        coords: dict[str, Any] = {
            "iterations": iterations,
            "on_rank": ranks,
            "on_node": (
                ("iterations", "on_rank"),
                np.array(used_nodes).reshape(iter_amount, benchmark.ranks),
            ),
            "mean_time": time_mean,
            "time_std": time_std,
            "time_relative_std": time_rsd,
            "time_error_bar": time_error,
            "throughput_per_measure": (
                ("iterations", "on_rank"),
                np.array(throughputs).reshape(iter_amount, benchmark.ranks),
            ),
            "mean_throughput": throughput_mean,
            "throughput_std": throughput_std,
            "throughput_relative_std": throughput_rsd,
            "throughput_error_bar": throughput_err,
            "anomaly_hint_prob": (
                ("iterations", "on_rank"),
                np.array(anomaly_prob).reshape(iter_amount, benchmark.ranks),
            ),
            "anomaly_hint_classification": (
                ("iterations", "on_rank"),
                np.array(anomaly_class).reshape(iter_amount, benchmark.ranks),
            ),
        }

        return xr.DataArray(
            data=np.array(measures).reshape(iter_amount, benchmark.ranks),
            coords=coords,
            dims=["iterations", "on_rank"],
            attrs={
                "description": "Time taken per benchmark run (lower is better)",
                "units": "ms (microseconds)",
            },
        )

    def __build_used_package_array(
        self,
        spack_manager: SpackManager,
        benchmark: BenchmarkManager,
    ) -> xr.DataArray:
        package_versions: list[str] = []
        package_names: list[str] = []
        package_flags: list[str] = []
        install_methods: list[str] = []

        required_packages = benchmark.bm_config.required_packages
        for name, config in spack_manager.spack_packages.items():
            if any(bool(name.lower() in package) for package in required_packages):
                package_names.append(name)
                package_versions.append(config["version"])
                package_flags.append(config["variant"])
                install_methods.append("spack")

        for name, config in spack_manager.pip_packages.items():
            if any(bool(name.lower() in package) for package in required_packages):
                package_names.append(name)
                package_versions.append(config["version"])
                package_flags.append(config["variant"])
                install_methods.append("pip")

        coords: dict[str, Any] = {
            "package_name": package_names,
            "install_method": ("package_name", install_methods),
            "package_flag": ("package_name", package_flags),
        }

        return xr.DataArray(
            data=package_versions,
            coords=coords,
            dims=["package_name"],
            attrs={
                "description": "Versions of all packages specifically required by this benchmark",
            },
        )

    def __build_avail_packages_array(self, spack_manager: SpackManager) -> xr.DataArray:
        package_names = list(spack_manager.spack_packages.keys())
        package_names.extend(list(spack_manager.pip_packages.keys()))

        package_versions: list[str] = []
        package_flags: list[str] = []
        install_methods: list[str] = []
        for config in spack_manager.spack_packages.values():
            package_versions.append(config["version"])
            package_flags.append(config["variant"])
            install_methods.append("spack")

        for config in spack_manager.pip_packages.values():
            package_versions.append(config["version"])
            package_flags.append(config["variant"])
            install_methods.append("pip")

        coords: dict[str, Any] = {
            "all_package_versions": package_versions,
            "all_package_flag": ("all_package_versions", package_flags),
            "all_install_method": ("all_package_versions", install_methods),
        }

        return xr.DataArray(
            data=package_names,
            coords=coords,
            dims=["all_package_versions"],
            attrs={
                "description": "All available packages within the tested environment.",
            },
        )

    def __build_overview_dataset(
        self, res_path: Path, benchmark: BenchmarkManager, date_run: str
    ) -> xr.DataTree:
        overview_array = self.__build_overview_array(
            res_path=res_path, benchmark=benchmark
        )

        coords: dict[str, Any] = {
            "format": benchmark.format,
            "task_type": benchmark.task,
            "language": benchmark.language,
            "engine": benchmark.engine,
            "no_caching": benchmark.no_caching,
            "num_nodes": benchmark.nodes,
            "num_ranks": benchmark.ranks,
            "parallel": benchmark.parallel,
            "parallel_backend": benchmark.par_backend,
            "access_kind": "collective"
            if benchmark.collective is not None and benchmark.collective is True
            else "independent",
            "total_filesize": benchmark.total_filesize,
            # "var_to_bm": benchmark.var_to_bm,
            "filesize_per_var": benchmark.filesize_var[0][1],
            "unit_var": benchmark.unit_var,
            "filesize_per_chunk": benchmark.chunksize_var[0][1],
            "unit_chunk": benchmark.unit_chunk,
        }

        data_vars: dict[str, xr.DataArray] = {
            "overview": overview_array,
        }

        return xr.DataTree.from_dict(
            {
                "/": xr.Dataset(coords=coords),
                date_run: xr.Dataset(data_vars=data_vars),
            }
        )

    def __build_used_package_dataset(
        self, spack_manager: SpackManager, benchmark: BenchmarkManager
    ) -> xr.Dataset:
        used_package_array = self.__build_used_package_array(
            spack_manager=spack_manager, benchmark=benchmark
        )

        data_vars: dict[str, xr.DataArray] = {
            "used_packages": used_package_array,
        }

        return xr.Dataset(data_vars=data_vars)

    def __build_avail_packages_dataset(self, spack_manager: SpackManager) -> xr.Dataset:
        avail_packages_array = self.__build_avail_packages_array(
            spack_manager=spack_manager
        )

        data_vars: dict[str, xr.DataArray] = {
            "all_avail_packages": avail_packages_array,
        }

        return xr.Dataset(data_vars=data_vars)

    def __build_sub_tree(
        self, res_path: Path, benchmark: BenchmarkManager, date_run: str
    ) -> xr.DataTree:

        spack_manager = benchmark.spack_manager

        final = {
            "date_run": self.__build_overview_dataset(
                res_path=res_path, benchmark=benchmark, date_run=date_run
            ),
            "used_packages": self.__build_used_package_dataset(
                spack_manager=spack_manager, benchmark=benchmark
            ),
            "all_avail_packages": self.__build_avail_packages_dataset(
                spack_manager=spack_manager
            ),
        }

        return xr.DataTree.from_dict(final)

    def __build_datasets(self) -> dict[str, xr.DataTree]:
        final: dict[str, xr.DataTree] = {}

        root = Path(self.config.paths["path_to_bm_results"]["path"])

        benchmarks = dict(self.__benchmarks)

        for path in root.rglob("*.json"):
            if path.is_file() and "results" not in path.name:
                tmp = path.name.replace(".json", "").split("-")
                path_name = tmp[0]
                path_date = tmp[1]

                if path_name in benchmarks:
                    benchmark = benchmarks[path_name]
                    date_run = str(
                        datetime.strptime(path_date, "%Y_%m_%d_%H_%M_%S").astimezone()
                    )

                    if path_name in final:
                        new = self.__build_sub_tree(path, benchmark, date_run)
                        old = final[path_name]
                        final[path_name] = xr.merge([old, new], compat="no_conflicts")

                    else:
                        final[path_name] = self.__build_sub_tree(
                            path, benchmark, date_run
                        )

        return final

    def __build_datatree(self):
        dt = xr.DataTree.from_dict(self.__build_datasets(), name="root", nested=True)

        res_path: str = self.config.paths["path_to_results"]["path"]
        res_file_path: Path = Path(f"{res_path}/results.zarr")

        # merge does not support mixed type arguments when one argument is a DataTree: [<xarray.Dataset> Size: 0B
        # Dimensions:  ()
        # Data variables:
        #    *empty*, <xarray.DataTree 'root'>

        # if res_file_path.exists():
        #     existing: xr.DataTree = xr.open_zarr(res_file_path)
        #     dt = xr.merge([existing, dt], join="exact")

        dt.to_zarr(res_file_path, mode="a")
