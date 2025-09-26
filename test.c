#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <hdf5.h>
#include <unistd.h>
#include <argp.h>

#define ANSI_COLOR_RED "\x1b[31m"
#define ANSI_COLOR_GREEN "\x1b[32m"
#define ANSI_COLOR_YELLOW "\x1b[33m"
#define ANSI_COLOR_BLUE "\x1b[34m"
#define ANSI_COLOR_MAGENTA "\x1b[35m"
#define ANSI_COLOR_CYAN "\x1b[36m"
#define ANSI_COLOR_RESET "\x1b[0m"

void create(bool with_chunking, hsize_t size, hsize_t chunk, char *location)
{
    // printf(ANSI_COLOR_YELLOW "Create hdf5 file" ANSI_COLOR_RESET "\n");
    hid_t plist_id, file_id, filespace, dset_id; /* file identifier */
    herr_t status;
    hsize_t dims[1];
    hsize_t cdims[1];

    /* Create a new file using default properties. */
    file_id = H5Fcreate(location, H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);

    // setup dimensions
    hsize_t some_size = size;

    dims[0] = some_size;
    filespace = H5Screate_simple(1, dims, NULL);

    plist_id = H5Pcreate(H5P_DATASET_CREATE);

    if (chunk != 0)
    {
        // setup chunking
        cdims[0] = chunk;
        status = H5Pset_chunk(plist_id, 1, cdims);
    }

    // create Dataset
    dset_id = H5Dcreate(file_id, "/X", H5T_IEEE_F64LE, filespace, H5P_DEFAULT, plist_id, H5P_DEFAULT);

    // fill buffer
    float *wbuf = calloc(some_size, sizeof(float));

    if (!wbuf)
    {
        fprintf(stderr, "Fatal: unable to allocate shape_arr\n");
        exit(EXIT_FAILURE);
    }

    hsize_t i;

    for (i = 0; i < some_size; i++)
    {
        wbuf[i] = (float)rand() / RAND_MAX;
    }

    status = H5Dwrite(dset_id, H5T_NATIVE_FLOAT, H5S_ALL, H5S_ALL, H5P_DEFAULT, wbuf);

    free(wbuf);

    /* Terminate access to the file. */
    status = H5Dclose(dset_id);
    status = H5Sclose(filespace);
    status = H5Fclose(file_id);
    // printf(ANSI_COLOR_YELLOW "Finish creating hdf5 file" ANSI_COLOR_RESET "\n");
}

#include <unistd.h>
#include <argp.h>
#include <stdio.h>
#include <string.h>

typedef struct args_t
{
    int create;
    int benchmark;
    char *var_to_bm;
    char *variables;
    char *shapes;
    char *chunks;
    char *datatypes;
    hsize_t factor;
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
    case 'i':
        arguments->iterations = atoi(arg);
        break;
    case 'v':
        arguments->var_to_bm = arg;
        break;
    case 'V':
        arguments->variables = arg;
        break;
    case 'S':

        arguments->shapes = arg;
        break;
    case 'C':
        arguments->chunks = arg;
        break;
    case 'D':
        arguments->datatypes = arg;
        break;
    case 'f':
        arguments->factor = strtoull(arg, NULL, 10);
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
    {"benchmark", 'b', "NUM", 0, "If to run benchmark"},
    {"var_to_bm", 'v', "c", 0, "Variables within a file to benchmark"},
    {"variables", 'V', "c", 0, "Variables the file should contain"},
    {"shapes", 'S', "c", 0, "Specifiy the shapes of the file you want to create as list of lists"},
    {"chunks", 'C', "c", 0, "Specifiy the chunksize of the file you want to create as list of lists"},
    {"datatypes", 'D', "c", 0, "Data types each variable should have as list"},
    {"factor", 'f', "NUM", 0, "Factor to multiply shape with to increase / decrease size"},
    {"iterations", 'i', "NUM", 0, "Ammount of iterations the benchmark should run"},
    {"location", 'l', "c", 0, "Location where file is going to be created / read from"},
    {0}};

hsize_t word_count(char *smth, char delim)
{
    hsize_t count = 1;
    for (hsize_t x = 0; x < strlen(smth); x++)
        if (smth[x] == delim)
            count++;
    return count;
}

