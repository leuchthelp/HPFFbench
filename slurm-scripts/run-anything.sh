#!/bin/bash
#SBATCH --wait
#SBATCH --partition=compute
#SBATCH --account=ku0598
#SBATCH --constraint="[cell02]"
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=0
#SBATCH --cpu-freq=High
#SBATCH --distribution=block:cyclic
#SBATCH --time=08:00:00
#SBATCH --output=log/log-%j/log.%j.txt
#SBATCH --error=log/log-%j/log.%j.err


# Begin of section with executable commands
set -e
ls -l

$1

mpi_enabled=$2
w=true

if [ "$mpi_enabled" = "$w" ]; then

    export OMPI_MCA_osc="ucx"
    export OMPI_MCA_pml="ucx"
    export OMPI_MCA_btl="self"
    export UCX_HANDLE_ERRORS="bt"
    export OMPI_MCA_pml_ucx_opal_mem_hooks=1
    
    export OMPI_MCA_io="romio321"          # basic optimisation of I/O
    export UCX_TLS="shm,rc_mlx5,rc_x,self" # for jobs using LESS than 150 nodes
    #export UCX_TLS="shm,dc_mlx5,dc_x,self" # for jobs using MORE than 150 nodes
    export UCX_UNIFIED_MODE="y"            
    
    export OMPI_MCA_coll_tuned_use_dynamic_rules="true"
    export OMPI_MCA_coll_tuned_alltoallv_algorithm=2

fi


$3

$4

$5