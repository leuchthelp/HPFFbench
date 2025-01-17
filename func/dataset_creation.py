# Create Testing Dataset, Change Parameters to vary size 

def create_dataset():
    import mpi4py as MPI
    import netCDF4
    import numpy
    
    comm = MPI.COMM_WORLD
    print(f"Hello World from rank {comm.Get_rank()}. total ranks={comm.Get_size()}")

    var_levels = np.random.rand(1_000_000)
    var_rooms = np.random.rand(10)

    rootgrp = netCDF4.Dataset("data/test_dataset.nc", mode="w", format="NETCDF4", comm=MPI_COMM_WORLD, parallel=True)
    xgrp = rootgrp.createGroup("x")
    level = rootgrp.createDimension("level", None)
    room = rootgrp.createDimension("room", None)

    levels = rootgrp.createVariable("levels")
    rooms = rootgrp.createVariable("rooms")

    levels = var_levels
    rooms = var_rooms

    rootgrp.close()
    
    return 0

import ipyparallel as ipp

with ipp.Cluster(n=1) as rc:
    view = rc.load_balanced_view()
    asyncresults = view.map_async(create_dataset)
    asyncresults.wait_interactive()
    results = asyncresults.get()
