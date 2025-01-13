#include <stdio.h>
#include <netcdf.h>
#include <time.h>

void handle_error(int status)
{
    if (status != NC_NOERR)
    {
        fprintf(stderr, "%s\n", nc_strerror(status));
    }
}

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

int test_open()
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
}

int main(int, char **)
{

    int status = NC_NOERR;
    int ncid;

    printf("create Dataset with netcdf-c \n");
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

    double arr[1000];

    for (int i = 0; i < 1000; i++)
    {
        clock_t begin = clock();

        status = nc_open("file:///home/test/dkrz_dev/data/test_dataset.zarr#mode=nczarr,file", NC_WRITE, &ncid);

        double time_spent = (double)(clock() - begin) / CLOCKS_PER_SEC;
        arr[i] = time_spent;
        // printf("Time spend: %f \n", time_spent);
    }

    printf("Saving to json \n");
    save_to_json(arr, "test_plotting.json", "lol", 1000);

    printf("Status %d \n", status);
    printf("ncid %d \n", ncid);

    if (status != NC_NOERR)
        handle_error(status);
}