char *get_chars(char *smth, hsize_t size)
{
    char *arr = (char *)malloc(size * sizeof(char));
    if (arr == NULL)
    {
        printf("Memory allocation failed!\n");
        exit(1); // Exit the program if allocation fails
    }
    hsize_t i = 0;

    for (hsize_t x = 0; x < strlen(smth); x++)
    {
        if (smth[x] != 44) // ASCII ","
        {
            arr[i] = smth[x];
            i++;
        }
        else
        {
            continue;
        }
    }
    return arr;
}

int get_list_contents(char *smth, hsize_t *jagged)
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
            jagged[i] = (hsize_t)strtoull(tmp_char, NULL, 10);
            tmp_char[0] = '\0';
            i++;
        }
    }
    jagged[i] = (hsize_t)strtoull(tmp_char, NULL, 10);
    return 0;
}

void print_jagged(hsize_t **jagged_arr, hsize_t *jagged_size, hsize_t count)
{

    hsize_t k = 0;
    // To display elements of Jagged array
    for (hsize_t i = 0; i < count; i++)
    {

        // pointer to hold the address of the row
        hsize_t *ptr = jagged_arr[i];

        for (hsize_t j = 0; j < jagged_size[k]; j++)
        {
            printf("%ld ", *ptr);

            // move the pointer to the
            // next element in the row
            ptr++;
        }

        printf("\n");
        k++;

        // move the pointer to the next row
        jagged_arr[i]++;
    }
}

int main(int argc, char *argv[])
{
    struct argp argp = {options, parse_opt};

    args_t arguments;
    arguments.create = -1;
    arguments.benchmark = -1;
    hsize_t tmpsize = 134217728;
    arguments.var_to_bm = "[]";
    arguments.variables = "[]";
    arguments.shapes = "[]";
    arguments.chunks = "[]";
    arguments.datatypes = "[]";
    arguments.factor = 1;
    arguments.iterations = 1;
    arguments.location = "test.c";

    printf("Parsing: %d, filesize: %lu, var_to_bm: %s, variables: %s, shapes: %s, chunks: %s, datatypes: %s, factor: %lu, iterations: %d --- \n", arguments.benchmark, tmpsize, arguments.var_to_bm, arguments.variables, arguments.shapes, arguments.chunks, arguments.datatypes, arguments.factor, arguments.iterations);
    argp_parse(&argp, argc, argv, 0, 0, &arguments);

    hsize_t size = tmpsize * arguments.factor;
    char *var_to_bm = arguments.var_to_bm;
    char *variables = arguments.variables;
    char *shapes = arguments.shapes;
    char *chunks = arguments.chunks;
    char *datatypes = arguments.datatypes;
    char *location = arguments.location;
    int iterations = arguments.iterations;
    int res;

    char *var_tmp;
    hsize_t var_count = word_count(variables, ',');
    var_tmp = get_chars(variables, var_count);

    char *token;
    char *rest = shapes;

    hsize_t **testing = malloc(var_count * sizeof(hsize_t *));
    hsize_t jagged_size[var_count], k = 0;

    hsize_t current_var = 0;
    while ((token = strtok_r(rest, "-", &rest)))
    {
        hsize_t dims = word_count(token, ',');
        printf("token: %s, dim count: %ld \n", token, dims);

        testing[current_var] = malloc(dims * sizeof(hsize_t *));
        get_list_contents(token, testing[current_var]);
        jagged_size[current_var] = dims;
        current_var++;
    }

    print_jagged(testing, jagged_size, var_count);

    printf("Parsing: %d, filesize: %lu, var_to_bm: %s, variables: %s, shapes: %s, chunks: %s, datatypes: %s, factor: %lu, iterations: %d --- \n", arguments.benchmark, size, var_to_bm, variables, shapes, chunks, datatypes, arguments.factor, arguments.iterations);

    // arguments parsing for creation of file
    switch (arguments.create)
    {
    case -1:
        break;
    case 1:
        // printf("Creating hdf5 file with a filesize of %lu and chunksize of %s", size, chunks);
        // create(false, size, 0, location);
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
        // printf("No benchmark specified, exiting programm now");
        break;
    case 1:
        // printf("Running hdf5 benchmark with a filesize of %lu for %d iterations", size, iterations);
        bench(size, iterations, location);
        break;
    case ARGP_KEY_ARG:
        return 0;
    default:
        return ARGP_ERR_UNKNOWN;
    }

    for (int i = 0; i < var_count; i++)
    {
        free(testing[i]);
    }
    free(testing);
    free(var_tmp);
    return 0;
}