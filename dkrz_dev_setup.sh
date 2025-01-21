echo "install spack"

git clone --depth=2 --branch=releases/v0.23 https://github.com/spack/spack.git ~/spack
cd ~/spack
. share/spack/setup-env.sh

spack install lmod
. $(spack location -i lmod)/lmod/lmod/init/bash
. share/spack/setup-env.sh

echo "finish install spack"

echo "install gcc via spack"
spack install gcc
spack load gcc
which gcc
spack compiler find

echo "install netcdf-c via spack"
spack install netcdf-c

echo "install py-netcdf4 via spack"
spack install py-netcdf4@1.6.5

echo "install hdf5 via spack"
spack install hdf5

echo "install hdf5-vol-async via spack"
spack install hdf5-vol-async

echo "install py-numpy via spack"
spack install py-numpy

echo "install py-h5py via spack"
spack install py-h5py

echo "install py-xarray via spack"
spack install py-xarray

echo "install py-pandas via spack"
spack install py-pandas

echo "install py-matplotlib via spack"
spack install py-matplotlib

echo "install py-rich via spack"
spack install py-rich

echo "install py-mpi4py via spack"
spack install py-mpi4py

echo "install py-ipython via spack"
spack install py-ipython

cd ~/dkrz_dev
spack env create -d
spack env activate
spack env status

spack add gcc hdf5 netcdf-c py-netcdf4@1.6.5 hdf5-vol-async py-numpy py-h5py py-xarray py-pandas py-matplotlib py-rich py-mpi4py py-ipython python@3.11.9 python-venv lmod
spack concretize
spack install
spack load gcc hdf5 netcdf-c py-netcdf4@1.6.5 hdf5-vol-async py-numpy py-h5py py-xarray py-pandas py-matplotlib py-rich py-mpi4py py-ipython python@3.11.9 python-venv lmod
spack load --list

echo "install packages missing in spack via pip"
source .venv/bin/activate
pip3 install -r requirements.txt