#include <stdio.h>
#include <stdlib.h>
#include <netcdf.h>
#include <time.h>
#include <hdf5.h>

/* void handle_error(int status)
{
    if (status != NC_NOERR)
    {
        fprintf(stderr, "%s\n", nc_strerror(status));
    }
} */

void save_to_json(double *arr, char *file_name, char *name, size_t size)
{
    FILE *fptr;

    fptr = fopen(file_name, "w");

    fprintf(fptr, "{\"%s\":{", name);

    for (int i = 0; i < size; i++)
    {
        fprintf(fptr, "\"%d\":%f", i, arr[i]);

        if (i != size - 1)
        {
            fprintf(fptr, ",");
        }
    }

    fprintf(fptr, "}}");

    fclose(fptr);
}

void bench_nczarr_open()
{

    int status = NC_NOERR;
    int ncid;
    double arr[10000];

    for (int i = 0; i < 10000; i++)
    {

        struct timespec start, end;

        clock_gettime(CLOCK_MONOTONIC, &start);

        status = nc_open("file:///home/test/dkrz_dev/data/test_dataset.zarr#mode=nczarr,file", NC_WRITE, &ncid);

        clock_gettime(CLOCK_MONOTONIC, &end);

        status = nc_close(ncid);

        double elapsed = end.tv_sec - start.tv_sec;
        elapsed += (end.tv_nsec - start.tv_nsec) / 1000000000.0;
        arr[i] = elapsed;
        // printf("Time spend: %f \n", time_spent);
    }

    printf("Saving to json for nczarr benchmark \n");
    save_to_json(arr, "test_plotting_zarr.json", "nczarr-open", 10000);
    printf("Finished saving \n");
}

void bench_netcdf4_open()
{

    int status = NC_NOERR;
    int ncid;

    double arr2[10000];

    for (int i = 0; i < 10000; i++)
    {

        struct timespec start, end;

        clock_gettime(CLOCK_MONOTONIC, &start);

        status = nc_open("data/test_dataset.nc", NC_WRITE, &ncid);

        clock_gettime(CLOCK_MONOTONIC, &end);

        status = nc_close(ncid);

        double elapsed = end.tv_sec - start.tv_sec;
        elapsed += (end.tv_nsec - start.tv_nsec) / 1000000000.0;
        arr2[i] = elapsed;
        // printf("Time spend: %f \n", time_spent);
    }

    printf("Saving to json for netcdf benchmark \n");
    save_to_json(arr2, "test_plotting_netcdf.json", "netcdf4-open", 10000);
    printf("Finished saving \n");
}

void bench_hdf5_open()
{

    int status = NC_NOERR;
    int ncid;

    double arr3[10000];

    for (int i = 0; i < 10000; i++)
    {

        struct timespec start, end;

        int faplist_id = H5Pcreate(H5P_FILE_ACCESS);

        clock_gettime(CLOCK_MONOTONIC, &start);

        hid_t fileid = H5Fopen("data/test_dataset.h5", H5F_ACC_RDWR, faplist_id);

        clock_gettime(CLOCK_MONOTONIC, &end);

        H5Fclose(fileid);

        double elapsed = end.tv_sec - start.tv_sec;
        elapsed += (end.tv_nsec - start.tv_nsec) / 1000000000.0;
        arr3[i] = elapsed;
        // printf("Time spend: %f \n", time_spent);
    }

    printf("Saving to json for hdf benchmark \n");
    save_to_json(arr3, "test_plotting_hdf.json", "hdf5-open", 10000);
    printf("Finished saving \n");
}

void bench_nczarr_read()
{
    int status = NC_NOERR;
    int ncid;
    double arr[10000];
    status = nc_open("file:///home/test/dkrz_dev/data/test_dataset.zarr#mode=nczarr,file", NC_WRITE, &ncid);

    for (int i = 0; i < 10000; i++)
    {

        struct timespec start, end;

        clock_gettime(CLOCK_MONOTONIC, &start);

        status = nc_open("file:///home/test/dkrz_dev/data/test_dataset.zarr#mode=nczarr,file", NC_WRITE, &ncid);

        clock_gettime(CLOCK_MONOTONIC, &end);

        double elapsed = end.tv_sec - start.tv_sec;
        elapsed += (end.tv_nsec - start.tv_nsec) / 1000000000.0;
        arr[i] = elapsed;
        // printf("Time spend: %f \n", time_spent);
    }

    status = nc_close(ncid);

    printf("Saving to json for nczarr benchmark \n");
    save_to_json(arr, "test_plotting_zarr.json", "nczarr-open", 10000);
    printf("Finished saving \n");
}

