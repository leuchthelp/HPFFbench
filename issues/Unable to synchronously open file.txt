netcdf / hdf5 bug:
Can open netcdf file through either h5py netcdf4 or h5netcdf engine

error:
Unable to synchronously open file (unable to open file: name = , errno = 2, error message = 'No such file or directory', flags = 0, o_flags = 0)

cause:
unknown

debugging:

run h5dump results in: h5dump error: unable to open file "data/4f6e0dccfcfe4f76f1e64f187cc0551c.nc"
run ncdump results in: ncdump: data/4f6e0dccfcfe4f76f1e64f187cc0551c.nc: NetCDF: HDF error

run xxd    results in: 00000000: 8948 4446 0d0a 1a0a                      .HDF....

according to xxd the file is a correct HDF file as it does contain the correct string for a HDF file

possible reasons:

unknown

similar issues:

https://forum.hdfgroup.org/t/issue-unlocking-hdf5-file/8552/4
https://github.com/h5py/h5py/issues/2513
