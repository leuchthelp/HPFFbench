#!/bin/bash
#SBATCH --partition=compute
#SBATCH --account=ku0598
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=6
#SBATCH --time=01:00:00

# Begin of section with executable commands
set -e
ls -l
srun ./main.py