#!/bin/bash
#SBATCH --partition=compute
#SBATCH --account=ku0598
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=6
#SBATCH --time=01:00:00
#SBATCH --output=log.%j.txt

# Begin of section with executable commands
set -e
ls -l
srun ./main.py