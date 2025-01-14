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

        if (i != size-1)
        {
            fprintf(fptr, ",");
        }
    }

    fprintf(fptr, "}}");

    fclose(fptr);
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

    int status = NC_NOERR;
    int ncid;

/*     printf("create Dataset with netcdf-c \n");
    status = nc_create("test.nc", NC_NETCDF4, &ncid);

    printf("Status %d \n", status);
    printf("ncid %d \n", ncid);

    if (status != NC_NOERR)
        handle_error(status);

    printf("open Dataset with netcdf-c \n");
    status = nc_open("test.nc", NC_WRITE, &ncid);

    printf("Status %d \n", status);
    printf("ncid %d \n", ncid);

    if (status != NC_NOERR)
        handle_error(status);

    printf("open Dataset created in python with netcdf-c \n");
    status = nc_open("data/test_dataset.nc", NC_WRITE, &ncid);

    printf("Status %d \n", status);
    printf("ncid %d \n", ncid);

    if (status != NC_NOERR)
        handle_error(status);

    printf("open Dataset with zarr using netcdf-c \n");
 */
    double arr[10000];

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

    printf("Saving to json for zarr benchmark \n");
    save_to_json(arr, "test_plotting_zarr.json", "lol", 10000);


    for (int i = 0; i < 10000; i++)
    {
        
        struct timespec start, end;

        clock_gettime(CLOCK_MONOTONIC, &start);

        status = nc_open("data/test_dataset.nc", NC_WRITE, &ncid);

        clock_gettime(CLOCK_MONOTONIC, &end);

        double elapsed = end.tv_sec - start.tv_sec;
        elapsed += (end.tv_nsec - start.tv_nsec) / 1000000000.0;
        arr[i] = elapsed;
        // printf("Time spend: %f \n", time_spent);
    }

    printf("Saving to json for netcdf benchmark \n");
    save_to_json(arr, "test_plotting_netcdf.json", "lol2", 10000);


    for (int i = 0; i < 10000; i++)
    {
        
        struct timespec start, end;

        clock_gettime(CLOCK_MONOTONIC, &start);

        status = nc_open("data/test_dataset.h5", NC_WRITE, &ncid);

        clock_gettime(CLOCK_MONOTONIC, &end);

        double elapsed = end.tv_sec - start.tv_sec;
        elapsed += (end.tv_nsec - start.tv_nsec) / 1000000000.0;
        arr[i] = elapsed;
        // printf("Time spend: %f \n", time_spent);
    }

    printf("Saving to json for hdf benchmark \n");
    save_to_json(arr, "test_plotting_hdf.json", "lol3", 10000);
/* 
    printf("Status %d \n", status);
    printf("ncid %d \n", ncid);

    if (status != NC_NOERR)
        handle_error(status); */
}
