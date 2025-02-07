#include <stdio.h>
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

/* int test_open()
{
    int status = NC_NOERR;
    int ncid;
    return status = nc_open("file:///home/test/dkrz_dev/data/test_dataset.zarr#mode=nczarr,file", NC_WRITE, &ncid);
}

int test_open_netcdf()
{
    int status = NC_NOERR;
    int ncid;
    return status = nc_open("data/test_dataset.nc", NC_WRITE, &ncid);
} */

int main(int, char **)
{

    bench_nczarr_open();
    bench_netcdf4_open();
    bench_hdf5_open();

    return 0;
}
