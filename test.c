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

void create(bool with_chunking, char **variables, hsize_t **shapes, hsize_t **chunks, char **datatypes, char *location)
{
    printf(ANSI_COLOR_YELLOW "Create hdf5 file" ANSI_COLOR_RESET "\n");
    hid_t plist_id, file_id, filespace, dset_id; /* file identifier */
    herr_t status;
    hsize_t dims[1];
    hsize_t cdims[1];

    /* Create a new file using default properties. */
    file_id = H5Fcreate(location, H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);

    // setup dimensions
    printf("size of dataset %ld \n", shapes[0][0]);
    hsize_t some_size = shapes[0][0];

    dims[0] = some_size;
    filespace = H5Screate_simple(1, dims, NULL);

    plist_id = H5Pcreate(H5P_DATASET_CREATE);

    if (chunks[0][0] != 0)
    {
        // setup chunking
        printf("chunksize %ld \n", chunks[0][0]);
        cdims[0] = chunks[0][0];
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

    for (hsize_t i = 0; i < some_size; i++)
    {
        wbuf[i] = (float)rand() / RAND_MAX;
    }

    status = H5Dwrite(dset_id, H5T_NATIVE_FLOAT, H5S_ALL, H5S_ALL, H5P_DEFAULT, wbuf);

    free(wbuf);

    /* Terminate access to the file. */
    status = H5Dclose(dset_id);
    status = H5Sclose(filespace);
    status = H5Fclose(file_id);
    printf(ANSI_COLOR_YELLOW "Finish creating hdf5 file" ANSI_COLOR_RESET "\n");
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
    char *variable;
    char *shape;
    char *chunk;
    char *datatype;
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
        arguments->variable = arg;
        break;
    case 'S':

        arguments->shape = arg;
        break;
    case 'C':
        arguments->chunk = arg;
        break;
    case 'D':
        arguments->datatype = arg;
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
    {"variable", 'V', "c", 0, "Variables the file should contain"},
    {"shape", 'S', "c", 0, "Specifiy the shapes of the file you want to create as list of lists"},
    {"chunk", 'C', "c", 0, "Specifiy the chunksize of the file you want to create as list of lists"},
    {"datatype", 'D', "c", 0, "Data types each variable should have as list"},
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

int get_chars(char *smth, hsize_t amount, char **buf)
{
    hsize_t i = 0;
    char *token;
    char *rest = smth;

    while ((token = strtok_r(rest, ",", &rest)))
    {
        if (i == amount)
            break;
        buf[i] = calloc(strlen(token), sizeof(char *));
        strcpy(buf[i], token);
        i++;
    }
    return 0;
}

int get_list_contents(char *smth, hsize_t *buf)
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
            buf[i] = (hsize_t)strtoull(tmp_char, NULL, 10);
            tmp_char[0] = '\0';
            i++;
        }
    }
    buf[i] = (hsize_t)strtoull(tmp_char, NULL, 10);
    return 0;
}

int get_individual_as_jagged(char *smth, hsize_t size, hsize_t **buf, hsize_t *jagged_size)
{
    char *token;
    char *rest = smth;

    hsize_t current_var = 0;
    while ((token = strtok_r(rest, "-", &rest)))
    {
        if (current_var == size)
            break;
        hsize_t dims = word_count(token, ',');
        printf("token: %s, dim count: %ld \n", token, dims);

        buf[current_var] = calloc(dims, sizeof(hsize_t));
        int res = get_list_contents(token, buf[current_var]);
        jagged_size[current_var] = dims;
        current_var++;
    }
    return 0;
}

