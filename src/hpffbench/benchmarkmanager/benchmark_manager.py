import hashlib
import logging
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import yaml

from hpffbench.configloader import (
    BenchmarkConfig,
    BenchmarkConfigLoader,
    GlobalConfigLoader,
    ProfilerConfigLoader,
    Run,
    RunCommands,
)
from hpffbench.configloader.config_loaders import RunConfig
from hpffbench.dev_utils import calc_size_unit
from hpffbench.spackmanager import SpackManager

logger = logging.getLogger(__name__)


class CompileInfo(TypedDict):
    compiled_file_location: str
    ld_library_path: str


@dataclass
class BenchmarkManager:
    """Defines handler to read configuration from yaml file and create matching benchmarks. Also configures the benchmark environments and gathers system information.

    Parameters
    ----------
    handler_id: str
        Unique handler ID to identify the handler assigned to this specific benchmark.

    run_config: dict
        The run configuration that was requested, contains the basic structure of a file that will be created.

    bm_config: dict
        The configuration of the benchmark file with all it's adjacent information like source code, commands and such.

    global_config: dict
        Contains global metadata like the variable to benchmark or number of iterations to perform.

    nodes: int
        Number of nodes used with the context of a slurm environment, otherwise always 1.

    slurm_avail: bool
        Flag to signal if the benchmark runs within a slurm equipped environment.

    slurm_options:
        Slurm options supplied by the user. Are simply being passed to the eventual `sbatch` script.

    parallel: bool
        If parallelism is requested.

    collective: None | bool
        If collective MPI I/O is requested, default is "False" for independent I/O. Will be none for serial benchmarks.

    ranks: int
        Represents how many cores are used to execute the benchmark following the MPI terminology. Will always be 1 for serial benchmarks.

    requested: dict
        Contains metadata on the type of benchmark the user has asked for like language, format or which parallel backend to use.

    spack_manager: SpackManager
        The SpackManager object that manages the environment to use while running the benchmark.

    paths: dict
        Dictionary of paths. Specifically to identify where to save environment data to.


    Attributes
    ----------
    handler_id: str
        Unique handler ID to identify the handler assigned to this specific benchmark.

    id: str
        Unique ID to identify this specific benchmark with.

    run_config: dict
        The run configuration that was requested, contains the basic structure of a file that will be created.

    bm_config: dict
        The configuration of the benchmark file with all it's adjacent information like source code, commands and such.

    nodes: int
        Number of nodes used with the context of a slurm environment, otherwise always 1.

    parallel: bool
        If parallelism is requested.

    par_backend: None | str
        What kind of backend is being used to facilitate parallelism. Will be "None" if parallelism is not requested.

    ranks: int
        Represents how many cores are used to execute the benchmark following the MPI terminology. Will always be 1 for serial benchmarks.

    collective: None | bool
        If collective MPI I/O is requested, default is "False" for independent I/O. Will be none for serial benchmarks.

    language: str

    format: str
        Simplified representation of the kind of benchmark that was requested.

    engine: str
        Represent the file format following the xarray terminology.

    extension: str
        File extension used for the created file.

    datatype: list
        Datatypes of each variable / dataset within the file.

    var_to_bm: str | list
        Which variable / dataset will be benchmarked from the file. Can either be a single value string or a list of strings.

    total_filesize: float
        The total filesize benchmarked calculated from all variables / datasets were requested for benchmarking.

    unit: str
        Unit for the total filesize, i.e. MB, GB, etc.

    filesize_var: list
        filesize per variable / dataset.

    chunksize_var: list
        filesize per variable / dataset chunks.

    iterations: int
        total iterations performed. In the context of a slurm environment equal to the number of unique node allocations performed.

    internal_i: int
        The benchmark itself can have iterations to be performed as well, this would result in caching of files on the nodes used in the context of a slurm environment.
    """

    handler_id: str
    id: str
    run_config: Run
    bm_config: BenchmarkConfigLoader
    task: str
    nodes: int
    parallel: bool
    par_backend: None | str
    ranks: int
    collective: None | bool
    no_caching: bool
    language: str
    format: str
    engine: str
    extension: str
    datatype: list[str]
    var_to_bm: str | list[str]
    total_filesize: float
    unit: str
    filesize_var: list[str]
    chunksize_var: list[str]
    iterations: int
    internal_i: int
    current_time: str

    def __init__(
        self,
        handler_id: str,
        run_config: Run,
        bm_config: BenchmarkConfigLoader,
        nodes: int,
        slurm_avail: bool,
        global_config: GlobalConfigLoader,
        slurm_options: str,
        parallel: bool,
        collective: None | bool,
        ranks: int,
        requested: BenchmarkConfig,
        spack_manager: SpackManager,
        no_caching: bool,
        profiler: bool,
        profiler_config: ProfilerConfigLoader | None,
    ):
        paths = global_config.paths

        # Object config
        self.current_time = datetime.now().astimezone().strftime("%Y_%m_%d_%H_%M_%S")
        self.handler_id = handler_id
        self.bm_config = bm_config
        self.global_config = global_config
        self.bash_location = "slurm-config"
        self.slurm_avail = slurm_avail
        self.slurm_options = slurm_options
        self.spack_manager = spack_manager

        # Source code
        self.create = bm_config.create
        self.compile = bm_config.compile
        self.compile_command = bm_config.compile_command
        self.src = bm_config.source

        # Benchmark config
        self.run_config = run_config
        self.task = requested["task"]
        self.nodes = nodes
        self.parallel = parallel
        self.collective = collective
        self.ranks = ranks
        self.format = requested["format"]
        self.language = requested["language"]
        self.engine = (
            f"{self.format}-{self.language}-parallel"
            if self.parallel
            else f"{self.format}-{self.language}"
        )
        self.extension = bm_config.extension

        if (
            isinstance(requested["par_backend"], str)
            or requested["par_backend"] is None
        ):
            self.par_backend: str | None = requested["par_backend"]

        self.language = requested["language"]
        self.format = requested["format"]

        datatype: list[str] = []
        for item in run_config.variables.values():
            datatype.append(item["datatype"])
        self.datatype: list[str] = datatype

        self.var_to_bm = self.global_config.variable_to_benchmark
        self.iterations = self.global_config.iterations
        self.internal_i = 1

        self.no_caching = no_caching
        self.local = False

        self.imports: str = ""
        self.profiler = profiler

        profiler_config_msg = ""
        if profiler_config is not None:
            self.profiler_config = profiler_config
            self.imports = "\n" + self.profiler_config.imports
            profiler_config_msg = self.profiler_config.package

        # Assemble ID
        id_str = (
            str(self.run_config.variables)
            + str(self.no_caching)
            + str(self.par_backend)
            + str(self.bm_config.par_backend)
            + str(self.parallel)
            + str(self.bm_config.parallel)
            + str(self.task)
            + str(self.bm_config.task)
            + str(self.format)
            + str(self.bm_config.format)
            + str(self.ranks)
            + str(self.var_to_bm)
            + str(self.collective)
            + str(self.nodes)
            + str(self.spack_manager.target)
            + str(self.spack_manager.additional)
            + str(self.spack_manager.compiler)
            + str(self.spack_manager.packages)
            + str(self.spack_manager.language)
            + str(self.spack_manager.env_name)
            # Reasoning: profilers also influence the results since they have runtime overhead, so they need to be taken into account
            + str(self.profiler)
            + str(asdict(self.profiler_config) if self.profiler else None)
            # Reasoning: If source code changes, do not consider the same benchmark even if it might be functionally the same, could still have an effect in performance
            + self.src
        )

        self.id = hashlib.sha256(id_str.encode()).hexdigest()

        logger.debug(self.id)

        if self.profiler:
            profiling_res_path = Path(paths["path_res_profiling"]["path"])
            new_profiler_path = Path(f"{profiling_res_path.absolute()}/{self.id}")
            self.profiling_res_path = new_profiler_path

        self.use_path = Path(paths["path_to_tmp"]["path"])
        self.root_path = Path(paths["path_to_root"]["path"])
        self.results_path = Path(paths["path_to_results"]["path"])
        self.dir_path = Path(f"{self.use_path}/{self.id}")

        # Benchmark info
        self.location = f"{self.id}.{self.extension}"

        filesize_per_var: list[tuple[str, tuple[float, str]]] = [
            (key, calc_size_unit(item["shape"]))
            for key, item in run_config.variables.items()
            if key in self.var_to_bm
        ]

        total_filesize = 0
        for filesize in filesize_per_var:
            total_filesize += filesize[1][0]

        self.total_filesize: float = total_filesize
        self.unit: str = filesize_per_var[0][1][1]
        self.filesize_var: list[tuple[str, tuple[float, str]]] = filesize_per_var
        self.chunksize_var: list[tuple[str, tuple[float, str]]] = [
            (key, calc_size_unit(item["chunks"]))
            for key, item in run_config.variables.items()
            if key in self.var_to_bm
        ]
        self.show_metadata = True

        # Environment config

        logger.info(
            f"Managing Benchmark with; file-structure: {run_config.variables}, "
            f"as task: {self.task}, "
            f"no caching: {self.no_caching}, "
            f"nodes: {self.nodes}, "
            f"datatype: {self.datatype}, "
            f"parallel: {self.parallel}, "
            f"collective: {self.collective}, "
            f"ranks: {self.ranks}, "
            f"par_backend: {self.par_backend}, "
            f"language: {self.language}, "
            f"format: {self.format}, "
            f"iterations: {self.iterations}, "
            f"in env: {self.spack_manager.env_name}, "
            f'with profiler: {self.profiler} using "{profiler_config_msg}". '
            f"It will be stored in {self.use_path.absolute()}"
        )

    def run(self) -> tuple[str, BenchmarkManager]:
        """
        Runs the benchmark.

        Running a benchmark happens in 4 stages:

        1. Creates a temporary storage location based on the user supplied `path_to_tmp`.
        2. Creates a `create_file` containing source code for a sample dataset to benchmark with.
        3. Executes source code containing benchmark logic.
        4. Once finished, removes all temporary data for cleanup.

        Returns
        -------

        str
            The Id of this specific benchmark for later identification.

        dict
            Returns the whole BenchmarkManager object as a dictionary to provide general metadata.

        Raises
        ------
        TODO
        """
        if self.dir_path.exists():
            shutil.rmtree(self.dir_path)

        self.dir_path.mkdir(parents=True)

        try:
            if self.show_metadata:
                with open(f"{self.dir_path}/metadata.yaml", "w") as f:
                    yaml.safe_dump(asdict(self), f)

            if self.profiler:
                self.profiling_res_path.mkdir(parents=True, exist_ok=True)

            if self.create is not None:
                self.__create_file(self.create)
            else:
                logger.warning(
                    'Not creating a source file since "create" is not supplied. Please make sure your executing code references a valid dataset.'
                )

            self.__execute_file()

        finally:
            shutil.rmtree(path=self.dir_path)
            pass

        return self.id, self

    def __create_file(self, create: str):
        """
        Will create a `create_file`. This type of file contains the source code needed `create` a requested file for a given format and language.
        This file with either be a `bash` or `sbatch` script depending on the environment the benchmark-framework is being run in.

        This function also assembles the final `create_command` that is needed to finally execute the given file. Depending on if a compiled language is being requested
        it also calls `__compile_file()`.

        Finally it executes the `create_file` with the `create_command`.
        """
        # Get create command
        create_commands: RunCommands = self.bm_config.create_commands
        language = self.language
        compile = self.compile

        command_type = "serial"
        if self.par_backend in create_commands:
            command_type = self.par_backend

        # I'm to lazy to reimplement creating the given file in c again, so will just reuse easier python code as files should be identical
        if "lazy" in create_commands:
            create_command = create_commands["lazy"]["command"]
            language = create_commands["lazy"]["language"]
            compile = create_commands["lazy"]["compile"]
        else:
            create_command = str(create_commands[command_type])  # ty:ignore[invalid-key]

        # Create the file that contains code to create the given dataset
        create = create.replace("#MAIN", self.__replace_main(language))

        path_to_create_file = Path(f"{self.dir_path}/create.{language}")
        with open(path_to_create_file, "w") as file:
            file.write(create)

        create_file = f"create.{language}"
        compiled_file_info: CompileInfo = {
            "compiled_file_location": "",
            "ld_library_path": "",
        }
        if compile:
            compiled_file_info = self.__compile_file(path=path_to_create_file)
            create_file = f"./{compiled_file_info['compiled_file_location']}"

        if self.par_backend is not None:
            create_command = create_command + " -p"
            create_command = create_command.replace(" -n ", f" -n {self.ranks} ", 1)

            if self.collective:
                create_command = create_command + f"-I {self.collective}"

        create_command = create_command.replace("{runnable}", f"{create_file} ", 1)
        create_command = create_command.replace(" -p", f" -p {self.parallel} ", 1)

        if "-c" not in create_command:
            create_command = create_command + " -c 1"

        if "-l" not in create_command:
            create_command = create_command + " -l"

        create_command = create_command.replace(" -l", f" -l {self.location}")

        # Transform run config into 4 lists; variables (list(string)), shape (list(list(int))), chunks (list(list(int))) & datatypes (list(string))
        flag_variable = "-V"
        if flag_variable not in create_command:
            create_command = create_command + f" {flag_variable}"

        variables: str = ",".join(list(self.run_config.variables.keys()))
        create_command = create_command.replace(
            f"{flag_variable}", f"{flag_variable} {variables}"
        )

        values: list[RunConfig] = list(self.run_config.variables.values())
        shapes: list[list[int]] = []
        chunks: list[list[int]] = []
        datatypes = self.datatype
        for value in values:
            shapes.append(value["shape"])
            chunks.append(value["chunks"])

        create_command = self.__append_flag(
            flag="-S", command=create_command, data=shapes
        )
        create_command = self.__append_flag(
            flag="-C", command=create_command, data=chunks
        )
        create_command = self.__append_flag(
            flag="-D", command=create_command, data=datatypes
        )

        shell_type = "bash"
        if self.slurm_avail and not self.local:
            shell_type = "sbatch"

        create_command = [
            shell_type,
            self.__assemble_bash(
                self.bash_location, compile_file_info=compiled_file_info
            ),
            create_command,
        ]

        logger.debug(f"create command used: {create_command}")
        p = subprocess.run(
            create_command,
            capture_output=True,
            text=True,
            check=True,
            cwd=self.dir_path,
        )

        if logger.isEnabledFor(logging.DEBUG):
            logger.error(p.stderr)
        logger.debug(p.stdout)

    def __append_flag(self, flag: str, command: str, data: list) -> str:
        """
        Appends flags internally used by all argument parser written specifically for this benchmark and injected into user source code.

        Parameters
        ----------

        flag: str
            The flag to append.

        command: str
            The command to append the flag to.

        data: list
            The data appended with the flag. This is a list containing an encoding of for example the shape of a dataset or chunks.

        Returns
        -------

        str
            The final assembled command to be executed.
        """
        if flag not in command:
            command = command + f" {flag}"

        data_str = ",".join(str(x) for x in data)
        command = command.replace(f"{flag}", f"{flag} {data_str}")

        return command

    def __compile_file(self, path: Path) -> CompileInfo:
        """
        Compiles a file at a given path. Resolves required metadata from self.

        Parameters
        ----------

        path: Path
            Path to file to be compiled by the BenchmarkManager.

        Returns
        -------

        str
            Location of the compiled file.

        str
            String containing `export LD_LIBRARY_PATH=` to be injected later.
        """
        if isinstance(self.compile_command, str):
            compile_command = self.compile_command.replace(
                "{runnable}", f"{path.absolute()}"
            )
        else:
            raise TypeError(
                "Compile was True, but somehow we got here without a compile_command being supplied ..."
            )

        pattern = r"\<(.*?)\>"
        requested_packages = re.findall(string=compile_command, pattern=pattern)

        ld_library_path = "export LD_LIBRARY_PATH="
        for package in requested_packages:
            package_location = self.spack_manager.package_locations[package][1]
            compile_command = compile_command.replace(
                f"<{package}>",
                f"-I{package_location}/include -L{package_location}/lib -L{package_location}/lib64",
                1,
            )
            ld_library_path = (
                ld_library_path + f"{package_location}/lib:{package_location}/lib64:"
            )

        compiled_file = f"{path.name}.out"
        compile_command = (
            compile_command
            + " -Wl,--unresolved-symbols=ignore-in-object-files"
            + f" -o {compiled_file}"
        )

        logger.debug(f"compile command used: {compile_command}")
        with open(f"{self.dir_path.absolute()}/compile.sh", "w") as file:
            file.write("#!/bin/bash\n")
            try:
                subprocess.run(
                    ["git", "--version"], check=True, capture_output=True, text=True
                )
            except subprocess.CalledProcessError:
                file.write("module load git\n")

            file.write(f". {self.root_path}/spack/share/spack/setup-env.sh\n")
            file.write(self.spack_manager.load_env())
            file.write(compile_command)

        p = subprocess.run(
            ["bash", "compile.sh"], check=True, capture_output=True, cwd=self.dir_path
        )

        if logger.isEnabledFor(logging.DEBUG):
            logger.error(p.stderr)
        logger.debug(p.stdout)

        return {
            "compiled_file_location": compiled_file,
            "ld_library_path": ld_library_path,
        }

    def __execute_file(self):
        """
        Similar to `__create_file()`. Creates a `execute` file matching the programming language requested and assembles a `run_command` to execute the file with.
        If a compiled language is requested, also compiles the necessary file and finally executes it.
        """
        # Get run command to execute the code with
        run_commands: RunCommands = self.bm_config.run_commands
        if self.profiler:
            run_commands = self.profiler_config.run_commands

        command_type = "serial"
        if self.par_backend in run_commands:
            command_type = self.par_backend

        run_command = str(run_commands[command_type])  # ty:ignore[invalid-key]

        # Create the executable to run the benchmark on a given file with
        execute = self.src.replace("#MAIN", self.__replace_main(self.language), 1)
        if self.profiler and self.profiler_config.instrumenter is not None:
            if self.global_config.profiler_mode == "manual":
                execute = (
                    f"{self.imports if self.language == 'py' else ''} \n" + execute
                )

                inst_start = self.profiler_config.instrumenter["start"]
                inst_start = inst_start.replace(
                    "<format>",
                    f'"{self.format}-{self.par_backend}-{self.filesize_var}-{self.chunksize_var}"',
                    count=1,
                )

                execute = execute.replace(
                    "#INSTRUMENTER_START",
                    inst_start,
                )

                if "stop" in self.profiler_config.instrumenter:
                    inst_stop = self.profiler_config.instrumenter["stop"]
                    inst_stop = inst_stop.replace(
                        "<format>",
                        f'"{self.format}-{self.par_backend}-{self.filesize_var}-{self.chunksize_var}"',
                        count=1,
                    )

                    execute = execute.replace(
                        "#INSTRUMENTER_STOP",
                        inst_stop,
                    )
                else:
                    logger.warning(
                        "No stopping instrumenter found, assuming you're using decorator or context managers."
                    )
            else:
                logger.warning(
                    f'No instrumenter methods found of {self.profiler_config.package} but mode was set to "{self.global_config.profiler_mode}" which requires instrumenter metthods. Continuing with mode: "auto" for now.'
                )

        path_to_tmp_file = Path(f"{self.dir_path}/execute.{self.language}")
        with open(path_to_tmp_file, "w") as file:
            file.write(execute)

        tmp_file = f"execute.{self.language}"
        compiled_file_info: CompileInfo = {
            "compiled_file_location": "",
            "ld_library_path": "",
        }
        if self.compile:
            compiled_file_info = self.__compile_file(path=path_to_tmp_file)
            tmp_file = f"./{compiled_file_info['compiled_file_location']}"

        if self.par_backend is not None:
            run_command = run_command + " -p"
            run_command = run_command.replace(" -n ", f" -n {self.ranks} ", 1)

            if self.collective:
                run_command = run_command + f"-I {self.collective}"

        run_command = run_command.replace("{runnable}", f"{tmp_file} ", 1)
        run_command = run_command.replace(" -i", f" -i {self.internal_i} ", 1)
        run_command = run_command.replace(" -p", f" -p {self.parallel} ", 1)

        if "-b" not in run_command:
            run_command = run_command + "-b 1 "

        if "-l" not in run_command:
            run_command = run_command + f"-l {self.location} "

        vars_to_bm = ",".join(self.var_to_bm)
        if "-v" not in run_command:
            run_command = run_command + "-v"

        run_command = run_command.replace(" -v", f" -v {vars_to_bm} ", 1)

        if self.language == "c":
            size = []
            for var in self.var_to_bm:
                size.append(self.run_config.variables[var]["shape"])

            run_command = run_command + f"-s {sum([sum(x) for x in size])}"

        shell_type = "bash"
        if self.slurm_avail and not self.local:
            shell_type = "sbatch"

        run_command = [
            shell_type,
            self.__assemble_bash(
                self.bash_location, compile_file_info=compiled_file_info
            ),
            run_command,
        ]

        original_run_command = str(run_command[-1])
        for i in range(self.iterations):
            env_vars: dict[str, str] = {}
            if self.profiler:
                tmp_command = original_run_command
                profiling_res_path = f"{self.profiling_res_path.absolute()}/{self.format}-{self.par_backend}-{self.filesize_var}-{self.chunksize_var}-{self.current_time}-{i}"
                env_vars.update(self.profiler_config.env_vars)

                if self.profiler_config.export_method:
                    for key in self.profiler_config.export_method:
                        item = self.profiler_config.export_method[key]
                        item = item.replace(
                            "<profile_path>", profiling_res_path, count=1
                        )
                        self.profiler_config.export_method[key] = item

                    env_vars.update(self.profiler_config.export_method)
                else:
                    tmp_command = tmp_command.replace(
                        "<profile_path>",
                        str(profiling_res_path),
                        count=1,
                    )
                    run_command[-1] = tmp_command

            logger.debug(f"Run command used {run_command}")
            logger.debug(f"env vars: {env_vars}")
            env_vars.update(os.environ)
            if self.no_caching:
                self.__no_caching_helper(run_command, i)

            p = subprocess.run(
                run_command,
                capture_output=True,
                text=True,
                cwd=self.dir_path,
                check=True,
                env=env_vars,
            )

            if logger.isEnabledFor(logging.DEBUG):
                logger.error(p.stderr)
            logger.debug(p.stdout)

    def __no_caching_helper(self, run_command: list[str], iteration: int):
        new_path = Path(f"{self.dir_path}/{iteration}")
        new_path.mkdir(parents=True)

        current_path = Path()
        for path in self.dir_path.rglob(f"*.{self.extension}"):
            current_path = path

        logger.debug(f"current location: {current_path} -> new location: {new_path}")
        self.__prepare_files()
        new_file_location = shutil.move(
            current_path.absolute(),
            f"{new_path.absolute()}/{iteration}.{self.extension}",
        )

        tmp_command = str(run_command[-1]).replace(
            f"-l {self.location}", f"-l {new_file_location}"
        )
        run_command[-1] = tmp_command

        logger.debug(f"new run command: {run_command}")
        self.location = new_file_location
        self.__prepare_files()

    def __prepare_files(self):
        purge_files = []
        current_path = Path(self.location)
        if current_path.is_file():
            purge_files.append(current_path)
        else:
            purge_files = current_path.rglob("*")

        for path in purge_files:
            if path.is_file():
                with open(path, "r+") as file:
                    file.flush()
                    os.fsync(file.fileno())
                    if hasattr(os, "posix_fadvise"):
                        os.posix_fadvise(file.fileno(), 0, 0, os.POSIX_FADV_DONTNEED)

    def __replace_main(self, language: str) -> str:
        """
        Contains pre-made main methods that can be injected. These methods contain functioning code to achieve feature parity among benchmarks requested.

        Parameters
        ----------

        language: str
            The programming language requested. Depending on which is requested, a different `main` method will be returned.

        Returns
        -------

        str
            Source code for a main method that will be injected into either or both the `create_file` or `execute_file`.
        """
        match language:
            ##################################################################################################
            #### Py Part to be injected for #MAIN
            ##################################################################################################

            case "py":
                return f"""
import argparse
import ast
import os

from mpi4py import MPI
            
def main():

    parser = argparse.ArgumentParser(
        prog="Python Dataformat-Benchmark",
        description="run python based benchmark for Zarr, NetCDF4 and HDF5",
    )
    parser.add_argument("-c", "--create", type=int, default=-1, help="creates Zarr, NetCDF4 and HDF5 Files using a previously saved run format")
    parser.add_argument("-b", "--benchmark", type=int, default=-1, help="benchmark to run")
    parser.add_argument("-v", "--var_to_bm", type=str, default=None, help="var_to_bm to read, if none is provided all are read")
    parser.add_argument("-V", "--variables", type=str, default=None, help="variables to create")
    parser.add_argument("-S", "--shape", type=str, default=None, help="shapes per variable to create")
    parser.add_argument("-C", "--chunk", type=str, default=None, help="chunks per variable to create")
    parser.add_argument("-D", "--datatype", type=str, default=None, help="datatype per variable to create")
    parser.add_argument("-p", "--parallel", type=bool, default=False, help="If to run the benchmark using parallelism of any kind supported")
    parser.add_argument("-i", "--iterations", type=int, default=1, help="number of internal iterations to run the benchmark for. Will cause caching effects")
    parser.add_argument("-l", "--location", type=str, default="", help="Location where file will be create / saved")
    parser.add_argument("-I", "--input_output", type=bool, default=False, help="Set I/O to either use independent (default or False) or collective I/O (True)")
    args = parser.parse_args()
    
    match args.benchmark:
        case 1:
            
            result: list[tuple[str, str, str]] | None = bench(iterations=args.iterations, 
                            variables=args.var_to_bm, 
                            parallel=args.parallel, 
                            path=args.location, 
                            collective=args.input_output,
                            )

            import json
            if result:
                from pathlib import Path
                
                converted: list[str] = []
                for entry in result:
                    converted.append(("-").join(entry))

                res_path = "{self.results_path.absolute()}/{self.id}-{self.current_time}.json"
                if Path(res_path).exists():
                    with open(res_path, "r") as t:
                        tmp: list[str] = []
                        tmp.extend(json.load(t))
                        tmp.extend(converted)
                        converted = tmp

                with open(res_path, "w") as f:
                    json.dump(converted, f)
                
        case -1:
            variables   = args.variables.split(",")
            shapes      = [ast.literal_eval(e) for e in args.shape.split(",")]
            chunks      = [ast.literal_eval(e) for e in args.chunk.split(",")]
            datatypes   = args.datatype.split(",")
            
            if args.create != -1:
                create(variables=variables, 
                        shapes=shapes, 
                        chunks=chunks, 
                        datatypes=datatypes, 
                        parallel=args.parallel, 
                        path=args.location, 
                        collective=args.input_output
                        )

if __name__=="__main__":
    main()
        """

            ##################################################################################################
            #### C Part to be injected for #MAIN
            ##################################################################################################

            case "c":
                tmp = """
            
#include <unistd.h>
#include <argp.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

void save_double_list_to_json(double *arr, char *file_name, size_t size)
{
    FILE *fptr;

    fptr = fopen(file_name, "r+");
    
    if (fptr == NULL)
    {
        fptr = fopen(file_name, "w");
        
        if (fptr == NULL)
        {
            fprintf(stderr, "cannot open target file %s\\n", file_name);
            exit(1);
        }
    }
    
    if(fgetc(fptr) != 91){     
        fprintf(fptr, "[");
    } else {
        (void)0;
    }
    
    int ch;
    while ((ch = fgetc(fptr)) != EOF)
    {   
        if (ch == ']')
        {
            fseek(fptr, -1, SEEK_CUR);
            fputc(',',fptr);
            fseek(fptr, 0, SEEK_CUR);
        }
    }

    for (size_t i = 0; i < size; i++)
    {
        fprintf(fptr, "%f", arr[i]);

        if (i != size - 1)
        {
            fprintf(fptr, ",");
        }
    }

    fprintf(fptr, "]");

    fclose(fptr);
}

void removeCharPointer(char *str, char c) {
    char *rS = str;
    char *rD = str;
    for(; *rD != 0; rS++) {
        if(*rS == c && *rS)
            continue;
        *rD = *rS;
        rD++;
        if(!*rS)
            return;
    }
}

void save_string_list_to_json(char **arr, char *file_name, size_t size)
{
    FILE *fptr;

    fptr = fopen(file_name, "r+");
    
    if (fptr == NULL)
    {
        fptr = fopen(file_name, "w");
        
        if (fptr == NULL)
        {
            fprintf(stderr, "cannot open target file %s\\n", file_name);
            exit(1);
        }
    }
    
    if(fgetc(fptr) != 91){     
        fprintf(fptr, "[");
    } else {
        (void)0;
    }
    
    int ch;
    while ((ch = fgetc(fptr)) != EOF)
    {   
        if (ch == ']')
        {
            fseek(fptr, -1, SEEK_CUR);
            fputc(',',fptr);
            fseek(fptr, 0, SEEK_CUR);
        }
    }

    for (size_t i = 0; i < size; i++)
    {   
        char * tmp = arr[i];
        removeCharPointer(tmp, '[');
        removeCharPointer(tmp, ']');
        fprintf(fptr, "\\"%s\\"", tmp);

        if (i != size - 1)
        {
            fprintf(fptr, ",");
        }
    }

    fprintf(fptr, "]");

    fclose(fptr);
}


typedef struct args_t
{
    int create;
    int benchmark;
    char *var_to_bm;
    char *variables;
    hsize_t size;
    char *shape;
    char *chunk;
    char *datatype;
    int parallel;
    int input_output;
    int iterations;
    char *location;
} args_t;

static int parse_opt(int key, char *arg, struct argp_state *state)
{
    args_t *arguments = state->input;

    switch (key)
    {
    case 'c':
        arguments->create = atoi(arg);
        break;
    case 'b':
        arguments->benchmark = atoi(arg);
        break;
    case 'v':
        arguments->var_to_bm = arg;
        break;
    case 'V':
        arguments->variables = arg;
        break;
    case 's':
        arguments->size = strtoull(arg, NULL, 10);
        break;
    case 'S':
        arguments->shape = arg;
        break;
    case 'C':
        arguments->chunk = arg;
        break;
    case 'D':
        arguments->datatype = arg;
        break;
    case 'p':
        arguments->parallel = strtoull(arg, NULL, 10);
        break;
    case 'i':
        arguments->iterations = atoi(arg);
        break;
    case 'I':
        arguments->input_output = atoi(arg);
        break;
    case 'l':
        arguments->location = arg;
        break;
    case ARGP_KEY_ARG:
        return 0;
    default:
        return ARGP_ERR_UNKNOWN;
    }
    return 0;
}

static struct argp_option options[] = {
    {"create file", 'c', "NUM", 0, "If to create a file"},
    {"benchmark",   'b', "NUM", 0, "If to run benchmark"},
    {"var_to_bm",   'v', "c",   0, "Variables within a file to benchmark"},
    {"variables",   'V', "c",   0, "Variables the file should contain"},
    {"size",        's', "NUM", 0, "Specifiy the size of the file to read"},
    {"shape",       'S', "c",   0, "Specifiy the shapes of the file you want to create as list of lists"},
    {"chunk",       'C', "c",   0, "Specifiy the chunksize of the file you want to create as list of lists"},
    {"datatype",    'D', "c",   0, "Data types each variable should have as list"},
    {"parallel",    'p', "NUM", 0, "If to use parallelism or not"},
    {"iterations",  'i', "NUM", 0, "Ammount of iterations the benchmark should run"},
    {"input-output",'I', "NUM", 0, "Set I/O to either use independent (default or False) or collective I/O (True)"},
    {"location",    'l', "c",   0, "Location where file is going to be created / read from"},
    {0}};

hsize_t word_count(char *smth, char delim)
{
    hsize_t count = 1;
    for (hsize_t x = 0; x < strlen(smth); x++)
        if (smth[x] == delim)
            count++;
    return count;
}

int get_chars(char *smth, hsize_t amount, char **buf)
{
    hsize_t i = 0;
    char *token;
    char *rest = smth;

    while ((token = strtok_r(rest, ",", &rest)))
    {
        if (i == amount)
            break;
        buf[i] = calloc(strlen(token), sizeof(char *));
        strcpy(buf[i], token);
        i++;
    }
    return 0;
}

int get_list_contents(char *smth, hsize_t *buf)
{
    hsize_t i = 0;
    char tmp_char[CHAR_MAX] = "";
    bool flag = false;
    for (hsize_t x = 0; x < strlen(smth); x++)
    {
        if (smth[x] != 44) // ASCII ","
        {
            if (smth[x] == 91) // ASCII "["
                flag = true;
            if (smth[x] == 93) // ASCII "]"
                flag = false;

            if (flag == true && smth[x] != 91)
            {
                char tmp = smth[x];
                strncat(tmp_char, &tmp, 1);
            }
        }
        else
        {
            buf[i] = (hsize_t)strtoull(tmp_char, NULL, 10);
            tmp_char[0] = '\\0';
            i++;
        }
    }
    buf[i] = (hsize_t)strtoull(tmp_char, NULL, 10);
    return 0;
}

int get_individual_as_jagged(char *smth, hsize_t size, hsize_t **buf, hsize_t *jagged_size)
{
    char *token;
    char *rest = smth;

    hsize_t current_var = 0;
    while ((token = strtok_r(rest, "-", &rest)))
    {
        if (current_var == size)
            break;
        hsize_t dims = word_count(token, ',');

        buf[current_var] = calloc(dims, sizeof(hsize_t));
        int res = get_list_contents(token, buf[current_var]);
        jagged_size[current_var] = dims;
        current_var++;
    }
    return 0;
}

int main(int argc, char *argv[])
{
    struct argp argp = {options, parse_opt};

    args_t arguments;
    arguments.create = -1;
    arguments.benchmark = -1;
    arguments.var_to_bm = "[]";
    arguments.variables = "[]";
    arguments.size = 134217728;
    arguments.shape = "[]";
    arguments.chunk = "[]";
    arguments.datatype = "[]";
    arguments.parallel = 1;
    arguments.iterations = 1;
    arguments.location = "test.c";

    printf("Parsing: %d, var_to_bm: %s, variables: %s, shapes: %s, chunks: %s, datatypes: %s, parallel: %d, iterations: %d\\n", arguments.benchmark, arguments.var_to_bm, arguments.variables, arguments.shape, arguments.chunk, arguments.datatype, arguments.parallel, arguments.iterations);
    argp_parse(&argp, argc, argv, 0, 0, &arguments);
    
    hsize_t size = arguments.size;

    char *location = arguments.location;
    int iterations = arguments.iterations;
    int res;

    // get variables to benchmark
    hsize_t var_bm_count = word_count(arguments.var_to_bm, ',');

    // get variables
    hsize_t var_count = word_count(arguments.variables, ',');

    // get shapes
    hsize_t **shapes = calloc(var_count, sizeof(hsize_t *));
    hsize_t shapes_size[var_count];

    // get chunks
    hsize_t **chunks = calloc(var_count, sizeof(hsize_t *));
    hsize_t chunks_size[var_count];

    printf("Parsing: %d, parallel: %d, iterations: %d\\n", arguments.benchmark, arguments.parallel, arguments.iterations);

    // arguments parsing for creation of file
    switch (arguments.create)
    {
    case -1:
        break;
    case 1:

        // get variables
        char **variables = calloc(var_count, sizeof(char *));
        res = get_chars(arguments.variables, var_count, variables);


        // get shapes
        res = get_individual_as_jagged(arguments.shape, var_count, shapes, shapes_size);


        // get chunks
        res = get_individual_as_jagged(arguments.chunk, var_count, chunks, chunks_size);


        // get datatypes
        printf("word count: %ld\\n", var_count);
        char **datatypes = calloc(var_count, sizeof(char *));
        res = get_chars(arguments.datatype, var_count, datatypes);


        printf("Creating hdf5 file\\n");
        create(argc, argv, false, variables, shapes, chunks, datatypes, location);

        // Free variables, datatypes, shape and chunks
        for (int i = 0; i < var_count; i++)
        {
            free(variables[i]);
        }
        free(variables);

        for (int i = 0; i < var_count; i++)
        {
            free(datatypes[i]);
        }
        free(datatypes);

        for (int i = 0; i < var_count; i++)
        {
            free(shapes[i]);
        }
        free(shapes);

        for (int i = 0; i < var_count; i++)
        {
            free(chunks[i]);
        }
        free(chunks);
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
        printf("No benchmark specified, exiting programm now \\n");
        break;
    case 1:
        // get variables to benchmark
        char **vars_to_bm = calloc(var_bm_count, sizeof(char *));
        res = get_chars(arguments.var_to_bm, var_bm_count, vars_to_bm);

        
        double * result = calloc(iterations, sizeof(double));
        char ** nodes   = calloc(iterations, sizeof(char *));

        printf("Running hdf5 benchmark for %d iterations reading %ld elements\\n", iterations, size);
        bench(argc, argv, size, vars_to_bm, iterations, location, result);

        // Free variables to benchmark
        for (int i = 0; i < var_bm_count; i++)
        {
            free(vars_to_bm[i]);
        }
        free(vars_to_bm);
        
        <result-collection>
        
        free(result);
        free(nodes);
        break;
    case ARGP_KEY_ARG:
        return 0;
    default:
        return ARGP_ERR_UNKNOWN;
    }
    
    //MPI_FINALIZE
    
    return 0;
}
"""

                case_serial = """               
        save_double_list_to_json(result, "<result-path>.json", iterations);
        
        for(int i = 0; i < iterations; i++){
            if (getenv("SLURM_JOB_NODELIST") != NULL) {
                nodes[i] = getenv("SLURM_JOB_NODELIST");
            } else {
                char str[] = "None";
                nodes[i] = str;
            }
        }
        save_string_list_to_json(nodes, "<nodes-path>.json", iterations);
"""

                case_mpi = """
        int mpi_rrank;
        MPI_Comm comm = MPI_COMM_WORLD;
        MPI_Comm_rank(comm, &mpi_rrank);

        printf("rank: %d \\n", mpi_rrank);
        if (mpi_rrank == 0)
        {
            save_double_list_to_json(result, "<result-path>.json", iterations);
            
            for(int i = 0; i < iterations; i++){
                
                if (getenv("SLURM_JOB_NODELIST") != NULL) {
                    nodes[i] = getenv("SLURM_JOB_NODELIST");
                } else {
                    char str[] = "None";
                    nodes[i] = str;
                }
            }
            save_string_list_to_json(nodes, "<nodes-path>.json", iterations);
        }
"""

                if self.parallel and self.par_backend == "MPI":
                    tmp = tmp.replace("//MPI_FINALIZE", "MPI_Finalize();", 1)
                    tmp = tmp.replace("<result-collection>", case_mpi, 1)
                else:
                    tmp = tmp.replace("<result-collection>", case_serial, 1)

                tmp = tmp.replace(
                    "<result-path>",
                    f"{self.results_path.absolute()}/{self.id}-{self.current_time}",
                    1,
                )
                return tmp

            case _:
                raise ValueError(
                    f"{language} is not support by the BenchmarkConfig. Somehow we came all the way until here without catching that."
                )

    def __assemble_bash(self, path: str, compile_file_info: CompileInfo) -> str:
        """
        Assembles the final `bash` or `sbatch` file containing all required information to execute whatever source provided.

        Parameters
        ----------

        path: str
            Location where the `bash` or `sbatch` file will be created.

        compile_file_info: tuple
            Contains the location of the compiled file and the ld_library_path that will be injected.

        Returns
        -------

        str
            Name of the final `bash` or `sbatch` script containing all required information like file location, slurm_options, package location, etc.

        """
        if self.slurm_avail and not self.local:
            self.slurm_options = self.slurm_options.replace("#SBATCH --nodes=", "#")
            self.slurm_options = self.slurm_options.replace("#SBATCH --job-name=", "#")

            if "#SBATCH --wait" not in self.slurm_options:
                self.slurm_options = self.slurm_options + "#SBATCH --wait\n"

            self.slurm_options = self.slurm_options + f"#SBATCH --ntasks={self.ranks}\n"

            self.slurm_options = (
                self.slurm_options
                + f"#SBATCH --job-name={self.format.replace(' ', '')}-{self.total_filesize}{self.unit}-{str(self.run_config).replace(' ', '')}\n"
            )

            if "#SBATCH --nodes=" not in self.slurm_options:
                self.slurm_options = (
                    self.slurm_options + f"#SBATCH --nodes={self.nodes}\n"
                )

        else:
            self.slurm_options = ""

        load_git = ""
        try:
            subprocess.run(
                ["git", "--version"], check=True, capture_output=True, text=True
            )
        except subprocess.CalledProcessError:
            load_git = "module load git"

        bash_location = f"{path}.sh"

        if not Path(f"{self.dir_path}/{bash_location}").exists():
            with open(Path(f"{self.dir_path}/{bash_location}"), "w") as file:
                file.write(f"""#!/bin/bash

{self.slurm_options}
                       
# Begin of section with executable commands
ls -lh

#sbcast -f "$bin" /tmp/bin
#export $bin="/tmp/bin"

{load_git}
. {self.root_path}/spack/share/spack/setup-env.sh


{self.spack_manager.load_env()}

source {self.spack_manager.env_location.absolute()}/.venv/bin/activate

{compile_file_info["ld_library_path"]}

$1

mpi_enabled=$2
w=true

if [ "$mpi_enabled" = "$w" ]; then

    export OMPI_MCA_osc="ucx"
    export OMPI_MCA_pml="ucx"
    export OMPI_MCA_btl="self"
    export UCX_HANDLE_ERRORS="bt"
    export OMPI_MCA_pml_ucx_opal_mem_hooks=1
    
    export OMPI_MCA_io="romio321"          # basic optimisation of I/O
    export UCX_TLS="shm,rc_mlx5,rc_x,self" # for jobs using LESS than 150 nodes
    #export UCX_TLS="shm,dc_mlx5,dc_x,self" # for jobs using MORE than 150 nodes
    export UCX_UNIFIED_MODE="y"            
    
    export OMPI_MCA_coll_tuned_use_dynamic_rules="true"
    export OMPI_MCA_coll_tuned_alltoallv_algorithm=2
    
fi
spack env deactivate                     
""")

        return bash_location
