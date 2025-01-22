echo "install spack"

git clone --depth=2 --branch=releases/v0.23 https://github.com/spack/spack.git ~/spack
cd ~/spack
. share/spack/setup-env.sh

echo "finish install spack"

echo "install gcc via spack"
spack install gcc
spack load gcc
which gcc
spack compiler find

spack config add "modules:default:enable:[tcl]"

spack install lmod
. $(spack location -i lmod)/lmod/lmod/init/bash
. share/spack/setup-env.sh

echo "install python@3.11.9 via spack"
spack install python@3.11.9 

echo "install python-venv via spack"
spack install python-venv

echo "install openmpi via spack"
spack install openmpi

echo "install hdf5 via spack"
spack install hdf5+threadsafe

echo "install hdf5-vol-async via spack"
spack install hdf5-vol-async

echo "install netcdf-c via spack"
spack install netcdf-c

#spack add gcc python@3.11.9 python-venv hdf5 netcdf-c hdf5-vol-async lmod
#spack install
#spack load gcc python@3.11.9 python-venv hdf5 netcdf-c hdf5-vol-async lmod
#spack load gcc python@3.11.9 python-venv openmpi hdf5 /opj45mn netcdf-c
spack load --list