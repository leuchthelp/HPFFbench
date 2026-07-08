from typing import TypedDict, TypeAlias, Literal
import time
import math

from mpi4py import MPI
import numpy as np
import netCDF4
import zarr
import h5py


class Form(TypedDict):
    shape: list[int]
    chunks: list[int]
    dtype: str


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


Mode: TypeAlias = Literal["r", "r+", "a", "w"]


class Datastruct:
    def __init__(
        self,
        dataset: zarr.Group | h5py.File | netCDF4.Dataset | None = None,
        path: str = "",
        shape: list[int] = [],
        chunks: list[int] = [],
        mode: Mode = "r",
        engine: str = "",
        compression: str = "",
        parallel: bool = False,
        collective: bool = False,
    ):
        self.path: str = path
        self.shape: list[int] = shape
        self.chunks: list[int] = chunks
        self.mode: Mode = mode
        self.engine: str = engine
        self.compression: str = compression
        self.dataset = dataset
        self.parallel: bool = parallel
        self.collective: bool = collective

    def create(
        self,
        path: str,
        form: dict[str, Form],
        engine: str,
        parallel: bool = False,
        collective: bool = False,
    ):
        self.parallel = parallel
        self.collective = collective
        self.engine = engine

        match self.engine:
            case "zarr":
                self.create_zarr(form=form, path=path)

            case "hdf5":
                self.create_hdf5(form=form, path=path)

            case "netcdf4":
                self.create_netcdf4(form=form, path=path)

        return self

    def create_zarr(self, form: dict[str, Form], path: str):

        if MPI.COMM_WORLD.rank == 0 or not self.parallel:
            root = zarr.create_group(store=path, overwrite=True)

            for variable, element in form.items():
                shape = element["shape"]
                chunks = element["chunks"]
                dtype = element["dtype"]

                if len(chunks) != 0:
                    x = root.create_array(
                        name=variable, shape=shape, chunks=chunks, dtype=dtype
                    )
                else:
                    x = root.create_array(name=variable, shape=shape, dtype=dtype)

                if self.parallel:
                    if self.collective:
                        print(
                            bcolors.WARNING
                            + "Setting I/O to be collective not supported"
                            + bcolors.ENDC
                        )
                        x[:] = np.random.random_sample(shape)
                    else:
                        print(
                            bcolors.OKBLUE
                            + "Setting I/O to be independent"
                            + bcolors.ENDC
                        )
                        x[:] = np.random.random_sample(shape)

                else:
                    x[:] = np.random.random_sample(shape)

            print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")

        MPI.COMM_WORLD.Barrier()
        return self

    def create_hdf5(self, form: dict[str, Form], path: str):
        # Create file either through mpio or serial
        print(f"{bcolors.WARNING}Creating hdf5 file{bcolors.ENDC}")

        if not self.parallel:
            root = h5py.File(path, "w-")
        else:
            root = h5py.File(path, "w-", driver="mpio", comm=MPI.COMM_WORLD)

        # Create dataset corresponding to the provide number of variables
        for variable, element in form.items():
            shape = element["shape"]
            chunks = element["chunks"]
            dtype = element["dtype"]

            if len(chunks) != 0:
                x = root.create_dataset(
                    variable, shape=shape, chunks=tuple(chunks), dtype=dtype
                )
            else:
                x = root.create_dataset(variable, shape=shape, dtype=dtype)

            # File created dataset with values
            if not self.parallel:
                x[:] = np.random.random_sample(shape)
            else:
                rank = MPI.COMM_WORLD.rank
                rsize = MPI.COMM_WORLD.size
                total_size = shape[0]
                size = int(total_size / rsize)

                rstart = rank * size
                rend = rstart + size

                if self.collective:
                    print(
                        bcolors.OKBLUE + "Setting I/O to be collective" + bcolors.ENDC
                    )
                    x[rstart:rend:] = np.random.random_sample(size)
                else:
                    print(
                        bcolors.OKBLUE + "Setting I/O to be independent" + bcolors.ENDC
                    )
                    if rank == rank:
                        x[rstart:rend:] = np.random.random_sample(size)
                MPI.COMM_WORLD.Barrier()

        root.close()
        print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")

        return self

    def create_netcdf4(self, form: dict[str, Form], path: str):
        root = netCDF4.Dataset(path, "w", format="NETCDF4", parallel=self.parallel)
        root.createGroup("/")
        used = 0

        for variable, element in form.items():
            shape = element["shape"]
            chunks = element["chunks"]
            dtype = element["dtype"]
            dimensions = []

            for size in shape:
                root.createDimension(f"{used}", size)
                dimensions.append(f"{used}")
                used += 1

            if len(chunks) != 0:
                x = root.createVariable(variable, dtype, dimensions, chunksizes=chunks)
            else:
                x = root.createVariable(variable, dtype, dimensions)

            if not self.parallel:
                x[:] = np.random.random_sample(shape)
            else:
                rank = MPI.COMM_WORLD.rank
                rsize = MPI.COMM_WORLD.size
                total_size = shape[0]
                size = int(total_size / rsize)

                rstart = rank * size
                rend = rstart + size

                if self.collective:
                    print(
                        bcolors.OKBLUE + "Setting I/O to be collective" + bcolors.ENDC
                    )
                    x.set_collective(True)
                else:
                    print(
                        bcolors.OKBLUE + "Setting I/O to be independent" + bcolors.ENDC
                    )

                x[rstart:rend:] = np.random.random_sample(size)
                MPI.COMM_WORLD.Barrier()

        root.close()
        print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")

        return self

    def open(self, mode: Mode, engine: str, path: str, parallel: bool = False):
        self.mode = mode
        self.engine = engine
        self.path = path

        self.parallel = parallel
        match self.engine:
            case "zarr":
                self.dataset = zarr.open(self.path, mode=self.mode)

            case "hdf5":
                if self.parallel:
                    self.dataset = h5py.File(
                        self.path, mode=self.mode, driver="mpio", comm=MPI.COMM_WORLD
                    )
                else:
                    self.dataset = h5py.File(self.path, mode=self.mode)

            case "netcdf4":
                self.dataset = netCDF4.Dataset(
                    self.path, mode=self.mode, format="NETCDF4", parallel=self.parallel
                )

        return self

    def __bench_variable(self, variables: list[str], iterations: int):
        if len(variables) > 1:
            raise ValueError("Function with pattern only takes one variable")
        var = variables[0]

        bench = []
        match self.engine:
            case "zarr":
                if not isinstance(self.dataset, zarr.Group):
                    raise ValueError("Not from kind of AnyArray for zarr")

                arrays = dict(self.dataset.arrays())

                var_size: tuple[int, ...] = arrays[var].shape
                for i in range(iterations):
                    print(
                        f"i: {i} for variable: {var} for engine: {self.engine}, size: {var_size}"
                    )
                    start = time.monotonic()
                    arrays[var][:]
                    bench.append(time.monotonic() - start)

                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")

            case "hdf5":
                if not isinstance(self.dataset, h5py.File):
                    raise ValueError("Not from kind of File for hdf5 h5py")

                var_size: tuple[int, ...] = self.dataset[var].shape
                for i in range(iterations):
                    print(
                        f"i: {i} for variable: {var} for engine: {self.engine}, size: {var_size}"
                    )
                    start = time.monotonic()
                    self.dataset[var][:]
                    bench.append(time.monotonic() - start)

                self.dataset.close()
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")

            case "netcdf4":
                if not isinstance(self.dataset, netCDF4.Dataset):
                    raise ValueError("Not from kind of dataset for netcdf4")

                var_size: tuple[int, ...] = self.dataset[var].shape
                for i in range(iterations):
                    print(
                        f"i: {i} for variable: {var} for engine: {self.engine}, size: {var_size}"
                    )
                    start = time.monotonic()
                    self.dataset[var][:]
                    bench.append(time.monotonic() - start)

                self.dataset.close()
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")

    def __bench_variable_parallel(self, variables: list[str], iterations: int):
        if len(variables) > 1:
            raise ValueError("Function with pattern only takes one variable")
        var = variables[0]

        bench = []
        rank = MPI.COMM_WORLD.rank
        rsize = MPI.COMM_WORLD.size
        match self.engine:
            case "zarr":
                if not isinstance(self.dataset, zarr.Group):
                    raise ValueError("Not from kind of AnyArray for zarr")

                arrays = dict(self.dataset.arrays())

                for i in range(iterations):
                    var_size: tuple[int, ...] = arrays[var].shape
                    print(
                        f"i: {i} for variable: {var} for engine: {self.engine}, rank: {rank}, size: {var_size}"
                    )

                    if rank == 0:
                        start = time.monotonic()

                    total_size: int = math.prod(var_size)
                    size = int(total_size / rsize)

                    rstart = rank * size
                    rend = rstart + size
                    arrays[var][rstart:rend:]

                    if rank == 0:
                        bench.append(time.monotonic() - start)
                    MPI.COMM_WORLD.Barrier()

                self.log = bench

                MPI.COMM_WORLD.Barrier()
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")

            case "hdf5":
                if not isinstance(self.dataset, h5py.File):
                    raise ValueError("Not from kind of File for hdf5 h5py")

                for i in range(iterations):
                    var_size: tuple[int, ...] = self.dataset[var].shape
                    print(
                        f"i: {i} for variable: {var} for engine: {self.engine}, rank: {rank}, size: {var_size}"
                    )

                    if rank == 0:
                        start = time.monotonic()

                    total_size: int = math.prod(var_size)
                    size = int(total_size / rsize)

                    rstart = rank * size
                    rend = rstart + size

                    self.dataset[var][rstart:rend:]

                    if rank == 0:
                        bench.append(time.monotonic() - start)
                    MPI.COMM_WORLD.Barrier()

                if rank == 0:
                    self.log = bench

                self.dataset.close()
                MPI.COMM_WORLD.Barrier()
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")

            case "netcdf4":
                if not isinstance(self.dataset, netCDF4.Dataset):
                    raise ValueError("Not from kind of dataset for netcdf4")

                for i in range(iterations):
                    var_size: tuple[int, ...] = self.dataset[var].shape
                    print(
                        f"i: {i} for variable: {var} for engine: {self.engine}, rank: {rank}, size: {var_size}"
                    )

                    if rank == 0:
                        start = time.monotonic()

                    self.dataset[var].set_collective(True)

                    total_size: int = math.prod(var_size)
                    size = int(total_size / rsize)

                    rstart = rank * size
                    rend = rstart + size

                    self.dataset[var][rstart:rend:]

                    if rank == 0:
                        bench.append(time.monotonic() - start)

                    MPI.COMM_WORLD.Barrier()

                if rank == 0:
                    self.log = bench

                self.dataset.close()
                MPI.COMM_WORLD.Barrier()
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")

    def __bench_complete(self, variables: list[str], iterations: int):
        bench = []
        var_sizes: list[tuple[int, ...]] = []
        var_tmp = []

        match self.engine:
            case "zarr":
                if not isinstance(self.dataset, zarr.Group):
                    raise ValueError("Not from kind of AnyArray for zarr")

                arrays = dict(self.dataset.arrays())
                for var in variables:
                    try:
                        var_size: tuple[int, ...] = arrays[var].shape
                        var_sizes.append(var_size)
                        var_tmp.append(var)
                    except KeyError:
                        print(f"Variable: {var} does not exist.")

                for i in range(iterations):
                    print(
                        f"i: {i} for variable: {var_tmp} for engine: {self.engine}, size: {var_sizes}"
                    )
                    start = time.monotonic()

                    for var in variables:
                        try:
                            arrays[var][:]
                        except KeyError:
                            print(f"Variable: {var} does not exist.")

                    bench.append(time.monotonic() - start)

                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")

            case "hdf5":
                if not isinstance(self.dataset, h5py.File):
                    raise ValueError("Not from kind of File for hdf5 h5py")

                for var in variables:
                    try:
                        var_size: tuple[int, ...] = self.dataset[var].shape
                        var_sizes.append(var_size)
                        var_tmp.append(var)
                    except KeyError:
                        print(f"Variable: {var} does not exist.")

                for i in range(iterations):
                    print(
                        f"i: {i} for variable: {var_tmp} for engine: {self.engine}, size: {var_sizes}"
                    )
                    start = time.monotonic()

                    for var in variables:
                        try:
                            # self.dataset[variable].read_direct(arr)
                            self.dataset[var][:]
                        except KeyError:
                            print(f"Variable: {var_tmp} does not exist.")

                    bench.append(time.monotonic() - start)

                self.dataset.close()
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")

            case "netcdf4":
                if not isinstance(self.dataset, netCDF4.Dataset):
                    raise ValueError("Not from kind of dataset for netcdf4")

                for var in variables:
                    try:
                        var_size: tuple[int, ...] = self.dataset[var].shape
                        var_sizes.append(var_size)
                        var_tmp.append(var)
                    except IndexError:
                        print(f"Variable: {var} does not exist.")

                for i in range(iterations):
                    print(
                        f"i: {i} for variable: {variables} for engine: {self.engine}, size: {var_sizes}"
                    )
                    start = time.monotonic()

                    for var in variables:
                        try:
                            self.dataset[var][:]
                        except IndexError:
                            print(f"Variable: {var} does not exist.")

                    bench.append(time.monotonic() - start)

                self.dataset.close()
                self.log = bench
                print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")

    def __bench_complete_parallel(self, variables: list[str], iterations: int):
        match self.engine:
            case "zarr":
                self.__bench_complete_parallel_zarr(
                    variables=variables, iterations=iterations
                )

            case "hdf5":
                self.__bench_complete_parallel_hdf5(
                    variables=variables, iterations=iterations
                )

            case "netcdf4":
                self.__bench_complete_parallel_netcdf4(
                    variables=variables, iterations=iterations
                )

    def __bench_complete_parallel_zarr(self, variables: list[str], iterations: int):
        if not isinstance(self.dataset, zarr.Group):
            raise ValueError("Not from kind of AnyArray for zarr")

        arrays = dict(self.dataset.arrays())

        bench = []
        var_tmp = []
        rank = MPI.COMM_WORLD.rank
        rsize = MPI.COMM_WORLD.size
        for i in range(iterations):
            var_sizes: list[tuple[int, ...]] = []
            for var in variables:
                try:
                    var_size: tuple[int, ...] = arrays[var].shape
                    var_sizes.append(var_size)
                    var_tmp.append(var)
                except KeyError:
                    print(f"Variable: {var} does not exist.")
            print(
                f"i: {i} for variable: {var_tmp} for engine: {self.engine}, rank: {rank}, size: {var_sizes}"
            )

            if rank == 0:
                start = time.monotonic()

            for var in variables:
                try:
                    print(arrays[var].shape)
                    print(math.prod(arrays[var].shape))
                    total_size: int = math.prod(arrays[var].shape)
                    size = int(total_size / rsize)

                    rstart = rank * size
                    rend = rstart + size

                    if self.collective:
                        print(
                            bcolors.WARNING
                            + "Setting I/O to be collective not supported"
                            + bcolors.ENDC
                        )
                    else:
                        print(
                            bcolors.OKBLUE
                            + "Setting I/O to be independent"
                            + bcolors.ENDC
                        )
                        arrays[var][rstart:rend:]

                except KeyError:
                    print(f"Variable: {var} does not exist.")

            if rank == 0:
                bench.append(time.monotonic() - start)

            MPI.COMM_WORLD.Barrier()

        if rank == 0:
            self.log = bench

        MPI.COMM_WORLD.Barrier()
        print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")

    def __bench_complete_parallel_hdf5(self, variables: list[str], iterations: int):
        if not isinstance(self.dataset, h5py.File):
            raise ValueError("Not from kind of File for hdf5 h5py")

        bench = []
        var_tmp = []

        rank = MPI.COMM_WORLD.rank
        rsize = MPI.COMM_WORLD.size

        for i in range(iterations):
            var_sizes: list[tuple[int, ...]] = []
            for var in variables:
                try:
                    var_size: tuple[int, ...] = self.dataset[var].shape
                    var_sizes.append(var_size)
                    var_tmp.append(var)
                except KeyError:
                    print(f"Variable: {var} does not exist.")
            print(
                f"i: {i} for variable: {var_tmp} for engine: {self.engine}, rank: {rank}, size: {var_sizes}"
            )

            if rank == 0:
                start = time.monotonic()

            for var in variables:
                try:
                    total_size: int = math.prod(self.dataset[var].shape)
                    size = int(total_size / rsize)

                    rstart = rank * size
                    rend = rstart + size

                    if self.collective:
                        print(
                            bcolors.OKBLUE
                            + "Setting I/O to be collective"
                            + bcolors.ENDC
                        )
                        self.dataset[var][rstart:rend:]
                    else:
                        print(
                            bcolors.OKBLUE
                            + "Setting I/O to be independent"
                            + bcolors.ENDC
                        )
                        if rank == rank:
                            self.dataset[var][rstart:rend:]

                except KeyError:
                    print(f"Variable: {var} does not exist.")

            if rank == 0:
                bench.append(time.monotonic() - start)

            MPI.COMM_WORLD.Barrier()

        if rank == 0:
            self.log = bench

        self.dataset.close()
        MPI.COMM_WORLD.Barrier()
        print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")

    def __bench_complete_parallel_netcdf4(self, variables: list[str], iterations: int):
        if not isinstance(self.dataset, netCDF4.Dataset):
            raise ValueError("Not from kind of dataset for netcdf4")

        bench = []
        var_tmp = []

        rank = MPI.COMM_WORLD.rank
        rsize = MPI.COMM_WORLD.size

        for i in range(iterations):
            var_sizes: list[tuple[int, ...]] = []
            for var in variables:
                try:
                    var_size: tuple[int, ...] = self.dataset[var].shape
                    var_sizes.append(var_size)
                    var_tmp.append(var)
                except IndexError:
                    print(f"Variable: {var} does not exist.")
            print(
                f"i: {i} for variable: {var_tmp} for engine: {self.engine}, rank: {rank}, size: {var_sizes}"
            )

            if rank == 0:
                start = time.monotonic()

            for var in variables:
                try:
                    total_size: int = math.prod(self.dataset[var].shape)
                    size = int(total_size / rsize)

                    rstart = rank * size
                    rend = rstart + size

                    if self.collective:
                        print(
                            bcolors.OKBLUE
                            + "Setting I/O to be collective"
                            + bcolors.ENDC
                        )
                        self.dataset[var].set_collective(True)
                    else:
                        print(
                            bcolors.OKBLUE
                            + "Setting I/O to be independent"
                            + bcolors.ENDC
                        )

                    self.dataset[var][rstart:rend:]

                except IndexError:
                    print(f"Variable: {var} does not exist.")

            if rank == 0:
                bench.append(time.monotonic() - start)

            MPI.COMM_WORLD.Barrier()

        if rank == 0:
            self.log = bench

        self.dataset.close()
        MPI.COMM_WORLD.Barrier()
        print(f"{bcolors.OKGREEN}FINISHED{bcolors.ENDC}")

    def read(self, pattern: str, variables: str, iterations: int):

        patterns = {
            "bench_variable": self.__bench_variable,
            "bench_complete": self.__bench_complete,
            "bench_variable_parallel": self.__bench_variable_parallel,
            "bench_complete_parallel": self.__bench_complete_parallel,
        }

        return patterns[pattern](variables=variables.split(","), iterations=iterations)
