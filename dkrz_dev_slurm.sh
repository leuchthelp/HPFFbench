#!/bin/bash
#SBATCH --partition=compute
#SBATCH --account=ku0598
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBACTH --mem=0
#SBATCH --time=08:00:00
#SBATCH --output=log-/log-%j/log.%j.txt
#SBATCH --error=log-/log-%j/log.%j.err


# Begin of section with executable commands
set -e
ls -l
python main_cluster.py