void bench_hdf5_read()
{

    int status = NC_NOERR;
    int ncid;

    double arr3[1];
    hid_t fileid, dset;
    float tmp[1];

    fileid = H5Fopen("data/test_dataset.h5", H5F_ACC_RDWR, H5P_DEFAULT);

    for (int i = 0; i < 1; i++)
    {

        struct timespec start, end;

        clock_gettime(CLOCK_MONOTONIC, &start);

        if ((dset = H5Dopen2(fileid, "/x", H5P_DEFAULT)) == H5I_INVALID_HID)
        {
            printf("something went wrong when opening dataset");
        };

        if (H5Dread(dset, H5T_NATIVE_FLOAT, H5S_ALL, H5S_ALL, H5P_DEFAULT, tmp) < 0)
        {
            printf("something went wrong when reading");
        };

        clock_gettime(CLOCK_MONOTONIC, &end);

        H5Dclose(dset);
        H5Fclose(fileid);

        double elapsed = end.tv_sec - start.tv_sec;
        elapsed += (end.tv_nsec - start.tv_nsec) / 1000000000.0;
        arr3[i] = elapsed;
        // printf("Time spend: %f \n", time_spent);
    }

    printf("Saving to json for hdf benchmark \n");
    save_to_json(arr3, "test_plotting_hdf_read.json", "hdf5-read", 1);
    printf("Finished saving \n");
}

void create_hdf5_subfiling(int argc, char **argv)
{
    H5FD_subfiling_config_t subf_config;
    H5FD_ioc_config_t ioc_config;
    MPI_Comm comm = MPI_COMM_WORLD;
    MPI_Info info = MPI_INFO_NULL;
    hid_t file_id = H5I_INVALID_HID;
    hid_t fapl_id = H5I_INVALID_HID;
    int mpi_thread_required = MPI_THREAD_MULTIPLE;
    int mpi_thread_provided = 0;
    /* Initialize MPI with threading support */
    MPI_Init_thread(&argc, &argv, mpi_thread_required, &mpi_thread_provided);

    if (mpi_thread_provided != mpi_thread_required)
        MPI_Abort(comm, -1);
    /*
     * Set up File Access Property List with MPI
     * parameters for the Subfiling VFD to use
     */
    fapl_id = H5Pcreate(H5P_FILE_ACCESS);
    H5Pset_mpi_params(fapl_id, comm, info);
    /*
     * Get a default Subfiling and IOC configuration
     */
    H5Pget_fapl_subfiling(fapl_id, &subf_config);
    H5Pget_fapl_ioc(fapl_id, &ioc_config);
    /*
     * Set Subfiling configuration to use a 1MiB
     * stripe size.
     */
    // subf_config.shared_cfg.stripe_size = 1048576;
    /*
     * Set IOC configuration to use 2 worker threads
     * per IOC instead of the default setting.
     */
    // ioc_config.thread_pool_size = 2;

    /*
     * Set our new configuration on the IOC
     * FAPL used for Subfiling
     */
    H5Pset_fapl_ioc(subf_config.ioc_fapl_id, &ioc_config);
    /*
     * Finally, set our new Subfiling configuration
     * on the original FAPL
     */
    H5Pset_fapl_subfiling(fapl_id, &subf_config);
    /*
     * Create a new Subfiling-based HDF5 file
     */
    file_id = H5Fcreate("data/datasets/test_dataset_subfiling.h5", H5F_ACC_TRUNC, H5P_DEFAULT, fapl_id);


    hid_t dset, fspace, lcpl;

    lcpl = H5Pcreate(H5P_LINK_CREATE);

    fspace = H5Screate_simple(3, (hsize_t[]){512}, NULL);

    dset = H5Dcreate2(file_id, "/X", H5T_IEEE_F64LE, fspace, lcpl, H5P_DEFAULT, H5P_DEFAULT);

    /* Close/free resources */

    H5Dclose(dset);
    H5Sclose(fspace);
    H5Pclose(lcpl);

    H5Pclose(fapl_id);
    H5Fclose(file_id);
    MPI_Finalize();
}

void create_hdf5(){
    hid_t       file_id, dataspace_id, dataset_id;   /* file identifier */
    herr_t      status;
    hsize_t dims[3];

    int some_size = 128;

    dims[0]      = some_size;
    dims[1]      = some_size;
    dims[2]      = some_size;

    float (* dset_data)[some_size][some_size] = calloc(some_size, sizeof(dset_data));

    if ( !dset_data )
    {
      fprintf( stderr, "Fatal: unable to allocate array\n" );
      exit( EXIT_FAILURE );
    }

    /* Create a new file using default properties. */
    printf("Create file \n");
    file_id = H5Fcreate("data/datasets/test_dataset_hdf5-c.h5", H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);

    dataspace_id = H5Screate_simple (3, dims, NULL);

    printf("Create dataset \n");
    dataset_id = H5Dcreate2(file_id, "/X", H5T_IEEE_F64LE, dataspace_id, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);

    int i, j, k;
    int a = 12;

    printf("Fill with values \n");
    for (i = 0; i < some_size; i++)
        for (j = 0; j < some_size; j++)
            for (k = 0; k < some_size; k++)
                printf("i: %d, j: %d, k: %d \n", i, j, k);
                dset_data[i][j][k] = (float)((double)rand()/(double)(RAND_MAX/a));

    
    printf("Write data to dataset \n");
    //status = H5Dwrite(dataset_id, H5T_NATIVE_FLOAT, H5S_ALL, H5S_ALL, H5P_DEFAULT, dset_data);

    free(dset_data);

    /* Terminate access to the file. */
    status = H5Dclose (dataset_id);
    status = H5Sclose (dataspace_id);
    status = H5Fclose(file_id); 
}

int main(int argc, char **argv)
{

    // bench_nczarr_open();
    // bench_netcdf4_open();
    // bench_hdf5_open();

    //create_hdf5_subfiling(argc, argv);
    create_hdf5();

    return 0;
}