void print_jagged(hsize_t **jagged_arr, hsize_t *jagged_size, hsize_t count)
{

    hsize_t k = 0;
    // Display elements in Jagged array
    for (int i = 0; i < 2; i++)
    {

        hsize_t *p = jagged_arr[i];
        for (int j = 0; j < jagged_size[k]; j++)
        {

            printf("%ld ", *p);
            // move the pointer to the next element
            p++;
        }
        printf("\n");
        k++;
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
    arguments.variable = "[]";
    arguments.shape = "[]";
    arguments.chunk = "[]";
    arguments.datatype = "[]";
    arguments.factor = 1;
    arguments.iterations = 1;
    arguments.location = "test.c";

    printf("Parsing: %d, var_to_bm: %s, variables: %s, shapes: %s, chunks: %s, datatypes: %s, factor: %lu, iterations: %d --- \n", arguments.benchmark, arguments.var_to_bm, arguments.variable, arguments.shape, arguments.chunk, arguments.datatype, arguments.factor, arguments.iterations);
    argp_parse(&argp, argc, argv, 0, 0, &arguments);

    hsize_t size = tmpsize * arguments.factor;
    char *location = arguments.location;
    int iterations = arguments.iterations;
    int res;

    // get variables to benchmark
    hsize_t var_bm_count = word_count(arguments.var_to_bm, ',');
    printf("word count->variables to benchmark: %ld \n", var_bm_count);

    // get variables
    hsize_t var_count = word_count(arguments.variable, ',');
    printf("word count->variables for dataset creation: %ld \n", var_count);

    // get shapes
    hsize_t **shapes = calloc(var_count, sizeof(hsize_t *));
    hsize_t shapes_size[var_count];

    // get chunks
    hsize_t **chunks = calloc(var_count, sizeof(hsize_t *));
    hsize_t chunks_size[var_count];

    printf("Parsing: %d, factor: %lu, iterations: %d --- \n", arguments.benchmark, arguments.factor, arguments.iterations);

    // arguments parsing for creation of file
    switch (arguments.create)
    {
    case -1:
        break;
    case 1:

        // get variables
        char **variables = calloc(var_count, sizeof(char *));
        res = get_chars(arguments.variable, var_count, variables);

        for (int i = 0; i < var_count; i++)
        {
            printf("%s\n", variables[i]);
        }

        // get shapes
        res = get_individual_as_jagged(arguments.shape, var_count, shapes, shapes_size);
        print_jagged(shapes, shapes_size, var_count);

        // get chunks
        res = get_individual_as_jagged(arguments.chunk, var_count, chunks, chunks_size);
        if (chunks[0][0] != 0)
            print_jagged(chunks, chunks_size, var_count);


        // get datatypes
        printf("word count: %ld \n", var_count);
        char **datatypes = calloc(var_count, sizeof(char *));
        res = get_chars(arguments.datatype, var_count, datatypes);

        for (int i = 0; i < var_count; i++)
        {
            printf("%s\n", datatypes[i]);
        }

        printf("Creating hdf5 file \n");
        create(false, variables, shapes, chunks, datatypes, location);

        // Free variables, datatypes, shape and chunks
        for (int i = 0; i < var_count; i++)
        {
            free(variables[i]);
        }
        free(variables);

        for (int i = 0; i < var_count; i++)
        {
            free(datatypes[i]);
        }
        free(datatypes);

        for (int i = 0; i < var_count; i++)
        {
            free(shapes[i]);
        }
        free(shapes);

        for (int i = 0; i < var_count; i++)
        {
            free(chunks[i]);
        }
        free(chunks);

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
        printf("No benchmark specified, exiting programm now \n");
        break;
    case 1:
        // get variables to benchmark
        char **vars_to_bm = calloc(var_bm_count, sizeof(char *));
        res = get_chars(arguments.var_to_bm, var_bm_count, vars_to_bm);

        for (int i = 0; i < var_bm_count; i++)
        {
            printf("%s\n", vars_to_bm[i]);
        }

        printf("Running hdf5 benchmark for %d iterations\n", iterations);
        bench(size, vars_to_bm, iterations, location);

        // Free variables to benchmark
        for (int i = 0; i < var_bm_count; i++)
        {
            free(vars_to_bm[i]);
        }
        free(vars_to_bm);
        break;
    case ARGP_KEY_ARG:
        return 0;
    default:
        return ARGP_ERR_UNKNOWN;
    }
    return 0;
}