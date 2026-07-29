from ClusterShell.Worker.fastsubprocess import CalledProcessError
import itertools
import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from hpffbench.configloader import ProcessedPath, SpackEnv

logger = logging.getLogger(__name__)


@dataclass
class SpackManager:
    """Defines spack manager class which acts as an interface for the benchmark-framework with spack. Creates, initializes & manages a spack environment.

    Parameters
    ----------
    handler_id: str
        The handlers id that controls this manager.

    env_name: str

    spack_env: dict
        Dictionary containing the configuration of a environments to be created.

    use_spack_env: bool
        If to used the specific environment or to skip it and rely on system installed packages.

    paths: dict
        Dictionary of paths. Specifically to identify where to save environment data to.

    only_data: bool
        If to run environment initialization, checks, etc. or to skip them entirely.
        Since the environment is being hashed at runtime, at least creating basic metadata
        is required to generate the same hash even when just performing a dry-run to gather data.

    Attributes
    ----------
    handler_id: str
        The handlers id that controls this manager.

    env_name: str

    spack_env: dict
        Dictionary containing the configuration of a environments to be created.

    target: list
        List of formats this environment is being used for. Formats not in this list will not be used with this environment.

    language: list
        Similar to `target` for programming languages.

    packages: dict
        Dictionary describing the spack packages to be added or installed to the environment.

    additional: str
        Additional python packages to be installed for the environment via pip.

    env_location: Path
        The location the environment and related metadata has been saved to.

    package_locations: dict
        Dictionary of where every spack packages can be found identified via their spack packages hash.

    initialized: bool
    """

    handler_id: str
    env_name: str
    spack_env: SpackEnv
    target: list
    language: list
    packages: dict
    additional: str
    env_location: Path
    package_locations: dict
    initialized: bool

    def __init__(
        self,
        handler_id: str,
        env_name: str,
        spack_env: SpackEnv,
        paths: dict[str, ProcessedPath],
        use_spack_env=True,
        only_data=False,
    ):

        self.initialized = False
        self.handler_id = handler_id
        self.spack_env = spack_env
        self.env_name = env_name

        self.__use_spack_env: bool = use_spack_env
        self.__only_data: bool = only_data
        self.__root_path: str = paths["path_to_root"]["path"]

        self.compiler = self.spack_env.config["compiler"]
        self.target = self.spack_env.config["target"]
        self.language = self.spack_env.config["language"]
        self.packages = self.spack_env.config["packages"]

        self.env_name_present = False
        self.install = self.spack_env.config["install"]

        self.package_locations = {}
        self.python_version = "python"

        self.additional = self.spack_env.config["additional"]

        self.loadables = {}

        self.env_location = Path(f"environments/{self.env_name}")
        self.env_location.mkdir(parents=True, exist_ok=True)

        self.file_location = Path(
            f"{self.env_location.absolute()}/env-{self.env_name}.sh"
        )

        for name, info in self.packages.items():
            versions = info["versions"]
            variants = [info["variants"]]

            combinations = list(
                itertools.product(*[versions, variants, [self.compiler]])
            )
            self.loadables[name] = combinations

            # Check if environment exits, reuse if it does. Will usually exist, even if downstream processes fail. Hence further checks
            with open(f"{self.env_location.absolute()}/check-location.sh", "w") as file:
                file.write("#!/bin/bash\n")
                file.write("set -e\n")
                file.write(f". {self.__root_path}/spack/share/spack/setup-env.sh\n")
                file.write(f"spack env activate {self.env_name}\n")

            try:
                subprocess.run(
                    ["bash", f"{self.env_location.absolute()}/check-location.sh"],
                    text=True,
                    capture_output=True,
                    check=True,
                )
                self.env_name_present = True
            except CalledProcessError:
                pass

            for combination in combinations:
                package = f"{name}@{combination[0]} {combination[1]} %{combination[2]}"

                if name == "python":
                    self.python_version = package

                if not self.__only_data and self.env_name_present:
                    # Check if package can be found in environment, usually fails if version or compiler is mismatched with what is available in spack at the time.

                    with open(
                        f"{self.env_location.absolute()}/check-location.sh", "w"
                    ) as file:
                        file.write("#!/bin/bash\n")
                        file.write("set -e\n")
                        file.write(
                            f". {self.__root_path}/spack/share/spack/setup-env.sh\n"
                        )
                        file.write(f"spack -e {self.env_name} find {package}\n")

                    try:
                        p = subprocess.run(
                            [
                                "bash",
                                f"{self.env_location.absolute()}/check-location.sh",
                            ],
                            check=True,
                            text=True,
                            capture_output=True,
                        )
                    except subprocess.CalledProcessError:
                        raise RuntimeError(
                            f'At least one package "{package}" failed installing. Usually due to spack package / compiler version mismatch.'
                        )

                    if not Path(f"{self.env_location}/.venv").is_dir():
                        raise OSError(
                            "additional pip packages have not installed properly"
                        )

                    with open(
                        f"{self.env_location.absolute()}/check-location.sh", "w"
                    ) as file:
                        file.write("#!/bin/bash\n")
                        file.write(
                            f". {self.__root_path}/spack/share/spack/setup-env.sh\n"
                        )
                        file.write(f"spack -e {self.env_name} location -i {package}\n")

                    p = subprocess.run(
                        [
                            "bash",
                            f"{self.env_location.absolute()}/check-location.sh",
                        ],
                        text=True,
                        capture_output=True,
                        check=True,
                    )
                    if p.returncode != 0:
                        raise RuntimeError(f"{package}, unknown cause {p.stderr}")
                    self.package_locations[name] = (f"{package}", p.stdout.rstrip())

                    self.initialized = True

    def initialize_env(self):
        """
        Initialized the spack environment, creates a named directory within the environment store path and sets the `initialized` to `True` once finished.
        """
        env_not_exists = False
        try:
            with open(self.file_location, "w") as file:
                file.write("#!/bin/bash\n")
                file.write("set -e\n")
                file.write(f". {self.__root_path}/spack/share/spack/setup-env.sh\n")
                file.write(f"spack env activate {self.env_name}\n")

            subprocess.run(
                ["bash", self.file_location],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            env_not_exists = True

        if env_not_exists:
            with open(self.file_location, "w") as file:
                file.write("#!/bin/bash\n")
                file.write("set -e\n")

                try:
                    subprocess.run(
                        ["git", "--version"], check=True, capture_output=True
                    )
                except subprocess.CalledProcessError:
                    file.write("module load git\n")

                file.write(f". {self.__root_path}/spack/share/spack/setup-env.sh\n")

                first = True
                check_installed = Path(f"{self.file_location}/.venv")
                for index, (name, _) in enumerate(self.packages.items()):
                    combinations = self.loadables[name]

                    if first:
                        file.write(f"spack env create {self.env_name}\n")
                        file.write("spack env list\n")
                        first = False

                    self.__add_packages(
                        file=file, combinations=list(combinations), package_name=name
                    )

                    if (
                        index == len(self.packages.items()) - 1
                        and self.install
                        and not check_installed.exists()
                    ):
                        file.write(f"spack -e {self.env_name} install\n")

                file.write("spack env list\n")
                file.write(f"spack env activate {self.env_name}\n")
                file.write(f"spack load {self.python_version}\n")
                file.write("python --version\n")
                file.write(f"python -m venv {self.env_location.absolute()}/.venv\n")
                file.write(
                    f"source {self.env_location.absolute()}/.venv/bin/activate\n"
                )
                file.write("pip install --upgrade pip \n")
                file.write(f"{self.additional}\n")
                file.write(f"pip install -e {self.__root_path}\n")
                file.write("pip list\n")
                file.write("spack env deactivate\n")

            logger.info(f"Initialize environment {self.env_name}")

            if self.__use_spack_env:
                try:
                    subprocess.run(
                        ["bash", self.file_location],
                        stdout=sys.stdout,
                        stderr=sys.stderr,
                        check=True,
                    )
                except subprocess.CalledProcessError:
                    if not self.env_name_present:
                        raise RuntimeError(
                            "Environment creation has failed, most likely due to compiler or version mismatch, please check above for which package failed!"
                        )

            self.file_location.unlink()

        logger.info("Finish Initialize environment")
        self.initialized = True

        # Check if location to package can be found, usually fails if the package has not been installed
        for name, combinations in self.loadables.items():
            for combination in combinations:
                package = f"{name}@{combination[0]} {combination[1]} %{combination[2]}"

                with open(
                    f"{self.env_location.absolute()}/check-location.sh", "w"
                ) as file:
                    file.write("#!/bin/bash\n")
                    file.write(f". {self.__root_path}/spack/share/spack/setup-env.sh\n")
                    file.write(f"spack -e {self.env_name} location -i {package}\n")

                p = subprocess.run(
                    ["bash", f"{self.env_location.absolute()}/check-location.sh"],
                    text=True,
                    capture_output=True,
                    check=True,
                )
                if p.returncode != 0:
                    raise RuntimeError(
                        f'{package}, has not been installed yet. Either pass "install" flag or install it manually.'
                    )
                self.package_locations[name] = (f"{package}", p.stdout.rstrip())

    def load_env(self) -> str:
        """
        Creates a str of packages to load into the environment.

        Returns
        -------
        str
            Returns the str containing the packages to load. This string can then be injected into a `bash` or `sbatch` script.
        """
        loadable = f"spack env activate {self.env_name}\n"

        logger.debug(self.loadables)
        for name, combinations in self.loadables.items():
            loadable = self.__load_packages(
                loadable=loadable, combinations=combinations, package_name=name
            )

        return loadable

    def __add_packages(
        self, file, combinations: list[tuple[str, ...]], package_name: str
    ):
        """
        Assembles the individual add commands for each package to add to the environment.

        Parameters
        ----------
        file : TextIOWrapper[_WrappedBuffer]
            Bash script that will be executed to facilitated the functionally.
            Required commands will be written to the file.

        combinations: list
            List of combinations of packages, variants, versions and compilers to use.
            Should be deprecated and renamed to something more fitting as multiple combinations
            within a single environment is no longer planned and currently not supported.

        package_name: str
            Name of the packages to be loaded.
        """
        for combination in combinations:
            logger.debug(
                f"spack -e {self.env_name} add {package_name}@{combination[0]} {combination[1]} %{combination[2]}"
            )
            file.write(
                f"spack -e {self.env_name} add {package_name}@{combination[0]} {combination[1]} %{combination[2]}\n"
            )

    def __load_packages(
        self, loadable: str, combinations: list, package_name: str
    ) -> str:
        """
        Assembles the individual load commands for each package.

        Parameters
        ----------
        loadable : str
            String ot eventually contain all packages that need to be loaded into the environment.

        combinations: list
            List of combinations of packages, variants, versions and compilers to use.
            Should be deprecated and renamed to something more fitting as multiple combinations
            within a single environment is no longer planned and currently not supported.

        package_name: str
            Name of the packages to be loaded.


        Returns
        -------
        str
            String containing packages to load by combinations requested.
        """
        for combination in combinations:
            logger.debug(
                f"spack -e {self.env_name} load {package_name}@{combination[0]} {combination[1]} %{combination[2]}"
            )
            loadable = (
                loadable
                + f"eval $(spack -e {self.env_name} load --sh {package_name}@{combination[0]} {combination[1]} %{combination[2]})\n"
            )

        return loadable

    def delete(self):
        """
        Deletes the environment and purges associated data & metadata.
        """

        if self.initialized:
            with open(self.file_location, "w") as file:
                file.write("#!/bin/bash  \n")
                try:
                    subprocess.run(
                        ["git", "--version"],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                except subprocess.CalledProcessError:
                    file.write("module load git\n")

                file.write(f". {self.__root_path}/spack/share/spack/setup-env.sh\n")
                file.write(f"spack env activate {self.env_name} -p \n")
                file.write("spack remove --all \n")
                file.write("spack env deactivate\n")
                file.write(f"spack env remove {self.env_name} -y \n")

            p = subprocess.run(
                ["bash", self.file_location], capture_output=True, check=True
            )
            logger.error(p.stderr)
            logger.info(p.stdout)

            self.file_location.unlink()
            shutil.rmtree(path=self.env_location.absolute())

        else:
            logger.warning(
                f"{self.env_name} has not been initialized, nothing to delete"
            )
