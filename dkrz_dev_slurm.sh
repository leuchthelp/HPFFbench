#!/bin/bash
#SBATCH --partition=compute
#SBATCH --account=ku0598
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=08:00:00
#SBATCH --output=log.%j.txt
#SBATCH --error=log.%j.err

# Begin of section with executable commands
set -e
ls -l
srun python main.py