#include <stdio.h>
#include <stdlib.h>
#include <netcdf.h>
#include <time.h>
#include <hdf5.h>

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


void create_hdf5(bool with_chunking)
{
    hid_t plist_id, file_id, dataspace_id, dataset_id; /* file identifier */
    herr_t status;
    hsize_t dims[1];
    hsize_t cdims[1];

    /* Create a new file using default properties. */
    printf("Create file \n");
    file_id = H5Fcreate("data/datasets/test_dataset_hdf5-c.h5", H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);

    // setup dimensions
    int some_size = 134217728;
    printf("size: %d \n", some_size);

    dims[0] = some_size;
    dataspace_id = H5Screate_simple(1, dims, NULL);

    plist_id = H5Pcreate(H5P_DATASET_CREATE);

    if (with_chunking)
    {
        // setup chunking
        cdims[0] = 512;
        status = H5Pset_chunk(plist_id, 1, cdims);
    }

    // fill buffer
    float *dset_data = calloc(some_size, sizeof(float));

    if (!dset_data)
    {
        fprintf(stderr, "Fatal: unable to allocate array\n");
        exit(EXIT_FAILURE);
    }

    // create Dataset
    printf("Create dataset \n");
    dataset_id = H5Dcreate2(file_id, "/X", H5T_IEEE_F64LE, dataspace_id, H5P_DEFAULT, plist_id, H5P_DEFAULT);

    int i, j, k;

    printf("Fill with values \n");
    for (i = 0; i < some_size; i++)
    {

        float rand_float = (float)rand() / RAND_MAX;
        // printf("i: %d, j: %d, k: %d, random float: %f \n", i, j, k, rand_float);

        dset_data[i] = (float)rand() / RAND_MAX;
    }

    printf("Write data to dataset \n");
    status = H5Dwrite(dataset_id, H5T_NATIVE_FLOAT, H5S_ALL, H5S_ALL, H5P_DEFAULT, dset_data);

    free(dset_data);

    /* Terminate access to the file. */
    status = H5Dclose(dataset_id);
    status = H5Sclose(dataspace_id);
    status = H5Fclose(file_id);
}


void bench_variable()
{
    int iteration = 10;
    double arr3[iteration];

    for (int i = 0; i < iteration; i++)
    {
        struct timespec start, end;

        clock_gettime(CLOCK_MONOTONIC, &start);

        hid_t file_id, dataset_id;
        herr_t status;
        int some_size = 134217728;
        float *rbuf = calloc(some_size, sizeof(float));

        file_id = H5Fopen("data/datasets/test_dataset_hdf5-c.h5", H5F_ACC_RDWR, H5P_DEFAULT);
        dataset_id = H5Dopen2(file_id, "/X", H5P_DEFAULT);

        status = H5Dread(dataset_id, H5T_NATIVE_FLOAT, H5S_ALL, H5S_ALL, H5P_DEFAULT, rbuf);

        status = H5Dclose(dataset_id);
        status = H5Fclose(file_id);

        clock_gettime(CLOCK_MONOTONIC, &end);
        double elapsed = end.tv_sec - start.tv_sec;
        elapsed += (end.tv_nsec - start.tv_nsec) / 1000000000.0;
        arr3[i] = elapsed;

        free(rbuf);
    }

    save_to_json(arr3, "test_hdf5-c.json", "hdf5-c-read", iteration);
}


int main(int argc, char **argv)
{

    // bench_nczarr_open();
    // bench_netcdf4_open();
    // bench_hdf5_open();

    // create_hdf5_subfiling(argc, argv);
    create_hdf5(false);

    printf("Bench variable complete \n");
    bench_variable();

    return 0;
}
