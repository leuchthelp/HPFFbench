#!/bin/bash
#SBATCH --partition=compute
#SBATCH --account=ku0598
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBACTH --mem=0
#SBATCH --cpu-freq=High
#SBATCH --distribution=block:cyclic
#SBATCH --time=08:00:00
#SBATCH --output=log.%j.txt
#SBATCH --error=log.%j.err


# Begin of section with executable commands
set -e
ls -l
srun --cpu_bind=cores --cpu-freq=High --distribution=block:cyclic python main_cluster.py