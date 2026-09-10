#!/bin/bash
#SBATCH --partition=compute
#SBATCH --account=ku0598
#SBATCH --output=log-/log-%j/log.%j.txt
#SBATCH --error=log-/log-%j/log.%j.err

set -e

source spack/share/spack/setup-env.sh

spack install gcc@15.2