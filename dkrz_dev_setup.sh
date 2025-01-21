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

spack install lmod
. $(spack location -i lmod)/lmod/lmod/init/bash
. share/spack/setup-env.sh

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

echo "install py-mpi4py via spack"
spack install py-mpi4py

cd ..
spack env activate --create ./dkrz_dev
spack env status

cd dkrz_dev/

spack add gcc hdf5 netcdf-c py-netcdf4@1.6.5 hdf5-vol-async py-numpy py-h5py py-mpi4py python@3.11.9 python-venv lmod py-rich
spack install
spack load gcc hdf5 netcdf-c py-netcdf4@1.6.5 hdf5-vol-async py-numpy py-h5py py-mpi4py python@3.11.9 python-venv lmod py-rich
spack load --list