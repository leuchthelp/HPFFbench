echo "install spack"

git clone --depth=2 --branch=releases/v0.23 https://github.com/spack/spack.git ~/spack
cd ~/spack
. share/spack/setup-env.sh

echo "finish install spack"

echo "install gcc via spack"
spack install gcc
spack load gcc
spack compiler find

echo "install netcdf-c via spack"
spack install netcdf-c

echo "install py-netcdf4 via spack"
spack install py-netcdf4

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

echo "install py-plotly via spack"
spack install py-plotly

echo "install py-pandas via spack"
spack install py-pandas

echo "install py-matplotlib via spack"
spack install py-matplotlib

echo "install py-rich via spack"
spack install py-rich

echo "install py-ippyparallel via spack"
spack install py-ipyparallel

echo "install py-mpi4py via spack"
spack install py-mpi4py

echo "install packages missing in spack via pip"
pip install -r requirements.txt